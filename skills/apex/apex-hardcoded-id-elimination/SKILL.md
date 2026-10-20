---
name: apex-hardcoded-id-elimination
description: "Remove hardcoded Salesforce record IDs (Profile, RecordType, User, Queue, custom) from Apex and replace with describe-API, name-based SOQL, or Custom Metadata-driven lookups. NOT for record type IDs in Flow, formulas or LWC — use admin/record-type-id-management. NOT for storing the config values themselves — use apex/custom-metadata-in-apex."
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
  - "use metadata relationship field instead of hardcoding record id"
  - "does getinstance query soql or use the application cache"
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
version: 1.1.2
author: Pranav Nagrecha
updated: 2026-10-20
---

# Apex Hardcoded ID Elimination

Activate when Apex contains literal Salesforce record IDs (`'00e1x000000ABcD'`, `'012xx0000004C9I'`, `'00G3x000003abcD'`). Hardcoded IDs are catastrophic in any multi-org topology: the same Profile, RecordType, Queue, or User has a **different ID in sandbox vs production**, in every scratch org, and after some sandbox refreshes. Code that runs in prod silently breaks the moment it deploys to a sandbox copy, a partial copy refresh, or a scratch org spun up for CI.

The fix is to look IDs up by something stable — DeveloperName, MasterLabel via describe, or a Custom Metadata mapping — and to cache the result for the rest of the transaction.

---

## Before Starting

- **Identify the ID kind.** RecordType IDs come from the describe API. Profile, Group, Queue, UserRole IDs come from SOQL by `DeveloperName`. Configurable IDs (a default Account, a routing User) belong in Custom Metadata.
- **Use DeveloperName where the object has one.** `Group` has a `DeveloperName` field (object_reference 264 L155245); the Profile field list shows `Name` and no `DeveloperName` (L234840), and PermissionSet shows `Name` and `Label` (L219421-219444). The earlier "DeveloperName (`SysAdmin`)" for Profile was CONTRADICTED by those field lists. UNVERIFIED (2026-10-20): that "System Administrator" is renamed "Standard System Administrator" in some orgs. For Profile the predicate is `Name`, so Custom Metadata is safer for any cross-org code.
- **Audit tests.** A test class that hardcodes a sandbox-specific ID will not run in scratch orgs or new sandboxes.

## Questions to Ask Before Configuring

Ask these before replacing a literal Id. Skipping them ships a describe lookup against the wrong stable key or a cache that never warms in scratch orgs.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What kind of Id is this — RecordType, Profile, Queue, Group, UserRole, or a business record?" | Each kind has a different canonical lookup (describe vs name-based SOQL vs Custom Metadata) | The right mechanism from the table in Core Concepts, not a one-size-fits-all SOQL |
| "Which orgs must this code run in — prod only, named sandboxes, scratch orgs, CI?" | Ids differ across every topology; scratch orgs have no pre-existing rows | Whether Custom Metadata or describe is mandatory instead of a one-time SOQL |
| "What is the stable API name — DeveloperName, Name, or a CMDT key?" | Labels rename; DeveloperName and CMDT keys survive refresh | The predicate for `getRecordTypeInfosByDeveloperName()` or the cache key for Profile/Queue lookups |
| "Is this Id referenced from production code, tests, or both?" | Tests must `insert` and capture `.Id`; production literals are P0 defects | Separate fixtures: seeded data in tests, describe/CMDT in production |
| "Does the lookup run per call or once per transaction?" | Uncached `[SELECT Id FROM Profile WHERE Name = …]` is a P1 finding | A `static Map<String, Id>` helper sized before the first hot path |

What a proper Id elimination adds over swapping literals: code survives sandbox refresh and scratch-org CI, caches avoid SOQL-101 on hot paths, and subscribers can retarget configurable Ids through Custom Metadata without a redeploy.

---

## Core Concepts

### The four canonical lookup mechanisms

| ID kind | Mechanism | Why |
|---|---|---|
| RecordType | `Schema.SObjectType.X.getRecordTypeInfosByDeveloperName()` | A map of developer name to record type; the user needn't have access to the record type to see it (apexref 262 L192556-192558). UNVERIFIED (2026-10-20): that describe costs no SOQL and that DeveloperName is stable across orgs |
| Profile | `[SELECT Id FROM Profile WHERE Name = :name]` cached per-transaction | Profile has `Name` and no `DeveloperName` field; the cache avoids the 100-query limit (apex dev guide 264 L19747) |
| Group / Queue / UserRole | `[SELECT Id FROM Group WHERE DeveloperName = :n AND Type = 'Queue']` cached per-transaction | `Group.DeveloperName` exists (object_reference 264 L155245), and so does `UserRole.DeveloperName` (L306256) |
| Configurable metadata references (another CMDT record, object, field) | Custom Metadata Type with a **Metadata Relationship** field | Referential integrity, no raw ID string, `getInstance()` reads cache with no SOQL |
| Configurable business-record IDs (default Account, fallback User) | Custom Metadata Type with a `Text__c` field holding the Id | Subscriber-org safe, deployable, no code change to retarget |
| Test data IDs | `insert` then capture `record.Id` | Test data is created per run; never persistent |

### Schema describe for RecordType

`Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName()` returns `Map<String, Schema.RecordTypeInfo>`. Always use DeveloperName, never the label — `RecordTypeInfo.getName()` returns the UI label, which "can be translated into any language that Salesforce supports" (apexref 262 L193789), while `getDeveloperName()` returns the developer name (L193786-193787).

```apex
Id customerRtId = Schema.SObjectType.Account
    .getRecordTypeInfosByDeveloperName()
    .get('Customer')
    .getRecordTypeId();
```

This resolves the Id at run time instead of pinning a literal. UNVERIFIED (2026-10-20): that it costs no SOQL and works across every org.

### Caching SOQL-derived IDs

Profile/Group/Queue lookups are SOQL. A single naive lookup inside a loop blows the per-transaction limit of 100 SOQL queries (apex dev guide 264 L19747; "SOQL-101" is shorthand for the 101st query). Cache once per transaction:

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

The static map lives for the transaction: "the value of a static variable persists within the context of a single transaction and is reset across transaction boundaries" (apex dev guide 264 L3746-3748). Subsequent calls are free.

### Custom Metadata for configurable IDs

When the "right" ID is environment-specific (a default-owner User, a routing Queue, a fallback Account), put the mapping in a Custom Metadata Type. The records are metadata, deployable with `Metadata.Operations.enqueueDeployment()` (apex dev guide 264 L43295) — UNVERIFIED (2026-10-20): that they travel in packages and change sets as XML components rather than data rows — so the value differs per org and changes without a code release.

**Prefer a Metadata Relationship field over a raw `Text__c` ID.** When the thing you're referencing is itself metadata — another custom metadata record, an object (EntityDefinition), a field (FieldDefinition), or an entity particle — Salesforce provides a purpose-built **Metadata Relationship** field type. It stores a stable reference and enforces referential integrity instead of parking a raw 15/18-char ID in a text field, which is exactly the failure mode this skill exists to remove. `MetadataRelationship` is a documented custom field type (api_meta 264 L48110, alongside `Lookup` and `MasterDetail` in the same list; L45650 refers to it on custom metadata fields). UNVERIFIED (2026-10-20): that custom metadata types offer no Lookup or Master-detail field and that a Text field is the only way to store a data-record Id — those restrictions are Help-only. Reserve a plain `Text__c` field (holding the record Id) for referencing *data* records (a specific Account or User) that metadata relationships can't target.

**Custom metadata queries are not limited like other SOQL.** "In a single Apex transaction, custom metadata records can have unlimited SOQL queries" (apex dev guide 264 L19819-19820). UNVERIFIED (2026-10-20): that `getInstance()` / `getAll()` read an application cache and cost no query rows. `getAll()` returns a map whose keys are the record DeveloperNames (apexref 262 L204556-204557); `getInstance(...)` returns one record by record Id (L204587-204588) or by developerName (L204618-204620), and null when nothing matches. UNVERIFIED (2026-10-20): lookup by qualified API name.

**Watch the 255-character truncation.** "Only the first 255 characters are returned for any field in a custom metadata type record, so longer text fields get truncated. If you want all the field data … use a SOQL query" (apexref 262 L204570-204571, L204605-204607). If a config value (a long endpoint, a serialized payload) exceeds 255 chars, fall back to a full SOQL query against the `__mdt` type.

**Seeding and visibility.** UNVERIFIED (2026-10-20): that Apex can create, read and update but cannot delete custom metadata records, and that DML on custom metadata is blocked through the Partner and Enterprise APIs — the corpus documents only deployment through `Metadata.Operations.enqueueDeployment()` (apex dev guide 264 L43295). Protected metadata, such as a custom metadata type marked protected, "can only be accessed by Apex classes in the same namespace" (L28643-28645); UNVERIFIED (2026-10-20): the Public / Protected / PackageProtected visibility list. Use Protected when a managed package must hide environment-specific config such as API keys from subscriber-org Apex.

### Test class discipline

Tests must never hardcode any record ID. Always insert seed data and capture the resulting ID. `Test.startTest()` / `Test.stopTest()` and `TestDataFactory` patterns belong here — see `templates/apex/tests/TestDataFactory.cls`.

### Id vs String — the 15/18-char trap

Salesforce IDs are 15 chars (case-sensitive) or 18 chars (case-insensitive). The corpus states that "if you set ID to a 15-character value, Apex converts the value to its 18-character representation" (apex dev guide 264 L1254-1255). UNVERIFIED (2026-10-20): the case-sensitivity of each form and that a `String` compared with an `Id` fails equality. **Always use the `Id` data type.**

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
| Profile / Permission Set | SOQL by `Name`, cached (neither lists a `DeveloperName` field) |
| Group / Queue | SOQL by `DeveloperName`, cached (`UserRole.DeveloperName` too, object_reference 264 L306256) |
| Reference to another CMDT record, object, or field | Custom Metadata Type with a Metadata Relationship field |
| Environment-specific config (default user, fallback record) | Custom Metadata Type (`Text__c` holding the Id for data records) |
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
2. **`Name='System Administrator'` is not portable.** UNVERIFIED (2026-10-20): that some orgs renamed it. Profile has no `DeveloperName` field (object_reference 264 L234799-234887 lists `Description`, `Name`, `UserType` among its fields), so Custom Metadata holding the Profile `Name` is safer for any cross-org code.
3. **`getRecordTypeInfosByName` is keyed by the record type label** (apexref 262 L192589), and `RecordTypeInfo.getName()` is the UI label that "can be translated" (L193789). Always prefer `getRecordTypeInfosByDeveloperName`.
4. **`getInstance()`/`getAll()` truncate fields to 255 chars** (apexref 262 L204570-204571). Any config value longer than 255 characters comes back truncated — query the `__mdt` type with SOQL to get the full value.
5. **Seeding CMDT is a deployment, not DML** — the documented path is `Metadata.Operations.enqueueDeployment()` (apex dev guide 264 L43295). UNVERIFIED (2026-10-20): that Apex cannot delete CMDT rows and that the Partner and Enterprise APIs block CMDT DML; don't design a seeding routine that expects to `delete` CMDT rows.

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
- `apex/test-data-factory-patterns` — test-side ID discipline
- `apex/apex-dynamic-soql-binding-safety` — bound variables for name lookups
