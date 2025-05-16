from datetime import date
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._utils import convert_none_str_to_none


class AnnualEarning(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: date = Field(
        ...,
        alias="fiscalDateEnding",
        description="Fiscal date ending in YYYY-MM-DD format",
    )
    reported_eps: float = Field(
        ...,
        alias="reportedEPS",
        description="Reported earnings per share",
    )


class QuarterlyEarning(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: date = Field(
        ...,
        alias="fiscalDateEnding",
        description="Fiscal date ending in YYYY-MM-DD format",
    )
    reported_date: date = Field(
        ..., alias="reportedDate", description="Date the earnings were reported"
    )
    reported_eps: Optional[float] = Field(
        None,
        alias="reportedEPS",
        description="Actual earnings per share reported",
    )
    estimated_eps: Optional[float] = Field(
        None,
        alias="estimatedEPS",
        description="Estimated earnings per share",
    )
    surprise: Optional[float] = Field(
        None,
        alias="surprise",
        description="Difference between reported EPS and estimated EPS",
    )
    surprise_percentage: Optional[float] = Field(
        None,
        alias="surprisePercentage",
        description="Percentage difference between reported EPS and estimate",
    )
    report_time: Literal["pre-market", "post-market"] = Field(
        ..., alias="reportTime", description="Time of day the earnings were reported"
    )

    @field_validator(
        "reported_eps",
        "estimated_eps",
        "surprise",
        "surprise_percentage",
        mode="before",
    )
    @classmethod
    def _normalize_none_strings(cls, v: Any) -> Any:
        return convert_none_str_to_none(v)


class EarningsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    annual_earnings: List[AnnualEarning] = Field(
        ..., alias="annualEarnings", description="List of annual earnings reports"
    )
    quarterly_earnings: List[QuarterlyEarning] = Field(
        ..., alias="quarterlyEarnings", description="List of quarterly earnings reports"
    )
