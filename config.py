"""Central configuration for MatsyaLink AI.

The application is usable without cloud credentials. In that mode it reads the
CSV files in ``data/``, uses deterministic reasoning, and writes email previews
to the execution log instead of contacting an SMTP server.

Every tunable threshold, weight, and operational constant is expressed here as
an env-driven field so operators can adjust system behaviour at runtime without
touching source code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _as_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    # ------------------------------------------------------------------ App
    app_name: str = field(
        default_factory=lambda: os.getenv("APP_NAME", "MatsyaLink AI")
    )
    environment: str = field(
        default_factory=lambda: os.getenv("APP_ENV", "development")
    )
    timezone: str = field(
        default_factory=lambda: os.getenv("APP_TIMEZONE", "Asia/Kolkata")
    )
    currency_code: str = field(
        default_factory=lambda: os.getenv("CURRENCY_CODE", "INR")
    )

    # ------------------------------------------------------------------ LLM
    # Gemma 4 is served through Ollama. The default host uses a signed-in local
    # Ollama daemon to offload the ``-cloud`` model; ``https://ollama.com`` plus
    # an API key can be used for direct cloud API access.
    ollama_enabled: bool = field(
        default_factory=lambda: _as_bool(os.getenv("OLLAMA_ENABLED"), False)
    )
    ollama_host: str = field(
        default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
    ollama_api_key: str = field(
        default_factory=lambda: os.getenv("OLLAMA_API_KEY", "")
    )
    ollama_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")
    )

    # ------------------------------------------------------------------ Google Sheets
    # A service-account file or a JSON value may be supplied.
    google_sheet_id: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SHEET_ID", "")
    )
    google_service_account_file: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    )
    google_service_account_json: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    )
    use_google_sheets: bool = field(
        default_factory=lambda: _as_bool(os.getenv("USE_GOOGLE_SHEETS"), False)
    )

    # ------------------------------------------------------------------ SMTP
    smtp_host: str = field(
        default_factory=lambda: os.getenv("SMTP_HOST", "smtp.gmail.com")
    )
    smtp_port: int = field(
        default_factory=lambda: _as_int(os.getenv("SMTP_PORT"), 587)
    )
    smtp_username: str = field(
        default_factory=lambda: os.getenv("SMTP_USERNAME", "")
    )
    smtp_password: str = field(
        default_factory=lambda: os.getenv("SMTP_PASSWORD", "")
    )
    smtp_sender: str = field(
        default_factory=lambda: os.getenv("SMTP_SENDER", "")
    )
    smtp_timeout_sec: int = field(
        default_factory=lambda: _as_int(os.getenv("SMTP_TIMEOUT_SEC"), 20)
    )
    email_dry_run: bool = field(
        default_factory=lambda: _as_bool(os.getenv("EMAIL_DRY_RUN"), True)
    )

    # ------------------------------------------------------------------ Data / Sheet tabs
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data")
    market_sheet_name: str = field(
        default_factory=lambda: os.getenv("MARKET_SHEET_NAME", "Market Prices")
    )
    buyers_sheet_name: str = field(
        default_factory=lambda: os.getenv("BUYERS_SHEET_NAME", "Buyers")
    )
    transactions_sheet_name: str = field(
        default_factory=lambda: os.getenv("TRANSACTIONS_SHEET_NAME", "Transactions")
    )

    # ------------------------------------------------------------------ Freshness thresholds (hours)
    freshness_fresh_hours: float = field(
        default_factory=lambda: _as_float(os.getenv("FRESHNESS_FRESH_HOURS"), 6.0)
    )
    freshness_moderate_hours: float = field(
        default_factory=lambda: _as_float(os.getenv("FRESHNESS_MODERATE_HOURS"), 12.0)
    )

    # ------------------------------------------------------------------ Urgency thresholds (kg)
    urgency_high_qty_kg: float = field(
        default_factory=lambda: _as_float(os.getenv("URGENCY_HIGH_QTY_KG"), 750.0)
    )
    urgency_medium_qty_kg: float = field(
        default_factory=lambda: _as_float(os.getenv("URGENCY_MEDIUM_QTY_KG"), 300.0)
    )

    # ------------------------------------------------------------------ Buyer scoring weights
    # Must sum to 1.0. Validated by the score_weights_valid property.
    score_weight_price: float = field(
        default_factory=lambda: _as_float(os.getenv("SCORE_WEIGHT_PRICE"), 0.35)
    )
    score_weight_distance: float = field(
        default_factory=lambda: _as_float(os.getenv("SCORE_WEIGHT_DISTANCE"), 0.25)
    )
    score_weight_demand: float = field(
        default_factory=lambda: _as_float(os.getenv("SCORE_WEIGHT_DEMAND"), 0.20)
    )
    score_weight_capacity: float = field(
        default_factory=lambda: _as_float(os.getenv("SCORE_WEIGHT_CAPACITY"), 0.10)
    )
    score_weight_freshness: float = field(
        default_factory=lambda: _as_float(os.getenv("SCORE_WEIGHT_FRESHNESS"), 0.10)
    )

    # ------------------------------------------------------------------ Demand score values (0–100)
    score_demand_high: float = field(
        default_factory=lambda: _as_float(os.getenv("SCORE_DEMAND_HIGH"), 100.0)
    )
    score_demand_medium: float = field(
        default_factory=lambda: _as_float(os.getenv("SCORE_DEMAND_MEDIUM"), 65.0)
    )
    score_demand_low: float = field(
        default_factory=lambda: _as_float(os.getenv("SCORE_DEMAND_LOW"), 25.0)
    )

    # ------------------------------------------------------------------ Freshness compatibility
    # Score (0–100) awarded when the catch is one grade below what the buyer requires.
    freshness_partial_score: float = field(
        default_factory=lambda: _as_float(os.getenv("FRESHNESS_PARTIAL_SCORE"), 40.0)
    )

    # ------------------------------------------------------------------ Derived properties

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
        if not self.ollama_enabled:
            return False
        is_direct_cloud = self.ollama_host.rstrip("/") == "https://ollama.com"
        return bool(not is_direct_cloud or self.ollama_api_key)

    @property
    def model_provider(self) -> str:
        """Human-readable provider label derived from the configured host."""
        host = self.ollama_host.rstrip("/").lower()
        if "ollama.com" in host:
            return "ollama_cloud"
        return "ollama_local"

    @property
    def score_weights_sum(self) -> float:
        return (
            self.score_weight_price
            + self.score_weight_distance
            + self.score_weight_demand
            + self.score_weight_capacity
            + self.score_weight_freshness
        )

    @property
    def score_weights_valid(self) -> bool:
        """Return True when the five weights sum to 1.0 within floating-point tolerance."""
        return abs(self.score_weights_sum - 1.0) <= 0.001


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    if not settings.score_weights_valid:
        raise ValueError(
            f"Buyer scoring weights must sum to 1.0 but sum to "
            f"{settings.score_weights_sum:.4f}. "
            f"Check SCORE_WEIGHT_* environment variables."
        )
    return settings
