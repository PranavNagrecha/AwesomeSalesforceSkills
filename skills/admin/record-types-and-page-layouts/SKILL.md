---
name: record-types-and-page-layouts
description: "Use when designing, auditing, or simplifying Record Types and Page Layouts. Triggers: 'record type', 'page layout', 'different picklist values', 'different fields per team', 'dynamic forms', 'business process', 'recordTypeVisibilities', 'layoutAssignments', 'record type deploy failed', 'businessProcess required', 'layout assignment matrix'. NOT for layout explosion across many profiles — use admin/record-type-strategy-at-scale. NOT for sharing rules — use admin/sharing-and-visibility. NOT for FLS — use admin/permission-sets-vs-profiles."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
tags: ["record-types", "page-layouts", "dynamic-forms", "picklists", "ui-simplification"]
triggers:
  - "user cannot select a record type when creating a record"
  - "page layout showing wrong fields for this user"
  - "picklist values not available on a record type"
  - "record type missing after package install"
  - "how do I simplify too many page layouts"
  - "dynamic forms not showing the right fields"
  - "record type deploy fails with businessProcess required"
  - "record type deploy fails with businessProcess not allowed"
  - "wildcard package.xml did not retrieve any record types"
  - "recordTypeVisibilities disappeared from the profile after retrieve"
  - "permission set will not let me assign a page layout"
  - "picklist values went blank after a record type change"
  - "required field on the layout is still blank on API-created records"
  - "which profile gets which page layout for this record type"
  - "layout must contain an item for required layout field"
  - "deploy fails required layout field ContactId"
inputs: ["process differences", "page requirements", "picklist variation needs"]
outputs: ["record type strategy", "layout simplification findings", "ui model recommendations"]
dependencies: []
version: 1.2.3
author: Pranav Nagrecha
updated: 2026-09-19
---

You are a Salesforce Admin expert in UX and data architecture. Your goal is to design a Record Type model that supports distinct business processes with minimum complexity — and to help orgs that have over-built their Record Type model find a simpler path forward.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first — particularly whether Person Accounts are enabled (Record Type interaction with Person Accounts is complex), and whether Lightning Experience is active (affects Dynamic Forms availability).
Only ask for information not already covered there.

Gather if not available:
- What object are we working with?
- How many distinct business processes or user groups use this object?
- Are the differences in picklist values, page layouts, or both?
- Is Lightning Experience enabled? (Required for Dynamic Forms)
- Is this greenfield or simplifying an existing model?

## Questions to Ask Before Configuring

Ask these before opening Object Manager. Each one maps to a way this model fails in production, and an LLM that skips them produces a record type that deploys cleanly and nobody can select.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which picklist values differ between these processes, field by field?" | If nothing differs, the requirement is a layout or a Dynamic Forms problem, not a record type | The `picklistValues` blocks, and the evidence that a record type is warranted at all |
| "Is this object Lead, Opportunity, Solution, or Case?" | Those four require a `businessProcess`; every other object forbids one, and both mistakes are deploy failures | Whether a `BusinessProcess` must be authored alongside the record type (gotchas #6) |
| "Which profile does each affected user actually hold?" | Permission sets grant record type *visibility* only — the default record type and the page layout assignment exist solely on `Profile` | The profile × record type × layout matrix, not a per-record-type layout list |
| "Do records already exist on the record type we are changing or retiring?" | Reassignment blanks any picklist value absent from the target record type, silently | The at-risk record count and the value-mapping step that must run first (gotchas #1) |
| "Which reports, list views, and Flow entry criteria filter on this record type today?" | Report filters key on the label, which is not stable; code and Flows key on `DeveloperName`, which is | The rename blast radius, before anyone renames anything (gotchas #4) |
| "Is a field being marked Required on the layout meant to be enforced everywhere?" | Layout `Required` binds to that layout only — API, Flow, and every other layout ignore it | A decision between field-level `required` and a record-type-scoped validation rule (gotchas #11) |
| "Which standard fields does the platform require on this object's layout?" | A layout that omits one does not deploy, and no static checker can derive the set from the Metadata API guide — it is not documented there | The layout-required item list before the file is written, instead of one `--dry-run` round trip per missing field (gotchas #12, #13). On Case the answer is `ContactId`, `Description`, `SuppliedEmail`, and `Status` at `behavior=Required` |
| "Are Person Accounts enabled on this org?" | Person Account record types are a separate model, and the Metadata API will not round-trip their custom picklist values | A separate design track and a manual verification step for the picklist matrix (gotchas #2, #9) |

What a proper configuration adds over just creating the record type: the record type is selectable by the right users with the right default, every profile lands on an intended page layout instead of falling through to a default, the picklist matrix survives a scratch-org rebuild, and no existing record loses a field value on the way there.

## How This Skill Works

### Mode 1: Build from Scratch

1. Run the "Do you actually need a Record Type?" decision framework (below)
2. If yes: define the minimum number of Record Types that covers the use cases
3. Map each Record Type to: picklist value sets, page layout, assigned personas
4. Design the Profile/PSG → Record Type assignment matrix
5. Document using the template

### Mode 2: Review Existing

1. Count Record Types per object — flag if > 8
2. Identify: Record Types with identical page layouts (merge candidates)
3. Identify: Record Types not assigned to any Profile/Permission Set (orphaned)
4. Identify: Record Types sharing all the same picklist values (unnecessary differentiation)
5. Identify: Record Types with existing records — cannot delete without reassignment
6. Report: simplification opportunities, orphaned types, merge candidates

### Mode 3: Troubleshoot

1. Identify the symptom: wrong picklist values, wrong layout, missing RT in create flow, or risky RT migration
2. Check assignments first: Profile/Permission Set visibility, default RT, page layout assignment
3. Check the data impact: will an RT change blank any picklist values on existing records?
4. Validate Lightning assumptions: if the issue is only field visibility, decide whether Dynamic Forms is the actual fix
5. Test the correction in sandbox before changing RT assignments in production

## Do You Actually Need a Record Type?

Run every requirement through this framework before creating a Record Type:

| Requirement | Use Record Type? | Alternative |
|-------------|-----------------|-------------|
| Different picklist values per process | ✅ Yes | — |
| Different page layout per user group | ✅ Yes (or Dynamic Forms) | Dynamic Forms if Lightning |
| Different required fields per process | ❌ No | Validation rule scoped to RT |
| Different default field values | ❌ No | Flow with entry criteria |
| Different automation logic per process | ❌ No | Flow entry criteria |
| Just different labels for the same thing | ❌ No | Picklist value alias |
| You have > 8 record types on one object | 🚨 Stop | Redesign the model |

**The rule:** If the ONLY difference between two business processes is which fields appear on the layout — not which picklist values are available — consider Dynamic Forms instead of multiple Record Types.

## Record Type Count Guide

| Count | Status | Action |
|-------|--------|--------|
| 1-4 | Healthy | Standard model |
| 5-8 | Monitor | Justify each one. Could any merge? |
| 9-12 | Warning | Likely over-built. Audit for merge candidates. |
| 13+ | Problem | Architectural redesign needed. |

## Page Layout vs Dynamic Forms

| Scenario | Page Layout | Dynamic Forms |
|----------|-------------|--------------|
| Classic org | ✅ Use | ❌ Not available |
| Lightning org, simple layout | ✅ Fine | ✅ Also fine |
| Different fields per user role | Multiple layouts + RTs | ✅ Dynamic Forms with visibility rules |
| Same RT, different fields per field value | Not possible | ✅ Dynamic Forms |
| Mobile app | ✅ Supported | ⚠️ Limited support |
| AppExchange package compatibility | ✅ More compatible | ⚠️ Check package support |

**The Dynamic Forms case:** Instead of 4 Record Types with 4 page layouts that differ only in which fields are shown — use 1 Record Type + Dynamic Forms with field visibility rules. Simpler, more maintainable, and allows field visibility based on field values, not just Record Type.

## Master Record Type

The Master Record Type:
- Is created automatically by Salesforce for every object
- Cannot be deleted
- Is not user-assignable (you can't create a record and choose "Master")
- Represents the "no record type" state
- Contains all picklist values by default
- Page layout assigned to Master RT is shown to users without a specific RT assignment

**When to use:** Leave Master RT alone unless you're not using Record Types at all. Don't assign it to users in production — create named Record Types for actual business processes.


## Recommended Workflow

1. Justify the record type — run the "Do you actually need a Record Type?" table above. If the only difference is which fields appear, stop and route to `admin/dynamic-forms-and-actions`. Record the outcome in `templates/record-type-design-template.md`
2. Fill the design template — record types, the picklist-by-record-type matrix, the profile × record type × layout matrix, and (for Lead, Opportunity, Solution, Case) the business process. The template is the human-readable source of truth, because the Metadata API does not round-trip the whole picklist matrix (`references/gotchas.md` #9)
3. Write the metadata — copy the shapes in `references/metadata-examples.md`: `recordTypes` and `businessProcesses` inside the `CustomObject`, the `Layout` file, and the `recordTypeVisibilities` / `layoutAssignments` in the profiles and permission sets. Use one manifest that names every record type explicitly — `RecordType` does not accept `*`
4. Check before deploying — `python3 scripts/check_record_type_layouts.py --manifest-dir force-app/main/default` (add `--strict` to fail on MEDIUM/LOW/INFO too; add `--require-assignment` to promote `RTL-ASSIGN-01` from INFO to REVIEW). It flags layout assignments pointing at inactive record types, missing business processes on the four objects that need them, record types nobody can see, objects past the count threshold, identical layouts on the same object as REVIEW `RTL-MERGE-01` (Mode 2 merge candidates), active record types with neither a Profile `layoutAssignments` nor any Profile/PermissionSet `recordTypeVisibilities` entry as INFO `RTL-ASSIGN-01` (or one INFO when the tree holds no Profile/PermissionSet at all), and — as ERROR-severity `RL-REQ-01` / `RL-REQ-02` — a Case layout missing `ContactId`, `Description`, or `SuppliedEmail`, or whose `Status` item is absent or not `Required` (`RL-REQ-03` is an ADVISORY heuristic for other standard objects); and — as HIGH-severity `RTL-REQ-01` / `RTL-REQ-02` — an Opportunity layout with no `Probability` item, or whose `Name` or `StageName` item is present with a behavior other than `Required` (org-verified 2026-09-18; `CloseDate` is an INFO carrying `UNVERIFIED (2026-09-18)`, because run 4 proved the set is accepted, not that CloseDate is required). Point it at a tree that carries the objects, the layouts **and** the profiles — run it over profiles alone and it reports `N reference(s) unresolvable at this scope` instead of a cross-check, because there is nothing to cross-check against. Exit 1 means a CRITICAL/HIGH deploy-breaker
5. Plan the data impact — if any existing record moves record type, run the at-risk SOQL in `references/gotchas.md` #1 and migrate the picklist values *before* the reassignment
6. Deploy and verify — `--dry-run` first, then deploy the object, layouts, profiles, and permission sets in one package. Layout pre-deploy checklist: every Case layout carries `ContactId`, `Description`, and `SuppliedEmail` as items and `Status` at `<behavior>Required</behavior>`; on any other object, treat the layout-required set as unknown and let `--dry-run` name it one field per run rather than guessing (gotchas #12). Confirm with the `RecordType` SOQL and the Page Layout Assignment grid in `references/metadata-examples.md`
7. Test as a user, not as an admin — create a record as each affected persona and confirm the record type selector, the default, the layout, and the filtered picklist values. System Administrator sees everything and will not reproduce the failure

---

## Salesforce-Specific Gotchas

- **Changing a record's Record Type can wipe picklist values**: If a picklist field has value "Premium" on the old RT but "Premium" doesn't exist on the new RT's picklist value set, that field goes blank after the RT change. No warning is shown. Run a data quality check BEFORE and AFTER any bulk RT reassignment.
- **Record Types and Person Accounts**: Person Accounts have their own RT model that's separate from Business Account RTs. Mixing them up causes assignment errors. If Person Accounts are enabled, design RT models for Business Accounts and Person Accounts independently.
- **New profiles don't inherit Record Type assignments**: When you create a new Profile (or when a managed package adds a Profile), it has NO Record Type assignments by default. Users with that profile get the Master RT only. Always check RT assignments when creating or importing new Profiles.
- **Reports filter by Record Type Name, not Developer Name**: If you rename the Label of a Record Type (e.g. "New Biz" → "New Business"), all report filters using that RT name break. Developer Name is stable; Label is not. Document this before any RT renaming.
- **Deleting a Record Type requires record reassignment**: You cannot delete a Record Type that has existing records assigned to it. You must first bulk-update those records to a different RT. In large orgs, this can be a significant data operation. Always check record count before planning a deletion.
- **Page layouts ≠ access control**: A field hidden on a page layout is still visible in reports, list views, related lists, and API queries. If you need to hide a field from a user, use FLS — not a page layout. Page layouts are UX tools, not security tools.
- **`businessProcess` is mandatory on four objects and banned everywhere else**: Lead, Opportunity, Solution, and Case record types must name one; every other object rejects one. Both directions fail the deploy (`references/gotchas.md` #6).
- **A permission set cannot assign a page layout or a default record type**: `PermissionSet.recordTypeVisibilities` carries only `recordType` and `visible`. `layoutAssignments` and `default` exist only on `Profile`, so a profile-free assignment model still leaves layouts on the profile (`references/gotchas.md` #8, `references/metadata-examples.md`).
- **Some standard fields are required on the layout itself, and only the deploy knows which**: a Case layout without `ContactId`, `Description`, and `SuppliedEmail`, or with `Status` at anything but `behavior=Required`, fails `sf project deploy start` with four errors delivered one per run — while passing every static check. The Metadata API guide does not state the rule; the set for objects other than Case is unverified (`references/gotchas.md` #12, #13).
- **`RecordType` does not accept the `*` wildcard in package.xml**: a wildcard manifest retrieves the object and its layouts but no record types, so a "full" source snapshot quietly omits them (`references/metadata-examples.md`).

## Proactive Triggers

Surface these WITHOUT being asked:
- **Record Type with identical page layout to another RT** → Flag as merge candidate. If the ONLY difference is the RT name and the picklist value sets are identical, ask: why do these exist separately?
- **Record Type not assigned to any Profile or Permission Set** → Flag as orphaned. This RT cannot be selected when creating records. It may have existing records assigned to it from a previous assignment — check with SOQL.
- **All Record Types share identical picklist values** → Flag: Record Types may be unnecessary. If every RT shows the same picklist options, the differentiation purpose is lost. Validate what they're actually for.
- **Record Type count > 8 on a single object** → Flag as architectural smell. Surface immediately and ask the user to justify the count. In 8+ years of implementations, fewer than 5% of business requirements genuinely need more than 6 Record Types on a single object.

## Output Artifacts

| When you ask for...               | You get...                                                          |
|-----------------------------------|---------------------------------------------------------------------|
| RT design for new feature         | RT count recommendation + picklist mapping + layout assignment plan |
| Audit existing RT model           | Merge candidates, orphaned RTs, simplification opportunities        |
| Migration plan                    | RT reassignment steps + picklist impact assessment + sandbox steps  |
| Do I need a Record Type?          | Decision framework result + recommended alternative if no            |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing deployable `RecordType`, `BusinessProcess`, `Layout`, and profile/permission-set assignment XML, the layout-required standard fields, the package.xml, and the verification SOQL |
| `references/gotchas.md` | Fifteen platform behaviours that cause most record type and layout incidents — picklist wipes, deploy failures, profile-diff noise, layout `Required` that enforces nothing, layout-required standard fields that fail the deploy rather than the checker, identical layouts after an undifferentiated record-type split, and deployable-but-unselectable types |
| `references/examples.md` | Worked Opportunity, Case, and Dynamic-Forms-instead-of-record-types designs with picklist and layout matrices |
| `references/well-architected.md` | Pillar mapping, governance (who approves a new record type), and the official-source list behind every claim in this package |
| `references/llm-anti-patterns.md` | Self-checking generated output — the seven ways an assistant gets record types and layouts wrong |
| `templates/record-type-design-template.md` | Capturing the design before building it: the decision, the matrices, the migration plan, and the test protocol |

---

## Related Skills

- **admin/permission-sets-vs-profiles**: Use when Record Type availability or defaults are really an access-assignment problem. NOT when the main question is page design or picklist architecture.
- **admin/validation-rules**: Use when the only difference between processes is required fields or save-time enforcement. NOT when you truly need different picklist sets or page experiences.
- **admin/flow-for-admins**: Use when process differences can be handled by entry criteria or automation branching instead of new Record Types. NOT when the requirement is record-create UX or picklist segmentation.
- **admin/dynamic-forms-and-actions**: Use when the only difference between processes is which fields appear, and the org is Lightning. NOT when picklist values differ by process.
- **admin/record-type-strategy-at-scale**: Use when the record type and layout count has already exploded across many objects or profiles. NOT for designing a single object's model.
- **admin/record-type-id-management**: Use when code, Flows, or data loads need to resolve a Record Type Id without hardcoding it. NOT for the design decision itself.
- **admin/picklist-and-value-sets**: Use when the underlying value set (global vs local, restricted, dependent) is the real question. NOT for which record type exposes which subset.
- **admin/permission-set-architecture**: Use when the assignment side needs designing — which permission set grants record type visibility, and which profile still owns the default and the layout.
