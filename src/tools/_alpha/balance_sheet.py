from typing import Any, List, Optional

from pydantic import BaseModel, field_validator

from ._utils import convert_none_str_to_none


class AnnualBalanceSheetReport(BaseModel):
    fiscalDateEnding: str
    reportedCurrency: str
    accumulatedDepreciationAmortizationPPE: Optional[float]
    capitalLeaseObligations: Optional[float]
    cashAndCashEquivalentsAtCarryingValue: Optional[float]
    cashAndShortTermInvestments: Optional[float]
    commonStock: Optional[float]
    commonStockSharesOutstanding: Optional[float]
    currentAccountsPayable: Optional[float]
    currentDebt: Optional[float]
    currentLongTermDebt: Optional[float]
    currentNetReceivables: Optional[float]
    deferredRevenue: Optional[float]
    goodwill: Optional[float]
    intangibleAssets: Optional[float]
    intangibleAssetsExcludingGoodwill: Optional[float]
    inventory: Optional[float]
    investments: Optional[float]
    longTermDebt: Optional[float]
    longTermDebtNoncurrent: Optional[float]
    longTermInvestments: Optional[float]
    otherCurrentAssets: Optional[float]
    otherCurrentLiabilities: Optional[float]
    otherNonCurrentAssets: Optional[float]
    otherNonCurrentLiabilities: Optional[float]
    propertyPlantEquipment: Optional[float]
    retainedEarnings: Optional[float]
    shortLongTermDebtTotal: Optional[float]
    shortTermDebt: Optional[float]
    shortTermInvestments: Optional[float]
    totalAssets: Optional[float]
    totalCurrentAssets: Optional[float]
    totalCurrentLiabilities: Optional[float]
    totalLiabilities: Optional[float]
    totalNonCurrentAssets: Optional[float]
    totalNonCurrentLiabilities: Optional[float]
    totalShareholderEquity: Optional[float]
    treasuryStock: Optional[float]

    @field_validator("*", mode="before")
    @classmethod
    def _normalize_and_convert(cls, v: Any) -> Any:
        return convert_none_str_to_none(v)


class QuarterlyBalanceSheetReport(BaseModel):
    fiscalDateEnding: str
    reportedCurrency: str
    accumulatedDepreciationAmortizationPPE: Optional[float]
    capitalLeaseObligations: Optional[float]
    cashAndCashEquivalentsAtCarryingValue: Optional[float]
    cashAndShortTermInvestments: Optional[float]
    commonStock: Optional[float]
    commonStockSharesOutstanding: Optional[float]
    currentAccountsPayable: Optional[float]
    currentDebt: Optional[float]
    currentLongTermDebt: Optional[float]
    currentNetReceivables: Optional[float]
    deferredRevenue: Optional[float]
    goodwill: Optional[float]
    intangibleAssets: Optional[float]
    intangibleAssetsExcludingGoodwill: Optional[float]
    inventory: Optional[float]
    investments: Optional[float]
    longTermDebt: Optional[float]
    longTermDebtNoncurrent: Optional[float]
    longTermInvestments: Optional[float]
    otherCurrentAssets: Optional[float]
    otherCurrentLiabilities: Optional[float]
    otherNonCurrentAssets: Optional[float]
    otherNonCurrentLiabilities: Optional[float]
    propertyPlantEquipment: Optional[float]
    retainedEarnings: Optional[float]
    shortLongTermDebtTotal: Optional[float]
    shortTermDebt: Optional[float]
    shortTermInvestments: Optional[float]
    totalAssets: Optional[float]
    totalCurrentAssets: Optional[float]
    totalCurrentLiabilities: Optional[float]
    totalLiabilities: Optional[float]
    totalNonCurrentAssets: Optional[float]
    totalNonCurrentLiabilities: Optional[float]
    totalShareholderEquity: Optional[float]
    treasuryStock: Optional[float]

    @field_validator("*", mode="before")
    @classmethod
    def _normalize_and_convert(cls, v: Any) -> Any:
        return convert_none_str_to_none(v)


class BalanceSheetResponse(BaseModel):
    annualReports: List[AnnualBalanceSheetReport]
    quarterlyReports: List[QuarterlyBalanceSheetReport]
