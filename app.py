"""
app.py — Supply Chain Resilience Dashboard
Rotman MBA 2027 · GenAI Applications in Business

Three modes:
  BASELINE   — factory cards, production flow, order tracker
  DISRUPTION — F2 failure triggered, affected orders flagged, backup math shown
  RESPONSE   — 4 agent output tabs, option selector, executive brief

Run:  streamlit run app.py
Env:  ANTHROPIC_API_KEY must be set in environment or .env file
"""

import streamlit as st
import re
from factory_network_data import (
    get_factories, get_process_flow, get_product_economics,
    get_active_orders, get_disruption_scenarios, get_scenario,
    get_network_summary, get_orders_by_category, get_affected_orders,
)
from agents import run_agent_1, run_agent_2, run_agent_3, run_agent_4

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Supply Chain Resilience Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load data ─────────────────────────────────────────────────────────────────
FACTORIES        = get_factories()
PROCESS_FLOW     = get_process_flow()
PRODUCT_ECON     = get_product_economics()
ACTIVE_ORDERS    = get_active_orders()
SCENARIOS        = get_disruption_scenarios()
SUMMARY          = get_network_summary()
SCENARIO_01      = get_scenario("DISRUPT-01")

# ── Session state ─────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "mode": "baseline",          # baseline | disruption | response
        "agent_1_output": None,
        "agent_2_output": None,
        "agent_3_output": None,
        "agent_4_output": None,
        "selected_option": None,     # "A" | "B" | "C"
        "pipeline_running": False,
        "pipeline_stage": 0,         # 0=idle, 1-4=running agent N
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ── Visual constants ──────────────────────────────────────────────────────────
STAGE_BG = {
    "S1": "#e1f5ee", "S2": "#9fe1cb",
    "S3": "#faeeda", "S4": "#f5c97a",
    "S5": "#eeedfe", "S6": "#c9c5f2", "S7": "#a8a3e8",
}
FACTORY_ACCENT = {"F1": "#1d9e75", "F2": "#ba7517", "F3": "#534ab7", "F4": "#993c1d"}

def util_color(u):
    return "#e24b4a" if u >= 0.85 else "#ef9f27" if u >= 0.75 else "#1d9e75"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#fafaf8}
[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1.25rem;padding-bottom:2rem;max-width:1440px}
.dash-label{font-size:10px;font-family:monospace;letter-spacing:.1em;text-transform:uppercase;color:#888780;margin:0 0 5px}
.dash-title{font-size:22px;font-weight:600;color:#1a1a18;margin:0 0 3px}
.dash-sub{font-size:13px;color:#73726c;margin:0}
.sec-label{font-size:10px;font-weight:600;color:#888780;letter-spacing:.1em;text-transform:uppercase;padding-bottom:6px;border-bottom:1px solid #e8e6e0;margin-bottom:10px}
.kpi-card{background:white;border:1px solid #e8e6e0;border-radius:10px;padding:12px 16px;text-align:center}
.kpi-val{font-size:20px;font-weight:600;color:#1a1a18;display:block;line-height:1.1}
.kpi-lbl{font-size:10px;color:#888780;margin-top:3px;letter-spacing:.05em;text-transform:uppercase}
.kpi-card-danger{background:#fcebeb;border-color:#f09595}
.kpi-val-danger{font-size:20px;font-weight:600;color:#a32d2d;display:block;line-height:1.1}
.kpi-lbl-danger{font-size:10px;color:#a32d2d;opacity:.7;margin-top:3px;letter-spacing:.05em;text-transform:uppercase}
.factory-card{background:white;border:1px solid #e8e6e0;border-radius:12px;padding:16px;height:100%}
.factory-card-danger{background:#fcebeb;border:2px solid #e24b4a;border-radius:12px;padding:16px;height:100%}
.fid-badge{font-size:11px;font-weight:700;padding:2px 8px;border-radius:4px;display:inline-block;margin-bottom:6px}
.factory-name{font-size:15px;font-weight:600;color:#1a1a18;margin:0 0 2px}
.factory-owner{font-size:12px;color:#888780;margin:0 0 8px}
.factory-role{font-size:11px;color:#5f5e5a;margin:0 0 10px;line-height:1.4}
.util-bar-bg{height:5px;background:#f1efe8;border-radius:3px;overflow:hidden;flex:1}
.stage-pill{font-size:11px;font-weight:600;padding:3px 8px;border-radius:4px;display:inline-block;margin:2px 2px 2px 0}
.bottleneck-tag{font-size:10px;font-weight:700;color:#854f0b;background:#faeeda;padding:2px 7px;border-radius:4px;display:inline-block;margin-bottom:5px}
.govspec-tag{font-size:10px;font-weight:700;color:#3c3489;background:#eeedfe;padding:2px 7px;border-radius:4px;display:inline-block;margin-bottom:5px}
.offline-tag{font-size:10px;font-weight:700;color:#a32d2d;background:#fcebeb;padding:2px 7px;border-radius:4px;display:inline-block;margin-bottom:5px}
.flow-bar{background:white;border:1px solid #e8e6e0;border-radius:10px;padding:12px 16px;display:flex;align-items:center;margin-bottom:1.25rem;overflow-x:auto}
.flow-stage{text-align:center;padding:6px 8px;border-radius:6px;font-size:11px;font-weight:600;white-space:nowrap;min-width:60px}
.flow-arrow{color:#b4b2a9;font-size:14px;padding:0 4px;flex-shrink:0}
.flow-label{font-size:9px;font-weight:400;margin-top:2px}
.disruption-banner{background:#fcebeb;border:1px solid #f09595;border-radius:10px;padding:14px 18px;margin-bottom:1rem}
.disruption-title{font-size:15px;font-weight:600;color:#a32d2d;margin:0 0 4px}
.disruption-body{font-size:12px;color:#791f1f;margin:0;line-height:1.6}
.backup-card{background:#e1f5ee;border:1px solid #5dcaa5;border-radius:10px;padding:14px 18px;margin-bottom:1rem}
.backup-title{font-size:13px;font-weight:600;color:#085041;margin:0 0 6px}
.backup-body{font-size:12px;color:#0f6e56;margin:0;line-height:1.6}
.order-row-affected{background:#fff9f0}
.order-row-blocked{background:#fff5f5}
.order-row-safe{background:#f6fdf9}
.col-header{font-size:10px;font-weight:600;color:#888780;text-transform:uppercase;letter-spacing:.07em;padding-bottom:5px;border-bottom:1px solid #e8e6e0}
.cell{font-size:13px;color:#1a1a18;padding:7px 0}
.cell-sub{font-size:11px;color:#888780}
.penalty-badge{background:#fcebeb;color:#a32d2d;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600}
.agent-output{background:white;border:1px solid #e8e6e0;border-radius:10px;padding:18px;font-family:monospace;font-size:12px;white-space:pre-wrap;line-height:1.6;max-height:600px;overflow-y:auto;color:#2c2c2a}
.option-btn-selected{background:#e1f5ee;border:2px solid #1d9e75;border-radius:8px;padding:12px 16px;cursor:pointer;text-align:center}
.option-btn{background:white;border:1px solid #e8e6e0;border-radius:8px;padding:12px 16px;cursor:pointer;text-align:center}
.divider{border:none;border-top:1px solid #e8e6e0;margin:1rem 0}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_cad(n):
    return f"CAD {n:,.0f}"

def mode_is(m):
    return st.session_state["mode"] == m

def set_mode(m):
    st.session_state["mode"] = m

def stage_badge_html(stage, disruption_active=False):
    if disruption_active and stage in ("S3", "S4"):
        return f'<span class="stage-pill" style="background:#fcebeb;color:#a32d2d;">{stage}</span>'
    bg = STAGE_BG.get(stage, "#f1efe8")
    return f'<span class="stage-pill" style="background:{bg}">{stage}</span>'

def delay_for_order(order, disruption_days=5):
    """Quick delay estimate for disruption mode display."""
    cat = order["disruption_category"]
    if cat == "SAFE_PAST_F2":
        return 0
    if cat == "BLOCKED_AT_F2":
        return disruption_days
    # QUEUED_AT_F1 — add 0.5d per queue position (simplified)
    queued_orders = get_orders_by_category("QUEUED_AT_F1")
    pos = next((i for i, o in enumerate(queued_orders)
                if o["order_id"] == order["order_id"]), 0)
    return disruption_days + round(pos * 0.5, 1)

def extract_mgmt_briefing(agent_3_text):
    """Extract Part 5 (management briefing) from Agent 3 output."""
    if not agent_3_text:
        return ""
    match = re.search(
        r"PART 5.*?MANAGEMENT BRIEFING(.*?)(?:═{3,}|END OF COMMUNICATIONS)",
        agent_3_text, re.DOTALL | re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    return agent_3_text  # fallback: pass full text

# ── Header ────────────────────────────────────────────────────────────────────
mode_label = {
    "baseline": "BASELINE — ALL SYSTEMS NORMAL",
    "disruption": "DISRUPTION ACTIVE — F2 NORTHERN FORGE OFFLINE",
    "response": "RESPONSE MODE — AI PIPELINE COMPLETE",
}
mode_colors = {
    "baseline": "#1d9e75",
    "disruption": "#e24b4a",
    "response": "#534ab7",
}
mc = mode_colors[st.session_state["mode"]]
ml = mode_label[st.session_state["mode"]]

col_hdr, col_badge = st.columns([4, 1])
with col_hdr:
    st.markdown(f"""
    <div style="border-bottom:1px solid #e8e6e0;padding-bottom:.875rem;margin-bottom:.875rem">
        <div style="font-size:10px;font-family:monospace;letter-spacing:.1em;
                    text-transform:uppercase;color:{mc};margin:0 0 5px;font-weight:700">
            {ml}
        </div>
        <div class="dash-title">Supply Chain Resilience Dashboard</div>
        <div class="dash-sub">
            4-factory automotive leaf spring network &nbsp;·&nbsp;
            Westfield → Northern Forge → Ridgeway &nbsp;·&nbsp;
            13-day end-to-end pipeline &nbsp;·&nbsp; Claude Sonnet API
        </div>
    </div>""", unsafe_allow_html=True)

with col_badge:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if mode_is("baseline"):
        if st.button("⚡ Trigger F2 Disruption", type="primary", use_container_width=True):
            set_mode("disruption")
            st.rerun()
    elif mode_is("disruption"):
        if st.button("↩ Back to Baseline", use_container_width=True):
            set_mode("baseline")
            st.session_state["agent_1_output"] = None
            st.session_state["agent_2_output"] = None
            st.session_state["agent_3_output"] = None
            st.session_state["agent_4_output"] = None
            st.session_state["selected_option"] = None
            st.session_state["pipeline_stage"] = 0
            st.rerun()
    else:  # response
        if st.button("↩ Back to Disruption", use_container_width=True):
            set_mode("disruption")
            st.rerun()

# ── KPI Strip ─────────────────────────────────────────────────────────────────
if mode_is("baseline"):
    k1, k2, k3, k4, k5 = st.columns(5)
    cards = [
        (k1, f"{SUMMARY['total_orders']}", "Active orders", False),
        (k2, f"CAD {SUMMARY['total_sets']:,}", "Sets in pipeline", False),
        (k3, f"CAD {SUMMARY['total_revenue_cad']/1e6:.1f}M", "Order book", False),
        (k4, fmt_cad(SUMMARY["total_contribution_cad"]), "Total contribution", False),
        (k5, f"{SUMMARY['blended_margin_pct']:.1f}%", "Blended margin", False),
    ]
    for col, val, lbl, danger in cards:
        with col:
            cls = "kpi-card-danger" if danger else "kpi-card"
            vcls = "kpi-val-danger" if danger else "kpi-val"
            lcls = "kpi-lbl-danger" if danger else "kpi-lbl"
            st.markdown(f'<div class="{cls}"><span class="{vcls}">{val}</span>'
                        f'<div class="{lcls}">{lbl}</div></div>', unsafe_allow_html=True)

else:  # disruption or response
    k1, k2, k3, k4, k5 = st.columns(5)
    blocked    = get_orders_by_category("BLOCKED_AT_F2")
    queued     = get_orders_by_category("QUEUED_AT_F1")
    affected   = get_affected_orders()
    blocked_sets = sum(o["quantity_sets"] for o in blocked)
    stuck_sets = sum(o["quantity_sets"] for o in affected)
    contrib_at_risk = sum(o["contribution_cad"] for o in affected)
    coverage = 21.0  # 650 / 3,100
    cards = [
        (k1, f"{SUMMARY['affected_orders']} of {SUMMARY['total_orders']}", "Orders affected", True),
        (k2, f"CAD {blocked_sets:,}", "Sets blocked at F2", True),
        (k3, fmt_cad(contrib_at_risk), "Contribution at risk", True),
        (k4, "650 sets", "Backup available", False),
        (k5, f"{coverage}%", "Backup coverage", False),
    ]
    for col, val, lbl, danger in cards:
        with col:
            cls = "kpi-card-danger" if danger else "kpi-card"
            vcls = "kpi-val-danger" if danger else "kpi-val"
            lcls = "kpi-lbl-danger" if danger else "kpi-lbl"
            st.markdown(f'<div class="{cls}"><span class="{vcls}">{val}</span>'
                        f'<div class="{lcls}">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Disruption banner (disruption + response modes) ───────────────────────────
if not mode_is("baseline"):
    st.markdown("""
    <div class="disruption-banner">
        <div class="disruption-title">F2 — Northern Forge furnace failure · 5 days estimated downtime</div>
        <div class="disruption-body">
            Heat treatment (S3/S4) offline · 11 of 12 orders affected ·
            F1 backup furnace active at 130 sets/day spare · 650 sets over 5 days ·
            Core triage tension: ORD-2607 vs ORD-2601 (Lakeland Transport, CAD 600K relationship)
        </div>
    </div>""", unsafe_allow_html=True)

# ── Production flow bar ───────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Production flow</div>', unsafe_allow_html=True)

FLOW_STAGES = [
    ("S1", "F1", "#e1f5ee", "#0f6e56", "1.0d", False),
    ("S2", "F1", "#9fe1cb", "#085041", "1.5d", False),
    (None, None, None, None, "1.5d", False),
    ("S3", "F2", "#faeeda", "#854f0b", "2.0d", True),
    ("S4", "F2", "#f5c97a", "#633806", "1.0d", True),
    (None, None, None, None, "2.5d", False),
    ("S5", "F3", "#eeedfe", "#534ab7", "1.5d", False),
    ("S6", "F3", "#c9c5f2", "#3c3489", "1.5d", False),
    ("S7", "F3", "#a8a3e8", "#26215c", "0.5d", False),
]

flow_html = '<div class="flow-bar">'
for i, item in enumerate(FLOW_STAGES):
    stage, factory, bg, color, dur, is_f2 = item
    if stage:
        if is_f2 and not mode_is("baseline"):
            bg_use, color_use = "#fcebeb", "#a32d2d"
            badge = f' <span style="font-size:8px;background:#e24b4a;color:white;padding:1px 4px;border-radius:3px;">OFFLINE</span>'
        else:
            bg_use, color_use, badge = bg, color, ""
        flow_html += (f'<div class="flow-stage" style="background:{bg_use};color:{color_use}">'
                      f'<div>{stage}{badge}</div>'
                      f'<div class="flow-label">{factory}·{dur}</div></div>')
    else:
        flow_html += (f'<div style="text-align:center;flex-shrink:0;padding:0 3px">'
                      f'<div style="font-size:8px;color:#b4b2a9;white-space:nowrap">{dur}</div>'
                      f'<div class="flow-arrow">→</div></div>')
    if i < len(FLOW_STAGES) - 1 and stage and FLOW_STAGES[i+1][0]:
        flow_html += '<div class="flow-arrow">→</div>'

flow_html += "</div>"
st.markdown(flow_html, unsafe_allow_html=True)

# ── Factory cards ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Factory network</div>', unsafe_allow_html=True)

fcols = st.columns(4)
for i, f in enumerate(FACTORIES):
    fid = f["factory_id"]
    accent = FACTORY_ACCENT[fid]
    util = f["utilization"]
    util_col = util_color(util)
    is_offline = (fid == "F2" and not mode_is("baseline"))

    stage_pills = "".join([
        f'<span class="stage-pill" style="background:{"#fcebeb" if (is_offline and s in ("S3","S4")) else STAGE_BG.get(s,"#eee")};'
        f'color:{"#a32d2d" if is_offline else accent}">{s}</span>'
        for s in f["stages"]
    ])

    tags = ""
    if f.get("is_bottleneck"):
        tags += '<span class="bottleneck-tag">BOTTLENECK</span> '
    if f.get("government_spec_certified"):
        tags += '<span class="govspec-tag">GOVT-SPEC</span> '
    if is_offline:
        tags = '<span class="offline-tag">OFFLINE — 5 DAYS</span> '

    cap_items = "".join([
        f'<div style="font-size:11px;color:#5f5e5a;display:flex;justify-content:space-between;padding:1px 0">'
        f'<span>{k}</span><span style="font-weight:600;color:#1a1a18">{v:,}/day</span></div>'
        for k, v in f["capacity_per_stage"].items()
    ])
    if f.get("backup_stages"):
        cap_items += ('<div style="font-size:11px;color:#5f5e5a;display:flex;justify-content:space-between;padding:1px 0">'
                      '<span>Backup furnace</span><span style="font-weight:600;color:#1d9e75">340/day</span></div>')

    card_class = "factory-card-danger" if is_offline else "factory-card"

    with fcols[i]:
        st.markdown(f"""
        <div class="{card_class}">
            <div class="fid-badge" style="background:{accent}22;color:{accent}">{fid}</div>
            {f'<div style="margin-bottom:5px">{tags}</div>' if tags else ''}
            <div class="factory-name">{f["name"]}</div>
            <div class="factory-owner">{f["owner"]}</div>
            <div class="factory-role">{f["role"]}</div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                <div class="util-bar-bg">
                    <div style="width:{int(util*100)}%;height:100%;background:{util_col};border-radius:3px"></div>
                </div>
                <div style="font-size:12px;font-weight:600;color:{util_col};min-width:30px;text-align:right">
                    {int(util*100)}%
                </div>
            </div>
            <div style="margin-bottom:8px">{stage_pills}</div>
            <div style="margin-bottom:8px">{cap_items}</div>
            <div style="font-size:11px;color:#888780;border-top:1px solid #f1efe8;padding-top:7px">
                Cost: <strong style="color:#1a1a18">{f["cost_multiplier"]:.2f}×</strong> baseline
            </div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Backup capacity panel (disruption / response modes) ───────────────────────
if not mode_is("baseline"):
    st.markdown("""
    <div class="backup-card">
        <div class="backup-title">F1 Westfield Processing — Backup heat treatment</div>
        <div class="backup-body">
            Nameplate: 340 sets/day &nbsp;·&nbsp;
            Spare (after normal ops): 130 sets/day &nbsp;·&nbsp;
            Startup allowance: 0.5 days &nbsp;·&nbsp;
            Total over 5 days: <strong>650 sets</strong> &nbsp;·&nbsp;
            Cost rate: 0.95× baseline (F1 0.85× + 0.10× surge premium) &nbsp;·&nbsp;
            Quality risk: P04, P05, P06, P07, P08, P09 — manager sign-off required
        </div>
    </div>""", unsafe_allow_html=True)

# ── Order tracker ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Order tracker</div>', unsafe_allow_html=True)

# Filter row
fc1, fc2, fc3, _ = st.columns([1.4, 1.4, 1.8, 4])
with fc1:
    factory_filter = st.selectbox("Factory", ["All", "F1", "F2", "F3", "F4"], key="ff")
with fc2:
    stage_filter = st.selectbox("Stage", ["All", "S1", "S2", "S3", "S4", "S5", "S6", "S7"], key="sf")
with fc3:
    cat_options = ["All orders"]
    if not mode_is("baseline"):
        cat_options += ["Blocked at F2", "Queued at F1", "Safe — past F2"]
    cat_filter = st.selectbox("Category", cat_options, key="cf")

# Apply filters
orders = ACTIVE_ORDERS.copy()
if factory_filter != "All":
    orders = [o for o in orders if o["factory_assigned"] == factory_filter]
if stage_filter != "All":
    orders = [o for o in orders if o["current_stage"] == stage_filter]
if cat_filter == "Blocked at F2":
    orders = [o for o in orders if o["disruption_category"] == "BLOCKED_AT_F2"]
elif cat_filter == "Queued at F1":
    orders = [o for o in orders if o["disruption_category"] == "QUEUED_AT_F1"]
elif cat_filter == "Safe — past F2":
    orders = [o for o in orders if o["disruption_category"] == "SAFE_PAST_F2"]

# Column headers
show_disruption_cols = not mode_is("baseline")
if show_disruption_cols:
    h = st.columns([1.2, 1.6, 2.8, 0.9, 1, 1.4, 1.4, 1.1, 1.2])
    hdrs = ["Order ID", "Customer", "Product", "Stage", "Sets",
            "Revenue", "Contribution", "Delay", "Status"]
else:
    h = st.columns([1.2, 1.6, 2.8, 0.9, 1, 1.4, 1.4, 1.4])
    hdrs = ["Order ID", "Customer", "Product", "Stage", "Sets",
            "Revenue", "Contribution", "Due"]

for col, hdr in zip(h, hdrs):
    col.markdown(f'<div class="col-header">{hdr}</div>', unsafe_allow_html=True)

# Data rows
for o in orders:
    cat = o["disruption_category"]
    stage = o["current_stage"]
    accent = FACTORY_ACCENT.get(o["factory_assigned"], "#888")
    margin_pct = o["contribution_cad"] / o["revenue_cad"] * 100

    bg_map = {
        "BLOCKED_AT_F2": "#fff5f5",
        "QUEUED_AT_F1": "#fff9f0",
        "SAFE_PAST_F2": "#f6fdf9",
    }
    row_bg = bg_map.get(cat, "white") if show_disruption_cols else "white"

    delay = delay_for_order(o) if show_disruption_cols else None

    stage_bg = "#fcebeb" if (stage in ("S3","S4") and show_disruption_cols) else STAGE_BG.get(stage, "#eee")
    stage_color = "#a32d2d" if (stage in ("S3","S4") and show_disruption_cols) else accent

    status_map = {
        "BLOCKED_AT_F2": ("🔴 Blocked", "#a32d2d"),
        "QUEUED_AT_F1": ("🟡 Queued", "#854f0b"),
        "SAFE_PAST_F2": ("🟢 Safe", "#0f6e56"),
    }
    status_txt, status_color = status_map.get(cat, ("—", "#888"))

    penalty_html = (' <span class="penalty-badge">P</span>' if o["penalty_clause"] else "")

    if show_disruption_cols:
        r = st.columns([1.2, 1.6, 2.8, 0.9, 1, 1.4, 1.4, 1.1, 1.2])
    else:
        r = st.columns([1.2, 1.6, 2.8, 0.9, 1, 1.4, 1.4, 1.4])

    r[0].markdown(f'<div class="cell" style="background:{row_bg}">'
                  f'<strong>{o["order_id"]}</strong>{penalty_html}</div>',
                  unsafe_allow_html=True)
    r[1].markdown(f'<div class="cell" style="background:{row_bg}">{o["customer"]}</div>',
                  unsafe_allow_html=True)
    r[2].markdown(f'<div class="cell" style="background:{row_bg}">{o["product_name"]}</div>',
                  unsafe_allow_html=True)
    r[3].markdown(f'<div class="cell" style="background:{row_bg}">'
                  f'<span style="background:{stage_bg};color:{stage_color};'
                  f'padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600">'
                  f'{stage}</span></div>', unsafe_allow_html=True)
    r[4].markdown(f'<div class="cell" style="background:{row_bg}">'
                  f'<strong>{o["quantity_sets"]:,}</strong></div>', unsafe_allow_html=True)
    r[5].markdown(f'<div class="cell" style="background:{row_bg}">'
                  f'CAD {o["revenue_cad"]:,.0f}</div>', unsafe_allow_html=True)
    r[6].markdown(f'<div class="cell" style="background:{row_bg}">'
                  f'CAD {o["contribution_cad"]:,.0f}'
                  f'<div class="cell-sub">{margin_pct:.1f}%</div></div>',
                  unsafe_allow_html=True)
    if show_disruption_cols:
        delay_color = "#e24b4a" if delay and delay > 0 else "#1d9e75"
        delay_txt = f"+{delay}d" if delay and delay > 0 else "0d"
        r[7].markdown(f'<div class="cell" style="background:{row_bg};'
                      f'color:{delay_color};font-weight:600">{delay_txt}</div>',
                      unsafe_allow_html=True)
        r[8].markdown(f'<div class="cell" style="background:{row_bg};'
                      f'color:{status_color};font-size:12px">{status_txt}</div>',
                      unsafe_allow_html=True)
    else:
        r[7].markdown(f'<div class="cell" style="background:{row_bg}">'
                      f'Day {o["due_date_day"]}</div>', unsafe_allow_html=True)

    st.markdown('<div style="border-bottom:1px solid #f1efe8;margin:0"></div>',
                unsafe_allow_html=True)

# Totals row
st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
filt_rev = sum(o["revenue_cad"] for o in orders)
filt_con = sum(o["contribution_cad"] for o in orders)
filt_sets = sum(o["quantity_sets"] for o in orders)
tot_style = "font-size:12px;font-weight:600;color:#5f5e5a;padding:5px 0"
if show_disruption_cols:
    tr = st.columns([1.2, 1.6, 2.8, 0.9, 1, 1.4, 1.4, 1.1, 1.2])
    tr[0].markdown(f'<div style="{tot_style}">Showing {len(orders)}</div>',
                   unsafe_allow_html=True)
    tr[4].markdown(f'<div style="{tot_style}">{filt_sets:,}</div>', unsafe_allow_html=True)
    tr[5].markdown(f'<div style="{tot_style}">CAD {filt_rev:,.0f}</div>', unsafe_allow_html=True)
    tr[6].markdown(f'<div style="{tot_style}">CAD {filt_con:,.0f}</div>', unsafe_allow_html=True)
else:
    tr = st.columns([1.2, 1.6, 2.8, 0.9, 1, 1.4, 1.4, 1.4])
    tr[0].markdown(f'<div style="{tot_style}">Showing {len(orders)}</div>',
                   unsafe_allow_html=True)
    tr[4].markdown(f'<div style="{tot_style}">{filt_sets:,}</div>', unsafe_allow_html=True)
    tr[5].markdown(f'<div style="{tot_style}">CAD {filt_rev:,.0f}</div>', unsafe_allow_html=True)
    tr[6].markdown(f'<div style="{tot_style}">CAD {filt_con:,.0f}</div>', unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DISRUPTION MODE — AI Pipeline launcher
# ══════════════════════════════════════════════════════════════════════════════
if mode_is("disruption"):
    st.markdown('<div class="sec-label">AI response pipeline</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background:white;border:1px solid #e8e6e0;border-radius:10px;
                padding:16px 20px;margin-bottom:1rem">
        <div style="font-size:14px;font-weight:600;color:#1a1a18;margin-bottom:4px">
            Ready to run the 4-agent Claude pipeline
        </div>
        <div style="font-size:12px;color:#73726c;line-height:1.6">
            Agent 1 — Impact Analyst &nbsp;→&nbsp;
            Agent 2 — Reallocation Advisor &nbsp;→&nbsp;
            Agent 3 — Communications Drafter &nbsp;→&nbsp;
            Agent 4 — Decision Summarizer
        </div>
    </div>""", unsafe_allow_html=True)

    if st.button("▶  Run AI Pipeline", type="primary", use_container_width=False):
        st.session_state["pipeline_running"] = True
        st.session_state["pipeline_stage"] = 1

        with st.status("Running Agent 1 — Impact Analyst...", expanded=True) as status:
            st.write("Analysing 12 orders across 4 factories...")
            st.write("Classifying blocked vs queued vs safe orders...")
            st.write("Calculating contribution at risk and backup coverage...")
            try:
                out1 = run_agent_1(
                    FACTORIES, PROCESS_FLOW, PRODUCT_ECON,
                    ACTIVE_ORDERS, SCENARIO_01
                )
                st.session_state["agent_1_output"] = out1
                st.session_state["pipeline_stage"] = 2
                status.update(label="Agent 1 complete ✓", state="complete")
            except Exception as e:
                status.update(label=f"Agent 1 failed: {e}", state="error")
                st.error(f"Agent 1 failed. Check your API key and try again.\n\nError: {e}")
                st.session_state["pipeline_running"] = False
                st.stop()
            st.write("Building 3 reallocation options...")
            st.write("Calculating capacity math, cost deltas, contribution recovery...")
            st.write("Surfacing triage conflicts and decision points...")
            try:
                out2 = run_agent_2(
                    st.session_state["agent_1_output"],
                    FACTORIES, PRODUCT_ECON, SCENARIO_01
                )
                st.session_state["agent_2_output"] = out2
                st.session_state["pipeline_stage"] = 3
                status.update(label="Agent 2 complete ✓", state="complete")
            except Exception as e:
                status.update(label=f"Agent 2 failed: {e}", state="error")
                st.error(f"Agent 2 failed. Agent 1 output is saved — try re-running.\n\nError: {e}")
                st.session_state["pipeline_running"] = False
                st.stop()
        set_mode("response")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RESPONSE MODE — Agent output tabs
# ══════════════════════════════════════════════════════════════════════════════
if mode_is("response"):
    st.markdown('<div class="sec-label">AI pipeline outputs</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "01 — Impact Analyst",
        "02 — Reallocation Advisor",
        "03 — Communications Drafter",
        "04 — Decision Summarizer",
    ])

    # ── Tab 1 ─────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("**Agent 1 — Impact Analyst** · Contribution-ranked impact report")
        if st.session_state["agent_1_output"]:
            st.markdown(
                f'<div class="agent-output">{st.session_state["agent_1_output"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Agent 1 output not yet available.")

    # ── Tab 2 ─────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("**Agent 2 — Reallocation Advisor** · Three options with full tradeoffs")
        if st.session_state["agent_2_output"]:
            st.markdown(
                f'<div class="agent-output">{st.session_state["agent_2_output"]}</div>',
                unsafe_allow_html=True
            )
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("**Select a reallocation option to proceed to communications drafting:**")
            oc1, oc2, oc3 = st.columns(3)
            sel = st.session_state["selected_option"]

            with oc1:
                if st.button("Option A — Speed priority\nMinimise total delay days",
                             use_container_width=True,
                             type="primary" if sel == "A" else "secondary"):
                    st.session_state["selected_option"] = "A"
                    st.rerun()
            with oc2:
                if st.button("Option B — Cost priority\nMaximise contribution recovered",
                             use_container_width=True,
                             type="primary" if sel == "B" else "secondary"):
                    st.session_state["selected_option"] = "B"
                    st.rerun()
            with oc3:
                if st.button("Option C — Relationship priority\nProtect highest-value customers",
                             use_container_width=True,
                             type="primary" if sel == "C" else "secondary"):
                    st.session_state["selected_option"] = "C"
                    st.rerun()

            if sel:
                st.success(f"Option {sel} selected. Run Agents 3 & 4 below.")
                if not st.session_state["agent_3_output"]:
                    if st.button("▶  Run Agents 3 & 4", type="primary"):
                        with st.status("Running Agent 3 — Communications Drafter...",
                                       expanded=True) as status:
                            st.write(f"Drafting communications for Option {sel}...")
                            st.write("Factory partner call framework and written confirmation...")
                            st.write("Tier 1 and Tier 2 customer emails...")
                            st.write("Management briefing...")
                            try:
                                out3 = run_agent_3(
                                    st.session_state["agent_1_output"],
                                    st.session_state["agent_2_output"],
                                    sel, FACTORIES, ACTIVE_ORDERS
                                )
                                st.session_state["agent_3_output"] = out3
                                status.update(label="Agent 3 complete ✓", state="complete")
                            except Exception as e:
                                status.update(label=f"Agent 3 failed: {e}", state="error")
                                st.error(f"Agent 3 failed. Agents 1+2 output is saved — select an option and retry.\n\nError: {e}")
                                st.stop()

                        with st.status("Running Agent 4 — Decision Summarizer...",
                                       expanded=True) as status:
                            st.write("Synthesising executive brief...")
                            st.write("Building P&L projection table...")
                            st.write("Formulating recommendation with rationale...")
                            try:
                                mgmt_briefing = extract_mgmt_briefing(
                                    st.session_state["agent_3_output"]
                                )
                                out4 = run_agent_4(
                                    st.session_state["agent_1_output"],
                                    st.session_state["agent_2_output"],
                                    mgmt_briefing, sel
                                )
                                st.session_state["agent_4_output"] = out4
                                status.update(label="Agent 4 complete ✓", state="complete")
                            except Exception as e:
                                status.update(label=f"Agent 4 failed: {e}", state="error")
                                st.error(f"Agent 4 failed. Agents 1+2+3 output is saved — retry Agent 4 by re-selecting your option.\n\nError: {e}")
                                st.stop()

                        st.rerun()
        else:
            st.info("Agent 2 output not yet available. Return to Disruption mode and run the pipeline.")

    # ── Tab 3 ─────────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("**Agent 3 — Communications Drafter** · Factory partner · Customers · Management")
        if st.session_state["agent_3_output"]:
            opt = st.session_state["selected_option"]
            opt_names = {"A": "Speed priority", "B": "Cost priority", "C": "Relationship priority"}
            st.caption(f"Drafted for Option {opt} — {opt_names.get(opt, '')}")
            st.markdown(
                f'<div class="agent-output">{st.session_state["agent_3_output"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Select an option in the Reallocation Advisor tab, then run Agents 3 & 4.")

    # ── Tab 4 ─────────────────────────────────────────────────────────────────
    with tab4:
        st.markdown("**Agent 4 — Decision Summarizer** · One-page executive brief · P&L projection · Recommendation")
        if st.session_state["agent_4_output"]:
            st.markdown(
                f'<div class="agent-output">{st.session_state["agent_4_output"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Select an option in the Reallocation Advisor tab, then run Agents 3 & 4.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
st.markdown(
    '<div style="font-size:11px;color:#b4b2a9;text-align:center;padding-top:1rem;'
    'border-top:1px solid #e8e6e0">'
    'Supply Chain Resilience Dashboard &nbsp;·&nbsp; GenAI Applications in Business '
    '&nbsp;·&nbsp; Rotman MBA 2027 &nbsp;·&nbsp; Claude Sonnet API'
    '</div>',
    unsafe_allow_html=True
)
