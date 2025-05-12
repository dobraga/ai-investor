from dataclasses import dataclass
from pathlib import Path

DAY_IN_SECONDS = 60 * 60 * 24


@dataclass
class AlphaVantageConfig:
    timeout: int = 10  # timeout in seconds
    cache_dir: Path = Path(".cache") / "alpha"  # cache directory
    cache_timeout: int = DAY_IN_SECONDS # cache timeout
