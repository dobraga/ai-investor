from json import dumps
from pathlib import Path

from src.tools.alpha import AlphaVantageClient

if __name__ == "__main__":
    data_dir = Path(__file__).parent / "alpha_data"
    data_dir.mkdir(exist_ok=True)

    client = AlphaVantageClient(api_key="demo")

    (data_dir / "earnings.json").write_text(
        dumps(client._fetch("EARNINGS", "IBM"), indent=4)
    )

    (data_dir / "cash_flow.json").write_text(
        dumps(client._fetch("CASH_FLOW", "IBM"), indent=4)
    )

    (data_dir / "balance_sheet.json").write_text(
        dumps(client._fetch("BALANCE_SHEET", "IBM"), indent=4)
    )
