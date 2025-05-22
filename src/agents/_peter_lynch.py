from logging import getLogger
from pathlib import Path
from typing import Optional

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.workflow import Context

from src.agents._signal import SignalEvent
from src.tools import AlphaVantageClient, TickerData
from src.tools._alpha.earnings import AnnualEarning
from src.utils.format import id_to_name

ID = Path(__file__).stem
NAME = id_to_name(ID)
LOG = getLogger(__name__)


async def peter_lynch_agent(context: Context):
    ticker: str = await context.get("ticker")

    LOG.info(f"Running {NAME} agent {ticker}")
    llm = await context.get("llm")
    llm = llm.as_structured_llm(SignalEvent)
    client: AlphaVantageClient = await context.get("alpha_client")

    data = await client.aget_ticker_data(ticker)

    metrics = compute_metrics(data)
    analysis = generate_output(llm, metrics)

    LOG.info(f"Finished {NAME} agent {ticker}")

    return analysis


def compute_metrics(ticker_data: TickerData, growth_years: int = 5) -> dict[str, float]:
    """
    Calculates and extracts key Peter Lynch metrics from TickerData.

    Args:
        ticker_data: An instance of the TickerData Pydantic model.
        growth_years: The number of years to use for calculating historical EPS growth.

    Returns:
        A dictionary containing the calculated/extracted metrics.
    """
    metrics_data: dict[str, float | str] = {}

    overview = ticker_data.overview
    balance_sheet = ticker_data.balance_sheet
    cash_flow = ticker_data.cash_flow
    earnings = ticker_data.earnings

    # 1. PEG Ratio (Extracted directly)
    metrics_data["PEG Ratio"] = overview.peg_ratio

    # 2. Historical EPS Growth Rate (Calculated)
    eps_growth = calculate_eps_growth_rate(earnings.annual_earnings, growth_years)
    metrics_data[f"EPS Growth Rate ({growth_years}yr CAGR %)"] = eps_growth

    # 3. P/E Ratio (Extracted)
    # Use Trailing PE if available, otherwise use PE Ratio (TTM)
    pe_ratio = (
        overview.trailing_pe if overview.trailing_pe is not None else overview.pe_ratio
    )
    metrics_data["P/E Ratio"] = pe_ratio

    # Use the most recent annual balance sheet for financial health metrics
    latest_annual_bs = (
        balance_sheet.annual_reports[0] if balance_sheet.annual_reports else None
    )

    # 4. Debt-to-Equity Ratio (Calculated)
    if (
        latest_annual_bs
        and latest_annual_bs.total_liabilities is not None
        and latest_annual_bs.total_shareholder_equity is not None
    ):
        if latest_annual_bs.total_shareholder_equity != 0:
            metrics_data["Debt-to-Equity Ratio"] = (
                latest_annual_bs.total_liabilities
                / latest_annual_bs.total_shareholder_equity
            )
        else:
            metrics_data["Debt-to-Equity Ratio"] = (
                float("inf")
                if latest_annual_bs.total_liabilities is not None
                and latest_annual_bs.total_liabilities > 0
                else 0.0
            )  # Handle division by zero
    else:
        metrics_data["Debt-to-Equity Ratio"] = None

    # 5. Current Ratio (Calculated)
    if (
        latest_annual_bs
        and latest_annual_bs.total_current_assets is not None
        and latest_annual_bs.total_current_liabilities is not None
    ):
        if latest_annual_bs.total_current_liabilities != 0:
            metrics_data["Current Ratio"] = (
                latest_annual_bs.total_current_assets
                / latest_annual_bs.total_current_liabilities
            )
        else:
            metrics_data["Current Ratio"] = (
                float("inf")
                if latest_annual_bs.total_current_assets is not None
                and latest_annual_bs.total_current_assets > 0
                else 0.0
            )  # Handle division by zero
    else:
        metrics_data["Current Ratio"] = None

    # 6. Net Cash (Cash & Short-Term Investments) (Calculated)
    if (
        latest_annual_bs
        and latest_annual_bs.cash_and_cash_equivalents_at_carrying_value is not None
        and latest_annual_bs.short_term_investments is not None
    ):
        metrics_data["Cash and Short-Term Investments"] = (
            latest_annual_bs.cash_and_cash_equivalents_at_carrying_value
            + latest_annual_bs.short_term_investments
        )
    elif (
        latest_annual_bs
        and latest_annual_bs.cash_and_cash_equivalents_at_carrying_value is not None
    ):
        metrics_data["Cash and Short-Term Investments"] = (
            latest_annual_bs.cash_and_cash_equivalents_at_carrying_value
        )
    else:
        metrics_data["Cash and Short-Term Investments"] = None

    # 7. Free Cash Flow (FCF) (Calculated)
    latest_annual_cf = cash_flow.annual_reports[0] if cash_flow.annual_reports else None
    if (
        latest_annual_cf
        and latest_annual_cf.operating_cashflow is not None
        and latest_annual_cf.capital_expenditures is not None
    ):
        metrics_data["Free Cash Flow (Latest Annual)"] = (
            latest_annual_cf.operating_cashflow + latest_annual_cf.capital_expenditures
        )  # CapEx is usually reported as a negative outflow, so add it
    else:
        metrics_data["Free Cash Flow (Latest Annual)"] = None

    # 8. Return on Equity (ROE) (Extracted)
    metrics_data["Return on Equity (TTM)"] = overview.return_on_equity_ttm

    # Optional: Add Dividend Yield
    metrics_data["Dividend Yield (%)"] = overview.dividend_yield

    # Optional: Add Book Value per Share (Extracted)
    metrics_data["Book Value per Share"] = overview.book_value

    metrics_data["Book Value per Share"] = overview.description

    return metrics_data


def generate_output(llm, metrics: dict) -> SignalEvent:
    message = f"Based on the following data, create the investment signal. Analysis Data: {metrics}"

    chat = [
        ChatMessage.from_str(PROMPT, MessageRole.SYSTEM),
        ChatMessage.from_str(message, MessageRole.USER),
    ]

    response: SignalEvent = llm.chat(chat).raw
    response.agent = NAME
    return response


def calculate_eps_growth_rate(
    annual_earnings: list[AnnualEarning], years: int
) -> Optional[float]:
    """
    Calculates the Compound Annual Growth Rate (CAGR) for EPS over a specified number of years.
    Assumes annual_earnings list is ordered with the most recent year first.
    Returns growth rate as a percentage.
    Handles cases with insufficient data, zero or negative starting EPS.
    """
    if not annual_earnings or len(annual_earnings) < years + 1:
        return None  # Not enough data for the requested number of years

    starting_eps_report = annual_earnings[years]  # EPS 'years' years ago
    ending_eps_report = annual_earnings[0]  # Most recent EPS

    starting_eps = starting_eps_report.reported_eps
    ending_eps = ending_eps_report.reported_eps

    if starting_eps is None or ending_eps is None:
        return None  # Missing EPS data

    if starting_eps <= 0:
        # Cannot calculate meaningful CAGR with zero or negative starting EPS
        # You might return None or indicate this condition differently
        return None

    try:
        # CAGR formula: ((Ending Value / Starting Value)^(1 / Number of Years)) - 1
        cagr = ((ending_eps / starting_eps) ** (1 / years)) - 1
        return cagr * 100  # Return as percentage
    except Exception:
        return None  # Handle potential math errors (e.g., negative base with fractional exponent)


PROMPT = """
Act as an investment analyst specializing in the Peter Lynch stock-picking methodology. Your task is to analyze a stock using the provided financial data and qualitative information, and then present a concise analysis including a verdict, confidence score, and a detailed reasoning.

You will be given:
1.  A dictionary containing quantitative financial metrics calculated or extracted based on a stock's data (like P/E, PEG, growth rates, balance sheet items, etc.), generated by a specific Python function.
2.  Optional qualitative information about the company (e.g., business description, industry context, competitive landscape).

Your analysis MUST be structured around the following core Peter Lynch investment principles. Your "Reasoning" section MUST explicitly discuss each of these points, relating them to the provided data (quantitative and qualitative). If specific data for a criterion is missing from the input, state that the data is unavailable and explain how this lack of information impacts your assessment of that specific criterion and your overall confidence:

* **Understanding the Business:** Can the business be easily understood? What is its industry and competitive position? (Address using Qualitative Information if provided, otherwise state N/A or lack of data).
* **Earnings Growth:** Analyze the historical earnings growth rate over multiple years (provided as 'EPS Growth Rate (Nyr CAGR %)' in the metrics). Is it consistent and strong?
* **PEG Ratio:** Assess the stock's valuation relative to its growth using the PEG ratio (provided as 'PEG Ratio'). Is it <= 1, indicating potential value? Discuss the relationship between the P/E and the growth rate.
* **Financial Health:** Evaluate the balance sheet, particularly the level of debt (provided as 'Debt-to-Equity Ratio') and liquidity (provided as 'Current Ratio'). Is the company financially sound based on these metrics?
* **Free Cash Flow:** Examine the company's free cash flow generation (provided as 'Free Cash Flow (Latest Annual)'). Is it healthy and sufficient?
* **Dividends:** Note the dividend yield (provided as 'Dividend Yield (%)'). Is it a dividend-paying company? (Comment on its relevance based on the company's characteristics, if known from qualitative data, or generally).
* **Valuation:** Consider the P/E ratio (provided as 'P/E Ratio') and its context, primarily through the lens of the PEG ratio. Is the stock reasonably priced based on these figures?
* **Inventory:** If applicable to the industry (e.g., retail, manufacturing - potentially inferred from Qualitative Information), comment on inventory levels based on available data (only the latest value might be available as part of Balance Sheet details if not explicitly in the metrics dictionary; if not available or applicable, state so).
* **Book Value / Net Cash:** Review the Book Value per Share (provided as 'Book Value per Share') and the Net Cash position (provided as 'Cash and Short-Term Investments'). What do these figures suggest about the company's underlying value and financial cushion?
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
            result = await peter_lynch_agent(ctx)
            return StopEvent(result=result)

    async def run():
        wf = MockWorkflow()
        result = await wf.run(ticker="META")
        return result

    result = asyncio.run(run())
    print(result.model_dump_json(indent=2))
