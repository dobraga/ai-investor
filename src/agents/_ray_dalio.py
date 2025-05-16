from logging import getLogger
from pathlib import Path
from typing import Any, Dict

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.workflow import Context

from src.agents._signal import SignalEvent
from src.tools import AlphaVantageClient, TickerData
from src.utils.format import id_to_name

ID = Path(__file__).stem
NAME = id_to_name(ID)
LOG = getLogger(__name__)


async def ray_dalio_agent(context: Context):
    ticker: str = await context.get("ticker")

    LOG.info(f"Running {NAME} agent {ticker}")
    llm = await context.get("llm_struct")
    client: AlphaVantageClient = await context.get("alpha_vantage_client")

    data = client.get_ticker_data(ticker)

    metrics = compute_metrics(data)
    analysis = generate_output(llm, metrics)

    LOG.info(f"Finished {NAME} agent {ticker}")

    return analysis


def compute_metrics(ticker_data: TickerData) -> Dict[str, Any]:
    """
    Extracts key financial metrics from TickerData relevant to a Ray Dalio-like
    analysis, focusing on the most recent data.

    Args:
        ticker_data: An instance of TickerData containing financial reports.

    Returns:
        A dictionary containing the extracted metrics.
    """
    metrics = {}

    # Extracting from Overview
    overview = ticker_data.overview
    metrics["Market Capitalization"] = overview.market_capitalization
    metrics["PE Ratio (TTM)"] = overview.pe_ratio
    metrics["Forward PE"] = overview.forward_pe
    metrics["Price to Book Ratio"] = overview.price_to_book_ratio
    metrics["Price to Sales Ratio (TTM)"] = overview.price_to_sales_ratio_ttm
    metrics["Return on Assets (TTM)"] = overview.return_on_assets_ttm
    metrics["Return on Equity (TTM)"] = overview.return_on_equity_ttm
    metrics["Operating Margin (TTM)"] = overview.operating_margin_ttm
    metrics["Profit Margin"] = overview.profit_margin
    metrics["Diluted EPS (TTM)"] = overview.diluted_eps_ttm
    metrics["Quarterly Earnings Growth YOY"] = overview.quarterly_earnings_growth_yoy
    metrics["Quarterly Revenue Growth YOY"] = overview.quarterly_revenue_growth_yoy
    metrics["Beta"] = overview.beta

    # Extracting from Balance Sheet (Most Recent Annual)
    if ticker_data.balance_sheet.annual_reports:
        latest_annual_bs = ticker_data.balance_sheet.annual_reports[0]
        metrics["Total Assets (Most Recent Annual)"] = latest_annual_bs.total_assets
        metrics["Total Liabilities (Most Recent Annual)"] = (
            latest_annual_bs.total_liabilities
        )
        metrics["Total Shareholder Equity (Most Recent Annual)"] = (
            latest_annual_bs.total_shareholder_equity
        )
        metrics[
            "Total Debt (Most Recent Annual - approximated as Short-Long Term Debt Total)"
        ] = latest_annual_bs.short_long_term_debt_total

    # Extracting from Cash Flow (Most Recent Annual)
    if ticker_data.cash_flow.annual_reports:
        latest_annual_cf = ticker_data.cash_flow.annual_reports[0]
        metrics["Operating Cashflow (Most Recent Annual)"] = (
            latest_annual_cf.operating_cashflow
        )
        metrics["Capital Expenditures (Most Recent Annual)"] = (
            latest_annual_cf.capital_expenditures
        )
        # Using Net Income from Cash Flow for consistency with cash generation
        metrics["Net Income (Most Recent Annual)"] = latest_annual_cf.net_income

    # Note: We are prioritizing the most recent annual data as per the prompt.
    # Quarterly data is available but not explicitly requested for these specific metrics
    # in the context of "principal metrics Ray Dalio uses", which tend to be broader
    # or focus on longer-term cycles. If quarterly analysis was needed, we would
    # access ticker_data.balance_sheet.quarterly_reports[0], etc.

    return metrics


def generate_output(llm, metrics: dict) -> SignalEvent:
    message = f"Based on the following data, create the investment signal. Analysis Data: {metrics}"

    chat = [
        ChatMessage.from_str(PROMPT, MessageRole.SYSTEM),
        ChatMessage.from_str(message, MessageRole.USER),
    ]

    response: SignalEvent = llm.chat(chat).raw
    response.agent = NAME
    return response


PROMPT = """
You are an AI specializing in financial analysis with a focus on principles aligned with Ray Dalio's approach, emphasizing a deep understanding of how the "economic machine" affects different assets and prioritizing risk management and diversification.

Your task is to analyze the provided TickerData for a specific company and generate a structured analysis based on the following financial metrics and associated rules. While Ray Dalio's primary focus is macroeconomics and asset allocation across different economic regimes, this analysis focuses on the fundamental characteristics of an individual company as a component asset within a diversified portfolio.

Analysis Steps:

Process Data: Analyze the provided TickerData object.

Apply Rules: Evaluate the company based on the following metrics and their associated considerations.

Provide Reasoning: For each metric considered, explain its current value, its trend (if applicable from the latest data), and what it suggests about the company's financial health, valuation, growth prospects, or risk profile in the context of a potential investment. Connect these points to how the company might perform in different economic environments (e.g., inflationary growth, deflationary recession), even if implicitly.

Synthesize Findings: Combine the insights from individual metrics to form a holistic view of the company.

Confidence Score: Provide a confidence score (0-100) for the overall analysis and verdict, indicating the certainty based on the available data and the clarity of the signals.

Final Verdict: Deliver a final verdict on the company's attractiveness as an investment from this analytical perspective (e.g., Favorable, Neutral, Unfavorable).
Metrics and Considerations for Decision-Making:

Market Capitalization:
Consideration: Assesses company size. Large caps may offer stability, while small/mid caps may offer higher growth potential but also higher risk. Consider its position within its sector/industry.

PE Ratio (TTM) & Forward PE:
Consideration: Evaluates current and future earnings valuation. Compare to industry peers and historical levels. High PE might indicate high growth expectations or overvaluation; low PE might suggest undervaluation or poor prospects.

Price to Book Ratio:
Consideration: Compares market value to book value. Useful for asset-heavy companies. A low P/B might suggest undervaluation; a high P/B might indicate overvaluation or significant intangible assets.

Price to Sales Ratio (TTM):
Consideration: Values company relative to revenue. Useful for companies with inconsistent earnings. Compare to industry. High P/S might indicate high growth expectations or overvaluation.

Return on Assets (TTM):
Consideration: Measures asset efficiency. Higher ROA indicates better utilization of assets to generate profit. Look for stable or improving trends.

Return on Equity (TTM):
Consideration: Measures profitability relative to shareholder investment. Higher ROE indicates better profit generation from equity. Look for stable or improving trends. Be mindful of high ROE driven by excessive debt.

Operating Margin (TTM):
Consideration: Indicates profitability of core operations. Higher margins suggest better operational efficiency and pricing power. Look for stable or improving trends.

Profit Margin:
Consideration: Overall profitability after all expenses. Higher margins indicate better cost management and pricing power. Look for stable or improving trends.

Diluted EPS (TTM):
Consideration: Represents earnings per share considering dilution. Look for positive and growing EPS.

Quarterly Earnings Growth YOY:
Consideration: Recent earnings momentum. Positive growth is generally favorable, but consider sustainability and comparison to peers/industry.

Quarterly Revenue Growth YOY:
Consideration: Recent revenue momentum. Positive growth is generally favorable, but consider sustainability and comparison to peers/industry.

Total Assets (Most Recent Annual):
Consideration: Provides context for the company's scale and asset base.

Total Liabilities (Most Recent Annual):
Consideration: Assesses the company's obligations. High liabilities relative to assets or equity can indicate higher financial risk.

Total Shareholder Equity (Most Recent Annual):
Consideration: Represents the owners' stake. Growth in equity is generally positive, but assess the drivers (earnings vs. new issuance).

Total Debt (Most Recent Annual):
Consideration: Assesses the company's leverage. High debt levels can increase financial risk, especially in rising interest rate environments. Consider the company's ability to service its debt (though specific interest coverage ratios are not provided in the TickerData).

Operating Cashflow (Most Recent Annual):
Consideration: Measures cash generated from core business. Positive and growing operating cash flow is crucial for sustainability, investment, and debt repayment.

Capital Expenditures (Most Recent Annual):
Consideration: Investment in long-term assets. Compare to operating cash flow to see if the company can fund its investments internally. Significant capex might indicate growth investment or necessary maintenance.

Net Income (Most Recent Annual):
Consideration: The bottom line profit. Look for positive and stable or growing net income. Assess quality of earnings (e.g., is it driven by core operations or one-time gains).

Beta:
Consideration: Measures the stock's sensitivity to market movements. Lower beta might be preferred for stability in certain portfolio constructions; higher beta might offer greater potential gains (and losses) in market swings.
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
            await ctx.set(
                "alpha_vantage_client", AlphaVantageClient(environ["ALPHA_VANTAGE"])
            )
            await ctx.set("ticker", ev.ticker)
            result = await ray_dalio_agent(ctx)
            return StopEvent(result=result)

    async def run():
        wf = MockWorkflow()
        result = await wf.run(ticker="META")
        return result

    result = asyncio.run(run())
    print(result.model_dump_json(indent=2))
