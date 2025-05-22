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


async def cathie_wood_agent(context: Context):
    ticker: str = await context.get("ticker")

    LOG.info(f"Running {NAME} agent {ticker}")
    llm = await context.get("llm_struct")
    client: AlphaVantageClient = await context.get("alpha_client")

    data = await client.aget_ticker_data(ticker)

    metrics = compute_metrics(data)
    analysis = generate_output(llm, metrics)

    LOG.info(f"Finished {NAME} agent {ticker}")

    return analysis


def compute_metrics(data: TickerData) -> Dict[str, Any]:
    """
    Extracts and calculates key financial metrics relevant to Cathie Wood's
    investment philosophy from TickerData.

    Args:
        data: An object structured like the TickerData BaseModel, containing
              overview, balance_sheet, cash_flow, and earnings information.
              Lists within TickerData are assumed to have the most recent data first.

    Returns:
        A dictionary containing the extracted and calculated metrics. Returns
        None for metrics that cannot be calculated due to missing data.
    """
    metrics = {}

    # --- Growth Metrics (Focus on top-line and earnings growth) ---
    overview = data.overview
    metrics["QuarterlyRevenueGrowthYOY"] = overview.quarterly_revenue_growth_yoy
    metrics["QuarterlyEarningsGrowthYOY"] = overview.quarterly_earnings_growth_yoy
    metrics["DilutedEPSTTM"] = overview.diluted_eps_ttm
    metrics["RevenueTTM"] = (
        float(overview.revenue_ttm) if overview.revenue_ttm is not None else None
    )
    metrics["GrossProfitTTM"] = (
        float(overview.gross_profit_ttm)
        if overview.gross_profit_ttm is not None
        else None
    )

    # --- Profitability and Efficiency Metrics (Indicative of scaling potential) ---
    metrics["OperatingMarginTTM"] = overview.operating_margin_ttm
    metrics["ProfitMargin"] = overview.profit_margin  # TTM profit margin

    # Calculate Gross Margin TTM
    if metrics["RevenueTTM"] is not None and metrics["RevenueTTM"] != 0:
        metrics["GrossMarginTTM"] = (
            (metrics["GrossProfitTTM"] / metrics["RevenueTTM"]) * 100
            if metrics["GrossProfitTTM"] is not None
            else None
        )
    else:
        metrics["GrossMarginTTM"] = None

    metrics["ReturnOnEquityTTM"] = overview.return_on_equity_ttm
    metrics["ReturnOnAssetsTTM"] = overview.return_on_assets_ttm

    # --- Cash Flow Metrics (Crucial for funding innovation and growth) ---
    latest_quarterly_cashflow = (
        data.cash_flow.quarterly_reports[0]
        if data.cash_flow.quarterly_reports
        else None
    )

    if latest_quarterly_cashflow:
        metrics["OperatingCashFlow_LQ"] = latest_quarterly_cashflow.operating_cashflow
        metrics["CapitalExpenditures_LQ"] = (
            latest_quarterly_cashflow.capital_expenditures
        )
        # Calculate Free Cash Flow (Operating Cash Flow - Capital Expenditures) for Latest Quarter
        if (
            metrics["OperatingCashFlow_LQ"] is not None
            and metrics["CapitalExpenditures_LQ"] is not None
        ):
            metrics["FreeCashFlow_LQ"] = (
                metrics["OperatingCashFlow_LQ"] - metrics["CapitalExpenditures_LQ"]
            )
        else:
            metrics["FreeCashFlow_LQ"] = None
        metrics["NetIncome_LQ"] = (
            latest_quarterly_cashflow.net_income
        )  # Using Net Income from Cash Flow

    latest_annual_cashflow = (
        data.cash_flow.annual_reports[0] if data.cash_flow.annual_reports else None
    )
    if latest_annual_cashflow:
        metrics["OperatingCashFlow_LA"] = latest_annual_cashflow.operating_cashflow
        metrics["CapitalExpenditures_LA"] = latest_annual_cashflow.capital_expenditures
        # Calculate Free Cash Flow (Operating Cash Flow - Capital Expenditures) for Latest Annual
        if (
            metrics["OperatingCashFlow_LA"] is not None
            and metrics["CapitalExpenditures_LA"] is not None
        ):
            metrics["FreeCashFlow_LA"] = (
                metrics["OperatingCashFlow_LA"] - metrics["CapitalExpenditures_LA"]
            )
        else:
            metrics["FreeCashFlow_LA"] = None
        metrics["NetIncome_LA"] = (
            latest_annual_cashflow.net_income
        )  # Using Net Income from Cash Flow

    # --- Balance Sheet Strength (Assessing runway and financial health) ---
    latest_quarterly_balancesheet = (
        data.balance_sheet.quarterly_reports[0]
        if data.balance_sheet.quarterly_reports
        else None
    )

    if latest_quarterly_balancesheet:
        metrics["CashAndCashEquivalents_LQ"] = (
            latest_quarterly_balancesheet.cash_and_cash_equivalents_at_carrying_value
        )
        metrics["CashAndShortTermInvestments_LQ"] = (
            latest_quarterly_balancesheet.cash_and_short_term_investments
        )
        metrics["TotalCurrentAssets_LQ"] = (
            latest_quarterly_balancesheet.total_current_assets
        )
        metrics["TotalCurrentLiabilities_LQ"] = (
            latest_quarterly_balancesheet.total_current_liabilities
        )
        metrics["TotalShareholderEquity_LQ"] = (
            latest_quarterly_balancesheet.total_shareholder_equity
        )

        # Calculate Current Ratio
        if (
            metrics["TotalCurrentLiabilities_LQ"] is not None
            and metrics["TotalCurrentLiabilities_LQ"] != 0
        ):
            metrics["CurrentRatio_LQ"] = (
                metrics["TotalCurrentAssets_LQ"] / metrics["TotalCurrentLiabilities_LQ"]
                if metrics["TotalCurrentAssets_LQ"] is not None
                else None
            )
        else:
            metrics["CurrentRatio_LQ"] = None

        # Calculate Total Debt to Equity (Using Short-Term Debt + Long-Term Debt)
        total_debt_lq = None
        st_debt_lq = latest_quarterly_balancesheet.short_term_debt
        lt_debt_lq = latest_quarterly_balancesheet.long_term_debt
        if st_debt_lq is not None and lt_debt_lq is not None:
            total_debt_lq = st_debt_lq + lt_debt_lq
        elif (
            st_debt_lq is not None
        ):  # Account for cases where only short-term debt is reported
            total_debt_lq = st_debt_lq
        elif (
            lt_debt_lq is not None
        ):  # Account for cases where only long-term debt is reported
            total_debt_lq = lt_debt_lq

        if (
            total_debt_lq is not None
            and metrics["TotalShareholderEquity_LQ"] is not None
            and metrics["TotalShareholderEquity_LQ"] != 0
        ):
            metrics["TotalDebtToEquity_LQ"] = (
                total_debt_lq / metrics["TotalShareholderEquity_LQ"]
            )
        else:
            metrics["TotalDebtToEquity_LQ"] = None

    latest_annual_balancesheet = (
        data.balance_sheet.annual_reports[0]
        if data.balance_sheet.annual_reports
        else None
    )
    if latest_annual_balancesheet:
        metrics["CashAndCashEquivalents_LA"] = (
            latest_annual_balancesheet.cash_and_cash_equivalents_at_carrying_value
        )
        metrics["CashAndShortTermInvestments_LA"] = (
            latest_annual_balancesheet.cash_and_short_term_investments
        )
        metrics["TotalCurrentAssets_LA"] = (
            latest_annual_balancesheet.total_current_assets
        )
        metrics["TotalCurrentLiabilities_LA"] = (
            latest_annual_balancesheet.total_current_liabilities
        )
        metrics["TotalShareholderEquity_LA"] = (
            latest_annual_balancesheet.total_shareholder_equity
        )

        # Calculate Current Ratio
        if (
            metrics["TotalCurrentLiabilities_LA"] is not None
            and metrics["TotalCurrentLiabilities_LA"] != 0
        ):
            metrics["CurrentRatio_LA"] = (
                metrics["TotalCurrentAssets_LA"] / metrics["TotalCurrentLiabilities_LA"]
                if metrics["TotalCurrentAssets_LA"] is not None
                else None
            )
        else:
            metrics["CurrentRatio_LA"] = None

        # Calculate Total Debt to Equity (Using Short-Term Debt + Long-Term Debt)
        total_debt_la = None
        st_debt_la = latest_annual_balancesheet.short_term_debt
        lt_debt_la = latest_annual_balancesheet.long_term_debt
        if st_debt_la is not None and lt_debt_la is not None:
            total_debt_la = st_debt_la + lt_debt_la
        elif st_debt_la is not None:
            total_debt_la = st_debt_la
        elif lt_debt_la is not None:
            total_debt_la = lt_debt_la

        if (
            total_debt_la is not None
            and metrics["TotalShareholderEquity_LA"] is not None
            and metrics["TotalShareholderEquity_LA"] != 0
        ):
            metrics["TotalDebtToEquity_LA"] = (
                total_debt_la / metrics["TotalShareholderEquity_LA"]
            )
        else:
            metrics["TotalDebtToEquity_LA"] = None

    # --- Valuation Metrics (Relative to growth potential) ---
    metrics["PriceToSalesRatioTTM"] = overview.price_to_sales_ratio_ttm
    metrics["ForwardPE"] = overview.forward_pe
    metrics["PEGRatio"] = overview.peg_ratio
    metrics["EVToRevenue"] = overview.ev_to_revenue
    metrics["EVToEBITDA"] = overview.ev_to_ebitda
    metrics["MarketCapitalization"] = (
        float(overview.market_capitalization)
        if overview.market_capitalization is not None
        else None
    )

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
You are an investment analyst specializing in Cathie Wood's ARK Invest philosophy. Your focus is on identifying and evaluating companies at the forefront of disruptive innovation with significant long-term growth potential. You prioritize understanding the total addressable market, the pace of innovation, and the company's position within its disruptive theme.

Goal: Analyze a given stock based only on the provided financial data (TickerData), applying the principles and key metrics associated with Cathie Wood's investment approach. Provide a clear assessment, detailed reasoning, a final verdict, and a confidence score.

Evaluate the company's performance and financial health through the lens of disruptive innovation and long-term growth potential, using the metrics as quantitative indicators supporting a qualitative assessment of the company's position in its market and its ability to execute on its vision.

Apply the general rules associated with each metric category and the overarching investment philosophy to inform your analysis.

Construct a detailed analysis, providing specific reasoning for each point based solely on the data in the TickerData and the defined metrics/rules.

Formulate a final verdict (Attractive, Neutral, Unattractive) based on the comprehensive analysis.

Assign a confidence score (0-100) reflecting the certainty of your analysis based on the available data and the clarity of the company's alignment with the investment philosophy.

**Detailed Analysis:**

* **Growth Potential:**
    * Reasoning based on Quarterly Revenue Growth YOY, Quarterly Earnings Growth YOY, Diluted EPS TTM, Revenue TTM, and Gross Profit TTM.
    * *Rule Applied:* Look for strong positive growth and analyze trends. High growth is favorable, indicating the company is capturing market opportunity. Assess if earnings growth is beginning to follow revenue growth as the company scales.

* **Profitability and Efficiency:**
    * Reasoning based on Gross Margin TTM, Operating Margin TTM, Profit Margin, Return on Equity TTM, and Return on Assets TTM.
    * *Rule Applied:* Evaluate trends in margins. Improving margins as revenue grows are positive signs of scaling efficiency. Low or negative current profitability is acceptable if the long-term growth trajectory and market opportunity are significant.

* **Cash Flow and Financial Runway:**
    * Reasoning based on Operating Cash Flow (Latest Quarter & Annual), Capital Expenditures (Latest Quarter & Annual), Free Cash Flow (Latest Quarter & Annual), and Net Income (Latest Quarter & Annual).
    * *Rule Applied:* Assess the cash burn rate (negative Free Cash Flow). A significant burn rate necessitates a strong balance sheet. Look for positive or improving Operating Cash Flow as the business matures. Evaluate if CapEx is fueling future growth. Sufficient cash reserves are critical for companies with cash burn.

* **Balance Sheet Strength:**
    * Reasoning based on Cash and Cash Equivalents (Latest Quarter & Annual), Cash and Short-Term Investments (Latest Quarter & Annual), Total Current Assets (Latest Quarter & Annual), Total Current Liabilities (Latest Quarter & Annual), Current Ratio (Latest Quarter & Annual), Total Shareholder Equity (Latest Quarter & Annual), and Total Debt to Equity (Latest Quarter & Annual).
    * *Rule Applied:* Evaluate liquidity (Cash, Current Ratio) to ensure the company has sufficient runway to fund operations and growth, especially if burning cash. Assess leverage (Total Debt to Equity); manageable debt is acceptable, but excessive debt can pose a risk to long-term viability.

* **Valuation:**
    * Reasoning based on Price to Sales Ratio TTM, Forward PE, PEG Ratio, EV to Revenue, EV to EBITDA, and Market Capitalization.
    * *Rule Applied:* Consider valuation metrics in the context of the company's growth rate and the size of the disruptive opportunity. High valuations can be justified by exceptional growth potential, but assess if the current valuation appears excessive relative to the perceived long-term opportunity and risks.

**Final Verdict:**

**Confidence Score:** [0-100] (Based on the clarity and completeness of the provided data and the strength of the signals)

**Metrics Used and Decision Rules Summary:**

* **Quarterly Revenue Growth YOY:** Year-over-year revenue growth for the latest quarter. *Rule: Strong positive growth is favorable.*
* **Quarterly Earnings Growth YOY:** Year-over-year earnings growth for the latest quarter. *Rule: Positive or improving growth is a good sign.*
* **Diluted EPS TTM:** Earnings per share after dilution (TTM). *Rule: Positive or improving EPS is favorable, but not strictly required for early-stage growth.*
* **Revenue TTM:** Total revenue (TTM). *Rule: Provides context for scale and growth rate.*
* **Gross Profit TTM:** Gross profit (TTM). *Rule: Provides context for operational efficiency before overheads.*
* **Gross Margin TTM:** Gross Profit TTM / Revenue TTM. *Rule: Look for high or improving margins as an indicator of scaling potential.*
* **Operating Margin TTM:** Operating income / Revenue TTM. *Rule: Indicates efficiency after operating expenses; look for improvement.*
* **Profit Margin:** Net profit / Revenue TTM. *Rule: Overall profitability; less critical than growth for early-stage disruptors but improvement is positive.*
* **Return On Equity TTM:** Net income / Shareholder Equity TTM. *Rule: Measures efficiency in using shareholder capital; low or negative values are common in high-growth phases.*
* **Return On Assets TTM:** Net income / Total Assets TTM. *Rule: Measures efficiency in using assets; low or negative values are common in high-growth phases.*
* **Operating Cash Flow (Latest Quarter & Annual):** Cash from core operations. *Rule: Positive or improving OCF is favorable; indicates the core business is generating cash.*
* **Capital Expenditures (Latest Quarter & Annual):** Investment in assets. *Rule: Assess if CapEx supports growth initiatives.*
* **Free Cash Flow (Latest Quarter & Annual):** OCF - CapEx. *Rule: Indicates cash available after investments; negative FCF (cash burn) requires sufficient cash reserves.*
* **Net Income (Latest Quarter & Annual):** The bottom line. *Rule: Provides context on accounting profitability; cash flow is often more critical for growth companies.*
* **Cash And Cash Equivalents (Latest Quarter & Annual):** Immediate liquidity. *Rule: Sufficient cash provides runway, especially with cash burn.*
* **Cash And Short-Term Investments (Latest Quarter & Annual):** Total liquid assets. *Rule: Higher values indicate better short-term financial flexibility.*
* **Total Current Assets (Latest Quarter & Annual):** Assets convertible to cash within a year. *Rule: Used for Current Ratio calculation.*
* **Total Current Liabilities (Latest Quarter & Annual):** Obligations due within a year. *Rule: Used for Current Ratio calculation.*
* **Current Ratio (Latest Quarter & Annual):** Current Assets / Current Liabilities. *Rule: Indicates short-term solvency; a ratio > 1 is generally preferred.*
* **Total Shareholder Equity (Latest Quarter & Annual):** Book value of assets minus liabilities. *Rule: Represents shareholder stake; used for Debt to Equity.*
* **Total Debt To Equity (Latest Quarter & Annual):** Total Debt / Total Shareholder Equity. *Rule: Assesses leverage; lower is generally less risky, but some debt may be acceptable for funding growth.*
* **Price To Sales Ratio TTM:** Market Cap / Revenue TTM. *Rule: A key valuation metric for growth companies; assess relative to growth rate and market opportunity.*
* **Forward PE:** Price / Projected Future Earnings. *Rule: Forward-looking valuation; applicable if projected earnings are positive.*
* **PEG Ratio:** PE Ratio / Earnings Growth Rate. *Rule: Attempts to factor growth into valuation; applicable if PE and growth rate are meaningful.*
* **EV To Revenue:** Enterprise Value / Revenue TTM. *Rule: Valuation metric considering debt and cash; assess relative to growth and opportunity.*
* **EV To EBITDA:** Enterprise Value / EBITDA TTM. *Rule: Valuation relative to operational cash flow; assess relative to growth and opportunity.*
* **Market Capitalization:** Total value of outstanding shares. *Rule: Provides context for the company's size.*

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
