---
name: record-type-id-management
description: "RecordType ID differences across orgs: dynamic lookup via Schema.SObjectType methods, DeveloperName for stable refs, hard-coded ID anti-patterns, record-type caching, deployment impact. NOT for record-type strategy or when to use record types (use admin-foundation or data-model-design)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Record Type ID Management

Activate when code, flow, or configuration references record types by ID. Record type IDs are org-specific and change across sandbox refreshes, packaging, and org clones. Hard-coded IDs are one of the most common causes of "works in sandbox, fails in production" deployment failures on Salesforce.

## Before Starting

- **Grep the codebase for IDs that look like record-type keys.** Apex string literals starting with `012` are the smoking gun.
- **Prefer DeveloperName over Name.** Admins rename labels; DeveloperName is the stable API handle.
- **Know the caching story.** `Schema.SObjectType.RecordTypeInfosByDeveloperName` is cached per transaction — safe to call often, but not free across transactions.

## Core Concepts

### DeveloperName is the stable handle

Record types have three identifiers: `Id` (org-specific), `Name` (user-facing label), `DeveloperName` (API name). Only `DeveloperName` is stable across orgs. All code and config should reference by DeveloperName, resolving to Id at runtime.

### Schema.SObjectType resolution

Apex: `Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName().get('Business_Account').getRecordTypeId()`. Returns the Id in the current org. Works everywhere — triggers, batch, LWC `@AuraEnabled` methods.

### Flow

Flow formula or Get Records on `RecordType` with `SobjectType` and `DeveloperName` filters. Avoid referencing record-type Ids directly in flow; use the record type lookup component or DeveloperName-based query.

### Validation rules and formulas

Formulas can reference `$RecordType.DeveloperName` (scoped to the context record). Compare to strings rather than IDs. `RecordType.DeveloperName = 'Business_Account'` survives deployment; `RecordTypeId = "012..."` does not.

### LWC

LWC receives record-type Id via `@wire(getObjectInfo)` which returns `recordTypeInfos` keyed by Id with `name` and `developerName` attributes. Resolve DeveloperName → Id on the client once per session.

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

Use as `RecordTypes.idFor(Account.SObjectType, 'Business_Account')`. Cached by the platform; cheap to call repeatedly.

### Pattern: Custom Metadata Type as record-type registry

`RecordTypeRef__mdt` with `Object__c`, `DeveloperName__c`, and any semantic flags. Apex/Flow read the CMDT, then resolve to Id. Useful when the same logical "primary" record type differs across products.

### Pattern: Validation rule via DeveloperName

`AND($RecordType.DeveloperName = 'Business_Account', ISBLANK(Industry))`. No ID in the formula. Deploys cleanly to every org.

## Decision Guidance

| Reference point | Preferred pattern |
|---|---|
| Apex logic | `Schema.getRecordTypeInfosByDeveloperName` |
| Flow decision | DeveloperName via Get Records |
| Validation rule | `$RecordType.DeveloperName` |
| Formula field | `$RecordType.DeveloperName` |
| LWC | `@wire(getObjectInfo)` → lookup by developerName |
| Assignment rule / Approval process | Record-type aware criteria on DeveloperName if possible |

## Recommended Workflow

1. Grep codebase for `012[A-Za-z0-9]{12,15}` literals and audit every match.
2. Catalog every record type per object with `SELECT DeveloperName, SObjectType FROM RecordType`.
3. Replace each hard-coded Id with the DeveloperName resolution pattern matching its reference point.
4. Introduce a central `RecordTypes` utility and migrate Apex references.
5. Update validation rules and formulas to `$RecordType.DeveloperName`.
6. Run a sandbox-refresh smoke test: deploy to a freshly refreshed sandbox and verify no test failures reference ID literals.
7. Add a CI check that blocks commits containing 18-char record-type IDs.

## Review Checklist

- [ ] No hard-coded record-type IDs remain in Apex, LWC, Flow, or metadata
- [ ] Central Apex utility used for ID resolution
- [ ] Validation rules and formulas use `$RecordType.DeveloperName`
- [ ] LWC resolves via `getObjectInfo`
- [ ] Smoke test on freshly refreshed sandbox passes
- [ ] CI check blocks new hard-coded record-type IDs
- [ ] Documentation notes DeveloperName convention for admins

## Salesforce-Specific Gotchas

1. **Master record type has DeveloperName `Master`** — handle gracefully when looking up the master programmatically.
2. **Inactive record types are not excluded by `getRecordTypeInfosByDeveloperName`.** Filter on `isActive()` if you care.
3. **Change Sets preserve DeveloperName but not Id.** The destination org creates a new Id — code that hard-codes Id from the source fails on first run.

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
- `devops/cicd-pipeline-design` — CI regex hooks
