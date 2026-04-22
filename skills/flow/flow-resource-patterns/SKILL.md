---
name: flow-resource-patterns
description: "Flow resource types and when to use each: Variables, Collection Variables, Constants, Formulas, Text Templates, Choices, Stages, Picklist Choice Sets, Record Choice Sets. Covers scope, data types, and reuse patterns. NOT for decision elements. NOT for custom metadata (use admin/custom-metadata-types)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - flow
  - variables
  - formulas
  - constants
  - choice-sets
  - text-template
triggers:
  - "flow variable vs constant vs formula when to use"
  - "flow collection variable sobject add to collection"
  - "flow text template merge fields email body"
  - "flow picklist choice set dynamic from record"
  - "flow formula resource reuse versus assignment"
  - "flow sobject variable null initialization"
inputs:
  - Flow type (screen, record-triggered, autolaunched)
  - Data you need to hold, compute, or render
outputs:
  - Correct resource choice per use case
  - Naming + scoping guidelines
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-22
---

# Flow Resource Patterns

Activate when designing or debugging a flow's data layer — variables, formulas, constants, collections, text templates, choice sets. Picking the right resource type avoids brittle assignment chains and makes the flow debuggable.

## Before Starting

- **Determine reuse vs one-off.** Formulas recompute every reference and are ideal for derived values; assignments cache a value and are faster when referenced many times.
- **Understand scope.** All resources are flow-scoped — not global. Subflows need input/output variables.
- **Think about null.** Uninitialized variables return null, not zero or empty string.

## Core Concepts

### Variable vs Constant vs Formula

| Resource | Mutable? | Recomputes? | Use when |
|---|---|---|---|
| Variable | Yes (via Assignment) | No | Holding mutable state across elements |
| Constant | No | No | Hardcoded value reused multiple times (e.g. record type Id) |
| Formula | No (derived) | Yes, every reference | Computing a value from other resources (e.g. `{!Amount} * 0.1`) |

### Collection variables

A collection holds multiple values of the same type (primitive or SObject).

- **Primitive collection** — `Text[]`, `Number[]` — for filters, merge targets.
- **SObject collection** — `Contact[]` — for bulk DML.
- **Add elements with Assignment + "Add" operator**, or populate from Get Records.

### SObject variables

Hold one record's fields. Initialized to null. Getting a single record populates an SObject variable; referencing a field on a null SObject throws `NullPointerException`-style error.

### Text templates

Rich-text or plain-text blocks with merge fields. Primary use: email body, screen display. Plain-text mode needed for Send Email action if the recipient expects non-HTML.

### Choice resources

| Resource | Source | Use when |
|---|---|---|
| Choice | Hardcoded label/value | Yes/No, small static lists |
| Picklist Choice Set | Picklist field on an object | Reflects admin-maintained picklist |
| Record Choice Set | SOQL against any object | Dynamic list (e.g., active accounts) |
| Collection Choice Set | Collection variable | Choices derived from in-flow data |

## Common Patterns

### Pattern: Derived value as Formula (not Assignment)

```
Formula: Discounted_Amount = {!Amount} - {!Amount} * {!Discount_Rate}
```

Formulas stay synced; an Assignment value goes stale when inputs change.

### Pattern: Collection-of-ids for IN-filter

```
Assignment: Add {!$Record.Id} to collection accountIds
Get Records: Contact where AccountId IN accountIds
```

### Pattern: Email body as Text Template

Text Template with merge fields → referenced from Send Email Action Body. Easier to test than inline string concatenation in Assignments.

### Pattern: Config via Constants (not hardcoded values)

```
Constant: DEFAULT_REGION = "NAMER"
Used in: 4 Decision elements and 1 Create Records field map
```

Swapping the constant in one place updates all references.

## Decision Guidance

| Need | Resource |
|---|---|
| Hold changing value | Variable |
| Reuse a literal many times | Constant |
| Derive value from inputs | Formula |
| Collect records / primitives | Collection Variable |
| Hold one record | SObject Variable |
| Build a formatted string/email | Text Template |
| Let user pick from hardcoded options | Choice |
| Show picklist values | Picklist Choice Set |
| Show live records | Record Choice Set |
| Show in-memory collection | Collection Choice Set |

## Recommended Workflow

1. Inventory the values the flow needs: derived, cached, shared, per-element.
2. Choose resource type per the table above.
3. Name with a prefix that encodes scope and type (e.g. `v_` variable, `c_` constant, `f_` formula, `col_` collection, `tt_` text template).
4. Initialize SObject variables defensively (check null before dot-access).
5. Prefer formulas over "assignment chains" for derived values.
6. Avoid "magic number" literals in element fields — promote to Constants.
7. Document non-obvious formulas with a Description.

## Review Checklist

- [ ] No duplicated literals — promoted to Constants
- [ ] Derived values computed by Formulas, not Assignments
- [ ] Collection variables typed correctly (SObject vs primitive)
- [ ] SObject field references null-guarded
- [ ] Naming prefix convention applied
- [ ] Description filled on every non-trivial resource

## Salesforce-Specific Gotchas

1. **Collection variables do not deduplicate.** Adding the same record twice leaves two entries; loops see both.
2. **Formulas recompute every reference.** Heavy formulas referenced inside a loop multiply cost — cache in an Assignment if recompute is expensive.
3. **Formula return types cannot be changed after saving without errors in downstream references.** Plan the return type upfront.
4. **`{!$Record}` changes meaning in scheduled paths after a DML in the same transaction** — the in-memory record does not reflect mid-transaction updates.
5. **Text Template merge fields do not HTML-escape by default in rich-text mode** — user-entered text can break layout or inject markup. Use plain-text mode or strip HTML before inclusion.
6. **Choice labels and values are both strings** — a numeric-looking choice value is still text and must be Converted before numeric comparison.

## Output Artifacts

| Artifact | Description |
|---|---|
| Resource-type decision table | Quick-reference for which resource to use |
| Naming convention | Prefixes for variable, constant, formula, collection |
| Null-guard formula | `IF(ISBLANK(sobj.Field), default, sobj.Field)` |

## Related Skills

- `flow/flow-cross-object-updates` — uses collections to bulkify DML
- `flow/flow-best-practices` — naming conventions, documentation
- `admin/custom-metadata-types` — externalize flow configuration
