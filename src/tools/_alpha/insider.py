from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._utils import convert_none_str_to_none


class InsiderTransaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    # transaction date in date format
    transaction_date: Optional[date] = Field(
        ..., alias="transactionDate", description="Date of the transaction"
    )
    # ticker: str = Field(..., alias="ticker", description="Ticker symbol")
    # executive: str = Field(..., alias="executive", description="Name of the executive")
    executive_title: str = Field(
        ..., alias="executiveTitle", description="Title of the executive"
    )
    # security_type: str = Field(
    #     ..., alias="securityType", description="Type of the security"
    # )
    acquisition_or_disposal: Literal["A", "D"] = Field(
        ...,
        alias="acquisitionOrDisposal",
        description="A for acquisition, D for disposal",
    )
    shares: Optional[float] = Field(None, alias="shares")
    share_price: Optional[float] = Field(None, alias="sharePrice")

    @field_validator("shares", "share_price", "transaction_date", mode="before")
    @classmethod
    def _normalize_none_strings(cls, v):
        return convert_none_str_to_none(v)


class InsiderTransactionsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    data: List[InsiderTransaction] = Field(
        ..., alias="data", description="List of insider transactions"
    )

    @field_validator("data", mode="after")
    def _remove_without_date(cls, v):
        return [x for x in v if x.transaction_date is not None]
