# Gotchas — Agent Metric Dashboards

## Gotcha 1: CSAT response bias

**What happens:** Only frustrated users answer the survey — CSAT looks terrible.

**When it occurs:** Opt-in survey only.

**How to avoid:** Sample randomly and weight responses; complement with LLM-as-judge.


---

## Gotcha 2: Deflection = 'user gave up'

**What happens:** No escalation because user closed the browser in frustration.

**When it occurs:** No session-end signal.

**How to avoid:** Combine deflection with CSAT + repeat-contact-rate; triangulate.


---

## Gotcha 3: Cost metric without model version

**What happens:** Cost/conversation changes overnight due to model upgrade.

**When it occurs:** Model upgrade mid-quarter.

**How to avoid:** Annotate the dashboard with model-version timeline.

