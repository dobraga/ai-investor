from typing import Any, List, Optional

from pydantic import BaseModel, field_validator

from ._utils import convert_none_str_to_none, convert_str_to_number


class AnnualCashFlowReport(BaseModel):
    fiscalDateEnding: str
    reportedCurrency: str
    capitalExpenditures: Optional[float]
    cashflowFromFinancing: Optional[float]
    cashflowFromInvestment: Optional[float]
    changeInCashAndCashEquivalents: Optional[float]
    changeInExchangeRate: Optional[float]
    changeInInventory: Optional[float]
    changeInOperatingAssets: Optional[float]
    changeInOperatingLiabilities: Optional[float]
    changeInReceivables: Optional[float]
    depreciationDepletionAndAmortization: Optional[float]
    dividendPayout: Optional[float]
    dividendPayoutCommonStock: Optional[float]
    dividendPayoutPreferredStock: Optional[float]
    netIncome: Optional[float]
    operatingCashflow: Optional[float]
    profitLoss: Optional[float]

    @field_validator(
        "capitalExpenditures",
        "cashflowFromFinancing",
        "cashflowFromInvestment",
        "changeInCashAndCashEquivalents",
        "changeInExchangeRate",
        "changeInInventory",
        "changeInOperatingAssets",
        "changeInOperatingLiabilities",
        "changeInReceivables",
        "depreciationDepletionAndAmortization",
        "dividendPayout",
        "dividendPayoutCommonStock",
        "dividendPayoutPreferredStock",
        "netIncome",
        "operatingCashflow",
        "profitLoss",
        mode="before",
    )
    @classmethod
    def _normalize_and_convert_numeric(cls, v: Any) -> Any:
        v = convert_none_str_to_none(v)
        return convert_str_to_number(v)


class QuarterlyCashFlowReport(BaseModel):
    fiscalDateEnding: str
    reportedCurrency: str
    capitalExpenditures: Optional[float]
    cashflowFromFinancing: Optional[float]
    cashflowFromInvestment: Optional[float]
    changeInCashAndCashEquivalents: Optional[float]
    changeInExchangeRate: Optional[float]
    changeInInventory: Optional[float]
    changeInOperatingAssets: Optional[float]
    changeInOperatingLiabilities: Optional[float]
    changeInReceivables: Optional[float]
    depreciationDepletionAndAmortization: Optional[float]
    dividendPayout: Optional[float]
    dividendPayoutCommonStock: Optional[float]
    dividendPayoutPreferredStock: Optional[float]
    netIncome: Optional[float]
    operatingCashflow: Optional[float]
    profitLoss: Optional[float]

    @field_validator(
        "capitalExpenditures",
        "cashflowFromFinancing",
        "cashflowFromInvestment",
        "changeInCashAndCashEquivalents",
        "changeInExchangeRate",
        "changeInInventory",
        "changeInOperatingAssets",
        "changeInOperatingLiabilities",
        "changeInReceivables",
        "depreciationDepletionAndAmortization",
        "dividendPayout",
        "dividendPayoutCommonStock",
        "dividendPayoutPreferredStock",
        "netIncome",
        "operatingCashflow",
        "profitLoss",
        mode="before",
    )
    @classmethod
    def _normalize_and_convert_numeric(cls, v: Any) -> Any:
        return convert_none_str_to_none(v)


class CashFlowResponse(BaseModel):
    annualReports: List[AnnualCashFlowReport]
    quarterlyReports: Optional[List[QuarterlyCashFlowReport]]
