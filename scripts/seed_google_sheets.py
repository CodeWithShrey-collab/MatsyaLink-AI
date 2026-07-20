"""Create/update the three prototype tabs from the bundled CSV datasets."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings  # noqa: E402
from repositories import TRANSACTION_COLUMNS  # noqa: E402


def read_rows(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def main() -> None:
    import gspread

    settings = get_settings()
    if not settings.google_sheet_id:
        raise SystemExit("Set GOOGLE_SHEET_ID before running this script.")
    if settings.google_service_account_json:
        client = gspread.service_account_from_dict(
            json.loads(settings.google_service_account_json)
        )
    elif settings.google_service_account_file:
        client = gspread.service_account(
            filename=settings.google_service_account_file
        )
    else:
        raise SystemExit("Configure a Google service-account file or JSON value.")

    workbook = client.open_by_key(settings.google_sheet_id)
    datasets = {
        settings.market_sheet_name: read_rows(settings.data_dir / "market_prices.csv"),
        settings.buyers_sheet_name: read_rows(settings.data_dir / "buyers.csv"),
        settings.transactions_sheet_name: [TRANSACTION_COLUMNS],
    }
    existing = {sheet.title: sheet for sheet in workbook.worksheets()}
    for title, rows in datasets.items():
        worksheet = existing.get(title) or workbook.add_worksheet(
            title=title, rows=max(len(rows) + 100, 200), cols=20
        )
        worksheet.clear()
        worksheet.update(rows, "A1", value_input_option="USER_ENTERED")
        print(f"Seeded {title}: {len(rows) - 1} data row(s)")


if __name__ == "__main__":
    main()

