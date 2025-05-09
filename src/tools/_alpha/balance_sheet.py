from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._utils import convert_none_str_to_none


class AnnualBalanceSheetReport(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: str = Field(
        ...,
        alias="fiscalDateEnding",
        description="Date when the fiscal period ends, in YYYY-MM-DD format",
    )
    reported_currency: str = Field(
        ...,
        alias="reportedCurrency",
        description="Currency in which figures are reported",
    )
    accumulated_depreciation_amortization_ppe: Optional[float] = Field(
        None,
        alias="accumulatedDepreciationAmortizationPPE",
        description="Total accumulated depreciation and amortization of property, plant, and equipment",
    )
    capital_lease_obligations: Optional[float] = Field(
        None,
        alias="capitalLeaseObligations",
        description="Outstanding obligations under capital leases",
    )
    cash_and_cash_equivalents_at_carrying_value: Optional[float] = Field(
        None,
        alias="cashAndCashEquivalentsAtCarryingValue",
        description="Cash and cash equivalents at carrying value",
    )
    cash_and_short_term_investments: Optional[float] = Field(
        None,
        alias="cashAndShortTermInvestments",
        description="Cash and short-term investments",
    )
    common_stock: Optional[float] = Field(
        None, alias="commonStock", description="Value of common stock"
    )
    common_stock_shares_outstanding: Optional[float] = Field(
        None,
        alias="commonStockSharesOutstanding",
        description="Number of outstanding shares of common stock",
    )
    current_accounts_payable: Optional[float] = Field(
        None,
        alias="currentAccountsPayable",
        description="Accounts payable due within one year",
    )
    current_debt: Optional[float] = Field(
        None, alias="currentDebt", description="Total debt due within one year"
    )
    current_long_term_debt: Optional[float] = Field(
        None,
        alias="currentLongTermDebt",
        description="Portion of long-term debt due within one year",
    )
    current_net_receivables: Optional[float] = Field(
        None,
        alias="currentNetReceivables",
        description="Net receivables expected to be collected within one year",
    )
    deferred_revenue: Optional[float] = Field(
        None, alias="deferredRevenue", description="Revenue received but not yet earned"
    )
    goodwill: Optional[float] = Field(
        None, alias="goodwill", description="Goodwill recorded from acquisitions"
    )
    intangible_assets: Optional[float] = Field(
        None, alias="intangibleAssets", description="Total value of intangible assets"
    )
    intangible_assets_excluding_goodwill: Optional[float] = Field(
        None,
        alias="intangibleAssetsExcludingGoodwill",
        description="Intangible assets excluding goodwill",
    )
    inventory: Optional[float] = Field(
        None, alias="inventory", description="Value of inventory held"
    )
    investments: Optional[float] = Field(
        None, alias="investments", description="Value of investments"
    )
    long_term_debt: Optional[float] = Field(
        None, alias="longTermDebt", description="Total long-term debt"
    )
    long_term_debt_noncurrent: Optional[float] = Field(
        None,
        alias="longTermDebtNoncurrent",
        description="Long-term debt not due within one year",
    )
    long_term_investments: Optional[float] = Field(
        None,
        alias="longTermInvestments",
        description="Investments held for longer than one year",
    )
    other_current_assets: Optional[float] = Field(
        None, alias="otherCurrentAssets", description="Other current assets"
    )
    other_current_liabilities: Optional[float] = Field(
        None, alias="otherCurrentLiabilities", description="Other current liabilities"
    )
    other_non_current_assets: Optional[float] = Field(
        None, alias="otherNonCurrentAssets", description="Other non-current assets"
    )
    other_non_current_liabilities: Optional[float] = Field(
        None,
        alias="otherNonCurrentLiabilities",
        description="Other non-current liabilities",
    )
    property_plant_equipment: Optional[float] = Field(
        None,
        alias="propertyPlantEquipment",
        description="Value of property, plant, and equipment",
    )
    retained_earnings: Optional[float] = Field(
        None, alias="retainedEarnings", description="Accumulated retained earnings"
    )
    short_long_term_debt_total: Optional[float] = Field(
        None,
        alias="shortLongTermDebtTotal",
        description="Total of short and long-term debt",
    )
    short_term_debt: Optional[float] = Field(
        None, alias="shortTermDebt", description="Debt due within one year"
    )
    short_term_investments: Optional[float] = Field(
        None,
        alias="shortTermInvestments",
        description="Investments held for less than one year",
    )
    total_assets: Optional[float] = Field(
        None, alias="totalAssets", description="Total assets"
    )
    total_current_assets: Optional[float] = Field(
        None, alias="totalCurrentAssets", description="Total current assets"
    )
    total_current_liabilities: Optional[float] = Field(
        None, alias="totalCurrentLiabilities", description="Total current liabilities"
    )
    total_liabilities: Optional[float] = Field(
        None, alias="totalLiabilities", description="Total liabilities"
    )
    total_non_current_assets: Optional[float] = Field(
        None, alias="totalNonCurrentAssets", description="Total non-current assets"
    )
    total_non_current_liabilities: Optional[float] = Field(
        None,
        alias="totalNonCurrentLiabilities",
        description="Total non-current liabilities",
    )
    total_shareholder_equity: Optional[float] = Field(
        None, alias="totalShareholderEquity", description="Total shareholders' equity"
    )
    treasury_stock: Optional[float] = Field(
        None, alias="treasuryStock", description="Value of treasury stock"
    )

    @field_validator("*", mode="before")
    @classmethod
    def _normalize_and_convert(cls, v: Any) -> Any:
        return convert_none_str_to_none(v)


class QuarterlyBalanceSheetReport(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: str = Field(
        ...,
        alias="fiscalDateEnding",
        description="Date when the fiscal period ends, in YYYY-MM-DD format",
    )
    reported_currency: str = Field(
        ...,
        alias="reportedCurrency",
        description="Currency in which figures are reported",
    )
    accumulated_depreciation_amortization_ppe: Optional[float] = Field(
        None,
        alias="accumulatedDepreciationAmortizationPPE",
        description="Total accumulated depreciation and amortization of property, plant, and equipment",
    )
    capital_lease_obligations: Optional[float] = Field(
        None,
        alias="capitalLeaseObligations",
        description="Outstanding obligations under capital leases",
    )
    cash_and_cash_equivalents_at_carrying_value: Optional[float] = Field(
        None,
        alias="cashAndCashEquivalentsAtCarryingValue",
        description="Cash and cash equivalents at carrying value",
    )
    cash_and_short_term_investments: Optional[float] = Field(
        None,
        alias="cashAndShortTermInvestments",
        description="Cash and short-term investments",
    )
    common_stock: Optional[float] = Field(
        None, alias="commonStock", description="Value of common stock"
    )
    common_stock_shares_outstanding: Optional[float] = Field(
        None,
        alias="commonStockSharesOutstanding",
        description="Number of outstanding shares of common stock",
    )
    current_accounts_payable: Optional[float] = Field(
        None,
        alias="currentAccountsPayable",
        description="Accounts payable due within one year",
    )
    current_debt: Optional[float] = Field(
        None, alias="currentDebt", description="Total debt due within one year"
    )
    current_long_term_debt: Optional[float] = Field(
        None,
        alias="currentLongTermDebt",
        description="Portion of long-term debt due within one year",
    )
    current_net_receivables: Optional[float] = Field(
        None,
        alias="currentNetReceivables",
        description="Net receivables expected to be collected within one year",
    )
    deferred_revenue: Optional[float] = Field(
        None, alias="deferredRevenue", description="Revenue received but not yet earned"
    )
    goodwill: Optional[float] = Field(
        None, alias="goodwill", description="Goodwill recorded from acquisitions"
    )
    intangible_assets: Optional[float] = Field(
        None, alias="intangibleAssets", description="Total value of intangible assets"
    )
    intangible_assets_excluding_goodwill: Optional[float] = Field(
        None,
        alias="intangibleAssetsExcludingGoodwill",
        description="Intangible assets excluding goodwill",
    )
    inventory: Optional[float] = Field(
        None, alias="inventory", description="Value of inventory held"
    )
    investments: Optional[float] = Field(
        None, alias="investments", description="Value of investments"
    )
    long_term_debt: Optional[float] = Field(
        None, alias="longTermDebt", description="Total long-term debt"
    )
    long_term_debt_noncurrent: Optional[float] = Field(
        None,
        alias="longTermDebtNoncurrent",
        description="Long-term debt not due within one year",
    )
    long_term_investments: Optional[float] = Field(
        None,
        alias="longTermInvestments",
        description="Investments held for longer than one year",
    )
    other_current_assets: Optional[float] = Field(
        None, alias="otherCurrentAssets", description="Other current assets"
    )
    other_current_liabilities: Optional[float] = Field(
        None, alias="otherCurrentLiabilities", description="Other current liabilities"
    )
    other_non_current_assets: Optional[float] = Field(
        None, alias="otherNonCurrentAssets", description="Other non-current assets"
    )
    other_non_current_liabilities: Optional[float] = Field(
        None,
        alias="otherNonCurrentLiabilities",
        description="Other non-current liabilities",
    )
    property_plant_equipment: Optional[float] = Field(
        None,
        alias="propertyPlantEquipment",
        description="Value of property, plant, and equipment",
    )
    retained_earnings: Optional[float] = Field(
        None, alias="retainedEarnings", description="Accumulated retained earnings"
    )
    short_long_term_debt_total: Optional[float] = Field(
        None,
        alias="shortLongTermDebtTotal",
        description="Total of short and long-term debt",
    )
    short_term_debt: Optional[float] = Field(
        None, alias="shortTermDebt", description="Debt due within one year"
    )
    short_term_investments: Optional[float] = Field(
        None,
        alias="shortTermInvestments",
        description="Investments held for less than one year",
    )
    total_assets: Optional[float] = Field(
        None, alias="totalAssets", description="Total assets"
    )
    total_current_assets: Optional[float] = Field(
        None, alias="totalCurrentAssets", description="Total current assets"
    )
    total_current_liabilities: Optional[float] = Field(
        None, alias="totalCurrentLiabilities", description="Total current liabilities"
    )
    total_liabilities: Optional[float] = Field(
        None, alias="totalLiabilities", description="Total liabilities"
    )
    total_non_current_assets: Optional[float] = Field(
        None, alias="totalNonCurrentAssets", description="Total non-current assets"
    )
    total_non_current_liabilities: Optional[float] = Field(
        None,
        alias="totalNonCurrentLiabilities",
        description="Total non-current liabilities",
    )
    total_shareholder_equity: Optional[float] = Field(
        None, alias="totalShareholderEquity", description="Total shareholders' equity"
    )
    treasury_stock: Optional[float] = Field(
        None, alias="treasuryStock", description="Value of treasury stock"
    )

    @field_validator("*", mode="before")
    @classmethod
    def _normalize_and_convert(cls, v: Any) -> Any:
        return convert_none_str_to_none(v)


class BalanceSheetResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    annual_reports: List[AnnualBalanceSheetReport] = Field(
        ..., alias="annualReports", description="List of annual balance sheet reports"
    )
    quarterly_reports: List[QuarterlyBalanceSheetReport] = Field(
        ...,
        alias="quarterlyReports",
        description="List of quarterly balance sheet reports",
    )
