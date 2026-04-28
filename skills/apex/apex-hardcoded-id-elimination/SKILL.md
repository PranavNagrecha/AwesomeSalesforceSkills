---
name: apex-hardcoded-id-elimination
description: "Remove hardcoded Salesforce record IDs (Profile, RecordType, User, Queue, custom) from Apex and replace with describe-API, name-based SOQL, or Custom Metadata-driven lookups. NOT for storing config data — see apex-custom-settings-hierarchy / custom-metadata-in-apex. NOT for ID-based sharing rules (see sharing-selection)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - apex
  - hardcoded-id
  - record-type
  - profile
  - custom-metadata
  - schema-describe
triggers:
  - "how to remove hardcoded profile id from apex"
  - "record type id different in sandbox vs production"
  - "apex breaks after sandbox refresh because of hardcoded ids"
  - "replace hardcoded queue id with developer name lookup"
  - "schema getrecordtypeinfosbydevelopername best practice"
  - "15 char vs 18 char id comparison failing in apex"
inputs:
  - Apex class or trigger containing literal 15/18-char IDs
  - Org context (sandbox, scratch, prod) where IDs differ
  - Required RecordType / Profile / Queue / Group developer names
  - Custom Metadata Type for config-driven IDs (if applicable)
outputs:
  - Refactored Apex using describe-API or name-based lookup
  - Cached helper class for Profile / Queue / Group ID resolution
  - Custom Metadata mapping for config-driven IDs
  - Test class that inserts data instead of hardcoding IDs
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Apex Hardcoded ID Elimination

Activate when Apex contains literal Salesforce record IDs (`'00e1x000000ABcD'`, `'012xx0000004C9I'`, `'00G3x000003abcD'`). Hardcoded IDs are catastrophic in any multi-org topology: the same Profile, RecordType, Queue, or User has a **different ID in sandbox vs production**, in every scratch org, and after some sandbox refreshes. Code that runs in prod silently breaks the moment it deploys to a sandbox copy, a partial copy refresh, or a scratch org spun up for CI.

The fix is to look IDs up by something stable — DeveloperName, MasterLabel via describe, or a Custom Metadata mapping — and to cache the result for the rest of the transaction.

---

## Before Starting

- **Identify the ID kind.** RecordType IDs come from the describe API. Profile, Group, Queue, UserRole IDs come from SOQL by `DeveloperName`. Configurable IDs (a default Account, a routing User) belong in Custom Metadata.
- **Confirm DeveloperName, not Name.** "System Administrator" has been renamed to "Standard System Administrator" in some orgs; DeveloperName (`SysAdmin`) is the API-stable identifier. For Profile, the canonical predicate is `Name`, but the value differs across org versions — Custom Metadata is safer for any cross-org code.
- **Audit tests.** A test class that hardcodes a sandbox-specific ID will not run in scratch orgs or new sandboxes.

---

## Core Concepts

### The four canonical lookup mechanisms

| ID kind | Mechanism | Why |
|---|---|---|
| RecordType | `Schema.SObjectType.X.getRecordTypeInfosByDeveloperName()` | Describe is metadata-driven, no SOQL cost, DeveloperName is stable |
| Profile / Group / Queue / UserRole | `[SELECT Id FROM Profile WHERE Name = :name]` cached per-transaction | DeveloperName / Name is stable; cache avoids SOQL-101 |
| Configurable business-record IDs (default Account, fallback User) | Custom Metadata Type with `Lookup__c` or `Text__c` field | Subscriber-org safe, deployable, no code change to retarget |
| Test data IDs | `insert` then capture `record.Id` | Test data is created per run; never persistent |

### Schema describe for RecordType

`Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName()` returns `Map<String, Schema.RecordTypeInfo>`. Always use DeveloperName, never MasterLabel — labels are translatable.

```apex
Id customerRtId = Schema.SObjectType.Account
    .getRecordTypeInfosByDeveloperName()
    .get('Customer')
    .getRecordTypeId();
```

This is metadata-driven, costs no SOQL, and works across every org.

### Caching SOQL-derived IDs

Profile/Group/Queue lookups are SOQL. A single naive lookup inside a loop blows the SOQL-101 limit. Cache once per transaction:

```apex
private static Map<String, Id> profileIdByName;
public static Id getProfileId(String name) {
    if (profileIdByName == null) {
        profileIdByName = new Map<String, Id>();
        for (Profile p : [SELECT Id, Name FROM Profile]) {
            profileIdByName.put(p.Name, p.Id);
        }
    }
    return profileIdByName.get(name);
}
```

The static map lives for the transaction. Subsequent calls are free.

### Custom Metadata for configurable IDs

When the "right" ID is environment-specific (a default-owner User, a routing Queue, a fallback Account), put the mapping in a Custom Metadata Type. The metadata deploys with code; the value differs per org and changes without a code release.

### Test class discipline

Tests must never hardcode any record ID. Always insert seed data and capture the resulting ID. `Test.startTest()` / `Test.stopTest()` and `TestDataFactory` patterns belong here — see `templates/apex/tests/TestDataFactory.cls`.

### Id vs String — the 15/18-char trap

Salesforce IDs are 15 chars (case-sensitive) or 18 chars (case-insensitive). Stored as `String`, the same record yields two different values that fail equality. **Always use the `Id` data type.** `Id` normalizes to 18-char internally; equality works.

```apex
// WRONG
String accId = '0011x00000ABCDe';      // 15-char
if (accId == acc.Id) { ... }            // acc.Id is 18-char — never matches

// RIGHT
Id accId = '0011x00000ABCDe';           // auto-normalized to 18
if (accId == acc.Id) { ... }            // works
```

### Integration boundary

When a third-party system requires a Salesforce ID (webhook target, named credential payload), that ID **must come from a name-based lookup or Custom Metadata at runtime**, never a literal in code. A literal pinned to one org silently sends the wrong ID after a refresh.

---

## Common Patterns

### Pattern: RecordType resolution helper

```apex
public with sharing class RecordTypes {
    private static final Map<String, Map<String, Id>> CACHE = new Map<String, Map<String, Id>>();

    public static Id idFor(SObjectType sot, String developerName) {
        String key = String.valueOf(sot);
        if (!CACHE.containsKey(key)) {
            Map<String, Id> byName = new Map<String, Id>();
            for (Schema.RecordTypeInfo rti :
                    sot.getDescribe().getRecordTypeInfosByDeveloperName().values()) {
                byName.put(rti.getDeveloperName(), rti.getRecordTypeId());
            }
            CACHE.put(key, byName);
        }
        return CACHE.get(key).get(developerName);
    }
}
```

### Pattern: Group / Queue lookup by DeveloperName

```apex
public static Id queueIdByDevName(String devName) {
    return [SELECT Id FROM Group WHERE DeveloperName = :devName AND Type = 'Queue' LIMIT 1].Id;
}
```

Wrap in a static map cache as above.

### Pattern: Custom Metadata-driven config

```apex
RoutingConfig__mdt cfg = RoutingConfig__mdt.getInstance('CaseRouter');
Id defaultQueueId = cfg.DefaultQueue__c;  // populated per-org
```

---

## Decision Guidance

| ID is... | Use |
|---|---|
| RecordType | `Schema.SObjectType.X.getRecordTypeInfosByDeveloperName()` |
| Profile / Permission Set | SOQL by `Name` / `DeveloperName`, cached |
| Group / Queue / UserRole | SOQL by `DeveloperName`, cached |
| Environment-specific config (default user, fallback record) | Custom Metadata Type |
| Test seed record | Insert in test, capture `.Id` |
| External-system reference | Custom Metadata or Named Credential, never literal |

---

## Recommended Workflow

1. Grep the codebase for the Salesforce ID regex `[a-zA-Z0-9]{15}(?:[a-zA-Z0-9]{3})?` enclosed in quotes — every hit is a candidate.
2. Classify each hit: RecordType, Profile/Group/Queue, configurable, or test-only.
3. Replace RecordType literals with `Schema...getRecordTypeInfosByDeveloperName()` calls.
4. Replace Profile/Group/Queue literals with cached name-based SOQL helpers.
5. Move configurable IDs to a Custom Metadata Type and read via `getInstance()`.
6. Refactor tests to insert seed records and capture IDs at runtime.
7. Run `scripts/check_apex_hardcoded_id_elimination.py` against the project to confirm zero residual literals outside test setup.

---

## Review Checklist

- [ ] No 15- or 18-char ID literal in non-test Apex
- [ ] All RecordType IDs resolved via `Schema.SObjectType.X.getRecordTypeInfosByDeveloperName()`
- [ ] Profile / Group / Queue lookups cached in a static `Map<String, Id>`
- [ ] Configurable IDs live in a Custom Metadata Type
- [ ] No SOQL for ID lookup inside a loop
- [ ] All Apex variables holding IDs are typed `Id`, not `String`
- [ ] Test classes insert seed data; no hardcoded test IDs
- [ ] Integration payloads source IDs from CMDT or runtime lookup, not literals

---

## Salesforce-Specific Gotchas

1. **15 vs 18 char comparison fails as String.** Stored as `String`, the same record can have two different representations. Always use the `Id` type.
2. **`Name='System Administrator'` is not portable.** Some orgs renamed it; Custom Metadata or `DeveloperName` is safer for any cross-org code.
3. **`getRecordTypeInfosByName` uses translatable label.** Always prefer `getRecordTypeInfosByDeveloperName`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Refactored Apex class | All literal IDs replaced with describe / SOQL / CMDT lookups |
| Cached lookup helper | `RecordTypes`, `Profiles`, `Queues` helpers with static maps |
| Custom Metadata Type | Config-driven mapping for environment-specific IDs |
| Refactored test class | Inserts seed data; captures IDs at runtime |

---

## Related Skills

- `apex/apex-custom-settings-hierarchy` — when config differs per profile/user
- `apex/custom-metadata-in-apex` — deployable config types
- `apex/apex-test-data-factory` — test-side ID discipline
- `apex/apex-soql-injection-prevention` — bound variables for name lookups
