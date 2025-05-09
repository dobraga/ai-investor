from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._utils import convert_none_str_to_none, convert_str_to_number


class AnnualCashFlowReport(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: str = Field(alias="fiscalDateEnding")
    reported_currency: str = Field(alias="reportedCurrency")
    capital_expenditures: Optional[float] = Field(alias="capitalExpenditures")
    cashflow_from_financing: Optional[float] = Field(alias="cashflowFromFinancing")
    cashflow_from_investment: Optional[float] = Field(alias="cashflowFromInvestment")
    change_in_cash_and_cash_equivalents: Optional[float] = Field(
        alias="changeInCashAndCashEquivalents"
    )
    change_in_exchange_rate: Optional[float] = Field(alias="changeInExchangeRate")
    change_in_inventory: Optional[float] = Field(alias="changeInInventory")
    change_in_operating_assets: Optional[float] = Field(alias="changeInOperatingAssets")
    change_in_operating_liabilities: Optional[float] = Field(
        alias="changeInOperatingLiabilities"
    )
    change_in_receivables: Optional[float] = Field(alias="changeInReceivables")
    depreciation_depletion_and_amortization: Optional[float] = Field(
        alias="depreciationDepletionAndAmortization"
    )
    dividend_payout: Optional[float] = Field(alias="dividendPayout")
    dividend_payout_common_stock: Optional[float] = Field(
        alias="dividendPayoutCommonStock"
    )
    dividend_payout_preferred_stock: Optional[float] = Field(
        alias="dividendPayoutPreferredStock"
    )
    net_income: Optional[float] = Field(alias="netIncome")
    operating_cashflow: Optional[float] = Field(alias="operatingCashflow")
    profit_loss: Optional[float] = Field(alias="profitLoss")

    @field_validator(
        "capital_expenditures",
        "cashflow_from_financing",
        "cashflow_from_investment",
        "change_in_cash_and_cash_equivalents",
        "change_in_exchange_rate",
        "change_in_inventory",
        "change_in_operating_assets",
        "change_in_operating_liabilities",
        "change_in_receivables",
        "depreciation_depletion_and_amortization",
        "dividend_payout",
        "dividend_payout_common_stock",
        "dividend_payout_preferred_stock",
        "net_income",
        "operating_cashflow",
        "profit_loss",
        mode="before",
    )
    @classmethod
    def _normalize_and_convert_numeric(cls, v: Any) -> Any:
        v = convert_none_str_to_none(v)
        return convert_str_to_number(v)


class QuarterlyCashFlowReport(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: str = Field(alias="fiscalDateEnding")
    reported_currency: str = Field(alias="reportedCurrency")
    capital_expenditures: Optional[float] = Field(alias="capitalExpenditures")
    cashflow_from_financing: Optional[float] = Field(alias="cashflowFromFinancing")
    cashflow_from_investment: Optional[float] = Field(alias="cashflowFromInvestment")
    change_in_cash_and_cash_equivalents: Optional[float] = Field(
        alias="changeInCashAndCashEquivalents"
    )
    change_in_exchange_rate: Optional[float] = Field(alias="changeInExchangeRate")
    change_in_inventory: Optional[float] = Field(alias="changeInInventory")
    change_in_operating_assets: Optional[float] = Field(alias="changeInOperatingAssets")
    change_in_operating_liabilities: Optional[float] = Field(
        alias="changeInOperatingLiabilities"
    )
    change_in_receivables: Optional[float] = Field(alias="changeInReceivables")
    depreciation_depletion_and_amortization: Optional[float] = Field(
        alias="depreciationDepletionAndAmortization"
    )
    dividend_payout: Optional[float] = Field(alias="dividendPayout")
    dividend_payout_common_stock: Optional[float] = Field(
        alias="dividendPayoutCommonStock"
    )
    dividend_payout_preferred_stock: Optional[float] = Field(
        alias="dividendPayoutPreferredStock"
    )
    net_income: Optional[float] = Field(alias="netIncome")
    operating_cashflow: Optional[float] = Field(alias="operatingCashflow")
    profit_loss: Optional[float] = Field(alias="profitLoss")

    @field_validator(
        "capital_expenditures",
        "cashflow_from_financing",
        "cashflow_from_investment",
        "change_in_cash_and_cash_equivalents",
        "change_in_exchange_rate",
        "change_in_inventory",
        "change_in_operating_assets",
        "change_in_operating_liabilities",
        "change_in_receivables",
        "depreciation_depletion_and_amortization",
        "dividend_payout",
        "dividend_payout_common_stock",
        "dividend_payout_preferred_stock",
        "net_income",
        "operating_cashflow",
        "profit_loss",
        mode="before",
    )
    @classmethod
    def _normalize_and_convert_numeric(cls, v: Any) -> Any:
        v = convert_none_str_to_none(v)
        return convert_str_to_number(v)


class CashFlowResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    annual_reports: List[AnnualCashFlowReport] = Field(alias="annualReports")
    quarterly_reports: Optional[List[QuarterlyCashFlowReport]] = Field(
        alias="quarterlyReports"
    )
