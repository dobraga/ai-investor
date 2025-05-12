from json import loads
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from .balance_sheet import BalanceSheetResponse
from .cash_flow import CashFlowResponse
from .earnings import EarningsResponse
from .overview import OverviewResponse

__all__ = ["TickerData", "BalanceSheetResponse", "CashFlowResponse", "EarningsResponse"]


class TickerData(BaseModel):
    overview: OverviewResponse
    balance_sheet: BalanceSheetResponse
    cash_flow: CashFlowResponse
    earnings: EarningsResponse

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
