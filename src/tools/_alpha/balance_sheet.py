from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._utils import convert_none_str_to_none


class AnnualBalanceSheetReport(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: str = Field(alias="fiscalDateEnding")
    reported_currency: str = Field(alias="reportedCurrency")
    accumulated_depreciation_amortization_ppe: Optional[float] = Field(
        alias="accumulatedDepreciationAmortizationPPE"
    )
    capital_lease_obligations: Optional[float] = Field(alias="capitalLeaseObligations")
    cash_and_cash_equivalents_at_carrying_value: Optional[float] = Field(
        alias="cashAndCashEquivalentsAtCarryingValue"
    )
    cash_and_short_term_investments: Optional[float] = Field(
        alias="cashAndShortTermInvestments"
    )
    common_stock: Optional[float] = Field(alias="commonStock")
    common_stock_shares_outstanding: Optional[float] = Field(
        alias="commonStockSharesOutstanding"
    )
    current_accounts_payable: Optional[float] = Field(alias="currentAccountsPayable")
    current_debt: Optional[float] = Field(alias="currentDebt")
    current_long_term_debt: Optional[float] = Field(alias="currentLongTermDebt")
    current_net_receivables: Optional[float] = Field(alias="currentNetReceivables")
    deferred_revenue: Optional[float] = Field(alias="deferredRevenue")
    goodwill: Optional[float] = Field(alias="goodwill")
    intangible_assets: Optional[float] = Field(alias="intangibleAssets")
    intangible_assets_excluding_goodwill: Optional[float] = Field(
        alias="intangibleAssetsExcludingGoodwill"
    )
    inventory: Optional[float] = Field(alias="inventory")
    investments: Optional[float] = Field(alias="investments")
    long_term_debt: Optional[float] = Field(alias="longTermDebt")
    long_term_debt_noncurrent: Optional[float] = Field(alias="longTermDebtNoncurrent")
    long_term_investments: Optional[float] = Field(alias="longTermInvestments")
    other_current_assets: Optional[float] = Field(alias="otherCurrentAssets")
    other_current_liabilities: Optional[float] = Field(alias="otherCurrentLiabilities")
    other_non_current_assets: Optional[float] = Field(alias="otherNonCurrentAssets")
    other_non_current_liabilities: Optional[float] = Field(
        alias="otherNonCurrentLiabilities"
    )
    property_plant_equipment: Optional[float] = Field(alias="propertyPlantEquipment")
    retained_earnings: Optional[float] = Field(alias="retainedEarnings")
    short_long_term_debt_total: Optional[float] = Field(alias="shortLongTermDebtTotal")
    short_term_debt: Optional[float] = Field(alias="shortTermDebt")
    short_term_investments: Optional[float] = Field(alias="shortTermInvestments")
    total_assets: Optional[float] = Field(alias="totalAssets")
    total_current_assets: Optional[float] = Field(alias="totalCurrentAssets")
    total_current_liabilities: Optional[float] = Field(alias="totalCurrentLiabilities")
    total_liabilities: Optional[float] = Field(alias="totalLiabilities")
    total_non_current_assets: Optional[float] = Field(alias="totalNonCurrentAssets")
    total_non_current_liabilities: Optional[float] = Field(
        alias="totalNonCurrentLiabilities"
    )
    total_shareholder_equity: Optional[float] = Field(alias="totalShareholderEquity")
    treasury_stock: Optional[float] = Field(alias="treasuryStock")

    @field_validator("*", mode="before")
    @classmethod
    def _normalize_and_convert(cls, v: Any) -> Any:
        return convert_none_str_to_none(v)


class QuarterlyBalanceSheetReport(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    fiscal_date_ending: str = Field(alias="fiscalDateEnding")
    reported_currency: str = Field(alias="reportedCurrency")
    accumulated_depreciation_amortization_ppe: Optional[float] = Field(
        alias="accumulatedDepreciationAmortizationPPE"
    )
    capital_lease_obligations: Optional[float] = Field(alias="capitalLeaseObligations")
    cash_and_cash_equivalents_at_carrying_value: Optional[float] = Field(
        alias="cashAndCashEquivalentsAtCarryingValue"
    )
    cash_and_short_term_investments: Optional[float] = Field(
        alias="cashAndShortTermInvestments"
    )
    common_stock: Optional[float] = Field(alias="commonStock")
    common_stock_shares_outstanding: Optional[float] = Field(
        alias="commonStockSharesOutstanding"
    )
    current_accounts_payable: Optional[float] = Field(alias="currentAccountsPayable")
    current_debt: Optional[float] = Field(alias="currentDebt")
    current_long_term_debt: Optional[float] = Field(alias="currentLongTermDebt")
    current_net_receivables: Optional[float] = Field(alias="currentNetReceivables")
    deferred_revenue: Optional[float] = Field(alias="deferredRevenue")
    goodwill: Optional[float] = Field(alias="goodwill")
    intangible_assets: Optional[float] = Field(alias="intangibleAssets")
    intangible_assets_excluding_goodwill: Optional[float] = Field(
        alias="intangibleAssetsExcludingGoodwill"
    )
    inventory: Optional[float] = Field(alias="inventory")
    investments: Optional[float] = Field(alias="investments")
    long_term_debt: Optional[float] = Field(alias="longTermDebt")
    long_term_debt_noncurrent: Optional[float] = Field(alias="longTermDebtNoncurrent")
    long_term_investments: Optional[float] = Field(alias="longTermInvestments")
    other_current_assets: Optional[float] = Field(alias="otherCurrentAssets")
    other_current_liabilities: Optional[float] = Field(alias="otherCurrentLiabilities")
    other_non_current_assets: Optional[float] = Field(alias="otherNonCurrentAssets")
    other_non_current_liabilities: Optional[float] = Field(
        alias="otherNonCurrentLiabilities"
    )
    property_plant_equipment: Optional[float] = Field(alias="propertyPlantEquipment")
    retained_earnings: Optional[float] = Field(alias="retainedEarnings")
    short_long_term_debt_total: Optional[float] = Field(alias="shortLongTermDebtTotal")
    short_term_debt: Optional[float] = Field(alias="shortTermDebt")
    short_term_investments: Optional[float] = Field(alias="shortTermInvestments")
    total_assets: Optional[float] = Field(alias="totalAssets")
    total_current_assets: Optional[float] = Field(alias="totalCurrentAssets")
    total_current_liabilities: Optional[float] = Field(alias="totalCurrentLiabilities")
    total_liabilities: Optional[float] = Field(alias="totalLiabilities")
    total_non_current_assets: Optional[float] = Field(alias="totalNonCurrentAssets")
    total_non_current_liabilities: Optional[float] = Field(
        alias="totalNonCurrentLiabilities"
    )
    total_shareholder_equity: Optional[float] = Field(alias="totalShareholderEquity")
    treasury_stock: Optional[float] = Field(alias="treasuryStock")

    @field_validator("*", mode="before")
    @classmethod
    def _normalize_and_convert(cls, v: Any) -> Any:
        return convert_none_str_to_none(v)


class BalanceSheetResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    annual_reports: List[AnnualBalanceSheetReport] = Field(alias="annualReports")
    quarterly_reports: List[QuarterlyBalanceSheetReport] = Field(
        alias="quarterlyReports"
    )
