import asyncio
import json
from datetime import date
from logging import getLogger
from typing import Dict

import httpx
from pydantic import BaseModel, ValidationError

from src.config.alpha import AlphaVantageConfig
from src.tools._alpha import (
    BalanceSheetResponse,
    CashFlowResponse,
    EarningsResponse,
    InsiderTransactionsResponse,
    OverviewResponse,
    TickerData,
)
from src.utils.datetime import seconds_since_creation
from src.utils.debug import collect_first_elements

logger = getLogger(__name__)


class AlphaVantageClient:
    """
    Client to fetch and parse financial data from Alpha Vantage,
    with centralized file-based caching for individual API calls, deduplication via per-symbol locks, and error handling.
    Supports filtering of reports by a provided end_date.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, config: AlphaVantageConfig = AlphaVantageConfig()):
        self.config = config
        self._locks: Dict[str, asyncio.Lock] = {}
        if self.config.cache_dir:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
            self.config.cache_error_dir.mkdir(parents=True, exist_ok=True)

    async def aget_ticker_data(
        self,
        symbol: str,
        end_date: date = date.today(),
    ) -> TickerData:
        lock = self._locks.setdefault(symbol, asyncio.Lock())
        async with lock:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                tasks = {
                    "overview": self._fetch(
                        client, "OVERVIEW", symbol, OverviewResponse
                    ),
                    "balance_sheet": self._fetch(
                        client, "BALANCE_SHEET", symbol, BalanceSheetResponse
                    ),
                    "cash_flow": self._fetch(
                        client, "CASH_FLOW", symbol, CashFlowResponse
                    ),
                    "earnings": self._fetch(
                        client, "EARNINGS", symbol, EarningsResponse
                    ),
                    "insider_transactions": self._fetch(
                        client,
                        "INSIDER_TRANSACTIONS",
                        symbol,
                        InsiderTransactionsResponse,
                    ),
                }
                overview, bs_resp, cf_resp, er_resp, it_resp = await asyncio.gather(
                    *tasks.values()
                )

            full = TickerData(
                overview=overview,
                balance_sheet=bs_resp,
                cash_flow=cf_resp,
                earnings=er_resp,
                insider_transactions=it_resp,
            )

            return self._apply_filter(full, end_date)

    def get_ticker_data(
        self,
        symbol: str,
        end_date: date = date.today(),
    ) -> TickerData:
        return asyncio.run(self.aget_ticker_data(symbol, end_date))

    def _apply_filter(self, data: TickerData, end_date: date) -> TickerData:
        data.cash_flow.annual_reports = [
            r for r in data.cash_flow.annual_reports if r.fiscal_date_ending <= end_date
        ]
        if data.cash_flow.quarterly_reports:
            data.cash_flow.quarterly_reports = [
                r
                for r in data.cash_flow.quarterly_reports
                if r.fiscal_date_ending <= end_date
            ]
        data.balance_sheet.annual_reports = [
            r
            for r in data.balance_sheet.annual_reports
            if r.fiscal_date_ending <= end_date
        ]
        data.balance_sheet.quarterly_reports = [
            r
            for r in data.balance_sheet.quarterly_reports
            if r.fiscal_date_ending <= end_date
        ]
        data.earnings.annual_earnings = [
            r for r in data.earnings.annual_earnings if r.fiscal_date_ending <= end_date
        ]
        data.earnings.quarterly_earnings = [
            r
            for r in data.earnings.quarterly_earnings
            if r.fiscal_date_ending <= end_date
        ]
        data.insider_transactions.data = [
            tx
            for tx in data.insider_transactions.data
            if tx.transaction_date <= end_date
        ]
        return data

    async def _fetch(
        self,
        client: httpx.AsyncClient,
        function: str,
        symbol: str,
        response_model: BaseModel,
    ) -> BaseModel:
        cache_file_path = None
        if self.config.cache_dir:
            cache_file_path = self.config.cache_dir / f"{symbol}_{function}.json"
            if (
                cache_file_path.exists()
                and seconds_since_creation(cache_file_path) < self.config.cache_timeout
            ):
                logger.debug(f"Using cached response for {symbol} {function}")
                raw = cache_file_path.read_text()
                try:
                    return response_model.model_validate_json(raw)
                except ValidationError as e:
                    logger.warning(f"Cached data for {symbol} {function} is invalid")
                    raise RuntimeError(
                        f"Validation error: {e}\n\n{symbol=} {function=}"
                    )

        logger.info(f"Fetching data for {symbol} {function}")
        response = await client.get(
            self.BASE_URL,
            params={
                "function": function,
                "symbol": symbol,
                "apikey": self.config.api_key,
            },
        )
        response.raise_for_status()
        data = response.json()

        if "Information" in data:
            raise RuntimeError(data["Information"])

        # Store raw response after status check and before Information check
        if cache_file_path:
            cache_file_path.write_text(json.dumps(data, indent=2))
            logger.debug(
                f"Stored raw response for {symbol} {function} at {cache_file_path}"
            )

        try:
            return response_model(**data)
        except ValidationError as e:
            logger.error(f"Validation failed for {symbol} {function}: {e}")

            error_cache_file_path = (
                self.config.cache_error_dir / f"{symbol}_{function}_error.json"
            )
            error_info = {
                "validation_errors": e.errors(),
                "raw_data": data,
            }
            error_cache_file_path.write_text(json.dumps(error_info, indent=2))

            logger.error(f"Validation failed for {symbol} {function}: {e}")
            raise RuntimeError(
                f"Validation error: {e}\n\nCollected first elements: {collect_first_elements(data)}\n\n{symbol=} {function=}"
            )


if __name__ == "__main__":
    client = AlphaVantageClient()
    symbol = "IBM"
    ticker_data = client.get_ticker_data(symbol, end_date=date(2023, 12, 31))

    print(f"Overview for {symbol} up to 2023-12-31:")
    print(ticker_data.overview.model_dump_json(indent=2))

    print("\nEarnings:")
    for ann in ticker_data.earnings.annual_earnings[:1]:
        print(ann.model_dump_json(indent=2))
    for q in ticker_data.earnings.quarterly_earnings[:1]:
        print(q.model_dump_json(indent=2))

    print("\nCash Flow:")
    cf = ticker_data.cash_flow.annual_reports[0]
    print(cf.model_dump_json(indent=2))

    print("\nBalance Sheet:")
    bs = ticker_data.balance_sheet.annual_reports[0]
    print(bs.model_dump_json(indent=2))

    print("\nInsider Transactions:")
    for tx in ticker_data.insider_transactions.data[:3]:
        print(tx.model_dump_json(indent=2))
