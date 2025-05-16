from datetime import date
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class InsiderTransaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    # transaction date in date format
    transaction_date: date = Field(
        ...,
        alias="transactionDate",
        description="Date of the transaction",
    )
    # ticker: str = Field(..., alias="ticker", description="Ticker symbol")
    # executive: str = Field(..., alias="executive", description="Name of the executive")
    executive_title: str = Field(
        ...,
        alias="executiveTitle",
        description="Title of the executive",
    )
    security_type: str = Field(
        ...,
        alias="securityType",
        description="Type of the security",
    )
    acquisition_or_disposal: Literal["A", "D"] = Field(
        ...,
        alias="acquisitionOrDisposal",
        description="A for acquisition, D for disposal",
    )
    shares: float = Field(..., alias="shares", description="Number of shares")
    share_price: float = Field(..., alias="sharePrice", description="Share price")


class InsiderTransactionsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    data: List[InsiderTransaction] = Field(
        ...,
        alias="data",
        description="List of insider transactions",
    )
