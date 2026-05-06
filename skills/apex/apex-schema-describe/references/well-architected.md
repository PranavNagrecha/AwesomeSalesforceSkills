# Well-Architected Notes — Apex Schema Describe

## Relevant Pillars

- **Operational Excellence** — `static final` caching of describe
  results is the highest-leverage Apex perf discipline. The
  difference between a 50ms trigger and a 500ms trigger.
- **Security** — `Security.stripInaccessible` honors runtime
  user context; per-field `getDescribe().isAccessible()` doesn't
  always. For FLS-correctness on bulk DML, use stripInaccessible.

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
3. **Picklist enumeration without `isActive()` filter.**
4. **Type.forName for SObject lookup.**
5. **Hardcoded `getRecordTypeInfosByName()`** (label, renameable).

## Official Sources Used

- Schema Class Reference — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Schema.htm
- Schema.SObjectType — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Schema_SObjectType.htm
- Schema.DescribeFieldResult — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_fields_describe.htm
- Security.stripInaccessible — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Security.htm
- PicklistEntry — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Schema_PicklistEntry.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
