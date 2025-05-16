from datetime import date
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._utils import convert_none_str_to_none, convert_str_to_number


class AnnualCashFlowReport(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: date = Field(
        alias="fiscalDateEnding",
        description="The end date of the fiscal period for the report.",
    )
    reported_currency: str = Field(
        alias="reportedCurrency",
        description="The currency in which the financial figures are reported.",
    )
    capital_expenditures: Optional[float] = Field(
        alias="capitalExpenditures",
        description="Funds used by the company to acquire or upgrade physical assets such as property, industrial buildings, or equipment.",
    )
    cashflow_from_financing: Optional[float] = Field(
        alias="cashflowFromFinancing",
        description="Net cash generated from financing activities, including debt issuance, equity issuance, and dividend payments.",
    )
    cashflow_from_investment: Optional[float] = Field(
        alias="cashflowFromInvestment",
        description="Net cash used in investing activities, such as the purchase or sale of assets and investments.",
    )
    change_in_cash_and_cash_equivalents: Optional[float] = Field(
        alias="changeInCashAndCashEquivalents",
        description="The net change in cash and cash equivalents over the reporting period.",
    )
    change_in_exchange_rate: Optional[float] = Field(
        alias="changeInExchangeRate",
        description="The effect of exchange rate changes on cash and cash equivalents.",
    )
    change_in_inventory: Optional[float] = Field(
        alias="changeInInventory",
        description="The net change in inventory levels during the reporting period.",
    )
    change_in_operating_assets: Optional[float] = Field(
        alias="changeInOperatingAssets",
        description="The net change in operating assets, excluding cash, during the reporting period.",
    )
    change_in_operating_liabilities: Optional[float] = Field(
        alias="changeInOperatingLiabilities",
        description="The net change in operating liabilities during the reporting period.",
    )
    change_in_receivables: Optional[float] = Field(
        alias="changeInReceivables",
        description="The net change in accounts receivable during the reporting period.",
    )
    depreciation_depletion_and_amortization: Optional[float] = Field(
        alias="depreciationDepletionAndAmortization",
        description="Non-cash expenses that reduce the value of the company's assets over time.",
    )
    dividend_payout: Optional[float] = Field(
        alias="dividendPayout",
        description="Total dividends paid to shareholders during the reporting period.",
    )
    dividend_payout_common_stock: Optional[float] = Field(
        alias="dividendPayoutCommonStock",
        description="Dividends paid to holders of common stock.",
    )
    dividend_payout_preferred_stock: Optional[float] = Field(
        alias="dividendPayoutPreferredStock",
        description="Dividends paid to holders of preferred stock.",
    )
    net_income: Optional[float] = Field(
        alias="netIncome",
        description="The company's total earnings, calculated as revenue minus expenses, taxes, and costs.",
    )
    operating_cashflow: Optional[float] = Field(
        alias="operatingCashflow",
        description="Cash generated from the company's core business operations.",
    )
    profit_loss: Optional[float] = Field(
        alias="profitLoss", description="Net profit or loss for the reporting period."
    )

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

    fiscal_date_ending: date = Field(
        alias="fiscalDateEnding",
        description="The end date of the fiscal quarter for the report.",
    )
    reported_currency: str = Field(
        alias="reportedCurrency",
        description="The currency in which the financial figures are reported.",
    )
    capital_expenditures: Optional[float] = Field(
        alias="capitalExpenditures",
        description="Funds used by the company to acquire or upgrade physical assets such as property, industrial buildings, or equipment.",
    )
    cashflow_from_financing: Optional[float] = Field(
        alias="cashflowFromFinancing",
        description="Net cash generated from financing activities, including debt issuance, equity issuance, and dividend payments.",
    )
    cashflow_from_investment: Optional[float] = Field(
        alias="cashflowFromInvestment",
        description="Net cash used in investing activities, such as the purchase or sale of assets and investments.",
    )
    change_in_cash_and_cash_equivalents: Optional[float] = Field(
        alias="changeInCashAndCashEquivalents",
        description="The net change in cash and cash equivalents over the reporting period.",
    )
    change_in_exchange_rate: Optional[float] = Field(
        alias="changeInExchangeRate",
        description="The effect of exchange rate changes on cash and cash equivalents.",
    )
    change_in_inventory: Optional[float] = Field(
        alias="changeInInventory",
        description="The net change in inventory levels during the reporting period.",
    )
    change_in_operating_assets: Optional[float] = Field(
        alias="changeInOperatingAssets",
        description="The net change in operating assets, excluding cash, during the reporting period.",
    )
    change_in_operating_liabilities: Optional[float] = Field(
        alias="changeInOperatingLiabilities",
        description="The net change in operating liabilities during the reporting period.",
    )
    change_in_receivables: Optional[float] = Field(
        alias="changeInReceivables",
        description="The net change in accounts receivable during the reporting period.",
    )
    depreciation_depletion_and_amortization: Optional[float] = Field(
        alias="depreciationDepletionAndAmortization",
        description="Non-cash expenses that reduce the value of the company's assets over time.",
    )
    dividend_payout: Optional[float] = Field(
        alias="dividendPayout",
        description="Total dividends paid to shareholders during the reporting period.",
    )
    dividend_payout_common_stock: Optional[float] = Field(
        alias="dividendPayoutCommonStock",
        description="Dividends paid to holders of common stock.",
    )
    dividend_payout_preferred_stock: Optional[float] = Field(
        alias="dividendPayoutPreferredStock",
        description="Dividends paid to holders of preferred stock.",
    )
    net_income: Optional[float] = Field(
        alias="netIncome",
        description="The company's total earnings, calculated as revenue minus expenses, taxes, and costs.",
    )
    operating_cashflow: Optional[float] = Field(
        alias="operatingCashflow",
        description="Cash generated from the company's core business operations.",
    )
    profit_loss: Optional[float] = Field(
        alias="profitLoss", description="Net profit or loss for the reporting period."
    )

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

    annual_reports: List[AnnualCashFlowReport] = Field(
        alias="annualReports", description="A list of annual cash flow reports."
    )
    quarterly_reports: Optional[List[QuarterlyCashFlowReport]] = Field(
        alias="quarterlyReports", description="A list of quarterly cash flow reports."
    )
