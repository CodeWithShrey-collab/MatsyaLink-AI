"""LangGraph topology and true conditional routing for MatsyaLink AI."""

from __future__ import annotations

from typing import Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from nodes import (
    buyer_retrieval_node,
    buyer_scoring_node,
    decision_node,
    freshness_analysis_node,
    market_retrieval_node,
    notification_node,
    persistence_node,
    proposal_generation_node,
    response_node,
    submission_validation_node,
    urgency_analysis_node,
)
from state import AgentState, initial_state


def route_after_validation(state: AgentState) -> Literal["freshness_analysis", "persistence"]:
    return "freshness_analysis" if state.get("validated_submission") else "persistence"


def route_after_decision(
    state: AgentState,
) -> Literal["direct_sale_proposal", "negotiation_proposal", "fallback_proposal"]:
    decision = state["decision"]["type"]
    return {
        "direct_sale": "direct_sale_proposal",
        "negotiate": "negotiation_proposal",
        "alternate_market": "fallback_proposal",
    }[decision]


def build_graph(*, with_memory: bool = True):
    builder = StateGraph(AgentState)

    builder.add_node("submission_validation", submission_validation_node)
    builder.add_node("freshness_analysis", freshness_analysis_node)
    builder.add_node("urgency_analysis", urgency_analysis_node)
    builder.add_node("market_retrieval", market_retrieval_node)
    builder.add_node("buyer_retrieval", buyer_retrieval_node)
    builder.add_node("buyer_scoring", buyer_scoring_node)
    # Keep executable node names distinct from AgentState channel names. Some
    # LangGraph releases reject a node/channel collision during construction.
    builder.add_node("decision_agent", decision_node)
    # One implementation, three explicit path nodes for a visible conditional trace.
    builder.add_node("direct_sale_proposal", proposal_generation_node)
    builder.add_node("negotiation_proposal", proposal_generation_node)
    builder.add_node("fallback_proposal", proposal_generation_node)
    builder.add_node("notification", notification_node)
    builder.add_node("persistence", persistence_node)
    builder.add_node("response", response_node)

    builder.add_edge(START, "submission_validation")
    builder.add_conditional_edges(
        "submission_validation",
        route_after_validation,
        {
            "freshness_analysis": "freshness_analysis",
            "persistence": "persistence",
        },
    )
    builder.add_edge("freshness_analysis", "urgency_analysis")
    builder.add_edge("urgency_analysis", "market_retrieval")
    builder.add_edge("market_retrieval", "buyer_retrieval")
    builder.add_edge("buyer_retrieval", "buyer_scoring")
    builder.add_edge("buyer_scoring", "decision_agent")
    builder.add_conditional_edges(
        "decision_agent",
        route_after_decision,
        {
            "direct_sale_proposal": "direct_sale_proposal",
            "negotiation_proposal": "negotiation_proposal",
            "fallback_proposal": "fallback_proposal",
        },
    )
    builder.add_edge("direct_sale_proposal", "notification")
    builder.add_edge("notification", "persistence")
    builder.add_edge("negotiation_proposal", "persistence")
    builder.add_edge("fallback_proposal", "persistence")
    builder.add_edge("persistence", "response")
    builder.add_edge("response", END)

    checkpointer = InMemorySaver() if with_memory else None
    return builder.compile(checkpointer=checkpointer)


def run_agent(raw_submission: dict, thread_id: str):
    app = build_graph(with_memory=True)
    return app.invoke(
        initial_state(raw_submission),
        config={"configurable": {"thread_id": thread_id}},
    )


if __name__ == "__main__":
    print(build_graph(with_memory=False).get_graph().draw_mermaid())
