# Well-Architected Notes — Record Type Id Management

## Relevant Pillars

- **Reliability** — Primary. A hard-coded record-type Id is a latent defect that stays invisible until an environment changes: a sandbox refresh, a package install, an org clone, or a Change Set into a new org. The failure mode is usually silent (a branch stops matching) rather than loud (an exception), which is what makes it expensive.
- **Operational Excellence** — Secondary. DeveloperName-based resolution is what makes a deployment repeatable across the sandbox chain. It is also what lets a CI gate exist at all: you can regex-block `012` literals; you cannot regex-detect "wrong record type assumed."
- **Performance** — Tertiary, and mostly a non-issue. `Schema` describe resolution costs no SOQL query, unlike the `[SELECT Id FROM RecordType ...]` pattern it replaces. The real performance risk is the anti-pattern, not the pattern.
- **Security** — Marginal but real. `getRecordTypeInfos*` deliberately ignores the running user's access ("The current user is not required to have access to a record type to see it in this map"), so a picker built from the raw map leaks the existence of record types the user cannot use.

## Architectural Tradeoffs

| Tradeoff | Decision criteria |
|---|---|
| Describe resolution vs SOQL on `RecordType` | Describe by default — no query consumed, no language sensitivity. Query the sObject only when you need fields that describe does not expose, and then once per transaction into a map. |
| Central `RecordTypes` utility vs inline describe calls | Central utility once more than two classes resolve record types. It gives you one place to add the null-guard, the cache, and the `isAvailable`/`isActive` filter. Inline is acceptable in a single-purpose class. |
| Static cache vs re-resolving every call | Cache in a `static Map` keyed by object + DeveloperName. Apex statics are transaction-scoped, so the cache cannot leak across orgs the way a hard-coded literal does — it just avoids repeated describe work within one transaction. |
| Fail-fast on missing DeveloperName vs null-tolerant lookup | Fail fast. A missing record type is a deployment defect. Returning `null` converts it into a `NullPointerException` in unrelated code, or worse, into a record saved with no record type. |
| Custom Metadata registry vs DeveloperName literals in code | A `RecordTypeRef__mdt` registry earns its keep only when the *logical* record type varies by org, product line, or subscriber. For a single-org build it adds indirection without removing a failure mode. |

## Architectural Anti-Patterns

1. **Environment-specific literals in deployable metadata** — The `012` Id is the canonical example, but the class of problem is broader: any Id, any org URL, any user Id baked into code or a formula. All of them survive the deploy and none of them survive the environment change. The architectural rule is that deployable artifacts reference stable API names, and Ids are resolved at runtime.
2. **Renaming `fullName` to "clean up" naming** — `fullName` is the component key. Changing it creates a parallel record type and orphans every existing record against the old one, with no deploy error. Labels are for humans and are safe to change; API names are the contract.
3. **Building user-facing lists from schema describe without access filters** — The describe maps are a schema view. Presenting them directly shows users record types they cannot select, and shows deactivated types indefinitely. Filter on `isAvailable()`, `isActive()`, and `isMaster()` before rendering.

## Official Sources Used

- Apex Reference Guide — DescribeSObjectResult record-type accessors: `getRecordTypeInfos()`, `getRecordTypeInfosByDeveloperName()`, `getRecordTypeInfosByName()`, `getRecordTypeInfosById()`. Confirms the exact signatures and the verbatim caveat that "The current user is not required to have access to a record type to see it in this map." — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_sobject_describe.htm (verified 2026-08-14)
- Apex Reference Guide — `Schema.RecordTypeInfo` class. Confirms `getName()` returns a translatable UI label, `getDeveloperName()` / `getRecordTypeId()` signatures, and the semantics of `isAvailable()`, `isActive()`, `isDefaultRecordTypeMapping()` and `isMaster()`. — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Schema_RecordTypeInfo.htm (verified 2026-08-14)
- Metadata API Developer Guide — `RecordType` metadata type. Confirms availability in API version 12.0 and later, the `active` / `businessProcess` / `compactLayoutAssignment` / `description` / `label` / `picklistValues` fields, that `fullName` "can contain only underscores and alphanumeric characters", and the verbatim instruction not to prefix the object name inside the component. — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_recordtype.htm (verified 2026-08-14)
- Salesforce Well-Architected Overview — pillar definitions used to map the tradeoffs above. — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
