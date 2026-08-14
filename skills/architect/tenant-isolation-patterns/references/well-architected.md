# Well-Architected Notes — Tenant Isolation Patterns

## Relevant Pillars

- **Secure (primary)** — isolation is the product promise, and on this platform it has two independent halves that get
  conflated. Sharing keywords and sharing rules control *which records*; access mode and FLS control *which fields*.
  "Sharing declarations don't enforce object-level access or field-level security" — a tenant design
  that only addresses the first half is half a design, and the missing half is invisible until an sObject is serialised
  to a frontend.
- **Resilient** — the failure mode of a leaky tenant boundary is not degraded service, it is a disclosure incident with
  a contractual counterparty. That asymmetry justifies failing closed everywhere: an unresolvable feature flag is off,
  an unrecognised tenant sees nothing.
- **Adaptable** — tenant-specific Apex is the debt that compounds fastest. Every branch is a permanent tax on every
  future change, and the branches are discovered rather than documented. Configuration-driven variation (Custom
  Metadata, Custom Permissions, record types) keeps the codebase single.
- **Automated** — onboarding and offboarding are the operations that get performed under pressure, by whoever is
  available. If either is a sequence of remembered clicks, isolation degrades one tenant at a time.

## Architectural Tradeoffs

**One org with logical tenants vs one org per tenant.** Separate orgs give a boundary the platform enforces and no
shared-release coordination; they also multiply the deployment surface by the tenant count and make cross-tenant
reporting an integration project. Logical tenancy is cheaper to operate and puts the entire isolation burden on a
sharing model that must be correct on every object, forever. The deciding question is not cost — it is whether any
tenant needs its own release cadence or its own compliance boundary. If one does, the org boundary is the honest
answer.

**Apex managed sharing vs declarative sharing.** Apex managed sharing expresses arbitrary tenant rules, survives owner
changes, and is attributable through named sharing reasons. It is also limited to custom objects, requires "Modify All
Data" to write, cannot grant to unauthenticated guest users, and adds a recalculation story you now own. Declarative
sharing is bounded but free and visible to admins. Use declarative sharing until a requirement provably cannot be
expressed that way, and write down which requirement forced the change.

**Tenant filter in the query vs in the platform.** A `WHERE Tenant__c = :x` clause is immediate, testable, and holds
only for the code paths that remember it — reports, list views, the REST API, and Flow do not. Platform-enforced access
(OWD Private plus tenant-scoped sharing) is slower to build and cannot be forgotten by a future query. The application
filter is acceptable as defence in depth; it is not acceptable as the boundary.

**Cross-tenant reporting placement.** A role above the tenant branches satisfies the reporting requirement in an
afternoon and grants record-level access to everything in every tenant, permanently. A summarised object or an
analytics tool with its own security predicate takes longer and keeps the boundary intact. The requirement is almost
always aggregate numbers, so the expensive-looking option is usually the correct one.

## Anti-Patterns

1. **Sharing keyword as the whole isolation story.** Declaring services `with sharing` and considering the tenant
   boundary closed. Records are filtered; fields are not. At API version 67.0 and later, database operations default to
   user mode and classes without a sharing declaration default to `with sharing` — two different switches that people
   read as one.
2. **The cross-tenant role above the hierarchy.** Placing a "global admin" or regional role above two tenant branches
   to satisfy reporting. Managed sharing grants upward by design and no sharing rule subtracts access, so the grant is
   total and permanent for anyone who ever holds the role.
3. **Feature flags that fail open.** Calling `FeatureManagement.checkPermission` without handling the
   `System.NoDataFoundException` thrown for a permission that is not deployed in the org — which is the *normal* state
   for a newly-onboarded tenant. Unhandled, it fatals the transaction; handled carelessly, it defaults a premium
   capability on.
4. **Testing isolation between peers only.** Two peer users in two tenants is the case that always passes. The failures
   live at the hierarchy edges, in guest contexts, and in anonymous Apex — which, with Connect in Apex, "always run[s]
   in with sharing mode", so an admin console check proves nothing about the tenant model.

## Official Sources Used

- Apex Developer Guide, Version 67.0 (Summer '26) — *Understanding Apex Managed Sharing*: the "Modify All Data"
  requirement, that Apex managed sharing is maintained when the record owner changes or is deactivated, and the
  custom-objects-only restriction on sharing reasons and recalculation.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Sharing a Record Using Apex*: the `AccessLevel` requirement relative to OWD,
  the guest-user prohibition on `UserOrGroupId`, and the `RowCause="Manual"` default with its ownership-change
  deletion behaviour.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_creating_with_apex.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Using the with sharing, without sharing, and inherited sharing Keywords*: the
  FLS disclaimer, the API 67.0 default, and "Anonymous Apex and Connect in Apex always run in with sharing mode".
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm (verified 2026-08-14)
- Repo template `templates/apex/TriggerControl.cls` — the memoised, fail-closed `FeatureManagement.checkPermission`
  wrapper and its citation of the Winter '20 behaviour change (`System.NoDataFoundException` for an undefined API name,
  formerly `false`).
