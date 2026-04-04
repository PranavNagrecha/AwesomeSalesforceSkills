---
name: calculation-procedures
description: "Use when building, reviewing, or troubleshooting OmniStudio Calculation Procedures (also called Expression Sets) and Calculation Matrices (also called Decision Matrices). Triggers: 'calculation procedure', 'expression set', 'calculation matrix', 'decision matrix', 'pricing calculation', 'lookup step', 'matrix versioning'. NOT for DataRaptor transforms or DataRaptor-based field mapping."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - calculation-procedures
  - expression-sets
  - calculation-matrix
  - decision-matrix
  - omnistudio
  - pricing
inputs:
  - "Business calculation requirements: inputs, outputs, and lookup dimensions"
  - "Existing Calculation Procedure or Calculation Matrix metadata if reviewing"
  - "OmniScript or Integration Procedure that will call this procedure"
outputs:
  - "Calculation Procedure design with step sequence and variable contract"
  - "Calculation Matrix column definition and versioning plan"
  - "Review findings covering activation, version selection, and data-type issues"
triggers:
  - how do I set up a calculation procedure in OmniStudio
  - calculation matrix version is not being picked up at runtime
  - how do I use a lookup step to find a price in a decision matrix
  - expression set not returning the expected value
  - how do I call a calculation procedure from an OmniScript
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Calculation Procedures

Use this skill when building or auditing OmniStudio Calculation Procedures (Expression Sets) and their supporting Calculation Matrices (Decision Matrices). It covers step type selection, matrix versioning, lookup table configuration, activation, and integration with OmniScripts, Integration Procedures, and Apex.

---

## Before Starting

Gather this context before working on anything in this domain:

- What are the inputs and expected outputs of the calculation? Document the variable contract before touching the designer.
- Is the Calculation Procedure going to be called from an OmniScript, an Integration Procedure, or Apex? The invocation path affects how variables are named and how errors surface.
- Does this procedure reference a Calculation Matrix? If so, confirm the matrix is active and that its column data types match the variable types the procedure sends.
- What Salesforce API version is the org running? Calculation Procedures (as Expression Sets) and Decision Matrices were introduced in API version 53.0 and significantly expanded in 55.0+.

---

## Core Concepts

### Calculation Procedure = Expression Set

In OmniStudio, Calculation Procedures are the UI label for what the platform calls Expression Sets. The underlying object is `ExpressionSet`, with versions stored as `ExpressionSetVersion`. When working via API or metadata, use the `ExpressionSet` name; when working in the OmniStudio designer, use Calculation Procedure. Both terms refer to the same artifact.

A Calculation Procedure executes a series of ordered steps. Each version of the procedure is independent — you can have multiple versions, but only one can be active at a time. The procedure runs synchronously and returns a result map of output variables to the caller.

### Calculation Matrix = Decision Matrix

Calculation Matrices are the UI label for what the platform calls Decision Matrices (`CalculationMatrix` object, with rows in `CalculationMatrixRow` and versions in `CalculationMatrixVersion`). A matrix is a lookup table: you provide input column values and the matrix returns the matching output column value.

Matrix versioning uses effective date ranges (`StartDateTime`, `EndDateTime`) and a numeric `Rank` field. When a lookup occurs at a given timestamp and multiple matrix versions are active, the version with the highest `Rank` is selected. A matrix version with no `EndDateTime` remains permanently active until deactivated or given an end date.

### Step Types

A Calculation Procedure version is composed of steps. The valid step types are:

| Step Type | What It Does |
|-----------|--------------|
| **Assignment** | Assigns a literal, formula, or variable value to an output variable. Core arithmetic and text operations live here. |
| **Condition / Advanced Condition** | Evaluates logical criteria and branches execution. Controls which steps run. |
| **Decision Matrix Lookup** | Sends input variables to a Calculation Matrix and maps the returned columns back to procedure variables. |
| **Decision Table Lookup** | Sends input variables to a Decision Table (rule-based) and returns outputs. |
| **Aggregation** | Accumulates values across rows using functions: Sum, Avg, Min, Max, Count. |
| **SubExpression** | Calls another Calculation Procedure (expression set) inline. Useful for decomposing large procedures into reusable sub-components. |
| **Custom Element / Business Knowledge Model** | Extends the procedure with Apex-backed logic for platform integrations. |
| **Branch / Default Path** | Controls execution branching; Default Path marks the fallback branch. |

### Activation

A Calculation Procedure version must be activated before it can be called. Activation sets `IsActive = true` on the `ExpressionSetVersion` record. Only one version can be active at a time per procedure definition. Attempting to execute a procedure against an inactive version throws a runtime error. Similarly, any Calculation Matrix used in a Lookup step must also have at least one active version whose date range covers the execution timestamp.

---

## Common Patterns

### Pattern 1: Tiered Pricing via Matrix Lookup

**When to use:** When pricing or rating depends on a set of inputs (product type, quantity bracket, region) that change periodically without requiring a code change.

**How it works:**
1. Define the Calculation Matrix with input columns (e.g., `ProductCategory`, `QuantityBracket`) and one or more output columns (e.g., `UnitPrice`, `DiscountRate`).
2. Load matrix rows for the current pricing schedule. Set `StartDateTime` to the effective date and leave `EndDateTime` null for open-ended pricing.
3. In the Calculation Procedure, declare input variables matching the matrix input column names.
4. Add a Decision Matrix Lookup step. Map procedure input variables to matrix input columns and map matrix output columns to procedure output variables.
5. Add downstream Assignment steps to compute `TotalPrice = Quantity * UnitPrice`.
6. Activate the procedure version and the matrix version.
7. Call the procedure from OmniScript via the `Calculation Procedure` action or from an Integration Procedure's `Calculation Procedure` element.

**Why not a formula field or Flow formula:** A matrix-based approach lets pricing managers update rate tables without a deployment. A Flow or Apex formula requires a change set for every rate revision.

### Pattern 2: Insurance Eligibility with Sub-Procedures

**When to use:** When a single procedure would become unmanageably large — for example, an eligibility check that branches into separate benefit calculation procedures per product line.

**How it works:**
1. Create one "parent" Calculation Procedure that collects applicant inputs and routes to sub-procedures by product line.
2. Create one sub-procedure per product line (e.g., `EligibilityAutoCalc`, `EligibilityHomeCalc`).
3. In the parent procedure, use Condition steps to route to the correct SubExpression step.
4. Each SubExpression step references the appropriate child procedure by name.
5. Activate all sub-procedure versions before activating the parent.
6. Test each sub-procedure independently before testing the parent end-to-end.

**Why not one large procedure:** Deeply nested condition trees in a single procedure are hard to version independently. Sub-procedures allow product-line teams to evolve their own calculation logic without touching the parent.

### Pattern 3: Date-Effective Matrix Versioning

**When to use:** When business rules change on known future dates — for example, a new regulatory rate schedule that takes effect on January 1.

**How it works:**
1. Keep the existing active matrix version with its current `StartDateTime` and set its `EndDateTime` to December 31 of the current year (23:59:59 UTC).
2. Create a new matrix version with `StartDateTime` of January 1 next year, `EndDateTime` null, and `Rank` equal to or higher than the prior version.
3. Do not deactivate the prior version — the date range will handle selection automatically.
4. On runtime, the platform selects the version whose `StartDateTime <= execution time <= EndDateTime` (or no EndDateTime) with the highest `Rank`.
5. Test future-dated logic by setting the execution timestamp explicitly in the test harness.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Calculation logic changes frequently without IT involvement | Calculation Matrix with date-effective versions | Business users can upload new matrix rows without a deployment |
| Complex multi-condition eligibility with reusable branches | SubExpression steps referencing child procedures | Keeps each procedure small and independently versioned |
| Simple math with no lookups | Assignment steps with formula expressions | Avoids unnecessary matrix complexity |
| Need to call procedure from Apex | Use `ConnectApi.EvaluationService.executeExpression()` or the REST endpoint `/connect/business-rules/expression-sets` | Direct Apex invocation is supported via Connect API |
| Need to debug a failing lookup step | Use the built-in Test Execution panel in the OmniStudio designer | Surfaces variable state after each step; no sandbox deploy required |
| Matrix version not being selected at runtime | Check `StartDateTime`, `EndDateTime`, and `Rank` on all active versions | Version selection is timestamp-driven; gaps or overlaps cause silent wrong-version selection |

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

- [ ] Calculation Procedure version is activated (`IsActive = true` on `ExpressionSetVersion`)
- [ ] Every Calculation Matrix referenced in a Lookup step has an active version covering the expected execution date range
- [ ] Input variable names in the procedure match the column API names in the matrix exactly (case-sensitive)
- [ ] Output variables mapped from matrix columns have compatible data types (mismatch causes runtime null or cast error)
- [ ] SubExpression step targets are activated before the parent procedure is activated
- [ ] Built-in test execution passes with representative inputs including boundary values
- [ ] Procedure is callable from the intended consumer (OmniScript action, Integration Procedure element, or Apex Connect API)
- [ ] Matrix versioning strategy documented: which version is authoritative for which date range

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Matrix lookup returns first matching row only** — If multiple matrix rows satisfy the input criteria, the platform returns the first match. Row order within a version is not guaranteed by name; use unique input column combinations to ensure deterministic results. Duplicate input combos will cause inconsistent pricing or eligibility results that are hard to reproduce.

2. **Inactive procedure version causes silent failure at runtime** — Calling a procedure whose version is not active results in an error, not an empty result. If you create a new version to fix a bug, you must explicitly activate it and verify the old version is deactivated. The UI does not warn you at call time if the target is inactive.

3. **Data type mismatch between matrix column and variable produces null** — If the Calculation Procedure variable is declared as `Numeric` and the matrix output column returns a `Text` value (or vice versa), the mapped variable silently receives null. Always verify column data types in the matrix definition match the variable data type in the procedure. This is the most common cause of downstream `NullPointerException` in calculations.

4. **Matrix version rank gap causes wrong-version selection** — When two matrix versions overlap in date range, the version with the higher `Rank` wins. If versions are created with the same `Rank` and overlapping dates, behavior is non-deterministic. Always assign distinct, intentional ranks.

5. **Sub-procedure activation order matters** — If a parent procedure is activated while a child SubExpression target is inactive, the parent will error at runtime when the sub-expression step executes. Activate child procedures first, parent last.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Calculation Procedure variable contract | Input and output variable names, types, and required/optional status for the procedure |
| Calculation Matrix column definition | Input columns, output columns, data types, and versioning schedule |
| Review findings report | Step-by-step issues found in an existing procedure: activation status, type mismatches, lookup key uniqueness, version gaps |

---

## Related Skills

- **omnistudio/integration-procedures** — Use when the Calculation Procedure is one step inside a larger orchestration that reads from or writes to external systems or Salesforce data.
- **omnistudio/flexcard-design-patterns** — Use when the output of a Calculation Procedure needs to be displayed in a FlexCard component and the data binding approach is unclear.
