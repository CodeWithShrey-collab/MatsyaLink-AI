"""Central configuration for MatsyaLink AI.

The application is usable without cloud credentials. In that mode it reads the
CSV files in ``data/``, uses deterministic reasoning, and writes email previews
to the execution log instead of contacting an SMTP server.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "MatsyaLink AI")
    environment: str = os.getenv("APP_ENV", "development")
    timezone: str = os.getenv("APP_TIMEZONE", "Asia/Kolkata")

    # Gemini is opt-in so a hackathon demo stays deterministic without a key.
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_enabled: bool = _as_bool(os.getenv("GEMINI_ENABLED"), False)

    # A service-account file or a JSON value may be supplied.
    google_sheet_id: str = os.getenv("GOOGLE_SHEET_ID", "")
    google_service_account_file: str = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_FILE", ""
    )
    google_service_account_json: str = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON", ""
    )
    use_google_sheets: bool = _as_bool(os.getenv("USE_GOOGLE_SHEETS"), False)

    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_sender: str = os.getenv("SMTP_SENDER", "")
    email_dry_run: bool = _as_bool(os.getenv("EMAIL_DRY_RUN"), True)

    data_dir: Path = BASE_DIR / "data"
    market_sheet_name: str = "Market Prices"
    buyers_sheet_name: str = "Buyers"
    transactions_sheet_name: str = "Transactions"

    @property
    def cloud_sheets_ready(self) -> bool:
        return bool(
            self.use_google_sheets
            and self.google_sheet_id
            and (
                self.google_service_account_file
                or self.google_service_account_json
            )
        )

    @property
    def email_ready(self) -> bool:
        return bool(
            not self.email_dry_run
            and self.smtp_username
            and self.smtp_password
            and (self.smtp_sender or self.smtp_username)
        )

    @property
    def llm_ready(self) -> bool:
        return bool(self.gemini_enabled and self.gemini_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

