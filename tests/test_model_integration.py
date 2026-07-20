from __future__ import annotations

import json
from types import SimpleNamespace

import ollama

import nodes
from models import DecisionType


VALID_DECISION = {
    "decision": "direct_sale",
    "selected_buyer_id": "BUY-001",
    "selected_market_id": "MKT-001",
    "explanation": "The retrieved buyer meets the fisher's minimum price.",
    "negotiation_strategy": None,
}


def test_gemma_response_parser_tolerates_fences_and_thinking_markers():
    raw = (
        "<|channel>thought\n<channel|>\n```json\n"
        + json.dumps(VALID_DECISION)
        + "\n```"
    )

    parsed = nodes._parse_decision_output(raw)

    assert parsed.decision == DecisionType.DIRECT_SALE
    assert parsed.selected_buyer_id == "BUY-001"


def test_gemma_client_uses_configured_ollama_cloud_model(monkeypatch):
    calls: dict = {}

    class FakeClient:
        def __init__(self, host=None, **kwargs):
            calls["host"] = host
            calls["headers"] = kwargs.get("headers")

        def chat(self, **kwargs):
            calls["chat"] = kwargs
            return SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(VALID_DECISION))
            )

    settings = SimpleNamespace(
        llm_ready=True,
        ollama_host="https://ollama.com",
        ollama_api_key="test-key",
        ollama_model="gemma4:31b-cloud",
    )
    monkeypatch.setattr(ollama, "Client", FakeClient)
    monkeypatch.setattr(nodes, "get_settings", lambda: settings)

    result = nodes._gemma_decision(
        {
            "validated_submission": {"fish_type": "Mackerel"},
            "freshness_status": "Fresh",
            "urgency_level": "Low",
            "available_markets": [{"market_id": "MKT-001"}],
            "available_buyers": [{"buyer_id": "BUY-001"}],
            "buyer_scores": [{"buyer_id": "BUY-001", "score": 92}],
        },
        DecisionType.DIRECT_SALE,
        {"buyer_id": "BUY-001"},
        {"market_id": "MKT-001"},
    )

    assert result is not None
    assert result.decision == DecisionType.DIRECT_SALE
    assert calls["host"] == "https://ollama.com"
    assert calls["headers"] == {"Authorization": "Bearer test-key"}
    assert calls["chat"]["model"] == "gemma4:31b-cloud"
    assert calls["chat"]["stream"] is False
    assert calls["chat"]["messages"][0]["role"] == "system"
    assert "DecisionOutput" in calls["chat"]["messages"][1]["content"]

