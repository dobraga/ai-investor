from logging import getLogger
from typing import Any, Dict

import httpx
from pydantic import ValidationError

from src.tools._alpha import (
    BalanceSheetResponse,
    CashFlowResponse,
    EarningsResponse,
    TickerData,
)

logger = getLogger(__name__)


class AlphaVantageClient:
    """
    Client to fetch and parse financial data from Alpha Vantage.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str = "demo", timeout: int = 10):
        self.api_key = api_key
        self.timeout = timeout
        self.memory: Dict[str, TickerData] = {}

    def get_ticker_data(self, symbol: str) -> TickerData:
        if symbol not in self.memory:
            logger.info(f"Fetching data for {symbol}")
            data = TickerData(
                symbol=symbol,
                balance_sheet=self.get_balance_sheet(symbol),
                cash_flow=self.get_cashflow(symbol),
                earnings=self.get_earnings(symbol),
            )
            self.memory[symbol] = data
 
        else:
            logger.info(f"Using cached data for {symbol}")
            data = self.memory[symbol]

        return data

    def _fetch(self, function: str, symbol: str) -> Dict[str, Any]:
        params = {"function": function, "symbol": symbol, "apikey": self.api_key}
        response = httpx.get(self.BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data

    def get_earnings(self, symbol: str) -> "EarningsResponse":
        try:
            data = self._fetch("EARNINGS", symbol)
            return EarningsResponse(**data)
        except ValidationError as e:
            raise RuntimeError(f"Earnings data validation failed: {e}")

    def get_cashflow(self, symbol: str) -> "CashFlowResponse":
        try:
            data = self._fetch("CASH_FLOW", symbol)
            return CashFlowResponse(**data)
        except ValidationError as e:
            raise RuntimeError(f"Cash flow data validation failed: {e}")

    def get_balance_sheet(self, symbol: str) -> "BalanceSheetResponse":
        try:
            data = self._fetch("BALANCE_SHEET", symbol)
            return BalanceSheetResponse(**data)
        except ValidationError as e:
            raise RuntimeError(f"Balance sheet data validation failed: {e}")


if __name__ == "__main__":
    client = AlphaVantageClient()

    # Earnings example
    print("Annual and Quarterly Earnings for IBM:")
    try:
        earnings = client.get_earnings("IBM")
        for ann in earnings.annualEarnings:
            print(f"  [Annual] {ann.fiscalDateEnding}: EPS = {ann.reportedEPS}")
        for q in earnings.quarterlyEarnings[:2]:
            print(
                f"  [Quarterly] {q.fiscalDateEnding}: EPS = {q.reportedEPS}, estimate = {q.estimatedEPS}"
            )
    except RuntimeError as e:
        print(f"API error fetching earnings: {e}")
    except ValidationError as e:
        print("Earnings validation error:")
        print(e.json())

    # Cash Flow example
    print("\nLatest Annual and Quarterly Cash Flow for IBM:")
    try:
        cashflow = client.get_cashflow("IBM")
        latest_cf = cashflow.annualReports[0]
        print(
            f"  [Annual] {latest_cf.fiscalDateEnding}: Operating CF = {latest_cf.operatingCashflow}, CapEx = {latest_cf.capitalExpenditures}"
        )
        if cashflow.quarterlyReports:
            latest_qf = cashflow.quarterlyReports[0]
            print(
                f"  [Quarterly] {latest_qf.fiscalDateEnding}: Operating CF = {latest_qf.operatingCashflow}, CapEx = {latest_qf.capitalExpenditures}"
            )
    except RuntimeError as e:
        print(f"API error fetching cash flow: {e}")
    except ValidationError as e:
        print("Cash Flow validation error:")
        print(e.json())

    # Balance Sheet example
    print("\nLatest Annual and Quarterly Balance Sheet for IBM:")
    try:
        bs = client.get_balance_sheet("IBM")
        ar = bs.annualReports[0]
        print(
            f"  [Annual] {ar.fiscalDateEnding}: Total Assets = {ar.totalAssets}, Total Liabilities = {ar.totalLiabilities}"
        )
        if bs.quarterlyReports:
            qr = bs.quarterlyReports[0]
            print(
                f"  [Quarterly] {qr.fiscalDateEnding}: Total Assets = {qr.totalAssets}, Total Liabilities = {qr.totalLiabilities}"
            )
    except RuntimeError as e:
        print(f"API error fetching balance sheet: {e}")
    except ValidationError as e:
        print("Balance Sheet validation error:")
        print(e.json())
