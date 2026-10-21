---
name: record-type-id-management
description: "RecordType ID differences across orgs: dynamic lookup via Schema.SObjectType methods, DeveloperName for stable refs, hard-coded ID anti-patterns, record-type caching, deployment impact. NOT for deciding whether to use record types at all — use admin/record-types-and-page-layouts. NOT for layout/profile explosion at scale — use admin/record-type-strategy-at-scale. NOT for hard-coded Profile, Queue or User IDs in Apex — use apex/apex-hardcoded-id-elimination."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - record-type
  - developername
  - schema-describe
  - hardcoded-ids
  - deployment
triggers:
  - "why does my record type id differ between sandbox and production"
  - "how do i look up a record type id dynamically in apex or flow"
  - "record type developer name vs id best practice"
  - "record type id hardcoded in apex causing deployment failure"
  - "schema describe record type infos by developername"
  - "record type id changes when packaging or deploying"
  - "hard coded recordtypeid apex migration between orgs"
inputs:
  - Code or config referencing record types (Apex, Flow, LWC, Validation Rules, Formulas)
  - Target environments (sandbox set, packaging org, production)
  - Number of record types per object in scope
  - Deployment model (metadata API, managed package, unlocked package)
outputs:
  - Resolution pattern per reference point (Apex / Flow / formula)
  - Cleanup plan for hard-coded record-type IDs
  - Caching strategy for hot paths
  - Deployment test matrix across envs
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-21
status: stub
---

# Record Type ID Management

Activate when code, flow, or configuration references record types by ID. A record Id is generated when the record is created and is "unique within your org's data" (obj 264 L2290), so a record type created separately in each org gets a different Id there; DeveloperName is the "unique name of the object in the API" (obj 264 L246998). UNVERIFIED (2026-10-21): whether a sandbox refresh or org clone re-issues record-type Ids — no corpus line covers sandbox copies. Hard-coded IDs are one of the most common causes of "works in sandbox, fails in production" deployment failures on Salesforce.

## Before Starting

- **Grep the codebase for IDs that look like record-type keys.** Apex string literals starting with `012` are the smoking gun (the Master record type in the REST describe example is `012000000000000AAA`, api_rest 264 L9505).
- **Prefer DeveloperName over Name.** `Name` is the "Label of the record type in the user interface" (obj 264 L247039); DeveloperName is the stable API handle.
- **Know the method.** `getRecordTypeInfosByDeveloperName()` is a `Schema.DescribeSObjectResult` method (apexref 262 L192556-192562), not a `Schema` class method. UNVERIFIED (2026-10-21): any per-transaction caching of describe results — the corpus documents the method, not its cost.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which code, flows, formulas and list views compare against a literal `012…` Id today? | Every literal is a defect waiting for an org where that record type has a different Id (gotchas.md Gotcha 4 null-guard) | A file:line inventory the cleanup plan works from |
| Is the target list user-facing (a picker) or a resolution of one known DeveloperName? | The describe maps include record types the user cannot access (apexref 262 L192557-192558; Gotcha 1) | Whether `isAvailable()`/`isActive()`/`isMaster()` filtering is required |
| Could Master ever be returned, and what should happen then? | `isMaster()` marks the default record type used when none is set (apexref 262 L193892-193893; Gotcha 2) | An explicit Master exclusion instead of "first entry in the map" |
| Is any record type's API name (`fullName`) planned to change? | `fullName` is the record type name and component key (api_meta 264 L47382; Gotcha 3) | A label-only change, or a planned re-stamp of `RecordTypeId` |
| Is the record type hand-authored or retrieved metadata, and on which object? | `businessProcess` is required for lead, opportunity, solution and case record types and is written bare, not object-prefixed (api_meta 264 L47367-47373; Gotcha 4) | Metadata that deploys first time |
| Does the org run in more than one language, or use Translation Workbench? | `getName()` returns a translatable label and the by-Name map is keyed on labels (apexref 262 L193824, L192589; Gotcha 5) | A DeveloperName-only lookup rule |
| Does an LWC need the Id? | UI API Record Type Info has no `developerName` (UI API 262) | An `@AuraEnabled` resolver instead of client-side lookup |

A proper configuration resolves every reference at runtime from a DeveloperName that the deploy carries, so a new org needs no Id edits, where "just doing it" ships the Id that happened to exist in the org it was built in.

## Core Concepts

### DeveloperName is the stable handle

Record types have three identifiers: `Id` (org-specific), `Name` (user-facing label), `DeveloperName` (API name). Only `DeveloperName` is stable across orgs. All code and config should reference by DeveloperName, resolving to Id at runtime.

### Schema.SObjectType resolution

Apex: `Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName().get('Business_Account').getRecordTypeId()`. Returns the Id in the current org. Works everywhere — triggers, batch, LWC `@AuraEnabled` methods.

### Flow

Flow formula or Get Records on `RecordType` with `SobjectType` and `DeveloperName` filters. Avoid referencing record-type Ids directly in flow; use the record type lookup component or DeveloperName-based query.

### Validation rules and formulas

Formulas can reference `$RecordType.DeveloperName` (scoped to the context record). Compare to strings rather than IDs. `RecordType.DeveloperName = 'Business_Account'` survives deployment; `RecordTypeId = "012..."` does not. UNVERIFIED (2026-10-21): the `$RecordType` formula merge field and its scoping are Help-only; no corpus guide documents them — this applies to every `$RecordType.DeveloperName` row, step and checklist line below.

### LWC

`@wire(getObjectInfo)` returns `recordTypeInfos`, "a map of record type IDs to information about the record type" (UI API Object Info, 262), and each Record Type Info carries only `available`, `defaultRecordTypeMapping`, `master`, `name` (the translatable label) and `recordTypeId` — there is **no `developerName`** (UI API Record Type Info, 262). So the client cannot resolve DeveloperName → Id from `getObjectInfo`; return the Id from an `@AuraEnabled` Apex method that resolves it with `getRecordTypeInfosByDeveloperName()`.

## Common Patterns

### Pattern: Central Apex utility for record-type resolution

```
public class RecordTypes {
    public static Id idFor(SObjectType type, String developerName) {
        return type.getDescribe().getRecordTypeInfosByDeveloperName()
                   .get(developerName).getRecordTypeId();
    }
}
```

Use as `RecordTypes.idFor(Account.SObjectType, 'Business_Account')`. It issues no SOQL query; UNVERIFIED (2026-10-21): that the platform caches the describe result so repeated calls are cheap — cache in a `static Map` (statics persist "within the context of a single transaction", apexdev 264 L3747) rather than relying on it. Null-guard the `get()` — a missing DeveloperName returns `null`.

### Pattern: Custom Metadata Type as record-type registry

`RecordTypeRef__mdt` with `Object__c`, `DeveloperName__c`, and any semantic flags. Apex/Flow read the CMDT, then resolve to Id. Useful when the same logical "primary" record type differs across products.

### Pattern: Validation rule via DeveloperName

`AND($RecordType.DeveloperName = 'Business_Account', ISBLANK(Industry))`. No ID in the formula. UNVERIFIED (2026-10-21): `$RecordType` is Help-only (see Validation rules and formulas above).

## Decision Guidance

| Reference point | Preferred pattern |
|---|---|
| Apex logic | `<SObject>.SObjectType.getDescribe().getRecordTypeInfosByDeveloperName()` (a DescribeSObjectResult method, apexref 262 L192562) |
| Flow decision | DeveloperName via Get Records |
| Validation rule | `$RecordType.DeveloperName` (UNVERIFIED, Help-only) |
| Formula field | `$RecordType.DeveloperName` (UNVERIFIED, Help-only) |
| LWC | Id from an `@AuraEnabled` Apex resolver — `getObjectInfo` record type infos have no developerName (UI API 262) |
| Assignment rule / Approval process | Record-type aware criteria on DeveloperName if possible |

## Recommended Workflow

1. Grep codebase for `012[A-Za-z0-9]{12,15}` literals and audit every match.
2. Catalog every record type per object with `SELECT DeveloperName, SObjectType FROM RecordType`.
3. Replace each hard-coded Id with the DeveloperName resolution pattern matching its reference point.
4. Introduce a central `RecordTypes` utility and migrate Apex references.
5. Update validation rules and formulas to `$RecordType.DeveloperName` (UNVERIFIED merge field, see Core Concepts).
6. Deploy to an org where the record types were created by the deploy itself (a scratch org or a sandbox that did not copy them) and verify no test failures reference ID literals.
7. Run `python3 skills/admin/record-type-id-management/scripts/check_record_type_id_management.py --manifest-dir force-app --strict` in CI so quoted 15/18-char `012…` literals in `.cls`, `.trigger` and `.js` files block the merge (the checker does not scan XML metadata for Id literals — review formulas and flows by hand).

## Review Checklist

- [ ] No hard-coded record-type IDs remain in Apex, LWC, Flow, or metadata
- [ ] Central Apex utility used for ID resolution
- [ ] Validation rules and formulas use `$RecordType.DeveloperName` (UNVERIFIED merge field)
- [ ] LWC gets the Id from an Apex resolver, not a `getObjectInfo` developerName lookup (no such property)
- [ ] Smoke test passes in an org whose record types were created by the deploy
- [ ] CI check blocks new hard-coded record-type IDs
- [ ] Documentation notes DeveloperName convention for admins

## Salesforce-Specific Gotchas

1. **Master record type is named `Master`** — the REST describe example shows `"recordTypeName" : "Master"` with Id `012000000000000AAA` (api_rest 264 L9505-9506); exclude it with `isMaster()` (apexref 262 L193892). UNVERIFIED (2026-10-21): its DeveloperName value — the corpus shows the name only.
2. **Filter on `isActive()` before offering a record type.** "Only active record types can be applied to records" (obj 264 L247014). UNVERIFIED (2026-10-21): whether inactive record types appear in `getRecordTypeInfosByDeveloperName()` — the accessor text (apexref 262 L192557) does not say.
3. **A deploy carries DeveloperName, not Id.** The metadata component is keyed by `fullName` (api_meta 264 L47382) and the Id is generated in the target org (obj 264 L2290) — code that hard-codes the source Id fails there.

## Output Artifacts

| Artifact | Description |
|---|---|
| Hard-coded ID audit | List of files + line numbers with IDs |
| Central resolver utility | Apex class with caching |
| CI check | Regex hook blocking new ID literals |
| DeveloperName catalog | Object × DeveloperName × purpose |

## Related Skills

- `apex/apex-mocking-and-stubs` — mocking Schema.describe in tests
- `data/data-model-design-patterns` — record-type strategy itself
- `devops/salesforce-code-analyzer` — CI static-analysis gate
