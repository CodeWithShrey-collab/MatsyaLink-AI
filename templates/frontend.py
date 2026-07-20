"""Streamlit user experience for MatsyaLink AI.

Run from the repository root with: ``streamlit run templates/frontend.py``.
No custom CSS is used; presentation relies only on native Streamlit components.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings  # noqa: E402
from graph import build_graph  # noqa: E402
from state import initial_state  # noqa: E402
from tools import generate_analytics  # noqa: E402


st.set_page_config(page_title="MatsyaLink AI", page_icon="🐟", layout="wide")


@st.cache_resource
def graph_app():
    return build_graph(with_memory=True)


def render_submission() -> None:
    st.header("Catch Submission")
    st.caption("Submit a catch for autonomous market and buyer matching.")

    with st.form("catch_form"):
        left, right = st.columns(2)
        with left:
            fisher_name = st.text_input("Fisher Name", value="Anita Naik")
            contact_number = st.text_input("Contact Number", value="+91-9876501001")
            location = st.text_input("Location", value="Margao, Goa")
            fish_type = st.selectbox(
                "Fish Type", ["Pomfret", "Mackerel", "Rohu", "Prawns", "Tuna"]
            )
        with right:
            quantity = st.number_input("Quantity (kg)", min_value=1.0, value=250.0)
            catch_date = st.date_input("Catch Date", value=datetime.now().date())
            catch_time_value = st.time_input(
                "Catch Time", value=(datetime.now() - timedelta(hours=2)).time()
            )
            expected_price = st.number_input(
                "Expected Minimum Price (INR/kg)", min_value=0.0, value=280.0
            )
            max_distance = st.number_input(
                "Maximum Travel Distance (km)", min_value=1.0, value=40.0
            )
        submitted = st.form_submit_button("Run MatsyaLink Agent")

    if not submitted:
        return

    raw = {
        "fisher_name": fisher_name,
        "contact_number": contact_number,
        "location": location,
        "fish_type": fish_type,
        "quantity_kg": quantity,
        "catch_time": datetime.combine(catch_date, catch_time_value)
        .replace(tzinfo=ZoneInfo(settings.timezone))
        .isoformat(),
        "expected_min_price_per_kg": expected_price,
        "max_travel_distance_km": max_distance,
    }
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    progress = st.progress(0, text="Agent received the catch submission")
    trace = st.status("LangGraph execution", expanded=True)
    steps = 13
    completed = 0
    try:
        for update in graph_app().stream(
            initial_state(raw), config=config, stream_mode="updates"
        ):
            for node_name, values in update.items():
                completed += 1
                message = values.get("execution_logs", [{}])[-1].get(
                    "message", "Completed"
                )
                trace.write(f"{node_name.replace('_', ' ').title()}: {message}")
                progress.progress(
                    min(completed / steps, 1.0),
                    text=node_name.replace("_", " ").title(),
                )
        result = dict(graph_app().get_state(config).values)
        st.session_state["agent_result"] = result
        trace.update(label="LangGraph execution complete", state="complete")
        progress.progress(1.0, text="Completed")
        st.success(result["final_response"])
    except Exception as exc:
        trace.update(label="Execution stopped", state="error")
        st.error(f"The workflow could not complete: {exc}")


def render_analysis() -> None:
    st.header("Agent Analysis")
    result = st.session_state.get("agent_result")
    if not result:
        st.info("Run a catch submission to view the agent trace.")
        return
    a, b, c, d = st.columns(4)
    a.metric("Freshness", result.get("freshness_status", "Not available"))
    b.metric("Urgency", result.get("urgency_level", "Not available"))
    c.metric("Buyers Found", len(result.get("available_buyers", [])))
    d.metric("Expected Revenue", f"INR {result.get('expected_revenue', 0):,.2f}")
    st.subheader("Decision rationale")
    st.write(result.get("decision", {}).get("explanation", "No decision available."))
    if result.get("buyer_scores"):
        st.subheader("Explainable buyer ranking")
        columns = [
            "buyer_name",
            "score",
            "price_score",
            "distance_score",
            "demand_score",
            "capacity_score",
            "freshness_score",
            "expected_revenue",
            "reasoning",
        ]
        st.dataframe(pd.DataFrame(result["buyer_scores"])[columns], use_container_width=True)
    st.subheader("Execution log")
    st.dataframe(pd.DataFrame(result.get("execution_logs", [])), use_container_width=True)


def render_recommendations() -> None:
    st.header("Market Recommendations")
    result = st.session_state.get("agent_result")
    if not result:
        st.info("Run a catch submission to view recommendations.")
        return
    st.subheader(result.get("proposal", {}).get("title", "Recommendation"))
    st.write(result.get("proposal", {}).get("summary", "No recommendation."))
    if result.get("selected_buyer"):
        st.write("Selected buyer")
        st.json(result["selected_buyer"], expanded=False)
    if result.get("selected_market"):
        st.write("Selected market")
        st.json(result["selected_market"], expanded=False)
    if result.get("available_markets"):
        st.subheader("Eligible markets")
        st.dataframe(pd.DataFrame(result["available_markets"]), use_container_width=True)
    if result.get("notification_content"):
        with st.expander("Generated buyer email"):
            st.text(result["notification_content"].get("body", ""))


def _bar(data: dict, title: str, x_label: str):
    if not data:
        st.info(f"No {title.lower()} data yet.")
        return
    frame = pd.DataFrame({x_label: list(data), "Count": list(data.values())})
    st.plotly_chart(px.bar(frame, x=x_label, y="Count", title=title), use_container_width=True)


def render_analytics() -> None:
    st.header("Analytics Dashboard")
    metrics = generate_analytics.invoke({})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Catches Processed", metrics["total_catches_processed"])
    c2.metric("Average Revenue", f"INR {metrics['average_revenue']:,.2f}")
    c3.metric("Success Rate", f"{metrics['success_rate']:.1f}%")
    c4.metric("Negotiation Rate", f"{metrics['negotiation_rate']:.1f}%")
    c5, c6 = st.columns(2)
    c5.metric("No Buyer Rate", f"{metrics['no_buyer_rate']:.1f}%")
    c6.metric("Total Expected Revenue", f"INR {metrics['total_expected_revenue']:,.2f}")
    left, right = st.columns(2)
    with left:
        _bar(metrics["fish_type_counts"], "Most Requested Fish Types", "Fish Type")
        _bar(metrics["market_utilization"], "Market Utilization", "Market")
    with right:
        _bar(metrics["buyer_utilization"], "Buyer Utilization", "Buyer")
        rates = pd.DataFrame(
            {
                "Outcome": ["Direct Sale", "Negotiation", "No Buyer"],
                "Rate": [
                    metrics["success_rate"],
                    metrics["negotiation_rate"],
                    metrics["no_buyer_rate"],
                ],
            }
        )
        st.plotly_chart(
            px.pie(rates, names="Outcome", values="Rate", title="Outcome Rates"),
            use_container_width=True,
        )


settings = get_settings()
st.title("MatsyaLink AI")
st.caption("Autonomous market access for small-scale artisanal fishers · SDG 14.b")
with st.sidebar:
    st.write(f"Data: {'Google Sheets' if settings.cloud_sheets_ready else 'Local demo CSV'}")
    st.write(f"Reasoning: {'Gemini' if settings.llm_ready else 'Deterministic demo policy'}")
    page = st.radio(
        "Navigate",
        [
            "Catch Submission",
            "Agent Analysis",
            "Market Recommendations",
            "Analytics Dashboard",
        ],
    )

{
    "Catch Submission": render_submission,
    "Agent Analysis": render_analysis,
    "Market Recommendations": render_recommendations,
    "Analytics Dashboard": render_analytics,
}[page]()
