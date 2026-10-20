# Well-Architected Notes — Apex Managed Sharing

## Relevant Pillars

- **Security** — Apex managed sharing directly controls who can read and edit records. A misconfigured row cause, a missing `without sharing` on the wrong class, or a dropped share row after OWD recalculation can expose data to unauthorized users or lock legitimate users out. Every design decision in this skill has a direct security impact.
- **Reliability** — Share rows must be durably rebuilt after platform recalculation events. A recalculation class that silently under-queries (wrong sharing keyword) or is not registered on the reason produces sharing outages that are difficult to diagnose. Reliability requires testing the recalculation path explicitly, not just the happy-path trigger.
- **Performance** — Share DML at scale must go through batch Apex. Synchronous triggers that insert hundreds of share rows per record hit DML limits quickly and slow platform performance. Batch recalculation should use a batch size tuned to the DML volume per record (typical: 200 parent records per execute, each yielding 5–20 share rows = 1,000–4,000 DML rows per execute, well within the 10,000 limit).
- **Operational Excellence** — Custom row causes create auditable, queryable share grants. Teams should instrument the Share table with periodic SOQL audit jobs to detect missing or stale grants before users report access issues.

## Architectural Tradeoffs

**Trigger-based sharing vs. batch recalculation:**
Trigger-based share inserts are real-time and transactional but constrained by governor limits. They are appropriate when sharing grants are small (one share row per triggering record) and closely tied to a single DML event. Batch recalculation is appropriate when the sharing model can drift (e.g., territory reassignments affecting thousands of records) and correctness requires a full rebuild. In practice, both are used together: triggers maintain shares incrementally, and the recalculation batch provides a safety net for rebuilding after platform events.

**Custom row cause vs. `Manual`:**
Using `Manual` as the row cause is simpler (no sharing-reason prerequisite) but means the platform cannot distinguish Apex-managed grants from user-initiated manual shares, and Manual shares are removed when the record owner changes (apex dev guide 264 L12606, L12756-12757). UNVERIFIED (2026-10-20): that Manual grants are cleared by a manual sharing recalculation. Custom row causes add a metadata dependency but make the Share table auditable and survive an owner change (L12610-12611).

**`without sharing` scope:**
`without sharing` should be scoped as narrowly as possible — ideally only to the recalculation batch class and never to general business logic classes. Using `without sharing` broadly to work around sharing configuration problems is an anti-pattern that eliminates the platform's access control guarantees.

## Anti-Patterns

1. **Using `Manual` row cause for long-lived Apex grants** — Grants with `RowCause = 'Manual'` are removed when the record owner changes (apex dev guide 264 L12606) and when they become redundant after an OWD change (L13050-13052). UNVERIFIED (2026-10-20): that a manual recalculation run from Setup clears them. Use a custom Apex sharing reason for grants that must survive an owner change.

2. **Broad `without sharing` on the feature class** — Placing `without sharing` on the trigger handler or service class (rather than only the recalculation batch) bypasses record-level security for all operations in that class, not just sharing DML. This exposes records to all users who can trigger the code path, violating the principle of least privilege. Scope `without sharing` to the recalculation class only.

3. **Not associating a recalculation class with the object** — Apex recalculation classes defined for a custom object run on an OWD change (apex dev guide 264 L13071-13072) and from the object's detail page (L13059). UNVERIFIED (2026-10-20): that without one an OWD change or full recalculation permanently destroys all Apex-managed grants with no error or alert.

## Official Sources Used

- Apex Developer Guide — Creating Apex Managed Sharing: share objects, access levels, row causes, the recruiting trigger and recalculation sample: apex dev guide 264 L12596-13110 — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_creating_with_apex.htm
- Metadata API Developer Guide — SharingReason: api_meta 264 L47631-47650
- Object Reference — AccountShare: object_reference 264 L17338-17474
- Apex Developer Guide — Understanding Apex Managed Sharing: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Apex Developer Guide — Sharing Recalculation: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_sharing_recalc.htm
- Apex Developer Guide — Using the with sharing, without sharing, and inherited sharing Keywords: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Security Guide — Record-Level Security: https://help.salesforce.com/s/articleView?id=sf.security_sharing_about.htm
