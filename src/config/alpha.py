from dataclasses import dataclass
from pathlib import Path

DAY_IN_SECONDS = 60 * 60 * 24
CURRENT_DIR = Path(__file__).parent.parent.parent


@dataclass
class AlphaVantageConfig:
    api_key: str = "demo"
    timeout: int = 10  # timeout in seconds
    cache_dir: Path = CURRENT_DIR / ".cache" / "alpha"  # cache directory
    cache_timeout: int = 60 * DAY_IN_SECONDS  # cache timeout in seconds
    cache_error_dir = CURRENT_DIR / ".cache" / "alpha_error"  # cache error directory
