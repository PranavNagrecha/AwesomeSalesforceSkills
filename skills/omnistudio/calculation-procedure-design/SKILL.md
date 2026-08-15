---
name: calculation-procedure-design
description: "Design Calculation Procedures and Matrices for pricing, rating, and rules-heavy scoring. Triggers: calculation procedure, calculation matrix, expression set, decision matrix. NOT for Salesforce CPQ price rules — use admin/cpq-pricing-rules. NOT for Flow decision logic — use flow/flow-decision-element-patterns."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "calculation procedure design"
  - "calculation matrix lookup"
  - "pricing engine in omnistudio"
  - "rating matrix versioning"
  - "expression set in calc procedure"
  - "calculation procedure isn't working"
  - "decision matrix wildcard row not matching"
tags:
  - omnistudio
  - calculation-procedure
  - calculation-matrix
  - pricing
  - rules
inputs:
  - Business rules or rate tables in spreadsheet form
  - Input schema (line item, customer, product)
  - Output schema (price, score, eligibility)
outputs:
  - Calculation Procedure design (steps, matrices, constants)
  - Matrix versioning and activation plan
  - Test mode dataset and expected outputs
dependencies:
  - omnistudio/integration-procedure-cacheable-patterns
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
runtime_orphan: true
---

# Calculation Procedure Design

Use this skill when designing a pricing, rating, scoring, or eligibility engine
on OmniStudio's Business Rules Engine — and when a procedure that "looks
activated" is returning null. It covers the matrix column model, the version
selection rule, the invocation surfaces, and the handful of field-level facts
that decide whether the design works.

---

## The Names, Reconciled

Three vocabularies describe two artifacts. You cannot look up a field under the
designer's name, so start here.

| Designer label | API object | Version object | Since |
|---|---|---|---|
| Calculation Procedure | `ExpressionSet` | `ExpressionSetVersion` | API 55.0 |
| Calculation Matrix | `CalculationMatrix` — the object reference labels it **Decision Matrix** | `CalculationMatrixVersion` | API 53.0 |
| — | `CalculationMatrixColumn` | — | API 53.0 |

An expression set is, verbatim, "a series of steps connected in a logical flow
built from variables, constants, conditions, calculations, lookups, and
aggregations."

Two supporting objects worth knowing exist: `ExpressionSetView` exposes
file-based expression sets, which are "read-only templates that must be cloned
before modification"; `ExpsSetObjectAliasFieldVw` lists the source objects,
aliases, and fields an expression set uses, "for permission verification
purposes."

---

## The Column Model Is Where Designs Go Wrong

Two facts about `CalculationMatrixColumn` invalidate the way most people first
draw a matrix.

### Wildcards are a column opt-in, not a `*` in a cell

| Field | Type | Documented meaning |
|---|---|---|
| `IsWildcardColumn` | boolean, default `false` | "Specifies that this column can contain a wildcard value such as ALL." |
| `WildcardColumnValue` | string | "The value that indicates a wildcard, for example ALL." |

The token is whatever you set `WildcardColumnValue` to, on each column where
`IsWildcardColumn` is `true`. A column that has not opted in treats `*` as a
literal string no real input will ever equal — so the fallback row is dead and
fails silently. Being per-column is useful: permit a wildcard on `Region` while
requiring an exact `ProductTier`.

### Ranges are a `DataType`, not a Min/Max column pair

`DataType` is a restricted picklist with exactly these values:

The seven `DataType` values are enumerated, with what each one changes about
matching, in [`references/gotchas.md`](references/gotchas.md).

`NumberRange` and `TextRange` are first-class range types; boundaries go in
`RangeValues` — "a list of values that define range boundaries." One column per
dimension, bands that cannot overlap or gap by construction, and the comparison
out of your procedure steps. A column-name pair differing only by a
`Min`/`Max` suffix is the signature of a hand-rolled range that should be one
range column.

`ColumnType` is a restricted picklist: `Input` or `Output`. `DisplaySequence`
orders them.

---

## Version Selection Is Three Conditions, Not One

Both version objects carry the same four fields and select the same way.

1. The activation boolean is true.
2. The invocation time falls inside `[StartDateTime, EndDateTime]`.
3. Among the survivors, the **highest `Rank`** wins.

Verbatim, from `CalculationMatrixVersion.Rank`:

Overlapping enabled version windows are resolved deterministically by `Rank`, not
left undefined — quoted from the Object Reference in
[`references/gotchas.md`](references/gotchas.md).

**The activation field has a different name on each object:**

| Object | Field | Note |
|---|---|---|
| `ExpressionSetVersion` | **`IsActive`** | there is **no `Status` field** on this object |
| `CalculationMatrixVersion` | **`IsEnabled`** | there is **no `IsActive` field** on this object |

The UI calls both "activate." The API does not. Any script that generalises
from one to the other reads a field that does not exist.

**Use dates for the plan, `Rank` for the override.** A scheduled rate change
gets non-overlapping dates. A correction to a live version gets a new version
with the *same* `StartDateTime` and a higher `Rank` — which leaves the prior
version enabled and auditable instead of editing history. Leave rank gaps
(10, 20, 30) so a correction can slot in without renumbering. Two enabled
versions sharing a rank in an overlapping window have no documented tiebreaker.

---

## Invoking It

| Surface | Detail |
|---|---|
| **Connect REST API** | `POST /services/data/v67.0/connect/business-rules/expressionSet/${expressionSetName}`, API 55.0+. Body: `inputs` (`Map<String, Object>[]`, required) and optional `options` — `effectiveDate`, `useDatesOnly`, `actionContextCode`, `explainabilitySpecName`. Returns a Business Rules Result. |
| **Flow** | the "Invoke an active expression set" invocable action |
| **Integration Procedure** | the **Expression Set** action ("Invokes Expression Sets and returns results") and the **Decision Matrix** action ("Calls Decision Matrices with specified inputs") |
| **Apex** | via the invocable action, or the Connect REST resource over a Named Credential |

`options.effectiveDate` (ISO 8601) is what makes back-dated calculation
correct — version selection evaluates against it instead of "now," so a
reissued quote prices at the rates in force on its original issue date. Decide
this early; retrofitting it means every caller changes.

Two request-body conventions: for **field aliases**, append `Id` to the object
alias and pass the source object ID; for **context definitions**, append `Id`
to the developer name and pass the context ID.

There is **no** `ConnectApi.EvaluationService` class and no
`executeExpression()` method. See `references/llm-anti-patterns.md` §4.

---

## Recommended Workflow

1. Write the rule as a table and check it is genuinely tabular. If the branch
   conditions are business values (regions, tiers, bands), it is a matrix. If it
   needs iteration, recursion, or a mid-computation callout, it is Apex.
2. Design the columns before the rows: `ColumnType` (Input/Output), `DataType`
   — using `NumberRange`/`TextRange` with declared `RangeValues` for any banded
   dimension — and `IsWildcardColumn` + `WildcardColumnValue` on every column
   that needs a fallback.
3. Decide `MatrixType`. `Grouped` with `GroupKey`/`SubGroupKey` when the same
   rate structure repeats per partition and each partition changes on its own
   schedule; `Standard` when the dimensions are independent lookup inputs.
4. Build the procedure: matrix lookup steps plus the arithmetic that combines
   them. Keep the step count low — logic that grows past readability belongs in
   a sub-expression-set or in Apex.
5. Load rows and **gate enablement on `LoadProcessStatus = 'Completed'`**, not
   on the load finishing — `CompletedWithErrors` means a partial load. Assert
   the `CalculationMatrixRow` count against the source CSV, then activate leaves
   before roots (matrices and sub-expression-sets before the procedures that
   reference them) with distinct, gapped `Rank` values and explicit
   `StartDateTime` / `EndDateTime`.
6. Run fixtures from source control — one case per band boundary, one that must
   hit the wildcard, one single-element collection for any aggregation step —
   and record `DecimalScale` and `ExecutionScale` alongside the expected values.
7. If the procedure sits on a hot UI path, wrap the call in a cached
   Integration Procedure (see `omnistudio/integration-procedure-cacheable-patterns`).
   Nothing memoizes procedure results for you.

---

## Review Checklist

- [ ] Every fallback column has `IsWildcardColumn = true` **and** a set
      `WildcardColumnValue`, and rows use that exact token — not `*`
- [ ] Banded dimensions use one `NumberRange`/`TextRange` column with declared
      `RangeValues`, not Min/Max column pairs
- [ ] Activation checked with the right field per object — `IsActive` on
      `ExpressionSetVersion`, `IsEnabled` on `CalculationMatrixVersion`
- [ ] No two enabled versions share a `Rank` in an overlapping date window
- [ ] `LoadProcessStatus = 'Completed'` before enablement, plus a row-count
      assertion against the source CSV
- [ ] No edits to an enabled version; corrections ship as a higher-`Rank`
      version in the same window
- [ ] Referenced matrices and sub-expression-sets activated before their parents
- [ ] `DecimalScale` and `ExecutionScale` recorded as part of the version contract
- [ ] Back-dated paths pass `options.effectiveDate`
- [ ] Fixtures in source control cover band boundaries, the wildcard path, and a
      single-element aggregation input
- [ ] Hot UI callers go through a cached Integration Procedure

---

## Worked Examples (see `references/examples.md`)

- *The names, reconciled* — designer labels vs API objects
- *Activation is a different field on each object* — the verification queries
- *Wildcards are configured per column* — `IsWildcardColumn` / `WildcardColumnValue`
- *Ranges are a column data type* — `NumberRange` and `RangeValues`
- *Date range plus `Rank`* — planned changes vs emergency corrections
- *The matrix that loaded halfway* — `CompletedWithErrors`
- *The four invocation surfaces* — with the real REST contract
- *Simulation results are stored on the version* — `LatestSimulationResult`
- *Grouped matrices* — when one matrix is really twelve

## Common Gotchas (see `references/gotchas.md`)

- `IsActive` vs `IsEnabled`, and no `Status` field on either object
- `*` is not a wildcard; wildcards are a per-column opt-in
- Overlapping version windows are resolved by `Rank`, not undefined
- Editing an enabled version destroys reproducibility
- `CompletedWithErrors` is a partial load reported as success
- `DecimalScale` changes the answer without changing the rules
- Aggregation over a scalar silently aggregates one item

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- `*` as a wildcard
- Min/Max column pairs instead of `NumberRange`
- `IsActive` on a matrix version, or `Status` on either object
- Inventing `ConnectApi.EvaluationService`
- An Apex if-else ladder instead of a matrix
- Version selection explained without `Rank`
- Treating `CompletedWithErrors` as success

---

## Related

- **omnistudio/calculation-procedures** — build and troubleshoot an existing
  procedure. This skill is the design pass that precedes it.
- **omnistudio/business-rules-engine** — the wider BRE surface, including
  decision tables and explainability.
- **omnistudio/integration-procedure-cacheable-patterns** — how to put a cached
  read path in front of a hot procedure. Note the 5-minute Platform Cache TTL
  floor: a rate with a tighter freshness contract should not be cached at all.
- **standards/decision-trees/automation-selection.md** — read before choosing
  Business Rules Engine over Flow or Apex for a rules problem.

## Official Sources Used

See `references/well-architected.md` for the full source list with the specific
claim each source grounds.
