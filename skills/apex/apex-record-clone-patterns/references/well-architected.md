# Well-Architected Notes — Apex Record Clone Patterns

## Relevant Pillars

Cloning records looks like a one-line operation; the architectural
weight comes from what travels (or doesn't) with the copy, who can
preserve audit history, and how the clone is traced after the fact.

- **Reliability** — `.clone()` is shallow by default and the
  `isDeepClone` flag does NOT traverse child relationships. Teams
  that ship a duplicate button on a parent record without explicit
  child-handling code build a feature that "works" in dev and silently
  loses related Notes, Attachments, Files, and child sObjects in
  production. The reliability failure isn't an exception — it's
  missing data, discovered weeks later. Designing for "what travels
  with the clone" is the single largest architectural decision in this
  domain.
- **Security** — `preserveReadonlyTimestamps=true` requires the
  running user to have the `CreateAuditFields` system permission AND
  the org-level "Set Audit Fields upon Record Creation" feature
  enabled. Without both, the flag is silently ignored — there's no
  exception. Cloning operations exposed to community/portal users
  through Lightning Actions or LWC must explicitly enforce CRUD/FLS
  via `Security.stripInaccessible()` or `WITH SECURITY_ENFORCED` in
  the cloning SOQL, because `.clone()` itself does not run any access
  check.
- **Operational Excellence** — Cloned records are
  *origin-anonymous* once the Apex transaction ends. Support engineers
  investigating "why does this record look weird" have no way to
  trace a clone back to its source without an explicit `Cloned_From__c`
  lookup field (or text External Id). Adding one custom field per
  cloneable object is a tiny investment with outsized payoff for
  troubleshooting and data lineage audits.
- **Performance** — The JSON serialize/deserialize deep-clone
  pattern peaks at roughly 2× the source graph size in heap memory
  during the round-trip. For a synchronous transaction (6MB heap),
  source graphs above ~1k total records hit `LimitException`. The
  alternative (per-level explicit cloning with `Map<Id, Id>` lookup
  translation) trades code complexity for headroom — a real
  architectural tradeoff that depends on how big and how deep the
  source graphs actually get in production.

## Architectural Tradeoffs

The defining tradeoff is **which clone mechanism to use for a given
duplication need**. Five options sit on a spectrum from "platform
primitive" to "custom service class":

| Approach | Best for | Cost / Failure mode |
|---|---|---|
| `src.clone()` shallow | Single record, no children, no audit-history preservation | Misses child records; doesn't preserve audit |
| `src.clone(false, false, false, true)` autonumber-preserve | Test data builder needing same autonumber, migration row-mirroring | Same shallow limits; uniqueness collisions if downstream code keys on autonumber |
| `JSON.serialize` + `JSON.deserialize` | Parent + ≤1k records of children, one-shot admin actions | Heap-bound (~6MB sync); CPU-bound; relationship rewriting still manual |
| Manual `new SObject(field = value, ...)` field-by-field copy | Almost never — see `examples.md` anti-pattern | Schema drift makes the copy lose fields silently as the schema grows |
| `Database.merge()` for true duplicates | Two records that should become one (deduplication, not cloning) | Different operation — merges instead of cloning; only works on Accounts, Contacts, Leads |
| Custom `DuplicateBuilder` service class | Repeated clone-with-rules logic across multiple call sites | Higher up-front investment; pays back on the 3rd+ call site |

The handoff rule that works in practice: **start with `.clone()`,
upgrade to JSON round-trip when children must travel, build a service
class when the same clone rules show up in 3+ places.** The manual
field-by-field copy is never the right answer — it looks tidy in code
review and becomes a long-term maintenance liability because schema
additions silently bypass it.

A second tradeoff: **flag intent vs. terseness**. `src.clone()` is
concise. `src.clone(false, true, false, false)` makes every flag
decision visible at the call site. For one-off scripts the terse form
is fine; for production code, prefer the four-arg form even when all
flags are `false` — code reviewers can see the intent without having
to remember default values, and the call site becomes the documentation
for "we considered preserveAutonumber and rejected it." The minor
verbosity cost buys clarity that pays off the next time someone
modifies the cloner.

A third tradeoff: **clone-then-modify vs. constructor-then-copy**.
After `.clone()`, the developer can mutate fields on the copy (the
canonical pattern). Some teams prefer building a fresh constructor
with just the overrides, ostensibly for "clearer intent" — but this
loses the future-proofing of `.clone()` (every schema addition flows
through automatically) and re-introduces the manual-field-copy
problem. Always clone first, override second. The override lines are
the diff that tells a code reader "this is what changes between
source and copy."

## Anti-Patterns

1. **Treating `isDeepClone=true` as "clone with children."** The flag
   preserves formula/aggregate values in the in-memory copy; it does
   NOT traverse relationships. Use the JSON round-trip pattern or
   explicit child-by-child cloning for relationship traversal.
2. **`clone(preserveId=true)` followed by `insert`.** Always throws
   `DUPLICATE_VALUE`. `preserveId=true` is for in-memory work only —
   tests asserting equality, builder patterns needing Id-keyed maps
   before any DML.
3. **Manual field-by-field copy via `new SObject(field = src.field,
   ...)`.** Loses fields silently every time the schema grows. The
   "clean" appearance in code review is the trap. Always start with
   `.clone()`.
4. **No traceability field on cloned records.** Support engineers
   have no way to find the source after the fact. Adding a single
   `Cloned_From__c` lookup per cloneable object is a low-cost,
   high-payoff governance move.
5. **JSON round-trip deep clones on graphs >1k records in a sync
   transaction.** Peaks at 2× source graph size in heap; hits 6MB
   sync limit. Move to Queueable / Batch when source size is unbounded,
   or fall back to per-level explicit cloning with `Map<Id, Id>`
   translation.

## Official Sources Used

- Apex Developer Guide — Using SObjects:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SObjects_clone.htm
- Apex Reference Guide — SObject Class (clone method overloads):
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_sobject.htm
- Apex Reference Guide — System.JSON Methods (serialize/deserialize):
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_System_JSON_deserialize.htm
- Apex Developer Guide — Roundtrip Serialization and Deserialization:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_json_json.htm
- Salesforce Help — Set Audit Fields upon Record Creation (permission required for `preserveReadonlyTimestamps`):
  https://help.salesforce.com/s/articleView?id=sf.000334726.htm
- Salesforce Well-Architected — Trusted (Secure):
  https://architect.salesforce.com/well-architected/trusted/secure
