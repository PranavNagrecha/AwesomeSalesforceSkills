---
name: roll-up-summary-alternatives
description: "Use when native Roll-Up Summary fields are not enough and the design needs Flow, Apex aggregate, or DLRS-style alternatives for lookup or advanced summary scenarios. Triggers: 'roll up summary on lookup', 'DLRS', 'aggregate trigger', 'summary count on parent', 'roll-up limitation'. NOT for ordinary master-detail roll-up fields that fit native limits without extra design tradeoffs."
category: data
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - roll-up-summary
  - dlrs
  - aggregate-soql
  - lookup-rollup
  - parent-child-summary
triggers:
  - "how do I do a roll up summary on a lookup relationship"
  - "DLRS versus Flow versus Apex rollup"
  - "count child records on parent in Salesforce"
  - "native roll up summary limitations"
  - "aggregate trigger for parent totals"
inputs:
  - "relationship type such as master-detail or lookup"
  - "summary type such as count, sum, min, max, or filtered total"
  - "data volume, real-time expectation, and allowed tooling"
outputs:
  - "summary-pattern recommendation"
  - "review findings for scale and maintenance risk"
  - "implementation sketch for Flow, Apex, or native summary"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Roll Up Summary Alternatives

Use this skill when stakeholders say "just add a roll-up field" and the platform answer is "not natively, at least not that way." Native Roll-Up Summary fields are excellent when the relationship and limits fit, but many orgs need lookup-based summaries, filtered calculations, or higher-volume behavior that changes the right implementation choice.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the relationship master-detail or lookup?
- Does the summary need real-time accuracy, near-real-time, or just eventual consistency?
- Is the org comfortable with code, managed or open-source tooling, or declarative-only approaches?

---

## Core Concepts

### Native Roll-Up Summary Is The First Choice

If the relationship is master-detail and the supported summary behavior meets the requirement, keep it native. Native summary fields are easier to operate than custom recalculation logic.

### Lookup Rollups Need An Alternative Pattern

Once the relationship is lookup, teams move into tradeoff territory. Flow, Apex aggregate logic, or a tool such as Declarative Lookup Rollup Summaries can solve the gap, but they differ in scale, maintainability, and operational visibility.

### Volume And Recalculation Style Matter

Low-volume event-driven updates are different from large data backfills or high-churn parent-child relationships. The implementation needs to match both normal traffic and recalculation scenarios.

### Summary Logic Is Data Architecture

Every rollup decision affects locking, recursion, reporting, and user trust in totals. A "simple counter field" can still become a reliability problem if the design ignores bulk behavior.

---

## Common Patterns

### Native Roll-Up Summary Field

**When to use:** Master-detail relationship and supported summary logic.

**How it works:** Use the platform feature and avoid custom recalculation paths.

**Why not the alternative:** Custom logic adds maintenance cost with no benefit when native fit is available.

### Flow-Maintained Summary

**When to use:** Lookup relationship, moderate volume, and declarative ownership is preferred.

**How it works:** Record-triggered automation recalculates or adjusts a parent summary field with clear bulk and fault handling.

### Apex Aggregate Rollup

**When to use:** High-volume or complex filtered summaries need stronger control and testing.

**How it works:** Collect affected parent IDs, run aggregate SOQL once, and update parent records in bulk.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Master-detail and native summary fits | Native roll-up summary | Lowest maintenance and strongest platform fit |
| Lookup relationship with moderate volume | Flow or DLRS-style approach | Declarative option may be sufficient |
| Complex filter logic or higher volume | Apex aggregate pattern | Better control over recalculation and scale |
| Team wants no-code but needs lookup summaries at scale | Re-evaluate operational ownership carefully | Tooling convenience does not remove recalculation complexity |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Native roll-up summary was rejected for a real reason, not habit.
- [ ] Lookup versus master-detail constraints are explicit.
- [ ] Recalculation path is bulk-safe and tested for backfill scenarios.
- [ ] Parent locking and recursion risk were considered.
- [ ] Reporting expectations match the chosen summary model.
- [ ] The org has an owner for maintenance and re-sync operations.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Lookup rollups are not a free native feature** - once the relationship is not master-detail, you own more tradeoffs.
2. **Backfills expose weak designs** - a pattern that works per record can fail badly during migration or data cleanup.
3. **Parent locking can become the bottleneck** - summary updates concentrate writes on the same parent records.
4. **A declarative option still has operating cost** - someone must own failures, recalcs, and drift correction.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Summary decision | Recommendation for native, Flow, Apex, or DLRS-style pattern |
| Rollup review | Findings on scale, locking, and recalculation risk |
| Bulk recalculation pattern | Aggregate-based implementation guidance for parent totals |

---

## Related Skills

- `apex/trigger-framework` - use when the rollup implementation is becoming trigger-architecture work.
- `apex/recursive-trigger-prevention` - use when parent-summary writes are causing re-entry problems.
- `data/multi-currency-and-advanced-currency-management` - use when the rollup requirement depends on currency conversion behavior.
