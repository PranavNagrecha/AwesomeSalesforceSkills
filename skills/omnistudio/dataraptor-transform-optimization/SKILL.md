---
name: dataraptor-transform-optimization
description: "Use when DataRaptor Transform operations are slow, hit governor limits, or use Apex where formula fields would suffice. Covers formula vs Apex expressions, bulk transform sizing, and chained transform composition. Triggers: 'dataraptor transform slow'. NOT for DataRaptor Extract or Load performance — use omnistudio/dataraptor-patterns."
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
runtime_orphan: true
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# DataRaptor Transform Optimization

## First: which runtime, and which name

Before touching anything, settle two questions. Getting either wrong makes every
subsequent recommendation unreliable, and both are invisible in the artifact
itself.

**The name changed.** Salesforce renamed DataRaptor to **Omnistudio Data
Mapper**. Salesforce Help now carries two parallel trees — "Omnistudio Data
Mappers (Managed Package)" and "Omnistudio Data Mappers" — and they describe
different runtimes. This skill keeps `dataraptor` in its name because that is
what practitioners still type; everything below applies to a Data Mapper of type
Transform.

**There are two runtimes.** The managed package runtime (the old Vlocity
lineage, a custom data model, `vlocity_*` namespaces) and the standard runtime
(Salesforce standard objects and standard APIs). Migration between them is a
documented, three-phase process now assisted by the Omnistudio Migration
Assistant. A great deal of what is "known" about DataRaptors — including most
Apex invocation snippets in circulation — describes the managed package only.

| Concern | Managed package runtime | Standard runtime |
|---|---|---|
| Apex invocation | `vlocity_ins.DRGlobal.processObjectsJSON()` | `ConnectApi.OmniDesignerConnect.executeDataMapper(bundleName, apexInput)` |
| Calling Apex from a formula | Function Definition + `VlocityOpenInterface` | `FUNCTION()` + `Callable` |
| Deployment | DataPacks | Metadata API, once the Omnistudio Metadata setting is enabled |
| Storage | Managed-package custom objects | `OmniDataTransform` / `OmniDataTransformItem` standard objects |

The Apex row is not cosmetic. Salesforce's documentation for
`ConnectApi.OmniDesignerConnect.executeDataMapper` states that it "replaces the
`vlocity_ins.DRGlobal.processObjectsJSON()` method", that "This Connect API
removes the dependency on the managed package", and claims "up to 60% better
performance for Data Mapper calls from an Apex class compared to the previous
method". If your Transform is invoked from Apex on the standard runtime and the
call site still uses the managed-package method, that is the single largest
verified optimization available here, and it is a one-line change.

---

## What a Transform actually is

> "Transform—Perform intermediate data transformations without reading from or
> writing to Salesforce."

That sentence is the whole performance model. A Transform issues no SOQL and no
DML of its own. It restructures data it was handed. So when a Transform is slow,
the cost is in one of exactly three places:

1. **The evaluator** — formulas and custom functions run per mapping, per row.
2. **The materialization** — each Transform in a chain produces a full
   intermediate structure in heap before the next one starts.
3. **The context it inherits** — a Transform inside a synchronous Integration
   Procedure spends the *caller's* CPU-time and heap allocation, not its own.

Point 3 is why "the Transform is slow" is so often the wrong diagnosis. It is
frequently the last thing added to a transaction that was already at 9,000 ms.

**Scope.** This skill owns Transform-type Data Mappers. Extract, Turbo Extract,
and Load performance — where SOQL, DML, and batch sizing dominate — is
`omnistudio/dataraptor-patterns` and `omnistudio/dataraptor-load-and-extract`.
Caching is `omnistudio/integration-procedure-cacheable-patterns` and
`omnistudio/omnistudio-cache-strategies`.

---

## Before Starting

1. **Establish the runtime.** Managed package or standard. Everything else
   branches on it, and the answer is not visible in the Transform.

2. **Get a real profile, not a feeling.** Capture the Integration Procedure's
   own timing output and an Apex debug log for the same execution. You want the
   Transform's wall-clock share and the transaction's CPU total, because those
   two numbers ask different questions.

3. **Measure at production shape.** A Transform over 3 rows and one over 3,000
   are different programs. Take the row count and the field count from
   production, not from the designer's preview.

4. **Establish who consumes the output.** Half of Transform optimization is
   deleting mappings nothing reads. You cannot do that without knowing the
   consumers.

5. **Read the chain before the Transform.** If the payload arriving at the
   Transform is ten times larger than the fields it uses, the fix is upstream
   projection, not anything inside this artifact.

---

## Core Concepts

### The evaluator hierarchy

| Evaluator | Runs where | Costs |
|---|---|---|
| Direct mapping (Input JSON Path → Output JSON Path) | Transform engine | Cheapest — no expression evaluated |
| Transform Map Values (key-value substitution) | Transform engine | Near-free; a lookup, not an expression |
| Formula (Formulas tab, result to Formula Result Path) | Transform engine | Expression evaluation per row |
| Custom function calling Apex | Apex | Apex CPU, and any SOQL or DML that Apex does — against the *caller's* limits |

The ordering is the guidance: prefer a direct mapping, then a map-values
substitution, then a formula, and reach for Apex only when nothing above can
express the requirement. Each step down that list is a larger constant per row
and a larger blast radius when the row count grows.

Note what is *not* in that table: this skill makes no claim about a JavaScript
evaluator inside a Transform. The documented extension point for custom logic is
Apex — `FUNCTION()` plus `Callable` on the standard runtime, a Function
Definition plus `VlocityOpenInterface` on the managed package.

### Lists are where Transforms earn their existence, and where they go wrong

The three canonical Transform problems in Salesforce's own examples are all list
reshaping: converting a single item to a one-item list, converting a list of
objects to a list of values, and changing the hierarchical level of a list.

Two documented behaviours matter for both correctness and performance:

- The output data type has to be right. "Make sure that the output data type for
  your mapping is set to `List<Map>`."
- When several input lists map to one output list, **ordering is not
  guaranteed**: "the system does not guarantee the order of the items in the
  output". Salesforce's own remedy is to "use a formula to combine and filter the
  lists instead of using direct mappings" — for example
  `LIST(inputList1, inputList2, inputListNew)`.

That second one is the trap. A direct multi-list mapping is *cheaper* and
*wrong*; a `LIST()` formula is slightly more expensive and deterministic. This is
one of the few places in this skill where the right answer costs more, and taking
the cheap one produces a bug that appears only under load, when the ordering that
happened to be stable in the sandbox stops being stable.

### Chained Transforms materialize

Every Transform in a chain builds its complete output structure before the next
step reads it. Three chained Transforms over a 2,000-row payload hold three
full copies in heap at their peak — against 6 MB synchronously or 12 MB
asynchronously. Merging two adjacent Transforms removes an entire copy, and it is
usually the largest single win available on a chain that is failing with a heap
error rather than a CPU error.

Read the error before choosing the fix: heap and CPU failures look identical from
the outside and have opposite remedies. A CPU failure wants fewer or cheaper
expressions; a heap failure wants fewer materializations and a smaller payload.

### The Transform inherits the caller's limits

A Transform inside a synchronous Integration Procedure runs inside the calling
Apex transaction and draws on its allocation:

The synchronous vs asynchronous governor ceilings that bound a Transform are
tabulated in [`references/gotchas.md`](references/gotchas.md).

Since a Transform issues no queries of its own, the SOQL and DML rows are there
for the Apex a custom function calls. A custom function that queries once per row
turns a 500-row Transform into 500 queries against a limit of 100 — and that
failure is attributed to the Transform even though the Transform did nothing
except call the function you gave it.

Moving the Integration Procedure to an asynchronous shape multiplies the CPU
budget by six and the heap by two. That is not an optimization, it is a
relocation — but it is often the correct one, and it is cheaper than a rewrite.

### The standard objects are marked internal-use-only

`OmniDataTransform` and `OmniDataTransformItem` are documented in the Object
Reference (Spring '21 / API 51.0 onwards) with an unusually blunt warning:

`OmniDataTransform` is marked internal-use-only, which constrains what you may
query and what you must never write — quoted in full in
[`references/gotchas.md`](references/gotchas.md).
>
> "Modifying or deleting this object's records may result in errors with your
> implementation."

Read them for analysis if you like — a query that lists every Transform and its
item count is a legitimate way to find the chains worth auditing. Do not write to
them, and do not build an "optimizer" that rewrites mappings by DML. Changes go
through the designer or through the Metadata API.

---

## Common Patterns

### Pattern A — replace the Apex call site before touching the Transform

On the standard runtime, if Apex invokes the Data Mapper through the
managed-package method, switch to
`ConnectApi.OmniDesignerConnect.executeDataMapper(bundleName, apexInput)`. It is a
few lines, it removes the managed-package dependency, and Salesforce documents up
to 60% better performance for the call. Do this first: it costs nothing and it
changes the baseline every subsequent measurement is compared against. Full
example in [`references/examples.md`](references/examples.md), Example 1.

### Pattern B — demote every mapping one level down the evaluator hierarchy

Walk the mapping list and ask, per row: could this be a direct mapping? A
map-values substitution? A formula rather than a custom function? Most Transforms
that grew organically have at least a few mappings sitting one or two levels
above where they need to be.

### Pattern C — project upstream, transform downstream

If the Transform receives a 200-field payload and reads 12 fields, the 188 unused
fields cost heap in every materialization of every chained step. Narrow the field
list in the Extract that produced it. This is usually a larger win than anything
available inside the Transform.

### Pattern D — collapse adjacent Transforms

Two Transforms in sequence with no consumer between them are one Transform with
more mappings. Merging removes an intermediate materialization. Merge only where
the logic composes cleanly — a merged Transform that needs a comment explaining
the two halves has traded a performance win for a maintenance cost, and that is
usually the wrong trade.

### Pattern E — hoist per-row Apex into one bulk call

A custom function invoked once per row is N Apex invocations with N times the
fixed overhead, and if that Apex queries, it is also N queries. Where the logic is
genuinely code-shaped, replace the per-row function with a single Apex step that
receives the whole array and returns the whole transformed array. One invocation,
one query, one set of limits consumed.

### Pattern F — when the payload is the problem, stop optimizing the Transform

A Transform over a payload that is too large for the synchronous heap is not a
Transform problem. Either the upstream step should page, or the Integration
Procedure should be asynchronous, or the work belongs in Batch Apex. Optimizing
mappings on a payload that fundamentally does not fit is effort spent on the
wrong artifact.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Field copied unchanged | Direct mapping | No expression evaluated |
| Fixed value substitution (`Y`→`TRUE`) | Transform Map Values | A lookup, not an expression |
| Arithmetic or string composition | Formula | Runs in the Transform engine |
| Several input lists into one output list | `LIST()` formula, not direct mappings | Direct mapping does not guarantee order |
| Dynamic sObject access, regex, crypto | Custom function calling Apex | Nothing above can express it |
| Same Apex fires once per row | One bulk Apex step over the whole array | Collapses N invocations and N queries to one |
| Adjacent Transforms, no consumer between | Merge — if the logic composes cleanly | Removes a materialization |
| Payload far wider than the fields used | Project upstream | Cuts heap in every chained step |
| Failing on heap | Fewer materializations, smaller payload | Heap and CPU want opposite fixes |
| Failing on CPU | Fewer or cheaper expressions | As above, in the other direction |
| Apex call site uses `vlocity_ins.DRGlobal` on standard runtime | `ConnectApi.OmniDesignerConnect.executeDataMapper` | Documented, one-line, up to 60% |
| Payload cannot fit the synchronous budget at all | Asynchronous IP, or Batch Apex | The artifact is not the problem |

---

## Recommended Workflow

1. **Establish the runtime and the invocation path.** Managed package or
   standard; called from an Integration Procedure, an OmniScript, Apex, or REST.
   Record it — every later step branches on it.
2. **Profile before changing anything.** Capture the Transform's wall-clock share
   from the Integration Procedure output and the transaction's CPU and heap
   totals from an Apex debug log, at production row and field counts. Write the
   numbers down; they are the only evidence the change worked.
3. **Fix the call site first.** On the standard runtime, move an Apex caller to
   `ConnectApi.OmniDesignerConnect.executeDataMapper`. Re-profile — this changes
   the baseline.
4. **Classify every mapping** as direct, map-values, formula, or Apex, and demote
   each one as far down that list as it will go. Delete any mapping no consumer
   reads.
5. **Attack the structure, not the expressions, when the failure is heap**:
   project upstream, merge adjacent Transforms, and check whether the payload
   fundamentally fits the synchronous budget.
6. **Replace per-row Apex with one bulk call** wherever the same function fires
   for every row.
7. **Re-profile and record the before/after**, including which change produced
   which delta. A Transform that was optimized without evidence will be
   "optimized" again in six months by someone reversing your change.

---

## Review Checklist

- [ ] Runtime identified (managed package vs standard) and recorded
- [ ] Apex call sites on the standard runtime use `ConnectApi.OmniDesignerConnect.executeDataMapper`
- [ ] A before-profile exists, at production row and field counts
- [ ] Every mapping sits at the cheapest evaluator that can express it
- [ ] No mapping produces output that no consumer reads
- [ ] Multi-list merges use a `LIST()` formula, not direct mappings
- [ ] List outputs declare the correct output data type (`List<Map>`)
- [ ] No custom function performs SOQL or DML per row
- [ ] Adjacent Transforms with no consumer between them have been assessed for merging
- [ ] Upstream projection considered before any mapping-level tuning
- [ ] The failure mode (CPU vs heap) was identified before choosing the fix
- [ ] Synchronous vs asynchronous IP context is a deliberate choice, not an inherited one
- [ ] Nothing writes to `OmniDataTransform` or `OmniDataTransformItem`
- [ ] After-profile recorded, with the delta attributed to specific changes

---

## Salesforce-Specific Gotchas

Full detail in [`references/gotchas.md`](references/gotchas.md).

1. **Two runtimes, two Apex APIs** — most snippets in circulation are managed-package only.
2. **The rename** means half the search results describe the tree you are not in.
3. **Multi-list direct mappings do not guarantee order**; the `LIST()` formula does.
4. **A Transform spends the caller's CPU and heap**, not its own.
5. **A custom function that queries per row** blows the SOQL limit from inside an artifact that issues no SOQL.
6. **Chained Transforms hold one full copy each** in heap at peak.
7. **CPU and heap failures look identical** and want opposite fixes.
8. **`OmniDataTransform` is internal-use-only** — read it, never write it.
9. **The designer preview is not a benchmark** — three rows measure nothing.
10. **Metadata API deployment needs the Omnistudio Metadata setting enabled** first.
11. **A merged Transform that needs an explanatory comment** has traded the wrong way.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Runtime + invocation record | Managed package vs standard, and every call site with its API |
| Before-profile | Wall-clock share, transaction CPU, peak heap, at production row and field counts |
| Field-evaluator audit | Per-mapping: current evaluator, cheapest sufficient evaluator, and whether any consumer reads the output |
| Chain map | Every Transform in the sequence, what consumes each output, and which pairs can merge |
| Bulk-Apex plan | Which per-row custom functions become one array-level call |
| Upstream projection change | The narrowed field list in the Extract that feeds the Transform |
| After-profile | Same measurements, with each delta attributed to a specific change |

---

## Related Skills

- `omnistudio/dataraptor-patterns` — general Data Mapper design across all four
  types, and where Extract / Turbo Extract / Load performance lives
- `omnistudio/dataraptor-load-and-extract` — the SOQL- and DML-bound siblings,
  where batch sizing rather than expression cost dominates
- `omnistudio/omnistudio-performance` — Integration Procedure and OmniScript
  performance as a whole, which is usually the enclosing problem
- `omnistudio/integration-procedures` — IP step design, including where a
  Transform belongs in a chain
- `omnistudio/omnistudio-cache-strategies` — caching, the other lever when the
  Transform itself is already minimal
- `omnistudio/vlocity-to-native-omnistudio-migration` — the managed package to
  standard runtime move, if the runtime question above turned out to be the
  actual problem
- `apex/bulk-patterns-and-governor-limits` — the limits a Transform inherits, and
  how to bulkify the Apex a custom function calls
