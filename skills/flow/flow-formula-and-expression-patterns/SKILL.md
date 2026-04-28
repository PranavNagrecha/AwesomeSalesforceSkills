---
name: flow-formula-and-expression-patterns
description: "Author NULL-safe, type-correct, performance-aware Formula resources and condition expressions in Flow: lazy re-evaluation, BLANKVALUE/ISBLANK guards, ISPICKVAL vs =, VALUE/TEXT/DATETIMEVALUE coercion, time-zone differences between TODAY/NOW, and the 5,000-character formula limit. NOT for record-level formula fields on objects — see admin/formula-fields. NOT for Validation Rule formulas (different runtime context) — see admin/validation-rules."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "flow formula returns null unexpectedly"
  - "ISPICKVAL in flow formula"
  - "5000 character formula limit"
  - "formula inside loop slow"
  - "BLANKVALUE flow formula null handling"
  - "TODAY vs NOW time zone flow"
  - "VALUE TEXT DATETIMEVALUE flow type coercion"
  - "flow formula resource referenced many times performance"
tags:
  - flow-formula-and-expression-patterns
  - formulas
  - flow
  - null-safety
  - type-coercion
  - performance
  - picklist
inputs:
  - Flow design + the expression / formula intent
  - Return-type expectation (Text, Number, Boolean, Date, DateTime, Currency)
  - Whether any input is nullable
  - Whether the formula will be referenced inside a Loop body
outputs:
  - Correctly typed, NULL-safe, performance-aware formula resource OR decision-condition expression
  - Cached Assignment alternative when formula is referenced repeatedly inside a loop
  - Composed formula chain when the single-formula 5,000-char limit is at risk
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-27
---

# Flow Formula And Expression Patterns

Activate when authoring or reviewing any Flow Formula resource, Decision condition expression, or Screen-component formula property. The skill enforces NULL-safe wrapping, correct type coercion, lazy-re-evaluation awareness, and the 5,000-character ceiling — failure modes that surface at runtime as silent NULLs, "Comparison value cannot be null" decision errors, and per-iteration performance cliffs inside loops.

---

## Before Starting

Gather this context before writing or fixing any formula in Flow:

- **What type does the formula return?** Boolean, Text, Number, Currency, Date, DateTime, Time. Flow rejects implicit return-type changes; coercion must be explicit (`VALUE()`, `TEXT()`, `DATEVALUE()`, `DATETIMEVALUE()`).
- **What types are the inputs and which are nullable?** Any `null` input propagates to a `null` output for arithmetic, comparison, and logical operators (NULL + 1 = NULL; NULL && TRUE = NULL). Wrap nullable inputs with `BLANKVALUE(field, default)` or `IF(ISBLANK(field), default, field)`.
- **Will the formula be referenced inside a Loop body or by 3+ elements?** Each `{!FormulaResourceName}` reference re-evaluates the entire expression. A formula touched 10 times inside a 200-iteration loop runs 2,000 times. Cache the result in an Assignment if the formula is non-trivial.
- **Is the formula approaching 5,000 characters?** Single-formula limit. Decompose into composed Formula resources (FormulaA references FormulaB references FormulaC). Each layer still re-evaluates lazily.
- **Is this a picklist comparison?** Use `ISPICKVAL(PicklistField__c, "Value")` or `INCLUDES(MultiSelectField__c, "Value")`. Do NOT use `=` against a literal string — that compares the running locale's API name vs label and is a P1 source of silent false negatives.
- **Is this a date/time formula?** `TODAY()` returns the running user's local date in their TZ. `NOW()` returns the org's default TZ. Cross-TZ teams hit edge cases at day boundaries.
- **Is the formula in a Decision element vs a Formula resource vs a Screen-component property?** Same language, three evaluation contexts. A Decision condition that throws "Comparison value cannot be null" needs the same NULL-guard treatment as a Formula resource.

---

## Core Concepts

### Concept 1: Three places formulas appear (one language, three contexts)

The Flow formula language is a strict subset of the standard Salesforce formula language documented at Help → Formula Operators and Functions. The same syntax appears in three distinct evaluation contexts:

1. **Formula resource** — declared once under Resources, referenced by `{!FormulaResourceName}`. Lazy: evaluates each time it's referenced.
2. **Decision condition expression** — formula entered directly inside an outcome's condition row when "Formula Evaluates to True" is selected. Evaluates once when the Decision element runs.
3. **Screen-component formula property** — formulas inside Display Text, default values, validation, and reactive component bindings. Evaluates per-screen-render in flow runtime.

All three share the same operator/function library plus flow-specific globals like `{!$Flow.CurrentDateTime}`, `{!$Flow.CurrentDate}`, `{!$Flow.FaultMessage}`, `{!$Flow.InterviewStartTime}`, and `{!$Flow.ActiveStages}`. Validation Rule formula context is NOT identical — validation rules can call `PRIORVALUE()` and `ISCHANGED()`, Flow cannot. Workflow Field Update formula context is a third dialect — also not interchangeable.

### Concept 2: Lazy re-evaluation (the loop-body performance trap)

Flow does NOT memoise Formula resource results. Every `{!FormulaResourceName}` reference triggers a fresh evaluation. The cost compounds:

- A Formula resource referenced 1 time outside a loop: 1 evaluation. Free.
- A Formula resource referenced 1 time inside a loop iterating 200 records: 200 evaluations. Usually fine.
- A Formula resource referenced 10 times inside a loop iterating 200 records: 2,000 evaluations. Visible CPU.
- A Formula resource that itself references 3 OTHER Formula resources, each referenced 5 times in a 200-iteration loop: 200 × 5 × 4 = 4,000 evaluations and possible CPU-time governor breaches.

The fix: when an expensive formula will be referenced repeatedly, evaluate it ONCE in an Assignment to a typed variable, then reference the variable from then on. Decision elements, Screen components, and downstream Assignments all read the cached variable — zero re-evaluation cost.

### Concept 3: NULL propagation and explicit type coercion

Salesforce formula NULL semantics are SQL-like, not Java-like:

- `NULL + 1` → `NULL`, not `1`.
- `NULL = NULL` → unknown (often FALSE in practice — use `ISBLANK()` to test for null).
- `NULL && TRUE` → `NULL`, not `FALSE`. A Decision condition referencing a NULL-tainted formula throws or evaluates the default outcome unexpectedly.
- `"" = NULL` → TRUE for Text (empty string and null are interchangeable for Text fields). FALSE for Number (0 is not null).

Type coercion is explicit:

- Text → Number: `VALUE(TextVar)`. Throws at runtime if `TextVar` is non-numeric — wrap nullable input with `IF(ISBLANK(TextVar), 0, VALUE(TextVar))`.
- Number → Text: `TEXT(NumberVar)`. Returns no thousands separator and no localisation.
- Date → Text: `TEXT(DateVar)` returns ISO `YYYY-MM-DD`. Concatenation `"Date: " & DateVar` returns the running user's locale format — surprising in cross-locale orgs.
- Text → Date: `DATEVALUE(TextVar)` requires `YYYY-MM-DD`.
- Text → DateTime: `DATETIMEVALUE(TextVar)` requires `YYYY-MM-DD HH:MM:SS` in GMT.
- Picklist → Text: `TEXT(PicklistField__c)` returns the API name, NEVER the label. Comparing labels in formulas is impossible without a Custom Metadata lookup.

---

## Common Patterns

### Pattern 1: BLANKVALUE Default Wrap

**When to use:** Any time a formula consumes a nullable input (a record field that's not required, an optional Screen input, the output of a Get-Records that may be empty).

**How it works:**

```
// Risky: returns NULL if Discount__c is null, then propagates everywhere downstream.
{!recordVar.Amount} - {!recordVar.Discount__c}

// Safe: defaults Discount__c to 0 when null.
{!recordVar.Amount} - BLANKVALUE({!recordVar.Discount__c}, 0)
```

For Text:

```
BLANKVALUE({!recordVar.Description}, "(no description provided)")
```

For Booleans where you want the missing-input fallback to be FALSE:

```
IF(ISBLANK({!flagVar}), FALSE, {!flagVar})
```

**Why not the alternative:** Skipping the wrap and "checking the input upstream" works until someone adds a new caller. The defensive wrap inside the formula makes the contract explicit and survives upstream refactors.

### Pattern 2: Cache Expensive Formula in Assignment

**When to use:** A Formula resource (a) costs more than a single field reference (concatenation, REGEX, nested `IF`, `CASE` with 5+ branches, date math) AND (b) will be referenced more than 2 times, especially inside a Loop body.

**How it works:**

```
// Inside Loop body — BEFORE (re-evaluates 6 × 200 = 1,200 times):
//   Decision condition uses {!isHighValueOpportunity}
//   Assignment 1 sets stageDescription using {!isHighValueOpportunity}
//   Assignment 2 sets nextAction using {!isHighValueOpportunity}
//   Assignment 3 logs message using {!isHighValueOpportunity}
//   Update sets owner if {!isHighValueOpportunity}
//   Email body refers to {!isHighValueOpportunity}

// AFTER — single evaluation per loop iteration (200 evaluations total):
//   Assignment "cacheHighValue": cachedHighValue (Boolean) = {!isHighValueOpportunity}
//   All 6 references downstream now read {!cachedHighValue} (variable, not formula)
```

**Why not the alternative:** Leaving the formula referenced N times relies on developers to mentally track per-element cost. The Assignment makes the single-evaluation contract explicit, easy to audit, and survives loop-body edits.

### Pattern 3: ISPICKVAL for Picklist Comparisons

**When to use:** Comparing a single-select picklist field (`PicklistField__c`) or a multi-select picklist (`MultiSelectField__c`) against a known value.

**How it works:**

```
// Single-select picklist — CORRECT:
ISPICKVAL({!recordVar.Stage__c}, "Closed Won")

// Single-select picklist — WRONG (comparing label vs API name fails silently in some locales):
{!recordVar.Stage__c} = "Closed Won"

// Multi-select picklist — CORRECT:
INCLUDES({!recordVar.Industries__c}, "Healthcare")

// Negation:
NOT(ISPICKVAL({!recordVar.Stage__c}, "Closed Lost"))

// Multiple values:
OR(
  ISPICKVAL({!recordVar.Stage__c}, "Closed Won"),
  ISPICKVAL({!recordVar.Stage__c}, "Closed Lost")
)

// Convert picklist to API-name Text for further string ops:
TEXT({!recordVar.Stage__c}) & " — recorded"
```

**Why not the alternative:** `=` works for English-only orgs against the active default value, then breaks the moment a translation pack is enabled or someone changes the picklist label without changing the API name. ISPICKVAL compares against the API name and is locale-immune.

---

## Decision Guidance

| Scenario | Recommended Approach | Reason |
|---|---|---|
| One-time computation referenced once, outside a loop | Formula resource | Lazy evaluation cost is 1; readability beats variable indirection. |
| Computation referenced 3+ times inside a loop body | Assignment to typed variable (cache the result) | Avoids re-evaluation per reference. |
| Branching on the value of a Boolean/Number/Date | Decision condition (formula or operator) | Decision is the explicit branching primitive; formulas inside a Decision condition are fine. |
| Branching on a single-select picklist | Decision condition with `ISPICKVAL(...)` | Locale-safe; `=` against a literal is a known P1 bug. |
| Multi-step transformation across many fields with Apex-like logic | Apex Invocable Action returning a typed output | Beyond ~3 layers of nested formulas, Apex is more testable, debuggable, and reusable. |
| Expression > 4,500 chars and growing | Multiple composed Formula resources OR an Invocable Apex action | The single-formula limit is 5,000 characters; composition keeps each layer under the cap. |
| String concatenation that includes a Date and runs in a multi-locale org | `TEXT(DateVar)` + manual format OR an Invocable | Implicit concat uses running-user locale; explicit `TEXT()` returns deterministic ISO. |
| Boolean expression of 5+ ANDs/ORs with nullable inputs | Wrap each input with `BLANKVALUE` first, then combine | NULL propagation makes naïve `AND(...)` evaluate to NULL not FALSE. |
| "Has any of these picklist values" against a multi-select | `INCLUDES(MultiPicklistField__c, "value")` | `INCLUDES` is the only correct primitive for multi-select. |

---

## Recommended Workflow

1. **State the contract.** Write down the formula's expected return type, every input, which inputs are nullable, and where the formula will be referenced. If references include a Loop body, note the iteration count expectation.
2. **Choose the context.** Formula resource (reusable), Decision condition (one-time branching), Screen-component property (per-render). If the same expression is needed in 3+ places, choose the Formula resource and DRY the call sites.
3. **Author with NULL guards first.** Wrap every nullable input with `BLANKVALUE` or `IF(ISBLANK(...), default, value)` BEFORE composing the rest of the expression. NULL guards are far cheaper to add upfront than to retrofit after a runtime null surfaces in a downstream element.
4. **Make all type coercion explicit.** Replace any implicit coercion with `VALUE()`, `TEXT()`, `DATEVALUE()`, `DATETIMEVALUE()`. For picklists, replace any `=` with `ISPICKVAL()` and any "contains" with `INCLUDES()`.
5. **Audit for re-evaluation cost.** Count how many places reference the Formula resource. If any of them are inside a Loop, count `references × loop_iterations`. If the product exceeds ~500 and the formula is non-trivial, refactor to an Assignment-cached variable.
6. **Check the 5,000-char ceiling.** If the formula exceeds ~4,500 characters, split into composed Formula resources before you hit the hard limit at deploy time.
7. **Verify in Flow Debug.** Run the flow with realistic null and edge inputs (empty Get-Records result, missing optional fields, picklist with 0 selections, cross-TZ date boundary). Confirm no NULL surfaces in a downstream Decision or Update.

---

## Review Checklist

- [ ] Every nullable input is wrapped with `BLANKVALUE` or `IF(ISBLANK(...), default, value)`.
- [ ] Every picklist comparison uses `ISPICKVAL` (single) or `INCLUDES` (multi), not `=`.
- [ ] Every Text↔Number, Text↔Date, Text↔DateTime coercion uses `VALUE` / `TEXT` / `DATEVALUE` / `DATETIMEVALUE` explicitly.
- [ ] Formula resources referenced inside a Loop body are either trivial (single field reference, single arithmetic op) or cached in an Assignment.
- [ ] Each Formula resource is under 4,500 characters; composed chains used for any larger expression.
- [ ] `TODAY()` vs `NOW()` choice is documented when used in a multi-TZ org — confirm the right TZ semantic is desired.
- [ ] Decision condition formulas and Screen-component formulas have been reviewed with the same NULL-safety + coercion checklist as standalone Formula resources.
- [ ] Composed formula chains do not exceed 3 layers of nesting (FormulaA → FormulaB → FormulaC); deeper chains should become Apex Invocable.
- [ ] No Workflow-only or Validation-Rule-only formula functions are used (e.g. `PRIORVALUE`, `ISCHANGED`).

---

## Salesforce-Specific Gotchas

1. **NULL propagates through arithmetic and Boolean operators.** `NULL + 1 = NULL`, `NULL && TRUE = NULL`, `NULL > 0 = NULL`. A Decision condition that depends on a NULL-tainted formula either throws "Comparison value cannot be null" or quietly takes the default outcome — both are P1 production failures.
2. **`=` against a picklist literal is a silent locale bug.** `{!Account.Industry} = "Healthcare"` compares the value the user sees (label) to the literal string. Translation packs, label edits, or API-name vs label drift all turn this comparison FALSE without warning. Always use `ISPICKVAL`.
3. **Lazy re-evaluation inside Loop bodies multiplies CPU cost.** Every `{!FormulaResourceName}` reference re-runs the formula. Six references × 200 iterations = 1,200 evaluations. Cache in an Assignment when the formula is non-trivial and referenced more than twice in a loop body.
4. **5,000-character limit per formula.** The platform rejects deploys with a formula above 5,000 characters. Compose multiple Formula resources (FormulaA references FormulaB references FormulaC) — each child counts independently. Going deeper than ~3 composition layers is a smell; promote to Apex Invocable.
5. **`TODAY()` and `NOW()` use different time zones.** `TODAY()` returns the running user's local date in the user's TZ. `NOW()` returns the org's default TZ. In a multi-TZ org, "TODAY at 1am Pacific" and "TODAY at 1am Eastern" are different dates — formulas comparing `TODAY()` to a stored Date can be off-by-one for users on the far side of the org's default TZ.
6. **`TEXT(picklist)` returns the API name, not the label.** Any user-facing string built from `TEXT(PicklistField__c)` will show the API name. Use a Get-Records on a Custom Metadata mapping or a hardcoded `CASE` to map to label.
7. **Implicit Date-to-Text concatenation uses the running-user locale.** `"Created on " & {!recordVar.CreatedDate}` returns "10/27/2026" for US users and "27/10/2026" for UK users. Use `TEXT({!recordVar.CreatedDate})` for deterministic ISO output, or format explicitly with `LEFT/MID/RIGHT` of `TEXT()`.
8. **Decision conditions evaluate referenced formulas EVERY time the Decision runs.** A Decision inside a Loop body that references 3 Formula resources costs 3 evaluations per iteration — auditable in the same way as element-level references.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Formula resource definition | Frontmatter (name, return type, dependencies on input vars), expression body with NULL guards and explicit coercion. |
| Cached-variable Assignment refactor | When the formula was being re-evaluated inside a loop — the Assignment that materialises the result and the list of downstream references switched to read the cached variable. |
| Composed formula chain | When the original expression exceeded 4,500 chars — the parent + child Formula resources, each independently under the limit. |
| Decision-condition rewrite | When the original `=` against a picklist label was a bug — the `ISPICKVAL` or `INCLUDES` rewrite. |
| Review report | Itemised list of NULL-guards added, picklist comparisons rewritten, type coercions made explicit, and re-evaluation hot-spots fixed, with line-level pointers in the flow XML or screenshot evidence. |

---

## Related Skills

- `flow-resource-patterns` — broader guidance on naming, scoping, and choosing among Variable / Constant / Formula / Choice / Stage resources. This skill handles the formula-specific subset.
- `flow-decision-element-patterns` — when the formula is being authored as the condition of a Decision outcome, pair these two skills.
- `admin/formula-fields` — for record-level formula fields on objects (a different runtime context — same language, but evaluated by the platform on read, with field-history and reportability concerns this skill does not cover).
- `flow-collection-processing` — when caching a formula across loop iterations, the assignment pattern interacts with collection-iteration patterns documented there.
- `flow-bulkification` — performance audits of formula re-evaluation overlap with broader bulkification work.
- `flow-loop-element-patterns` — formula re-evaluation is one of the top performance traps inside Loop bodies; cross-reference for loop-body design.
- `flow-runtime-error-diagnosis` — when "Comparison value cannot be null" or "The formula expression is invalid" surfaces at runtime, that skill handles the diagnostic flow; this skill handles the prevention.

---

## Official Sources Used

- Salesforce Help — Formula Operators and Functions — https://help.salesforce.com/s/articleView?id=sf.customize_functions.htm
- Salesforce Help — Flow Formula Resource — https://help.salesforce.com/s/articleView?id=platform.flow_ref_resources_formula.htm
- Salesforce Help — Flow $Flow Global Variables — https://help.salesforce.com/s/articleView?id=platform.flow_ref_resources_systemvariables.htm
- Salesforce Help — Flow Resources Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources.htm&type=5
- Salesforce Help — Flow Decision Element — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_decision.htm&type=5
- Salesforce Help — ISPICKVAL Formula Function — https://help.salesforce.com/s/articleView?id=sf.functions_ispickval.htm
- Salesforce Help — INCLUDES Formula Function — https://help.salesforce.com/s/articleView?id=sf.functions_includes.htm
- Salesforce Help — BLANKVALUE Formula Function — https://help.salesforce.com/s/articleView?id=sf.functions_blankvalue.htm
- Salesforce Help — TEXT Formula Function — https://help.salesforce.com/s/articleView?id=sf.functions_text.htm
- Salesforce Help — Date and DateTime Formula Functions — https://help.salesforce.com/s/articleView?id=sf.formula_using_date_datetime.htm
