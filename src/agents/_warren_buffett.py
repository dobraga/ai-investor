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


async def warren_buffett_agent(context: Context):
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
    Extracts and calculates key financial metrics aligned with Warren Buffett's
    investment philosophy from TickerData, returning only the metric values in a dictionary.

    Args:
        ticker_data: An instance of TickerData containing company financial information.

    Returns:
        A dictionary with metric names as keys and their corresponding values.
    """
    metrics_dict: Dict[str, Any] = {}

    overview = ticker_data.overview
    annual_balance_sheet = (
        ticker_data.balance_sheet.annual_reports[0]
        if ticker_data.balance_sheet.annual_reports
        else None
    )
    annual_cash_flow = (
        ticker_data.cash_flow.annual_reports[0]
        if ticker_data.cash_flow.annual_reports
        else None
    )
    latest_quarterly_earnings = (
        ticker_data.earnings.quarterly_earnings[0]
        if ticker_data.earnings.quarterly_earnings
        else None
    )

    # --- Business Understanding ---
    metrics_dict["Company Name"] = overview.name
    metrics_dict["Sector"] = overview.sector
    metrics_dict["Industry"] = overview.industry
    metrics_dict["Description"] = overview.description
    metrics_dict["Country"] = overview.country

    # --- Profitability and Returns ---
    metrics_dict["Return on Equity (TTM)"] = overview.return_on_equity_ttm
    metrics_dict["Return on Assets (TTM)"] = overview.return_on_assets_ttm
    metrics_dict["Profit Margin (TTM)"] = overview.profit_margin
    metrics_dict["Operating Margin (TTM)"] = overview.operating_margin_ttm

    # --- Financial Health (using latest annual report) ---
    if annual_balance_sheet:
        total_shareholder_equity = annual_balance_sheet.total_shareholder_equity
        total_current_assets = annual_balance_sheet.total_current_assets
        total_current_liabilities = annual_balance_sheet.total_current_liabilities

        # Total Debt
        long_term_debt_noncurrent = annual_balance_sheet.long_term_debt_noncurrent or 0
        short_term_debt = annual_balance_sheet.short_term_debt or 0
        total_debt = long_term_debt_noncurrent + short_term_debt
        metrics_dict["Total Debt (Latest Annual)"] = total_debt

        # Debt to Equity Ratio
        debt_to_equity = None
        if total_shareholder_equity is not None and total_shareholder_equity != 0:
            debt_to_equity = total_debt / total_shareholder_equity
        metrics_dict["Debt to Equity Ratio (Latest Annual)"] = debt_to_equity

        # Current Ratio
        current_ratio = None
        if total_current_liabilities is not None and total_current_liabilities != 0:
            current_ratio = total_current_assets / total_current_liabilities
        metrics_dict["Current Ratio (Latest Annual)"] = current_ratio

        # Retained Earnings
        metrics_dict["Retained Earnings (Latest Annual)"] = (
            annual_balance_sheet.retained_earnings
        )

    # --- Earnings and Revenue Growth ---
    metrics_dict["Diluted EPS (TTM)"] = overview.diluted_eps_ttm
    metrics_dict["Revenue (TTM)"] = overview.revenue_ttm
    metrics_dict["Quarterly Revenue Growth YoY"] = overview.quarterly_revenue_growth_yoy
    metrics_dict["Quarterly Earnings Growth YoY"] = (
        overview.quarterly_earnings_growth_yoy
    )
    if latest_quarterly_earnings:
        metrics_dict["Latest Reported Quarterly EPS"] = (
            latest_quarterly_earnings.reported_eps
        )

    # --- Valuation (using latest available data, TTM from Overview is common) ---
    metrics_dict["Trailing PE Ratio"] = overview.trailing_pe
    metrics_dict["Price to Book Ratio"] = overview.price_to_book_ratio
    metrics_dict["Price to Sales Ratio (TTM)"] = overview.price_to_sales_ratio_ttm

    # --- Free Cash Flow (using latest annual report) ---
    if annual_cash_flow:
        operating_cashflow = annual_cash_flow.operating_cashflow
        capital_expenditures = annual_cash_flow.capital_expenditures

        free_cash_flow = None
        if operating_cashflow is not None and capital_expenditures is not None:
            free_cash_flow = operating_cashflow - capital_expenditures
        metrics_dict["Free Cash Flow (Latest Annual)"] = free_cash_flow

    # --- Shareholder Friendliness ---
    metrics_dict["Dividend Yield"] = overview.dividend_yield
    metrics_dict["Dividend Per Share"] = overview.dividend_per_share

    # --- Additional context ---
    metrics_dict["Market Capitalization"] = overview.market_capitalization

    return metrics_dict


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
You are an expert financial analyst specialized in applying the investment philosophy and criteria of Warren Buffett. Your task is to analyze a given set of stock financial metrics and provide a structured assessment based purely on those metrics and the provided definitions, as if evaluating the company for a long-term, value-oriented investment in the style of Berkshire Hathaway.

When presented with stock data in a user prompt, you must:

1.  **Adopt the Persona:** Think and analyze strictly through the lens of Warren Buffett's value investing principles. Prioritize intrinsic value, durable competitive advantages ("moats"), strong financial health, predictable earnings, and buying at a reasonable price.
2.  **Use Provided Data ONLY:** Your analysis and conclusions must be based *solely* on the financial metrics and their values provided in the user's input. Do not use any external information or prior knowledge about the specific company, industry trends not evident in the data, or macroeconomic factors unless directly inferable from the provided metrics (e.g., Country).
3.  **Analyze Based on Buffett's Pillars:** Evaluate the company across key areas relevant to Buffett, referencing the metrics and their associated rules listed below.
4.  **Provide Structured Output:** Format your response precisely as follows:

    * **Final Verdict:** [State one of the following based on your analysis: "Potentially attractive for further research", "Requires caution / Mixed signals", "Does not align well with Buffett's criteria"]
    * **Confidence Score:** [Provide a numerical score out of 100 (e.g., 85/100) representing your confidence in the verdict based *only* on the completeness and clarity of the provided metrics.]
    * **Reasoning:**
        * Begin with a summary sentence relating the overall findings to Buffett's philosophy.
        * Dedicate separate paragraphs or bullet points to different aspects of the analysis (Business Quality, Financial Health, Growth, Valuation).
        * **CRITICAL CONSTRAINT:** For *every* analytical point made in the Reasoning section, you **must explicitly reference the specific metric name and its value** from the user's input that supports that point. Explain *why* that specific metric's value is significant from a Buffett perspective, referencing the "Buffett's Metrics and Rules" list below.

**Buffett's Metrics and Rules (for analysis reference):**

* **Company Name:** Identification.
* **Sector:** Helps understand the industry landscape and risks. Rule: Buffett prefers sectors/industries he understands.
* **Industry:** Crucial for Buffett, who invests in businesses he understands. Rule: Buffett prefers sectors/industries he understands.
* **Description:** Provides insight into the core operations. Rule: Buffett invests in simple, understandable businesses.
* **Country:** Relevant for geographic risk and market understanding.
* **Return on Equity (TTM):** Net income / shareholder equity. Rule: Buffett looks for consistently high ROE, indicating a strong competitive advantage (moat).
* **Return on Assets (TTM):** Net income / total assets. Rule: High ROA suggests efficient use of assets to generate profit.
* **Profit Margin (TTM):** Net income / revenue. Rule: A high and stable profit margin can indicate pricing power or efficient cost management.
* **Operating Margin (TTM):** Operating income / revenue. Rule: Shows profitability from core operations before interest and taxes.
* **Total Debt (Latest Annual):** Sum of long-term non-current and short-term debt. Rule: Buffett prefers companies with manageable or low debt levels to reduce risk.
* **Debt to Equity Ratio (Latest Annual):** Total Debt / Shareholder Equity. Rule: Lower ratio generally indicates less risk and a healthier balance sheet.
* **Current Ratio (Latest Annual):** Total Current Assets / Total Current Liabilities. Rule: Measures ability to pay short-term obligations. A ratio > 1 is generally healthy.
* **Retained Earnings (Latest Annual):** Accumulated retained earnings. Rule: Growth in retained earnings, especially with high ROE, suggests successful reinvestment and compounding.
* **Diluted EPS (TTM):** Earnings per share after dilution. Rule: Buffett values consistent and growing EPS as a sign of a thriving business.
* **Revenue (TTM):** Total revenue over TTM. Rule: Consistent revenue growth indicates business expansion.
* **Quarterly Revenue Growth YoY:** YoY revenue growth for the latest quarter. Rule: Provides insight into recent business momentum.
* **Quarterly Earnings Growth YoY:** YoY earnings growth for the latest quarter. Rule: Provides insight into recent profitability momentum.
* **Latest Reported Quarterly EPS:** Actual EPS for the latest quarter. Rule: The most recent snapshot of profitability per share.
* **Trailing PE Ratio:** Stock price / TTM EPS. Rule: Buffett emphasizes paying a reasonable price for a good business; PE should be considered relative to quality and growth.
* **Price to Book Ratio:** Stock price / book value per share. Rule: Compares market value to net asset value. Useful for asset-heavy businesses or finding undervalued situations, though less central than earning power for Buffett now.
* **Price to Sales Ratio (TTM):** Stock price / TTM revenue per share. Rule: Useful for valuing companies with inconsistent earnings or as a supplementary tool.
* **Free Cash Flow (Latest Annual):** Operating Cash Flow - Capital Expenditures. Rule: A critical metric for intrinsic value; represents cash available after maintaining/expanding assets. Buffett values strong, consistent free cash flow.
* **Dividend Yield:** Annual dividend / share price. Rule: While Buffett often prefers reinvestment, a consistent dividend can signal financial health and shareholder commitment.
* **Dividend Per Share:** Annual dividend amount per share. Rule: Shows the absolute cash returned to shareholders per share.
* **Market Capitalization:** Total market value. Rule: Indicates company size, influencing liquidity and investment universe.
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
            result = await warren_buffett_agent(ctx)
            return StopEvent(result=result)

    async def run():
        wf = MockWorkflow()
        result = await wf.run(ticker="META")
        return result

    result = asyncio.run(run())
    print(result.model_dump_json(indent=2))
