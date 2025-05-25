from logging import getLogger
from pathlib import Path
from typing import Any, Dict

from llama_index.core.workflow import Context

from src.agents._signal import SignalEvent
from src.tools import AlphaVantageClient, TickerData
from src.utils.format import id_to_name

from ._utils import generate_output

ID = Path(__file__).stem
NAME = id_to_name(ID)
LOG = getLogger(__name__)


async def cathie_wood_agent(context: Context):
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
    ticker_data: TickerData, timeframe="annual", lookback_years=5
) -> Dict[str, Any]:
    """
    Calculate fundamental analysis metrics in the style of Cathie Wood/ARK Invest.

    Args:
        ticker_data: TickerData object containing financial statements
        timeframe: 'annual' or 'quarterly' analysis
        lookback_years: Number of years to analyze for trends (default 5)

    Returns:
        dict: Comprehensive metrics dictionary
    """

    def safe_divide(numerator, denominator, default=None):
        """Safe division with None handling"""
        if numerator is None or denominator is None or denominator == 0:
            return default
        return numerator / denominator

    def safe_percentage(numerator, denominator, default=None):
        """Safe percentage calculation with None handling"""
        if numerator is None or denominator is None or denominator == 0:
            return default
        return numerator / denominator * 100

    def safe_subtract(a, b, default=None):
        """Safe subtraction with None handling"""
        if a is None or b is None:
            return default
        return a - b

    def calculate_growth_rate(values, periods=1):
        """Calculate compound annual growth rate"""
        if len(values) < 2 or values[0] is None or values[-1] is None:
            return None
        if values[-1] <= 0:
            return None
        try:
            return ((values[0] / values[-1]) ** (1 / periods) - 1) * 100
        except Exception as e:
            LOG.error(e)
            return None

    def calculate_trend_score(values):
        """Calculate trend consistency score (0-100)"""
        if len(values) < 3:
            return None
        positive_changes = 0
        total_changes = 0
        for i in range(1, len(values)):
            if values[i - 1] is not None and values[i] is not None:
                if values[i] > values[i - 1]:
                    positive_changes += 1
                total_changes += 1
        return (positive_changes / total_changes * 100) if total_changes > 0 else None

    # Select data source based on timeframe
    if timeframe == "quarterly":
        balance_reports = ticker_data.balance_sheet.quarterly_reports[
            : min(lookback_years * 4, len(ticker_data.balance_sheet.quarterly_reports))
        ]
        cash_flow_reports = (
            ticker_data.cash_flow.quarterly_reports[
                : min(lookback_years * 4, len(ticker_data.cash_flow.quarterly_reports))
            ]
            if ticker_data.cash_flow.quarterly_reports
            else []
        )
        earnings_reports = ticker_data.earnings.quarterly_earnings[
            : min(lookback_years * 4, len(ticker_data.earnings.quarterly_earnings))
        ]
    else:
        balance_reports = ticker_data.balance_sheet.annual_reports[
            : min(lookback_years, len(ticker_data.balance_sheet.annual_reports))
        ]
        cash_flow_reports = ticker_data.cash_flow.annual_reports[
            : min(lookback_years, len(ticker_data.cash_flow.annual_reports))
        ]
        earnings_reports = ticker_data.earnings.annual_earnings[
            : min(lookback_years, len(ticker_data.earnings.annual_earnings))
        ]

    if not balance_reports:
        return {"error": "No balance sheet data available"}

    # Get most recent data
    latest_balance = balance_reports[0]
    latest_cash_flow = cash_flow_reports[0] if cash_flow_reports else None
    latest_earnings = earnings_reports[0] if earnings_reports else None

    # Initialize results
    metrics = {
        "data_quality": {
            "fiscal_date_ending": latest_balance.fiscal_date_ending,
            "reported_currency": latest_balance.reported_currency,
            "timeframe": timeframe,
            "periods_analyzed": len(balance_reports),
        }
    }

    # === GROWTH METRICS (Cathie Wood's primary focus) ===

    # Revenue Growth (from cash flow net income as proxy)
    net_incomes = [
        cf.net_income for cf in cash_flow_reports if cf.net_income is not None
    ]
    if len(net_incomes) >= 2:
        revenue_growth_rate = calculate_growth_rate(net_incomes, len(net_incomes) - 1)
        revenue_trend_score = calculate_trend_score(
            net_incomes[::-1]
        )  # Reverse for chronological order
        metrics["revenue_growth_rate"] = revenue_growth_rate
        metrics["revenue_trend_consistency"] = revenue_trend_score

    # Asset Growth Rate
    total_assets = [
        bs.total_assets for bs in balance_reports if bs.total_assets is not None
    ]
    if len(total_assets) >= 2:
        asset_growth_rate = calculate_growth_rate(total_assets, len(total_assets) - 1)
        metrics["asset_growth_rate"] = asset_growth_rate

    # R&D Intensity Proxy (Intangible Assets Growth)
    intangible_assets = [
        bs.intangible_assets
        for bs in balance_reports
        if bs.intangible_assets is not None
    ]
    if len(intangible_assets) >= 2:
        intangible_growth_rate = calculate_growth_rate(
            intangible_assets, len(intangible_assets) - 1
        )
        metrics["innovation_investment_growth"] = intangible_growth_rate

    # === FINANCIAL STRENGTH METRICS ===

    # Current Ratio
    current_ratio = safe_divide(
        latest_balance.total_current_assets, latest_balance.total_current_liabilities
    )
    metrics["current_ratio"] = current_ratio

    # Quick Ratio (Cash + Short-term investments / Current liabilities)
    quick_assets = (latest_balance.cash_and_cash_equivalents_at_carrying_value or 0) + (
        latest_balance.cash_and_short_term_investments or 0
    )
    quick_ratio = safe_divide(quick_assets, latest_balance.total_current_liabilities)
    metrics["quick_ratio"] = quick_ratio

    # Debt-to-Equity Ratio
    total_debt = latest_balance.short_long_term_debt_total or 0
    debt_to_equity = safe_divide(total_debt, latest_balance.total_shareholder_equity)
    metrics["debt_to_equity_ratio"] = debt_to_equity

    # Debt-to-Assets Ratio
    debt_to_assets = safe_divide(total_debt, latest_balance.total_assets)
    metrics["debt_to_assets_ratio"] = debt_to_assets

    # === EFFICIENCY METRICS ===

    # Asset Turnover (approximated using available data)
    if latest_cash_flow and latest_cash_flow.net_income:
        asset_turnover = safe_divide(
            latest_cash_flow.net_income, latest_balance.total_assets
        )
        metrics["asset_efficiency"] = asset_turnover

    # Return on Assets (ROA)
    if latest_cash_flow and latest_cash_flow.net_income:
        roa = (
            safe_percentage(latest_cash_flow.net_income, latest_balance.total_assets)
            
        )
        metrics["return_on_assets"] = roa

    # Return on Equity (ROE)
    if latest_cash_flow and latest_cash_flow.net_income:
        roe = (
            safe_percentage(
                latest_cash_flow.net_income, latest_balance.total_shareholder_equity
            )
        )
        metrics["return_on_equity"] = roe

    # === CASH FLOW METRICS (Critical for ARK's analysis) ===

    if latest_cash_flow:
        # Operating Cash Flow Margin
        if latest_cash_flow.operating_cashflow and latest_cash_flow.net_income:
            ocf_margin = (
                safe_percentage(
                    latest_cash_flow.operating_cashflow, latest_cash_flow.net_income
                )
            )
            metrics["operating_cash_flow_margin"] = ocf_margin

        # Free Cash Flow (Operating Cash Flow - Capital Expenditures)
        if (
            latest_cash_flow.operating_cashflow
            and latest_cash_flow.capital_expenditures
        ):
            free_cash_flow = latest_cash_flow.operating_cashflow - abs(
                latest_cash_flow.capital_expenditures
            )
            metrics["free_cash_flow"] = free_cash_flow

            # Free Cash Flow Yield
            if latest_balance.total_assets:
                fcf_yield = (
                    safe_percentage(free_cash_flow, latest_balance.total_assets)
                )
                metrics["free_cash_flow_yield"] = fcf_yield

        # Cash Flow Growth
        operating_cash_flows = [
            cf.operating_cashflow
            for cf in cash_flow_reports
            if cf.operating_cashflow is not None
        ]
        if len(operating_cash_flows) >= 2:
            cash_flow_growth = calculate_growth_rate(
                operating_cash_flows, len(operating_cash_flows) - 1
            )
            metrics["operating_cash_flow_growth"] = cash_flow_growth

    # === BALANCE SHEET QUALITY METRICS ===

    # Cash Position Strength
    total_cash = (latest_balance.cash_and_cash_equivalents_at_carrying_value or 0) + (
        latest_balance.cash_and_short_term_investments or 0
    )
    cash_to_assets = safe_percentage(total_cash, latest_balance.total_assets) 
    metrics["cash_position_ratio"] = cash_to_assets

    # Working Capital
    working_capital = safe_subtract(
        latest_balance.total_current_assets, latest_balance.total_current_liabilities
    )
    metrics["working_capital"] = working_capital

    # Working Capital Ratio
    working_capital_ratio = (
        safe_percentage(working_capital, latest_balance.total_assets) 
    )
    metrics["working_capital_ratio"] = working_capital_ratio

    # === INNOVATION & INTANGIBLES FOCUS ===

    # Intangible Asset Ratio (Key for tech/innovation companies)
    intangible_ratio = (
        safe_percentage(latest_balance.intangible_assets, latest_balance.total_assets)
        
    )
    metrics["intangible_assets_ratio"] = intangible_ratio

    # Goodwill Ratio
    goodwill_ratio = (
        safe_percentage(latest_balance.goodwill, latest_balance.total_assets) 
    )
    metrics["goodwill_ratio"] = goodwill_ratio

    # === EARNINGS QUALITY METRICS ===

    if earnings_reports:
        # EPS Growth Rate
        eps_values = [
            e.reported_eps for e in earnings_reports if e.reported_eps is not None
        ]
        if len(eps_values) >= 2:
            eps_growth_rate = calculate_growth_rate(eps_values, len(eps_values) - 1)
            eps_trend_score = calculate_trend_score(eps_values[::-1])
            metrics["eps_growth_rate"] = eps_growth_rate
            metrics["eps_trend_consistency"] = eps_trend_score

        # Earnings Surprise Analysis (for quarterly data)
        if timeframe == "quarterly" and hasattr(earnings_reports[0], "surprise"):
            recent_surprises = [
                e.surprise for e in earnings_reports[:4] if e.surprise is not None
            ]
            if recent_surprises:
                avg_surprise = sum(recent_surprises) / len(recent_surprises)
                positive_surprises = sum(1 for s in recent_surprises if s > 0)
                surprise_consistency = (
                    positive_surprises / len(recent_surprises)
                ) * 100
                metrics["average_earnings_surprise"] = avg_surprise
                metrics["earnings_surprise_consistency"] = surprise_consistency

    # === INSIDER SENTIMENT ===

    if ticker_data.insider_transactions and ticker_data.insider_transactions.data:
        # Recent insider activity (last 90 days approximation - take first 10 transactions)
        recent_transactions = ticker_data.insider_transactions.data[:10]

        if recent_transactions:
            acquisitions = [
                t for t in recent_transactions if t.acquisition_or_disposal == "A"
            ]
            disposals = [
                t for t in recent_transactions if t.acquisition_or_disposal == "D"
            ]

            total_acquired = sum(t.shares for t in acquisitions) if acquisitions else 0
            total_disposed = sum(t.shares for t in disposals) if disposals else 0

            net_insider_activity = total_acquired - total_disposed
            metrics["net_insider_share_activity"] = net_insider_activity

            if len(recent_transactions) > 0:
                insider_bullishness = (
                    len(acquisitions) / len(recent_transactions)
                ) * 100
                metrics["insider_bullishness_ratio"] = insider_bullishness

    # === COMPOSITE SCORES ===

    # Growth Score (0-100)
    growth_components = []
    if metrics.get("revenue_growth_rate"):
        growth_components.append(min(max(metrics["revenue_growth_rate"], -50), 100))
    if metrics.get("asset_growth_rate"):
        growth_components.append(min(max(metrics["asset_growth_rate"], -50), 100))
    if metrics.get("eps_growth_rate"):
        growth_components.append(min(max(metrics["eps_growth_rate"], -50), 100))

    if growth_components:
        growth_score = sum(growth_components) / len(growth_components)
        metrics["composite_growth_score"] = max(
            0, min(100, growth_score + 50)
        )  # Normalize to 0-100

    # Financial Health Score (0-100)
    health_score = 0
    health_components = 0

    if current_ratio:
        health_score += min(100, max(0, (current_ratio - 0.5) * 50))  # Good if >1.5
        health_components += 1

    if debt_to_equity is not None:
        health_score += max(0, 100 - (debt_to_equity * 20))  # Good if <0.5
        health_components += 1

    if cash_to_assets:
        health_score += min(100, cash_to_assets * 5)  # Good if >20%
        health_components += 1

    if health_components > 0:
        metrics["composite_financial_health_score"] = health_score / health_components

    # Innovation Score (0-100) - Key for ARK-style investing
    innovation_score = 0
    innovation_components = 0

    if intangible_ratio:
        innovation_score += min(100, intangible_ratio * 2)  # Good if >50%
        innovation_components += 1

    if metrics.get("innovation_investment_growth"):
        innovation_score += min(
            100, max(0, metrics["innovation_investment_growth"] + 50)
        )
        innovation_components += 1

    if innovation_components > 0:
        metrics["composite_innovation_score"] = innovation_score / innovation_components

    # Overall ARK-Style Score (weighted toward growth and innovation)
    overall_components = []
    if metrics.get("composite_growth_score"):
        overall_components.append(("growth", metrics["composite_growth_score"], 0.4))
    if metrics.get("composite_innovation_score"):
        overall_components.append(
            ("innovation", metrics["composite_innovation_score"], 0.35)
        )
    if metrics.get("composite_financial_health_score"):
        overall_components.append(
            ("health", metrics["composite_financial_health_score"], 0.25)
        )

    if overall_components:
        weighted_score = sum(score * weight for _, score, weight in overall_components)
        total_weight = sum(weight for _, _, weight in overall_components)
        metrics["ark_style_investment_score"] = weighted_score / total_weight

    return metrics


PROMPT = """
# Cathie Wood Financial Analyst System Prompt

## Persona Definition

You are an expert financial analyst embodying the investment philosophy and analytical approach of Cathie Wood, founder and CEO of ARK Invest. Your focus is on identifying disruptive innovation companies with exceptional growth potential that can deliver transformative returns over 5+ year investment horizons. You prioritize companies that are pioneering breakthrough technologies, demonstrate strong fundamentals with sustainable competitive advantages, and show consistent execution in expanding markets.

Your analysis emphasizes three core pillars: **Growth**, **Innovation**, and **Financial Health**, with particular attention to companies that are reshaping industries through technological disruption.

## Two-Stage Analytical Process

### Stage 1: Pre-Analysis Setup - Metric Definitions and Decision Rules

Before analyzing any company, you must first establish your analytical framework by listing all fundamental metrics and their corresponding decision rules:

#### Growth Metrics

**Revenue Growth Rate**
- *Definition*: Annual percentage growth in company revenue ((Current Period Revenue / Previous Period Revenue)^(1/periods) - 1) * 100
- *Decision Rule*: Strongly favor companies with >20% sustained annual revenue growth; consider companies with 15-20% growth if other factors are exceptional; be cautious of companies with <10% growth unless in mature, stable markets

**Asset Growth Rate**
- *Definition*: Rate at which company's total assets are expanding year-over-year
- *Decision Rule*: Prefer companies showing 15-30% annual asset growth as indicator of scaling operations; be wary of >40% growth unless clearly justified by business expansion

**EPS Growth Rate**
- *Definition*: Compound annual growth rate of earnings per share over specified period
- *Decision Rule*: Target companies with >20% annual EPS growth; accept lower rates (10-15%) if revenue growth is exceptional and path to profitability is clear

**EPS Trend Consistency**
- *Definition*: Percentage of periods where EPS increased compared to previous period
- *Decision Rule*: Prefer companies with >80% consistency; accept 60-80% if growth magnitude is strong during positive periods

#### Innovation Metrics

**Innovation Investment Growth**
- *Definition*: Growth rate of intangible assets over time, measuring R&D and IP investment
- *Decision Rule*: Strongly favor companies with >15% annual growth in intangible assets; this indicates commitment to future competitive advantages

**Intangible Assets Ratio**
- *Definition*: (Intangible Assets / Total Assets) * 100
- *Decision Rule*: Prefer companies with >25% intangible asset ratios; exceptional candidates have >40%, indicating technology-driven business models

**Composite Innovation Score**
- *Definition*: Combination of intangible asset ratio and innovation investment growth (0-100 scale)
- *Decision Rule*: Target companies scoring >60; scores >75 indicate innovation leaders deserving premium valuations

#### Financial Health Metrics

**Current Ratio**
- *Definition*: Total Current Assets / Total Current Liabilities
- *Decision Rule*: Prefer ratios between 1.5-3.0; ratios <1.2 raise liquidity concerns; ratios >4.0 may indicate inefficient cash deployment

**Quick Ratio**
- *Definition*: (Cash + Cash Equivalents + Short-term Investments) / Current Liabilities
- *Decision Rule*: Maintain minimum threshold of 0.8; prefer >1.2 for growth companies that may face unexpected capital needs

**Debt-to-Equity Ratio**
- *Definition*: Total Debt / Total Shareholders' Equity
- *Decision Rule*: Prefer ratios <0.6 for growth companies; be cautious of ratios >1.0 unless debt clearly supports growth initiatives

**Cash Position Ratio**
- *Definition*: (Cash + Cash Equivalents + Short-term Investments) / Total Assets * 100
- *Decision Rule*: Prefer 12-25% cash ratios for strategic flexibility; >30% may indicate lack of growth opportunities; <8% raises operational risk concerns

#### Profitability and Efficiency Metrics

**Return on Assets (ROA)**
- *Definition*: (Net Income / Total Assets) * 100
- *Decision Rule*: Accept lower ROA (2-8%) for high-growth companies investing in future capacity; mature companies should show >10%

**Return on Equity (ROE)**
- *Definition*: (Net Income / Total Shareholders' Equity) * 100
- *Decision Rule*: Target >15% for established companies; accept 8-15% for companies in heavy investment phase with clear path to higher returns

**Operating Cash Flow Margin**
- *Definition*: (Operating Cash Flow / Net Income) * 100
- *Decision Rule*: Require >90% for earnings quality; be cautious of <80% unless clearly explained by business model or timing factors

**Free Cash Flow**
- *Definition*: Operating Cash Flow - Capital Expenditures
- *Decision Rule*: Prefer positive and growing free cash flow; accept negative FCF for companies in rapid expansion phase if path to positive FCF is clear within 2-3 years

**Free Cash Flow Yield**
- *Definition*: (Free Cash Flow / Total Assets) * 100
- *Decision Rule*: Target >6% for efficient capital deployment; accept 2-6% for growth companies with strong revenue expansion

#### Market Sentiment and Management Metrics

**Average Earnings Surprise**
- *Definition*: Average difference between reported EPS and analyst estimates over recent quarters
- *Decision Rule*: Favor companies with consistent positive surprises >$0.03; view negative surprises as concerning unless clearly explained

**Net Insider Share Activity**
- *Definition*: Total shares acquired by insiders minus total shares disposed over recent period
- *Decision Rule*: Prefer net insider buying; modest selling acceptable if not concentrated among key executives

**Insider Bullishness Ratio**
- *Definition*: (Number of Acquisition Transactions / Total Insider Transactions) * 100
- *Decision Rule*: Prefer >50% acquisition ratio; be cautious if <25% unless driven by estate planning or diversification needs

#### Composite Scores

**Composite Growth Score**
- *Definition*: Normalized average of revenue growth, asset growth, and EPS growth rates (0-100 scale)
- *Decision Rule*: Target scores >75 for strong candidates; scores >85 indicate exceptional growth momentum deserving premium consideration

**Composite Financial Health Score**
- *Definition*: Normalized combination of liquidity, leverage, and cash position metrics (0-100 scale)
- *Decision Rule*: Require minimum score of 55; prefer >70 for investment consideration; scores >85 indicate exceptionally strong financial foundation

**ARK-Style Investment Score**
- *Definition*: Weighted combination of Growth Score (40%), Innovation Score (35%), and Financial Health Score (25%)
- *Decision Rule*: Scores >75 indicate strong investment candidates; scores >85 warrant deep due diligence for potential portfolio inclusion; scores <60 typically not suitable for ARK-style investing

### Stage 2: Company Analysis and Verdict Generation

After establishing the analytical framework above, you will receive actual numerical data for a specific company. Your task is to:

1. **Apply Decision Rules**: Systematically evaluate each provided metric against its corresponding decision rule
2. **Assess Strategic Alignment**: Determine how well the company aligns with disruptive innovation themes
3. **Evaluate Risk-Reward Profile**: Consider both upside potential and downside risks
4. **Generate Final Assessment**: Provide comprehensive analysis leading to investment verdict

## Mandatory Output Format

Your final assessment must be provided in exactly this JSON format:

```json
{
  "reasoning": "Provide a detailed explanation in markdown-style format for your investment decision. For each available metric, explain how its value or trend influences your assessment and reference the specific decision rule and with value investing principles.",
  "confidence_score": <integer between 0 and 100 representing your confidence>,
  "final_verdict": "<one of: 'Strong Candidate', 'Possible Candidate', 'Not a Typical Investment', 'Avoid'>"
}
```

## Reasoning Requirements

The reasoning field must include:

1. **Metric-by-Metric Analysis**: For each fundamental metric provided, explain:
   - The metric's actual value or trend
   - How this value compares to the established decision rule
   - The specific impact on your overall assessment
   - Any contextual factors that modify standard interpretation

2. **Thematic Alignment Assessment**: Evaluate how the company fits ARK's disruptive innovation thesis

3. **Risk Assessment**: Identify key risks and how they're mitigated or amplified by the financial metrics

4. **Synthesis**: Explain how all factors combine to reach your final verdict

Format the reasoning using clear markdown structure with headers, bullet points, and emphasis where appropriate for maximum readability.

## Confidence Score Definition

The confidence_score is an integer between 0 and 100 representing your certainty in the assessment:
- **90-100**: Extremely confident - comprehensive data supports clear conclusion
- **75-89**: Highly confident - strong evidence with minor gaps or uncertainties
- **60-74**: Moderately confident - good evidence but some conflicting indicators or missing data
- **40-59**: Somewhat confident - mixed signals requiring additional analysis
- **20-39**: Low confidence - insufficient or highly conflicting data
- **0-19**: Very low confidence - major data gaps or contradictory information

## Final Verdict Definitions

- **"Strong Candidate"**: Company demonstrates exceptional alignment with ARK's investment criteria across growth, innovation, and financial health metrics. Suitable for significant portfolio allocation.

- **"Possible Candidate"**: Company shows good potential with strong performance in most key areas but has some concerns or areas needing improvement. May warrant smaller position or continued monitoring.

- **"Not a Typical Investment"**: Company may be fundamentally sound but doesn't align well with ARK's disruptive innovation focus or growth requirements. Better suited for different investment strategies.

- **"Avoid"**: Company shows significant red flags in critical areas such as deteriorating fundamentals, poor financial health, or lack of growth prospects that make it unsuitable for ARK-style investing.

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
            result = await cathie_wood_agent(ctx)
            return StopEvent(result=result)

    async def run():
        wf = MockWorkflow()
        result = await wf.run(ticker="META")
        return result

    result = asyncio.run(run())
    print(result.model_dump_json(indent=2))
