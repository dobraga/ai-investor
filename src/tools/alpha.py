import asyncio
import json
from json import dumps
from logging import getLogger
from typing import Optional

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
    Client to fetch and parse financial data from Alpha Vantage, with centralized caching and error handling.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(
        self,
        api_key: str = "demo",
        config: Optional[AlphaVantageConfig] = AlphaVantageConfig(),
    ):
        self.api_key = api_key
        self.config = config
        # Initialize a persistent AsyncClient for all requests
        self.client = httpx.AsyncClient(timeout=self.config.timeout)

    async def aget_ticker_data(self, symbol: str) -> TickerData:
        """
        Async method to fetch all ticker data concurrently and return a TickerData object.
        """
        tasks = {
            "overview": self._fetch_and_validate("OVERVIEW", symbol, OverviewResponse),
            "balance_sheet": self._fetch_and_validate(
                "BALANCE_SHEET", symbol, BalanceSheetResponse
            ),
            "cash_flow": self._fetch_and_validate(
                "CASH_FLOW", symbol, CashFlowResponse
            ),
            "earnings": self._fetch_and_validate("EARNINGS", symbol, EarningsResponse),
            "insider_transactions": self._fetch_and_validate(
                "INSIDER_TRANSACTIONS", symbol, InsiderTransactionsResponse
            ),
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=False)
        return TickerData(
            overview=results[0],
            balance_sheet=results[1],
            cash_flow=results[2],
            earnings=results[3],
            insider_transactions=results[4],
        )

    def get_ticker_data(self, symbol: str) -> TickerData:
        """
        Synchronous wrapper around async aget_ticker_data for convenience.
        """
        return asyncio.run(self.aget_ticker_data(symbol))

    async def _fetch_and_validate(
        self,
        function: str,
        symbol: str,
        response_model: BaseModel,
    ) -> BaseModel:
        """
        Async fetch data from Alpha Vantage and validate with a Pydantic model.
        On validation errors, optionally cache the raw response for inspection.
        """
        # Determine cache paths
        cache_file = None
        if self.config.cache_dir:
            cache_dir = self.config.cache_dir / function
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / f"{symbol}.json"

        # Use existing cache if still fresh
        if (
            cache_file
            and cache_file.exists()
            and seconds_since_creation(cache_file) < self.config.cache_timeout
        ):
            logger.debug(f"Using cached data for {symbol} {function}")
            raw = cache_file.read_text()
            return (
                TickerData.from_json(raw)
                if response_model is TickerData
                else response_model(**json.loads(raw))
            )

        # Fetch remote data async
        response = await self.client.get(
            self.BASE_URL,
            params={"function": function, "symbol": symbol, "apikey": self.api_key},
        )
        response.raise_for_status()
        data = response.json()

        # Validate
        try:
            result = response_model(**data)
        except ValidationError as e:
            logger.error(f"Validation failed for {symbol} {function}: {e}")
            # Write raw JSON for debugging
            if self.config.cache_dir:
                debug_file = self.config.cache_dir / f"{function.lower()}_{symbol}.json"
                debug_file.write_text(dumps(data, indent=2))
            raise RuntimeError(f"{function} data validation failed: {e.json(indent=2)}")

        # Cache the successful raw response
        if cache_file:
            cache_file.write_text(dumps(data, indent=2))

        return result


if __name__ == "__main__":
    client = AlphaVantageClient()
    symbol = "IBM"

    # Fetch all data in one go
    ticker_data = client.get_ticker_data(symbol)

    # Earnings example
    print("\nAnnual and Quarterly Earnings:")
    for ann in ticker_data.earnings.annual_earnings[:1]:
        print(ann.model_dump_json(indent=2))
    for q in ticker_data.earnings.quarterly_earnings[:1]:
        print(f"  [Quarterly]\n{q.model_dump_json(indent=2)}")

    # Cash Flow example
    print("\nLatest Annual and Quarterly Cash Flow:")
    latest_cf = ticker_data.cash_flow.annual_reports[0]
    print(f"  [Annual]\n{latest_cf.model_dump_json(indent=2)}")
    if ticker_data.cash_flow.quarterly_reports:
        latest_qf = ticker_data.cash_flow.quarterly_reports[0]
        print(f"  [Quarterly]\n{latest_qf.model_dump_json(indent=2)}")

    # Balance Sheet example
    print("\nLatest Annual and Quarterly Balance Sheet:")
    latest_bs = ticker_data.balance_sheet.annual_reports[0]
    print(f"  [Annual]\n{latest_bs.model_dump_json(indent=2)}")
    if ticker_data.balance_sheet.quarterly_reports:
        latest_qb = ticker_data.balance_sheet.quarterly_reports[0]
        print(f"  [Quarterly]\n{latest_qb.model_dump_json(indent=2)}")

    # Insider Transactions example
    print("\nRecent Insider Transactions:")
    for tx in ticker_data.insider_transactions.data[:5]:
        print(tx.model_dump_json(indent=2))
