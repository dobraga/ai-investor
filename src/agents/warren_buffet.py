from typing import Literal

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.workflow import Context
from pydantic import BaseModel

from src.tools import AlphaVantageClient


class BuffetAnalysis(BaseModel):
    final_verdict: Literal["buy", "hold", "sell"]
    confidence: int
    explanation: str


async def warren_buffet_agent(context: Context):
    llm = await context.get("llm")
    llm = llm.as_structured_llm(BuffetAnalysis)
    tickers: list[str] = await context.get("tickers")
    client: AlphaVantageClient = await context.get("alpha_vantage_client")

    for ticker in tickers:
        data = client.get_ticker_data(ticker)

        last_cash_flow = data.cash_flow.annual_reports[-1]
        last_balance_sheet = data.balance_sheet.annual_reports[-1]

        net_income = last_cash_flow.net_income
        depr_amort = last_cash_flow.depreciation_depletion_and_amortization
        capex = last_cash_flow.capital_expenditures
        equity = last_balance_sheet.total_shareholder_equity
        liabilities = last_balance_sheet.total_liabilities
        shares = last_balance_sheet.common_stock_shares_outstanding

        roe = net_income / equity * 100
        owner_earnings = net_income + depr_amort - capex
        owner_earnings_per_share = owner_earnings / shares
        de_ratio = liabilities / equity

        data = {
            "roe": roe,
            "owner_earnings": owner_earnings,
            "owner_earnings_per_share": owner_earnings_per_share,
            "de_ratio": de_ratio,
        }

        return generate_buffet_output(llm, data)


def generate_buffet_output(llm, data: dict) -> BuffetAnalysis:
    message = f"Based on the following data, create the investment signal as Warren Buffett would. Analysis Data: {data}"

    chat = [
        ChatMessage.from_str(BUFFET_PROMPT, MessageRole.SYSTEM),
        ChatMessage.from_str(message, MessageRole.USER),
    ]

    return llm.chat(chat).raw


BUFFET_PROMPT = """
You are Warren Buffett conducting a shareholder-level analysis of a company. You will be given four key metrics:

- ROE (return on equity) in percentage  
- Owner earnings (Dollars)  
- Owner earnings per share (Dollars)  
- Debt-to-equity ratio (number)  

Your task:

1. Evaluate these metrics against Buffett’s criteria:
   - Sustainable competitive advantage (economic moat)
   - Consistent high return on equity
   - Growing, predictable owner earnings
   - Prudent use of debt
   - Management quality and integrity
   - Reasonable price relative to intrinsic value
2. Produce a JSON object exactly in this format:
   {
     "verdict": "<Buy, Hold, or Sell>",
     "confidence": <integer 0–100>,
     "reasoning": "<detailed reasoning covering every Buffett criterion>"
   }
3. In your reasoning, explicitly address each of Buffett’s criteria above.
"""


if __name__ == "__main__":
    import asyncio
    from logging import basicConfig

    from dotenv import load_dotenv
    from llama_index.core.workflow import StartEvent, StopEvent, Workflow, step
    from llama_index.llms.google_genai import GoogleGenAI

    load_dotenv()

    basicConfig(level="INFO")

    llm = GoogleGenAI(model="gemini-2.0-flash")

    class MockWarrenBuffetWorkflow(Workflow):
        @step
        async def warren_buffet(self, ctx: Context, ev: StartEvent) -> StopEvent:
            await ctx.set("llm", llm)
            await ctx.set("alpha_vantage_client", AlphaVantageClient("demo"))
            await ctx.set("tickers", [ev.ticker])
            result = await warren_buffet_agent(ctx)
            return StopEvent(result=result)

    async def run():
        wf = MockWarrenBuffetWorkflow()
        result = await wf.run(ticker="IBM")
        return result

    result = asyncio.run(run())
    print(result.model_dump_json(indent=2))
