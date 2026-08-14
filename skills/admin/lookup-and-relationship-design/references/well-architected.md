# Well-Architected Notes — Lookup And Relationship Design

## Relevant Pillars

### Reliability

Relationship type is the least reversible decision in a Salesforce data model. Master-detail removes the Owner field from the detail object permanently — "The Owner field on the detail object isn't available and is automatically set to the owner of its associated master record" — and with it the ability to use sharing rules, manual sharing, or queues on that object. Reliability here means choosing the type from ownership and deletion semantics rather than from whichever capability was mentioned first in the requirement, and declaring `deleteConstraint` and `relationshipOrder` explicitly in source so a redeploy cannot quietly change either.

### Scalability

Query reach, not storage, is what a relationship graph runs out of. SOQL caps a single query at five child-to-parent levels, 55 child-to-parent relationships, and 20 parent-to-child relationships, and a custom object allows up to 40 relationships in total. A model designed without that budget scales in record count but not in queryability: the data is present and unreachable. Scalable models keep the common read path shallow and spend the depth budget deliberately.

### Security

Relationship type is a sharing decision wearing a data-model costume. Detail records inherit the master's sharing and security settings, so putting an object on the detail side hands its entire visibility model to the parent. That is the right answer when the child genuinely has no independent audience, and a security incident waiting to happen when it does. The `CHILD_SHARE_FAILS_PARENT` status code is the runtime expression of the same coupling: without adequate access to the parent, a user cannot change the owner of, or define sharing for, the child.

## Architectural Tradeoffs

**Cascade delete vs. independent ownership.** Master-detail gives cascade delete and roll-up summaries but costs the Owner field. A Lookup with `deleteConstraint` set to `Cascade` gives most of the delete behaviour while keeping ownership — at the price of no native roll-up summary. Decide which of the two you would rather rebuild in Apex, then pick.

**`Restrict` vs. `SetNull` on lookups.** `SetNull` is the platform default and fails open: the parent delete succeeds and the child is silently detached. `Restrict` fails closed: the delete is blocked and someone has to make a decision. Prefer `Restrict` wherever the link carries business meaning, and accept that admins will occasionally hit a delete they cannot complete — that friction is the control working.

**Depth vs. denormalisation.** A deep hierarchy is honest about the business but unqueryable past five hops. A cross-object formula flattening the middle of the chain trades a small amount of storage and a recalculation cost for a read path every report and component can actually follow. Flatten at the point the chain crosses a stable boundary, not at every level.

## Anti-Patterns

1. **Reaching for master-detail to get cascade delete.** Cascade is available on a Lookup through `deleteConstraint`; the Owner field is not recoverable once the object is on the detail side. Choosing master-detail for delete behaviour alone trades a permanent capability for one that had a cheaper substitute.

2. **Leaving `relationshipOrder` implicit on a junction object.** Creation order silently decides which master supplies the junction record's owner. Undeclared, the designation drifts between orgs and the visibility of every junction record drifts with it.

3. **Modelling depth the query layer cannot follow.** Adding the sixth child-to-parent hop is free in Setup and impossible in SOQL. Treat the five-level cap as a design constraint at whiteboard time, not a bug discovered during build.

## Official Sources Used

- Object Reference — Relationships Among Objects — detail-record Owner field, sharing-rule/manual-sharing/queue restrictions, cascade delete, inherited sharing (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/relationships_among_objects.htm
- Metadata API `CustomField` — `deleteConstraint` values (Cascade / Restrict / SetNull, SetNull is the default), `relationshipOrder` non-zero only on junction objects, `referenceTo` (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/customfield.htm
- Metadata API — Metadata Field Types — `DeleteConstraint` enum definition (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_field_types.htm
- SOQL and SOSL Reference — Understanding Relationship Query Limitations — five child-to-parent levels, 55 child-to-parent and 20 parent-to-child relationships per query, 40 relationships per custom object, five parent-to-child levels from API 58.0 (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships_query_limits.htm
- SOAP API Developer Guide — Core Data Objects / status codes — `CHILD_SHARE_FAILS_PARENT` (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_concepts_core_data_objects.htm
- Object Reference — Objects and Fields overview — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
