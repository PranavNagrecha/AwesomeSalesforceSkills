# Agent Topic Design — Gotchas

## 1. Broad Subagent Names Hide Weak Routing

Names like `Support` or `General Help` feel useful but give the agent almost no real boundary.

Avoid it:
- Name subagents (called topics before April 2026) by capability.
- Make activation and exclusion signals explicit.

## 2. Subagent Count Becomes A Reliability Issue

As the subagent set grows, routing quality drops if boundaries stay fuzzy.

Avoid it:
- Keep the direct subagent set small.
- Introduce a topic selector when the broader domain has too many candidate subagents.

## 3. Handoff Logic Cannot Be Bolted On Later

If escalation rules are missing, the agent will try to do work it should hand off.

Avoid it:
- Define handoff criteria inside the subagent design.
- State what context the subagent should collect before escalating.

## 4. Action Lists Can Distort Subagent Boundaries

Teams sometimes keep a bad subagent because it is the only place where certain actions are attached.

Avoid it:
- Fix the subagent boundary first.
- Then reassign the action set to the right capability.
