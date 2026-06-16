# Gotchas — Apex Record Clone Patterns

Second-order behaviors that bite practitioners after they've moved
past the obvious `clone()` mistakes. These compound the rules in
`SKILL.md`'s gotchas section — these are the issues that only surface
when you push beyond the first working version of a clone.

## Gotcha 1: `.clone()` default is shallow — Notes, Attachments, Files, ContentDocumentLinks do NOT travel

**What happens:** A developer clones a Case for the "Duplicate Case"
button using `src.clone()` and ships it. Two weeks later support
reports that duplicates are missing the attached PDFs and the
escalation notes from the source Case. The bug surfaces because users
rely on attachments and notes for context — they assumed a "duplicate"
would mirror the source completely.

**When it occurs:** Any clone of a parent record where the source has
related child records — child sObjects via lookup/master-detail,
classic Notes (`Note`), classic Attachments (`Attachment`), modern
Files (via `ContentDocumentLink`), Tasks, Events, Chatter feed posts,
EmailMessages on Case, Knowledge linkages, or anything else with the
source's Id as a foreign key. `isDeepClone=true` does NOT help here
— that flag controls in-memory formula/aggregate preservation, not
relationship traversal. The name is misleading and is the root cause
of most clone-coverage bugs.

**How to avoid:** Enumerate every child relationship you care about
in the source SOQL (subselects for direct children; separate queries
for `ContentDocumentLink` because polymorphic FKs can't be subselected
from the parent). For each child collection: query → `child.clone()`
→ reparent the FK to the new parent's Id → bulk insert. For
`ContentDocumentLink` specifically you don't clone the Files
themselves (the binary `ContentVersion` payload is shared across
links) — you just insert new `ContentDocumentLink` rows pointing the
existing `ContentDocumentId` at the new `LinkedEntityId`. Document the
list of "what travels with a clone" in your code comments so the next
developer doesn't have to reverse-engineer it.

---

## Gotcha 2: `preserveReadonlyTimestamps=true` silently no-ops without the `CreateAuditFields` user permission

**What happens:** A migration script runs `src.clone(false, false,
true, false)` intending to preserve `CreatedDate`, `CreatedById`,
`LastModifiedDate`, and `LastModifiedById` on the copies. The script
runs without error. Spot-check reveals every cloned record has
`CreatedDate = <time the migration ran>` — the original timestamps
were dropped. No exception, no warning, no debug log entry hinting at
the cause.

**When it occurs:** Any context where the running user lacks the
"Set Audit Fields upon Record Creation" system permission (also
displayed as `CreateAuditFields`) AND/OR the org hasn't enabled the
"Set Audit Fields upon Record Creation" feature under Setup → User
Interface. Both gates must be in place; the flag is permissive in the
API — it asks the platform to preserve, but the platform silently
discards the request if the user can't. Note the parameter is named
`preserveReadonlyTimestamps` in the four-arg signature; older code
and docs sometimes say `preserveReadonly`, which refers to the same
flag.

**How to avoid:** Before relying on the preserved timestamps, verify
the running user can actually do it:

```apex
Boolean canPreserve =
    FeatureManagement.checkPermission('CreateAuditFields');
System.assert(canPreserve,
    'Running user lacks CreateAuditFields — audit fields will reset.');
```

For production migration runs, only use this in test contexts or
under a dedicated integration user with the permission assigned via
permission set. Don't preserve audit fields for "normal" duplicate
buttons — the duplicate was actually created now, and preserving the
source's timestamps misrepresents reality to anyone reading the audit
log later. Reserve the flag for data-migration / org-split scenarios
where preserving history is the explicit goal.

---

## Gotcha 3: `.clone(preserveId=true)` cannot be DML-inserted — you get `System.DmlException: DUPLICATE_VALUE`

**What happens:** A developer reads `preserveId` in autocomplete,
assumes "preserve" means "carry through the insert," writes
`Account copy = acc.clone(true); insert copy;`, and ships. At runtime
the insert throws `System.DmlException: Insert failed. First
exception on row 0; first error: DUPLICATE_VALUE, duplicate value
found: <unknown> duplicates value on record with id: <the source
Id>: []`. The error is cryptic; the fix is non-obvious unless you
know `preserveId=true` is meant for in-memory use only.

**When it occurs:** Any code path that calls `clone(true, ...)` and
then attempts `insert`, `upsert`, or `Database.insert()` on the
result. Salesforce won't allow DML insert of a record with a non-null
Id — the Id is the database's to assign, and inserting one violates
the uniqueness contract. The same `DUPLICATE_VALUE` surfaces for
`upsert` because upsert reads the supplied Id as "this row already
exists, update it" — which then fails because the existing row is
the source, not the in-memory clone.

**How to avoid:** Use `preserveId=true` ONLY when the clone won't be
inserted — typical use cases are unit tests asserting before/after
state, in-memory graph construction (e.g., test data builders that
need an Id-keyed map before any DML), and side-by-side diffing in
controllers. For any path that ends in `insert`, use `clone()` (no
args) or `clone(false, ...)`. The skill's
`scripts/check_apex_record_clone_patterns.py` checker scans for
`clone(true, ...)` followed by `insert` in the same class — wire it
into your CI to catch this before code review.

---

## Gotcha 4: `OwnerId` clones across users, but `Email`, `Phone`, and address compound fields have per-object quirks

**What happens:** A clone of a Contact carries `OwnerId` through to
the copy — usually fine, occasionally surprising (the new Contact
belongs to whoever owned the source, not the user running the clone).
Meanwhile, address compound fields (`MailingAddress`, `BillingAddress`)
clone field-by-field, but normalized geocode fields like
`MailingLatitude`/`MailingLongitude` may be re-derived on save by the
Data.com / Maps Geocoding cleanup rule, blanking the cloned values.
`Email` fields clone literally, which can trigger unique-email
constraints on PersonAccount or Customer Community users. `Phone`
fields clone literally and don't re-normalize.

**When it occurs:** Cloning standard sObjects where address geocoding
is enabled (Setup → Data.com → Clean Rules → Geocodes), cloning
Person Accounts or Community User records where Email is the
External_Id, or cloning Contacts/Leads where the org has a
data-quality rule on duplicate emails. The Owner behavior surfaces
whenever a clone is performed by a user who isn't the source's owner
— the new record looks "wrong" in the cloning user's My Records
report.

**How to avoid:** Be explicit about ownership: after `.clone()`, set
`copy.OwnerId = UserInfo.getUserId()` (or whatever the new-owner
rule is for your business). For email-keyed sObjects, blank out
`Email` and force the user to re-enter — or append a suffix like
`copy+<random>@example.com` to satisfy uniqueness until the user
edits it. For geocoded addresses, either accept that the cleanup rule
will re-derive coordinates on next batch run, or preemptively null
out `<addressPrefix>Latitude` / `<addressPrefix>Longitude` so the
cleanup rule starts from a clean state. Audit any "external Id" text
field on the object and decide whether the clone should carry it,
blank it, or get a synthetic suffix.

---

## Gotcha 5: JSON deep-clone pattern hits `LimitException: Apex CPU time limit exceeded` on graphs with >5 levels of nested children

**What happens:** A practitioner adapts the JSON deep-clone pattern
from `examples.md` Example 2 for an Account graph with five levels
nested (Account → Opportunity → OpportunityLineItem →
OpportunityLineItemSchedule → custom child object → another custom
child). On a small source (3 levels populated), the clone runs in
~400ms. On a real-world large source (every level populated with
20+ records each), the clone throws `System.LimitException: Apex
heap size too large` or `System.LimitException: Apex CPU time limit
exceeded` part-way through `JSON.serialize()`. Heap usage during
serialize can briefly hit 6MB on a populated graph, and the
serialize/deserialize round-trip is single-transaction so the limit
is the full 6MB synchronous / 12MB async heap.

**When it occurs:** Any JSON-based deep clone where the source graph
is meaningfully deep AND wide. The serializer doesn't stream — it
builds the full JSON string in heap, then deserialize allocates a
mirror in-memory graph, so peak memory is roughly 2× the source
graph's size in addition to the original SOQL result. CPU spends
linearly with the number of fields serialized. Empirically the
pattern is safe for ~1k total records across all levels in a sync
transaction; beyond that you need to split.

**How to avoid:** For graphs that flirt with the limits, abandon JSON
round-trip and use per-level explicit cloning with
`Map<Id, Id>` translation tables (one per child relationship) and
incremental insert. Or move the clone to Queueable / Batch where the
12MB heap and 60-second CPU limits buy headroom. Watch heap with
`Limits.getHeapSize()` / `Limits.getLimitHeapSize()` around the
serialize call to catch this in dev before production traffic does.
For one-shot admin tools cloning at most a handful of records, the
JSON pattern is fine — the failure mode is loud (limit exception),
just not what the developer expected the first time it fired.
