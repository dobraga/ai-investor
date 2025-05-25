import statistics
from datetime import date, datetime
from logging import getLogger
from pathlib import Path
from typing import Dict, List

from llama_index.core.workflow import Context

from src.agents._signal import SignalEvent
from src.tools import AlphaVantageClient
from src.utils.format import id_to_name

from ._utils import generate_output

ID = Path(__file__).stem
NAME = id_to_name(ID)
LOG = getLogger(__name__)


async def ray_dalio_agent(context: Context):
    ticker: str = await context.get("ticker")

    LOG.info(f"Running {NAME} agent {ticker}")
    llm = await context.get("llm_struct")
    client: AlphaVantageClient = await context.get("alpha_client")

    data = await client.aget_ticker_data(ticker)

    metrics = compute_metrics(data)
    analysis = generate_output(llm, metrics, PROMPT, NAME)

    LOG.info(f"Finished {NAME} agent {ticker}")

    return analysis


def compute_metrics(
    ticker_data, use_quarterly: bool = False, lookback_periods: int = 4
) -> Dict:
    """
    Compute comprehensive fundamental analysis metrics based on Ray Dalio's investment principles.

    Args:
        ticker_data: TickerData object containing financial information
        use_quarterly: Whether to use quarterly data (True) or annual data (False)
        lookback_periods: Number of periods to analyze for trends and averages

    Returns:
        Dictionary containing all calculated metrics with data freshness indicators
    """

    # Helper function to safely get numeric values
    def safe_float(value, default=0.0):
        if value is None or value == "None":
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    # Helper function to calculate percentile rankings
    def calculate_percentile(values: List[float], target_value: float) -> float:
        if not values or target_value is None:
            return 50.0  # Default to median if no data
        sorted_vals = sorted([v for v in values if v is not None])
        if not sorted_vals:
            return 50.0
        rank = sum(1 for v in sorted_vals if v < target_value)
        return (rank / len(sorted_vals)) * 100

    # Select data source based on use_quarterly flag
    if use_quarterly and ticker_data.balance_sheet.quarterly_reports:
        balance_reports = ticker_data.balance_sheet.quarterly_reports[:lookback_periods]
        cash_flow_reports = (
            ticker_data.cash_flow.quarterly_reports[:lookback_periods]
            if ticker_data.cash_flow.quarterly_reports
            else []
        )
        earnings_reports = ticker_data.earnings.quarterly_earnings[:lookback_periods]
    else:
        balance_reports = ticker_data.balance_sheet.annual_reports[:lookback_periods]
        cash_flow_reports = ticker_data.cash_flow.annual_reports[:lookback_periods]
        earnings_reports = ticker_data.earnings.annual_earnings[:lookback_periods]

    if not balance_reports:
        raise ValueError("No financial data available for analysis")

    # Get most recent data
    latest_balance = balance_reports[0]
    latest_cash_flow = cash_flow_reports[0] if cash_flow_reports else None

    # Extract key financial values with safe conversion
    total_assets = safe_float(latest_balance.total_assets)
    total_current_assets = safe_float(latest_balance.total_current_assets)
    total_current_liabilities = safe_float(latest_balance.total_current_liabilities)
    total_liabilities = safe_float(latest_balance.total_liabilities)
    total_shareholder_equity = safe_float(latest_balance.total_shareholder_equity)
    cash_and_equivalents = safe_float(
        latest_balance.cash_and_cash_equivalents_at_carrying_value
    )
    inventory = safe_float(latest_balance.inventory)
    shares_outstanding = safe_float(latest_balance.common_stock_shares_outstanding)
    intangible_assets = safe_float(latest_balance.intangible_assets)

    # Calculate total debt (combination of short and long-term debt)
    short_term_debt = safe_float(latest_balance.short_term_debt)
    long_term_debt = safe_float(latest_balance.long_term_debt)
    current_debt = safe_float(latest_balance.current_debt)
    long_term_debt_noncurrent = safe_float(latest_balance.long_term_debt_noncurrent)

    # Use the most comprehensive debt measure available
    total_debt = max(
        safe_float(latest_balance.short_long_term_debt_total),
        short_term_debt + long_term_debt,
        current_debt + long_term_debt_noncurrent,
    )

    # Cash flow data
    net_income = safe_float(latest_cash_flow.net_income) if latest_cash_flow else 0
    operating_cash_flow = (
        safe_float(latest_cash_flow.operating_cashflow) if latest_cash_flow else 0
    )
    capital_expenditures = (
        safe_float(latest_cash_flow.capital_expenditures) if latest_cash_flow else 0
    )

    # Initialize metrics dictionary
    metrics = {}

    # === LIQUIDITY RATIOS ===

    # Current Ratio
    if total_current_liabilities > 0:
        metrics["current_ratio"] = total_current_assets / total_current_liabilities
    else:
        metrics["current_ratio"] = float("inf") if total_current_assets > 0 else 0

    # Quick Ratio (Acid Test)
    quick_assets = total_current_assets - inventory
    if total_current_liabilities > 0:
        metrics["quick_ratio"] = quick_assets / total_current_liabilities
    else:
        metrics["quick_ratio"] = float("inf") if quick_assets > 0 else 0

    # Cash Ratio
    if total_current_liabilities > 0:
        metrics["cash_ratio"] = cash_and_equivalents / total_current_liabilities
    else:
        metrics["cash_ratio"] = float("inf") if cash_and_equivalents > 0 else 0

    # Working Capital
    metrics["working_capital"] = total_current_assets - total_current_liabilities

    # Working Capital Ratio
    if total_assets > 0:
        metrics["working_capital_ratio"] = metrics["working_capital"] / total_assets
    else:
        metrics["working_capital_ratio"] = 0

    # === LEVERAGE RATIOS ===

    # Debt-to-Equity Ratio
    if total_shareholder_equity > 0:
        metrics["debt_to_equity"] = total_debt / total_shareholder_equity
    else:
        metrics["debt_to_equity"] = float("inf") if total_debt > 0 else 0

    # Debt-to-Assets Ratio
    if total_assets > 0:
        metrics["debt_to_assets"] = total_debt / total_assets
    else:
        metrics["debt_to_assets"] = 0

    # Equity Multiplier
    if total_shareholder_equity > 0:
        metrics["equity_multiplier"] = total_assets / total_shareholder_equity
    else:
        metrics["equity_multiplier"] = float("inf") if total_assets > 0 else 0

    # Interest Coverage Ratio (estimated)
    estimated_interest_expense = total_debt * 0.05  # Assume 5% average interest rate
    if estimated_interest_expense > 0:
        metrics["interest_coverage_ratio"] = (
            operating_cash_flow / estimated_interest_expense
        )
    else:
        metrics["interest_coverage_ratio"] = (
            float("inf") if operating_cash_flow > 0 else 0
        )

    # === PROFITABILITY RATIOS ===

    # Return on Equity (ROE)
    if total_shareholder_equity > 0:
        metrics["roe"] = net_income / total_shareholder_equity
    else:
        metrics["roe"] = 0

    # Return on Assets (ROA)
    if total_assets > 0:
        metrics["roa"] = net_income / total_assets
    else:
        metrics["roa"] = 0

    # Estimate revenue from net income (conservative approach using 10% margin assumption)
    estimated_revenue = net_income / 0.10 if net_income > 0 else 0

    # Asset Turnover
    if total_assets > 0 and estimated_revenue > 0:
        metrics["asset_turnover"] = estimated_revenue / total_assets
    else:
        metrics["asset_turnover"] = 0

    # Operating Margin (Proxy)
    if estimated_revenue > 0:
        metrics["operating_margin_proxy"] = operating_cash_flow / estimated_revenue
    else:
        metrics["operating_margin_proxy"] = 0

    # === PER-SHARE METRICS ===

    if shares_outstanding > 0:
        # Tangible Book Value per Share
        tangible_equity = total_shareholder_equity - intangible_assets
        metrics["tangible_book_value_per_share"] = tangible_equity / shares_outstanding

        # Cash per Share
        metrics["cash_per_share"] = cash_and_equivalents / shares_outstanding
    else:
        metrics["tangible_book_value_per_share"] = 0
        metrics["cash_per_share"] = 0

    # === CASH FLOW METRICS ===

    # Free Cash Flow (Proxy)
    metrics["free_cash_flow_proxy"] = operating_cash_flow - abs(capital_expenditures)

    # === EARNINGS QUALITY METRICS ===

    # Earnings Surprise Consistency
    if earnings_reports and len(earnings_reports) > 1:
        if hasattr(earnings_reports[0], "surprise_percentage"):  # Quarterly data
            surprises = [
                safe_float(e.surprise_percentage)
                for e in earnings_reports
                if hasattr(e, "surprise_percentage")
                and e.surprise_percentage is not None
            ]
        else:
            surprises = []

        if len(surprises) > 1:
            metrics["earnings_surprise_consistency"] = statistics.stdev(surprises)
        else:
            metrics["earnings_surprise_consistency"] = 0
    else:
        metrics["earnings_surprise_consistency"] = 0

    # === INSIDER TRADING ANALYSIS ===

    insider_signal = 0
    if ticker_data.insider_transactions and ticker_data.insider_transactions.data:
        for transaction in ticker_data.insider_transactions.data[
            :20
        ]:  # Last 20 transactions
            shares = safe_float(transaction.shares)
            if transaction.acquisition_or_disposal == "A":  # Acquisition
                insider_signal += shares
            else:  # Disposal
                insider_signal -= shares

    metrics["insider_trading_signal"] = insider_signal

    # === COMPOSITE SCORES ===

    # Financial Strength Score (weighted composite)
    def normalize_ratio(value, optimal_range, reverse=False):
        """Normalize ratio to 0-100 scale"""
        if value is None or value == float("inf") or value == float("-inf"):
            return 0

        min_val, max_val = optimal_range
        if reverse:
            if value <= min_val:
                return 100
            elif value >= max_val:
                return 0
            else:
                return 100 * (max_val - value) / (max_val - min_val)
        else:
            if value <= min_val:
                return 0
            elif value >= max_val:
                return 100
            else:
                return 100 * (value - min_val) / (max_val - min_val)

    # Normalize key ratios for composite score
    current_ratio_score = normalize_ratio(metrics["current_ratio"], (1.0, 3.0))
    debt_equity_score = normalize_ratio(
        metrics["debt_to_equity"], (0.0, 0.6), reverse=True
    )
    roe_score = normalize_ratio(metrics["roe"], (0.05, 0.20))
    cash_ratio_score = normalize_ratio(metrics["cash_ratio"], (0.1, 0.5))
    interest_coverage_score = normalize_ratio(
        metrics["interest_coverage_ratio"]
        if metrics["interest_coverage_ratio"] != float("inf")
        else 10,
        (2.0, 10.0),
    )

    # Weighted composite score
    weights = {
        "current_ratio": 0.20,
        "debt_equity": 0.25,
        "roe": 0.20,
        "cash_ratio": 0.15,
        "interest_coverage": 0.20,
    }

    metrics["financial_strength_score"] = (
        weights["current_ratio"] * current_ratio_score
        + weights["debt_equity"] * debt_equity_score
        + weights["roe"] * roe_score
        + weights["cash_ratio"] * cash_ratio_score
        + weights["interest_coverage"] * interest_coverage_score
    )

    # === DATA FRESHNESS INDICATORS ===

    try:
        latest_date = latest_balance.fiscal_date_ending.date()
        today = date.today()
        days_since_report = (today - latest_date).days
        metrics["data_freshness_score"] = days_since_report / 365.0
    except Exception as e:
        metrics["data_freshness_score"] = 1.0  # Assume 1 year old if parsing fails
        LOG.error(e)

    # === HISTORICAL TRENDS ===

    if len(balance_reports) > 1:
        # Calculate trend indicators for key metrics
        asset_growth_rates = []
        roe_values = []
        debt_equity_values = []

        for i in range(min(len(balance_reports), lookback_periods)):
            report = balance_reports[i]
            assets = safe_float(report.total_assets)
            equity = safe_float(report.total_shareholder_equity)
            debt = max(
                safe_float(report.short_long_term_debt_total),
                safe_float(report.short_term_debt, 0)
                + safe_float(report.long_term_debt, 0),
            )

            if (
                i > 0
                and assets > 0
                and safe_float(balance_reports[i - 1].total_assets) > 0
            ):
                prev_assets = safe_float(balance_reports[i - 1].total_assets)
                growth_rate = (
                    prev_assets - assets
                ) / assets  # Note: reversed because data is chronological
                asset_growth_rates.append(growth_rate)

            # ROE calculation for historical periods
            if equity > 0 and len(cash_flow_reports) > i:
                hist_income = safe_float(cash_flow_reports[i].net_income)
                roe_values.append(hist_income / equity)

            # Debt-to-equity historical
            if equity > 0:
                debt_equity_values.append(debt / equity)

        # Add trend metrics
        if asset_growth_rates:
            metrics["asset_growth_trend"] = statistics.mean(asset_growth_rates)
        if roe_values:
            metrics["roe_stability"] = (
                statistics.stdev(roe_values) if len(roe_values) > 1 else 0
            )
        if debt_equity_values:
            metrics["leverage_trend"] = statistics.mean(debt_equity_values)

    # === RISK INDICATORS ===

    # High leverage warning
    metrics["high_leverage_warning"] = (
        metrics["debt_to_equity"] > 1.0
        or metrics["debt_to_assets"] > 0.6
        or metrics["current_ratio"] < 1.0
    )

    # Liquidity stress indicator
    metrics["liquidity_stress_indicator"] = (
        metrics["current_ratio"] < 1.2
        and metrics["quick_ratio"] < 1.0
        and metrics["cash_ratio"] < 0.1
    )

    # === METADATA ===

    metrics["analysis_date"] = datetime.now().isoformat()
    metrics["data_source"] = "quarterly" if use_quarterly else "annual"
    metrics["periods_analyzed"] = min(len(balance_reports), lookback_periods)
    metrics["fiscal_date_ending"] = latest_balance.fiscal_date_ending
    metrics["reported_currency"] = latest_balance.reported_currency

    # Round all float values to 4 decimal places for readability
    for key, value in metrics.items():
        if isinstance(value, float) and not (
            value == float("inf") or value == float("-inf")
        ):
            metrics[key] = round(value, 4)

    return metrics


PROMPT = """
You are a specialized AI financial analyst embodying the investment philosophy and analytical rigor of Ray Dalio. Your primary focus is to identify companies that exhibit exceptional financial health, resilience to economic downturns, and consistent, predictable performance, aligning with Dalio's principles of risk mitigation and long-term value creation.

Your analytical process will consist of two stages:

### Stage 1: Pre-computation/Pre-analysis Setup

In this stage, you will internalize the fundamental metrics and their associated "Decision Rules" as follows:

* **Current Ratio**
    * **Formula:** Total Current Assets / Total Current Liabilities
    * **Interpretation:** Measures company's ability to pay short-term obligations. Higher is generally better.
    * **Significance:** Critical for assessing liquidity risk and operational efficiency. Dalio emphasizes companies that can weather economic storms.
    * **Benchmarks:** 1.5-3.0 is typically healthy; <1.0 indicates potential liquidity issues; >3.0 may suggest inefficient asset use
    * **Limitations:** Doesn't consider quality of current assets or timing of cash flows
    * **Decision Rule:** Prefer companies with a current ratio of 1.5 or higher, ideally between 1.5 and 3.0, to ensure strong short-term liquidity. Avoid companies with a ratio below 1.0.

* **Quick Ratio (Acid Test)**
    * **Formula:** (Current Assets - Inventory) / Current Liabilities
    * **Interpretation:** More conservative liquidity measure excluding inventory. Higher indicates better immediate liquidity.
    * **Significance:** Dalio values companies with strong immediate liquidity to handle unexpected downturns without fire sales.
    * **Benchmarks:** 1.0+ is healthy; 0.5-1.0 requires monitoring; <0.5 indicates liquidity stress
    * **Limitations:** May not reflect seasonal business patterns or rapid inventory turnover
    * **Decision Rule:** Seek companies with a quick ratio of 1.0 or higher for robust immediate liquidity. Ratios below 0.5 are a significant red flag.

* **Debt-to-Equity Ratio**
    * **Formula:** Total Debt / Total Shareholder Equity
    * **Interpretation:** Measures financial leverage. Lower ratios indicate less financial risk.
    * **Significance:** Central to Dalio's risk assessment - highly leveraged companies are vulnerable during economic contractions.
    * **Benchmarks:** <0.3 is conservative; 0.3-0.6 is moderate; >1.0 indicates high leverage risk
    * **Limitations:** Doesn't account for debt quality, interest rates, or cash flow coverage
    * **Decision Rule:** Favor companies with a debt-to-equity ratio below 0.6, ideally below 0.3, to minimize financial leverage and risk. Avoid companies with ratios above 1.0.

* **Debt-to-Assets Ratio**
    * **Formula:** Total Debt / Total Assets
    * **Interpretation:** Shows what proportion of assets are financed by debt. Lower is typically better.
    * **Significance:** Dalio uses this to assess financial stability and bankruptcy risk during economic stress.
    * **Benchmarks:** <0.3 is strong; 0.3-0.5 is moderate; >0.6 indicates high financial leverage
    * **Limitations:** Asset values may not reflect market reality; doesn't consider asset quality
    * **Decision Rule:** Prioritize companies with a debt-to-assets ratio below 0.5, preferably below 0.3, for enhanced financial stability and reduced bankruptcy risk.

* **Interest Coverage Ratio**
    * **Formula:** Operating Cash Flow / Interest Expense (estimated as 5% of total debt)
    * **Interpretation:** Measures ability to pay interest on debt. Higher ratios indicate better debt service capability.
    * **Significance:** Critical for Dalio's debt sustainability analysis - companies must service debt through economic cycles.
    * **Benchmarks:** >5x is strong; 2-5x is adequate; <2x indicates potential distress
    * **Limitations:** Uses estimated interest expense; doesn't reflect varying interest rate environments
    * **Decision Rule:** Investigate companies with an interest coverage ratio greater than 5x to ensure strong debt service capability. Ratios below 2x signal potential distress.

* **Return on Equity (ROE)**
    * **Formula:** Net Income / Average Shareholder Equity
    * **Interpretation:** Measures profitability relative to shareholder investment. Higher indicates better returns.
    * **Significance:** Dalio seeks companies that consistently generate superior returns on invested capital.
    * **Benchmarks:** >15% is excellent; 10-15% is good; <10% may indicate inefficient capital use
    * **Limitations:** Can be inflated by high leverage; doesn't reflect risk or sustainability
    * **Decision Rule:** Target companies with an ROE consistently above 15% to identify strong, consistent returns on invested capital.

* **Return on Assets (ROA)**
    * **Formula:** Net Income / Average Total Assets
    * **Interpretation:** Measures how efficiently assets generate profit. Higher indicates better asset utilization.
    * **Significance:** Dalio values efficient asset utilization as a sign of quality management and competitive advantage.
    * **Benchmarks:** >5% is strong; 2-5% is adequate; <2% suggests poor asset efficiency
    * **Limitations:** Asset book values may not reflect current market values
    * **Decision Rule:** Prefer companies with an ROA above 5% as an indicator of efficient asset utilization and quality management.

* **Asset Turnover**
    * **Formula:** Revenue (estimated from earnings) / Average Total Assets
    * **Interpretation:** Measures how efficiently assets generate revenue. Higher indicates better asset productivity.
    * **Significance:** Dalio looks for companies that maximize revenue generation from their asset base.
    * **Benchmarks:** >1.0 is generally good; varies significantly by industry
    * **Limitations:** Revenue estimation may be imprecise; industry variations make comparison difficult
    * **Decision Rule:** Favor companies with an asset turnover ratio consistently above 1.0, considering industry specific benchmarks, to indicate efficient revenue generation from assets.

* **Working Capital**
    * **Formula:** Current Assets - Current Liabilities
    * **Interpretation:** Measures short-term liquidity buffer. Positive values indicate financial cushion.
    * **Significance:** Dalio emphasizes companies with adequate working capital to fund operations and growth.
    * **Benchmarks:** Positive is essential; amount varies by business model and industry
    * **Limitations:** Absolute amount less meaningful than trends and ratios
    * **Decision Rule:** Require companies to maintain positive working capital, indicating sufficient short-term liquidity for operations and growth.

* **Working Capital Ratio**
    * **Formula:** Working Capital / Total Assets
    * **Interpretation:** Shows working capital as percentage of total assets. Higher indicates better liquidity position.
    * **Significance:** Helps Dalio assess liquidity relative to company size and operational needs.
    * **Benchmarks:** >10% is typically healthy; varies by industry and business model
    * **Limitations:** May not reflect seasonal variations or growth capital needs
    * **Decision Rule:** Look for a working capital ratio generally above 10%, adjusted for industry norms, to assess liquidity relative to company size.

* **Cash Ratio**
    * **Formula:** Cash and Cash Equivalents / Current Liabilities
    * **Interpretation:** Most conservative liquidity measure using only cash. Higher indicates better immediate payment ability.
    * **Significance:** Dalio values cash as the ultimate liquidity buffer during market stress and opportunities.
    * **Benchmarks:** >0.2 is strong; 0.1-0.2 is adequate; <0.1 may indicate cash flow stress
    * **Limitations:** Very conservative measure; excess cash may indicate poor capital allocation
    * **Decision Rule:** Seek companies with a cash ratio greater than 0.2, as a strong indicator of immediate liquidity and a buffer against market stress.

* **Equity Multiplier**
    * **Formula:** Total Assets / Total Shareholder Equity
    * **Interpretation:** Measures financial leverage. Higher values indicate more debt financing.
    * **Significance:** Dalio uses this to assess financial leverage and risk amplification during downturns.
    * **Benchmarks:** <2.0 is conservative; 2-3 is moderate; >4 indicates high leverage
    * **Limitations:** Doesn't distinguish between different types of leverage or debt quality
    * **Decision Rule:** Favor companies with an equity multiplier below 2.0 to ensure conservative financial leverage and mitigate risk during downturns.

* **Tangible Book Value per Share**
    * **Formula:** (Shareholder Equity - Intangible Assets) / Shares Outstanding
    * **Interpretation:** Book value excluding intangible assets per share. Represents tangible asset backing.
    * **Significance:** Dalio values tangible assets as they provide more reliable value during distress scenarios.
    * **Benchmarks:** Higher is generally better; compare to market price for value assessment
    * **Limitations:** Book values may not reflect current market values of assets
    * **Decision Rule:** Prefer companies with a substantial and growing tangible book value per share, as it represents reliable asset backing.

* **Cash per Share**
    * **Formula:** Cash and Cash Equivalents / Shares Outstanding
    * **Interpretation:** Cash backing per share. Higher indicates better liquidity per ownership unit.
    * **Significance:** Dalio appreciates companies with strong cash positions for flexibility and opportunity capture.
    * **Benchmarks:** Higher is generally better; context depends on business model and growth needs
    * **Limitations:** Doesn't reflect cash generation capability or future cash needs
    * **Decision Rule:** Look for companies with consistently high and improving cash per share, indicating strong liquidity and flexibility.

* **Free Cash Flow (Proxy)**
    * **Formula:** Operating Cash Flow - Capital Expenditures
    * **Interpretation:** Cash available after necessary investments. Positive indicates cash generation capability.
    * **Significance:** Dalio values companies that generate consistent free cash flow for dividends and growth.
    * **Benchmarks:** Positive is essential; higher and growing trends are preferred
    * **Limitations:** Capital expenditure classification may vary; doesn't include all growth investments
    * **Decision Rule:** Insist on companies consistently generating positive and growing free cash flow as a sign of financial health and ability to fund growth and dividends.

* **Operating Margin (Proxy)**
    * **Formula:** Operating Cash Flow / Estimated Revenue
    * **Interpretation:** Operating efficiency measure. Higher indicates better operational profitability.
    * **Significance:** Dalio seeks companies with sustainable competitive advantages reflected in margins.
    * **Benchmarks:** >15% is strong; 5-15% is moderate; <5% indicates potential efficiency issues
    * **Limitations:** Revenue estimation introduces uncertainty; margins vary significantly by industry
    * **Decision Rule:** Target companies with an operating margin (proxy) consistently above 15%, considering industry specifics, to identify sustainable competitive advantages and strong operational profitability.

* **Financial Strength Composite Score**
    * **Formula:** Weighted average of key ratios: Current Ratio (20%), Debt/Equity (25%), ROE (20%), Cash Ratio (15%), Interest Coverage (20%)
    * **Interpretation:** Overall financial health score from 0-100. Higher indicates stronger financial position.
    * **Significance:** Dalio's approach emphasizes multiple factors - this composite captures overall financial robustness.
    * **Benchmarks:** >80 is excellent; 60-80 is good; 40-60 is moderate; <40 indicates concerns
    * **Limitations:** Weighting is subjective; may not capture all relevant factors for specific industries
    * **Decision Rule:** Only consider companies with a Financial Strength Composite Score above 80, indicating excellent overall financial health. Scores below 60 are a significant deterrent.

* **Earnings Surprise Consistency**
    * **Formula:** Standard deviation of quarterly earnings surprises over available periods
    * **Interpretation:** Measures earnings predictability. Lower values indicate more consistent performance.
    * **Significance:** Dalio values predictable earnings as indicator of business quality and management capability.
    * **Benchmarks:** <1.0 is very consistent; 1-3 is moderate; >3 indicates high volatility
    * **Limitations:** Limited by available quarterly data; may not reflect recent business changes
    * **Decision Rule:** Prefer companies with an earnings surprise consistency score below 1.0, indicating highly predictable earnings and business quality. Scores above 3 are a strong negative signal.

* **Insider Trading Signal**
    * **Formula:** Net insider buying activity over recent transactions (positive = net buying)
    * **Interpretation:** Measures insider confidence. Positive values suggest insider optimism.
    * **Significance:** Dalio considers insider activity as potential signal of company prospects from informed parties.
    * **Benchmarks:** Positive is generally favorable; magnitude and consistency matter more than absolute values
    * **Limitations:** Limited transaction history; insiders may trade for personal reasons unrelated to company outlook
    * **Decision Rule:** A consistently positive and significant insider trading signal, reflecting net buying, is a favorable indicator of management confidence.

* **Data Freshness Score**
    * **Formula:** Days since most recent financial data / 365
    * **Interpretation:** Measures how current the financial data is. Lower scores indicate more recent data.
    * **Significance:** Dalio emphasizes using current information - stale data reduces decision quality.
    * **Benchmarks:** <0.25 (90 days) is current; 0.25-0.5 is acceptable; >0.5 requires caution
    * **Limitations:** Doesn't reflect whether business fundamentals have changed since last report
    * **Decision Rule:** Insist on financial data with a Data Freshness Score below 0.25 (within 90 days) to ensure decisions are based on current information. Data older than 0.5 (180 days) makes analysis unreliable.

### Stage 2: Company Analysis and Verdict Generation

You will receive actual numerical data for a company. Your task is to analyze this data against the established "Decision Rules" for each metric.

Your final assessment must be provided in the following JSON format:

```json
{
  "reasoning": "Provide a detailed explanation in markdown-style format for your investment decision. For each available metric, explain how its value or trend influences your assessment and reference the specific decision rule and with value investing principles.",
  "confidence_score": <integer between 0 and 100 representing your confidence>,
  "final_verdict": "<one of: 'Strong Candidate', 'Possible Candidate', 'Not a Typical Investment', 'Avoid'>"
}
```

The `reasoning` field must include a detailed explanation for each fundamental metric. This explanation should clearly articulate how the metric's calculated value (or observed trend) influences your overall assessment of the company. Crucially, you must directly reference the "Decision Rule" for each metric in your explanation (e.g., "The Current Ratio of 2.5 aligns with the decision rule of 'Prefer companies with a current ratio of 1.5 or higher, ideally between 1.5 and 3.0', indicating strong short-term liquidity."). The reasoning should be presented in a clear, markdown-style format, making it easy to read and understand.

The `confidence_score` should be an integer between 0 and 100, representing your certainty in the `final_verdict`.

The `final_verdict` must be one of the following:

* **Strong Candidate:** The company exhibits exceptional financial health, strong resilience, and consistent performance across most Dalio-aligned metrics, significantly exceeding benchmarks.
* **Possible Candidate:** The company shows good financial health and potential, but has some areas that warrant further investigation or slight deviations from optimal Dalio-aligned metrics.
* **Not a Typical Investment:** The company deviates significantly from several key Dalio-aligned financial metrics, indicating higher risk or less predictable performance, making it generally unsuitable for a Dalio-esque portfolio.
* **Avoid:** The company displays critical weaknesses in multiple fundamental metrics, indicating high risk, poor financial health, or a lack of resilience, making it an unsuitable investment.
"""


if __name__ == "__main__":
    import asyncio
    from logging import basicConfig
    from os import environ

    from dotenv import load_dotenv
    from llama_index.core.workflow import StartEvent, StopEvent, Workflow, step
    from llama_index.llms.google_genai import GoogleGenAI

    load_dotenv()

    basicConfig(level="INFO")

    llm = GoogleGenAI(model="gemini-2.0-flash")
    llm = llm.as_structured_llm(SignalEvent)

    class MockWorkflow(Workflow):
        @step
        async def agent(self, ctx: Context, ev: StartEvent) -> StopEvent:
            await ctx.set("llm_struct", llm)
            await ctx.set("alpha_client", AlphaVantageClient(environ["ALPHA_VANTAGE"]))
            await ctx.set("ticker", ev.ticker)
            result = await ray_dalio_agent(ctx)
            return StopEvent(result=result)

    async def run():
        wf = MockWorkflow()
        result = await wf.run(ticker="META")
        return result

    result = asyncio.run(run())
    print(result.model_dump_json(indent=2))
