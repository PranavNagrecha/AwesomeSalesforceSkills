# Well-Architected Notes — Flow Invocable From Apex

## Relevant Pillars

- **Reliability** — The bulk contract (one list in, one list out, same length, same order) is what keeps invocables stable under load. Violations of this contract produce silent data corruption that is extremely difficult to debug.
- **Security** — Invocables expand the security surface: they run in Apex context, typically called by a flow running as an end user. Sharing posture (`with sharing` / `without sharing` / `inherited sharing`) must be declared explicitly and CRUD/FLS enforcement applied with `Schema.DescribeFieldResult` checks or `WITH SECURITY_ENFORCED` SOQL.
- **Performance** — A well-bulked invocable is cheaper per record than equivalent Flow logic because Apex can batch SOQL/DML. A poorly-bulked one is dramatically more expensive because each request-loop iteration counts separately.
- **Operational Excellence** — The `label`, `description`, and `category` parameters on `@InvocableMethod` are the admin-facing contract. A well-documented invocable is usable by admins without reading the source; a poorly-documented one generates support tickets.

## Architectural Tradeoffs

### Soft-error vs fault-path error handling

| Approach | When | Cost |
|---|---|---|
| Populate `error` output field | Business-rule failures the admin should branch on | Flow must read & branch — more complexity in the flow |
| Throw `AuraHandledException` | System failures the admin should log + continue | Fault path must be wired on every action usage |
| Throw plain `Exception` | Fatal errors that must roll back the whole transaction | Every call site needs try/catch or accepts rollback |

Prefer soft errors for business-rule failures; fault paths for system failures; never use plain `Exception` unless rollback is the desired outcome.

### Inner vs top-level wrapper classes

Inner classes are fine for single-use invocables. Promote to top-level when two or more invocables share the wrapper shape — saves duplication and makes refactoring safer.

### Direct callouts vs Platform Event indirection

When a flow needs to trigger external work, the invocable can either issue a callout directly (with `callout=true`) or publish a Platform Event that an external subscriber consumes (via the Pub/Sub API). Direct callouts are simpler for synchronous needs; Platform Events decouple producer and consumer and give replay / durability for free.

## Anti-Patterns

1. **Per-record SOQL inside the invocable loop** — Treating the invocable as if Flow calls it per-record and issuing a SOQL per input. Fails at ~50 records. Always bulk-query once for the entire input list.

2. **Shortened output list to "skip" records** — Returning fewer outputs than inputs shifts all downstream Flow Loop references onto the wrong records. Always return `inputs.size()` elements; use an explicit `status='skipped'` marker for records to ignore.

3. **Static caches shared across interviews** — A `static Map` built in one interview leaks data into subsequent interviews in the same transaction. Build lookup maps as local variables; use `Platform Cache` with explicit partition for genuine cross-call reuse.

4. **Exposing internal exception details to Flow faults** — Throwing `new Exception(e.getMessage())` can surface stack details to the flow's fault connector, which may render in user-facing error screens. Wrap with `AuraHandledException` and log internally.

5. **Undocumented wrapper variables** — Omitting `description` on `@InvocableVariable` leaves admins guessing what each field does in Flow Builder. Treat the description as mandatory public API documentation.

## Official Sources Used

- Salesforce Developer — `@InvocableMethod` Annotation: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_InvocableMethod.htm
- Salesforce Developer — `@InvocableVariable` Annotation: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_InvocableVariable.htm
- Salesforce Developer — Flow.Interview Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Flow_Interview.htm
- Salesforce Help — Customize Flow Behavior with Apex: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_apex.htm
- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/design/architecture-framework/well-architected
