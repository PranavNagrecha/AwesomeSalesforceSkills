---
name: apex-cpu-and-heap-optimization
description: "Use when diagnosing or preventing Apex CPU time and heap size problems, including nested-loop refactors, JSON memory pressure, string work, and `Limits.getCpuTime()` checkpoints. Triggers: 'CPU time limit exceeded', 'heap size too large', 'string concatenation', 'regex in loop', 'Limits.getCpuTime'. NOT for generic SOQL/DML governor-limit basics without a CPU or heap bottleneck."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
tags:
  - cpu-time
  - heap-size
  - limits-getcputime
  - string-optimization
  - json-memory
triggers:
  - "CPU time limit exceeded in Apex"
  - "heap size too large debugging"
  - "Limits.getCpuTime checkpoint usage"
  - "string concatenation in loops"
  - "regex or JSON causing performance issues"
inputs:
  - "exact exception or hotspot location if known"
  - "whether the issue is CPU-heavy, heap-heavy, or both"
  - "transaction type and approximate data volume"
outputs:
  - "CPU/heap optimization recommendation"
  - "review findings for high-cost patterns"
  - "remediation plan for memory and compute hotspots"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when Apex is already bulkified but still failing because the transaction does too much compute or holds too much memory. CPU and heap problems are often caused by algorithm shape, payload handling, or repeated expensive work rather than by the usual SOQL/DML mistakes alone.

## Before Starting

- Is the failure specifically CPU time, heap size, or a mixed symptom that needs profiling?
- What part of the transaction is hot: nested loops, JSON parsing, regex, logging, serialization, or object graph size?
- Can the work be reduced, chunked, cached, or moved to async rather than merely micro-optimized?

## Core Concepts

### CPU And Heap Fail For Different Reasons

CPU time is usually consumed by algorithmic cost: nested loops, repeated parsing, regex, sorting, or complex branching. Heap is usually consumed by retained data volume: large lists, maps, payloads, or serialized strings. A fix for one does not necessarily help the other.

### Algorithm Shape Beats Micro-Optimizing Syntax

Replacing nested loops with `Map<Id, SObject>` lookups or precomputed sets usually matters more than shaving tiny operations. The biggest gains often come from changing data structures and reducing repeated work.

### Large Payload Handling Is A Memory Problem First

JSON responses, long string concatenation, and large debug serialization can explode heap quickly. Chunking work, nulling references when no longer needed, and avoiding redundant copies often matter more than clever loops.

### Measure Before And After

`Limits.getCpuTime()` and lightweight checkpoints help identify where the transaction burns time. The same discipline applies to heap: understand what collections or payloads remain in memory and when they can be released.

## Common Patterns

### Map/Set Refactor For Nested Loops

**When to use:** CPU time is being spent in N x M record comparisons.

**How it works:** Build maps or sets once, then use constant-time lookups inside the loop.

**Why not the alternative:** Micro-tuning the loop body does little if the algorithm is still quadratic.

### Chunk Large Payload Work

**When to use:** Heap spikes during JSON parsing, serialization, or large-string processing.

**How it works:** Process smaller batches, avoid duplicate payload copies, and release references after use.

### Instrument With Lightweight Checkpoints

**When to use:** The hotspot is unclear.

**How it works:** Add temporary `Limits.getCpuTime()` checkpoints around suspect blocks and remove them after diagnosis.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| CPU time dominated by nested comparisons | Refactor with maps/sets | Algorithm change gives the biggest gain |
| Heap limit triggered by large payloads or strings | Reduce retained objects and process in chunks | Memory pressure is the actual bottleneck |
| Hotspot is unclear | Add temporary CPU checkpoints | Measure before refactoring blindly |
| Work is intrinsically heavy for one transaction | Move or split work into async chunks | Sometimes the right fix is architectural |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Nested loops and repeated expensive parsing are identified and challenged.
- [ ] Large payloads are not copied or serialized unnecessarily.
- [ ] Temporary checkpoints or profiling data support the optimization choice.
- [ ] Logging and debug output are not inflating heap or CPU cost.
- [ ] The chosen fix addresses the real bottleneck, not a secondary symptom.
- [ ] Async decomposition is considered when one transaction is simply too heavy.

## Salesforce-Specific Gotchas

1. **CPU and heap limits can come from different root causes in the same transaction** — treat them separately.
2. **Large debug or JSON serialization can become the problem** — diagnostics can make the incident worse.
3. **Nested loops over related record sets are classic CPU traps even after SOQL is bulkified** — the database is no longer the bottleneck.
4. **Nulling references helps only after the data is no longer needed** — memory discipline must match object lifetime.

## Output Artifacts

| Artifact | Description |
|---|---|
| CPU/heap review | Findings on hot algorithms, payload pressure, and bad memory habits |
| Optimization plan | Ordered remediations targeting the highest-cost patterns first |
| Checkpoint strategy | Temporary instrumentation guidance for locating hotspots |

## Related Skills

- `apex/governor-limits` — use when the problem still includes basic SOQL, DML, or row-limit mistakes.
- `apex/platform-cache` — use when repeated lookups can be avoided across transactions.
- `apex/async-apex` — use when the correct fix is to split heavy work into background execution.
