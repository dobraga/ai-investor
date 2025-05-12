from dataclasses import dataclass

from .alpha import AlphaVantageConfig

__all__ = ["AlphaVantageConfig", "Config"]


@dataclass
class Config:
    alpha: AlphaVantageConfig
