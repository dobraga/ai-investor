from json import loads
from pathlib import Path

import pytest

from src.tools._alpha import BalanceSheetResponse, CashFlowResponse, EarningsResponse
from src.tools.alpha import AlphaVantageClient


@pytest.fixture
def client():
    return AlphaVantageClient(api_key="demo")


@pytest.fixture
def alpha_data_dir():
    return Path(__file__).parent / "data" / "alpha_data"


def test_parse_earnings(client, alpha_data_dir):
    data = (alpha_data_dir / "earnings.json").read_text()
    data = loads(data)
    data = EarningsResponse(**data)
    assert isinstance(data, EarningsResponse)

    assert len(data.annual_earnings) > 0
    assert len(data.quarterly_earnings) > 0


def test_parse_balance_sheet(client, alpha_data_dir):
    data = (alpha_data_dir / "balance_sheet.json").read_text()
    data = loads(data)
    data = BalanceSheetResponse(**data)
    assert isinstance(data, BalanceSheetResponse)


def test_parse_cash_flow(client, alpha_data_dir):
    data = (alpha_data_dir / "cash_flow.json").read_text()
    data = loads(data)
    data = CashFlowResponse(**data)
    assert isinstance(data, CashFlowResponse)


def test_get_earnings(client):
    data = client.get_earnings("IBM")
    assert isinstance(data, EarningsResponse)


def test_get_balance_sheet(client):
    data = client.get_balance_sheet("IBM")
    assert isinstance(data, BalanceSheetResponse)


def test_get_cash_flow(client):
    data = client.get_cashflow("IBM")
    assert isinstance(data, CashFlowResponse)
