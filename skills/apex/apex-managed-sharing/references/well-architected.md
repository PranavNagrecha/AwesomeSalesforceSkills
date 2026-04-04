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
Using `Manual` as the row cause is simpler (no Setup prerequisite) but means the platform cannot distinguish Apex-managed grants from user-initiated manual shares. More importantly, the grants are cleared and cannot be automatically rebuilt during manual sharing recalculation. Custom row causes add a Setup dependency but enable registered recalculation and make the Share table auditable.

**`without sharing` scope:**
`without sharing` should be scoped as narrowly as possible — ideally only to the recalculation batch class and never to general business logic classes. Using `without sharing` broadly to work around sharing configuration problems is an anti-pattern that eliminates the platform's access control guarantees.

## Anti-Patterns

1. **Using `Manual` row cause for long-lived Apex grants** — Grants with `RowCause = 'Manual'` are cleared by manual sharing recalculation. If a user runs recalculation from Setup, all programmatic grants using `Manual` disappear with no automatic rebuild. Always use a custom Apex sharing reason for grants that must survive platform recalculation.

2. **Broad `without sharing` on the feature class** — Placing `without sharing` on the trigger handler or service class (rather than only the recalculation batch) bypasses record-level security for all operations in that class, not just sharing DML. This exposes records to all users who can trigger the code path, violating the principle of least privilege. Scope `without sharing` to the recalculation class only.

3. **Not registering a recalculation class on the Apex sharing reason** — Deploying code that creates share rows with a custom row cause but not registering the recalculation class in Setup means that an OWD change or full recalculation will permanently destroy all Apex-managed grants for the object. There is no automatic rebuild, no error, and no alert. The data access loss may not be discovered until users report it.

## Official Sources Used

- Apex Developer Guide — Creating Apex Managed Sharing: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_creating_with_apex.htm
- Apex Developer Guide — Understanding Apex Managed Sharing: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Apex Developer Guide — Sharing Recalculation: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_sharing_recalc.htm
- Apex Developer Guide — Using the with sharing, without sharing, and inherited sharing Keywords: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Security Guide — Record-Level Security: https://help.salesforce.com/s/articleView?id=sf.security_sharing_about.htm
