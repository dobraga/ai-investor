from dataclasses import dataclass
from logging import basicConfig


@dataclass
class LogConfig:
    level: str = "INFO"  #
    format: str = "%(asctime)s %(levelname)s %(message)s"  #
    datefmt: str = "%H:%M:%S"  #

    def basic_config(self):
        basicConfig(level=self.level, format=self.format, datefmt=self.datefmt)
