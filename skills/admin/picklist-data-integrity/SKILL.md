---
name: picklist-data-integrity
description: "Picklist governance for Salesforce admins — Restricted vs Unrestricted, Global Value Sets vs local picklists, value deactivation that breaks reports, dependent picklists with deactivated controllers, and the 'value not in picklist' phantom-data problem. Covers the per-record-type value selection model, the API-vs-label mismatch trap, and the mass-replace-values runbook. NOT for selection-list UX (that's LWC styling), NOT for the architectural decision of when to use a picklist vs lookup vs custom metadata."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "picklist restricted vs unrestricted decision"
  - "global value set vs local picklist field"
  - "deactivated picklist value records still using it"
  - "dependent picklist controller deactivated"
  - "picklist api name vs label mismatch"
  - "mass replace picklist value across records"
tags:
  - picklist
  - global-value-set
  - record-type
  - data-integrity
  - dependent-picklist
inputs:
  - "Picklist field's purpose: status / category / classification / external-system mirror"
  - "Whether the same value list appears on multiple objects (global-value-set candidate)"
  - "Per-record-type value subset requirements"
  - "Whether external systems write into the field via API (restricted vs unrestricted constraint)"
  - "Existing data volume on the field"
outputs:
  - "Restricted vs Unrestricted decision with justification"
  - "Global Value Set vs local-picklist decision"
  - "Per-record-type value-set assignment"
  - "Dependent-picklist mapping (if applicable) including controller-value coverage"
  - "Deactivation / replacement runbook for retiring values"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Picklist Data Integrity

Picklists look simple. They aren't. Restricted vs Unrestricted is a
data-quality control. Global Value Sets vs local picklists determines
whether a label change ripples or stops at one field. Deactivating a
value can leave existing records pointing at a "value not in
picklist" — visible in the UI as the value still appearing, but
filtered out of new selections. Dependent picklists where the
controller value gets deactivated produce records whose dependent
value is no longer reachable.

This skill covers the architectural decisions and the runbook for
picklist hygiene at scale.

What this skill is NOT. UI styling for picklist selection (LWC
combobox / lightning-record-edit-form behavior) is presentation
layer. The architectural decision "should this be a picklist at all
vs a lookup to a configuration object vs custom metadata" lives in
data-model design — see `data/data-model-fundamentals` or similar.

---

## Before Starting

- **Decide Restricted or Unrestricted upfront.** Restricted blocks
  API and Apex from writing values not in the picklist. Unrestricted
  permits anything (silently storing free-form text). Default for
  user-facing-only fields: Restricted. Default for fields that
  receive integration-system values: weighed against integration
  flexibility.
- **Decide Global Value Set vs local.** Global is shared across
  fields and objects; one place to add / remove / rename values.
  Local is field-specific; changes don't ripple. Pick global when
  the same domain (countries, categories, statuses) appears on
  multiple objects.
- **Identify per-record-type value subsets.** Different record types
  may show different value subsets of the same picklist. The
  per-record-type assignment is metadata, not a runtime filter.
- **Inventory existing data before deactivating values.** Records
  already using the value will still show it in their field —
  filtered out of new edits but persistent on existing records.

---

## Core Concepts

### Restricted vs Unrestricted picklists

| Setting | UI behavior | API / Apex behavior | Use case |
|---|---|---|---|
| **Restricted** | Only listed values selectable | API write rejected if value not in picklist (`INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`) | User-facing classification, status fields, anything where data quality matters |
| **Unrestricted** | Only listed values selectable | API can write ANY string (silently stored) | Integration-target fields where source system has its own value list; phasing migrations |

Unrestricted picklist + integration write = "phantom values" — the
field shows values that aren't in the picklist definition. They
appear on records but not in reports' picklist filters, not in Set
Up's value list. Source of confused users and admins.

### Global Value Sets

Defined in Setup → Picklist Value Sets. Reusable across multiple
picklist fields / objects. Changes (add value, rename value,
deactivate value) ripple to every consuming field.

| Decision | Right answer |
|---|---|
| Country list, used on Account, Contact, Lead, Opportunity | **Global** |
| Status field, unique to one object's lifecycle | **Local** |
| Category field, similar but slightly different per object | **Local** (different lists, despite similar shape) |
| Source-system code list, mirrored from external IDP | **Global** if used on multiple objects; otherwise local |

Global is more discipline (changes hit many fields); local is more
duplication. Pick by whether the value list is *the same domain*
across consumers.

### Value deactivation: the persistence trap

Deactivating a picklist value does NOT remove it from records that
already use it. The deactivated value:

- No longer appears in the picklist for new edits.
- Still appears on existing records that had it.
- Shows in standard reports under the deactivated value's label.
- Is filtered OUT of standard "all values" picklist reports —
  surprise for admins.

To migrate records off a deactivated value, you need a controlled
mass update (Data Loader, Flow, or Apex) that replaces the value
with a new active one. There is no "deactivate AND remove from all
records" platform action.

### Dependent picklists with deactivated controller values

Dependent picklists map controlling-value to dependent-value subset:
"if Country = US, show States: AK, AL, AR, ...". When the
controlling value (Country = US) is deactivated:

- Records with Country = US still have it.
- Their dependent State value is no longer accessible from edit UI
  (because no controlling-value path leads there).
- Mass-update of US records to a different country leaves orphaned
  State values that are now invalid.

Always plan the dependent-value migration BEFORE deactivating a
controller value.

### API name vs label mismatch

Picklist values have:

- **API name** (string identifier used in metadata, Apex, formulas).
- **Label** (display text user sees).

These are independent. Renaming the **label** does NOT change the
**API name**. Apex code, validation rules, and formulas that
reference the value reference the API name; they survive label
changes. But integration code that writes the **label** value
breaks if the label was renamed.

Common bug: admin renames "Pending" label to "Awaiting Review";
integration that posted `Pending` as the picklist value still
works (API name unchanged); integration that posted "Pending" via
literal string keyed off label might not.

---

## Common Patterns

### Pattern A — Restricted picklist as data-quality control

**When to use.** User-facing classification fields where any value
outside the defined list is wrong. Status, Priority, Type, Category.

**Setup.**

1. Field definition: `Restricted` checkbox on (the API name is
   `restrictPicklist` in metadata).
2. All existing values explicitly added to the picklist before
   enabling restriction (otherwise existing records' values become
   "phantom").
3. Validation rules NOT NEEDED for value validation — the picklist
   itself enforces it.

**Trade.** Integration that writes from an external system must
keep its value list synchronized with the picklist. A new value in
the source system requires adding it to the Salesforce picklist
before the integration writes it; otherwise the integration call
fails with `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`.

### Pattern B — Global Value Set for cross-object domain

**When to use.** Country lists, currency codes, category taxonomies
that appear on multiple objects.

**Setup.**

1. Setup → Picklist Value Sets → New.
2. Define values once.
3. Reference from each consuming picklist field (Field Definition →
   Use Global Value Set).

**Trade.** Changes ripple. Renaming a value in the global set
changes the label on every consuming field. Plan the rename as a
coordinated change.

### Pattern C — Value deactivation runbook

**When to use.** Retiring an obsolete picklist value while
preserving historical data integrity.

**Sequence.**

1. **Inventory existing usage.** Report on the field grouped by value
   to count records using the value-being-retired.
2. **Decide the migration target.** What value should records that
   currently use the obsolete value be migrated to?
3. **Build the migration.** Mass update (Data Loader, Flow, or
   Apex) that updates affected records to the target value.
4. **Run the migration in a sandbox first.** Confirm the count and
   sample records.
5. **In production:** run migration → verify zero records still
   using the old value → deactivate the value in the picklist.
6. **Optional: replace the deactivated value with the target value
   in the picklist's value-replacement workflow** (Setup → field →
   value → Replace) for any records you missed.

### Pattern D — Dependent picklist with controller deactivation

**When to use.** Restructuring a dependent-picklist hierarchy.

**Critical rule.** Migrate dependent values BEFORE deactivating the
controller value.

**Sequence.**

1. Inventory all records where Controller = `<value-being-deactivated>`.
2. Decide what the new Controller value + Dependent value should
   be for each record (often a 1-to-1 mapping; sometimes a manual
   review).
3. Mass-update Controller and Dependent atomically (same DML so the
   constraint is satisfied at every commit point).
4. Verify zero records remain on the controller-value being retired.
5. Deactivate the controller value.

The wrong order — deactivate controller first, then try to migrate
dependent values — leaves records in an unreachable state where the
dependent value can't be edited via UI.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| User-facing classification field | **Restricted** | Data quality matters; UI already constrains the user |
| Integration writes from a source system whose value list may diverge | **Unrestricted** with reconciliation | Integration flexibility; requires periodic sync |
| Same value list on multiple objects | **Global Value Set** | One place to manage |
| Different-but-similar-shape lists per object | **Local** picklists | Don't force-merge; semantic difference matters |
| Per-record-type value subset | **Record Type → Picklist Values** assignment | Metadata-driven; no Apex needed |
| Deactivating a value with thousands of records using it | **Pattern C runbook** | Migrate then deactivate |
| Deactivating a controlling value | **Pattern D runbook** | Migrate dependent first |
| Renaming a value's label | **Rename label only** — API name stays stable | Apex / formulas / validation rules unaffected |
| Renaming a value's API name | **Treat as a value migration** | Anything keyed on API name (Apex, formula, integration) breaks |
| Sorting picklist values | Default is creation order; **explicit sort** in field definition | Alphabetical sort is one option; business-priority sort is common |

---

## Recommended Workflow

1. **For new picklist fields:** decide Restricted vs Unrestricted, Global vs Local, per-record-type subset.
2. **For changes to existing picklists:** inventory usage first.
3. **For deactivations:** Pattern C (or D for dependents). Always migrate before deactivating.
4. **For renames:** rename **label** when possible (API name stays stable). Rename **API name** only when label changes don't satisfy the requirement, and treat it as a value migration.
5. **Validate after any change:** run a sample report grouped by the picklist field; confirm value counts match expectations.

---

## Review Checklist

- [ ] Restricted vs Unrestricted decision is documented per field.
- [ ] Global Value Set is used when the same value list appears on multiple objects.
- [ ] Per-record-type value subsets are explicit and deployed.
- [ ] No values are deactivated on production fields without a prior migration of records using them.
- [ ] Dependent picklist migrations migrate dependent values before deactivating controllers.
- [ ] No records have "phantom" values (values not in the current picklist definition) — periodic audit.
- [ ] Apex / formulas / validation rules reference picklist API names, not labels.

---

## Salesforce-Specific Gotchas

1. **Deactivating a value doesn't remove it from existing records.** They keep the value; UI no longer offers it for new edits. (See `references/gotchas.md` § 1.)
2. **Unrestricted picklist + API write = "phantom values".** Records show values not in the picklist definition. (See `references/gotchas.md` § 2.)
3. **Renaming the label doesn't change the API name.** Apex / formulas / validation rules referencing the value still work. (See `references/gotchas.md` § 3.)
4. **Dependent picklist with deactivated controller** leaves records' dependent values unreachable from the UI. (See `references/gotchas.md` § 4.)
5. **Global Value Set changes ripple to every consuming field.** Plan as coordinated changes. (See `references/gotchas.md` § 5.)
6. **Per-record-type value assignment is metadata, not a runtime filter** — the user's record type determines the visible value subset. (See `references/gotchas.md` § 6.)
7. **Inactive values still appear in some reports' historical buckets.** Reports filter by current picklist; field-history-rich reports can show inactive values. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Picklist field definition | Restricted / Unrestricted, Global / Local, per-record-type subsets |
| Migration runbook | For each value retirement: inventory, target, migration script, verification |
| Phantom-value audit query | SOQL that finds records whose picklist value isn't in the current value list |
| Dependent-picklist mapping | Controller-value → dependent-value pairs; coverage table |

---

## Related Skills

- `data/data-model-fundamentals` — when the architectural decision is "picklist vs lookup vs custom metadata".
- `flow/flow-time-based-patterns` — when picklist value changes drive scheduled flow paths.
- `apex/apex-event-bus-subscriber` — when external systems publish picklist-value-changed events that need org-side reconciliation.
- `admin/validation-rule-design` — when a picklist value combination needs cross-field validation beyond the picklist itself.
