from dataclasses import dataclass


@dataclass
class LLMConfig:
    model: str = "gemini-2.5-flash-preview-05-20"
