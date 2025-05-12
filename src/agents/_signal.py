from typing import Literal

from pydantic import BaseModel


class SignalAnalysis(BaseModel):
    final_verdict: Literal[
        "Strong Candidate", "Possible Candidate", "Not a Typical Investment", "Avoid"
    ]
    confidence: int
    explanation: str
