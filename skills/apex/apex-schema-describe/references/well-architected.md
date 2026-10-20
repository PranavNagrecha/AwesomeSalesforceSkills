# Well-Architected Notes — Apex Schema Describe

## Relevant Pillars

- **Operational Excellence** — `static final` caching of describe
  results avoids repeated describes in hot paths. The "50ms vs
  500ms trigger" figure is UNVERIFIED (2026-10-20): no guide measures it.
- **Security** — both check the running user: `isAccessible()` tests one
  field (apexdev 264 L12473-12474); `Security.stripInaccessible` also
  removes the fields (L12281-12282). For bulk DML, use stripInaccessible.

## Architectural Tradeoffs

- **Compile-time `Account.Name` vs runtime `getGlobalDescribe()`.**
  Compile-time has zero describe cost; only viable when the
  type/field is known at code-write time.
- **Per-call describe vs cached describe.** Per-call is simpler;
  cached scales. Hot paths require caching.
- **`stripInaccessible` vs per-field FLS check.** Strip is bulk-
  safe and runtime-context-aware; per-field is more explicit but
  doesn't scale to bulk DML.

## Anti-Patterns

1. **`getGlobalDescribe()` inside loops.**
2. **`getDescribe()` per field per record.**
3. **Assuming `getPicklistValues()` returns inactive values** (it returns active only, apexref 262 L190851).
4. **Type.forName for SObject lookup.**
5. **Hardcoded `getRecordTypeInfosByName()`** (label, renameable).

## Official Sources Used

- Apex Developer Guide 264 — getGlobalDescribe map, permissions-based (salesforce_apex_developer_guide.txt L11244-11249); namespace-prefixed keys at API 28.0+ (L11255-11257); field-map keys case-insensitive (L11079); dynamic creation via `newSObject()` (L11795-11801)
- Apex Reference Guide 262 — `getPicklistValues()` returns active values only (salesforce_apex_reference_guide.txt L190851); `getRecordTypeInfosByName()` keys on labels (L192589); `describeSObjects` (L229191, DEFERRED default L229225-229227); `Type.forName('Account')` example (L242043-242045)

- Schema Class Reference — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Schema.htm
- Schema.SObjectType — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Schema_SObjectType.htm
- Schema.DescribeFieldResult — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_fields_describe.htm
- Security.stripInaccessible — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Security.htm
- PicklistEntry — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Schema_PicklistEntry.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
