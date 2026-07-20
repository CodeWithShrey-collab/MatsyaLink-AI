from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from config import get_settings
from graph import build_graph
from state import initial_state


def submission(
    *, fish_type: str, expected_price: float, hours_old: float, location: str
) -> dict:
    now = datetime.now(ZoneInfo(get_settings().timezone))
    return {
        "fisher_name": "Demo Fisher",
        "contact_number": "+91-9876500000",
        "location": location,
        "fish_type": fish_type,
        "quantity_kg": 250,
        "catch_time": (now - timedelta(hours=hours_old)).isoformat(),
        "expected_min_price_per_kg": expected_price,
        "max_travel_distance_km": 50,
    }


@pytest.fixture
def app():
    return build_graph(with_memory=False)


def test_high_demand_routes_to_direct_sale_and_notification(app):
    result = app.invoke(
        initial_state(
            submission(
                fish_type="Mackerel",
                expected_price=280,
                hours_old=2,
                location="Margao, Goa",
            )
        )
    )

    assert result["decision"]["type"] == "direct_sale"
    assert result["selected_buyer"] is not None
    assert result["notification_status"] in {"dry_run", "sent"}
    assert result["transaction_id"].startswith("T-")


def test_below_expectation_routes_to_negotiation_without_email(app):
    result = app.invoke(
        initial_state(
            submission(
                fish_type="Tuna",
                expected_price=900,
                hours_old=5,
                location="Kasimedu, Chennai",
            )
        )
    )

    assert result["decision"]["type"] == "negotiate"
    assert result["decision"]["negotiation_strategy"]
    assert result["notification_content"] == {}
    assert result["notification_status"] == "not_started"


def test_no_buyer_routes_to_best_alternate_market(app):
    result = app.invoke(
        initial_state(
            submission(
                fish_type="Rohu",
                expected_price=220,
                hours_old=8,
                location="Howrah, West Bengal",
            )
        )
    )

    assert result["decision"]["type"] == "alternate_market"
    assert result["selected_buyer"] is None
    assert result["selected_market"]["market_id"] == "MKT-009"


def test_invalid_submission_is_rejected_and_logged(app):
    result = app.invoke(initial_state({"fisher_name": ""}))

    assert result["agent_status"] == "completed"
    assert result["validation_errors"]
    assert "could not be processed" in result["final_response"]
    assert result["transaction_id"].startswith("T-")


def test_score_components_are_explainable(app):
    result = app.invoke(
        initial_state(
            submission(
                fish_type="Prawns",
                expected_price=550,
                hours_old=3,
                location="Mangaluru, Karnataka",
            )
        )
    )
    score = result["buyer_scores"][0]
    assert 0 <= score["score"] <= 100
    assert all(
        key in score
        for key in (
            "price_score",
            "distance_score",
            "demand_score",
            "capacity_score",
            "freshness_score",
            "reasoning",
            "expected_revenue",
        )
    )

