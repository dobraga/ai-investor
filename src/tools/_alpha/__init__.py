from pydantic import BaseModel

from .balance_sheet import BalanceSheetResponse
from .cash_flow import CashFlowResponse
from .earnings import EarningsResponse


class TickerData(BaseModel):
    symbol: str
    balance_sheet: BalanceSheetResponse
    cash_flow: CashFlowResponse
    earnings: EarningsResponse


__all__ = ["TickerData", "BalanceSheetResponse", "CashFlowResponse", "EarningsResponse"]
