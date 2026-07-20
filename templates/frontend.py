"""Streamlit user experience for MatsyaLink AI — Ocean Intelligence Platform.

Design system: "Oceanic Futurism / Sonarpunk" — a maritime command-center
aesthetic (sonar sweeps, radar timelines, depth-gradient surfaces) built
entirely with native Streamlit components, custom CSS and Plotly.

Run from the repository root with: ``streamlit run templates/frontend.py``.
"""

from __future__ import annotations

import html
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings  # noqa: E402
from graph import build_graph  # noqa: E402
from state import initial_state  # noqa: E402
from tools import generate_analytics  # noqa: E402


st.set_page_config(page_title="MatsyaLink AI", page_icon="🐟", layout="wide")


# ─────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────
# Color: deep-ocean abyss background, layered surfaces, cyan "sonar ping"
# accent for primary signal, teal for confirmed/positive readings, coral
# for urgency/alerts — the one warm note in an otherwise cool system.
COLORS = {
    "abyss": "#050C14",     # page background — the deep, far from any light
    "deep": "#0A1B26",      # panel background
    "surface": "#0F2733",   # card surface
    "surface_hi": "#123544",  # elevated / hovered surface
    "line": "rgba(45, 212, 232, 0.18)",   # hairline borders
    "line_strong": "rgba(45, 212, 232, 0.4)",
    "cyan": "#2DD4E8",      # sonar ping — primary accent
    "teal": "#17B39A",      # signal teal — confirmed / positive
    "coral": "#FF7A5C",     # alert coral — urgency / attention
    "amber": "#F5B54C",     # caution
    "foam": "#E7F4F7",      # primary text
    "mist": "#7FA0AC",      # secondary / muted text
    "mist_dim": "#4E6773",  # tertiary text / captions
}

PLOTLY_FONT = "IBM Plex Mono, monospace"


def ocean_layout(fig: go.Figure, height: int = 360) -> go.Figure:
    """Apply the shared dark-ocean Plotly theme to any figure."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=PLOTLY_FONT, color=COLORS["mist"], size=12),
        title=dict(font=dict(family="Rajdhani, sans-serif", size=17, color=COLORS["foam"])),
        margin=dict(l=10, r=10, t=48, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["mist"])),
        colorway=[COLORS["cyan"], COLORS["teal"], COLORS["coral"], COLORS["amber"], "#5B8FA8"],
        hoverlabel=dict(bgcolor=COLORS["surface_hi"], font=dict(color=COLORS["foam"], family=PLOTLY_FONT)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=COLORS["line_strong"], color=COLORS["mist"])
    fig.update_yaxes(showgrid=True, gridcolor=COLORS["line"], zeroline=False, color=COLORS["mist"])
    return fig


# ─────────────────────────────────────────────────────────────────────────
# GLOBAL STYLE INJECTION
# ─────────────────────────────────────────────────────────────────────────
def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        /* ---- page canvas: deep ocean with faint depth rays ---- */
        .stApp {{
            background:
                radial-gradient(ellipse 90% 60% at 15% -10%, rgba(45,212,232,0.08), transparent 60%),
                radial-gradient(ellipse 70% 50% at 100% 0%, rgba(23,179,154,0.06), transparent 55%),
                {COLORS['abyss']};
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {COLORS['deep']} 0%, {COLORS['abyss']} 100%);
            border-right: 1px solid {COLORS['line']};
        }}
        header[data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
        #MainMenu, footer {{ visibility: hidden; }}

        h1, h2, h3 {{ font-family: 'Rajdhani', sans-serif; color: {COLORS['foam']}; letter-spacing: 0.02em; }}
        p, span, label, div {{ color: {COLORS['foam']}; }}

        /* ---- scrollbar ---- */
        ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
        ::-webkit-scrollbar-track {{ background: {COLORS['abyss']}; }}
        ::-webkit-scrollbar-thumb {{ background: {COLORS['line_strong']}; border-radius: 6px; }}

        /* ---- eyebrow / hero ---- */
        .ml-eyebrow {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 0.28em;
            text-transform: uppercase;
            color: {COLORS['cyan']};
            display: flex; align-items: center; gap: 8px;
            margin-bottom: 2px;
        }}
        .ml-eyebrow::before {{
            content: ''; width: 7px; height: 7px; border-radius: 50%;
            background: {COLORS['cyan']};
            box-shadow: 0 0 0 0 rgba(45,212,232,0.7);
            animation: ml-pulse 2.2s infinite;
        }}
        @keyframes ml-pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(45,212,232,0.55); }}
            70% {{ box-shadow: 0 0 0 9px rgba(45,212,232,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(45,212,232,0); }}
        }}
        .ml-title {{
            font-family: 'Rajdhani', sans-serif; font-weight: 700;
            font-size: 2.1rem; line-height: 1.1; color: {COLORS['foam']};
            margin: 2px 0 4px 0;
        }}
        .ml-subtitle {{ color: {COLORS['mist']}; font-size: 0.95rem; margin-bottom: 10px; }}
        .ml-divider {{
            height: 1px; margin: 6px 0 22px 0; border: none;
            background: linear-gradient(90deg, {COLORS['line_strong']}, transparent 75%);
        }}

        /* ---- card surfaces (bordered containers) ---- */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: linear-gradient(180deg, {COLORS['surface']} 0%, {COLORS['deep']} 100%) !important;
            border: 1px solid {COLORS['line']} !important;
            border-radius: 10px !important;
        }}

        .ml-card-header {{
            font-family: 'Rajdhani', sans-serif; font-weight: 600; font-size: 1.05rem;
            color: {COLORS['foam']}; display: flex; align-items: center; gap: 8px;
            margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid {COLORS['line']};
        }}

        /* ---- KPI metrics ---- */
        div[data-testid="stMetric"] {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['line']};
            border-radius: 10px;
            padding: 14px 16px;
        }}
        div[data-testid="stMetricLabel"] {{
            font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
            letter-spacing: 0.1em; text-transform: uppercase; color: {COLORS['mist']} !important;
        }}
        div[data-testid="stMetricValue"] {{ color: {COLORS['cyan']} !important; font-family: 'Rajdhani', sans-serif; }}

        /* ---- badges ---- */
        .ml-badge {{
            display: inline-flex; align-items: center; gap: 6px;
            font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
            letter-spacing: 0.06em; text-transform: uppercase;
            padding: 4px 10px; border-radius: 100px; border: 1px solid;
        }}
        .ml-badge-cyan {{ color: {COLORS['cyan']}; border-color: rgba(45,212,232,0.4); background: rgba(45,212,232,0.08); }}
        .ml-badge-teal {{ color: {COLORS['teal']}; border-color: rgba(23,179,154,0.45); background: rgba(23,179,154,0.1); }}
        .ml-badge-coral {{ color: {COLORS['coral']}; border-color: rgba(255,122,92,0.45); background: rgba(255,122,92,0.1); }}
        .ml-badge-amber {{ color: {COLORS['amber']}; border-color: rgba(245,181,76,0.45); background: rgba(245,181,76,0.1); }}
        .ml-badge-mist {{ color: {COLORS['mist']}; border-color: {COLORS['line']}; background: rgba(255,255,255,0.03); }}

        /* ---- score bars ---- */
        .ml-scorebar-track {{ background: rgba(255,255,255,0.06); border-radius: 100px; height: 7px; overflow: hidden; }}
        .ml-scorebar-fill {{ height: 100%; border-radius: 100px; background: linear-gradient(90deg, {COLORS['teal']}, {COLORS['cyan']}); }}

        /* ---- buttons ---- */
        div[data-testid="stButton"] button {{
            font-family: 'Rajdhani', sans-serif; font-weight: 700; letter-spacing: 0.06em;
            text-transform: uppercase; border-radius: 8px;
            border: 1px solid {COLORS['line_strong']};
            background: {COLORS['surface']}; color: {COLORS['foam']};
            transition: all 0.15s ease;
        }}
        div[data-testid="stButton"] button:hover {{
            border-color: {COLORS['cyan']}; color: {COLORS['cyan']};
            box-shadow: 0 0 16px rgba(45,212,232,0.25);
        }}
        div[data-testid="stButton"] button[kind="primary"] {{
            background: linear-gradient(90deg, {COLORS['teal']}, {COLORS['cyan']});
            color: {COLORS['abyss']}; border: none;
            box-shadow: 0 0 24px rgba(45,212,232,0.35);
        }}
        div[data-testid="stButton"] button[kind="primary"]:hover {{
            box-shadow: 0 0 34px rgba(45,212,232,0.55);
            color: {COLORS['abyss']};
        }}

        /* ---- inputs ---- */
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input,
        div[data-baseweb="select"] > div, div[data-testid="stDateInput"] input,
        div[data-testid="stTimeInput"] input {{
            background: {COLORS['deep']} !important; border: 1px solid {COLORS['line']} !important;
            color: {COLORS['foam']} !important; border-radius: 7px !important;
        }}

        /* ---- radio / nav ---- */
        div[role="radiogroup"] label {{
            font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;
        }}

        /* ---- terminal-style execution log ---- */
        .ml-terminal {{
            background: {COLORS['abyss']}; border: 1px solid {COLORS['line']}; border-radius: 8px;
            padding: 10px 14px; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;
            max-height: 260px; overflow-y: auto;
        }}
        .ml-terminal .row {{ color: {COLORS['mist']}; padding: 3px 0; border-bottom: 1px dashed rgba(255,255,255,0.05); }}
        .ml-terminal .row:last-child {{ color: {COLORS['cyan']}; }}
        .ml-terminal .ts {{ color: {COLORS['mist_dim']}; margin-right: 8px; }}

        /* ---- radar timeline ---- */
        .ml-timeline-wrap {{
            position: relative; background: {COLORS['deep']}; border: 1px solid {COLORS['line']};
            border-radius: 10px; padding: 22px 20px 14px 20px; overflow: hidden;
        }}
        .ml-timeline-wrap::before {{
            content: ''; position: absolute; inset: -50%;
            background: conic-gradient(from 0deg, transparent 0deg, rgba(45,212,232,0.10) 25deg, transparent 55deg);
            animation: ml-sweep 4.5s linear infinite;
        }}
        @keyframes ml-sweep {{ to {{ transform: rotate(360deg); }} }}
        .ml-timeline-row {{ position: relative; display: flex; align-items: center; z-index: 1; overflow-x: auto; padding-bottom: 6px; }}
        .ml-node {{ display: flex; flex-direction: column; align-items: center; min-width: 108px; flex-shrink: 0; }}
        .ml-node-dot {{ width: 16px; height: 16px; border-radius: 50%; margin-bottom: 8px; border: 2px solid {COLORS['line_strong']}; }}
        .ml-node-dot.done {{ background: {COLORS['teal']}; border-color: {COLORS['teal']}; }}
        .ml-node-dot.active {{ background: {COLORS['cyan']}; border-color: {COLORS['cyan']}; box-shadow: 0 0 0 5px rgba(45,212,232,0.22); animation: ml-pulse 1.4s infinite; }}
        .ml-node-dot.pending {{ background: transparent; }}
        .ml-node-label {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; text-align: center; color: {COLORS['mist']}; letter-spacing: 0.02em; }}
        .ml-node.active .ml-node-label {{ color: {COLORS['cyan']}; }}
        .ml-node.done .ml-node-label {{ color: {COLORS['teal']}; }}
        .ml-connector {{ flex: 1; height: 1px; background: {COLORS['line_strong']}; min-width: 24px; margin-bottom: 24px; }}
        .ml-connector.done {{ background: {COLORS['teal']}; }}

        /* ---- entity / recommendation cards ---- */
        .ml-hero-card {{
            background: linear-gradient(135deg, rgba(23,179,154,0.12), rgba(45,212,232,0.05));
            border: 1px solid {COLORS['line_strong']}; border-radius: 12px; padding: 18px 20px;
        }}
        .ml-kv-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 10px; }}
        .ml-kv {{ background: rgba(255,255,255,0.03); border: 1px solid {COLORS['line']}; border-radius: 8px; padding: 8px 10px; }}
        .ml-kv-label {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.07em; color: {COLORS['mist_dim']}; }}
        .ml-kv-value {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.95rem; color: {COLORS['foam']}; margin-top: 2px; }}

        .ml-rank-1 {{ color: {COLORS['amber']}; }}
        table.ml-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
        table.ml-table th {{
            font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; text-transform: uppercase;
            letter-spacing: 0.06em; color: {COLORS['mist']}; text-align: left; padding: 8px 10px;
            border-bottom: 1px solid {COLORS['line_strong']};
        }}
        table.ml-table td {{ padding: 9px 10px; border-bottom: 1px solid {COLORS['line']}; color: {COLORS['foam']}; vertical-align: middle; }}
        table.ml-table tr:hover td {{ background: rgba(45,212,232,0.04); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────
# REUSABLE COMPONENTS
# ─────────────────────────────────────────────────────────────────────────
def section_header(eyebrow: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="ml-eyebrow">{html.escape(eyebrow)}</div>
        <div class="ml-title">{html.escape(title)}</div>
        {f'<div class="ml-subtitle">{html.escape(subtitle)}</div>' if subtitle else ''}
        <hr class="ml-divider" />
        """,
        unsafe_allow_html=True,
    )


def card_header(icon: str, title: str) -> None:
    st.markdown(f'<div class="ml-card-header">{icon} {html.escape(title)}</div>', unsafe_allow_html=True)


def badge(text: str, tone: str = "cyan") -> str:
    return f'<span class="ml-badge ml-badge-{tone}">{html.escape(str(text))}</span>'


def _to_pct(value) -> float:
    """Best-effort normalisation of an unknown-scale score to 0-100."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    if -1.5 <= v <= 1.5:
        v *= 100
    return max(0.0, min(100.0, v))


def score_bar_html(value, width: int = 90) -> str:
    pct = _to_pct(value)
    return (
        f'<div style="width:{width}px" class="ml-scorebar-track">'
        f'<div class="ml-scorebar-fill" style="width:{pct:.0f}%"></div></div>'
        f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.68rem;color:{COLORS["mist"]};margin-top:2px;">{pct:.0f}%</div>'
    )


def tone_for_text(text: str) -> str:
    """Heuristic tone classification for freshness / urgency style strings."""
    t = (text or "").lower()
    if any(k in t for k in ["urgent", "critical", "sell now", "immediate", "spoil"]):
        return "coral"
    if any(k in t for k in ["fresh", "good", "excellent", "high", "low urgency", "standard"]):
        return "teal"
    if any(k in t for k in ["moderate", "fair", "medium", "watch"]):
        return "amber"
    return "cyan"


def status_card(icon: str, label: str, value: str) -> None:
    tone = tone_for_text(value)
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="ml-eyebrow" style="margin-bottom:8px;">{icon} {html.escape(label)}</div>
            <div style="font-family:'Rajdhani',sans-serif;font-weight:700;font-size:1.5rem;color:{COLORS['foam']};margin-bottom:8px;">
                {html.escape(str(value))}
            </div>
            {badge('TRACKED', tone)}
            """,
            unsafe_allow_html=True,
        )


def entity_card(title: str, icon: str, data: dict | None, empty_text: str) -> None:
    with st.container(border=True):
        card_header(icon, title)
        if not data:
            st.caption(empty_text)
            return
        preferred_order = [
            "name", "buyer_name", "market_name", "price", "price_per_kg",
            "distance_km", "capacity_kg", "demand_score", "reliability",
        ]
        keys = [k for k in preferred_order if k in data] + [k for k in data if k not in preferred_order]
        name_key = next((k for k in ("buyer_name", "market_name", "name") if k in data), None)
        if name_key:
            st.markdown(
                f'<div style="font-family:\'Rajdhani\',sans-serif;font-weight:700;font-size:1.3rem;color:{COLORS["cyan"]};">{html.escape(str(data[name_key]))}</div>',
                unsafe_allow_html=True,
            )
            keys = [k for k in keys if k != name_key]
        kv_html = []
        for k in keys:
            v = data[k]
            if isinstance(v, (dict, list)):
                continue
            label = k.replace("_", " ").title()
            kv_html.append(
                f'<div class="ml-kv"><div class="ml-kv-label">{html.escape(label)}</div>'
                f'<div class="ml-kv-value">{html.escape(str(v))}</div></div>'
            )
        st.markdown(f'<div class="ml-kv-grid">{"".join(kv_html)}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────
# GRAPH APP (cached)
# ─────────────────────────────────────────────────────────────────────────
@st.cache_resource
def graph_app():
    return build_graph(with_memory=True)


# ─────────────────────────────────────────────────────────────────────────
# PAGE: CATCH SUBMISSION — "Intake Mission Control"
# ─────────────────────────────────────────────────────────────────────────
def render_submission() -> None:
    section_header(
        "Live Intake · Sector Watch",
        "Catch Submission",
        "Log a catch for autonomous market and buyer matching.",
    )

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        with st.container(border=True):
            card_header("🧑‍🌾", "Fisher Profile")
            fisher_name = st.text_input("Fisher Name", value="Anita Naik")
            contact_number = st.text_input("Contact Number", value="+91-9876501001")
            location = st.text_input("Location", value="Margao, Goa")

        with st.container(border=True):
            card_header("📡", "Logistics Constraints")
            max_distance = st.number_input("Maximum Travel Distance (km)", min_value=1.0, value=40.0)
            catch_date = st.date_input("Catch Date", value=datetime.now().date())
            catch_time_value = st.time_input(
                "Catch Time", value=(datetime.now() - timedelta(hours=2)).time()
            )

    with col_b:
        with st.container(border=True):
            card_header("🐟", "Catch Information")
            fish_type = st.selectbox("Fish Type", ["Pomfret", "Mackerel", "Rohu", "Prawns", "Tuna"])
            quantity = st.number_input("Quantity (kg)", min_value=1.0, value=250.0)

        with st.container(border=True):
            card_header("💰", "Market Expectations")
            expected_price = st.number_input(
                "Expected Minimum Price (INR/kg)", min_value=0.0, value=280.0
            )

    # ---- live pre-submission intelligence preview ----
    catch_dt = datetime.combine(catch_date, catch_time_value)
    hours_elapsed = max(0.0, (datetime.now() - catch_dt).total_seconds() / 3600)
    if hours_elapsed < 3:
        freshness_preview, freshness_tone = "Excellent", "teal"
    elif hours_elapsed < 6:
        freshness_preview, freshness_tone = "Good", "cyan"
    elif hours_elapsed < 12:
        freshness_preview, freshness_tone = "Fair", "amber"
    else:
        freshness_preview, freshness_tone = "Degrading", "coral"

    if quantity < 100:
        volume_label = "Small Lot"
    elif quantity < 300:
        volume_label = "Moderate Lot"
    elif quantity < 600:
        volume_label = "Large Lot"
    else:
        volume_label = "Bulk Lot"

    projected_revenue = quantity * expected_price

    st.markdown('<div class="ml-eyebrow" style="margin-top:6px;">Pre-Submission Readout</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1:
        st.container(border=True).markdown(
            f'<div class="ml-card-header" style="border:none;margin:0;">🌡️ Estimated Freshness</div>'
            f'<div style="font-family:\'Rajdhani\',sans-serif;font-weight:700;font-size:1.35rem;">{freshness_preview}</div>'
            f'{badge(f"{hours_elapsed:.1f}h since catch", freshness_tone)}',
            unsafe_allow_html=True,
        )
    with p2:
        st.container(border=True).markdown(
            f'<div class="ml-card-header" style="border:none;margin:0;">⚖️ Volume Significance</div>'
            f'<div style="font-family:\'Rajdhani\',sans-serif;font-weight:700;font-size:1.35rem;">{volume_label}</div>'
            f'{badge(f"{quantity:.0f} kg", "cyan")}',
            unsafe_allow_html=True,
        )
    with p3:
        st.container(border=True).markdown(
            f'<div class="ml-card-header" style="border:none;margin:0;">📈 Projected Revenue</div>'
            f'<div style="font-family:\'Rajdhani\',sans-serif;font-weight:700;font-size:1.35rem;">₹{projected_revenue:,.0f}</div>'
            f'{badge("baseline, pre-match", "mist")}',
            unsafe_allow_html=True,
        )

    st.write("")
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        submitted = st.button("🚀  Run MatsyaLink Agent", use_container_width=True, type="primary")

    if not submitted:
        return

    raw = {
        "fisher_name": fisher_name,
        "contact_number": contact_number,
        "location": location,
        "fish_type": fish_type,
        "quantity_kg": quantity,
        "catch_time": catch_dt.replace(tzinfo=ZoneInfo(settings.timezone)).isoformat(),
        "expected_min_price_per_kg": expected_price,
        "max_travel_distance_km": max_distance,
    }
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    st.markdown('<div class="ml-eyebrow" style="margin-top:18px;">Live Execution</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ml-title" style="font-size:1.4rem;">LangGraph Agent Trace</div>',
        unsafe_allow_html=True,
    )
    timeline_slot = st.empty()
    log_slot = st.empty()

    completed_nodes: list[str] = []
    log_rows: list[str] = []

    def render_timeline(active: str | None) -> None:
        nodes_html = []
        seen = completed_nodes + ([active] if active and active not in completed_nodes else [])
        for i, node in enumerate(seen):
            state = "done" if node in completed_nodes and node != active else ("active" if node == active else "pending")
            nodes_html.append(
                f'<div class="ml-node {state}"><div class="ml-node-dot {state}"></div>'
                f'<div class="ml-node-label">{html.escape(node.replace("_", " ").title())}</div></div>'
            )
            if i < len(seen) - 1:
                nodes_html.append(f'<div class="ml-connector {"done" if state == "done" else ""}"></div>')
        timeline_slot.markdown(
            f'<div class="ml-timeline-wrap"><div class="ml-timeline-row">{"".join(nodes_html)}</div></div>',
            unsafe_allow_html=True,
        )

    def render_log() -> None:
        rows = "".join(
            f'<div class="row"><span class="ts">{datetime.now().strftime("%H:%M:%S")}</span>{html.escape(r)}</div>'
            for r in log_rows[-30:]
        )
        log_slot.markdown(f'<div class="ml-terminal">{rows}</div>', unsafe_allow_html=True)

    try:
        render_timeline(None)
        for update in graph_app().stream(
            initial_state(raw), config=config, stream_mode="updates"
        ):
            for node_name, values in update.items():
                message = values.get("execution_logs", [{}])[-1].get("message", "Completed")
                log_rows.append(f"{node_name.replace('_', ' ').title()} → {message}")
                render_log()
                render_timeline(node_name)
                completed_nodes.append(node_name)
        render_timeline(None)
        result = dict(graph_app().get_state(config).values)
        st.session_state["agent_result"] = result
        st.success(f"✅ {result['final_response']}")
    except Exception as exc:  # noqa: BLE001
        log_rows.append(f"ERROR → {exc}")
        render_log()
        st.error(f"The workflow could not complete: {exc}")


# ─────────────────────────────────────────────────────────────────────────
# PAGE: AGENT ANALYSIS — "AI Decision Center"
# ─────────────────────────────────────────────────────────────────────────
def render_analysis() -> None:
    section_header("AI Decision Center", "Agent Analysis", "How the agent read this catch, and why.")
    result = st.session_state.get("agent_result")
    if not result:
        st.info("Run a catch submission to view the agent trace.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        status_card("🌡️", "Freshness", result.get("freshness_status", "Not available"))
    with c2:
        status_card("🚨", "Urgency", result.get("urgency_level", "Not available"))
    with c3:
        with st.container(border=True):
            st.metric("Buyers Found", len(result.get("available_buyers", [])))
    with c4:
        with st.container(border=True):
            st.metric("Expected Revenue", f"₹{result.get('expected_revenue', 0):,.2f}")

    st.write("")
    with st.container(border=True):
        card_header("🧭", "AI Recommendation")
        st.markdown(
            f'<div class="ml-hero-card">{html.escape(result.get("decision", {}).get("explanation", "No decision available."))}</div>',
            unsafe_allow_html=True,
        )

    buyer_scores = result.get("buyer_scores")
    if buyer_scores:
        st.write("")
        with st.container(border=True):
            card_header("📊", "Explainable Buyer Ranking")
            df = pd.DataFrame(buyer_scores)
            rows = []
            for i, row in df.iterrows():
                rank_cls = "ml-rank-1" if i == 0 else ""
                rows.append(
                    "<tr>"
                    f'<td class="{rank_cls}">#{i + 1}</td>'
                    f'<td>{html.escape(str(row.get("buyer_name", "—")))}</td>'
                    f'<td>{score_bar_html(row.get("score", 0))}</td>'
                    f'<td>{score_bar_html(row.get("price_score", 0), 60)}</td>'
                    f'<td>{score_bar_html(row.get("distance_score", 0), 60)}</td>'
                    f'<td>{score_bar_html(row.get("demand_score", 0), 60)}</td>'
                    f'<td>{score_bar_html(row.get("capacity_score", 0), 60)}</td>'
                    f'<td>{score_bar_html(row.get("freshness_score", 0), 60)}</td>'
                    f'<td>₹{float(row.get("expected_revenue", 0)):,.0f}</td>'
                    "</tr>"
                )
            st.markdown(
                '<table class="ml-table"><thead><tr>'
                "<th>Rank</th><th>Buyer</th><th>Overall</th><th>Price</th><th>Distance</th>"
                "<th>Demand</th><th>Capacity</th><th>Freshness</th><th>Revenue</th>"
                f"</tr></thead><tbody>{''.join(rows)}</tbody></table>",
                unsafe_allow_html=True,
            )
            if "reasoning" in df.columns:
                for i, row in df.iterrows():
                    with st.expander(f"Why #{i + 1} · {row.get('buyer_name', 'Buyer')} was ranked here"):
                        st.write(row.get("reasoning", "No reasoning provided."))

    logs = result.get("execution_logs", [])
    if logs:
        st.write("")
        with st.container(border=True):
            card_header("🗒️", "Execution Log")
            log_df = pd.DataFrame(logs)
            st.dataframe(log_df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────
# PAGE: MARKET RECOMMENDATIONS — "Strategic Recommendation Engine"
# ─────────────────────────────────────────────────────────────────────────
def render_recommendations() -> None:
    section_header("Recommendation Engine", "Market Recommendations", "Where this catch should go, and the case for it.")
    result = st.session_state.get("agent_result")
    if not result:
        st.info("Run a catch submission to view recommendations.")
        return

    with st.container(border=True):
        card_header("🎯", result.get("proposal", {}).get("title", "Recommendation"))
        st.markdown(
            f'<div class="ml-hero-card">{html.escape(result.get("proposal", {}).get("summary", "No recommendation."))}</div>',
            unsafe_allow_html=True,
        )

    st.write("")
    r1, r2 = st.columns(2, gap="medium")
    with r1:
        entity_card("Selected Buyer", "🧑‍💼", result.get("selected_buyer"), "No buyer selected.")
    with r2:
        entity_card("Selected Market", "🏬", result.get("selected_market"), "No market selected.")

    markets = result.get("available_markets")
    if markets:
        st.write("")
        with st.container(border=True):
            card_header("🗺️", "Eligible Markets — Comparative Opportunities")
            mdf = pd.DataFrame(markets)
            cols = st.columns(min(3, len(mdf)) or 1)
            for i, (_, m) in enumerate(mdf.iterrows()):
                with cols[i % len(cols)]:
                    name = m.get("market_name") or m.get("name") or f"Market {i + 1}"
                    with st.container(border=True):
                        st.markdown(
                            f'<div style="font-family:\'Rajdhani\',sans-serif;font-weight:700;color:{COLORS["cyan"]};font-size:1.05rem;">{html.escape(str(name))}</div>',
                            unsafe_allow_html=True,
                        )
                        for key in ("distance_km", "capacity_kg", "demand_score", "price_per_kg"):
                            if key in m and pd.notna(m[key]):
                                label = key.replace("_", " ").title()
                                if "score" in key:
                                    st.caption(label)
                                    st.markdown(score_bar_html(m[key], 140), unsafe_allow_html=True)
                                else:
                                    st.caption(f"{label}: **{m[key]}**")

    if result.get("notification_content"):
        st.write("")
        with st.container(border=True):
            card_header("✉️", "Generated Buyer Communication")
            with st.expander("View message body"):
                st.text(result["notification_content"].get("body", ""))


# ─────────────────────────────────────────────────────────────────────────
# PAGE: ANALYTICS DASHBOARD — "Executive Command Center"
# ─────────────────────────────────────────────────────────────────────────
def _bar(data: dict, title: str, x_label: str, orientation: str = "h"):
    if not data:
        st.info(f"No {title.lower()} data yet.")
        return
    frame = pd.DataFrame({x_label: list(data), "Count": list(data.values())}).sort_values("Count")
    if orientation == "h":
        fig = px.bar(frame, y=x_label, x="Count", title=title, orientation="h", text="Count")
    else:
        fig = px.bar(frame, x=x_label, y="Count", title=title, text="Count")
    fig.update_traces(marker_color=COLORS["cyan"], textposition="outside", marker_line_width=0)
    st.plotly_chart(ocean_layout(fig, height=320), use_container_width=True)


def render_analytics() -> None:
    section_header("Executive Command Center", "Analytics Dashboard", "Fleet-wide performance, at a glance.")
    metrics = generate_analytics.invoke({})

    st.markdown('<div class="ml-eyebrow">Operational Overview</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Catches Processed", metrics["total_catches_processed"])
    c2.metric("Avg Revenue", f"₹{metrics['average_revenue']:,.0f}")
    c3.metric("Success Rate", f"{metrics['success_rate']:.1f}%")
    c4.metric("Negotiation Rate", f"{metrics['negotiation_rate']:.1f}%")
    c5.metric("No-Buyer Rate", f"{metrics['no_buyer_rate']:.1f}%")
    c6.metric("Total Expected Rev.", f"₹{metrics['total_expected_revenue']:,.0f}")

    st.write("")
    gcol, rcol = st.columns([1, 1.4], gap="medium")
    with gcol:
        with st.container(border=True):
            card_header("🎯", "Success Rate — Sonar Gauge")
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=metrics["success_rate"],
                    number={"suffix": "%", "font": {"color": COLORS["cyan"], "family": "Rajdhani, sans-serif"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": COLORS["mist"]},
                        "bar": {"color": COLORS["cyan"]},
                        "bgcolor": COLORS["deep"],
                        "borderwidth": 1,
                        "bordercolor": COLORS["line_strong"],
                        "steps": [
                            {"range": [0, 40], "color": "rgba(255,122,92,0.15)"},
                            {"range": [40, 70], "color": "rgba(245,181,76,0.15)"},
                            {"range": [70, 100], "color": "rgba(23,179,154,0.18)"},
                        ],
                    },
                )
            )
            st.plotly_chart(ocean_layout(fig, height=260), use_container_width=True)
    with rcol:
        with st.container(border=True):
            card_header("📡", "Outcome Distribution")
            categories = ["Direct Sale", "Negotiation", "No Buyer"]
            values = [metrics["success_rate"], metrics["negotiation_rate"], metrics["no_buyer_rate"]]
            fig = go.Figure(
                go.Scatterpolar(
                    r=values + values[:1],
                    theta=categories + categories[:1],
                    fill="toself",
                    line_color=COLORS["cyan"],
                    fillcolor="rgba(45,212,232,0.18)",
                )
            )
            fig.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor=COLORS["line"], color=COLORS["mist"]),
                    angularaxis=dict(gridcolor=COLORS["line"], color=COLORS["foam"]),
                ),
                showlegend=False,
            )
            st.plotly_chart(ocean_layout(fig, height=260), use_container_width=True)

    st.write("")
    st.markdown('<div class="ml-eyebrow">Market &amp; Buyer Activity</div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2, gap="medium")
    with m1:
        with st.container(border=True):
            card_header("🏬", "Market Utilization")
            _bar(metrics["market_utilization"], "Market Utilization", "Market")
    with m2:
        with st.container(border=True):
            card_header("🧑‍💼", "Buyer Utilization")
            _bar(metrics["buyer_utilization"], "Buyer Utilization", "Buyer")

    st.write("")
    st.markdown('<div class="ml-eyebrow">Fish Category Insights</div>', unsafe_allow_html=True)
    with st.container(border=True):
        card_header("🐟", "Most Requested Fish Types")
        fish_counts = metrics["fish_type_counts"]
        if fish_counts:
            frame = pd.DataFrame({"Fish Type": list(fish_counts), "Count": list(fish_counts.values())})
            fig = px.treemap(frame, path=["Fish Type"], values="Count", title="")
            fig.update_traces(
                marker=dict(colors=frame["Count"], colorscale=[[0, COLORS["surface_hi"]], [1, COLORS["cyan"]]]),
                textfont=dict(family="Rajdhani, sans-serif", size=15, color=COLORS["abyss"]),
            )
            st.plotly_chart(ocean_layout(fig, height=320), use_container_width=True)
        else:
            st.info("No fish type data yet.")

    st.write("")
    st.markdown('<div class="ml-eyebrow">System Health</div>', unsafe_allow_html=True)
    h1, h2 = st.columns(2)
    with h1:
        tone = "teal" if settings.cloud_sheets_ready else "amber"
        with st.container(border=True):
            card_header("🗄️", "Data Source")
            st.markdown(
                badge("Google Sheets" if settings.cloud_sheets_ready else "Local Demo CSV", tone),
                unsafe_allow_html=True,
            )
    with h2:
        tone = "teal" if settings.llm_ready else "amber"
        with st.container(border=True):
            card_header("🧠", "Reasoning Engine")
            st.markdown(
                badge("Gemma 4 31B Cloud" if settings.llm_ready else "Deterministic Demo Policy", tone),
                badge("Gemini" if settings.llm_ready else "Deterministic Demo Policy", tone),
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────────────
# APP SHELL
# ─────────────────────────────────────────────────────────────────────────
settings = get_settings()
inject_theme()

st.markdown(
    f"""
    <div class="ml-eyebrow">Ocean Intelligence Platform · SDG 14.b</div>
    <div class="ml-title" style="font-size:2.4rem;">🐟 MatsyaLink AI</div>
    <div class="ml-subtitle">Autonomous market access for small-scale artisanal fishers.</div>
    <hr class="ml-divider" />
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="ml-eyebrow">System Status</div>', unsafe_allow_html=True)
    st.markdown(
        f"{badge('Google Sheets' if settings.cloud_sheets_ready else 'Local Demo CSV', 'teal' if settings.cloud_sheets_ready else 'amber')}"
        f"&nbsp;&nbsp;{badge('Gemma 4 Cloud' if settings.llm_ready else 'Demo Policy', 'teal' if settings.llm_ready else 'amber')}",
        f"&nbsp;&nbsp;{badge('Gemini' if settings.llm_ready else 'Demo Policy', 'teal' if settings.llm_ready else 'amber')}",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown('<div class="ml-eyebrow">Command Deck</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigate",
        [
            "Catch Submission",
            "Agent Analysis",
            "Market Recommendations",
            "Analytics Dashboard",
        ],
        label_visibility="collapsed",
    )

{
    "Catch Submission": render_submission,
    "Agent Analysis": render_analysis,
    "Market Recommendations": render_recommendations,
    "Analytics Dashboard": render_analytics,
}[page]()
