from dataclasses import dataclass


@dataclass
class WarrenBuffetConfig:
    discount_rate: float = 0.10  # Annual discount rate used to convert future free cash flows into present value
    fcf_growth_rate: float = 0.05  # Expected annual growth rate of Free Cash Flow, used to project FCF over the forecast period
    projection_years: int = 5  # Number of years over which future cash flows will be forecasted before applying a terminal value
