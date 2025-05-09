from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._utils import convert_none_str_to_none


class AnnualEarning(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: str = Field(
        ...,
        alias="fiscalDateEnding",
        description="Fiscal date ending in YYYY-MM-DD format",
    )
    reported_eps: float = Field(
        ..., alias="reportedEPS", description="Reported earnings per share"
    )


class QuarterlyEarning(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: str = Field(alias="fiscalDateEnding")
    reported_date: str = Field(alias="reportedDate")
    reported_eps: Optional[float] = Field(alias="reportedEPS")
    estimated_eps: Optional[float] = Field(alias="estimatedEPS")
    surprise: Optional[float] = Field(alias="surprise")
    surprise_percentage: Optional[float] = Field(alias="surprisePercentage")
    report_time: Literal["pre-market", "post-market"] = Field(alias="reportTime")

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

    annual_earnings: List[AnnualEarning] = Field(alias="annualEarnings")
    quarterly_earnings: List[QuarterlyEarning] = Field(alias="quarterlyEarnings")
