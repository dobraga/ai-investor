from logging import getLogger
from pathlib import Path
from typing import Any, Dict, List, Optional

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.workflow import Context

from src.agents._signal import SignalEvent
from src.tools import AlphaVantageClient, TickerData
from src.utils.format import id_to_name

ID = Path(__file__).stem
NAME = id_to_name(ID)
LOG = getLogger(__name__)


async def fundamentalist_agent(context: Context):
    ticker: str = await context.get("ticker")

    LOG.info(f"Running {NAME} agent {ticker}")
    llm = await context.get("llm_struct")
    client: AlphaVantageClient = await context.get("alpha_client")

    data = await client.aget_ticker_data(ticker)

    metrics = compute_metrics(data)
    analysis = generate_output(llm, metrics)

    LOG.info(f"Finished {NAME} agent {ticker}")

    return analysis


def compute_metrics(ticker_data: TickerData) -> Dict[str, Any]:
    """
    Calculates or extracts fundamental analysis metrics from TickerData.
    The most recent data is assumed to be the first element in lists.
    Only uses information available within the TickerData object.

    Args:
        ticker_data: An object containing financial data for a ticker.

    Returns:
        A dictionary where keys are metric names (str) and values are
        the calculated or extracted metric values. Returns None for metrics
        that cannot be calculated due to missing data or division by zero.
    """
    metrics: Dict[str, Any] = {}

    # --- Helper functions ---
    def safe_get_attr(obj: Optional[Any], attr_name: str, default: Any = None) -> Any:
        if obj is None:
            return default
        return getattr(obj, attr_name, default)

    def safe_get_from_list(
        data_list: Optional[List[Any]], index: int = 0
    ) -> Optional[Any]:
        if data_list and isinstance(data_list, list) and len(data_list) > index:
            return data_list[index]
        return None

    def safe_division(
        numerator: Optional[float], denominator: Optional[float], default: Any = None
    ) -> Optional[float]:
        if (
            numerator is None
            or denominator is None
            or not isinstance(denominator, (int, float))
            or denominator == 0
        ):
            return default
        if not isinstance(numerator, (int, float)):  # Ensure numerator is also a number
            return default
        return numerator / denominator

    # --- Overview ---
    overview_data = safe_get_attr(ticker_data, "overview")
    metrics["asset_type"] = safe_get_attr(overview_data, "asset_type")
    metrics["company_description"] = safe_get_attr(overview_data, "description")

    # --- Balance Sheet Data ---
    balance_sheet_data = safe_get_attr(ticker_data, "balance_sheet")
    # Annual
    annual_bs = safe_get_from_list(safe_get_attr(balance_sheet_data, "annual_reports"))
    # Quarterly
    quarterly_bs = safe_get_from_list(
        safe_get_attr(balance_sheet_data, "quarterly_reports")
    )

    # Most recent annual balance sheet values
    bs_ann_total_current_assets = safe_get_attr(annual_bs, "total_current_assets")
    bs_ann_total_current_liabilities = safe_get_attr(
        annual_bs, "total_current_liabilities"
    )
    bs_ann_cash_equivalents = safe_get_attr(
        annual_bs, "cash_and_cash_equivalents_at_carrying_value"
    )
    bs_ann_short_term_investments = safe_get_attr(annual_bs, "short_term_investments")
    bs_ann_net_receivables = safe_get_attr(annual_bs, "current_net_receivables")
    bs_ann_inventory = safe_get_attr(annual_bs, "inventory")
    bs_ann_total_liabilities = safe_get_attr(annual_bs, "total_liabilities")
    bs_ann_total_shareholder_equity = safe_get_attr(
        annual_bs, "total_shareholder_equity"
    )
    bs_ann_common_shares_outstanding = safe_get_attr(
        annual_bs, "common_stock_shares_outstanding"
    )
    bs_ann_total_assets = safe_get_attr(annual_bs, "total_assets")

    # Most recent quarterly balance sheet values
    bs_qtr_total_current_assets = safe_get_attr(quarterly_bs, "total_current_assets")
    bs_qtr_total_current_liabilities = safe_get_attr(
        quarterly_bs, "total_current_liabilities"
    )
    bs_qtr_cash_equivalents = safe_get_attr(
        quarterly_bs, "cash_and_cash_equivalents_at_carrying_value"
    )
    bs_qtr_short_term_investments = safe_get_attr(
        quarterly_bs, "short_term_investments"
    )
    bs_qtr_net_receivables = safe_get_attr(quarterly_bs, "current_net_receivables")
    bs_qtr_inventory = safe_get_attr(quarterly_bs, "inventory")
    bs_qtr_total_liabilities = safe_get_attr(quarterly_bs, "total_liabilities")
    bs_qtr_total_shareholder_equity = safe_get_attr(
        quarterly_bs, "total_shareholder_equity"
    )
    bs_qtr_common_shares_outstanding = safe_get_attr(
        quarterly_bs, "common_stock_shares_outstanding"
    )
    bs_qtr_total_assets = safe_get_attr(quarterly_bs, "total_assets")

    metrics["total_assets_annual"] = bs_ann_total_assets
    metrics["total_liabilities_annual"] = bs_ann_total_liabilities
    metrics["total_shareholder_equity_annual"] = bs_ann_total_shareholder_equity
    metrics["common_stock_shares_outstanding_annual"] = bs_ann_common_shares_outstanding

    metrics["total_assets_quarterly"] = bs_qtr_total_assets
    metrics["total_liabilities_quarterly"] = bs_qtr_total_liabilities
    metrics["total_shareholder_equity_quarterly"] = bs_qtr_total_shareholder_equity
    metrics["common_stock_shares_outstanding_quarterly"] = (
        bs_qtr_common_shares_outstanding
    )

    # Ratios from Balance Sheet
    metrics["book_value_per_share_annual"] = safe_division(
        bs_ann_total_shareholder_equity, bs_ann_common_shares_outstanding
    )
    metrics["current_ratio_annual"] = safe_division(
        bs_ann_total_current_assets, bs_ann_total_current_liabilities
    )

    quick_assets_annual = None
    if all(
        v is not None
        for v in [
            bs_ann_cash_equivalents,
            bs_ann_short_term_investments,
            bs_ann_net_receivables,
        ]
    ):
        quick_assets_annual = (
            bs_ann_cash_equivalents
            + bs_ann_short_term_investments
            + bs_ann_net_receivables
        )
    elif bs_ann_short_term_investments is None and all(
        v is not None for v in [bs_ann_cash_equivalents, bs_ann_net_receivables]
    ):
        quick_assets_annual = bs_ann_cash_equivalents + bs_ann_net_receivables
    elif bs_ann_total_current_assets is not None and bs_ann_inventory is not None:
        quick_assets_annual = bs_ann_total_current_assets - bs_ann_inventory
    metrics["quick_ratio_annual"] = safe_division(
        quick_assets_annual, bs_ann_total_current_liabilities
    )

    metrics["debt_to_equity_annual"] = safe_division(
        bs_ann_total_liabilities, bs_ann_total_shareholder_equity
    )

    metrics["book_value_per_share_quarterly"] = safe_division(
        bs_qtr_total_shareholder_equity, bs_qtr_common_shares_outstanding
    )
    metrics["current_ratio_quarterly"] = safe_division(
        bs_qtr_total_current_assets, bs_qtr_total_current_liabilities
    )

    quick_assets_quarterly = None
    if all(
        v is not None
        for v in [
            bs_qtr_cash_equivalents,
            bs_qtr_short_term_investments,
            bs_qtr_net_receivables,
        ]
    ):
        quick_assets_quarterly = (
            bs_qtr_cash_equivalents
            + bs_qtr_short_term_investments
            + bs_qtr_net_receivables
        )
    elif bs_qtr_short_term_investments is None and all(
        v is not None for v in [bs_qtr_cash_equivalents, bs_qtr_net_receivables]
    ):
        quick_assets_quarterly = bs_qtr_cash_equivalents + bs_qtr_net_receivables
    elif bs_qtr_total_current_assets is not None and bs_qtr_inventory is not None:
        quick_assets_quarterly = bs_qtr_total_current_assets - bs_qtr_inventory
    metrics["quick_ratio_quarterly"] = safe_division(
        quick_assets_quarterly, bs_qtr_total_current_liabilities
    )

    metrics["debt_to_equity_quarterly"] = safe_division(
        bs_qtr_total_liabilities, bs_qtr_total_shareholder_equity
    )

    # --- Cash Flow Data ---
    cash_flow_data = safe_get_attr(ticker_data, "cash_flow")
    # Annual
    annual_cf = safe_get_from_list(safe_get_attr(cash_flow_data, "annual_reports"))
    # Quarterly
    quarterly_cf = safe_get_from_list(
        safe_get_attr(cash_flow_data, "quarterly_reports")
    )

    cf_ann_operating_cashflow = safe_get_attr(annual_cf, "operating_cashflow")
    cf_ann_capital_expenditures = safe_get_attr(annual_cf, "capital_expenditures")
    cf_ann_net_income = safe_get_attr(annual_cf, "net_income")
    cf_ann_dividend_payout_common = safe_get_attr(
        annual_cf, "dividend_payout_common_stock"
    )

    cf_qtr_operating_cashflow = safe_get_attr(quarterly_cf, "operating_cashflow")
    cf_qtr_capital_expenditures = safe_get_attr(quarterly_cf, "capital_expenditures")
    cf_qtr_net_income = safe_get_attr(quarterly_cf, "net_income")

    metrics["operating_cash_flow_annual"] = cf_ann_operating_cashflow
    metrics["net_income_annual_from_cf"] = cf_ann_net_income

    free_cash_flow_annual = None
    if (
        cf_ann_operating_cashflow is not None
        and cf_ann_capital_expenditures is not None
    ):
        free_cash_flow_annual = cf_ann_operating_cashflow - cf_ann_capital_expenditures
    metrics["free_cash_flow_annual"] = free_cash_flow_annual

    metrics["operating_cash_flow_quarterly"] = cf_qtr_operating_cashflow
    metrics["net_income_quarterly_from_cf"] = cf_qtr_net_income

    free_cash_flow_quarterly = None
    if (
        cf_qtr_operating_cashflow is not None
        and cf_qtr_capital_expenditures is not None
    ):
        free_cash_flow_quarterly = (
            cf_qtr_operating_cashflow - cf_qtr_capital_expenditures
        )
    metrics["free_cash_flow_quarterly"] = free_cash_flow_quarterly

    metrics["cash_flow_per_share_annual"] = safe_division(
        cf_ann_operating_cashflow, bs_ann_common_shares_outstanding
    )
    metrics["cash_flow_per_share_quarterly"] = safe_division(
        cf_qtr_operating_cashflow, bs_qtr_common_shares_outstanding
    )

    # --- Earnings Data ---
    earnings_data = safe_get_attr(ticker_data, "earnings")
    # Annual
    annual_earn = safe_get_from_list(safe_get_attr(earnings_data, "annual_earnings"))
    # Quarterly
    quarterly_earn = safe_get_from_list(
        safe_get_attr(earnings_data, "quarterly_earnings")
    )

    metrics["eps_annual"] = safe_get_attr(annual_earn, "reported_eps")
    metrics["eps_quarterly"] = safe_get_attr(quarterly_earn, "reported_eps")
    metrics["earnings_surprise_percentage_quarterly"] = safe_get_attr(
        quarterly_earn, "surprise_percentage"
    )

    # --- Profitability Ratios (using annual data) ---
    metrics["return_on_equity_annual"] = safe_division(
        cf_ann_net_income, bs_ann_total_shareholder_equity
    )
    metrics["return_on_assets_annual"] = safe_division(
        cf_ann_net_income, bs_ann_total_assets
    )

    # --- Dividend Metrics (using annual data) ---
    metrics["dividend_per_share_annual"] = safe_division(
        cf_ann_dividend_payout_common, bs_ann_common_shares_outstanding
    )
    metrics["dividend_payout_ratio_annual"] = safe_division(
        cf_ann_dividend_payout_common, cf_ann_net_income
    )

    # --- Insider Transactions ---
    total_acquired_shares = 0.0
    total_disposed_shares = 0.0
    insider_tx_data = safe_get_attr(ticker_data, "insider_transactions")
    insider_tx_list = safe_get_attr(insider_tx_data, "data")

    if insider_tx_list and isinstance(insider_tx_list, list):
        for transaction in insider_tx_list:
            shares = safe_get_attr(transaction, "shares")
            acq_disp = safe_get_attr(transaction, "acquisition_or_disposal")
            if shares is not None and isinstance(shares, (int, float)):
                if acq_disp == "A":
                    total_acquired_shares += shares
                elif acq_disp == "D":
                    total_disposed_shares += shares

        latest_transaction = safe_get_from_list(insider_tx_list)
        if latest_transaction:
            metrics["latest_insider_transaction_date"] = safe_get_attr(
                latest_transaction, "transaction_date"
            )
            metrics["latest_insider_transaction_type"] = safe_get_attr(
                latest_transaction, "acquisition_or_disposal"
            )
            metrics["latest_insider_transaction_shares"] = safe_get_attr(
                latest_transaction, "shares"
            )
            metrics["latest_insider_transaction_price"] = safe_get_attr(
                latest_transaction, "share_price"
            )
            metrics["latest_insider_executive_title"] = safe_get_attr(
                latest_transaction, "executive_title"
            )

        metrics["total_insider_shares_acquired_all_time"] = total_acquired_shares
        metrics["total_insider_shares_disposed_all_time"] = total_disposed_shares
        metrics["net_insider_shares_traded_all_time"] = (
            total_acquired_shares - total_disposed_shares
        )
    else:  # No insider transaction data available
        metrics["latest_insider_transaction_date"] = None
        metrics["latest_insider_transaction_type"] = None
        metrics["latest_insider_transaction_shares"] = None
        metrics["latest_insider_transaction_price"] = None
        metrics["latest_insider_executive_title"] = None
        metrics["total_insider_shares_acquired_all_time"] = None
        metrics["total_insider_shares_disposed_all_time"] = None
        metrics["net_insider_shares_traded_all_time"] = None

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
You are a highly experienced and rigorous fundamental analyst specializing in equity markets. Your primary function is to evaluate the financial health, operational efficiency, and intrinsic value potential of a company based *solely* on provided fundamental financial metrics.

**Your Task:**
You will be provided with a set of fundamental financial metrics and their corresponding values for a specific asset. Your task is to perform a comprehensive fundamental analysis using *only* the data provided.

**Analysis Requirements:**
1.  **Metric-by-Metric Breakdown:** You MUST analyze and comment on *every single metric* listed below. For each metric, provide a concise explanation of its general significance in fundamental analysis and specifically how the *provided value* for this metric (which you will receive in the next input) impacts your overall assessment of the asset.
2.  **Apply Guiding Rules:** Based on the collective analysis of all metrics, you will apply the following guiding rules to arrive at your final verdict:
    * **Rule A (Favorable):** If the majority of key fundamental metrics show strong financial health (solid balance sheet, good liquidity), consistent profitability, efficient management (high ROE/ROA), healthy and sustainable cash flow generation, and positive or neutral insider sentiment, the asset is likely a "Strong Candidate" or "Possible Candidate".
    * **Rule B (Cautionary/Mixed):** If metrics present a mixed picture, show some areas of concern (e.g., increasing debt, declining margins, inconsistent cash flow) despite some strengths, or suggest the company is undergoing significant changes, the asset might be a "Possible Candidate" (requiring further diligence, which you cannot do with only the provided data) or "Not a Typical Investment" for a value-focused fundamental approach.
    * **Rule C (Unfavorable/Avoid):** If a significant number of core fundamental metrics indicate financial distress (e.g., high leverage, poor liquidity ratios, negative or declining profitability/cash flow, substantial net insider selling), the asset is likely "Not a Typical Investment" or warrants an "Avoid" recommendation.
    * **Rule D (Severe Distress):** If metrics reveal critical fundamental weaknesses such as negative shareholder equity, sustained significant losses, inability to generate operating cash flow, or dangerously high debt levels, the asset should definitively be an "Avoid".

**Metrics to Analyze (You must comment on each of these using the value provided in the next input):**

* **asset_type:** Type of the asset (e.g., Common Stock, ETF). *Explain its relevance.*
* **company_description:** Brief business summary or description of the company. *How does the business type influence the metric interpretation?*
* **total_assets_annual:** Total assets reported in the most recent annual balance sheet. *Significance of the scale.*
* **total_liabilities_annual:** Total liabilities reported in the most recent annual balance sheet. *Significance of total obligations.*
* **total_shareholder_equity_annual:** Total shareholders' equity reported in the most recent annual balance sheet. *Significance of net worth.*
* **common_stock_shares_outstanding_annual:** Number of outstanding shares of common stock from the most recent annual balance sheet. *Used in per-share calculations.*
* **total_assets_quarterly:** Total assets reported in the most recent quarterly balance sheet. *Compare to annual for trend.*
* **total_liabilities_quarterly:** Total liabilities reported in the most recent quarterly balance sheet. *Compare to annual for trend.*
* **total_shareholder_equity_quarterly:** Total shareholders' equity reported in the most recent quarterly balance sheet. *Compare to annual for trend.*
* **common_stock_shares_outstanding_quarterly:** Number of outstanding shares of common stock from the most recent quarterly balance sheet. *Compare to annual for trend.*
* **book_value_per_share_annual:** Shareholders' equity per outstanding common share (Annual). *Significance of net asset value per share.*
* **current_ratio_annual:** Measures a company's ability to pay short-term obligations (Annual). *Significance for liquidity.*
* **quick_ratio_annual:** Measures a company's ability to meet its short-term obligations with most liquid assets (Annual). *Significance for stringent liquidity.*
* **debt_to_equity_annual:** Indicates the relative proportion of shareholders' equity and debt (Annual). *Significance for leverage.*
* **book_value_per_share_quarterly:** Shareholders' equity per outstanding common share (Quarterly). *Compare to annual for trend.*
* **current_ratio_quarterly:** Measures a company's ability to pay short-term obligations (Quarterly). *Compare to annual for trend.*
* **quick_ratio_quarterly:** Measures a company's ability to meet its short-term obligations with most liquid assets (Quarterly). *Compare to annual for trend.*
* **debt_to_equity_quarterly:** Indicates the relative proportion of shareholders' equity and debt (Quarterly). *Compare to annual for trend.*
* **operating_cash_flow_annual:** Cash generated from core business operations (Annual). *Significance for financial health.*
* **net_income_annual_from_cf:** Total earnings (Annual, from CF). *Key for profitability ratios.*
* **free_cash_flow_annual:** Cash flow available after operational/capital expenditures (Annual). *Significance for financial flexibility.*
* **operating_cash_flow_quarterly:** Cash generated from core business operations (Quarterly). *Compare to annual for trend.*
* **net_income_quarterly_from_cf:** Total earnings (Quarterly, from CF). *Compare to annual for trend.*
* **free_cash_flow_quarterly:** Cash flow available after operational/capital expenditures (Quarterly). *Compare to annual for trend.*
* **cash_flow_per_share_annual:** Operating cash flow per outstanding share (Annual). *Significance of cash generation per share.*
* **cash_flow_per_share_quarterly:** Operating cash flow per outstanding share (Quarterly). *Compare to annual for trend.*
* **eps_annual:** Reported earnings per share (Annual). *Key profitability indicator.*
* **eps_quarterly:** Reported earnings per share (Quarterly). *Compare to annual for trend.*
* **earnings_surprise_percentage_quarterly:** Difference between reported and estimated EPS (Quarterly). *Significance for market expectations.*
* **return_on_equity_annual (ROE):** Profitability relative to stockholders’ equity (Annual). *Significance for using shareholder capital.*
* **return_on_assets_annual (ROA):** Profitability relative to total assets (Annual). *Significance for using assets.*
* **dividend_per_share_annual:** Total dividends paid per share (Annual). *Significance for income investors.*
* **dividend_payout_ratio_annual:** Proportion of earnings paid as dividends (Annual). *Significance for dividend sustainability.*
* **total_insider_shares_acquired_all_time:** Total shares acquired by insiders (All Time). *Significance for insider sentiment.*
* **total_insider_shares_disposed_all_time:** Total shares disposed by insiders (All Time). *Significance for insider sentiment.*
* **net_insider_shares_traded_all_time:** Net shares traded by insiders (Acquired - Disposed) (All Time). *Overall insider sentiment.*
* **latest_insider_transaction_date:** Date of most recent insider transaction. *Timeliness of sentiment data.*
* **latest_insider_transaction_type:** Type of most recent insider transaction (Acquisition/Disposal). *Nature of the latest sentiment.*
* **latest_insider_transaction_shares:** Number of shares in most recent insider transaction. *Scale of the latest sentiment.*
* **latest_insider_transaction_price:** Share price of most recent insider transaction. *Context for the latest sentiment.*
* **latest_insider_executive_title:** Title of insider in most recent transaction. *Level/influence of the insider.*

**Final Output Format:**
Your response MUST adhere strictly to the following structure:

1.  A detailed section for each metric listed above, providing:
    * Metric Name
    * Provided Value (You will insert the actual value from the user's next input here)
    * Significance & Impact: Explain the metric's general meaning and how its specific provided value influences your fundamental assessment of the asset.
2.  A summary section explaining which Guiding Rules (A, B, C, or D) were most applicable and how they led to the final verdict.
3.  Final Verdict: State your verdict, choosing *only one* from the following list: ["Strong Candidate", "Possible Candidate", "Not a Typical Investment", "Avoid"].
4.  Confidence Score: Provide a numerical score from 0 to 100 indicating your confidence in the Final Verdict, based *only* on the provided fundamental data.

You are now ready to receive the fundamental metrics data in the next input.
"""


if __name__ == "__main__":
    import asyncio
    from logging import basicConfig

    from llama_index.core.workflow import StartEvent, StopEvent, Workflow, step
    from llama_index.llms.google_genai import GoogleGenAI

    from src.config import Config

    cfg = Config()

    basicConfig(level="INFO")

    llm = GoogleGenAI(model="gemini-2.0-flash")
    llm = llm.as_structured_llm(SignalEvent)

    class MockWorkflow(Workflow):
        @step
        async def agent(self, ctx: Context, ev: StartEvent) -> StopEvent:
            await ctx.set("llm_struct", llm)
            await ctx.set("alpha_client", AlphaVantageClient(cfg.alpha))
            await ctx.set("ticker", ev.ticker)
            result = await fundamentalist_agent(ctx)
            return StopEvent(result=result)

    async def run():
        wf = MockWorkflow()
        result = await wf.run(ticker="META")
        return result

    result = asyncio.run(run())
    print(result.model_dump_json(indent=2))
