from dataclasses import dataclass, field

from .warren_buffet import WarrenBuffetConfig

__all__ = ["AgentConfig", "WarrenBuffetConfig"]


@dataclass
class AgentConfig:
    warren_buffet: WarrenBuffetConfig = field(default_factory=WarrenBuffetConfig)
