# Evidence and claim graph

## Goal

The framework’s primary product artifact is not prose. It is a validated graph of observations, claims, support, contradiction, confidence rationale, unknowns, and recommendations. Markdown is a rendering of that graph.

## Evidence node

An evidence node records:

- stable evidence ID;
- source type and source operation;
- product/run/target identity;
- observed/retrieved time and freshness;
- authority and directness;
- normalized payload or retained payload reference;
- source digest and upstream version;
- classification and redaction state;
- truncation, counts, and continuation;
- provenance chain.

Evidence is immutable within a run. New observations create new nodes.

## Claim node

A claim records:

- stable claim ID;
- type: observed fact, inference, recommendation, constraint, unknown;
- materiality;
- statement and structured subject/predicate/object where useful;
- support links and relation types;
- contradiction links;
- confidence label/score and rationale;
- status and reviewer disposition;
- applicable target and scope.

A platform principle can support an inference about behavior but cannot alone support a claim about target state.

## Relations

Minimum relations include:

- `supports`;
- `corroborates`;
- `contradicts`;
- `limits`;
- `derived_from`;
- `explains`;
- `requires`;
- `recommended_for`.

## Confidence

Confidence is computed from evidence coverage, authority, directness, freshness, completeness, target consistency, corroboration, and unresolved contradiction. Model self-reported confidence is advisory only.

A high-confidence material claim with no valid support is a release-blocking defect.

## Independent review

The reviewer attempts to invalidate the proposed graph:

- Are cited nodes present and target-compatible?
- Does the evidence actually support the claim?
- Is contradictory evidence omitted or minimized?
- Is a common cause overgeneralized from correlated symptoms?
- Is truncated/stale evidence treated as complete?
- Is the recommendation safe and within authority?
- Should the status or confidence be downgraded?

The review result can add unknowns, require evidence, split claims, reject recommendations, or change terminal status.

## Rendering

The final user view should be concise:

1. status and target;
2. what was observed;
3. likely causes with evidence IDs and confidence rationale;
4. affected components/users/automations as applicable;
5. ordered safe actions;
6. unknowns, contradictions, truncation, and limitations;
7. replay/report paths and run ID.

The graph remains available as JSON for audit, QA, and integrations.
