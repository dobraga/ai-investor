from typing import Literal

from llama_index.core.workflow import Event


class SignalEvent(Event):
    agent: str
    final_verdict: Literal[
        "Strong Candidate", "Possible Candidate", "Not a Typical Investment", "Avoid"
    ]
    confidence: int
    explanation: str
