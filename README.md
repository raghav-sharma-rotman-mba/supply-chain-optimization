# Supply Chain Resilience Dashboard
### Rotman MBA 2027 · GenAI Applications in Business

---

## Setup (one time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."

# On Windows:
# set ANTHROPIC_API_KEY=sk-ant-...
```

Get your API key at: https://console.anthropic.com
Estimated total API cost for full demo run: CAD 5–15.

---

## Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501

---

## File structure

```
supply_chain_dashboard/
├── app.py                    # Main Streamlit dashboard (all 3 modes)
├── agents.py                 # Four-agent Claude pipeline
├── factory_network_data.py   # Verified data model — all 5 data structures
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## How to use the dashboard

### Baseline mode
- Default view on startup
- Shows factory network, production flow, order tracker
- Filter orders by factory, stage, or category

### Disruption mode
- Click **"Trigger F2 Disruption"** button (top right)
- F2 card turns red, affected orders flagged with delay estimates
- Backup capacity panel shows F1 furnace math
- Click **"Run AI Pipeline"** to launch Agents 1 and 2

### Response mode (after pipeline runs)
- **Tab 01** — Agent 1 impact report: blocked vs queued orders, contribution at risk, triage flags
- **Tab 02** — Agent 2 advisory: 3 reallocation options with comparison matrix
  - Select Option A (Speed), B (Cost), or C (Relationship)
  - Click **"Run Agents 3 & 4"** to generate communications and executive brief
- **Tab 03** — Agent 3 communications: Dave Morrison call framework, customer emails, management briefing
- **Tab 04** — Agent 4 executive brief: P&L projection, recommendation, open items

---

## Swapping in your actual data

Replace the inline data in `factory_network_data.py` with:

```python
import json

with open("factories.json") as f:
    FACTORIES = json.load(f)
# repeat for other files
```

Or run `python factory_network_data.py` to export all 5 JSON files,
then swap to json.load() calls.

---

## Notes

- Agent 3 and 4 only run after an option is selected in Tab 02
- All [INSERT] and [CONFIRM] fields in Agent 3 output require
  manager review before sending
- The Lakeland Transport triage tension (ORD-2607 vs ORD-2601)
  surfaces automatically in Agent 1 Section 5 and Agent 2 Decision Point 1
