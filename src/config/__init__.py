from dataclasses import dataclass

from .agents import AgentConfig, WarrenBuffetConfig
from .alpha import AlphaVantageConfig

__all__ = ["AlphaVantageConfig", "Config", "WarrenBuffetConfig", "AgentConfig"]


@dataclass
class Config:
    alpha: AlphaVantageConfig
    agents: AgentConfig
