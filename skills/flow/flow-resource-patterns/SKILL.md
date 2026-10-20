---
name: flow-resource-patterns
description: "Flow resource types and when to use each: Variables, Collection Variables, Constants, Formulas, Text Templates, Choices, Stages, Picklist Choice Sets, Record Choice Sets. Covers scope, data types, and reuse patterns. Triggers: 'which Flow resource type', 'record choice set or picklist choice set', 'choice collection from records in a Flow' (the choice-set wiring itself is flow/flow-dynamic-choices). NOT for decision elements. NOT for custom metadata (use admin/custom-metadata-types)."
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
  - "flow record choice set dynamic picklist choice collection"
inputs:
  - Flow type (screen, record-triggered, autolaunched)
  - Data you need to hold, compute, or render
outputs:
  - Correct resource choice per use case
  - Naming + scoping guidelines
dependencies: []
version: 1.1.2
author: Pranav Nagrecha
updated: 2026-10-20
---

# Flow Resource Patterns

Activate when designing or debugging a flow's data layer — variables, formulas, constants, collections, text templates, choice sets. Picking the right resource type avoids brittle assignment chains and makes the flow debuggable.

## Before Starting

- **Determine reuse vs one-off.** Formulas recompute every reference and are ideal for derived values; assignments cache a value and are faster when referenced many times. UNVERIFIED (2026-10-20): per-reference recomputation and the speed claim are not in the corpus; `FlowFormula` is documented only as "Calculates a value using functions and elements in the flow" (api_meta 264 L73292).
- **Understand scope.** All resources are flow-scoped — not global. Subflows need input/output variables: `isInput` marks a variable that "can be set at the start of the flow using URL parameters, Visualforce controllers, or subflow inputs" and `isOutput` one whose value "can be accessed from Visualforce controllers and other flows" (api_meta 264 L75629-75631, L75648-75650). The flow-scoped claim itself is UNVERIFIED (2026-10-20): not stated in the corpus.
- **Think about null.** Uninitialized variables return null, not zero or empty string. UNVERIFIED (2026-10-20): the default value of an uninitialized variable is not in the corpus.

## Core Concepts

### Variable vs Constant vs Formula

| Resource | Mutable? | Recomputes? | Use when |
|---|---|---|---|
| Variable | Yes (via Assignment) | No | Holding mutable state across elements ("creates updatable values", api_meta 264 L75589) |
| Constant | No | No | Hardcoded value reused multiple times (e.g. record type Id); the value "can't have merge fields, nor can it reference another resource besides $GlobalConstant.EmptyString" (api_meta 264 L72921-72923) |
| Formula | No (derived) | Yes, every reference (UNVERIFIED (2026-10-20)) | Computing a value from other resources (e.g. `{!Amount} * 0.1`); `dataType` defaults to Number when not defined (api_meta 264 L73312) |

### Collection variables

A collection holds multiple values of the same type (primitive or SObject).

- **Primitive collection** — `Text[]`, `Number[]` — for filters, merge targets.
- **SObject collection** — `Contact[]` — for bulk DML.
- **Add elements with Assignment + "Add" operator** ("When the assignToReference field is a collection variable, this operator appends the value to the end of the collection", api_meta 264 L72366-72367), or populate from Get Records. `AddAtStart` adds at the beginning (L72374-72375). The `Add` operator "isn't supported when the assignToReference field is a variable of type boolean, dateTime, or sObject" (L72371-72372).

### SObject variables

Hold one record's fields. Initialized to null. Getting a single record populates an SObject variable; referencing a field on a null SObject throws `NullPointerException`-style error. UNVERIFIED (2026-10-20): the null initialization and the error behavior are not in the corpus.

### Text templates

Rich-text or plain-text blocks with merge fields (`text` "Supports merge fields", api_meta 264 L75572). Primary use: email body, screen display. Plain-text mode needed for Send Email action if the recipient expects non-HTML. UNVERIFIED (2026-10-20): the metadata field `isViewedAsPlainText` only "remembers the View as Plain Text setting used for the text template" and defaults to false (api_meta 264 L75566-75570); that plain-text mode controls the sent email format is not in the corpus.

### Choice resources

| Resource | Source | Use when |
|---|---|---|
| Choice | Hardcoded label/value | Yes/No, small static lists |
| Picklist Choice Set | Picklist field on an object | Reflects admin-maintained picklist |
| Record Choice Set | Records of one object, with filters, sort and a limit (maximum and default 200, api_meta 264 L73012-73022) | Dynamic list (e.g., active accounts) |
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

## Choosing Between Choice Resources

Three Flow resources present a list of options and they are not interchangeable. A **Choice** is one hand-typed label and value — right for a fixed yes/no or a short constant list. A **Picklist Choice Set** generates choices from "the available values for a picklist or multi-select picklist field" (api_meta 264 L72971-72973) at run time (L72965-72966), so the Flow follows the field without redeploying; it cannot filter (L73015). A **Record Choice Set** reads records with a filter and sort (at most 200 choices, api_meta 264 L73017-73018), maps one field to the label (`displayField`, L73002) and one to the stored value, and can assign the chosen record's other fields to variables (`outputAssignments`, L73040-73045); it is the resource for a dynamic choice collection driven by data. A collection variable of records is not a choice resource — to offer records as choices, bind a Record Choice Set to it (`collectionReference` is "The collection that's used to generate choices", API 54.0 and later, api_meta 264 L72976-72977). Dependent choices (one set filtered by another's selection) and the metadata shapes for all three are `flow/flow-dynamic-choices`; this skill decides which resource fits and how it is scoped and reused.

## Recommended Workflow

1. Inventory the values the flow needs: derived, cached, shared, per-element.
2. Choose resource type per the table above.
3. Name with a prefix that encodes scope and type (e.g. `v_` variable, `c_` constant, `f_` formula, `col_` collection, `tt_` text template).
4. Initialize SObject variables defensively (check null before dot-access).
5. Prefer formulas over "assignment chains" for derived values.
6. Avoid "magic number" literals in element fields — promote to Constants.
7. Document non-obvious formulas with a Description.

## Questions to Ask Before Configuring

Ask these before choosing a resource type. Each one maps to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is this value fixed at design time, or does it depend on the record?" | A Constant cannot hold a merge field or another resource (api_meta 264 L72921-72923) (gotcha 1) | Constant versus Formula decided up front |
| "Is a derived value referenced many times inside a Loop?" | Caching a heavy Formula in a Variable is this package's pattern; the per-reference recomputation and cost claims are UNVERIFIED (2026-10-20) in the corpus (gotcha 2) | The reference count per iteration and a measured CPU figure |
| "Which variables must be visible to a parent flow, page or Visualforce?" | `isInput` and `isOutput` are separate flags and disabling one "can break the functionality of applications and pages that call the flow" (api_meta 264 L75641-75646) (gotcha 3) | A written contract: variable names, data types, flags |
| "Does a screen choice need to remember the selection on Previous?" | The choice resource describes options only; selection storage is a screen setting (gotcha 4, UNVERIFIED in the corpus) | The bound variable for each choice component |
| "Is this a picklist field's values, or a list of records?" | A picklist choice set cannot filter; a record choice set returns at most 200 choices (api_meta 264 L73012-73018) (gotchas 5, anti-pattern 5) | Picklist or Record choice set picked on that basis |
| "What `dataType` does each Choice declare?" | The value follows the Choice's `dataType` (api_meta 264 L72471-72477) (SKILL gotcha 6) | A data type per Choice, checked before any comparison |
| "Is the flow run in user or system context?" | `runInMode` decides whether the running user's object and field permissions apply to a record choice set (api_meta 264 L70907-70927) | The context chosen, with `flow/flow-runtime-context-and-sharing` read first |

A proper configuration adds a resource type chosen per lifecycle, a stated variable contract and a choice set matched to its source, none of which "just adding variables" provides.

## Review Checklist

- [ ] No duplicated literals — promoted to Constants
- [ ] Derived values computed by Formulas, not Assignments
- [ ] Collection variables typed correctly (SObject vs primitive)
- [ ] SObject field references null-guarded
- [ ] Naming prefix convention applied
- [ ] Description filled on every non-trivial resource

## Salesforce-Specific Gotchas

1. **Collection variables do not deduplicate.** Adding the same record twice leaves two entries; loops see both. UNVERIFIED (2026-10-20): not in the corpus (`Add` appends to the end, api_meta 264 L72366).
2. **Formulas recompute every reference.** Heavy formulas referenced inside a loop multiply cost — cache in an Assignment if recompute is expensive. UNVERIFIED (2026-10-20): recomputation per reference is not in the corpus.
3. **Formula return types cannot be changed after saving without errors in downstream references.** Plan the return type upfront. UNVERIFIED (2026-10-20): the downstream-reference behavior is not in the corpus; `dataType` defaults to Number if undefined (api_meta 264 L73312).
4. **`{!$Record}` changes meaning in scheduled paths after a DML in the same transaction** — the in-memory record does not reflect mid-transaction updates. UNVERIFIED (2026-10-20): not in the corpus.
5. **Text Template merge fields do not HTML-escape by default in rich-text mode** — user-entered text can break layout or inject markup. Use plain-text mode or strip HTML before inclusion. UNVERIFIED (2026-10-20): escaping behavior is not in the corpus.
6. **A Choice carries a `dataType`, so check it before comparing.** `FlowChoice.dataType` is one of Currency, Date, Number, String, Boolean or Time (api_meta 264 L72471-72477); the label `choiceText` is text and the `value` takes the declared type (L72469-72484). A Choice declared String holds text and must be converted before numeric comparison; one declared Number does not. The earlier text said labels and values are always both strings.

## Output Artifacts

| Artifact | Description |
|---|---|
| Resource-type decision table | Quick-reference for which resource to use |
| Naming convention | Prefixes for variable, constant, formula, collection |
| Null-guard formula | `IF(ISBLANK(sobj.Field), default, sobj.Field)` |

## Related Skills

- `flow/flow-cross-object-updates` — uses collections to bulkify DML
- `flow/flow-element-naming-conventions` — naming conventions for elements and resources
- `admin/custom-metadata-types` — externalize flow configuration
