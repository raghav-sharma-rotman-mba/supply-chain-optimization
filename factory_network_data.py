"""
factory_network_data.py
Supply Chain Resilience Dashboard — Verified Data Model v3
Rotman MBA 2027 · GenAI Applications in Business

All figures verified. Run this file directly to export JSON files,
or import the get_*() functions for use in the dashboard and agents.
"""

import json, os

# ── 1. FACTORIES ─────────────────────────────────────────────────────────────

FACTORIES = [
    {
        "factory_id": "F1",
        "name": "Westfield Processing",
        "owner": "Dave Morrison",
        "role": "Upstream — raw preparation and hot forming",
        "stages": ["S1", "S2"],
        "backup_stages": ["S3", "S4"],
        "capacity_per_stage": {"S1": 1100, "S2": 825, "S3_backup": 340},
        "spare_backup_capacity_per_day": 130,
        "utilization": 0.62,
        "cost_multiplier": 0.85,
        "surge_premium": 0.10,
        "effective_backup_rate": 0.95,
        "is_bottleneck": False,
        "government_spec_certified": False,
        "notes": (
            "Upstream entry point — no redundancy. Runs below capacity "
            "deliberately to buffer the F2 bottleneck. Backup heat treatment "
            "furnace at 340/day nameplate, 130/day spare after normal ops. "
            "Older equipment — elevated quality risk for tight-tolerance products."
        ),
    },
    {
        "factory_id": "F2",
        "name": "Northern Forge",
        "owner": "Mike Sullivan",
        "role": "Midstream — heat treatment and quenching. Network bottleneck.",
        "stages": ["S3", "S4"],
        "backup_stages": [],
        "capacity_per_stage": {"S3": 900, "S4": 900},
        "spare_backup_capacity_per_day": 0,
        "utilization": 0.85,
        "cost_multiplier": 0.90,
        "surge_premium": None,
        "effective_backup_rate": None,
        "is_bottleneck": True,
        "government_spec_certified": False,
        "notes": (
            "Binding network constraint. Effective throughput 765/day at 85% "
            "utilization. Heat treatment ~30% of total transformation cost. "
            "Single point of failure — failure requires F1 backup furnace."
        ),
    },
    {
        "factory_id": "F3",
        "name": "Ridgeway Assembly",
        "owner": "Tom Bradley",
        "role": "Downstream hub — assembly, painting, packaging, customer interface",
        "stages": ["S5", "S6", "S7"],
        "backup_stages": [],
        "capacity_per_stage": {"S5": 980, "S6": 1050, "S7": 1200},
        "spare_capacity_per_day": 215,
        "utilization": 0.78,
        "cost_multiplier": 1.00,
        "surge_premium": None,
        "effective_backup_rate": None,
        "is_bottleneck": False,
        "government_spec_certified": False,
        "notes": (
            "Customer-facing hub. Tom Bradley holds 30-year relationships "
            "across 250+ B2B accounts. Baseline cost reference for network. "
            "S5 at 980/day is F3 internal constraint."
        ),
    },
    {
        "factory_id": "F4",
        "name": "Bayview Components",
        "owner": "Chris Lawson",
        "role": "Independent partner — S5–S7, government-specification coating",
        "stages": ["S5", "S6", "S7"],
        "backup_stages": [],
        "capacity_per_stage": {"S5": 560, "S6": 640, "S7": 490},
        "spare_capacity_per_day": 170,
        "utilization": 0.71,
        "cost_multiplier": 1.15,
        "surge_premium": None,
        "effective_backup_rate": None,
        "is_bottleneck": False,
        "government_spec_certified": True,
        "notes": (
            "Independent business — not subordinate. Participates commercially "
            "to fill 29% spare capacity at 1.15x premium. Only factory certified "
            "for govt-spec coating. S7 at 490/day is F4 internal constraint. "
            "All communications must use collaborative, not directive, language."
        ),
    },
]

# ── 2. PROCESS FLOW ───────────────────────────────────────────────────────────

PROCESS_FLOW = {
    "total_pipeline_days": 13.0,
    "processing_days": 9.5,
    "handover_days": 2.5,
    "transit_days": 1.0,
    "hidden_time_pct": 0.31,
    "stages": [
        {"stage_id": "S1", "factory_id": "F1",
         "description": "Raw material intake, cutting, straightening, inspection",
         "duration_days": 1.0, "sequence": 1, "type": "processing"},
        {"stage_id": "S2", "factory_id": "F1",
         "description": "Hot forming — heated and pressed into spring profile",
         "duration_days": 1.5, "sequence": 2, "type": "processing"},
        {"stage_id": "F1_F2_handover", "factory_id": None,
         "description": "Batch accumulation at F1 plus transit to F2",
         "duration_days": 1.5, "sequence": 3, "type": "handover",
         "from_factory": "F1", "to_factory": "F2"},
        {"stage_id": "S3", "factory_id": "F2",
         "description": "Heat treatment — 850–900°C held to specification",
         "duration_days": 2.0, "sequence": 4, "type": "processing"},
        {"stage_id": "S4", "factory_id": "F2",
         "description": "Quenching — rapid cooling to lock microstructure",
         "duration_days": 1.0, "sequence": 5, "type": "processing"},
        {"stage_id": "F2_F3_handover", "factory_id": None,
         "description": "Batch accumulation at F2 plus transit to F3/F4",
         "duration_days": 2.5, "sequence": 6, "type": "handover",
         "from_factory": "F2", "to_factory": "F3"},
        {"stage_id": "S5", "factory_id": "F3", "factory_id_alternate": "F4",
         "description": "Final assembly — leaf stack, centre bolt, clips, U-bolts",
         "duration_days": 1.5, "sequence": 7, "type": "processing"},
        {"stage_id": "S6", "factory_id": "F3", "factory_id_alternate": "F4",
         "description": "Painting and corrosion treatment (govt-spec via F4 only)",
         "duration_days": 1.5, "sequence": 8, "type": "processing"},
        {"stage_id": "S7", "factory_id": "F3", "factory_id_alternate": "F4",
         "description": "Packaging, batch tagging, dispatch staging",
         "duration_days": 0.5, "sequence": 9, "type": "processing"},
    ],
    "classification_rules": {
        "BLOCKED_AT_F2": (
            "Current stage is S3 or S4, OR in F1_F2_handover with "
            "less than 1.0 day remaining before F2 entry"
        ),
        "QUEUED_AT_F1": (
            "Current stage is S1, S2, OR in F1_F2_handover with "
            "more than 1.0 day remaining before F2 entry"
        ),
        "SAFE_PAST_F2": (
            "Current stage is F2_F3_handover, S5, S6, or S7"
        ),
    },
    "backup_capacity": {
        "source_factory": "F1",
        "furnace_nameplate_per_day": 340,
        "spare_per_day": 130,
        "total_sets_5day_disruption": 650,
        "coverage_pct_of_blocked": 21.0,
        "cost_rate": 0.95,
        "quality_risk_products": ["P04", "P05", "P06", "P07", "P08", "P09"],
        "note": "130/day spare × 5 days = 650 sets. Covers 21% of 3,100 blocked sets.",
    },
}

# ── 3. PRODUCT ECONOMICS ──────────────────────────────────────────────────────

PRODUCT_ECONOMICS = [
    {
        "product_id": "P01", "name": "Helper kit — light duty",
        "leaf_count": 2, "government_spec": False,
        "revenue_per_set_cad": 95,
        "contribution_per_set_cad": 24,
        "margin_pct": 25.3,
        "requires_F4_coating": False,
        "heat_treatment_tolerance": "standard",
        "quality_risk_via_backup": False,
        "notes": "Lowest contribution/set in portfolio. Triage tension anchor for ORD-2607.",
    },
    {
        "product_id": "P02", "name": "Standard 4-leaf spring",
        "leaf_count": 4, "government_spec": False,
        "revenue_per_set_cad": 170,
        "contribution_per_set_cad": 43,
        "margin_pct": 25.3,
        "requires_F4_coating": False,
        "heat_treatment_tolerance": "standard",
        "quality_risk_via_backup": False,
        "notes": "High-volume standard product. Two orders in current book.",
    },
    {
        "product_id": "P03", "name": "Standard 6-leaf spring",
        "leaf_count": 6, "government_spec": False,
        "revenue_per_set_cad": 250,
        "contribution_per_set_cad": 63,
        "margin_pct": 25.2,
        "requires_F4_coating": False,
        "heat_treatment_tolerance": "standard",
        "quality_risk_via_backup": False,
        "notes": "Mid-range standard product.",
    },
    {
        "product_id": "P04", "name": "Heavy-duty 8-leaf spring",
        "leaf_count": 8, "government_spec": False,
        "revenue_per_set_cad": 350,
        "contribution_per_set_cad": 88,
        "margin_pct": 25.1,
        "requires_F4_coating": False,
        "heat_treatment_tolerance": "tight",
        "quality_risk_via_backup": True,
        "notes": "Tight heat treatment tolerance — quality risk via F1 backup furnace.",
    },
    {
        "product_id": "P05", "name": "Heavy-duty 10-leaf spring",
        "leaf_count": 10, "government_spec": False,
        "revenue_per_set_cad": 445,
        "contribution_per_set_cad": 112,
        "margin_pct": 25.2,
        "requires_F4_coating": False,
        "heat_treatment_tolerance": "tight",
        "quality_risk_via_backup": True,
        "notes": "High-value product. Lakeland Transport's premium order (ORD-2601).",
    },
    {
        "product_id": "P06", "name": "Parabolic taper spring — light",
        "leaf_count": 3, "government_spec": False,
        "revenue_per_set_cad": 290,
        "contribution_per_set_cad": 73,
        "margin_pct": 25.2,
        "requires_F4_coating": False,
        "heat_treatment_tolerance": "tight",
        "quality_risk_via_backup": True,
        "notes": "Tight parabolic profile — heat treatment precision matters.",
    },
    {
        "product_id": "P07", "name": "Parabolic taper spring — heavy",
        "leaf_count": 5, "government_spec": False,
        "revenue_per_set_cad": 400,
        "contribution_per_set_cad": 101,
        "margin_pct": 25.3,
        "requires_F4_coating": False,
        "heat_treatment_tolerance": "tight",
        "quality_risk_via_backup": True,
        "notes": "Safe order product (ORD-2606). Cascade Vehicle Parts.",
    },
    {
        "product_id": "P08", "name": "Govt-spec 10-leaf spring",
        "leaf_count": 10, "government_spec": True,
        "revenue_per_set_cad": 535,
        "contribution_per_set_cad": 135,
        "margin_pct": 25.2,
        "requires_F4_coating": True,
        "heat_treatment_tolerance": "critical",
        "quality_risk_via_backup": True,
        "notes": "Govt procurement — penalty clause. F4 coating required. Critical tolerance.",
    },
    {
        "product_id": "P09", "name": "Govt-spec 12-leaf spring",
        "leaf_count": 12, "government_spec": True,
        "revenue_per_set_cad": 660,
        "contribution_per_set_cad": 166,
        "margin_pct": 25.2,
        "requires_F4_coating": True,
        "heat_treatment_tolerance": "critical",
        "quality_risk_via_backup": True,
        "notes": "Highest value product. Govt procurement — penalty clause. F4 coating required.",
    },
]

# ── 4. ACTIVE ORDERS ──────────────────────────────────────────────────────────

ACTIVE_ORDERS = [
    # ── BLOCKED AT F2 (S3 or S4) ── 6 orders, 3,100 sets ─────────────────────
    {
        "order_id": "ORD-2601", "customer": "Lakeland Transport",
        "product_id": "P05", "product_name": "Heavy-duty 10-leaf spring",
        "quantity_sets": 460, "current_stage": "S3",
        "revenue_cad": 204700, "contribution_cad": 51520,
        "due_date_day": 8, "penalty_clause": False, "penalty_amount_cad": None,
        "factory_assigned": "F2",
        "disruption_category": "BLOCKED_AT_F2",
        "relationship_group": "LAKELAND",
        "relationship_note": (
            "Shares customer with ORD-2607. Combined Lakeland revenue "
            "CAD 442,200. High contribution per set (CAD 112) vs ORD-2607 (CAD 24). "
            "Core triage tension — see ORD-2607."
        ),
    },
    {
        "order_id": "ORD-2603", "customer": "Meridian Truck Parts",
        "product_id": "P03", "product_name": "Standard 6-leaf spring",
        "quantity_sets": 800, "current_stage": "S4",
        "revenue_cad": 200000, "contribution_cad": 50400,
        "due_date_day": 12, "penalty_clause": False, "penalty_amount_cad": None,
        "factory_assigned": "F2",
        "disruption_category": "BLOCKED_AT_F2",
        "relationship_group": "MERIDIAN",
        "relationship_note": None,
    },
    {
        "order_id": "ORD-2605", "customer": "Prairie Auto Distributors",
        "product_id": "P02", "product_name": "Standard 4-leaf spring",
        "quantity_sets": 1050, "current_stage": "S3",
        "revenue_cad": 178500, "contribution_cad": 45150,
        "due_date_day": 9, "penalty_clause": False, "penalty_amount_cad": None,
        "factory_assigned": "F2",
        "disruption_category": "BLOCKED_AT_F2",
        "relationship_group": "PRAIRIE",
        "relationship_note": None,
    },
    {
        "order_id": "ORD-2608", "customer": "Ridgetop Mining Supply",
        "product_id": "P08", "product_name": "Govt-spec 10-leaf spring",
        "quantity_sets": 120, "current_stage": "S3",
        "revenue_cad": 64200, "contribution_cad": 16200,
        "due_date_day": 7, "penalty_clause": True, "penalty_amount_cad": 15000,
        "factory_assigned": "F2",
        "disruption_category": "BLOCKED_AT_F2",
        "relationship_group": "RIDGETOP",
        "relationship_note": (
            "Govt procurement order. Penalty clause active — CAD 15,000 known. "
            "Critical heat treatment tolerance — quality risk if routed via F1 backup."
        ),
    },
    {
        "order_id": "ORD-2609", "customer": "Summit Transport Group",
        "product_id": "P06", "product_name": "Parabolic taper spring — light",
        "quantity_sets": 420, "current_stage": "S4",
        "revenue_cad": 121800, "contribution_cad": 30660,
        "due_date_day": 13, "penalty_clause": False, "penalty_amount_cad": None,
        "factory_assigned": "F2",
        "disruption_category": "BLOCKED_AT_F2",
        "relationship_group": "SUMMIT",
        "relationship_note": None,
    },
    {
        "order_id": "ORD-2611", "customer": "Apex Fleet Solutions",
        "product_id": "P04", "product_name": "Heavy-duty 8-leaf spring",
        "quantity_sets": 250, "current_stage": "S3",
        "revenue_cad": 87500, "contribution_cad": 22000,
        "due_date_day": 10, "penalty_clause": True, "penalty_amount_cad": None,
        "factory_assigned": "F2",
        "disruption_category": "BLOCKED_AT_F2",
        "relationship_group": "APEX",
        "relationship_note": (
            "Shares customer with ORD-2602. Apex Fleet has two affected orders. "
            "Penalty amount unquantified — escalate."
        ),
    },
    # ── QUEUED AT F1 (S1 or S2) ── 5 orders, 7,000 sets ─────────────────────
    {
        "order_id": "ORD-2602", "customer": "Apex Fleet Solutions",
        "product_id": "P09", "product_name": "Govt-spec 12-leaf spring",
        "quantity_sets": 280, "current_stage": "S2",
        "revenue_cad": 184800, "contribution_cad": 46480,
        "due_date_day": 10, "penalty_clause": True, "penalty_amount_cad": None,
        "factory_assigned": "F1",
        "disruption_category": "QUEUED_AT_F1",
        "relationship_group": "APEX",
        "relationship_note": (
            "Govt procurement. Penalty amount unquantified — escalate. "
            "Shares customer with ORD-2611. Highest contribution/set in book (CAD 166)."
        ),
    },
    {
        "order_id": "ORD-2604", "customer": "Northern Fleet Co.",
        "product_id": "P04", "product_name": "Heavy-duty 8-leaf spring",
        "quantity_sets": 650, "current_stage": "S1",
        "revenue_cad": 227500, "contribution_cad": 57200,
        "due_date_day": 15, "penalty_clause": False, "penalty_amount_cad": None,
        "factory_assigned": "F1",
        "disruption_category": "QUEUED_AT_F1",
        "relationship_group": "NORTHERN",
        "relationship_note": None,
    },
    {
        "order_id": "ORD-2607", "customer": "Lakeland Transport",
        "product_id": "P01", "product_name": "Helper kit — light duty",
        "quantity_sets": 2500, "current_stage": "S2",
        "revenue_cad": 237500, "contribution_cad": 60000,
        "due_date_day": 11, "penalty_clause": False, "penalty_amount_cad": None,
        "factory_assigned": "F1",
        "disruption_category": "QUEUED_AT_F1",
        "relationship_group": "LAKELAND",
        "relationship_note": (
            "CORE TRIAGE TENSION: ranks LAST by contribution per set (CAD 24/set) "
            "but shares the Lakeland Transport relationship (combined CAD 442K revenue) "
            "with ORD-2601 (CAD 112/set). Contribution ranking deprioritises this order; "
            "relationship ranking requires protecting both. Manager must decide whether "
            "Lakeland views these as one commitment or two independent orders."
        ),
    },
    {
        "order_id": "ORD-2610", "customer": "Ironside Fleet Services",
        "product_id": "P03", "product_name": "Standard 6-leaf spring",
        "quantity_sets": 680, "current_stage": "S2",
        "revenue_cad": 170000, "contribution_cad": 42840,
        "due_date_day": 14, "penalty_clause": False, "penalty_amount_cad": None,
        "factory_assigned": "F1",
        "disruption_category": "QUEUED_AT_F1",
        "relationship_group": "IRONSIDE",
        "relationship_note": None,
    },
    {
        "order_id": "ORD-2612", "customer": "Highline Auto Parts",
        "product_id": "P02", "product_name": "Standard 4-leaf spring",
        "quantity_sets": 2890, "current_stage": "S1",
        "revenue_cad": 491300, "contribution_cad": 124270,
        "due_date_day": 16, "penalty_clause": False, "penalty_amount_cad": None,
        "factory_assigned": "F1",
        "disruption_category": "QUEUED_AT_F1",
        "relationship_group": "HIGHLINE",
        "relationship_note": "Largest order by sets. Standard commodity product.",
    },
    # ── SAFE — PAST F2 (S5/S6/S7) ── 1 order, 2,075 sets ────────────────────
    {
        "order_id": "ORD-2606", "customer": "Cascade Vehicle Parts",
        "product_id": "P07", "product_name": "Parabolic taper spring — heavy",
        "quantity_sets": 2075, "current_stage": "S6",
        "revenue_cad": 830000, "contribution_cad": 209575,
        "due_date_day": 6, "penalty_clause": False, "penalty_amount_cad": None,
        "factory_assigned": "F3",
        "disruption_category": "SAFE_PAST_F2",
        "relationship_group": "CASCADE",
        "relationship_note": (
            "Safe — already past F2 at time of failure. On schedule for Day 6. "
            "Proactive customer communication recommended to prevent inbound enquiries."
        ),
    },
]

# ── 5. DISRUPTION SCENARIOS ───────────────────────────────────────────────────

DISRUPTION_SCENARIOS = [
    {
        "scenario_id": "DISRUPT-01",
        "name": "F2 furnace breakdown",
        "short_name": "Furnace failure — 5 days",
        "facility_id": "F2",
        "failure_type": "Furnace breakdown",
        "duration_days": 5,
        "affected_stages": ["S3", "S4"],
        "backup_available": True,
        "backup_facility_id": "F1",
        "backup_capacity_per_day": 130,
        "backup_total_sets": 650,
        "backup_coverage_pct": 21.0,
        "backup_cost_rate": 0.95,
        "quality_risk_products": ["P04", "P05", "P06", "P07", "P08", "P09"],
        "description": (
            "Primary disruption scenario. F2 furnace fails for 5 days. "
            "6 orders (3,100 sets) physically blocked at F2. "
            "5 orders (7,000 sets) queued at F1 with no downstream path. "
            "F1 backup furnace: 130 spare sets/day × 5 days = 650 sets — covers 21% of blocked volume. "
            "Core triage tension: ORD-2607 (Lakeland, CAD 24/set) vs ORD-2601 (Lakeland, CAD 112/set). "
            "Combined Lakeland relationship: CAD 442,200 in current book."
        ),
    },
    {
        "scenario_id": "DISRUPT-02",
        "name": "EN45 steel price spike",
        "short_name": "Steel cost shock — 25%",
        "facility_id": None,
        "failure_type": "Raw material cost shock",
        "duration_days": None,
        "affected_stages": ["S1", "S2"],
        "price_increase_pct": 25,
        "backup_available": False,
        "description": (
            "EN45 spring steel price increases 25%. Tests margin erosion "
            "analysis and cost-contribution reasoning across the full order book."
        ),
    },
    {
        "scenario_id": "DISRUPT-03",
        "name": "Rush government order",
        "short_name": "Rush order — 3,500 sets",
        "facility_id": None,
        "failure_type": "Demand spike",
        "duration_days": None,
        "order_quantity_sets": 3500,
        "required_delivery_weeks": 3,
        "affected_stages": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"],
        "backup_available": False,
        "description": (
            "Rush government order for 3,500 sets in 3 weeks. Tests opportunity "
            "cost analysis and capacity allocation against existing order book."
        ),
    },
]

# ── GETTER FUNCTIONS ──────────────────────────────────────────────────────────

def get_factories():
    return FACTORIES

def get_process_flow():
    return PROCESS_FLOW

def get_product_economics():
    return PRODUCT_ECONOMICS

def get_active_orders():
    return ACTIVE_ORDERS

def get_disruption_scenarios():
    return DISRUPTION_SCENARIOS

def get_scenario(scenario_id):
    return next((s for s in DISRUPTION_SCENARIOS if s["scenario_id"] == scenario_id), None)

def get_product(product_id):
    return next((p for p in PRODUCT_ECONOMICS if p["product_id"] == product_id), None)

def get_factory(factory_id):
    return next((f for f in FACTORIES if f["factory_id"] == factory_id), None)

def get_orders_by_category(category):
    """Returns orders filtered by disruption_category."""
    return [o for o in ACTIVE_ORDERS if o["disruption_category"] == category]

def get_affected_orders():
    """Returns all orders except SAFE_PAST_F2."""
    return [o for o in ACTIVE_ORDERS if o["disruption_category"] != "SAFE_PAST_F2"]

# ── DERIVED METRICS (used by dashboard KPI strip) ─────────────────────────────

def get_network_summary():
    orders = ACTIVE_ORDERS
    affected = get_affected_orders()
    return {
        "total_orders": len(orders),
        "total_sets": sum(o["quantity_sets"] for o in orders),
        "total_revenue_cad": sum(o["revenue_cad"] for o in orders),
        "total_contribution_cad": sum(o["contribution_cad"] for o in orders),
        "blended_margin_pct": (
            sum(o["contribution_cad"] for o in orders) /
            sum(o["revenue_cad"] for o in orders) * 100
        ),
        "orders_with_penalty": len([o for o in orders if o["penalty_clause"]]),
        # Disruption-specific (DISRUPT-01)
        "affected_orders": len(affected),
        "stuck_sets": sum(o["quantity_sets"] for o in affected),
        "contribution_at_risk_cad": sum(o["contribution_cad"] for o in affected),
        "backup_sets_available": 650,
        "backup_coverage_pct": round(650 / sum(o["quantity_sets"] for o in get_orders_by_category("BLOCKED_AT_F2")) * 100, 1),
    }

# ── EXPORT TO JSON (run this file directly to regenerate) ─────────────────────

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    files = {
        "factories.json": FACTORIES,
        "process_flow.json": PROCESS_FLOW,
        "product_economics.json": PRODUCT_ECONOMICS,
        "active_orders.json": ACTIVE_ORDERS,
        "disruption_scenarios.json": DISRUPTION_SCENARIOS,
    }
    for fname, data in files.items():
        path = os.path.join(out_dir, fname)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Written: {fname}")
    summary = get_network_summary()
    print(f"\nNetwork summary:")
    print(f"  {summary['total_orders']} orders · CAD {summary['total_revenue_cad']:,.0f} revenue")
    print(f"  CAD {summary['total_contribution_cad']:,.0f} contribution · {summary['blended_margin_pct']:.1f}% blended margin")
    print(f"  DISRUPT-01: {summary['affected_orders']} affected · {summary['stuck_sets']:,} stuck sets")
    print(f"  Backup covers {summary['backup_coverage_pct']}% of stuck volume")
