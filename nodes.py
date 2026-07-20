"""Dedicated LangGraph nodes for the complete MatsyaLink workflow."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from config import get_settings
from models import (
    Buyer,
    Catch,
    DecisionOutput,
    DecisionType,
    DemandLevel,
    Fisher,
    FreshnessStatus,
    Market,
    Transaction,
    UrgencyLevel,
)
from prompts import (
    DECISION_PROMPT,
    EMAIL_BODY_TEMPLATE,
    EMAIL_SUBJECT_TEMPLATE,
    SYSTEM_PROMPT,
)
from state import AgentState, log_event
from tools import (
    calculate_buyer_score,
    get_available_buyers,
    get_market_prices,
    save_transaction,
    send_buyer_notification,
)


def _first(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return default


def submission_validation_node(state: AgentState) -> dict[str, Any]:
    """Validate aliases, normalize types, and produce one canonical Catch payload."""

    raw = state.get("raw_submission", {})
    try:
        fisher = Fisher(
            name=_first(raw, "fisher_name", "Fisher Name", "name"),
            contact_number=str(
                _first(raw, "contact_number", "Contact Number", "contact")
            ),
            location=_first(raw, "location", "Location"),
        )
        catch = Catch(
            fisher=fisher,
            fish_type=_first(raw, "fish_type", "Fish Type"),
            quantity_kg=_first(raw, "quantity_kg", "quantity", "Quantity"),
            catch_time=_first(raw, "catch_time", "Catch Time"),
            expected_min_price_per_kg=_first(
                raw,
                "expected_min_price_per_kg",
                "expected_min_price",
                "Expected Minimum Price",
            ),
            preferred_market=_first(raw, "preferred_market", "Preferred Market"),
            logistics_required=_first(raw, "logistics_required", "Logistics Required"),
            max_travel_distance_km=_first(
                raw,
                "max_travel_distance_km",
                "max_travel_distance",
                "Maximum Travel Distance",
            ),
        )
        normalized = catch.model_dump(mode="json")
        return {
            "validated_submission": normalized,
            "fish_type": catch.fish_type,
            "quantity": catch.quantity_kg,
            "validation_errors": [],
            "agent_status": "validated",
            "execution_logs": log_event(
                "submission_validation",
                "completed",
                "Submission validated and normalized.",
                {"catch_id": catch.catch_id},
            ),
        }
    except (ValidationError, TypeError, ValueError) as exc:
        if isinstance(exc, ValidationError):
            errors = [
                f"{'.'.join(map(str, item['loc']))}: {item['msg']}"
                for item in exc.errors()
            ]
        else:
            errors = [str(exc)]
        return {
            "validated_submission": None,
            "validation_errors": errors,
            "agent_status": "validation_failed",
            "execution_logs": log_event(
                "submission_validation",
                "failed",
                "Submission failed validation.",
                {"errors": errors},
            ),
        }


def freshness_analysis_node(state: AgentState) -> dict[str, Any]:
    catch = Catch.model_validate(state["validated_submission"])
    settings = get_settings()
    now = datetime.now(ZoneInfo(settings.timezone))
    caught = catch.catch_time.astimezone(ZoneInfo(settings.timezone))
    age_hours = max(0.0, (now - caught).total_seconds() / 3600)
    if age_hours <= 6:
        freshness = FreshnessStatus.FRESH
    elif age_hours <= 12:
        freshness = FreshnessStatus.MODERATE
    else:
        freshness = FreshnessStatus.LOW
    return {
        "freshness_status": freshness.value,
        "agent_status": "freshness_analyzed",
        "execution_logs": log_event(
            "freshness_analysis",
            "completed",
            f"Catch classified as {freshness.value}.",
            {"age_hours": round(age_hours, 2)},
        ),
    }


def urgency_analysis_node(state: AgentState) -> dict[str, Any]:
    freshness = FreshnessStatus(state["freshness_status"])
    quantity = float(state["quantity"])
    if freshness == FreshnessStatus.LOW or quantity >= 750:
        urgency = UrgencyLevel.HIGH
    elif freshness == FreshnessStatus.MODERATE or quantity >= 300:
        urgency = UrgencyLevel.MEDIUM
    else:
        urgency = UrgencyLevel.LOW
    return {
        "urgency_level": urgency.value,
        "agent_status": "urgency_analyzed",
        "execution_logs": log_event(
            "urgency_analysis",
            "completed",
            f"Selling urgency classified as {urgency.value}.",
            {"freshness": freshness.value, "quantity_kg": quantity},
        ),
    }


def market_retrieval_node(state: AgentState) -> dict[str, Any]:
    catch = Catch.model_validate(state["validated_submission"])
    records = get_market_prices.invoke({"fish_type": catch.fish_type})
    eligible = [
        record
        for record in records
        if float(record["distance_km"]) <= catch.max_travel_distance_km
    ]
    return {
        "available_markets": eligible,
        "agent_status": "markets_retrieved",
        "execution_logs": log_event(
            "market_retrieval",
            "completed",
            f"Retrieved {len(eligible)} eligible market record(s).",
            {"tool": "get_market_prices", "retrieved": len(records)},
        ),
    }


def buyer_retrieval_node(state: AgentState) -> dict[str, Any]:
    catch = Catch.model_validate(state["validated_submission"])
    records = get_available_buyers.invoke({"fish_type": catch.fish_type})
    eligible = [
        record
        for record in records
        if float(record["distance_km"]) <= catch.max_travel_distance_km
        and float(record["capacity_kg"]) > 0
    ]
    return {
        "available_buyers": eligible,
        "agent_status": "buyers_retrieved",
        "execution_logs": log_event(
            "buyer_retrieval",
            "completed",
            f"Retrieved {len(eligible)} eligible buyer record(s).",
            {"tool": "get_available_buyers", "retrieved": len(records)},
        ),
    }


def buyer_scoring_node(state: AgentState) -> dict[str, Any]:
    catch = Catch.model_validate(state["validated_submission"])
    markets = [Market.model_validate(item) for item in state["available_markets"]]
    market_reference = (
        sum(m.current_price_per_kg for m in markets) / len(markets)
        if markets
        else catch.expected_min_price_per_kg
    )
    scores = [
        calculate_buyer_score.invoke(
            {
                "buyer": buyer,
                "quantity_kg": catch.quantity_kg,
                "max_travel_distance_km": catch.max_travel_distance_km,
                "freshness_status": state["freshness_status"],
                "market_reference_price": market_reference,
            }
        )
        for buyer in state["available_buyers"]
    ]
    scores.sort(key=lambda item: (-float(item["score"]), item["buyer_name"]))
    return {
        "buyer_scores": scores,
        "agent_status": "buyers_scored",
        "execution_logs": log_event(
            "buyer_scoring",
            "completed",
            f"Ranked {len(scores)} buyer(s) with the weighted scoring model.",
            {
                "market_reference_price": round(market_reference, 2),
                "tool": "calculate_buyer_score",
                "tool_calls": len(scores),
            },
        ),
    }


def _best_market(markets: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not markets:
        return None
    demand = {DemandLevel.HIGH.value: 3, DemandLevel.MEDIUM.value: 2, DemandLevel.LOW.value: 1}
    return sorted(
        markets,
        key=lambda item: (
            -float(item["current_price_per_kg"]),
            -demand.get(str(item["current_demand"]), 0),
            float(item["distance_km"]),
        ),
    )[0]


def _policy_decision(state: AgentState) -> tuple[DecisionType, dict[str, Any] | None]:
    # A numerically high score cannot override complete freshness incompatibility.
    score = next(
        (
            item
            for item in state["buyer_scores"]
            if float(item["freshness_score"]) > 0
        ),
        None,
    )
    if score is None:
        return DecisionType.ALTERNATE_MARKET, None
    buyer = next(
        item
        for item in state["available_buyers"]
        if item["buyer_id"] == score["buyer_id"]
    )
    catch = Catch.model_validate(state["validated_submission"])
    if float(buyer["price_offered_per_kg"]) >= catch.expected_min_price_per_kg:
        return DecisionType.DIRECT_SALE, buyer
    return DecisionType.NEGOTIATE, buyer


def _parse_decision_output(raw_content: str) -> DecisionOutput:
    """Extract and validate one JSON object from an Ollama Cloud response.

    Ollama Cloud does not currently enforce the ``format`` schema for cloud
    models. Gemma therefore receives the schema in the prompt, and this parser
    treats every model response as untrusted until Pydantic validation succeeds.
    It also tolerates Markdown fences or empty thinking-channel markers.
    """

    content = raw_content.strip()
    try:
        return DecisionOutput.model_validate_json(content)
    except (ValueError, TypeError):
        pass

    decoder = json.JSONDecoder()
    for index, character in enumerate(content):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(content[index:])
            return DecisionOutput.model_validate(candidate)
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    raise ValueError("Gemma 4 response did not contain a valid DecisionOutput object.")


def _gemma_decision(
    state: AgentState,
    allowed: DecisionType,
    preferred_buyer: dict[str, Any] | None,
    preferred_market: dict[str, Any] | None,
) -> DecisionOutput | None:
    settings = get_settings()
    if not settings.llm_ready:
        return None
    from ollama import Client

    prompt = DECISION_PROMPT.format(
        catch_json=json.dumps(state["validated_submission"], indent=2),
        freshness=state["freshness_status"],
        urgency=state["urgency_level"],
        markets_json=json.dumps(state["available_markets"], indent=2),
        buyers_json=json.dumps(state["available_buyers"], indent=2),
        scores_json=json.dumps(state["buyer_scores"], indent=2),
        allowed_decision=allowed.value,
        preferred_buyer_id=(preferred_buyer or {}).get("buyer_id"),
        preferred_market_id=(preferred_market or {}).get("market_id"),
    )
    schema = json.dumps(DecisionOutput.model_json_schema(), ensure_ascii=False)
    output_contract = (
        "Return exactly one JSON object and no Markdown. The JSON must validate "
        f"against this schema: {schema}"
    )
    headers = (
        {"Authorization": f"Bearer {settings.ollama_api_key}"}
        if settings.ollama_api_key
        else None
    )
    client = Client(host=settings.ollama_host, headers=headers)
    response = client.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{prompt}\n\n{output_contract}"},
        ],
        stream=False,
        options={"temperature": 0},
    )
    content = getattr(response.message, "content", "")
    return _parse_decision_output(content)


def decision_node(state: AgentState) -> dict[str, Any]:
    allowed, buyer = _policy_decision(state)
    market = _best_market(state["available_markets"])
    catch = Catch.model_validate(state["validated_submission"])
    score = (
        next(
            item
            for item in state["buyer_scores"]
            if buyer and item["buyer_id"] == buyer["buyer_id"]
        )
        if buyer
        else None
    )

    if allowed == DecisionType.DIRECT_SALE:
        explanation = (
            f"{buyer['buyer_name']} ranks first at {score['score']:.2f}/100 and offers "
            f"INR {float(buyer['price_offered_per_kg']):.2f}/kg, meeting the fisher's "
            f"INR {catch.expected_min_price_per_kg:.2f}/kg minimum. {score['reasoning']}"
        )
        strategy = None
    elif allowed == DecisionType.NEGOTIATE:
        gap = catch.expected_min_price_per_kg - float(buyer["price_offered_per_kg"])
        explanation = (
            f"The best retrieved buyer is {buyer['buyer_name']} at {score['score']:.2f}/100, "
            f"but its offer is INR {gap:.2f}/kg below the fisher's minimum."
        )
        strategy = (
            f"Open at INR {catch.expected_min_price_per_kg:.2f}/kg, cite the "
            f"{state['freshness_status'].lower()} catch and current market benchmark, and "
            "offer a small volume discount only if the buyer confirms full pickup."
        )
    else:
        explanation = (
            "No eligible buyer was returned for this fish type, travel radius, and active "
            "demand. The best retrieved market is used as the fallback."
            if market
            else "No eligible buyer or market was returned from the stored records."
        )
        strategy = None

    llm_used = False
    try:
        llm_result = _gemma_decision(state, allowed, buyer, market)
        if llm_result:
            buyer_ids = {item["buyer_id"] for item in state["available_buyers"]}
            market_ids = {item["market_id"] for item in state["available_markets"]}
            ids_valid = (
                (llm_result.selected_buyer_id is None or llm_result.selected_buyer_id in buyer_ids)
                and (llm_result.selected_market_id is None or llm_result.selected_market_id in market_ids)
            )
            if llm_result.decision == allowed and ids_valid:
                explanation = llm_result.explanation
                strategy = llm_result.negotiation_strategy or strategy
                llm_used = True
    except Exception as exc:  # Cloud reasoning must never break the sale workflow.
        llm_error = type(exc).__name__
    else:
        llm_error = None

    expected_revenue = (
        float(score["expected_revenue"])
        if score
        else (
            catch.quantity_kg * float(market["current_price_per_kg"])
            if market
            else 0.0
        )
    )
    decision = {
        "type": allowed.value,
        "explanation": explanation,
        "negotiation_strategy": strategy,
        "reasoning_source": "gemma4_guardrailed" if llm_used else "deterministic_policy",
    }
    settings = get_settings()
    details = {
        "llm_used": llm_used,
        "model_provider": "ollama",
        "model": settings.ollama_model,
    }
    if llm_error:
        details["llm_fallback_reason"] = llm_error
    return {
        "selected_buyer": buyer,
        "selected_market": market,
        "expected_revenue": round(expected_revenue, 2),
        "decision": decision,
        "agent_status": "decision_made",
        "execution_logs": log_event(
            "decision_agent",
            "completed",
            f"Decision: {allowed.value}.",
            details,
        ),
    }


def proposal_generation_node(state: AgentState) -> dict[str, Any]:
    catch = Catch.model_validate(state["validated_submission"])
    decision = DecisionType(state["decision"]["type"])
    notification: dict[str, Any] = {}

    if decision == DecisionType.DIRECT_SALE:
        buyer = Buyer.model_validate(state["selected_buyer"])
        subject = EMAIL_SUBJECT_TEMPLATE.format(
            quantity=catch.quantity_kg, fish_type=catch.fish_type
        )
        body = EMAIL_BODY_TEMPLATE.format(
            buyer_name=buyer.buyer_name,
            fish_type=catch.fish_type,
            quantity=catch.quantity_kg,
            location=catch.fisher.location,
            expected_price=catch.expected_min_price_per_kg,
            offered_price=buyer.price_offered_per_kg,
            freshness=state["freshness_status"],
            revenue=state["expected_revenue"],
        )
        notification = {
            "recipient": str(buyer.contact_email),
            "subject": subject,
            "body": body,
        }
        proposal = {
            "title": "Direct sale proposal",
            "summary": f"Offer {catch.quantity_kg:.1f} kg to {buyer.buyer_name}.",
            "price_per_kg": buyer.price_offered_per_kg,
            "expected_revenue": state["expected_revenue"],
        }
    elif decision == DecisionType.NEGOTIATE:
        buyer = Buyer.model_validate(state["selected_buyer"])
        proposal = {
            "title": "Negotiation proposal",
            "summary": f"Negotiate with {buyer.buyer_name} before confirming the sale.",
            "listed_offer_per_kg": buyer.price_offered_per_kg,
            "target_price_per_kg": catch.expected_min_price_per_kg,
            "strategy": state["decision"].get("negotiation_strategy"),
        }
    else:
        market = state.get("selected_market")
        proposal = {
            "title": "Alternate market recommendation",
            "summary": (
                f"Take the catch to {market['market_name']}."
                if market
                else "Hold the catch safely and contact the local cooperative."
            ),
            "market": market,
        }
    proposal_node = {
        DecisionType.DIRECT_SALE: "direct_sale_proposal",
        DecisionType.NEGOTIATE: "negotiation_proposal",
        DecisionType.ALTERNATE_MARKET: "fallback_proposal",
    }[decision]
    return {
        "proposal": proposal,
        "notification_content": notification,
        "agent_status": "proposal_generated",
        "execution_logs": log_event(
            proposal_node,
            "completed",
            proposal["title"],
        ),
    }


def notification_node(state: AgentState) -> dict[str, Any]:
    content = state["notification_content"]
    try:
        result = send_buyer_notification.invoke(content)
        status = str(result["status"])
        log_status = "completed"
        message = f"Buyer notification status: {status}."
    except Exception as exc:
        status = "failed"
        log_status = "failed"
        message = f"Buyer notification failed: {type(exc).__name__}."
    return {
        "notification_status": status,
        "agent_status": "notification_processed",
        "execution_logs": log_event(
            "notification",
            log_status,
            message,
            {
                "recipient": content.get("recipient"),
                "tool": "send_buyer_notification",
            },
        ),
    }


def persistence_node(state: AgentState) -> dict[str, Any]:
    is_valid = bool(state.get("validated_submission"))
    decision_type = (
        DecisionType(state["decision"]["type"])
        if state.get("decision")
        else DecisionType.REJECTED
    )
    submission = state.get("validated_submission") or state.get("raw_submission", {})
    transaction = Transaction(
        submission=submission,
        decision=decision_type,
        selected_buyer=(state.get("selected_buyer") or {}).get("buyer_name"),
        selected_market=(state.get("selected_market") or {}).get("market_name"),
        fish_type=state.get("fish_type") or str(submission.get("fish_type", "Unknown")),
        quantity_kg=state.get("quantity", 0.0),
        expected_revenue=state.get("expected_revenue", 0.0),
        outcome=(
            "validation_failed" if not is_valid else decision_type.value
        ),
        notification_status=state.get("notification_status", "not_applicable"),
        execution_log=state.get("execution_logs", []),
    )
    try:
        result = save_transaction.invoke(
            {"transaction": transaction.model_dump(mode="json")}
        )
        return {
            "transaction_id": result["transaction_id"],
            "agent_status": "stored",
            "execution_logs": log_event(
                "persistence",
                "completed",
                "Execution stored in the transaction ledger.",
                {
                    "transaction_id": result["transaction_id"],
                    "tool": "save_transaction",
                },
            ),
        }
    except Exception as exc:
        return {
            "transaction_id": transaction.transaction_id,
            "agent_status": "storage_failed",
            "execution_logs": log_event(
                "persistence",
                "failed",
                f"Storage failed: {type(exc).__name__}.",
            ),
        }


def response_node(state: AgentState) -> dict[str, Any]:
    if state.get("validation_errors"):
        lines = "\n".join(f"- {item}" for item in state["validation_errors"])
        response = f"Submission could not be processed:\n{lines}"
    else:
        decision = state["decision"]
        response = (
            f"Decision: {decision['type'].replace('_', ' ').title()}\n\n"
            f"{decision['explanation']}\n\n"
            f"Expected revenue: INR {state['expected_revenue']:,.2f}\n\n"
            f"Recommended action: {state['proposal']['summary']}\n\n"
            f"Trace ID: {state.get('transaction_id', 'not stored')}"
        )
    return {
        "final_response": response,
        "agent_status": "completed",
        "execution_logs": log_event(
            "response", "completed", "Final fisher response generated."
        ),
    }
