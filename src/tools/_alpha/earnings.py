from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from ._utils import convert_none_str_to_none


class AnnualEarning(BaseModel):
    fiscalDateEnding: str = Field(
        ..., description="Fiscal date ending in YYYY-MM-DD format"
    )
    reportedEPS: float = Field(..., description="Reported earnings per share")


class QuarterlyEarning(BaseModel):
    fiscalDateEnding: str
    reportedDate: str
    reportedEPS: Optional[float]
    estimatedEPS: Optional[float]
    surprise: Optional[float]
    surprisePercentage: Optional[float]
    reportTime: Literal["pre-market", "post-market"]

    @field_validator(
        "reportedEPS", "estimatedEPS", "surprise", "surprisePercentage", mode="before"
    )
    @classmethod
    def _normalize_none_strings(cls, v: Any) -> Any:
        return convert_none_str_to_none(v)


class EarningsResponse(BaseModel):
    annualEarnings: List[AnnualEarning]
    quarterlyEarnings: List[QuarterlyEarning]
