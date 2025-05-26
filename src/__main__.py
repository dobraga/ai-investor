import asyncio
from logging import getLogger
from typing import Callable

import markdown2
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, step
from llama_index.core.workflow import Workflow as BaseWorkflow
from llama_index.llms.google_genai import GoogleGenAI

from src.agents import (
    SignalEvent,
    cathie_wood_agent,
    fundamentalist_agent,
    peter_lynch_agent,
    ray_dalio_agent,
    risk_manager_agent,
    warren_buffett_agent,
)
from src.config import Config
from src.tools import AlphaVantageClient

ALL_AGENTS = [
    warren_buffett_agent,
    ray_dalio_agent,
    peter_lynch_agent,
    cathie_wood_agent,
    fundamentalist_agent,
]


class StartAgentEvent(Event):
    agent_fn: Callable


class ResultEvent(Event):
    result: str


class Workflow(BaseWorkflow):
    @step
    async def start(self, ctx: Context, ev: StartEvent) -> StartAgentEvent:
        config: Config = ev.config

        llm = GoogleGenAI(model=config.llm.model)
        llm_struct = llm.as_structured_llm(SignalEvent)
        alpha_client = AlphaVantageClient(config.alpha)

        await ctx.set("llm", llm)
        await ctx.set("llm_struct", llm_struct)
        await ctx.set("alpha_client", alpha_client)
        await ctx.set("ticker", ev.ticker)

        await ctx.set("num_agents", len(ALL_AGENTS))

        for fn in ALL_AGENTS:
            ctx.send_event(StartAgentEvent(agent_fn=fn, ticker=ev.ticker))

    @step(num_workers=len(ALL_AGENTS))
    async def run_agent(self, ctx: Context, ev: StartAgentEvent) -> SignalEvent:
        result = await ev.agent_fn(ctx)
        return result

    @step
    async def combine_results(self, ctx: Context, ev: SignalEvent) -> StopEvent | None:
        num_to_collect = await ctx.get("num_agents")
        results = ctx.collect_events(ev, [SignalEvent] * num_to_collect)
        if results is None:
            return None

        ticker = await ctx.get("ticker")
        risk_manager_agent_result = await risk_manager_agent(ctx, results)
        results = [risk_manager_agent_result] + results

        html_content = generate_html_output(results)
        with open(f"docs/signal_events_{ticker}.html", "w") as f:
            f.write(html_content)

        combined_result = {event.agent: event.final_verdict for event in results}
        return StopEvent(result=combined_result)


def generate_html_output(signal_events: list[SignalEvent]) -> str:
    """Generates an HTML table string from a list of SignalEvent objects."""
    html_string = """
<html>
<head>
    <title>Signal Analysis Report</title>
    <style>
        table {
            font-family: arial, sans-serif;
            border-collapse: collapse;
            width: 100%;
        }
        td, th {
            border: 1px solid #dddddd;
            text-align: left;
            padding: 8px;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <h2>Signal Analysis Report</h2>
    <table>
        <tr>
            <th>Agent</th>
            <th>Final Verdict</th>
            <th>Confidence</th>
            <th>Explanation</th>
        </tr>
"""
    for event in signal_events:
        html_string += f"""
        <tr>
            <td>{event.agent}</td>
            <td>{event.final_verdict}</td>
            <td>{event.confidence}</td>
            <td>{markdown2.markdown(event.explanation)}</td>
        </tr>
"""
    html_string += """
    </table>
</body>
</html>
"""
    return html_string


if __name__ == "__main__":
    from dataclasses import dataclass, field

    import tyro

    getLogger("httpx").setLevel("WARNING")
    getLogger("google_genai").setLevel("WARNING")

    @dataclass
    class Args:
        tickers: list[str] = field(default_factory=lambda: ["IBM"])  # tickers
        config: Config = field(default_factory=Config)  # config

    args = tyro.cli(Args)
    args.config.log.basic_config()

    async def run():
        wf = Workflow(timeout=10 * 60)
        for ticker in args.tickers:
            result = await wf.run(ticker=ticker, config=args.config)
            print(ticker)
            print(result)

    result = asyncio.run(run())
