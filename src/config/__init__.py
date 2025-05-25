from dataclasses import dataclass, field
from os import environ

from dotenv import load_dotenv

from .agents import AgentConfig, WarrenBuffetConfig
from .alpha import AlphaVantageConfig
from .llm import LLMConfig
from .log import LogConfig

__all__ = ["AlphaVantageConfig", "Config", "WarrenBuffetConfig", "AgentConfig"]


@dataclass
class Config:
    log: LogConfig = field(default_factory=LogConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    alpha: AlphaVantageConfig = field(default_factory=AlphaVantageConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)

    def __post_init__(self):
        if not load_dotenv(override=True):
            raise RuntimeError("Failed to load environment variables")

        self.alpha.api_key = environ["ALPHA_VANTAGE"]
