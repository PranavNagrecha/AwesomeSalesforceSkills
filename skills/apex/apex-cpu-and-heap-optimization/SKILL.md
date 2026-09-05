---
name: apex-cpu-and-heap-optimization
description: "Use when diagnosing or preventing Apex CPU time and heap size problems, including nested-loop refactors, JSON memory pressure, string work, and `Limits.getCpuTime()` checkpoints. Triggers: 'CPU time limit exceeded', 'heap size too large', 'string concatenation', 'regex in loop', 'Limits.getCpuTime', 'System.LimitException', 'Apex heap size too large', 'SOQL for loop', 'Database.Stateful heap', 'batch job fails on later chunks'. NOT for generic SOQL/DML governor-limit basics — use apex/governor-limits. NOT for runtime limit guard clauses — use apex/apex-limits-monitoring."
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
  - "cpu time isn't working"
  - "refactor nested loops in Apex to a Map"
  - "batch job fails on a later chunk but not the first"
  - "profile which method is burning the CPU budget in a trigger"
  - "assert CPU and heap headroom in an Apex test"
  - "managed package pushed my transaction over the CPU limit"
  - "scheduled Apex hit the 10,000 ms limit instead of 60,000"
  - "System.LimitException is not being caught by my try block"
  - "convert a SOQL query to a SOQL for loop to avoid heap"
  - "fix apex cpu time limit exceeded"
inputs:
  - "exact exception or hotspot location if known"
  - "whether the issue is CPU-heavy, heap-heavy, or both"
  - "transaction type and approximate data volume"
  - "whether the transaction is synchronous, batch/future, or scheduled"
  - "whether any managed package code runs in the same save order"
outputs:
  - "CPU/heap optimization recommendation"
  - "review findings for high-cost patterns"
  - "remediation plan for memory and compute hotspots"
  - "refactored class plus a bulk test asserting CPU and heap headroom"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when Apex is already bulkified but still failing because the transaction does too much compute or holds too much memory. CPU and heap problems are often caused by algorithm shape, payload handling, or repeated expensive work rather than by the usual SOQL/DML mistakes alone.

`standards/decision-trees/performance-tuning.md` routes here from **Q2 → Q3** ("CPU time exceeded" or "Heap size exceeded", then nested loops / JSON / string work). If the symptom is a *count* limit — too many SOQL queries, DML rows, callouts — that tree's **Q4** sends you to `apex/governor-limits` instead. Its **Rule 0** applies first: without a measurement you are guessing, so start at `apex/apex-performance-profiling` when the hotspot is unknown.

## Before Starting

- Is the failure specifically CPU time, heap size, or a mixed symptom that needs profiling?
- What part of the transaction is hot: nested loops, JSON parsing, regex, logging, serialization, or object graph size?
- Can the work be reduced, chunked, cached, or moved to async rather than merely micro-optimized?
- Which ceiling actually applies? Synchronous is 10,000 ms / 6 MB and asynchronous is 60,000 ms / 12 MB, but scheduled Apex runs on the synchronous pair.

## Questions to Ask Before Configuring

Ask these before changing a line; each one maps to a gotcha in `references/gotchas.md` that has already cost somebody a production incident.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which limit failed, in which context — sync, batch/future, or scheduled?" | The ceiling differs 6x between the columns, and scheduled Apex sits in the synchronous one despite being async | The real budget, so the target is a number rather than "faster" |
| "Do you have a measurement, or an exception message?" | An exception names the limit that broke first, not the largest consumer; the debug log's `LIMIT_USAGE_FOR_NS` block names all of them | A hotspot instead of a guess, and a baseline to prove the fix |
| "What is the record volume the failing transaction actually saw?" | CPU and heap defects are invisible at one record; the reported heap can even read `0` on a small run | The volume the bulk test must reproduce |
| "Does any managed package or other trigger run in the same save order?" | Certified packages share your CPU and heap even though they get their own SOQL and DML | Whether the fix is in your class at all, or is "move this async" |
| "Is any of this work retained across chunks or invocations — `Database.Stateful`, a static cache, a chained queueable?" | Governor counters reset per chunk while retained state does not, which is why batches fail late rather than early | The accumulator that has to be bounded |
| "What must still be true after the refactor — ordering, partial success, error reporting?" | Limit exceptions are uncatchable, so any "log the failure" design silently disappears | The error path that has to move before the expensive block |
| "Who consumes this transaction afterwards — a callout, a flow, another trigger?" | A fix that lands at 95% of the ceiling has no headroom for the next feature | The headroom fraction the test should assert |

What a proper optimization adds over just making it faster: a measured before/after in the same units the platform enforces, a bulk test that fails the build when the headroom is spent again, and an explicit record of which ceiling was traded for which.

## Core Concepts

### The budget, exactly

| Resource | Sync | Async (batch, future) | Runtime accessor |
|---|---|---|---|
| Maximum CPU time on Salesforce servers | 10,000 ms | 60,000 ms | `Limits.getCpuTime()` / `getLimitCpuTime()` |
| Total heap size | 6 MB | 12 MB | `Limits.getHeapSize()` / `getLimitHeapSize()` |
| Maximum execution time per Apex transaction | 10 minutes | 10 minutes | — |

Source: *Salesforce Developer Limits and Allocations Quick Reference*, Per-Transaction Apex Limits (`salesforce_app_limits_cheatsheet.txt` L89–L94), mirrored at `apexdev.txt` L19577–L19601. Two qualifiers that change how the table is used: scheduled Apex takes the synchronous column, and CPU and heap are the two ceilings a certified managed package does *not* get its own copy of. Both are worked through in `references/gotchas.md`.

### CPU And Heap Fail For Different Reasons

CPU time is usually consumed by algorithmic cost: nested loops, repeated parsing, regex, sorting, or complex branching. Heap is usually consumed by retained data volume: large lists, maps, payloads, or serialized strings. A fix for one does not necessarily help the other — and the platform's own heap remedy, the SOQL for loop, explicitly costs CPU.

### What Counts Toward CPU

The quick reference (`salesforce_app_limits_cheatsheet.txt` L170–L177) draws the line: application-server CPU spent in DML *is* counted; the portion of execution time spent in the database for DML, SOQL and SOSL is *not*, and neither is callout wait time. So a transaction can be slow for minutes with a small `getCpuTime()` reading, and a fast-looking bulk update can be the thing that exhausts it.

### Algorithm Shape Beats Micro-Optimizing Syntax

Replacing nested loops with `Map<Id, SObject>` lookups or precomputed sets usually matters more than shaving tiny operations. The biggest gains often come from changing data structures and reducing repeated work. `references/code-examples.md` §1–§2 is the before/after pair.

### Large Payload Handling Is A Memory Problem First

JSON responses, long string concatenation, and large debug serialization can explode heap quickly. Chunking work, nulling references when no longer needed, and avoiding redundant copies often matter more than clever loops. Apex `String` size is itself bounded by the heap limit (`apexdev.txt` L1275), and a collection has no item-count limit — only the heap bound (`apexdev.txt` L1431).

### Measure Before And After

`Limits.getCpuTime()` and lightweight checkpoints help identify where the transaction burns time. Bracket blocks, never iterations. `Limits.getHeapSize()` is documented as *approximate* (`apexrefguide.txt` L220711–L220722), so read it as headroom rather than accounting.

## Common Patterns

### Map/Set Refactor For Nested Loops

**When to use:** CPU time is being spent in N x M record comparisons.

**How it works:** Build maps or sets once, then use constant-time lookups inside the loop.

**Why not the alternative:** Micro-tuning the loop body does little if the algorithm is still quadratic.

### Chunk Large Payload Work

**When to use:** Heap spikes during JSON parsing, serialization, or large-string processing.

**How it works:** Process smaller batches, avoid duplicate payload copies, and release references after use. Inside one transaction the lever is the SOQL for loop, which iterates in batches of 200 (`apexdev.txt` L20271–L20285); across transactions it is Batch Apex, where limits reset for each `execute` (`apexdev.txt` L17709–L17710).

### Instrument With Lightweight Checkpoints

**When to use:** The hotspot is unclear.

**How it works:** Add `Limits.getCpuTime()` and `Limits.getHeapSize()` deltas around suspect blocks and report them through `templates/apex/ApplicationLogger.cls` so the measurement survives in production, where debug logs are usually off.

### Gate The Test On Headroom, Not On Green

**When to use:** Every time you land a CPU or heap fix.

**How it works:** A bulk test at 200+ records captures the deltas inside `Test.startTest()`/`Test.stopTest()` and asserts them against `Limits.getLimit*()` as a fraction. See `references/code-examples.md` §4.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| CPU time dominated by nested comparisons | Refactor with maps/sets | Algorithm change gives the biggest gain |
| Heap limit triggered by large payloads or strings | Reduce retained objects and process in chunks | Memory pressure is the actual bottleneck |
| Heap fixed with a SOQL for loop, now CPU fails | Move the chunking to Batch Apex | Each `execute` gets a fresh set of limits; a for loop does not |
| Hotspot is unclear | Add temporary CPU checkpoints | Measure before refactoring blindly |
| Your own delta is small but the transaction still fails | Look at the rest of the save order, then move work async | CPU and heap are shared with certified managed packages |
| Batch succeeds early and fails on a late chunk | Size-check the `Database.Stateful` accumulator | Retained instance state grows while counters reset |
| Work is intrinsically heavy for one transaction | Move or split work into async chunks | Sometimes the right fix is architectural |

## Recommended Workflow

1. **Establish the ceiling and the baseline.** Confirm the context (sync / batch / future / scheduled), read the applicable row from the budget table above, and capture a `LIMIT_USAGE_FOR_NS` block from a failing run — `references/examples.md` Example 3 has the command.
2. **Localise the cost.** Bracket suspect blocks with `Limits.getCpuTime()` / `getHeapSize()` deltas logged through `templates/apex/ApplicationLogger.cls`; never probe per iteration. If the hotspot is still unclear, stop here and use `apex/apex-performance-profiling`.
3. **Pick the lever from the shape, not the symptom.** Nested loops → Map indexing; retained query results → SOQL for loop or Batch Apex; payload copies → parse once, typed classes, no defensive clones. `standards/decision-trees/performance-tuning.md` Q3 lists the branch for each.
4. **Refactor against the canonical artifact.** Follow `references/code-examples.md` §2 (Map-indexed service), §3 (heap-safe batch), reusing `templates/apex/BaseService.cls`, `templates/apex/BaseSelector.cls` and `templates/apex/ApplicationLogger.cls` rather than inventing equivalents.
5. **Prove it at 200+ records.** Write or extend the bulk test from §4 with headroom assertions taken inside `Test.startTest()`/`Test.stopTest()`, seeded from `templates/apex/tests/TestDataFactory.cls`.
6. **Run the static check, then the org check.** `python3 scripts/check_apex_cpu_and_heap_optimization.py --manifest-dir <classes dir>`, then `sf apex run test --tests <TestClass> --result-format human`, then re-read the limit-usage block and compare it against the baseline from step 1.
7. **Record the trade.** State which ceiling you spent to buy the other one, and what headroom is left, in the change description — the next person's fix depends on it.

---

## Review Checklist

- [ ] The applicable ceiling (sync vs async, scheduled counted as sync) is written down before any change
- [ ] A baseline limit-usage reading exists from a failing bulk run, not a single-record repro
- [ ] Nested loops and repeated expensive parsing are identified and challenged.
- [ ] Large payloads are not copied or serialized unnecessarily.
- [ ] Temporary checkpoints or profiling data support the optimization choice.
- [ ] Checkpoints bracket blocks; none sit inside a hot loop without throttling
- [ ] Logging and debug output are not inflating heap or CPU cost.
- [ ] Any `Database.Stateful` member or static cache that survives a chunk is bounded
- [ ] Error handling does not depend on catching the limit exception or on a `finally` block
- [ ] A bulk test at 200+ records asserts CPU and heap headroom as a fraction of `Limits.getLimit*()`
- [ ] The headroom assertions are captured inside `Test.startTest()`/`Test.stopTest()`
- [ ] The chosen fix addresses the real bottleneck, not a secondary symptom.
- [ ] Async decomposition is considered when one transaction is simply too heavy.

## Salesforce-Specific Gotchas

1. **CPU and heap limits can come from different root causes in the same transaction** — treat them separately.
2. **Large debug or JSON serialization can become the problem** — diagnostics can make the incident worse.
3. **Nested loops over related record sets are classic CPU traps even after SOQL is bulkified** — the database is no longer the bottleneck.
4. **Nulling references helps only after the data is no longer needed** — memory discipline must match object lifetime.
5. **Certified managed packages share your CPU and heap** — they get their own SOQL and DML, not their own compute budget.
6. **Scheduled Apex gets the synchronous ceiling** — 10,000 ms, not 60,000 ms.
7. **`System.LimitException` is uncatchable and skips `finally`** — the log line you were counting on never runs.
8. **`Maximum heap size: 0` in a debug log means unmeasured, not clean.**

Full treatment, with sources, in `references/gotchas.md`.

## Output Artifacts

| Artifact | Description |
|---|---|
| CPU/heap review | Findings on hot algorithms, payload pressure, and bad memory habits |
| Optimization plan | Ordered remediations targeting the highest-cost patterns first |
| Refactored class + `-meta.xml` | Map-indexed service or heap-safe batch, per `references/code-examples.md` |
| Bulk test with headroom assertions | 200+ record test that fails when the budget is spent again |
| Checkpoint strategy | Temporary instrumentation guidance for locating hotspots |
| Before/after limit-usage readings | The evidence that the trade actually paid |

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You need the deployable artifact: before/after service, heap-safe batch, bulk test with headroom assertions, `-meta.xml`, `package.xml`, deploy and verify commands |
| `references/gotchas.md` | A limit behaves differently from what the table implies — managed packages, scheduled Apex, `Database.Stateful`, uncatchable exceptions, log heap of `0` |
| `references/examples.md` | You want a short worked pattern: Map refactor, checkpointing, reading the limit-usage block out of a debug log |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated optimization advice, or writing some |
| `references/well-architected.md` | You are framing the finding for an architecture review, or need the source list with the claim each one supports |

## Related Skills

- `apex/governor-limits` — use when the problem still includes basic SOQL, DML, or row-limit mistakes.
- `apex/apex-limits-monitoring` — runtime guard clauses that check headroom before entering expensive work.
- `apex/apex-performance-profiling` — use first when there is no measured hotspot yet.
- `apex/governor-limit-recovery-patterns` — savepoints and partial-commit strategies once a limit is already in reach.
- `apex/salesforce-debug-log-analysis` — reading the limit-usage and profiling blocks the platform writes.
- `apex/platform-cache` — use when repeated lookups can be avoided across transactions.
- `apex/async-apex` — use when the correct fix is to split heavy work into background execution.
- `data/soql-query-optimization` — use when the real cost is the query, not the code around it.
