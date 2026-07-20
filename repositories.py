"""Google Sheets repository with a local CSV adapter for credential-free demos."""

from __future__ import annotations

import csv
import json
import threading
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Any

from config import Settings, get_settings


TRANSACTION_COLUMNS = [
    "transaction_id",
    "timestamp",
    "submission",
    "decision",
    "selected_buyer",
    "selected_market",
    "fish_type",
    "quantity_kg",
    "expected_revenue",
    "outcome",
    "notification_status",
    "execution_log",
]


class MarketplaceRepository(ABC):
    @abstractmethod
    def get_markets(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_buyers(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def save_transaction(self, record: dict[str, Any]) -> str: ...

    @abstractmethod
    def get_transactions(self) -> list[dict[str, Any]]: ...


class CSVRepository(MarketplaceRepository):
    """Simple, persistent local adapter that mirrors the three sheet tabs."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.market_file = data_dir / "market_prices.csv"
        self.buyers_file = data_dir / "buyers.csv"
        self.transactions_file = data_dir / "transactions.csv"
        # Instance-level lock so concurrent test runs with separate tmp
        # directories do not block or interfere with each other.
        self._write_lock = threading.Lock()

    @staticmethod
    def _read(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    def get_markets(self) -> list[dict[str, Any]]:
        return self._read(self.market_file)

    def get_buyers(self) -> list[dict[str, Any]]:
        return self._read(self.buyers_file)

    def save_transaction(self, record: dict[str, Any]) -> str:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        row = _serialize_transaction(record)
        with self._write_lock:
            exists = self.transactions_file.exists()
            with self.transactions_file.open(
                "a", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=TRANSACTION_COLUMNS)
                if not exists or self.transactions_file.stat().st_size == 0:
                    writer.writeheader()
                writer.writerow(row)
        return str(record["transaction_id"])

    def get_transactions(self) -> list[dict[str, Any]]:
        return self._read(self.transactions_file)


class GoogleSheetsRepository(MarketplaceRepository):
    """Repository backed by the requested Market Prices, Buyers and Transactions tabs."""

    def __init__(self, settings: Settings):
        import gspread

        if settings.google_service_account_json:
            credentials = json.loads(settings.google_service_account_json)
            client = gspread.service_account_from_dict(credentials)
        else:
            client = gspread.service_account(
                filename=settings.google_service_account_file
            )
        self.workbook = client.open_by_key(settings.google_sheet_id)
        self.market_sheet_name = settings.market_sheet_name
        self.buyers_sheet_name = settings.buyers_sheet_name
        self.transactions_sheet_name = settings.transactions_sheet_name

    def get_markets(self) -> list[dict[str, Any]]:
        return self.workbook.worksheet(self.market_sheet_name).get_all_records()

    def get_buyers(self) -> list[dict[str, Any]]:
        return self.workbook.worksheet(self.buyers_sheet_name).get_all_records()

    def save_transaction(self, record: dict[str, Any]) -> str:
        worksheet = self.workbook.worksheet(self.transactions_sheet_name)
        row = _serialize_transaction(record)
        if not worksheet.row_values(1):
            worksheet.append_row(TRANSACTION_COLUMNS, value_input_option="RAW")
        worksheet.append_row(
            [row[column] for column in TRANSACTION_COLUMNS],
            value_input_option="USER_ENTERED",
        )
        return str(record["transaction_id"])

    def get_transactions(self) -> list[dict[str, Any]]:
        return self.workbook.worksheet(
            self.transactions_sheet_name
        ).get_all_records()


def _serialize_transaction(record: dict[str, Any]) -> dict[str, Any]:
    row = {column: record.get(column, "") for column in TRANSACTION_COLUMNS}
    for field in ("submission", "execution_log"):
        value = row[field]
        if not isinstance(value, str):
            row[field] = json.dumps(value, ensure_ascii=False, default=str)
    return row


@lru_cache(maxsize=1)
def get_repository() -> MarketplaceRepository:
    settings = get_settings()
    if settings.cloud_sheets_ready:
        return GoogleSheetsRepository(settings)
    return CSVRepository(settings.data_dir)

