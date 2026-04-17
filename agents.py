"""
agents.py
Supply Chain Resilience Dashboard — Four-Agent Pipeline
Rotman MBA 2027 · GenAI Applications in Business

Four sequential Claude Sonnet API calls:
  Agent 1 — Impact Analyst
  Agent 2 — Reallocation Advisor
  Agent 3 — Communications Drafter
  Agent 4 — Decision Summarizer

Usage:
  from agents import run_agent_1, run_agent_2, run_agent_3, run_agent_4
"""

import anthropic
import json

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 4000

# ── Helper ─────────────────────────────────────────────────────────────────────

def _call_claude(system_prompt: str, user_message: str) -> str:
    """Single Claude API call. Returns the text response."""
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": user_message}],
        system=system_prompt,
    )
    return message.content[0].text

def _to_json_str(data) -> str:
    return json.dumps(data, indent=2)

# ── AGENT 1 — IMPACT ANALYST ───────────────────────────────────────────────────

AGENT_1_SYSTEM = """You are the Impact Analyst in a supply chain disruption response system for a four-factory automotive leaf spring manufacturing network. Your job is to perform a precise, structured analysis of a disruption event and produce a contribution-ranked impact report.

NETWORK CONTEXT
Production flow: F1 (S1,S2) → F2 (S3,S4) → F3/F4 (S5,S6,S7).
F2 is the bottleneck. When F2 fails, the only heat treatment backup is F1's older furnace at 130 sets/day spare capacity, 650 sets over 5 days (after 0.5-day startup allowance).
Backup cost rate: 0.95× baseline. Quality risk for products with tight/critical heat treatment tolerance.

ORDER CLASSIFICATION RULES
BLOCKED_AT_F2: Current stage S3 or S4 — physically stopped at failed facility.
QUEUED_AT_F1: Current stage S1, S2, or F1→F2 handover — upstream processing done, no downstream path.
SAFE_PAST_F2: Current stage F2→F3 handover, S5, S6, or S7 — unaffected.

DELAY CALCULATIONS
Blocked at F2: minimum delay = disruption duration (5 days).
Queued at F1: delay = disruption duration + queue position delay at F2 restart (0.5 days per position).
Safe: delay = 0.

PENALTY HANDLING
If penalty clause exists and order will be late: calculate days late and note penalty amount (or flag as UNQUANTIFIED).
Adjusted contribution = stated contribution − penalty amount.

OUTPUT FORMAT — produce all sections in order. Do not skip any section.

═══════════════════════════════════════
DISRUPTION IMPACT REPORT
═══════════════════════════════════════

DISRUPTION SUMMARY
Event: [description]
Facility: F2 — Northern Forge
Duration: 5 days
Total orders: [N] | Affected: [N] | Safe: [N]

────────────────────────────────────────
BACKUP CAPACITY SUMMARY
────────────────────────────────────────
Source: F1 backup furnace
Nameplate: 340 sets/day | Spare: 130 sets/day
Effective duration: 4.5 days (0.5 startup)
Total backup available: 650 sets
Total stuck volume: [N] sets
Backup coverage: [X]%
Quality risk products: [list product IDs]

────────────────────────────────────────
SECTION 1: BLOCKED AT F2
[For each order, sorted by contribution descending:]
Order ID: [ID]
Customer: [name]
Product: [name] | Qty: [N] sets
Stage: [S3/S4] | Due: Day [N]
Contribution: CAD [X] | Per set: CAD [X]
Penalty: [YES — CAD X / UNQUANTIFIED | NO]
Adjusted contribution: CAD [X]
Delay: [N] days minimum
Backup eligible: [YES/NO] — reason if NO
Relationship flag: [note if shared customer]
Priority rank by contribution: #[N]

────────────────────────────────────────
SECTION 2: QUEUED AT F1
[Same structure, sorted by contribution descending]

────────────────────────────────────────
SECTION 3: SAFE — PAST F2
Order ID: [ID] | Customer: [name] | Stage: [S] | Status: ON SCHEDULE

────────────────────────────────────────
SECTION 4: CONTRIBUTION AT RISK
Total at risk (stated): CAD [X]
Total at risk (adjusted for penalties): CAD [X]
Backup recovery potential: CAD [X]
Net unrecoverable (worst case): CAD [X]
Blocked at F2: CAD [X] ([N] orders)
Queued at F1: CAD [X] ([N] orders)

────────────────────────────────────────
SECTION 5: TRIAGE FLAGS
[List each flag:]
PENALTY RISK: [Order ID] — [N] days late — CAD [X] or UNQUANTIFIED
RELATIONSHIP RISK: [Order ID] shares customer [name] with [Order ID]
QUALITY RISK: [Order ID] — tight tolerance — backup furnace risk
COVERAGE GAP: Backup covers [X]% — [N] orders have no backup path

────────────────────────────────────────
SECTION 6: PRIORITY RANKING COMPARISON
RANKING A — BY ADJUSTED CONTRIBUTION (high to low):
[#1 ORD-XXXX CAD X, #2 ...]

RANKING B — BY CUSTOMER RELATIONSHIP VALUE (high to low):
[Customer: CAD X total — orders ORD-XXXX, ORD-XXXX]

RANKING C — BY DUE DATE (earliest first):
[#1 ORD-XXXX Day N, #2 ...]

RANKING CONFLICT SUMMARY:
[Orders whose rank differs materially across rankings — one sentence each]

═══════════════════════════════════════
END OF IMPACT REPORT
Do not include recommendations. Facts and calculations only.
═══════════════════════════════════════"""


def run_agent_1(factories, process_flow, product_economics, active_orders,
                disruption_scenario):
    """
    Agent 1 — Impact Analyst.
    Returns the structured impact report as a string.
    """
    user_message = f"""DISRUPTION EVENT
Facility: F2 — Northern Forge (Mike Sullivan)
Failure type: {disruption_scenario['failure_type']}
Estimated downtime: {disruption_scenario['duration_days']} days
Backup: F1 backup furnace — 130 sets/day spare, 650 sets over 5 days

FACTORY NETWORK DATA
{_to_json_str(factories)}

PROCESS FLOW DATA
{_to_json_str(process_flow)}

ACTIVE ORDERS
{_to_json_str(active_orders)}

PRODUCT ECONOMICS
{_to_json_str(product_economics)}

DISRUPTION SCENARIO
{_to_json_str(disruption_scenario)}

Each order already has its disruption_category field set (BLOCKED_AT_F2 / QUEUED_AT_F1 / SAFE_PAST_F2).
Use these classifications directly.

Produce the full impact report now. Show all calculations. Follow the output format exactly."""

    return _call_claude(AGENT_1_SYSTEM, user_message)


# ── AGENT 2 — REALLOCATION ADVISOR ────────────────────────────────────────────

AGENT_2_SYSTEM = """You are the Reallocation Advisor in a supply chain disruption response system. You receive an impact report from the Impact Analyst and generate three reallocation options for the operations manager.

NETWORK CONSTRAINTS
- F2 is completely offline. No partial F2 operations possible.
- Backup heat treatment: F1 only, 650 sets over 5 days.
- F3 and F4 can only receive product that has completed S3 and S4.
- Government-spec orders (requiring F4 coating) cannot be finished at F3.

BACKUP CAPACITY RULES
Full coverage: backup covers entire stuck quantity → 0.5-day delay (startup only).
Partial coverage: split order — covered portion 0.5-day delay, uncovered portion full 5-day delay + queue position.
No coverage: full 5-day delay + queue position at F2 restart.
Quality risk override: flag orders with tight/critical tolerance. Option A/C include with manager sign-off required. Option B excludes by default.

THREE OPTIONS
OPTION A — SPEED PRIORITY
Primary: minimise total delay days across all orders.
Allocate backup by earliest due date first.
Secondary: higher quantity orders where due dates tie.

OPTION B — COST PRIORITY  
Primary: maximise contribution per set recovered from backup.
Rank all backup-eligible orders by contribution_cad ÷ quantity_sets (descending).
Allocate highest contribution-per-set orders first until backup exhausted.

OPTION C — RELATIONSHIP PRIORITY
Primary: protect orders by total customer relationship value.
Group all affected orders by customer. Rank customers by sum of all order revenues in the book.
Allocate backup to fully cover highest-value customer's orders before moving to next.
Special rule: shared customer orders (same customer, multiple orders) must be evaluated together.

COST DELTA CALCULATION
Backup processing premium = sets through backup × (0.95 − 0.90) × baseline_cost_per_set
Penalty exposure = sum of known penalty amounts for orders delivered late
Total cost delta = premium + known penalties

CONTRIBUTION RECOVERY
Recovery rate = contribution of covered orders ÷ total at-risk contribution × 100

OUTPUT FORMAT — produce all sections for all three options.

═══════════════════════════════════════
REALLOCATION ADVISORY REPORT
Backup available: 650 sets over 5 days
Total stuck volume: [N] sets | Coverage ceiling: [X]%
═══════════════════════════════════════

────────────────────────────────────────
OPTION A — SPEED PRIORITY
Minimise total days late across all affected orders
────────────────────────────────────────
ALLOCATION SEQUENCE
[List orders in allocation order with running backup total:]
#1 ORD-XXXX | [customer] | [N] sets | Due Day [N]
   Allocation: [N] sets [FULL/PARTIAL: N of M] | Backup remaining: [N]
[Continue until backup exhausted, then NO COVERAGE for remainder]

COVERAGE SUMMARY
Fully covered: [N] ([list IDs]) | Partially covered: [N] | No coverage: [N]
Total sets covered: [N] of [N] ([X]%)

DELAY OUTCOMES
[One line per order:]
ORD-XXXX: [FULL COVER 0.5d / PARTIAL Xcovered 0.5d + Xuncovered Nd / NO COVER Nd]

PENALTY EXPOSURE
[Orders with penalty clauses and projected lateness:]
ORD-XXXX: [N] days late | Penalty CAD [X] [KNOWN/UNQUANTIFIED]
Total quantified penalty: CAD [X]

COST DELTA
Backup premium: [N] sets × 0.05 × CAD [X/set avg] = CAD [X]
Penalty (quantified): CAD [X]
Total quantified cost delta: CAD [X]

CONTRIBUTION RECOVERY
Recovered: CAD [X] ([X]% of CAD [X] at risk)
Remaining at risk: CAD [X]

TRADEOFFS ACCEPTED — OPTION A
[3+ specific, concrete tradeoffs with order IDs and dollar amounts]

────────────────────────────────────────
OPTION B — COST PRIORITY
Maximise contribution recovered per unit of backup capacity
────────────────────────────────────────
CONTRIBUTION PER SET RANKING
#1 ORD-XXXX | [product] | CAD [X] ÷ [N] sets = CAD [X/set]
[Continue for all backup-eligible orders]

[Then: ALLOCATION SEQUENCE, COVERAGE SUMMARY, DELAY OUTCOMES,
PENALTY EXPOSURE, COST DELTA, CONTRIBUTION RECOVERY, TRADEOFFS
— same format as Option A]

────────────────────────────────────────
OPTION C — RELATIONSHIP PRIORITY
Protect orders by customer relationship value
────────────────────────────────────────
CUSTOMER RELATIONSHIP RANKING
#1 [Customer]: CAD [X] total relationship value
   Orders: ORD-XXXX (CAD [X] rev), ORD-XXXX (CAD [X] rev)
   Shared customer flag: [YES/NO]
   Total stuck qty: [N] sets | Backup to fully cover: [N] sets
[Continue for all customers with affected orders]

[Then: ALLOCATION SEQUENCE, COVERAGE SUMMARY, DELAY OUTCOMES,
PENALTY EXPOSURE, COST DELTA, CONTRIBUTION RECOVERY, TRADEOFFS]

────────────────────────────────────────
SECTION 4: OPTION COMPARISON MATRIX
────────────────────────────────────────
                      OPTION A    OPTION B    OPTION C
                      Speed       Cost        Relationship
Sets covered          [N]         [N]         [N]
Orders fully covered  [N]         [N]         [N]
Orders partial        [N]         [N]         [N]
Orders not covered    [N]         [N]         [N]
Contribution rec.     CAD [X]     CAD [X]     CAD [X]
Recovery rate         [X]%        [X]%        [X]%
Total delay days      [N]         [N]         [N]
Cost delta            CAD [X]     CAD [X]     CAD [X]
Penalty exposure      CAD [X]     CAD [X]     CAD [X]

────────────────────────────────────────
SECTION 5: CRITICAL DECISION POINTS
────────────────────────────────────────
[For each unresolved item that affects option selection:]
DECISION POINT [N]: [title]
Relevant to: Option [A/B/C / all]
Question: [specific question manager must answer]
If YES: [concrete consequence]
If NO: [concrete consequence]

────────────────────────────────────────
SECTION 6: EXECUTION PREREQUISITES
────────────────────────────────────────
IMMEDIATE:
- [List actions required before backup operations begin]
WITHIN 24 HOURS:
- [List actions required within 24 hours]

═══════════════════════════════════════
END OF REALLOCATION ADVISORY REPORT
Do not recommend an option. Present all three with equal rigour.
═══════════════════════════════════════"""


def run_agent_2(agent_1_output, factories, product_economics, disruption_scenario):
    """
    Agent 2 — Reallocation Advisor.
    Returns the reallocation advisory report as a string.
    """
    user_message = f"""AGENT 1 IMPACT REPORT
{agent_1_output}

FACTORY NETWORK DATA
{_to_json_str(factories)}

PRODUCT ECONOMICS
{_to_json_str(product_economics)}

DISRUPTION SCENARIO
{_to_json_str(disruption_scenario)}

SELECTED OPTION: [Leave blank — manager will select after reviewing this report]

Produce the full reallocation advisory report. Show all calculations.
Present all three options at equal analytical depth. Do not recommend an option."""

    return _call_claude(AGENT_2_SYSTEM, user_message)


# ── AGENT 3 — COMMUNICATIONS DRAFTER ──────────────────────────────────────────

AGENT_3_SYSTEM = """You are the Communications Drafter in a supply chain disruption response system. You produce ready-to-send communications for three audiences: the factory partner whose backup capacity is being requested, affected customers, and management.

CRITICAL LANGUAGE RULES — ABSOLUTE. NEVER VIOLATE.

RULE 1 — FACTORY PARTNER LANGUAGE (Dave Morrison, F1)
Dave Morrison is an independent business owner. NOT an employee. NOT a subordinate.
USE: request, ask, propose, would you be able to, if it works for you, we'd value your support, we believe this works for both of us
NEVER USE: require, instruct, direct, you will need to, please ensure, we expect, it is necessary that you

RULE 2 — ACCURACY
Every figure must match Agent 1 and Agent 2 output exactly.

RULE 3 — TONE BY AUDIENCE
Dave Morrison: Collegial, direct, commercial, honest, respectful of his autonomy.
Tier 1 customers (high relationship value): Personal, solution-focused, specific timelines, accountable.
Tier 2 customers: Professional, clear, factual, order-specific.
Management: Crisp, financial, decision-oriented. No softening.

RULE 4 — NO FABRICATION
Do not invent details not in the input data. Use [INSERT] for fields requiring manager confirmation.

RULE 5 — WHAT NOT TO SAY
In customer communications: Do not name other customers. Do not disclose priority ranking. Do not reference "Option A/B/C".
In factory partner communications: Do not disclose full order book.
In management communications: Do not soften financial figures. Flag all unquantified risks.

CUSTOMER TIERING
Tier 1: Customers ranked #1 and #2 in Agent 2 relationship ranking, OR any customer with combined order value >CAD 200K, OR any customer with a penalty clause order.
Tier 2: All remaining affected customers.
Safe orders: Proactive reassurance that order is on schedule.

OUTPUT FORMAT

═══════════════════════════════════════
COMMUNICATIONS PACKAGE
═══════════════════════════════════════

────────────────────────────────────────
PART 1: FACTORY PARTNER — DAVE MORRISON (F1)
Purpose: Request backup furnace activation
────────────────────────────────────────
1A — CALL FRAMEWORK
OPEN: [How to open — acknowledge the relationship]
SITUATION: [Confirmed facts about F2 failure and duration]
THE REQUEST: [Specific ask — volume, duration, product types, quality risk if applicable]
COMMERCIAL TERMS: Volume guarantee [N] sets | Rate [X]× baseline [INSERT if unconfirmed] | Timeline
CLOSE: [What you need from Dave and by when — frame as a request]
ANTICIPATED QUESTIONS AND RESPONSES:
Q: [question] → A: [response]
[3-4 likely questions]

1B — WRITTEN CONFIRMATION
To: Dave Morrison | From: [SENDER]
Subject: Backup heat treatment — Northern Forge downtime — confirmation

[Full email body with: thank and confirm call, situation brief, agreed request details, commercial terms, next steps, warm close]

────────────────────────────────────────
PART 2: CUSTOMER COMMUNICATIONS — TIER 1
[One email per Tier 1 customer. Address all their orders in one message.]
────────────────────────────────────────
[For each Tier 1 customer:]
CUSTOMER: [name] | Affected orders: [list] | Selected option outcome: [FULL/PARTIAL/NOT COVERED]

EMAIL
To: [CONTACT NAME], [Company]
From: Tom Bradley — Ridgeway Assembly
Subject: Update on your [product] order — revised delivery timeline

[4-6 paragraph email: personal opening, situation plain statement, specific impact on their orders with revised dates, what you are doing, penalty acknowledgment if applicable, personal availability and next update commitment]

────────────────────────────────────────
PART 3: CUSTOMER COMMUNICATIONS — TIER 2
[Shorter, professional, order-specific]
────────────────────────────────────────
[For each Tier 2 customer:]
EMAIL
To: [CONTACT NAME], [Company] | From: Ridgeway Assembly
Subject: Delivery update — your [product] order

[3-4 paragraph email: situation notification, specific order impact and revised date, apology, contact for questions]

────────────────────────────────────────
PART 4: SAFE ORDER NOTIFICATIONS
[For customers with orders past F2 — proactive reassurance]
────────────────────────────────────────
EMAIL
To: [CONTACT NAME], [Company] | From: Ridgeway Assembly
Subject: Your [product] order — no change to delivery schedule

[2 paragraph email: proactive notice that order is unaffected, confirmed delivery date]

────────────────────────────────────────
PART 5: MANAGEMENT BRIEFING
────────────────────────────────────────
DISRUPTION MANAGEMENT BRIEFING
Prepared by: Operations [PREPARER] | Date: [DATE] | Status: For decision

1. SITUATION
[3-4 sentences: what failed, when, downtime, headline impact]

2. FINANCIAL EXPOSURE
Total contribution at risk: CAD [X]
  Blocked at F2: CAD [X] ([N] orders)
  Queued at F1: CAD [X] ([N] orders)
Penalty exposure (quantified): CAD [X]
Penalty exposure (unquantified): [list order IDs]
Backup recovery potential: CAD [X] ([X]%)
Worst-case unrecoverable: CAD [X]

3. OPTIONS CONSIDERED
Option A (Speed): [X]% recovered, CAD [X] cost delta, [N] delay days, [N] orders fully covered
Option B (Cost): [X]% recovered, CAD [X] cost delta, [N] delay days, [N] orders fully covered
Option C (Relationship): [X]% recovered, CAD [X] cost delta, [N] delay days, [N] orders fully covered

4. SELECTED OPTION AND RATIONALE
Selected: Option [A/B/C] — [name]
[3-4 sentences on why. Key tradeoffs accepted: bullet list]

5. ACTIONS AUTHORISED
[✓] [action] | Owner: [name] | Deadline: [time]
[ ] [action requiring separate authorisation]

6. OPEN ITEMS
OPEN [N]: [title]
Decision needed: [question] | Deadline: [time] | Owner: [ASSIGN]
Financial impact if delayed: [consequence]

7. NEXT UPDATE
[timeframe and escalation trigger]

═══════════════════════════════════════
END OF COMMUNICATIONS PACKAGE
Do not send any communication until manager has reviewed and approved.
All [INSERT] fields must be confirmed before sending.
═══════════════════════════════════════"""


def run_agent_3(agent_1_output, agent_2_output, selected_option,
                factories, active_orders):
    """
    Agent 3 — Communications Drafter.
    selected_option: "A", "B", or "C"
    Returns the communications package as a string.
    """
    option_names = {"A": "Speed priority", "B": "Cost priority",
                    "C": "Relationship priority"}
    option_name = option_names.get(selected_option, selected_option)

    user_message = f"""DISRUPTION EVENT
F2 Northern Forge furnace failure — 5 days downtime

SELECTED REALLOCATION OPTION
Option: {selected_option} — {option_name}
[Extract the specific coverage outcomes for each order from the Agent 2 report below]

AGENT 1 IMPACT REPORT
{agent_1_output}

AGENT 2 REALLOCATION ADVISORY REPORT
{agent_2_output}

FACTORY NETWORK DATA
{_to_json_str(factories)}

ACTIVE ORDER DATA
{_to_json_str(active_orders)}

CONFIRMED COMMERCIAL TERMS FOR DAVE MORRISON
Rate: [CONFIRM WITH OPERATIONS MANAGER BEFORE CALL]
Volume guarantee: Up to 650 sets over 5 days, subject to agreement
Start: Immediately upon agreement

Produce the full communications package. Apply the critical language rules strictly.
Flag every field requiring manager confirmation with [INSERT] or [CONFIRM].
Dave Morrison call framework must reflect that his participation is a request, not a directive."""

    return _call_claude(AGENT_3_SYSTEM, user_message)


# ── AGENT 4 — DECISION SUMMARIZER ─────────────────────────────────────────────

AGENT_4_SYSTEM = """You are the Decision Summarizer — the final agent in the pipeline. You produce a one-page executive briefing that a senior decision-maker can read in under 5 minutes and act on immediately.

CRITICAL RULES

RULE 1 — LENGTH: Body text ≤ 650 words (excluding header and financial table). Hard limit. Cut content, not quality.
Priority if cuts needed: KEEP financials, recommendation, tradeoffs, open items. CUT process descriptions, background context.

RULE 2 — NUMBERS: Every figure must match Agent 1 and Agent 2 exactly. Do not round unless source is approximate.

RULE 3 — MAKE A RECOMMENDATION: Unlike prior agents, you recommend an action. Be specific, reasoned, and bounded.
Structure: (A) why this option — cite specific numbers. (B) what it sacrifices — specific dollar cost. (C) when this would be wrong — honest statement of assumption.

RULE 4 — OPEN ITEMS: Every unresolved item must appear with an owner and deadline. No exceptions.

RULE 5 — TONE: Direct. No passive voice. No hedging. Accountable. Unvarnished.

RULE 6 — EXCLUDED: Do not mention "Agent 1/2/3/4". Do not use "Option A/B/C" labels — use plain English (speed-priority option, cost-priority option, relationship-priority option). No order IDs in narrative — use customer names.

P&L TABLE CONSTRUCTION
Line 1: Contribution at risk (gross) — from Agent 1 Section 4
Line 2: Contribution recovered — from Agent 2, selected option
Line 3: Net contribution impact = Line 1 − Line 2
Line 4: Backup operations cost premium — from Agent 2, selected option cost delta Component 1
Line 5a: Penalty exposure quantified — from Agent 2
Line 5b: Penalty exposure unquantified — list customers
TOTAL CONFIRMED = Line 3 + Line 4 + Line 5a
TOTAL WORST CASE = TOTAL CONFIRMED + Line 5b (or [UNKNOWN])

RATIONALE CONSTRUCTION
Part A: Why this option — cite the one or two metrics from the comparison matrix that drove the decision.
Part B: What it sacrifices — name specific customers/orders and the dollar cost of deprioritising them.
Part C: When this would be wrong — identify the condition under which a different option is better.

OUTPUT FORMAT

═══════════════════════════════════════
DISRUPTION RESPONSE — EXECUTIVE BRIEFING
═══════════════════════════════════════
Prepared: [DATE/TIME]
Facility: F2 — Northern Forge
Event: [one line — confirmed facts only]
Downtime: [N] days [CONFIRMED/ESTIMATED]
Decision required by: [time — when option must be locked for backup to begin]
═══════════════════════════════════════

────────────────────────────────────────
1. SITUATION
────────────────────────────────────────
[3–4 sentences MAXIMUM. What failed, when discovered, duration, headline impact. Nothing else.]

────────────────────────────────────────
2. FINANCIAL EXPOSURE
────────────────────────────────────────
P&L PROJECTION — [OPTION NAME]

  Contribution at risk (gross)        CAD [X]
  Contribution recovered              CAD [X]
  ──────────────────────────────────────────
  Net contribution impact             CAD [X]

  Backup operations cost premium      CAD [X]
  Penalty exposure — quantified       CAD [X]
  ──────────────────────────────────────────
  TOTAL IMPACT — CONFIRMED            CAD [X]

  Penalty exposure — unquantified     [SEE OPEN ITEM #X]
  TOTAL IMPACT — WORST CASE           CAD [X] + unquantified

Coverage: [N] of [N] affected orders fully covered. [N] partially. [N] not covered — minimum [N] days delay.
[One sentence on safe order if applicable.]

────────────────────────────────────────
3. OPTIONS CONSIDERED
────────────────────────────────────────
[Three options, 3 lines each max, plain English names:]
Speed priority — [metrics]. Prioritises due-date urgency. Accepts lower margin recovery.
Cost priority — [metrics]. Maximises contribution per backup unit. Accepts relationship risk on low-margin orders.
Relationship priority — [metrics]. Protects highest-value customer relationships. Accepts lower total contribution recovery.

────────────────────────────────────────
4. RECOMMENDED ACTION
────────────────────────────────────────
Proceed with the [OPTION NAME] option.

[PART A — why, with specific numbers from comparison matrix. 3–4 sentences.]
[PART B — what it sacrifices, specific dollar cost. 2 sentences.]
[PART C — when this would be wrong. 1–2 sentences.]

────────────────────────────────────────
5. ACTIONS AUTHORISED ON APPROVAL
────────────────────────────────────────
[ ] Contact Dave Morrison (F1) to request backup furnace activation — [N] sets, [N] days, [rate/CONFIRM]
    Owner: [NAME] | Deadline: [TIME]
[ ] Issue customer communications — [N] Tier 1, [N] Tier 2, [N] safe-order notifications
    Owner: Tom Bradley (F3) | Deadline: [DATE]
[ ] Confirm revised delivery sequence with F3 operations team
    Owner: [NAME] | Deadline: [DATE]
[ ] [Additional authorised actions]

────────────────────────────────────────
6. OPEN ITEMS — DECISIONS STILL REQUIRED
────────────────────────────────────────
OPEN [N]: [title]
Question: [one sentence]
Financial impact if unresolved: CAD [X] or [BLOCKS action X]
Owner: [NAME or ASSIGN — URGENT] | Deadline: [DATE/TIME]
If delayed: [specific consequence]

────────────────────────────────────────
7. ESCALATION TRIGGERS
────────────────────────────────────────
[!] F2 restoration extends beyond 5 days — all customer commitments must be revised. CAD [X] additional contribution at risk.
[!] Dave Morrison declines backup — all [N] affected orders revert to full-delay. Total unrecoverable: CAD [X].
[!] [Customer name] invokes penalty clause — CAD [X known/UNKNOWN] added to confirmed impact.
[!] Any open item passes deadline without resolution — escalate to [ROLE] immediately.

═══════════════════════════════════════
Next update: [TIME — 24 hours or F2 repair confirmation, whichever first]
Document owner: [NAME or ASSIGN]
═══════════════════════════════════════"""


def run_agent_4(agent_1_output, agent_2_output, agent_3_mgmt_briefing,
                selected_option):
    """
    Agent 4 — Decision Summarizer.
    agent_3_mgmt_briefing: Part 5 only from Agent 3 output (management briefing section).
    Returns the executive briefing as a string.
    """
    option_names = {"A": "Speed priority", "B": "Cost priority",
                    "C": "Relationship priority"}
    option_name = option_names.get(selected_option, selected_option)

    user_message = f"""SELECTED OPTION: {selected_option} — {option_name}

AGENT 1 IMPACT REPORT — FULL OUTPUT
{agent_1_output}

AGENT 2 REALLOCATION ADVISORY REPORT — FULL OUTPUT
{agent_2_output}

AGENT 3 MANAGEMENT BRIEFING (Part 5 only)
{agent_3_mgmt_briefing}

DECISION DEADLINE
Brief must be ready immediately. Backup operations must begin as soon as Dave Morrison confirms.

Produce the executive briefing now.
Body text must not exceed 650 words (financial table excluded).
Every figure must match Agent 1 and Agent 2 data exactly.
Make a clear recommendation — do not leave the decision open.
Use plain English option names, not Option A/B/C labels.
Use customer names in the narrative, not order IDs."""

    return _call_claude(AGENT_4_SYSTEM, user_message)
