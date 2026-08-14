# Gotchas — Tenant Isolation Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Apex managed sharing — the isolation primitive — is custom-objects-only

**What happens:** Apex managed sharing is the mechanism most tenant designs reach for when declarative sharing runs
out, and it carries a hard scope limit stated twice in the Apex Developer Guide: "Apex sharing reasons and Apex managed
sharing recalculation are only available for custom objects."

That single sentence eliminates the pattern for `Account`, `Contact`, `Case`, and `Opportunity`. Shares on standard
objects can still be inserted from Apex, but they are user managed shares — and "Manual shares written using Apex
contains `RowCause="Manual"` by default. Only shares with this condition are removed when ownership changes." So a
tenant grant written that way on a standard object silently disappears the first time a record changes hands.

**When it occurs:** During the second phase of a multi-tenant build, after the custom-object prototype worked. The
standard-object tenant grants pass their tests — the test never reassigns ownership — and evaporate in production
during a territory realignment or an offboarding.

**How to avoid:** Confirm the object type before designing around Apex managed sharing. On custom objects, define a
named Apex sharing reason and reference it as `Schema.CustomObject__Share.rowCause.SharingReason__c` (for example
`Schema.Job__Share.rowCause.Recruiter__c`) so the grant is durable, attributable, and separable from other grants to
the same user. On standard objects, isolate through owner assignment, criteria-based sharing, and the role hierarchy
instead, and state in the design that ownership changes will remove any Apex-written manual share.

---

## Gotcha 2: Apex managed sharing needs "Modify All Data", and guest users cannot be granted anything

**What happens:** Two access constraints sit on the mechanism itself. "Only users with 'Modify All Data' permission can
add or change Apex managed sharing on a record." And on the `UserOrGroupId` field of a share object: "You can't grant
access to unauthenticated guest users using Apex."

There is a third that determines whether a share does anything at all — the `AccessLevel` field "must be set to an
access level that's higher than the organization's default access level for the parent object". Writing `Read` into a
share on an object whose OWD is already Public Read is not a grant; it is an error.

**When it occurs:** The "Modify All Data" requirement bites when the sharing code is invoked from a context that is not
running as an integration user — a tenant admin flipping a flag, an LWC action, a Queueable started by an end user.
The guest-user constraint bites in Experience Cloud tenant designs, usually late, because guest access is the last
scenario anyone tests.

**How to avoid:** Run tenant-share maintenance from a dedicated, permission-audited context rather than from whatever
user happened to trigger it, and confirm the OWD is more restrictive than every access level your code writes. For
guest scenarios, plan around guest user sharing rules from the start — Apex is not an escape hatch there.

---

## Gotcha 3: `with sharing` isolates records, not fields

**What happens:** "Sharing declarations don't enforce object-level access or field-level security."
Sharing keywords are a record-visibility control and nothing more. A tenant-scoped service declared `with sharing`
returns only the calling tenant's records — and returns every field on them, including fields the user's Profile and
Permission Sets do not grant.

Two related facts change the shape of this at API version 67.0. Database operations now run in user mode by default,
so FLS is enforced on the query unless something opts out; and "In API version 67.0 and later, classes without an
explicit sharing declaration run in `with sharing` mode." The keyword and the access mode are separate switches that
people conflate.

**When it occurs:** In cross-tenant reporting features and in any service that serialises an sObject to JSON for a
frontend. Record isolation holds; field isolation was never in play.

**How to avoid:** Treat sharing and FLS as two decisions with two mechanisms. State the access mode on the operation
(`WITH USER_MODE`, `as user`, `AccessLevel.USER_MODE`) or strip with
`Security.stripInaccessible(AccessType, records).getRecords()` before serialising, and read the class's `apiVersion`
before assuming either default. Note also: "Anonymous Apex and Connect in Apex always run in with sharing mode" — an
admin's console script is not a test of the tenant model.

---

## Gotcha 4: The role hierarchy is an isolation hole that no sharing rule closes

**What happens:** Managed sharing grants access up the role hierarchy by design. Tenants modelled as branches of one
hierarchy therefore leak upward to any role above them, and a criteria-based sharing rule cannot subtract that access —
sharing rules only ever grant.

**When it occurs:** When a "global admin" or "regional manager" role is placed above two tenant branches to satisfy a
reporting requirement. The requirement was aggregate numbers; the implementation grants record-level access to
everything in both tenants, permanently, to anyone who ever holds that role.

**How to avoid:** Put cross-tenant reporting roles beside the tenants rather than above them, and satisfy aggregate
reporting through a summarised object or an analytics tool with its own security predicate. Validate isolation with a
two-tenant fixture that includes a user at every level of the hierarchy, not just two peer users — peer-to-peer
isolation is the case that always passes.

## Official Sources Used

- Apex Developer Guide, Version 67.0 (Summer '26) — *Understanding Apex Managed Sharing*: "Only users with 'Modify All
  Data' permission can add or change Apex managed sharing on a record", "Apex managed sharing is maintained when the
  record owner changes or is deactivated", and the note that "Apex sharing reasons and Apex managed sharing
  recalculation are only available for custom objects".
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Sharing a Record Using Apex*: the `AccessLevel` "higher than the organization's
  default access level" requirement, "You can't grant access to unauthenticated guest users using Apex", and the
  `RowCause="Manual"` default with its ownership-change deletion behaviour.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_creating_with_apex.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Using the with sharing, without sharing, and inherited sharing Keywords*:
  "Sharing declarations don't enforce object-level access or field-level security"; the API 67.0
  default of `with sharing` for undeclared classes; and "Anonymous Apex and Connect in Apex always run in with sharing mode".
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Set an Access Mode for Database Operations* and *Versioned Behavior Changes*:
  user mode as the API 67.0 default, system mode at 66.0 and earlier.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security_sharing_chapter.htm (verified 2026-08-14)
