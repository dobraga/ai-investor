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

        html_content = generate_html_output(results, ticker)
        with open(f"docs/signal_events_{ticker}.html", "w") as f:
            f.write(html_content)

        combined_result = {event.agent: event.final_verdict for event in results}
        return StopEvent(result=combined_result)


def generate_html_output(signal_events: list[SignalEvent], ticker: str) -> str:
    """Generates a beautiful, modern HTML report from a list of SignalEvent objects."""

    # Calculate overall metrics
    total_agents = len(signal_events)
    strong_candidates = sum(
        1 for event in signal_events if event.final_verdict == "Strong Candidate"
    )
    possible_candidates = sum(
        1 for event in signal_events if event.final_verdict == "Possible Candidate"
    )
    not_typical = sum(
        1
        for event in signal_events
        if event.final_verdict == "Not a Typical Investment"
    )
    avoid_signals = sum(1 for event in signal_events if event.final_verdict == "Avoid")
    avg_confidence = (
        sum(event.confidence for event in signal_events) / total_agents
        if total_agents > 0
        else 0
    )

    # Determine overall sentiment
    if strong_candidates >= total_agents * 0.4:  # 40% or more strong candidates
        overall_sentiment = "HIGHLY RECOMMENDED"
        sentiment_color = "#10B981"
        sentiment_icon = "🌟"
    elif (
        strong_candidates + possible_candidates
    ) >= total_agents * 0.6:  # 60% or more positive
        overall_sentiment = "RECOMMENDED"
        sentiment_color = "#3B82F6"
        sentiment_icon = "👍"
    elif avoid_signals >= total_agents * 0.4:  # 40% or more avoid signals
        overall_sentiment = "NOT RECOMMENDED"
        sentiment_color = "#EF4444"
        sentiment_icon = "⚠️"
    else:
        overall_sentiment = "MIXED SIGNALS"
        sentiment_color = "#F59E0B"
        sentiment_icon = "🤔"

    html_string = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Analysis Report - {ticker}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .ticker-display {{
            background: rgba(255, 255, 255, 0.15);
            padding: 15px 25px;
            border-radius: 12px;
            margin: 20px 0;
            border: 2px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(5px);
        }}
        
        .ticker-symbol {{
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: 2px;
            color: #ffffff;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            margin-bottom: 5px;
        }}
        
        .ticker-label {{
            font-size: 0.9rem;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .market-info {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        
        .market-item {{
            text-align: center;
        }}
        
        .market-value {{
            font-size: 1.2rem;
            font-weight: 600;
            color: white;
        }}
        
        .market-label {{
            font-size: 0.8rem;
            opacity: 0.7;
            margin-top: 2px;
        }}
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="75" cy="75" r="1" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100%" height="100%" fill="url(%23grain)"/></svg>');
            opacity: 0.3;
        }}
        
        .header-content {{
            position: relative;
            z-index: 1;
        }}
        
        .title {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8fafc;
        }}
        
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid #e2e8f0;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #64748b;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }}
        
        .sentiment-card {{
            background: linear-gradient(135deg, {sentiment_color}20, {sentiment_color}10);
            border: 2px solid {sentiment_color};
        }}
        
        .sentiment-value {{
            color: {sentiment_color};
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }}
        
        .agents-section {{
            padding: 40px;
        }}
        
        .section-title {{
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 30px;
            color: #1e293b;
            text-align: center;
        }}
        
        .agents-grid {{
            display: grid;
            gap: 20px;
        }}
        
        .agent-card {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid #e2e8f0;
        }}
        
        .agent-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}
        
        .agent-header {{
            padding: 20px;
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .agent-name {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 10px;
        }}
        
        .agent-verdict {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .verdict-buy {{
            background: #10B98120;
            color: #047857;
            border: 1px solid #10B981;
        }}
        
        .verdict-sell {{
            background: #EF444420;
            color: #DC2626;
            border: 1px solid #EF4444;
        }}
        
        .verdict-hold {{
            background: #F59E0B20;
            color: #D97706;
            border: 1px solid #F59E0B;
        }}
        
        .confidence-bar {{
            margin-top: 10px;
        }}
        
        .confidence-label {{
            font-size: 0.8rem;
            color: #64748b;
            margin-bottom: 5px;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #3b82f6, #1d4ed8);
            border-radius: 4px;
            transition: width 0.8s ease;
        }}
        
        .agent-body {{
            padding: 20px;
        }}
        
        .explanation {{
            color: #475569;
            line-height: 1.6;
            font-size: 0.95rem;
        }}
        
        .explanation h1, .explanation h2, .explanation h3 {{
            color: #1e293b;
            margin: 15px 0 10px 0;
        }}
        
        .explanation ul, .explanation ol {{
            padding-left: 20px;
            margin: 10px 0;
        }}
        
        .explanation p {{
            margin-bottom: 10px;
        }}
        
        .footer {{
            background: #1e293b;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        
        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: repeat(2, 1fr);
                padding: 20px;
            }}
            
            .agents-section {{
                padding: 20px;
            }}
            
            .title {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1 class="title">📊 Investment Analysis Report</h1>
                <div class="ticker-display">
                    <div class="ticker-symbol">{ticker}</div>
                    <div class="ticker-label">Stock Symbol</div>
                    <div class="market-info">
                        <div class="market-item">
                            <div class="market-value">{total_agents}</div>
                            <div class="market-label">AI Agents</div>
                        </div>
                        <div class="market-item">
                            <div class="market-value">{avg_confidence:.0f}%</div>
                            <div class="market-label">Avg Confidence</div>
                        </div>
                        <div class="market-item">
                            <div class="market-value">{sentiment_icon}</div>
                            <div class="market-label">Sentiment</div>
                        </div>
                    </div>
                </div>
                <p class="subtitle">AI-Powered Market Intelligence Report</p>
            </div>
        </div>
        
        <div class="dashboard">
            <div class="metric-card sentiment-card">
                <div class="metric-value sentiment-value">
                    <span>{sentiment_icon}</span>
                    <span>{overall_sentiment}</span>
                </div>
                <div class="metric-label">Overall Sentiment</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" style="color: #10B981;">{strong_candidates}</div>
                <div class="metric-label">Strong Candidates</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" style="color: #3B82F6;">{possible_candidates}</div>
                <div class="metric-label">Possible Candidates</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" style="color: #F59E0B;">{not_typical}</div>
                <div class="metric-label">Not Typical Investments</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" style="color: #EF4444;">{avoid_signals}</div>
                <div class="metric-label">Avoid Recommendations</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" style="color: #3B82F6;">{avg_confidence:.1f}%</div>
                <div class="metric-label">Avg Confidence</div>
            </div>
        </div>
        
        <div class="agents-section">
            <h2 class="section-title">🤖 Detailed Analysis for {ticker}</h2>
            <div class="agents-grid">
"""

    for event in signal_events:
        # Map verdict to CSS class and icon
        verdict_mapping = {
            "Strong Candidate": ("verdict-strong", "🌟"),
            "Possible Candidate": ("verdict-possible", "👍"),
            "Not a Typical Investment": ("verdict-not-typical", "🤔"),
            "Avoid": ("verdict-avoid", "❌"),
        }

        verdict_class, verdict_icon = verdict_mapping.get(
            event.final_verdict, ("verdict-strong", "❓")
        )

        html_string += f"""
                <div class="agent-card">
                    <div class="agent-header">
                        <div class="agent-name">{event.agent}</div>
                        <div class="agent-verdict {verdict_class}">
                            {verdict_icon} {event.final_verdict}
                        </div>
                        <div class="confidence-bar">
                            <div class="confidence-label">Confidence: {event.confidence}%</div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {event.confidence}%"></div>
                            </div>
                        </div>
                    </div>
                    <div class="agent-body">
                        <div class="explanation">
                            {markdown2.markdown(event.explanation)}
                        </div>
                    </div>
                </div>
"""

    html_string += """
            </div>
        </div>
        
        <div class="footer">
            <p>Investment Analysis Report for {ticker} | Generated by AI Investment Analysis System</p>
        </div>
    </div>
    
    <script>
        // Add smooth animations on load
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.metric-card, .agent-card');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.transition = 'all 0.6s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        });
    </script>
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
