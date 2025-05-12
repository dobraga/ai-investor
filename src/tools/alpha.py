from json import dumps
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from pydantic import ValidationError

from src.config.alpha import AlphaVantageConfig
from src.tools._alpha import (
    BalanceSheetResponse,
    CashFlowResponse,
    EarningsResponse,
    OverviewResponse,
    TickerData,
)
from src.utils.datetime import seconds_since_creation

logger = getLogger(__name__)


class AlphaVantageClient:
    """
    Client to fetch and parse financial data from Alpha Vantage.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(
        self,
        api_key: str = "demo",
        config: Optional[AlphaVantageConfig] = AlphaVantageConfig(),
    ):
        self.api_key = api_key
        self.config = config

    def get_ticker_data(self, symbol: str) -> TickerData:
        cache_file = None
        if self.config.cache_dir:
            cache_file = self.config.cache_dir / f"{symbol}.json"

        if (
            cache_file
            and cache_file.exists()
            and seconds_since_creation(cache_file) < self.config.cache_timeout
        ):
            logger.debug(f"Using cached data for {symbol}")
            return self.from_cache_file(cache_file)

        data = TickerData(
            overview=self.get_overview(symbol),
            balance_sheet=self.get_balance_sheet(symbol),
            cash_flow=self.get_cashflow(symbol),
            earnings=self.get_earnings(symbol),
        )
        if cache_file:
            data.to_json(cache_file)

        return data

    def _fetch(self, function: str, symbol: str) -> Dict[str, Any]:
        params = {"function": function, "symbol": symbol, "apikey": self.api_key}
        response = httpx.get(self.BASE_URL, params=params, timeout=self.config.timeout)
        response.raise_for_status()
        data = response.json()
        return data

    def get_overview(self, symbol: str) -> "OverviewResponse":
        try:
            data = self._fetch("OVERVIEW", symbol)
            return OverviewResponse(**data)
        except ValidationError as e:
            if self.config.cache_dir:
                cache_json = self.config.cache_dir / f"overview_{symbol}.json"
                cache_json.write_text(dumps(data, indent=2))
            raise RuntimeError(f"Overview data validation failed: {e.json(indent=2)}")

    def get_earnings(self, symbol: str) -> "EarningsResponse":
        try:
            data = self._fetch("EARNINGS", symbol)
            return EarningsResponse(**data)
        except ValidationError as e:
            if self.config.cache_dir:
                cache_json = self.config.cache_dir / f"earnings_{symbol}.json"
                cache_json.write_text(dumps(data, indent=2))
            raise RuntimeError(f"Earnings data validation failed: {e.json(indent=2)}")

    def get_cashflow(self, symbol: str) -> "CashFlowResponse":
        try:
            data = self._fetch("CASH_FLOW", symbol)
            return CashFlowResponse(**data)
        except ValidationError as e:
            if self.config.cache_dir:
                cache_json = self.config.cache_dir / f"cash_flow_{symbol}.json"
                cache_json.write_text(dumps(data, indent=2))
            raise RuntimeError(f"Cash flow data validation failed: {e.json(indent=2)}")

    def get_balance_sheet(self, symbol: str) -> "BalanceSheetResponse":
        try:
            data = self._fetch("BALANCE_SHEET", symbol)
            return BalanceSheetResponse(**data)
        except ValidationError as e:
            if self.config.cache_dir:
                cache_json = self.config.cache_dir / f"balance_sheet_{symbol}.json"
                cache_json.write_text(dumps(data, indent=2))
            raise RuntimeError(
                f"Balance sheet data validation failed: {e.json(indent=2)}"
            )

    def from_cache_file(self, cache_file: Path) -> None:
        return TickerData.from_json(cache_file.read_text())


if __name__ == "__main__":
    client = AlphaVantageClient()

    # Overview example
    print("Overview for IBM:")
    overview = client.get_overview("IBM")
    print(overview.model_dump_json(indent=2))

    # Earnings example
    print("\n\nAnnual and Quarterly Earnings for IBM:")
    earnings = client.get_earnings("IBM")
    for ann in earnings.annual_earnings[-1:]:
        print(ann.model_dump_json(indent=2))
    for q in earnings.quarterly_earnings[-1:]:
        print(f"  [Quarterly]\n{q.model_dump_json(indent=2)}")

    # Cash Flow example
    print("\n\nLatest Annual and Quarterly Cash Flow for IBM:")
    cashflow = client.get_cashflow("IBM")
    latest_cf = cashflow.annual_reports[-1]
    print(f"  [Annual]\n{latest_cf.model_dump_json(indent=2)}")
    if cashflow.quarterly_reports:
        latest_qf = cashflow.quarterly_reports[-1]
        print(f"  [Quarterly]\n{latest_qf.model_dump_json(indent=2)}")

    # Balance Sheet example
    print("\n\nLatest Annual and Quarterly Balance Sheet for IBM:")
    bs = client.get_balance_sheet("IBM")
    ar = bs.annual_reports[-1]
    print(f"  [Annual]\n{ar.model_dump_json(indent=2)}")
    if bs.quarterly_reports:
        qr = bs.quarterly_reports[-1]
        print(f"  [Quarterly]\n{qr.model_dump_json(indent=2)}")
