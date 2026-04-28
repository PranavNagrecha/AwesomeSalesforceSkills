---
name: dataraptor-transform-optimization
description: "Use when DataRaptor Transform operations are slow, hit governor limits, or use Apex where formula fields would suffice. Covers formula vs Apex expressions, bulk transform sizing, and chained transform composition. Triggers: 'dataraptor transform slow', 'dataraptor formula vs apex', 'dataraptor bulk transform', 'dr governor limit'. NOT for DataRaptor Extract or Load performance."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "dataraptor transform takes too long"
  - "should I use a formula or apex expression in a dataraptor"
  - "dataraptor bulk transform size limit"
  - "chained dataraptor transforms are confusing"
  - "transform hits cpu time limit"
tags:
  - omnistudio
  - dataraptor
  - performance
  - transform
  - bulkification
inputs:
  - "current DataRaptor Transform definition"
  - "input payload size and shape"
  - "downstream consumers and required output shape"
outputs:
  - "optimized transform definition"
  - "formula vs Apex decision per field"
  - "bulkification recommendations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# DataRaptor Transform Optimization

DataRaptor Transforms look simple in the designer but can silently dominate an Integration Procedure's runtime. A Transform can evaluate hundreds of formula fields per row, invoke Apex for each, and run through custom JavaScript functions — and it does this in the synchronous IP context, counting against the same governor limits as the calling Apex.

The two decisions that determine Transform performance are per-field: **formula vs Apex expression** and **row-by-row vs bulk**. Formulas run in the Transform engine with no per-row overhead; Apex expressions cross a boundary and count toward CPU time. Bulk transforms process the whole input array once; row-by-row transforms re-enter the evaluator per row.

Optimizing a Transform is less about rewriting logic and more about picking the right evaluator per field and collapsing avoidable chains.

---

## Before Starting

- Capture the Transform's average input size (rows × fields) in production.
- Capture wall-clock time for a representative execution from debug logs.
- List every field mapping and whether it uses formula, Apex, or JavaScript.

## Core Concepts

### Evaluator Costs

| Evaluator | Per-row cost | Governor hit |
|---|---|---|
| Formula (native) | Low | None |
| Apex expression | Medium | CPU time + possible SOQL |
| JavaScript | Medium | CPU time |
| Remote call (HTTP action in a chained transform) | High | Callout, CPU, apex heap |

Rule of thumb: default to formula; use Apex only when the logic truly needs it (dynamic sObject access, complex regex, crypto).

### Bulk vs Row-By-Row

A bulk Transform receives the full input array and iterates it internally. A row-by-row Transform is invoked per row — each invocation re-parses mappings, re-resolves references, and re-enters the evaluator. The designer does not always make this choice obvious; inspect the XML or JSON export to confirm.

### Chained Transforms

When multiple Transforms run in sequence (e.g. normalize → enrich → shape), each materializes its intermediate output. Collapsing two adjacent Transforms into one saves memory and evaluation cost if the logic composes cleanly.

### CPU Time In Synchronous IPs

An IP that runs in a synchronous context inherits the caller's 10,000 ms CPU limit. Transforms silently accumulate milliseconds; profiling matters.

---

## Common Patterns

### Pattern 1: Formula-First Default

Start every new field mapping in formula mode. Promote to Apex only when you hit something formula cannot do (dynamic field access, callouts, complex string manipulation).

### Pattern 2: Bulk Transform For List Inputs

If the input is an array, confirm the Transform is set to bulk. Row-by-row over 200 rows can be 5-10× slower with no functional difference.

### Pattern 3: Collapse Adjacent Transforms

If two consecutive Transforms share the same input scope, merge them. The combined transform is usually more readable, not less.

### Pattern 4: Projection Before Transform

If the source payload is large but only a few fields are used, add a projection step (DataRaptor Extract with explicit field list) before the Transform to reduce the payload size.

### Pattern 5: Hoist Apex Logic Into Invocable Method

When the same Apex expression fires per row, consider replacing the Transform with a single Invocable Apex that receives the full array and returns transformed output in one call.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple arithmetic or string concat | Formula | Fastest, no governor cost |
| Dynamic field access or complex regex | Apex expression | Formula cannot express it |
| Same Apex fires N times per row | Bulk Invocable Apex | Collapses N calls to 1 |
| Chained transforms with no consumer between them | Merge | Saves materialization cost |
| Large input, few fields used | Pre-project then transform | Reduces payload size |
| JavaScript function for non-trivial logic | Reconsider — Apex or formula usually better | JS is harder to test and slower |

## Review Checklist

- [ ] Every field mapping uses the cheapest sufficient evaluator.
- [ ] Array-input Transforms are set to bulk.
- [ ] Chains of adjacent Transforms have been reviewed for merging.
- [ ] Input payload is projected before the Transform if large.
- [ ] Per-row Apex has been considered for replacement with bulk Invocable.

## Recommended Workflow

1. Profile — capture current wall-clock and CPU time from IP debug output.
2. Classify — tag each field mapping as formula, Apex, or JavaScript.
3. Promote to formula — rewrite trivial Apex/JS expressions as formulas.
4. Switch to bulk — verify the Transform operates on arrays natively.
5. Merge chains — collapse adjacent transforms that share scope.
6. Re-profile — compare before/after numbers; document gains.

---

## Salesforce-Specific Gotchas

1. JavaScript evaluator blocks cannot share state across rows — any "memoize" pattern re-runs.
2. Apex expressions within a Transform still count against the parent IP's SOQL and DML limits.
3. Bulk mode is opt-in; the designer default varies across OmniStudio versions.
4. Chained Transforms materialize intermediate JSON — large arrays balloon heap use.
5. Formula errors produce silent empty values, not exceptions; add validation downstream.

## Proactive Triggers

- Transform runs row-by-row over an array input → Flag High.
- Apex expression fires per row with the same logic → Flag High.
- Three or more chained Transforms with no consumer between → Flag Medium.
- Transform CPU time > 1000 ms in debug log → Flag High.
- Formula producing empty value on malformed input → Flag Medium.

## Output Artifacts

| Artifact | Description |
|---|---|
| Field-evaluator audit | Per-field current vs recommended evaluator |
| Bulk-mode audit | Per-Transform bulk/row status |
| Chain-merge plan | Which adjacent Transforms can merge |

## Related Skills

- `omnistudio/dataraptor-patterns` — general DR design.
- `omnistudio/omnistudio-performance` — IP/OS performance overall.
- `omnistudio/integration-procedures` — IP step design.
- `apex/bulk-patterns-and-governor-limits` — Apex bulkification.
