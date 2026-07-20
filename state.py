"""Strongly typed, reducer-aware state for the LangGraph workflow."""

from __future__ import annotations

import operator
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict


class ExecutionLog(TypedDict, total=False):
    timestamp: str
    node: str
    status: str
    message: str
    details: dict[str, Any]


class AgentState(TypedDict, total=False):
    raw_submission: dict[str, Any]
    validated_submission: dict[str, Any] | None
    fish_type: str
    quantity: float
    freshness_status: str
    urgency_level: str
    available_markets: list[dict[str, Any]]
    available_buyers: list[dict[str, Any]]
    buyer_scores: list[dict[str, Any]]
    selected_buyer: dict[str, Any] | None
    selected_market: dict[str, Any] | None
    expected_revenue: float
    decision: dict[str, Any]
    notification_content: dict[str, Any]
    execution_logs: Annotated[list[ExecutionLog], operator.add]
    final_response: str
    agent_status: str

    # Supporting trace fields. Core fields above match the requested contract.
    proposal: dict[str, Any]
    notification_status: str
    transaction_id: str
    validation_errors: list[str]


def log_event(
    node: str,
    status: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> list[ExecutionLog]:
    return [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node": node,
            "status": status,
            "message": message,
            "details": details or {},
        }
    ]


def initial_state(raw_submission: dict[str, Any]) -> AgentState:
    """Return a fully initialized state so UI and tests can inspect every field."""

    return {
        "raw_submission": raw_submission,
        "validated_submission": None,
        "fish_type": "",
        "quantity": 0.0,
        "freshness_status": "",
        "urgency_level": "",
        "available_markets": [],
        "available_buyers": [],
        "buyer_scores": [],
        "selected_buyer": None,
        "selected_market": None,
        "expected_revenue": 0.0,
        "decision": {},
        "notification_content": {},
        "execution_logs": [],
        "final_response": "",
        "agent_status": "received",
        "proposal": {},
        "notification_status": "not_started",
        "transaction_id": "",
        "validation_errors": [],
    }
