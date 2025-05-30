## Core Principles
1. Extract and calculate the principal metrics that *Ray Dalio* use to make investment decisions
2. The most recent data is the first element of all lists (chronologically ordered)
3. Only use information available in the TickerData structure
4. The Python function must receive TickerData as input and can accept additional configuration variables if needed for customization

## Required Outputs
1. **Metrics Documentation**: Complete listing of all metrics with descriptions explaining their significance in fundamental analysis in a json style
2. **Python Function**: Create `compute_metrics` function that extracts, calculates, and returns all fundamental analysis metrics in a structured dictionary format


## Expected JSON Documentation Format
A list of a json should include:
```json
{
    "id": <Name returned on python function>,
    "name": <Clear, descriptive name>,
    "formula": <Mathematical calculation method>,
    "interpretation": <How to read and understand the metric>,
    "significance": <Why this metric matters for investment decisions>,
    "benchmarks": <Typical good/bad ranges when applicable>,
    "limitations": <What the metric doesn't tell you>
}
```

### Quality Standards
- All calculations must be mathematically accurate
- Include error handling for edge cases
- Provide clear variable names and inline comments
- Ensure reproducible results
- Include data freshness indicators (fiscal date endings)

### Advanced Features
- Calculate percentile rankings where applicable
- Provide industry-relative context when possible
- Include confidence indicators for data quality
- Support both annual and quarterly analysis timeframes
- Generate composite scores for overall financial health

## Performance Considerations
- Optimize for computational efficiency
- Minimize redundant calculations
- Use vectorized operations where possible
- Cache intermediate results for complex calculations
- Ensure scalability for multiple ticker analysis


```python
class TickerData(BaseModel):
    overview: OverviewResponse = Field(
        description="Company basic information and description"
    )
    balance_sheet: BalanceSheetResponse = Field(
        description="Annual and quarterly balance sheet data"
    )
    cash_flow: CashFlowResponse = Field(
        description="Annual and quarterly cash flow statements"
    )
    earnings: EarningsResponse = Field(
        description="Annual and quarterly earnings reports"
    )
    insider_transactions: InsiderTransactionsResponse = Field(
        description="Recent insider trading activity"
    )

class OverviewResponse(BaseModel):
    asset_type: Optional[str] = Field(
        alias="AssetType", description="Type of the asset (e.g., Common Stock, ETF)"
    )
    description: Optional[str] = Field(
        alias="Description", description="Brief business summary or description"
    )


class AnnualBalanceSheetReport(BaseModel):
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


class QuarterlyBalanceSheetReport(BaseModel):
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

class BalanceSheetResponse(BaseModel):
    annual_reports: List[AnnualBalanceSheetReport] = Field(
        ..., alias="annualReports", description="List of annual balance sheet reports"
    )
    quarterly_reports: List[QuarterlyBalanceSheetReport] = Field(
        ...,
        alias="quarterlyReports",
        description="List of quarterly balance sheet reports",
    )


class AnnualCashFlowReport(BaseModel):
    fiscal_date_ending: str = Field(
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


class QuarterlyCashFlowReport(BaseModel):
    fiscal_date_ending: str = Field(
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


class CashFlowResponse(BaseModel):
    annual_reports: List[AnnualCashFlowReport] = Field(
        alias="annualReports", description="A list of annual cash flow reports."
    )
    quarterly_reports: Optional[List[QuarterlyCashFlowReport]] = Field(
        alias="quarterlyReports", description="A list of quarterly cash flow reports."
    )



class AnnualEarning(BaseModel):
    fiscal_date_ending: str = Field(
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
    fiscal_date_ending: str = Field(
        ...,
        alias="fiscalDateEnding",
        description="Fiscal date ending in YYYY-MM-DD format",
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


class EarningsResponse(BaseModel):
    annual_earnings: List[AnnualEarning] = Field(
        ..., alias="annualEarnings", description="List of annual earnings reports"
    )
    quarterly_earnings: List[QuarterlyEarning] = Field(
        ..., alias="quarterlyEarnings", description="List of quarterly earnings reports"
    )

class InsiderTransaction(BaseModel):
    transaction_date: date = Field(
        ...,
        alias="transactionDate",
        description="Date of the transaction",
    )
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
    data: List[InsiderTransaction] = Field(
        ...,
        alias="data",
        description="List of insider transactions",
    )
```
