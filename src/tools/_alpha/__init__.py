from json import loads
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from .balance_sheet import BalanceSheetResponse
from .cash_flow import CashFlowResponse
from .earnings import EarningsResponse
from .insider import InsiderTransactionsResponse
from .overview import OverviewResponse

__all__ = ["TickerData", "BalanceSheetResponse", "CashFlowResponse", "EarningsResponse"]


class TickerData(BaseModel):
    overview: OverviewResponse = Field(
        description="Company basic information and description"
    )
    balance_sheet: BalanceSheetResponse = Field(
        description="Annual and quarterly balance sheet data"
    )
    cash_flow: CashFlowResponse = Field(
        description="Annual and quarterly cash flow statements"
    )
    earnings: EarningsResponse = Field(
        description="Annual and quarterly earnings reports"
    )
    insider_transactions: InsiderTransactionsResponse = Field(
        description="Recent insider trading activity"
    )

    def to_dict(self):
        return self.model_dump()

    def to_json(self, path: Optional[Path] = None):
        json = self.model_dump_json(indent=4)

        if not path:
            return json

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    @classmethod
    def from_json(cls, data: str):
        json_data = loads(data)
        return cls.from_dict(json_data)
