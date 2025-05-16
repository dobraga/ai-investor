import asyncio
from datetime import date
from logging import getLogger
from typing import Dict, Optional

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

logger = getLogger(__name__)


class AlphaVantageClient:
    """
    Client to fetch and parse financial data from Alpha Vantage,
    with centralized file-based caching, deduplication via per-symbol locks, and error handling.
    Supports filtering of reports by a provided end_date.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(
        self,
        api_key: str = "demo",
        config: Optional[AlphaVantageConfig] = AlphaVantageConfig(),
    ):
        self.api_key = api_key
        self.config = config
        self._locks: Dict[str, asyncio.Lock] = {}
        # Ensure top-level cache directory exists
        if self.config.cache_dir:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)

    async def aget_ticker_data(
        self,
        symbol: str,
        end_date: date = date.today(),
    ) -> TickerData:
        """
        Async method to fetch all ticker data concurrently and return a TickerData object.
        Checks cache before fetching; uses per-symbol lock to dedupe.
        Filters each report's fiscal_date_ending or transaction_date <= end_date.
        """
        # Top-level cache path (no end_date in filename)
        ticker_cache = None
        if self.config.cache_dir:
            ticker_cache = self.config.cache_dir / f"{symbol}.json"
            if (
                ticker_cache.exists()
                and seconds_since_creation(ticker_cache) < self.config.cache_timeout
            ):
                logger.debug(f"Using ticker_data cache for {symbol}")
                raw = ticker_cache.read_text()
                # load full dataset, then filter by end_date
                full = TickerData.model_validate_json(raw)
                return self._apply_filter(full, end_date)

        lock = self._locks.setdefault(symbol, asyncio.Lock())
        async with lock:
            if (
                ticker_cache
                and ticker_cache.exists()
                and seconds_since_creation(ticker_cache) < self.config.cache_timeout
            ):
                logger.debug(f"Using ticker_data cache for {symbol} after lock")
                full = TickerData.model_validate_json(ticker_cache.read_text())
                return self._apply_filter(full, end_date)

            # Fetch fresh data
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
                    *tasks.values(), return_exceptions=False
                )

            # assemble full data
            full = TickerData(
                overview=overview,
                balance_sheet=bs_resp,
                cash_flow=cf_resp,
                earnings=er_resp,
                insider_transactions=it_resp,
            )
            # Cache full data
            if ticker_cache:
                ticker_cache.write_text(full.model_dump_json(indent=2))
            # Return filtered by end_date
            return self._apply_filter(full, end_date)

    def get_ticker_data(
        self,
        symbol: str,
        end_date: date = date.today(),
    ) -> TickerData:
        """
        Synchronous wrapper around async aget_ticker_data, passing through end_date.
        """
        return asyncio.run(self.aget_ticker_data(symbol, end_date))

    def _apply_filter(self, data: TickerData, end_date: date) -> TickerData:
        """
        Internal helper to filter all report lists by end_date.
        """
        # Cash Flow
        data.cash_flow.annual_reports = [
            r for r in data.cash_flow.annual_reports if r.fiscal_date_ending <= end_date
        ]
        if data.cash_flow.quarterly_reports:
            data.cash_flow.quarterly_reports = [
                r
                for r in data.cash_flow.quarterly_reports
                if r.fiscal_date_ending <= end_date
            ]
        # Balance Sheet
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
        # Earnings
        data.earnings.annual_earnings = [
            r for r in data.earnings.annual_earnings if r.fiscal_date_ending <= end_date
        ]
        data.earnings.quarterly_earnings = [
            r
            for r in data.earnings.quarterly_earnings
            if r.fiscal_date_ending <= end_date
        ]
        # Insider Transactions
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
        """
        Internal fetch without caching; individual responses validated and returned.
        """
        logger.info(f"Fetching data for {symbol} {function}")
        response = await client.get(
            self.BASE_URL,
            params={"function": function, "symbol": symbol, "apikey": self.api_key},
        )
        response.raise_for_status()
        data = response.json()
        if "Information" in data:
            raise RuntimeError(data["Information"])
        try:
            return response_model(**data)
        except ValidationError as e:
            logger.error(f"Validation failed for {symbol} {function}: {e}")
            raise RuntimeError(f"{function} validation error: {e.json(indent=2)}")


if __name__ == "__main__":
    client = AlphaVantageClient(api_key="demo")
    symbol = "IBM"
    # Example: filter all data up to end of 2023
    ticker_data = client.get_ticker_data(symbol, end_date=date(2023, 12, 31))

    # Overview
    print(f"Overview for {symbol} up to 2023-12-31:")
    print(ticker_data.overview.model_dump_json(indent=2))

    # Earnings
    print("\nEarnings:")
    for ann in ticker_data.earnings.annual_earnings[:1]:
        print(ann.model_dump_json(indent=2))
    for q in ticker_data.earnings.quarterly_earnings[:1]:
        print(q.model_dump_json(indent=2))

    # Cash Flow
    print("\nCash Flow:")
    cf = ticker_data.cash_flow.annual_reports[0]
    print(cf.model_dump_json(indent=2))

    # Balance Sheet
    print("\nBalance Sheet:")
    bs = ticker_data.balance_sheet.annual_reports[0]
    print(bs.model_dump_json(indent=2))

    # Insider Transactions
    print("\nInsider Transactions:")
    for tx in ticker_data.insider_transactions.data[:3]:
        print(tx.model_dump_json(indent=2))
