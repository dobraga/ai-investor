from dataclasses import dataclass

from .warren_buffet import WarrenBuffetConfig

__all__ = ["AgentConfig", "WarrenBuffetConfig"]


@dataclass
class AgentConfig:
    warren_buffet: WarrenBuffetConfig
