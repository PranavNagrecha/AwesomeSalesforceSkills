# Agent Topic Design — Gotchas

## 1. Broad Topic Names Hide Weak Routing

Names like `Support` or `General Help` feel useful but give the agent almost no real boundary.

Avoid it:
- Name topics by capability.
- Make activation and exclusion signals explicit.

## 2. Topic Count Becomes A Reliability Issue

As the topic set grows, routing quality drops if boundaries stay fuzzy.

Avoid it:
- Keep the direct topic set small.
- Introduce a topic selector when the broader domain has too many candidate topics.

## 3. Handoff Logic Cannot Be Bolted On Later

If escalation rules are missing, the agent will try to do work it should hand off.

Avoid it:
- Define handoff criteria inside the topic design.
- State what context the topic should collect before escalating.

## 4. Action Lists Can Distort Topic Boundaries

Teams sometimes keep a bad topic because it is the only place where certain actions are attached.

Avoid it:
- Fix the topic boundary first.
- Then reassign the action set to the right capability.
