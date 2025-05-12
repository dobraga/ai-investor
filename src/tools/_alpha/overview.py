from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._utils import convert_none_str_to_none, convert_str_to_number


class OverviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_alias=True)

    name: str = Field(alias="Name", description="Company or asset name")
    asset_type: Optional[str] = Field(
        alias="AssetType", description="Type of the asset (e.g., Common Stock, ETF)"
    )
    exchange: Optional[str] = Field(
        alias="Exchange", description="Stock exchange where the asset is listed"
    )
    currency: Optional[str] = Field(alias="Currency", description="Trading currency")
    # cik: Optional[int] = Field(
    #     alias="CIK", description="Central Index Key assigned by the SEC"
    # )
    country: Optional[str] = Field(
        alias="Country", description="Country where the company is based"
    )
    # address: Optional[str] = Field(
    #     alias="Address", description="Registered company address"
    # )
    # official_site: Optional[str] = Field(
    #     alias="OfficialSite", description="Official company website"
    # )
    description: Optional[str] = Field(
        alias="Description", description="Brief business summary or description"
    )

    two_hundred_day_moving_average: Optional[float] = Field(
        alias="200DayMovingAverage", description="200-day moving average price"
    )
    fifty_day_moving_average: Optional[float] = Field(
        alias="50DayMovingAverage", description="50-day moving average price"
    )
    fifty_two_week_high: Optional[float] = Field(
        alias="52WeekHigh", description="Highest price in the last 52 weeks"
    )
    fifty_two_week_low: Optional[float] = Field(
        alias="52WeekLow", description="Lowest price in the last 52 weeks"
    )

    market_capitalization: Optional[int] = Field(
        alias="MarketCapitalization",
        description="Total market value of all outstanding shares",
    )
    book_value: Optional[float] = Field(
        alias="BookValue", description="Total assets minus liabilities per share"
    )
    price_to_book_ratio: Optional[float] = Field(
        alias="PriceToBookRatio",
        description="Market price divided by book value per share",
    )
    price_to_sales_ratio_ttm: Optional[float] = Field(
        alias="PriceToSalesRatioTTM",
        description="Market price divided by total revenue (TTM)",
    )
    pe_ratio: Optional[float] = Field(
        alias="PERatio", description="Price-to-earnings ratio (TTM)"
    )
    forward_pe: Optional[float] = Field(
        alias="ForwardPE",
        description="Price-to-earnings ratio based on projected earnings",
    )
    trailing_pe: Optional[float] = Field(
        alias="TrailingPE",
        description="Price-to-earnings ratio based on previous earnings",
    )
    ev_to_revenue: Optional[float] = Field(
        alias="EVToRevenue", description="Enterprise Value divided by revenue"
    )
    ev_to_ebitda: Optional[float] = Field(
        alias="EVToEBITDA", description="Enterprise Value divided by EBITDA"
    )
    peg_ratio: Optional[float] = Field(
        alias="PEGRatio", description="Price/Earnings to Growth ratio"
    )
    analyst_target_price: Optional[float] = Field(
        alias="AnalystTargetPrice", description="Average price target by analysts"
    )

    return_on_assets_ttm: Optional[float] = Field(
        alias="ReturnOnAssetsTTM", description="Return on assets (TTM)"
    )
    return_on_equity_ttm: Optional[float] = Field(
        alias="ReturnOnEquityTTM", description="Return on equity (TTM)"
    )
    gross_profit_ttm: Optional[int] = Field(
        alias="GrossProfitTTM", description="Gross profit (TTM)"
    )
    revenue_ttm: Optional[int] = Field(
        alias="RevenueTTM", description="Total revenue (TTM)"
    )
    revenue_per_share_ttm: Optional[float] = Field(
        alias="RevenuePerShareTTM", description="Revenue per outstanding share (TTM)"
    )
    ebitda: Optional[int] = Field(
        alias="EBITDA",
        description="Earnings Before Interest, Taxes, Depreciation, and Amortization",
    )
    operating_margin_ttm: Optional[float] = Field(
        alias="OperatingMarginTTM",
        description="Operating income as a percentage of revenue (TTM)",
    )
    profit_margin: Optional[float] = Field(
        alias="ProfitMargin", description="Net profit as a percentage of revenue"
    )

    eps: Optional[float] = Field(alias="EPS", description="Earnings per share")
    diluted_eps_ttm: Optional[float] = Field(
        alias="DilutedEPSTTM", description="Earnings per share after dilution (TTM)"
    )
    dividend_yield: Optional[float] = Field(
        alias="DividendYield", description="Annual dividend divided by share price"
    )
    dividend_per_share: Optional[float] = Field(
        alias="DividendPerShare", description="Annual dividend amount per share"
    )
    dividend_date: Optional[date] = Field(
        alias="DividendDate", description="Next dividend payment date"
    )
    ex_dividend_date: Optional[date] = Field(
        alias="ExDividendDate",
        description="Date on or after which a stock is traded without a dividend",
    )

    quarterly_earnings_growth_yoy: Optional[float] = Field(
        alias="QuarterlyEarningsGrowthYOY",
        description="Year-over-year earnings growth for the latest quarter",
    )
    quarterly_revenue_growth_yoy: Optional[float] = Field(
        alias="QuarterlyRevenueGrowthYOY",
        description="Year-over-year revenue growth for the latest quarter",
    )
    shares_outstanding: Optional[int] = Field(
        alias="SharesOutstanding", description="Number of shares currently outstanding"
    )

    analyst_rating_strong_buy: Optional[int] = Field(
        alias="AnalystRatingStrongBuy",
        description="Number of analysts rating as Strong Buy",
    )
    analyst_rating_buy: Optional[int] = Field(
        alias="AnalystRatingBuy", description="Number of analysts rating as Buy"
    )
    analyst_rating_hold: Optional[int] = Field(
        alias="AnalystRatingHold", description="Number of analysts rating as Hold"
    )
    analyst_rating_sell: Optional[int] = Field(
        alias="AnalystRatingSell", description="Number of analysts rating as Sell"
    )
    analyst_rating_strong_sell: Optional[int] = Field(
        alias="AnalystRatingStrongSell",
        description="Number of analysts rating as Strong Sell",
    )

    industry: Optional[str] = Field(
        alias="Industry", description="Industry classification"
    )
    sector: Optional[str] = Field(alias="Sector", description="Sector classification")
    fiscal_year_end: Optional[str] = Field(
        alias="FiscalYearEnd", description="Company’s fiscal year end date"
    )
    latest_quarter: Optional[date] = Field(
        alias="LatestQuarter", description="Date of the most recent fiscal quarter"
    )
    beta: Optional[float] = Field(
        alias="Beta",
        description="Stock volatility relative to the market (beta coefficient)",
    )

    @field_validator(
        "two_hundred_day_moving_average",
        "fifty_day_moving_average",
        "fifty_two_week_high",
        "fifty_two_week_low",
        "market_capitalization",
        "book_value",
        "price_to_book_ratio",
        "price_to_sales_ratio_ttm",
        "pe_ratio",
        "forward_pe",
        "trailing_pe",
        "ev_to_revenue",
        "ev_to_ebitda",
        "peg_ratio",
        "analyst_target_price",
        "return_on_assets_ttm",
        "return_on_equity_ttm",
        "gross_profit_ttm",
        "revenue_ttm",
        "revenue_per_share_ttm",
        "ebitda",
        "operating_margin_ttm",
        "profit_margin",
        "eps",
        "diluted_eps_ttm",
        "dividend_yield",
        "dividend_per_share",
        "quarterly_earnings_growth_yoy",
        "quarterly_revenue_growth_yoy",
        "shares_outstanding",
        "beta",
        mode="before",
    )
    @classmethod
    def _normalize_and_convert_numeric(cls, v):
        v = convert_none_str_to_none(v)
        return convert_str_to_number(v)
