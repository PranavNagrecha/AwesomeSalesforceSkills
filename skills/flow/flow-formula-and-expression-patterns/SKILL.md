---
name: flow-formula-and-expression-patterns
description: "Author NULL-safe, type-correct, performance-aware Formula resources and condition expressions in Flow: lazy re-evaluation, BLANKVALUE/ISBLANK guards, ISPICKVAL vs =. NOT for record-level formula fields on objects — use admin/formula-fields. NOT for Validation Rule formulas — use admin/validation-rules. Metadata surface: FlowFormula dataType/expression/scale, filterFormula on FlowStart, FlowTextTemplate isViewedAsPlainText, FlowRule conditionLogic, FlowTest assertions."
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
  - "write the filterFormula entry condition for a record-triggered flow"
  - "set dataType and scale on a FlowFormula so the deploy stops rounding"
  - "compare a field to its prior value inside a flow entry condition"
  - "branch a decision outcome on a formula instead of a condition row"
  - "build a text template with merge fields that renders as rich text"
  - "compute a business-day due date inside a flow formula"
  - "assert a flow formula's output with a FlowTest before activating"
  - "check whether a formula function is even allowed in a flow"
  - "flow formula in one org returns null and in another org throws"
  - "flow formula resource null handling with isblank and text templates"
tags:
  - flow-formula-and-expression-patterns
  - formulas
  - flow
  - null-safety
  - type-coercion
  - performance
  - picklist
  - flow-metadata
  - filter-formula
  - text-template
inputs:
  - Flow design + the expression / formula intent
  - Return-type expectation (Text, Number, Boolean, Date, DateTime, Currency)
  - Whether any input is nullable
  - Whether the formula will be referenced inside a Loop body
outputs:
  - Correctly typed, NULL-safe, performance-aware formula resource OR decision-condition expression
  - Cached Assignment alternative when formula is referenced repeatedly inside a loop
  - Composed formula chain when a single expression grows past the advisory length threshold
  - Deployable `<formulas>` / `<filterFormula>` / `<textTemplates>` XML with dataType, scale and merge fields declared
  - A FlowTest that asserts the formula's runtime value before the flow is activated
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Flow Formula And Expression Patterns

Activate when authoring or reviewing any Flow Formula resource, Decision condition expression, or Screen-component formula property. The skill enforces NULL-safe wrapping, correct type coercion, lazy-re-evaluation awareness, correct `FlowFormula` metadata (`dataType`, `scale`), and expression length — failure modes that surface at runtime as silent NULLs, "Comparison value cannot be null" decision errors, and per-iteration performance cliffs inside loops.

---

## Before Starting

Gather this context before writing or fixing any formula in Flow:

- **What type does the formula return?** Boolean, Text, Number, Currency, Date, DateTime, Time. Flow rejects implicit return-type changes; coercion must be explicit (`VALUE()`, `TEXT()`, `DATEVALUE()`, `DATETIMEVALUE()`).
- **What types are the inputs and which are nullable?** Any `null` input propagates to a `null` output for arithmetic, comparison, and logical operators (NULL + 1 = NULL; NULL && TRUE = NULL). Wrap nullable inputs with `BLANKVALUE(field, default)` or `IF(ISBLANK(field), default, field)`.
- **Will the formula be referenced inside a Loop body or by 3+ elements?** Each `{!FormulaResourceName}` reference re-evaluates the entire expression. A formula touched 10 times inside a 200-iteration loop runs 2,000 times. Cache the result in an Assignment if the formula is non-trivial.
- **How long is the expression?** The often-quoted 5,000-character ceiling is **not in the Metadata API guide, the Object Reference, the Apex Developer Guide or the App Limits cheat sheet** — `grep -n -i "5,000 bytes\|Compiled formula"` returns nothing. What is grounded is 3,900 source characters (`apexdev.txt` L28144), stated for formula *fields*. UNVERIFIED (2026-09-05): whether it binds a Flow `FlowFormula` `<expression>` too. Compose defensively well under it; see `references/metadata-examples.md` §3.
- **Is this a picklist comparison?** Use `ISPICKVAL(PicklistField__c, "Value")` or `INCLUDES(MultiSelectField__c, "Value")`. Do NOT use `=` against a literal string — that compares the running locale's API name vs label and is a P1 source of silent false negatives.
- **Is this a date/time formula?** `TODAY()` returns the running user's local date in their TZ. `NOW()` returns the org's default TZ. Cross-TZ teams hit edge cases at day boundaries.
- **Is the formula in a Decision element vs a Formula resource vs a Screen-component property?** Same language, three evaluation contexts. A Decision condition that throws "Comparison value cannot be null" needs the same NULL-guard treatment as a Formula resource.

---

## Questions to Ask Before Configuring

Ask these before you type a single `{!`. Each one maps to a defect that deploys cleanly, passes a happy-path debug run, and shows up as wrong data weeks later — the failure shape that makes formulas the hardest part of a flow to review.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What data type does this formula return, and is that type written in the XML?" | `FlowFormula.dataType` **defaults to Number when it is not declared** (`api_meta.txt` L70599–L70609). An undeclared Text or Boolean formula becomes a Number formula, and the failure is a type error at the *call site*, not at the formula | An explicit `<dataType>`, and a `<scale>` alongside it if the answer is Number or Currency (Gotcha 41) |
| "Which operands can be null on a real record, not on your test record?" | Null propagates through arithmetic, comparison and Boolean operators, so one unguarded optional field turns the whole expression null | The `BLANKVALUE` / `ISBLANK` guard list, written *inside* the resource so it survives a new caller (Gotchas 1, 48) |
| "Is this an entry condition, and does it need a function the condition rows cannot express?" | `filterFormula` (`api_meta.txt` L72390, API 55.0+) exists precisely for that case; a condition row is `field`/`operator`/`value` and cannot call `TEXT()` or `ISBLANK()` | The choice between `filterFormula` and `filters` + `filterLogic` — and the knowledge that the guide never says you may not have both (Gotcha 45) |
| "Does the condition depend on what the field *was*, not just what it is?" | `$Record__Prior` is undocumented in the Metadata API guide (0 grep hits), while `doesRequireRecordChangedToMeetCriteria` is documented on both `FlowStart` and `FlowRule` | A documented declarative equivalent where one exists, and an explicit acceptance of the undocumented token where it does not (Gotcha 46) |
| "Which picklist fields does the expression touch, and are you comparing to a label or an API name?" | `=` against a picklist literal compares the rendered label; it passes in an English-only dev org and turns false when a translation lands | Every picklist comparison rewritten as `ISPICKVAL` / `INCLUDES`, and a note that compound fields accept *neither* (Gotcha 47) |
| "How many elements reference this resource, and how many of them sit inside a Loop?" | Each `{!resourceName}` reference re-evaluates the whole expression; references × iterations is the real cost, and the CPU ceiling is 10,000 ms sync / 60,000 ms async (`apexdev.txt` L19578) | The reference count, and an Assignment-cached variable when the product is large enough to matter (Gotcha 3) |
| "Which org is this deploying to, and are its Process Automation Settings identical to the source org?" | Four documented `FlowSettings` switches change what an *unchanged* formula does: `doesFormulaEnforceDataAccess`, `doesFormulaGenerateHtmlOutput`, `enableFlowBREncodedFixEnabled`, `enableFlowFormulasFixEnabled` (`api_meta.txt` L116855–L116915) | A same-formula-different-orgs risk that is otherwise invisible in a diff (Gotchas 41–44) |

What a proper formula design adds over just writing the expression: the return type is declared rather than defaulted, every nullable operand is guarded inside the resource where the next caller inherits the guard, the entry condition uses the mechanism the guide documents rather than the one folklore recommends, and a `FlowTest` pins the *value* the formula returns so a later edit that changes it fails a test instead of a customer.

---

## Core Concepts

### Concept 1: Four places formulas appear (one language, four contexts)

The Flow formula language is a subset of the standard Salesforce formula language. The function list is defined by the **Formula Operators and Functions** reference, a help.salesforce.com article this repo cannot fetch — so which functions are legal in Flow is answered from the org instead: `SELECT Function.Name FROM FormulaFunctionAllowedType WHERE Type = 'FLOW'` (`object_reference.txt` L149310–L149400 documents the object and its restricted `Type` picklist `FLOW | VALIDATION | VISUALFORCE`). The same syntax appears in four distinct evaluation contexts:

1. **Formula resource** — declared once under Resources, referenced by `{!FormulaResourceName}`. Lazy: evaluates each time it's referenced.
2. **Decision condition expression** — formula entered directly inside an outcome's condition row when "Formula Evaluates to True" is selected. Evaluates once when the Decision element runs.
3. **Screen-component formula property** — formulas inside Display Text, default values, validation, and reactive component bindings. Evaluates per-screen-render in flow runtime.
4. **`filterFormula` on `<start>`** — the record-triggered entry condition, `api_meta.txt` L72390–L72392, API version 55.0 and later. Evaluates once per triggering record during the save, before any element runs.

All four share the same function library plus flow globals. Of those globals only `{!$Flow.CurrentDateTime}` (`api_meta.txt` L27212, L73380), `{!$Flow.ActiveStages}` (L69784–L69840) and `{!$Flow.CurrentStage}` (L71996) appear anywhere in the Metadata API guide. UNVERIFIED (2026-09-05): `{!$Flow.CurrentDate}`, `{!$Flow.FaultMessage}` and `{!$Flow.InterviewStartTime}` return **zero** grep hits — they are real, but undocumented in this corpus, and `{!$Flow.InterviewGuid}` is undocumented too (the sibling `flow/fault-handling` reached the same negative). Validation Rule formula context is not identical; `FormulaFunctionAllowedType.Type` is the field that tells you where a given function is legal.

### Concept 2: Lazy re-evaluation (the loop-body performance trap)

Flow does not memoise Formula resource results: every `{!FormulaResourceName}` reference triggers a fresh evaluation. UNVERIFIED (2026-09-05) — this is the observed and universally-reported behaviour, and every performance recommendation in this skill rests on it, but it is not stated in `api_meta.txt`, `apexdev.txt` or the App Limits cheat sheet. What *is* grounded is the budget you spend against: CPU 10,000 ms synchronous / 60,000 ms asynchronous (`apexdev.txt` L19578). The cost compounds:

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

### Concept 4: The formula's XML is half the contract

A formula is not just its expression. `FlowFormula` (`api_meta.txt` L70596–L70622) has three fields and two of them are routinely omitted:

| Field | Guide says | Consequence of omitting it |
|---|---|---|
| `dataType` | `Boolean`, `Currency`, `Date`, `DateTime`, `Number`, `String`, `Time`; API 31.0+. *"dataType defaults to Number if it isn't defined in a formula."* | A Text or Boolean formula silently becomes a Number formula. The error surfaces at the call site that consumes it, not at the formula. |
| `expression` | *Required.* *"Salesforce formula expression. The return value must match the data type."* | Deploy failure — this one is loud. |
| `scale` | *"the number of digits to the right of the decimal point. Available only when the data type is Number or Currency. Corresponds to the Decimal Places field in Flow Builder."* | The guide states no default. A Currency formula feeding a Currency field can write a value that does not match what the record displays. |

The neighbouring resource types matter too. `FlowTextTemplate` (L72820–L72831) has `isViewedAsPlainText`, **default `false`, and `false` means rich text** — so a template written as plain prose with `false` will have any stray `<` interpreted as markup, and a template full of HTML with `true` renders the tags literally. `text` *"Supports merge fields"*, and a merge field naming a resource that does not exist is a deploy failure the flow-level error message does not localise for you.

`references/metadata-examples.md` carries the deployable version of all of this, plus the `FlowTest` that asserts the resulting value.

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
| Expression growing past ~3,000 chars | Multiple composed Formula resources OR an Invocable Apex action | The only grounded source-length figure is 3,900 characters (`apexdev.txt` L28144), stated for formula fields; composition keeps every layer well under any ceiling that turns out to apply. |
| Entry condition needs a function, not a field/operator/value row | `filterFormula` on `<start>` | `api_meta.txt` L72390, API 55.0+. Condition rows (`FlowRecordFilter` L71066–L71090) have no function grammar. |
| Decision outcome branches on a computed Boolean | Boolean `FlowFormula` + `leftValueReference` + `EqualTo true` | Fully documented (`FlowRule` L71301–L71325); assertable by `FlowTest`; reusable by a second rule. The inline formula-mode body is not documented at all. |
| String concatenation that includes a Date and runs in a multi-locale org | `TEXT(DateVar)` + manual format OR an Invocable | Implicit concat uses running-user locale; explicit `TEXT()` returns deterministic ISO. |
| Boolean expression of 5+ ANDs/ORs with nullable inputs | Wrap each input with `BLANKVALUE` first, then combine | NULL propagation makes naïve `AND(...)` evaluate to NULL not FALSE. |
| "Has any of these picklist values" against a multi-select | `INCLUDES(MultiPicklistField__c, "value")` | `INCLUDES` is the only correct primitive for multi-select. |

---

## Recommended Workflow

1. **Fix the return type in the XML before you write the expression.** Open the target
   `<formulas>` block and set `<dataType>` explicitly — it defaults to `Number` when absent
   (`api_meta.txt` L70599–L70609) — plus `<scale>` if the type is `Number` or `Currency`.
   `references/metadata-examples.md` §1 is the shape; the guide's own flow sample at
   `api_meta.txt` L73357–L73362 is the minimum.
2. **Guard the nullable operands inside the resource, not at the call site.** List which
   operands are optional on a real record, wrap each with `BLANKVALUE` or
   `IF(ISBLANK(...), default, value)`, then compose the rest. A guard added at one call
   site is a guard the next call site does not get. `references/gotchas.md` Gotchas 1, 47,
   48 are the failure modes this step closes.
3. **Pick the mechanism the guide documents.** Entry condition that needs a function →
   `filterFormula` on `<start>` (`api_meta.txt` L72390, API 55.0+). Decision outcome →
   a Boolean `FlowFormula` referenced by `leftValueReference`, not an inline
   `conditionLogic` body the guide never documents (`references/metadata-examples.md` §4).
   Prior-value test → `doesRequireRecordChangedToMeetCriteria` before `$Record__Prior`
   (§1 "How to read it").
4. **Count the references, then decide whether to cache.** Multiply `{!resourceName}`
   occurrences by the worst-case iteration count of any enclosing Loop. If the product is
   large and the expression is more than one field reference, materialise it once in an
   Assignment and point every downstream element at the variable. The ceiling you are
   spending against is 10,000 ms synchronous / 60,000 ms asynchronous CPU
   (`apexdev.txt` L19578).
5. **Run the checker over the retrieved source.**
   `python3 scripts/check_flow_formula_and_expression_patterns.py --manifest-dir
   force-app/main/default --strict`. It reads the flow XML, not your intent: undeclared
   `dataType`, Number/Currency without `scale`, a `{!name}` that resolves to nothing in the
   flow, a text template merging a resource that does not exist, `filterFormula` sitting
   next to `filters`, an empty formula body on a formula-mode decision rule, and an
   expression past the advisory length threshold.
6. **Assert the value, not the syntax, with a FlowTest.** `references/metadata-examples.md`
   §2 pins `netClaimAmount` to a number for a record whose optional field is absent — the
   exact case a missing `BLANKVALUE` breaks. `FlowTest` is API 55.0+ and asserts only at
   `Start` and `Finish` (`api_meta.txt` L74138–L74146), so assert the guard and the branch,
   not the arithmetic.
7. **Settle every "does this function exist in Flow" question from the org, not from
   memory.** `SELECT Function.Name, Function.ExampleString FROM FormulaFunctionAllowedType
   WHERE Type = 'FLOW'` (`object_reference.txt` L149310–L149400). The Formula Operators and
   Functions reference is a help article this repo cannot fetch; this query is the
   substitute, and it is authoritative for the org you are deploying to.

---

## Review Checklist

- [ ] Every nullable input is wrapped with `BLANKVALUE` or `IF(ISBLANK(...), default, value)`.
- [ ] Every picklist comparison uses `ISPICKVAL` (single) or `INCLUDES` (multi), not `=`.
- [ ] Every Text↔Number, Text↔Date, Text↔DateTime coercion uses `VALUE` / `TEXT` / `DATEVALUE` / `DATETIMEVALUE` explicitly.
- [ ] Formula resources referenced inside a Loop body are either trivial (single field reference, single arithmetic op) or cached in an Assignment.
- [ ] Every `<formulas>` block declares `<dataType>` explicitly, and `<scale>` when that type is Number or Currency.
- [ ] Every `{!name}` inside an expression or a text template resolves to a resource, variable, constant, formula or element that exists in the same flow.
- [ ] `<start>` does not carry `filterFormula` and `filters` at the same time (the guide does not say which wins).
- [ ] Each Formula resource is well under 3,900 characters; composed chains used for any larger expression.
- [ ] `TODAY()` vs `NOW()` choice is documented when used in a multi-TZ org — confirm the right TZ semantic is desired.
- [ ] Decision condition formulas and Screen-component formulas have been reviewed with the same NULL-safety + coercion checklist as standalone Formula resources.
- [ ] Composed formula chains do not exceed 3 layers of nesting (FormulaA → FormulaB → FormulaC); deeper chains should become Apex Invocable.
- [ ] Every function used appears in `SELECT Function.Name FROM FormulaFunctionAllowedType WHERE Type = 'FLOW'` against the target org — not merely in someone's memory of the help article.
- [ ] Target-org Process Automation Settings match the source org for the four `FlowSettings` switches that change formula behaviour (`references/gotchas.md` Gotchas 41–44).
- [ ] `python3 scripts/check_flow_formula_and_expression_patterns.py --manifest-dir <src> --strict` exits 0.

---

## Salesforce-Specific Gotchas

1. **NULL propagates through arithmetic and Boolean operators.** `NULL + 1 = NULL`, `NULL && TRUE = NULL`, `NULL > 0 = NULL`. A Decision condition that depends on a NULL-tainted formula either throws "Comparison value cannot be null" or quietly takes the default outcome — both are P1 production failures.
2. **`=` against a picklist literal is a silent locale bug.** `{!Account.Industry} = "Healthcare"` compares the value the user sees (label) to the literal string. Translation packs, label edits, or API-name vs label drift all turn this comparison FALSE without warning. Always use `ISPICKVAL`.
3. **Lazy re-evaluation inside Loop bodies multiplies CPU cost.** Every `{!FormulaResourceName}` reference re-runs the formula. Six references × 200 iterations = 1,200 evaluations. Cache in an Assignment when the formula is non-trivial and referenced more than twice in a loop body.
4. **The formula-length ceiling everyone quotes is not in the guides.** Neither "5,000 characters" nor the error string "Compiled formula is too big to execute" appears in `api_meta.txt`, `object_reference.txt`, `apexdev.txt` or the App Limits cheat sheet. The grounded figure is 3,900 source characters (`apexdev.txt` L28144) and it is stated for formula fields, not for `FlowFormula`. UNVERIFIED (2026-09-05): the Flow binding. Compose at ~3,000; the composition mechanic itself is grounded by the guide's own flow sample (L73357–L73362).
5. **`TODAY()` and `NOW()` use different time zones.** `TODAY()` returns the running user's local date in the user's TZ. `NOW()` returns the org's default TZ. In a multi-TZ org, "TODAY at 1am Pacific" and "TODAY at 1am Eastern" are different dates — formulas comparing `TODAY()` to a stored Date can be off-by-one for users on the far side of the org's default TZ.
6. **`TEXT(picklist)` returns the API name, not the label.** Any user-facing string built from `TEXT(PicklistField__c)` will show the API name. Use a Get-Records on a Custom Metadata mapping or a hardcoded `CASE` to map to label.
7. **Implicit Date-to-Text concatenation uses the running-user locale.** `"Created on " & {!recordVar.CreatedDate}` returns "10/27/2026" for US users and "27/10/2026" for UK users. Use `TEXT({!recordVar.CreatedDate})` for deterministic ISO output, or format explicitly with `LEFT/MID/RIGHT` of `TEXT()`.
8. **Decision conditions evaluate referenced formulas EVERY time the Decision runs.** A Decision inside a Loop body that references 3 Formula resources costs 3 evaluations per iteration — auditable in the same way as element-level references.
9. **An omitted `<dataType>` makes the formula a Number formula.** `api_meta.txt` L70609 states the default outright. This is the highest-yield single check on any retrieved flow.
10. **`isViewedAsPlainText` defaults to `false`, and `false` means rich text.** `api_meta.txt` L72824–L72829. The name reads like the opposite of what it does, which is why templates get shipped with the wrong one.
11. **Four org-level `FlowSettings` switches change what an identical formula does.** `doesFormulaEnforceDataAccess`, `doesFormulaGenerateHtmlOutput`, `enableFlowBREncodedFixEnabled`, `enableFlowFormulasFixEnabled` (`api_meta.txt` L116855–L116915). A formula that returns null in sandbox and throws in production has not changed; the org has.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Formula resource definition | Frontmatter (name, return type, dependencies on input vars), expression body with NULL guards and explicit coercion. |
| Cached-variable Assignment refactor | When the formula was being re-evaluated inside a loop — the Assignment that materialises the result and the list of downstream references switched to read the cached variable. |
| Composed formula chain | When one expression grew past the advisory threshold — the parent + child Formula resources, each independently short. |
| Deployable flow XML | `<formulas>` with `dataType` and `scale`, `filterFormula` on `<start>`, `<textTemplates>` with `isViewedAsPlainText`, and a decision rule that reads a Boolean formula resource. Shape: `references/metadata-examples.md` §1. |
| `FlowTest` | Asserts the formula's runtime value at `Start`/`Finish` before the flow is activated. Shape: `references/metadata-examples.md` §2. |
| Checker run | `scripts/check_flow_formula_and_expression_patterns.py --strict` output over the retrieved source, with each finding's rule id. |
| Decision-condition rewrite | When the original `=` against a picklist label was a bug — the `ISPICKVAL` or `INCLUDES` rewrite. |
| Review report | Itemised list of NULL-guards added, picklist comparisons rewritten, type coercions made explicit, and re-evaluation hot-spots fixed, with line-level pointers in the flow XML or screenshot evidence. |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing or reviewing the actual flow XML — `FlowFormula` `dataType`/`expression`/`scale`, `filterFormula` on `<start>`, `FlowTextTemplate`, a decision rule that branches on a formula, the `FlowTest` that asserts the result, `package.xml`, deploy order, and the two SOQL verifications. Also carries the grep-level negative results (what is *not* in the guides). |
| `references/gotchas.md` | A formula deploys and then behaves wrongly — null propagation, picklist comparison, type coercion, the four org-level `FlowSettings` switches, compound-field function restrictions, and the metadata-level defaults that bite. |
| `references/llm-anti-patterns.md` | Before returning generated formula text or flow XML — the self-check list for the mistakes assistants make in this dialect. |
| `references/examples.md` | You want a worked expression to adapt: null guards, picklist comparisons, date math, composition, and the `FlowFormula` XML those expressions sit inside. |
| `references/well-architected.md` | You are choosing between a formula resource, a cached Assignment and an Invocable, or writing up the tradeoff for a reviewer. |

---

## Related Skills

- `flow/flow-resource-patterns` — broader guidance on naming, scoping, and choosing among Variable / Constant / Formula / Choice / Stage resources. This skill handles the formula-specific subset.
- `flow/flow-decision-element-patterns` — when the formula is being authored as the condition of a Decision outcome, pair these two skills.
- `admin/formula-fields` — for record-level formula fields on objects (a different runtime context — same language, but evaluated by the platform on read, with field-history and reportability concerns this skill does not cover).
- `flow/flow-collection-processing` — when caching a formula across loop iterations, the assignment pattern interacts with collection-iteration patterns documented there.
- `flow/flow-bulkification` — performance audits of formula re-evaluation overlap with broader bulkification work.
- `flow/flow-loop-element-patterns` — formula re-evaluation is one of the top performance traps inside Loop bodies; cross-reference for loop-body design.
- `flow/flow-runtime-error-diagnosis` — when "Comparison value cannot be null" or "The formula expression is invalid" surfaces at runtime, that skill handles the diagnostic flow; this skill handles the prevention.
- `flow/flow-record-save-order-interaction` — owns `doesRequireRecordChangedToMeetCriteria`, the documented alternative to a `$Record__Prior` comparison in an entry condition.
- `flow/fault-handling` — owns `$Flow.FaultMessage` and the fault-path interior; this skill only supplies the formula that builds the log line.
- `flow/flow-testing` — owns `FlowTest` generally; §2 of `references/metadata-examples.md` is the formula-assertion slice of it.
- `admin/validation-rules` — owns validation formulas, including `ISCHANGED` and `PRIORVALUE`, which are a different formula context (`FormulaFunctionAllowedType.Type = 'VALIDATION'`).

---

## Official Sources Used

Grounded in the extracted PDF corpus (line numbers are `grep -n` hits):

- Metadata API Developer Guide — `FlowFormula` `dataType`/`expression`/`scale`, L70596–L70622 (Concept 4, Recommended Workflow step 1) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `FlowStart.filterFormula` L72390–L72392 and `filters`/`filterLogic` L72395–L72404 (Concept 1 context 4, Decision Guidance) — same PDF
- Metadata API Developer Guide — `FlowTextTemplate.isViewedAsPlainText` L72820–L72831 (Concept 4, Gotcha 10) — same PDF
- Metadata API Developer Guide — `FlowRule.conditionLogic` L71301–L71325 (Decision Guidance; the inline formula mode is *absent* here) — same PDF
- Metadata API Developer Guide — `FlowTest` / `FlowTestPoint` / `FlowTestAssertion` L73960–L74400 (Recommended Workflow step 6) — same PDF
- Metadata API Developer Guide — `FlowSettings` L116849–L116915, four formula-affecting switches (Questions row 7, Gotcha 11) — same PDF
- Object Reference — `FormulaFunctionAllowedType` L149310–L149400, restricted `Type` picklist `FLOW | VALIDATION | VISUALFORCE` (Concept 1, Recommended Workflow step 7) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Apex Developer Guide — 3,900 formula source characters, L28143–L28144 (Before Starting, Gotcha 4) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide — CPU 10,000 ms sync / 60,000 ms async, L19578 (Questions row 6, Recommended Workflow step 4) — same PDF

Function semantics (`ISBLANK`, `ISPICKVAL`, `BLANKVALUE`, `TEXT`, `CASE`, `MOD`, `MAX`, `VALUE`, `INCLUDES`, `REGEX`, `ROUND`) come from **Formula Operators and Functions**, https://help.salesforce.com/s/articleView?id=sf.customize_functions.htm — a help article this repo cannot fetch. Every semantic claim resting on it is marked UNVERIFIED (2026-09-05) at the point of use, and `FormulaFunctionAllowedType` is the org-side substitute for the membership question.
