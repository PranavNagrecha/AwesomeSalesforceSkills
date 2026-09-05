---
name: record-type-strategy-at-scale
description: "Use when designing or refactoring record types across objects with many profiles, business processes, or picklist variations. Covers layout assignment explosion, Dynamic Forms migration, and record type ID portability. NOT for basic record type setup or page layout assignment — use admin/record-types-and-page-layouts. NOT for converting one page layout to Dynamic Forms — use admin/dynamic-forms-migration. Trigger keywords: record type consolidation, layout assignment matrix, recordTypeVisibilities, layoutAssignments, Master record type default, bulk RecordTypeId migration, record type audit, RecordType wildcard package.xml."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Operational Excellence
triggers:
  - "too many page layout assignments and record type combinations are becoming unmanageable"
  - "how do I avoid the N times M layout explosion with record types and profiles"
  - "migrating record types to Dynamic Forms to reduce layout sprawl"
  - "record type IDs are different between sandbox and production causing deployment failures"
  - "consolidate two record types into one and migrate the existing records"
  - "users are defaulting to the Master record type after we moved access to permission set groups"
  - "audit which record types every profile can actually see across the whole org"
  - "package.xml wildcard retrieved no record types so my audit says the org has none"
  - "deactivating a record type deleted recordTypeVisibilities from every profile in the diff"
  - "bulk update of RecordTypeId failed validation rules on thousands of records"
  - "too many record types, consolidate or merge them"
tags:
  - record-type-strategy-at-scale
  - record-types
  - page-layouts
  - dynamic-forms
  - layout-assignment
  - picklist-values
  - record-type-consolidation
  - layout-assignment-matrix
  - recordtypevisibilities
  - bulk-record-type-migration
inputs:
  - "List of objects with record types and current record type count per object"
  - "Number of profiles and permission sets in the org"
  - "Whether Dynamic Forms is enabled and which objects are compatible"
  - "Which personas take record type access from a profile and which take it from a permission set group"
  - "Record counts per RecordTypeId for any record type proposed for retirement"
outputs:
  - "Record type rationalization plan with consolidation recommendations"
  - "Layout assignment matrix showing before and after state"
  - "Migration checklist for record type consolidation or Dynamic Forms adoption"
  - "Deployable Profile and PermissionSet fragments rendered from the assignment matrix"
  - "Per-persona record type availability audit output from Schema describe"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Record Type Strategy At Scale

This skill activates when a practitioner is dealing with record type proliferation across objects that have accumulated many profiles, business processes, or picklist overrides. It provides patterns for rationalizing record types, managing the quadratic layout assignment problem, and migrating toward Dynamic Forms where supported.

---

## Before Starting

Gather this context before working on anything in this domain:

- How many record types exist per object and how many profiles exist in the org? The layout assignment count is N record types multiplied by M profiles, so even modest growth creates quadratic complexity.
- Are practitioners assuming that record types are the only way to control field visibility? Dynamic Forms (Lightning App Builder component visibility filters) can replace many record-type-driven layout differences without creating new record types.
- The constraint that bites is not a hard limit, it is the operational cost of maintaining N record types x M profiles layout assignments and the picklist matrix underneath them. Use the count guide in `admin/record-types-and-page-layouts` (1-4 healthy, 5-8 monitor, 9-12 likely over-built, 13+ redesign) as the operating threshold. UNVERIFIED (2026-09-04): the frequently quoted "200 record types per object" ceiling does not appear in the extracted Metadata API Developer Guide, Object Reference, or Salesforce App Limits cheat sheet; do not quote a number to a client without checking the current limits documentation for their edition.
- Which personas take record type access from a profile and which take it from a permission set group. The answer changes what you can render: `PermissionSetRecordTypeVisibility` carries `recordType` and `visible` only, so the default record type and every layout assignment stay on the profile.

---

## Questions to Ask Before Configuring

Ask these before the first retrieve. Each one maps to a failure this package has seen; an agent that skips them produces a matrix that deploys cleanly and governs nothing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which personas hold which profile, and which record types do they get from a permission set instead?" | The `default` flag and every `layoutAssignments` entry can only live on `Profile`; a permission set carries `visible` and nothing else | The grant-carrier column of the matrix, and the list of profiles that must still be edited (gotchas #5, #6) |
| "On each object, which single record type is the default for each persona?" | A persona with no profile default falls back to the Master record type, which applies no picklist filtering, and nothing errors | Exactly one `default=true` per (object, persona), verified with the describe audit rather than assumed (gotchas #5) |
| "How many records sit on each record type we intend to retire, and which picklist values do they hold?" | Reassignment blanks any value absent from the target type, and the update itself runs every validation rule, duplicate rule, and flow on the object | The at-risk row count, the value union to deploy first, and the automation inventory for the load (gotchas #7) |
| "Will this consolidation deactivate record types, and how many profiles and permission sets reference them?" | Inactive record types stop being retrieved or deployed inside profiles and permission sets, so the next diff shows mass deletions with no stated cause | A pre-deactivation snapshot commit and a split deploy plan (gotchas #8) |
| "Where is the record type inventory for this audit coming from?" | `RecordType` does not support the `*` wildcard, so a wildcard manifest returns zero record types and the audit reads clean on a sprawling org | A generated member list from a `RecordType` query, plus a non-zero assertion on it (gotchas #9) |
| "For each candidate merge, is the difference field visibility, or picklist values and business process?" | Only the first is removable by a FlexiPage; the second is what a record type is for | The consolidation shortlist, separated from the types that must survive |
| "What are N and M today, and which is cheaper to reduce?" | The cost is the product, so retiring profiles improves every object at once while retiring record types improves one | A prioritised target list, and an honest answer about whether the real project is profile consolidation |

What a proper configuration adds over just doing it: the matrix becomes a reviewable artefact that the profile and permission set XML is generated from, every persona has a governed default instead of a silent fall back to Master, and the retirement of a record type is a planned three-deploy sequence with a verified record migration rather than a delete that reassigns thousands of rows by owner profile.

---

## Core Concepts

### The N x M Layout Assignment Problem

Every record type on an object must have a page layout assigned for every profile in the org. If an object has 8 record types and the org has 50 profiles, that is 400 layout assignment cells to manage. Adding one record type adds 50 new assignments; adding one profile adds 8. This grows quadratically and is the primary driver of record type sprawl pain. The matrix is stored as repeated `layoutAssignments` elements inside each `.profile-meta.xml` — `ProfileLayoutAssignments`, with a required `layout` and an optional `recordType` — so it deploys per profile, and `PermissionSet` has no equivalent field to move it to. The real per-profile row count is N + 1, because the entry with no `recordType` is the fallback rule that applies when nothing matches.

### Dynamic Forms as a Layout Multiplier Reducer

Dynamic Forms, available in Lightning App Builder, allows field-level visibility rules on a single page layout rather than requiring a separate layout per record type. A visibility filter can show or hide fields based on record type, field values, permissions, or device form factor. This means one flexible page can replace several static layouts. However, Dynamic Forms is not available on all standard objects — check compatibility before planning a migration. UNVERIFIED (2026-09-04): the per-object support list is a Salesforce Help topic and help.salesforce.com is not fetchable from this environment; confirm the current object list in Lightning App Builder for the target org before committing to a consolidation, and see `admin/dynamic-forms-migration` for the migration itself.

### The Assignment Matrix Is the Artefact

At scale the thing you govern is not any one record type, it is the **(object, record type, persona)** table with `visible`, `default`, and layout columns. Author that table first; generate the XML from it. Three properties of the platform make the table, rather than the files, the right unit of review:

| Column | Carrier | Why it cannot move |
|---|---|---|
| `visible` | `Profile` **or** `PermissionSet` | Both types have `recordTypeVisibilities` (API 29.0+ on permission sets) |
| `default` | `Profile` only | `PermissionSetRecordTypeVisibility` has exactly two fields, `recordType` and `visible` — there is no `default` to set |
| layout | `Profile` only | `layoutAssignments` is a field of `Profile`; `PermissionSet` has none |

A blank `default` column for a persona is not a neutral state. The user falls back to Master, documented in `Schema.RecordTypeInfo.isMaster()` as "the default record type that's used when a record has no custom record type associated with it" — and Master filters no picklist values. The worked table, both rendered fragments, and the generator are in `references/metadata-examples.md`.

### The Audit Surface Is Describe, Not SOQL

`RecordType` is queryable (`SobjectType`, `DeveloperName`, `IsActive`, `BusinessProcessId`, `IsPersonType`) and so are record counts per `RecordTypeId`. The **visibility matrix is not**: there is no standard object exposing which record types a profile or permission set grants. UNVERIFIED (2026-09-04): `RecordTypeVisibility` does not appear in the extracted Object Reference, so a SOQL-based visibility audit cannot be promised; the Setup path (Object Manager > *object* > Record Types, and Page Layouts > Page Layout Assignment) is the manual fallback. What does answer the question is `Schema.DescribeSObjectResult.getRecordTypeInfos()` evaluated as the running user — `isAvailable()`, `isDefaultRecordTypeMapping()`, `isActive()`, `isMaster()` per record type. Run it once per persona; it is the only check that reads the matrix the way a user experiences it.

### Record Type ID Portability

Record Type IDs are org-specific 18-character Salesforce IDs. They are not stable across sandboxes and production. Code or configuration that hardcodes a Record Type ID will break on deployment. The canonical Apex pattern for resolving Record Type IDs at runtime is `Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName().get('Enterprise').getRecordTypeId()`. In metadata (flows, validation rules), use `$Record.RecordType.DeveloperName` rather than a literal ID. In formulas, use `RecordType.DeveloperName` comparisons.

---

## Common Patterns

### Pattern 1: Consolidate Record Types, Differentiate with Dynamic Forms

**When to use:** An object has 5+ record types where the differences are primarily field visibility rather than distinct business processes or picklist value sets.

**How it works:**
1. Audit existing record types and catalog the actual differences (fields shown, picklist values, business process).
2. Identify record types that share the same business process and picklist values but differ only in field layout.
3. Merge those record types into one, retaining the picklist and business process definition.
4. Build a Dynamic Forms page in Lightning App Builder with component visibility rules to show or hide fields based on a controlling field or the remaining record type.
5. Union the retired types' picklist values onto the surviving record type and deploy that, plus the merged layout, first — this deploy is additive and reversible.
6. Migrate existing records using Bulk API 2.0 to update RecordTypeId to the consolidated record type, while the old types are still active. Records must not point at a type you are about to deactivate.
7. Only then deactivate the retired record types and prune their `recordTypeVisibilities` and `layoutAssignments` rows from every profile and permission set — keeping the fallback assignment that names no record type.

**Why not the alternative:** Keeping separate record types solely for field visibility means every new profile multiplies the layout assignment burden. Dynamic Forms eliminates that multiplier for field-visibility-only differences.

### Pattern 2: Business Process Alignment

**When to use:** Record types have drifted from their original business process intent and picklist values are inconsistent across record types on the same object.

**How it works:**
1. Export RecordType metadata XML for the object. Each record type references a BusinessProcess and contains picklistValues overrides.
2. Map each record type to its actual business meaning (e.g., "Enterprise Sale" vs. "SMB Sale" on Opportunity).
3. Normalize picklist values so that each record type's overrides reflect the real business process, not historical accidents.
4. Remove record types that represent the same business process under different names.
5. Redeploy the cleaned metadata using Metadata API or a change set.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Field visibility is the only difference between record types | Consolidate record types and use Dynamic Forms | Eliminates N x M layout explosion for field-only differences |
| Record types drive distinct picklist value sets or business processes | Keep separate record types | Picklist filtering and business process (Sales Process, Support Process) require distinct record types |
| Record Type IDs are referenced in Apex or Flows | Replace with DeveloperName-based lookups | IDs are org-specific and break across environments |
| Object is not Dynamic Forms compatible | Use fewer record types with broader layouts | Cannot rely on Dynamic Forms; minimize layout assignments manually |
| Org has 50+ profiles and growing | Migrate to permission sets and reduce profile count | Fewer profiles directly reduces the M in the N x M equation |

---

## Recommended Workflow

1. **Build the inventory the manifest cannot.** Run `SELECT SobjectType, DeveloperName, IsActive FROM RecordType` and the per-object counts grouped by `RecordTypeId`. Generate the `RecordType` members for your manifest from that result — `RecordType` takes no wildcard, and a starred manifest returns zero of them with no error (gotchas #9). The generator is in `references/metadata-examples.md` §6.
2. **Retrieve the whole matrix in one manifest.** Objects, layouts, record types, **and every profile and permission set** together. Retrieving a record type or layout changes what the profiles in the same package contain, so a narrow retrieve produces profiles missing assignments they actually have. Commands and order: `references/metadata-examples.md` §7.
3. **Lint what came back.** `python3 skills/admin/record-type-strategy-at-scale/scripts/check_record_type_strategy_at_scale.py --manifest-dir force-app/main/default --profile-count <M>`. Clear every ERROR (hardcoded Ids; a profile that grants record types on an object and defaults none of them) before designing anything; triage the WARNs (orphan record types, record types with no layout assignment anywhere, objects at 13+).
4. **Write the target matrix.** Use the table shape in `references/metadata-examples.md` §1 — one row per (object, record type, persona), plus the fallback row with no record type. Mark the grant carrier per cell. Anything that changes here must survive the questions above, especially the single `default=true` per (object, persona).
5. **Render the matrix into XML and stage three deploys, not one.** Deploy (a) the merged layout and unioned picklist values, then (b) nothing — the data migration runs alone — then (c) deactivations plus the pruned profiles and permission sets. Splitting them is what keeps the deactivation diff reviewable (gotchas #8) and closes the window where a user can pick a type with no layout.
6. **Run the data migration as a data project.** Preflight the at-risk picklist values, size the automation that will fire on every row (`gotchas.md` #7), run a sandbox sample, read `failedResults`, then run production. Queries, CSV shape, `sf data update bulk`, and the raw Bulk API 2.0 ingest job are in `references/metadata-examples.md` §4.
7. **Verify per persona, not per file.** Re-run the checker, run the two verification queries in `references/metadata-examples.md` §8 (retired types inactive, zero records left on them), and run the Apex describe audit in §5 as each persona — exactly one `isDefaultRecordTypeMapping()`, and it must not be the Master row.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No Apex code or Flow references hardcode Record Type IDs — all use DeveloperName-based resolution
- [ ] Layout assignment count (N x M) has been calculated and is within operational tolerance
- [ ] Dynamic Forms compatibility has been verified for target objects before planning a migration
- [ ] Picklist value overrides per record type align with actual business process requirements
- [ ] Data migration plan exists for records on retired record types, including rollback steps
- [ ] Profile layout assignment matrix has been updated to remove retired record type rows
- [ ] Reports and list views that filter by record type have been reviewed for impact

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Master record type is always available** — The "Master" record type cannot be deleted and is always present. If a user's profile has no other record type assigned, they default to Master, which shows all picklist values with no filtering. This silently breaks picklist governance when profiles are misconfigured.
2. **A permission set grants visibility but can never grant the default or the layout** — `PermissionSetRecordTypeVisibility` has exactly two fields, `recordType` and `visible` (API 29.0+). The `default` flag lives on `ProfileRecordTypeVisibility` and layout assignment lives on `Profile.layoutAssignments`, neither of which has a permission set equivalent. A PSG migration that trims profiles therefore deletes the default rather than moving it.
3. **Deleting a record type does not delete the records** — When you delete a record type, existing records are reassigned to the default record type for their owner's profile. This can silently change business process membership and picklist value visibility on thousands of records with no audit trail beyond the record type field history (if enabled).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Record type rationalization plan | Document listing each object's current and target record type count, consolidation mapping, and Dynamic Forms eligibility |
| Layout assignment matrix | Before and after grid of record types by profiles showing assignment reductions |
| Migration checklist | Step-by-step checklist for data migration, metadata deployment, and post-deployment validation |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Authoring the assignment matrix, rendering it into `Profile` and `PermissionSet` XML, running the consolidation and its Bulk API migration, generating the `package.xml` members, or writing the per-persona describe audit |
| `references/gotchas.md` | Nine platform behaviours behind record type incidents at scale — the vanished default after a PSG migration, the deleted fallback layout row, the save order a bulk `RecordTypeId` update actually runs, the mass profile diff after deactivation, and the wildcard that returns nothing |
| `references/examples.md` | Sizing a real consolidation: the Opportunity layout-explosion worked example, the hardcoded-Id failure, and the evidence you need before merging record types that only differ by label |
| `references/well-architected.md` | Justifying the design against the pillars, the granularity-vs-maintainability tradeoff, or tracing any claim in this package back to its official source |
| `references/llm-anti-patterns.md` | Reviewing AI-generated record type guidance before acting on it |
| `templates/record-type-strategy-at-scale-template.md` | Capturing the current state, target state, and migration plan before any XML is written |
| `scripts/check_record_type_strategy_at_scale.py` | Linting a retrieved tree: orphan record types, profiles with no default, record types with no layout assignment, count thresholds, hardcoded Ids |

---

## Related Skills

- **admin/record-types-and-page-layouts**: The single-record-type shapes this skill builds on — `RecordType`, `BusinessProcess`, and `Layout` XML, the four-object `businessProcess` rule, the count guide, and the eleven core gotchas. Read it first if the question is "how do I set one up", not "how do I govern ninety".
- **admin/record-type-id-management**: Resolving a record type Id in Apex, Flow, formulas, and test data. This skill only states the portability rule; that one has the patterns.
- **admin/permission-set-architecture**: Designing the permission sets and PSGs whose `recordTypeVisibilities` fill the visible column of the matrix.
- **admin/permission-sets-vs-profiles**: The wider set of settings that are profile-only, of which the record type default and layout assignment are two. Read before any PSG migration that touches objects with record types.
- **admin/dynamic-forms-and-actions**: Building the FlexiPage and its component visibility filters once consolidation has decided a record type is not needed.
- **admin/dynamic-forms-migration**: Converting one page layout to Dynamic Forms, including current object support.
- **admin/picklist-and-value-sets**: Global value sets and the picklist model underneath the record type override matrix — read before unioning values for a merge.
