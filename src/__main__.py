import asyncio
from logging import basicConfig, getLogger
from typing import Callable

from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, step
from llama_index.core.workflow import Workflow as BaseWorkflow
from llama_index.llms.google_genai import GoogleGenAI

from src.agents import (
    SignalEvent,
    cathie_wood_agent,
    peter_lynch_agent,
    ray_dalio_agent,
    warren_buffett_agent,
)
from src.config import Config
from src.tools import AlphaVantageClient


class StartAgentEvent(Event):
    agent_fn: Callable


class ResultEvent(Event):
    result: str


class Workflow(BaseWorkflow):
    @step
    async def start(self, ctx: Context, ev: StartEvent) -> StartAgentEvent:
        config: Config = ev.config

        llm = GoogleGenAI(model="gemini-2.0-flash")
        llm_struct = llm.as_structured_llm(SignalEvent)
        alpha_client = AlphaVantageClient(config.alpha)

        await ctx.set("llm", llm)
        await ctx.set("llm_struct", llm_struct)
        await ctx.set("alpha_client", alpha_client)
        await ctx.set("ticker", ev.ticker)

        agents_to_run = [
            warren_buffett_agent,
            ray_dalio_agent,
            peter_lynch_agent,
            cathie_wood_agent,
        ]
        await ctx.set("num_agents", len(agents_to_run))

        for fn in agents_to_run:
            ctx.send_event(StartAgentEvent(agent_fn=fn, ticker=ev.ticker))

    @step(num_workers=4)
    async def run_agent(self, ctx: Context, ev: StartAgentEvent) -> SignalEvent:
        result = await ev.agent_fn(ctx)
        return result

    @step
    async def combine_results(self, ctx: Context, ev: SignalEvent) -> StopEvent | None:
        num_to_collect = await ctx.get("num_agents")
        results = ctx.collect_events(ev, [SignalEvent] * num_to_collect)
        if results is None:
            return None

        combined_result = ", ".join([event.final_verdict for event in results])
        return StopEvent(result=combined_result)


if __name__ == "__main__":
    from dataclasses import dataclass, field

    import tyro

    basicConfig(
        level="INFO", format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )
    getLogger("httpx").setLevel("WARNING")
    getLogger("google_genai").setLevel("WARNING")

    @dataclass
    class Args:
        ticker: str = "IBM"  # ticker
        config: Config = field(default_factory=Config)  # config

    args = tyro.cli(Args)

    async def run():
        wf = Workflow()
        result = await wf.run(ticker=args.ticker, config=args.config)
        return result

    result = asyncio.run(run())
    print(result)
