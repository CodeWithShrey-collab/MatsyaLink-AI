"""Extensible domain models for the MatsyaLink AI marketplace."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class FreshnessStatus(StrEnum):
    FRESH = "Fresh"
    MODERATE = "Moderate"
    LOW = "Low Freshness"


class UrgencyLevel(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class DecisionType(StrEnum):
    DIRECT_SALE = "direct_sale"
    NEGOTIATE = "negotiate"
    ALTERNATE_MARKET = "alternate_market"
    REJECTED = "rejected"


class DemandLevel(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class DomainModel(BaseModel):
    model_config = ConfigDict(
        extra="allow", validate_assignment=True, str_strip_whitespace=True
    )


class Fisher(DomainModel):
    fisher_id: str = Field(default_factory=lambda: f"F-{uuid4().hex[:8]}")
    name: str = Field(min_length=2, max_length=120)
    contact_number: str = Field(min_length=7, max_length=20)
    location: str = Field(min_length=2, max_length=160)
    cooperative_name: str | None = None


class Catch(DomainModel):
    catch_id: str = Field(default_factory=lambda: f"C-{uuid4().hex[:8]}")
    fisher: Fisher
    fish_type: str = Field(min_length=2, max_length=80)
    quantity_kg: float = Field(gt=0, le=100_000)
    catch_time: datetime
    expected_min_price_per_kg: float = Field(ge=0, le=1_000_000)
    max_travel_distance_km: float = Field(gt=0, le=2_000)
    grade: str | None = None

    @field_validator("fish_type")
    @classmethod
    def normalize_fish_type(cls, value: str) -> str:
        return " ".join(part.capitalize() for part in value.strip().split())

    @field_validator("catch_time")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class Market(DomainModel):
    market_id: str
    market_name: str
    location: str
    fish_type: str
    distance_km: float = Field(ge=0)
    current_demand: DemandLevel
    current_price_per_kg: float = Field(ge=0)
    updated_at: datetime | None = None


class MarketPrice(DomainModel):
    market_id: str
    fish_type: str
    price_per_kg: float = Field(ge=0)
    observed_at: datetime | None = None
    source: str = "Google Sheets"


class Buyer(DomainModel):
    buyer_id: str
    buyer_name: str
    accepted_fish_types: list[str]
    capacity_kg: float = Field(ge=0)
    location: str
    distance_km: float = Field(ge=0)
    price_offered_per_kg: float = Field(ge=0)
    contact_email: EmailStr
    current_demand: DemandLevel
    freshness_acceptance: FreshnessStatus = FreshnessStatus.MODERATE

    @field_validator("accepted_fish_types", mode="before")
    @classmethod
    def parse_fish_types(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            value = value.replace(",", "|").split("|")
        return [str(item).strip().title() for item in value if str(item).strip()]


class BuyerScore(DomainModel):
    buyer_id: str
    buyer_name: str
    score: float = Field(ge=0, le=100)
    price_score: float = Field(ge=0, le=100)
    distance_score: float = Field(ge=0, le=100)
    demand_score: float = Field(ge=0, le=100)
    capacity_score: float = Field(ge=0, le=100)
    freshness_score: float = Field(ge=0, le=100)
    expected_revenue: float = Field(ge=0)
    reasoning: str


class MatchResult(DomainModel):
    match_id: str = Field(default_factory=lambda: f"M-{uuid4().hex[:10]}")
    selected_buyer: Buyer | None = None
    selected_market: Market | None = None
    ranked_buyers: list[BuyerScore] = Field(default_factory=list)
    decision: DecisionType
    expected_revenue: float = 0
    explanation: str


class Notification(DomainModel):
    notification_id: str = Field(default_factory=lambda: f"N-{uuid4().hex[:10]}")
    recipient: EmailStr
    subject: str
    body: str
    status: str = "pending"
    sent_at: datetime | None = None


class Transaction(DomainModel):
    transaction_id: str = Field(default_factory=lambda: f"T-{uuid4().hex[:10]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submission: dict[str, Any]
    decision: DecisionType
    selected_buyer: str | None = None
    selected_market: str | None = None
    fish_type: str
    quantity_kg: float
    expected_revenue: float = 0
    outcome: str
    notification_status: str = "not_applicable"
    execution_log: list[dict[str, Any]] = Field(default_factory=list)


class DecisionOutput(DomainModel):
    """Schema used for Gemini's constrained decision explanation."""

    decision: DecisionType
    selected_buyer_id: str | None = None
    selected_market_id: str | None = None
    explanation: str
    negotiation_strategy: str | None = None

