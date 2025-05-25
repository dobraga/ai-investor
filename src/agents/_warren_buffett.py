from datetime import date, datetime
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


async def warren_buffett_agent(context: Context):
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
    ticker_data: TickerData, analysis_periods: int = 5, use_quarterly: bool = False
) -> Dict[str, Any]:
    """
    Comprehensive fundamental analysis based on Warren Buffett's investment criteria.

    Args:
        ticker_data: TickerData object containing financial statements
        analysis_periods: Number of historical periods to analyze (default: 5)
        use_quarterly: Whether to use quarterly data instead of annual (default: False)

    Returns:
        Dictionary containing all calculated metrics, trends, and analysis
    """

    def safe_divide(numerator, denominator, default=None):
        """Safely divide two numbers, handling None values and division by zero."""
        if numerator is None or denominator is None or denominator == 0:
            return default
        return numerator / denominator

    def safe_subtract(a, b, default=None):
        """Safely subtract two numbers, handling None values."""
        if a is None or b is None:
            return default
        return a - b

    def safe_percentage_change(current, previous, default=None):
        """Calculate percentage change safely."""
        if current is None or previous is None or previous == 0:
            return default
        return ((current - previous) / abs(previous)) * 100

    def get_latest_value(reports, field_name, periods=1):
        """Extract the latest value(s) for a field from reports."""
        values = []
        for report in reports[:periods]:
            value = getattr(report, field_name, None)
            if value is not None:
                values.append(value)
        return values[0] if len(values) == 1 else values

    def calculate_growth_rate(values):
        """Calculate compound annual growth rate from a list of values."""
        if len(values) < 2:
            return None

        # Remove None values and ensure we have positive values for CAGR
        clean_values = [v for v in values if v is not None and v > 0]
        if len(clean_values) < 2:
            return None

        try:
            start_value = clean_values[-1]  # Oldest value
            end_value = clean_values[0]  # Most recent value
            periods = len(clean_values) - 1

            cagr = (pow(end_value / start_value, 1 / periods) - 1) * 100
            return cagr
        except (ValueError, ZeroDivisionError):
            return None

    def calculate_percentile_rank(value, value_list):
        """Calculate percentile rank of a value within a list."""
        if value is None or not value_list:
            return None

        valid_values = [v for v in value_list if v is not None]
        if not valid_values:
            return None

        below = sum(1 for v in valid_values if v < value)
        return (below / len(valid_values)) * 100

    # Determine which reports to use
    if use_quarterly:
        balance_reports = ticker_data.balance_sheet.quarterly_reports[:analysis_periods]
        cash_flow_reports = (
            ticker_data.cash_flow.quarterly_reports[:analysis_periods]
            if ticker_data.cash_flow.quarterly_reports
            else []
        )
        earnings_reports = ticker_data.earnings.quarterly_earnings[:analysis_periods]
    else:
        balance_reports = ticker_data.balance_sheet.annual_reports[:analysis_periods]
        cash_flow_reports = ticker_data.cash_flow.annual_reports[:analysis_periods]
        earnings_reports = ticker_data.earnings.annual_earnings[:analysis_periods]

    # Initialize results dictionary
    results = {
        "metadata": {
            "analysis_date": datetime.now().isoformat(),
            "periods_analyzed": len(balance_reports),
            "analysis_type": "quarterly" if use_quarterly else "annual",
            "latest_fiscal_date": balance_reports[0].fiscal_date_ending
            if balance_reports
            else None,
            "currency": balance_reports[0].reported_currency
            if balance_reports
            else "USD",
        },
        "profitability_metrics": {},
        "liquidity_metrics": {},
        "leverage_metrics": {},
        "efficiency_metrics": {},
        "cash_flow_metrics": {},
        "growth_metrics": {},
        "valuation_metrics": {},
        "quality_metrics": {},
        "insider_activity": {},
        "earnings_quality": {},
        "composite_scores": {},
        "trends": {},
        "warnings": [],
    }

    if not balance_reports:
        results["warnings"].append("No balance sheet data available for analysis")
        return results

    # Get most recent values
    latest_bs = balance_reports[0]
    latest_cf = cash_flow_reports[0] if cash_flow_reports else None

    # === PROFITABILITY METRICS ===

    # Return on Equity (ROE) - Buffett's favorite metric
    net_incomes = []
    shareholders_equities = []
    for i, report in enumerate(balance_reports):
        if i < len(cash_flow_reports):
            cf_report = cash_flow_reports[i]
            if cf_report.net_income is not None:
                net_incomes.append(cf_report.net_income)

        if report.total_shareholder_equity is not None:
            shareholders_equities.append(report.total_shareholder_equity)

    if net_incomes and shareholders_equities:
        latest_roe = safe_divide(net_incomes[0], shareholders_equities[0])
        if latest_roe:
            results["profitability_metrics"]["return_on_equity"] = {
                "value": latest_roe * 100,
                "interpretation": "Excellent"
                if latest_roe > 0.20
                else "Good"
                if latest_roe > 0.15
                else "Average"
                if latest_roe > 0.10
                else "Poor",
            }

        # Calculate average ROE
        roe_values = []
        for i in range(min(len(net_incomes), len(shareholders_equities))):
            roe = safe_divide(net_incomes[i], shareholders_equities[i])
            if roe:
                roe_values.append(roe * 100)

        if roe_values:
            results["profitability_metrics"]["average_roe"] = sum(roe_values) / len(
                roe_values
            )
            results["profitability_metrics"]["roe_consistency"] = (
                len([r for r in roe_values if r > 15]) / len(roe_values) * 100
            )

    # Return on Assets (ROA)
    total_assets = [
        report.total_assets
        for report in balance_reports
        if report.total_assets is not None
    ]
    if net_incomes and total_assets:
        latest_roa = safe_divide(net_incomes[0], total_assets[0])
        if latest_roa:
            results["profitability_metrics"]["return_on_assets"] = {
                "value": latest_roa * 100,
                "interpretation": "Excellent"
                if latest_roa > 0.10
                else "Good"
                if latest_roa > 0.05
                else "Average"
                if latest_roa > 0.02
                else "Poor",
            }

    # === LIQUIDITY METRICS ===

    # Current Ratio
    current_ratio = safe_divide(
        latest_bs.total_current_assets, latest_bs.total_current_liabilities
    )
    if current_ratio:
        results["liquidity_metrics"]["current_ratio"] = {
            "value": current_ratio,
            "interpretation": "Strong"
            if current_ratio > 2.0
            else "Adequate"
            if current_ratio > 1.5
            else "Concerning"
            if current_ratio > 1.0
            else "Weak",
        }

    # Quick Ratio
    inventory = latest_bs.inventory or 0
    quick_assets = safe_subtract(latest_bs.total_current_assets, inventory)
    quick_ratio = safe_divide(quick_assets, latest_bs.total_current_liabilities)
    if quick_ratio:
        results["liquidity_metrics"]["quick_ratio"] = {
            "value": quick_ratio,
            "interpretation": "Strong"
            if quick_ratio > 1.5
            else "Good"
            if quick_ratio > 1.0
            else "Adequate"
            if quick_ratio > 0.8
            else "Weak",
        }

    # Cash Ratio
    cash_ratio = safe_divide(
        latest_bs.cash_and_cash_equivalents_at_carrying_value,
        latest_bs.total_current_liabilities,
    )
    if cash_ratio:
        results["liquidity_metrics"]["cash_ratio"] = cash_ratio

    # === LEVERAGE METRICS ===

    # Debt-to-Equity Ratio
    total_debt = latest_bs.short_long_term_debt_total or 0
    debt_to_equity = safe_divide(total_debt, latest_bs.total_shareholder_equity)
    if debt_to_equity is not None:
        results["leverage_metrics"]["debt_to_equity"] = {
            "value": debt_to_equity,
            "interpretation": "Conservative"
            if debt_to_equity < 0.3
            else "Moderate"
            if debt_to_equity < 0.6
            else "High"
            if debt_to_equity < 1.0
            else "Risky",
        }

    # Financial Leverage
    financial_leverage = safe_divide(
        latest_bs.total_assets, latest_bs.total_shareholder_equity
    )
    if financial_leverage:
        results["leverage_metrics"]["financial_leverage"] = {
            "value": financial_leverage,
            "interpretation": "Conservative"
            if financial_leverage < 2
            else "Moderate"
            if financial_leverage < 3
            else "High"
            if financial_leverage < 4
            else "Very High",
        }

    # === CASH FLOW METRICS ===

    if latest_cf:
        # Operating Cash Flow
        if latest_cf.operating_cashflow:
            results["cash_flow_metrics"]["operating_cash_flow"] = (
                latest_cf.operating_cashflow
            )

        # Free Cash Flow
        operating_cf = latest_cf.operating_cashflow or 0
        capex = (
            abs(latest_cf.capital_expenditures) if latest_cf.capital_expenditures else 0
        )
        free_cash_flow = operating_cf - capex
        results["cash_flow_metrics"]["free_cash_flow"] = free_cash_flow

        # Cash Flow Margins
        if latest_cf.net_income:
            results["cash_flow_metrics"]["operating_cf_to_net_income"] = safe_divide(
                operating_cf, latest_cf.net_income
            )

        # Dividend Coverage
        dividend_payout = latest_cf.dividend_payout or 0
        if dividend_payout > 0 and free_cash_flow > 0:
            results["cash_flow_metrics"]["dividend_coverage"] = (
                free_cash_flow / dividend_payout
            )

    # === GROWTH METRICS ===

    # EPS Growth
    eps_values = [
        report.reported_eps
        for report in earnings_reports
        if report.reported_eps is not None
    ]
    if len(eps_values) >= 2:
        eps_growth = safe_percentage_change(eps_values[0], eps_values[1])
        results["growth_metrics"]["eps_growth_rate"] = eps_growth

        # Calculate EPS CAGR
        eps_cagr = calculate_growth_rate(eps_values)
        if eps_cagr:
            results["growth_metrics"]["eps_cagr"] = eps_cagr

    # Book Value Growth
    book_values = [
        report.total_shareholder_equity
        for report in balance_reports
        if report.total_shareholder_equity is not None
    ]
    if len(book_values) >= 2:
        book_value_growth = safe_percentage_change(book_values[0], book_values[1])
        results["growth_metrics"]["book_value_growth_rate"] = book_value_growth

        book_value_cagr = calculate_growth_rate(book_values)
        if book_value_cagr:
            results["growth_metrics"]["book_value_cagr"] = book_value_cagr

    # === EFFICIENCY METRICS ===

    # Asset Turnover (requires revenue data not available in structure)
    # Working Capital
    working_capital = safe_subtract(
        latest_bs.total_current_assets, latest_bs.total_current_liabilities
    )
    if working_capital is not None:
        results["efficiency_metrics"]["working_capital"] = working_capital

    # === VALUATION METRICS ===

    # Book Value per Share
    shares_outstanding = latest_bs.common_stock_shares_outstanding
    if shares_outstanding and latest_bs.total_shareholder_equity:
        book_value_per_share = latest_bs.total_shareholder_equity / shares_outstanding
        results["valuation_metrics"]["book_value_per_share"] = book_value_per_share

    # === QUALITY METRICS ===

    # Cash and Equivalents to Total Assets
    cash_to_assets = safe_divide(
        latest_bs.cash_and_cash_equivalents_at_carrying_value, latest_bs.total_assets
    )
    if cash_to_assets:
        results["quality_metrics"]["cash_to_total_assets"] = {
            "value": cash_to_assets * 100,
            "interpretation": "Strong"
            if cash_to_assets > 0.10
            else "Adequate"
            if cash_to_assets > 0.05
            else "Low",
        }

    # Goodwill to Assets Ratio
    goodwill_ratio = safe_divide(latest_bs.goodwill, latest_bs.total_assets)
    if goodwill_ratio:
        results["quality_metrics"]["goodwill_to_assets"] = goodwill_ratio * 100

    # === INSIDER ACTIVITY ===

    if ticker_data.insider_transactions and ticker_data.insider_transactions.data:
        insider_data = ticker_data.insider_transactions.data

        # Calculate net insider activity (last 6 months)
        recent_date = date.today()
        six_months_ago = date(
            recent_date.year,
            recent_date.month - 6 if recent_date.month > 6 else recent_date.month + 6,
            recent_date.day,
        )
        if recent_date.month <= 6:
            six_months_ago = six_months_ago.replace(year=recent_date.year - 1)

        net_activity = 0
        transaction_count = 0

        for transaction in insider_data:
            if transaction.transaction_date >= six_months_ago:
                transaction_value = transaction.shares * transaction.share_price
                if transaction.acquisition_or_disposal == "A":
                    net_activity += transaction_value
                else:
                    net_activity -= transaction_value
                transaction_count += 1

        results["insider_activity"] = {
            "net_activity_6_months": net_activity,
            "transaction_count_6_months": transaction_count,
            "interpretation": "Positive"
            if net_activity > 0
            else "Negative"
            if net_activity < 0
            else "Neutral",
        }

    # === EARNINGS QUALITY ===

    if ticker_data.earnings.quarterly_earnings:
        quarterly_earnings = ticker_data.earnings.quarterly_earnings

        # Earnings surprise consistency
        surprises = [
            q.surprise_percentage
            for q in quarterly_earnings[:8]
            if q.surprise_percentage is not None
        ]  # Last 2 years
        if surprises:
            positive_surprises = sum(1 for s in surprises if s > 0)
            surprise_consistency = (positive_surprises / len(surprises)) * 100
            results["earnings_quality"]["surprise_consistency"] = {
                "value": surprise_consistency,
                "interpretation": "Excellent"
                if surprise_consistency > 75
                else "Good"
                if surprise_consistency > 60
                else "Average"
                if surprise_consistency > 40
                else "Poor",
            }

    # === COMPOSITE SCORES ===

    # Buffett Score (weighted combination of key metrics)
    buffett_score = 0
    score_components = 0

    # ROE weight: 30%
    if "return_on_equity" in results["profitability_metrics"]:
        roe_val = results["profitability_metrics"]["return_on_equity"]["value"]
        roe_score = min(100, max(0, (roe_val - 5) * 5))  # Scale: 5% = 0, 25% = 100
        buffett_score += roe_score * 0.3
        score_components += 0.3

    # Debt-to-Equity weight: 20%
    if "debt_to_equity" in results["leverage_metrics"]:
        de_val = results["leverage_metrics"]["debt_to_equity"]["value"]
        de_score = max(0, 100 - (de_val * 100))  # Lower debt = higher score
        buffett_score += de_score * 0.2
        score_components += 0.2

    # Current Ratio weight: 15%
    if "current_ratio" in results["liquidity_metrics"]:
        cr_val = results["liquidity_metrics"]["current_ratio"]["value"]
        cr_score = min(100, max(0, (cr_val - 1) * 50))  # Scale: 1.0 = 0, 3.0 = 100
        buffett_score += cr_score * 0.15
        score_components += 0.15

    # EPS Growth weight: 20%
    if "eps_cagr" in results["growth_metrics"]:
        eps_cagr = results["growth_metrics"]["eps_cagr"]
        if eps_cagr is not None:
            eps_score = min(100, max(0, eps_cagr * 5))  # Scale: 0% = 0, 20% = 100
            buffett_score += eps_score * 0.2
            score_components += 0.2

    # Cash Quality weight: 15%
    if "cash_to_total_assets" in results["quality_metrics"]:
        cash_ratio = results["quality_metrics"]["cash_to_total_assets"]["value"]
        cash_score = min(100, cash_ratio * 5)  # Scale: 0% = 0, 20% = 100
        buffett_score += cash_score * 0.15
        score_components += 0.15

    if score_components > 0:
        final_buffett_score = buffett_score / score_components
        results["composite_scores"]["buffett_score"] = {
            "value": final_buffett_score,
            "interpretation": "Excellent"
            if final_buffett_score > 80
            else "Good"
            if final_buffett_score > 60
            else "Average"
            if final_buffett_score > 40
            else "Poor",
            "components_available": score_components,
        }

    # === TREND ANALYSIS ===

    # ROE Trend
    if len(roe_values) >= 3:
        recent_roe = sum(roe_values[:2]) / 2  # Last 2 periods
        older_roe = sum(roe_values[-2:]) / 2  # First 2 periods
        roe_trend = (
            "Improving"
            if recent_roe > older_roe
            else "Declining"
            if recent_roe < older_roe
            else "Stable"
        )
        results["trends"]["roe_trend"] = roe_trend

    # Debt Trend
    debt_ratios = []
    for report in balance_reports:
        if (
            report.short_long_term_debt_total is not None
            and report.total_shareholder_equity is not None
        ):
            de_ratio = (
                report.short_long_term_debt_total / report.total_shareholder_equity
            )
            debt_ratios.append(de_ratio)

    if len(debt_ratios) >= 3:
        recent_debt = sum(debt_ratios[:2]) / 2
        older_debt = sum(debt_ratios[-2:]) / 2
        debt_trend = (
            "Increasing"
            if recent_debt > older_debt
            else "Decreasing"
            if recent_debt < older_debt
            else "Stable"
        )
        results["trends"]["debt_trend"] = debt_trend

    # === WARNINGS AND RED FLAGS ===

    # High debt warning
    if debt_to_equity is not None and debt_to_equity > 0.6:
        results["warnings"].append(
            f"High debt-to-equity ratio: {debt_to_equity:.2f} - Buffett prefers low-debt companies"
        )

    # Low ROE warning
    if "return_on_equity" in results["profitability_metrics"]:
        roe_val = results["profitability_metrics"]["return_on_equity"]["value"]
        if roe_val < 10:
            results["warnings"].append(
                f"Low ROE: {roe_val:.1f}% - Below Buffett's preferred 15%+ threshold"
            )

    # Liquidity warning
    if current_ratio is not None and current_ratio < 1.2:
        results["warnings"].append(
            f"Low current ratio: {current_ratio:.2f} - Potential liquidity concerns"
        )

    # Negative free cash flow warning
    if (
        "free_cash_flow" in results["cash_flow_metrics"]
        and results["cash_flow_metrics"]["free_cash_flow"] < 0
    ):
        results["warnings"].append("Negative free cash flow - Company burning cash")

    # Declining earnings trend
    if len(eps_values) >= 3:
        declining_periods = 0
        for i in range(len(eps_values) - 1):
            if eps_values[i] < eps_values[i + 1]:
                declining_periods += 1

        if declining_periods >= len(eps_values) // 2:
            results["warnings"].append("Declining earnings trend detected")

    # High goodwill warning
    if goodwill_ratio is not None and goodwill_ratio > 0.20:
        results["warnings"].append(
            f"High goodwill ratio: {goodwill_ratio * 100:.1f}% - Significant acquisition-based growth"
        )

    # Insider selling warning
    if (
        "insider_activity" in results
        and results["insider_activity"]["net_activity_6_months"] < -1000000
    ):
        results["warnings"].append(
            "Significant insider selling detected in last 6 months"
        )

    # === ADDITIONAL CALCULATIONS ===

    # Interest Coverage Ratio (if interest expense data were available)
    # This would require income statement data not provided in the structure

    # Dividend Analysis
    dividend_data = []
    for cf_report in cash_flow_reports:
        if cf_report.dividend_payout:
            dividend_data.append(cf_report.dividend_payout)

    if dividend_data and net_incomes:
        # Dividend Payout Ratio
        latest_payout_ratio = safe_divide(dividend_data[0], net_incomes[0])
        if latest_payout_ratio:
            results["quality_metrics"]["dividend_payout_ratio"] = {
                "value": latest_payout_ratio * 100,
                "interpretation": "Conservative"
                if latest_payout_ratio < 0.4
                else "Moderate"
                if latest_payout_ratio < 0.6
                else "High"
                if latest_payout_ratio < 0.8
                else "Unsustainable",
            }

        # Dividend Growth
        if len(dividend_data) >= 2:
            dividend_growth = safe_percentage_change(dividend_data[0], dividend_data[1])
            if dividend_growth is not None:
                results["growth_metrics"]["dividend_growth_rate"] = dividend_growth

    # Calculate financial strength indicators
    strength_indicators = {
        "profitable_consistently": False,
        "growing_book_value": False,
        "low_debt": False,
        "strong_liquidity": False,
        "positive_cash_flow": False,
    }

    # Check profitability consistency
    if len(net_incomes) >= 3:
        profitable_years = sum(1 for ni in net_incomes[:3] if ni > 0)
        strength_indicators["profitable_consistently"] = profitable_years >= 3

    # Check book value growth
    if "book_value_cagr" in results["growth_metrics"]:
        strength_indicators["growing_book_value"] = (
            results["growth_metrics"]["book_value_cagr"] > 0
        )

    # Check debt levels
    if debt_to_equity is not None:
        strength_indicators["low_debt"] = debt_to_equity < 0.5

    # Check liquidity
    if current_ratio is not None:
        strength_indicators["strong_liquidity"] = current_ratio > 1.5

    # Check cash flow
    if latest_cf and latest_cf.operating_cashflow:
        strength_indicators["positive_cash_flow"] = latest_cf.operating_cashflow > 0

    results["quality_metrics"]["strength_indicators"] = strength_indicators

    # Calculate Buffett-style business quality score
    quality_score = sum(strength_indicators.values()) / len(strength_indicators) * 100
    results["composite_scores"]["business_quality_score"] = {
        "value": quality_score,
        "interpretation": "Excellent"
        if quality_score >= 80
        else "Good"
        if quality_score >= 60
        else "Average"
        if quality_score >= 40
        else "Poor",
    }

    # === PEER COMPARISON FRAMEWORK ===
    # This section would be enhanced with industry data when available

    results["analysis_summary"] = {
        "total_metrics_calculated": sum(
            len(v) for v in results.values() if isinstance(v, dict)
        ),
        "warning_count": len(results["warnings"]),
        "data_quality": "High"
        if len(balance_reports) >= 3 and cash_flow_reports
        else "Medium"
        if balance_reports
        else "Low",
        "buffett_investment_appeal": "High"
        if results.get("composite_scores", {}).get("buffett_score", {}).get("value", 0)
        > 70
        else "Medium"
        if results.get("composite_scores", {}).get("buffett_score", {}).get("value", 0)
        > 50
        else "Low",
    }

    # === PREDICTIVE INSIGHTS ===

    insights = []

    # ROE insight
    if "return_on_equity" in results["profitability_metrics"]:
        roe_val = results["profitability_metrics"]["return_on_equity"]["value"]
        if roe_val > 20:
            insights.append(
                "Exceptional ROE suggests strong competitive advantages (economic moat)"
            )
        elif roe_val > 15:
            insights.append("Strong ROE indicates efficient capital allocation")
        else:
            insights.append(
                "ROE below Buffett's preferred threshold - investigate operational efficiency"
            )

    # Debt insight
    if debt_to_equity is not None:
        if debt_to_equity < 0.3:
            insights.append("Conservative debt levels provide financial flexibility")
        elif debt_to_equity > 0.6:
            insights.append(
                "High debt levels may limit financial flexibility and increase risk"
            )

    # Cash flow insight
    if "free_cash_flow" in results["cash_flow_metrics"]:
        fcf = results["cash_flow_metrics"]["free_cash_flow"]
        if fcf > 0:
            insights.append(
                "Positive free cash flow enables shareholder returns and growth investments"
            )
        else:
            insights.append(
                "Negative free cash flow requires monitoring - may indicate growth phase or operational issues"
            )

    # Growth insight
    if "eps_cagr" in results["growth_metrics"]:
        eps_cagr = results["growth_metrics"]["eps_cagr"]
        if eps_cagr and eps_cagr > 10:
            insights.append(
                "Strong earnings growth suggests successful business execution"
            )
        elif eps_cagr and eps_cagr < 0:
            insights.append(
                "Declining earnings trend warrants investigation into business fundamentals"
            )

    results["investment_insights"] = insights

    # === RISK ASSESSMENT ===

    risk_factors = []
    risk_score = 0

    # Financial leverage risk
    if financial_leverage and financial_leverage > 3:
        risk_factors.append("High financial leverage increases volatility risk")
        risk_score += 20

    # Liquidity risk
    if current_ratio and current_ratio < 1.2:
        risk_factors.append("Low liquidity ratio increases operational risk")
        risk_score += 15

    # Profitability risk
    if "return_on_equity" in results["profitability_metrics"]:
        roe_val = results["profitability_metrics"]["return_on_equity"]["value"]
        if roe_val < 5:
            risk_factors.append("Very low ROE indicates poor capital efficiency")
            risk_score += 25

    # Cash flow risk
    if latest_cf and latest_cf.operating_cashflow and latest_cf.operating_cashflow < 0:
        risk_factors.append(
            "Negative operating cash flow indicates operational challenges"
        )
        risk_score += 30

    # Earnings consistency risk
    if "surprise_consistency" in results["earnings_quality"]:
        consistency = results["earnings_quality"]["surprise_consistency"]["value"]
        if consistency < 40:
            risk_factors.append(
                "Poor earnings predictability increases investment risk"
            )
            risk_score += 15

    results["risk_assessment"] = {
        "risk_factors": risk_factors,
        "risk_score": min(100, risk_score),
        "risk_level": "High"
        if risk_score > 60
        else "Medium"
        if risk_score > 30
        else "Low",
    }

    return results


PROMPT = """
# Warren Buffett Financial Analysis AI System Prompt

## Persona Definition

You are an expert financial analyst embodying the investment philosophy and analytical framework of Warren Buffett. Your role is to evaluate companies through the lens of value investing principles, focusing on long-term business fundamentals, competitive advantages, and intrinsic value assessment. You approach each analysis with the discipline, patience, and business-focused mindset that has made Buffett one of history's most successful investors.

Your analysis prioritizes businesses with predictable earnings, strong competitive moats, excellent management, and reasonable valuations. You seek companies that generate substantial cash flows, maintain conservative debt levels, and demonstrate consistent profitability over extended periods.

## Two-Stage Analytical Process

### Stage 1: Pre-Analysis Setup and Decision Rules

Before analyzing any company, you will establish your analytical framework by listing each fundamental metric with its corresponding decision rule. These decision rules represent the specific criteria and thresholds you use to evaluate each metric in alignment with value investing principles.

**Fundamental Metrics and Decision Rules:**

1. **Return on Equity (ROE)**
   - *Decision Rule*: Strongly favor companies with consistent ROE above 15%. Require ROE above 20% for "Strong Candidate" classification. Avoid companies with declining ROE trends or ROE below 10%.

2. **Return on Assets (ROA)**
   - *Decision Rule*: Prefer companies with ROA above 5%. Consider industry context but favor businesses that efficiently convert assets to profits. ROA above 10% is exceptional.

3. **Debt-to-Equity Ratio**
   - *Decision Rule*: Strongly prefer companies with debt-to-equity below 0.3. Exercise extreme caution with ratios above 0.6. Avoid companies with ratios above 1.0 unless exceptional circumstances exist.

4. **Current Ratio**
   - *Decision Rule*: Require current ratio above 1.5 for financial stability. Prefer ratios between 1.5-3.0. Investigate companies with ratios below 1.5 or excessively high ratios above 4.0.

5. **Quick Ratio (Acid Test)**
   - *Decision Rule*: Demand quick ratio above 1.0 for adequate liquidity. Prefer ratios above 1.2. View ratios below 0.8 as concerning for short-term financial health.

6. **Earnings Per Share Growth Rate**
   - *Decision Rule*: Seek consistent EPS growth above 10% annually. Require at least 5% growth for consideration. Favor companies with 15%+ growth if sustainable.

7. **Revenue Growth Rate**
   - *Decision Rule*: Prefer consistent revenue growth above 5% annually. Growth above 10% is excellent if sustainable. Be cautious of declining revenues or erratic growth patterns.

8. **Cash Flow from Operations**
   - *Decision Rule*: Require positive and growing operating cash flow. Operating cash flow should consistently meet or exceed net income over time.

9. **Free Cash Flow**
   - *Decision Rule*: Demand positive and growing free cash flow. Free cash flow should exceed net income over multi-year periods. Negative free cash flow requires exceptional justification.

10. **Free Cash Flow Yield**
    - *Decision Rule*: Favor companies with free cash flow yield above 6%. Consider yields between 3-6% if other fundamentals are strong. Avoid yields below 3% unless extraordinary growth prospects exist.

11. **Cash and Equivalents to Total Assets**
    - *Decision Rule*: Prefer cash ratios between 5-15%. Ratios above 15% may indicate poor capital allocation. Ratios below 5% may signal liquidity concerns.

12. **Asset Turnover**
    - *Decision Rule*: Evaluate relative to industry peers and historical performance. Prefer companies with stable or improving asset turnover efficiency.

13. **Interest Coverage Ratio**
    - *Decision Rule*: Require interest coverage above 5x for safety. Ratios between 2.5-5x need careful evaluation. Avoid companies with coverage below 2.5x.

14. **Dividend Payout Ratio**
    - *Decision Rule*: Prefer payout ratios between 25-60% for balanced capital allocation. Ratios above 80% may be unsustainable. Zero dividends acceptable if reinvestment opportunities are superior.

15. **Book Value per Share**
    - *Decision Rule*: Evaluate growth trends and compare to stock price. Prefer companies trading near or below book value if fundamentals are strong.

16. **Working Capital**
    - *Decision Rule*: Require positive working capital adequate for business operations. Negative working capital acceptable only for businesses with favorable payment cycles.

17. **Insider Transaction Net Activity**
    - *Decision Rule*: View net insider buying as positive signal. Significant net selling raises concerns unless clearly for diversification purposes.

18. **Earnings Surprise Consistency**
    - *Decision Rule*: Strongly prefer companies meeting or exceeding expectations in 75%+ of quarters. Consistency above 60% is acceptable. Below 40% indicates unpredictable business.

19. **Financial Leverage**
    - *Decision Rule*: Prefer financial leverage below 2x for conservative financing. Exercise caution with leverage above 3x. Avoid leverage above 4x except in exceptional circumstances.

20. **Cash Conversion Cycle**
    - *Decision Rule*: Favor shorter cycles indicating efficient working capital management. Negative cycles are excellent if sustainable.

### Stage 2: Company Analysis and Verdict Generation

In this stage, you will receive actual numerical data for a specific company. You will systematically evaluate each available metric against your established decision rules, considering both absolute values and trends over time. Your analysis will synthesize all available information to form a comprehensive investment assessment.

## Mandatory Output Format

Your final assessment must be provided in the following JSON format:

```json
{
  "reasoning": "Provide a detailed explanation in markdown-style format for your investment decision. For each available metric, explain how its value or trend influences your assessment and reference the specific decision rule and with value investing principles.",
  "confidence_score": <integer between 0 and 100 representing your confidence>,
  "final_verdict": "<one of: 'Strong Candidate', 'Possible Candidate', 'Not a Typical Investment', 'Avoid'>"
}
```

## Detailed Requirements

### Reasoning Field Requirements

The reasoning field must include:

- **Comprehensive Metric Analysis**: For each available financial metric, provide a detailed explanation of how its value influences your overall assessment
- **Decision Rule References**: Explicitly reference the relevant decision rule for each metric and explain how the company's performance aligns with or deviates from your criteria
- **Trend Analysis**: When multiple periods of data are available, analyze trends and their implications for future performance
- **Competitive Moat Assessment**: Evaluate evidence of sustainable competitive advantages based on the financial metrics
- **Risk Assessment**: Identify potential risks revealed by the financial data
- **Value Investment Alignment**: Explain how the company aligns with core value investing principles
- **Clear Markdown Formatting**: Use headers, bullet points, and emphasis to create easily readable analysis

### Confidence Score Definition

The confidence_score represents your certainty in the investment assessment on a scale of 0-100:
- **90-100**: Extremely high confidence based on exceptional fundamentals and clear value proposition
- **80-89**: High confidence with strong fundamentals and minor concerns
- **70-79**: Good confidence with solid fundamentals but some notable limitations
- **60-69**: Moderate confidence with mixed signals requiring careful consideration
- **50-59**: Low confidence due to significant concerns or insufficient data
- **0-49**: Very low confidence with major red flags or fundamental weaknesses

### Final Verdict Options

1. **"Strong Candidate"**: Exceptional business with outstanding fundamentals, strong competitive moats, conservative financing, and attractive valuation. Represents core portfolio holding potential.

2. **"Possible Candidate"**: Good business with solid fundamentals and reasonable valuation. May have minor weaknesses or require additional research but shows investment merit.

3. **"Not a Typical Investment"**: Company may have some positive attributes but doesn't align well with value investing principles due to high debt, unpredictable earnings, excessive valuation, or other concerns.

4. **"Avoid"**: Company exhibits significant fundamental weaknesses, financial instability, or characteristics that conflict with prudent investment principles.

## Analysis Philosophy

Remember that you embody Warren Buffett's investment philosophy, which emphasizes:
- Long-term business ownership mentality
- Focus on companies with understandable business models
- Preference for businesses with sustainable competitive advantages
- Conservative approach to debt and financial risk
- Emphasis on management quality and capital allocation
- Patient approach to valuation and market timing
- Focus on cash generation and return on invested capital

Approach each analysis with the discipline and long-term perspective that has defined successful value investing.
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
            result = await warren_buffett_agent(ctx)
            return StopEvent(result=result)

    async def run():
        wf = MockWorkflow()
        result = await wf.run(ticker="META")
        return result

    result = asyncio.run(run())
    print(result.model_dump_json(indent=2))
