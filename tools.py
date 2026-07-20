"""Tools executed by MatsyaLink's LangGraph nodes.

The public functions are LangChain-compatible tools, but their invocation and
routing are owned entirely by the LangGraph workflow.
"""

from __future__ import annotations

import smtplib
import ssl
from collections import Counter
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any

from langchain_core.tools import tool

from config import get_settings
from models import Buyer, BuyerScore, DemandLevel, FreshnessStatus, Market, Transaction
from repositories import get_repository


def _clean_key(value: str) -> str:
    return value.strip().casefold()


@tool
def get_market_prices(fish_type: str) -> list[dict[str, Any]]:
    """Read and return only Google Sheet/local market records for a fish type."""

    records: list[dict[str, Any]] = []
    for raw in get_repository().get_markets():
        if _clean_key(str(raw.get("fish_type", ""))) != _clean_key(fish_type):
            continue
        records.append(Market.model_validate(raw).model_dump(mode="json"))
    return records


@tool
def get_available_buyers(fish_type: str) -> list[dict[str, Any]]:
    """Retrieve buyers whose stored accepted-fish list includes the requested type."""

    result: list[dict[str, Any]] = []
    for raw in get_repository().get_buyers():
        buyer = Buyer.model_validate(raw)
        accepted = {_clean_key(item) for item in buyer.accepted_fish_types}
        if _clean_key(fish_type) in accepted and buyer.current_demand != DemandLevel.LOW:
            result.append(buyer.model_dump(mode="json"))
    return result


def _freshness_compatible(
    catch_freshness: FreshnessStatus, buyer_acceptance: FreshnessStatus
) -> float:
    rank = {
        FreshnessStatus.LOW: 1,
        FreshnessStatus.MODERATE: 2,
        FreshnessStatus.FRESH: 3,
    }
    # A buyer marked "Fresh" is strict; "Low Freshness" accepts every class.
    required = rank[buyer_acceptance]
    supplied = rank[catch_freshness]
    if supplied >= required:
        return 100.0
    if supplied == required - 1:
        return 40.0
    return 0.0


@tool
def calculate_buyer_score(
    buyer: dict[str, Any],
    quantity_kg: float,
    max_travel_distance_km: float,
    freshness_status: str,
    market_reference_price: float,
) -> dict[str, Any]:
    """Compute a transparent weighted buyer score using the mandated weights."""

    record = Buyer.model_validate(buyer)
    reference = max(float(market_reference_price), 1.0)
    price_score = min(record.price_offered_per_kg / reference, 1.0) * 100
    distance_score = max(
        0.0,
        100 * (1 - record.distance_km / max(float(max_travel_distance_km), 1.0)),
    )
    demand_score = {
        DemandLevel.HIGH: 100.0,
        DemandLevel.MEDIUM: 65.0,
        DemandLevel.LOW: 25.0,
    }[record.current_demand]
    capacity_score = min(record.capacity_kg / max(float(quantity_kg), 1.0), 1.0) * 100
    freshness_score = _freshness_compatible(
        FreshnessStatus(freshness_status), record.freshness_acceptance
    )
    weighted_score = (
        price_score * 0.35
        + distance_score * 0.25
        + demand_score * 0.20
        + capacity_score * 0.10
        + freshness_score * 0.10
    )
    expected_revenue = min(record.capacity_kg, quantity_kg) * record.price_offered_per_kg
    reasoning = (
        f"Price {price_score:.0f}/100 (35%), distance {distance_score:.0f}/100 "
        f"(25%), demand {demand_score:.0f}/100 (20%), capacity "
        f"{capacity_score:.0f}/100 (10%), freshness compatibility "
        f"{freshness_score:.0f}/100 (10%)."
    )
    score = BuyerScore(
        buyer_id=record.buyer_id,
        buyer_name=record.buyer_name,
        score=round(weighted_score, 2),
        price_score=round(price_score, 2),
        distance_score=round(distance_score, 2),
        demand_score=round(demand_score, 2),
        capacity_score=round(capacity_score, 2),
        freshness_score=round(freshness_score, 2),
        expected_revenue=round(expected_revenue, 2),
        reasoning=reasoning,
    )
    return score.model_dump(mode="json")


@tool
def send_buyer_notification(
    recipient: str, subject: str, body: str
) -> dict[str, Any]:
    """Send a buyer offer using Gmail SMTP, or return a safe dry-run preview."""

    settings = get_settings()
    if not settings.email_ready:
        return {
            "status": "dry_run",
            "recipient": recipient,
            "message": "Email composed but not sent because EMAIL_DRY_RUN is enabled.",
        }

    message = EmailMessage()
    message["From"] = settings.smtp_sender or settings.smtp_username
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
    return {
        "status": "sent",
        "recipient": recipient,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }


@tool
def save_transaction(transaction: dict[str, Any]) -> dict[str, Any]:
    """Validate and persist a workflow result to the Transactions sheet."""

    validated = Transaction.model_validate(transaction)
    transaction_id = get_repository().save_transaction(
        validated.model_dump(mode="json")
    )
    return {"status": "saved", "transaction_id": transaction_id}


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@tool
def generate_analytics() -> dict[str, Any]:
    """Aggregate transaction metrics for the Streamlit analytics dashboard."""

    records = get_repository().get_transactions()
    total = len(records)
    decisions = Counter(str(row.get("decision", "")) for row in records)
    fish_types = Counter(str(row.get("fish_type", "Unknown")) for row in records)
    buyers = Counter(
        str(row.get("selected_buyer"))
        for row in records
        if row.get("selected_buyer")
    )
    markets = Counter(
        str(row.get("selected_market"))
        for row in records
        if row.get("selected_market")
    )
    revenue = sum(_float(row.get("expected_revenue")) for row in records)
    direct_sales = decisions.get("direct_sale", 0)
    negotiations = decisions.get("negotiate", 0)
    fallbacks = decisions.get("alternate_market", 0)

    def rate(count: int) -> float:
        return round(count / total * 100, 2) if total else 0.0

    return {
        "total_catches_processed": total,
        "average_revenue": round(revenue / total, 2) if total else 0.0,
        "total_expected_revenue": round(revenue, 2),
        "success_rate": rate(direct_sales),
        "negotiation_rate": rate(negotiations),
        "no_buyer_rate": rate(fallbacks),
        "fish_type_counts": dict(fish_types.most_common()),
        "buyer_utilization": dict(buyers.most_common()),
        "market_utilization": dict(markets.most_common()),
    }


AGENT_TOOLS = [
    get_market_prices,
    get_available_buyers,
    calculate_buyer_score,
    send_buyer_notification,
    save_transaction,
    generate_analytics,
]
