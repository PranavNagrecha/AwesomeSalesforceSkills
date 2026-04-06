# Well-Architected Notes — Sharing Recalculation Performance

## Relevant Pillars

- **Performance** — Sharing recalculation is one of the most resource-intensive background operations on the Salesforce platform. Poorly sequenced structural changes — OWD tightening without deferral, criteria-based rules on high-churn fields, deeply nested public groups — can produce multi-hour background jobs that degrade platform responsiveness for all users.
- **Reliability** — A full recalculation triggered during business hours introduces access inconsistency windows: users may gain or lose access to records intermittently while the job runs. For orgs with Apex managed sharing and no registered recalculation class, a full recalculation silently destroys all Apex grants, producing a permanent access outage until manually remediated.
- **Security** — OWD changes and sharing rule modifications directly control record-level access. A failed or incomplete recalculation can leave records over-exposed (if a tightening job fails partway) or under-accessible (if Apex grants are dropped). The integrity of recalculation output must be verified, not assumed.

## Architectural Tradeoffs

**Deferral and consistency vs. speed:** Defer Sharing Calculations reduces the number of recalculation cycles, but while enabled it introduces access inconsistency — users may have stale access during the deferral window. Orgs must weigh the performance benefit of batching structural changes against the access-consistency risk during the window. For compliance-sensitive objects, deferral windows should be limited to true maintenance periods.

**Criteria-based rules vs. role/group-based rules:** Criteria-based sharing rules offer fine-grained access control based on field values, but they create a recalculation dependency on every DML operation that touches the criteria field. Role- and group-based rules are triggered only by infrequent membership changes, making them far more predictable in recalculation cost. Architects should prefer role/group-based rules at large data volumes and reserve criteria-based rules for fields that change rarely.

**Apex managed sharing flexibility vs. recalculation brittleness:** Custom Apex sharing reasons give architects full programmatic control over record access beyond what standard sharing supports. The cost is recalculation fragility — any full recalculation on the object destroys all Apex grants unless a registered batch recalculation class is maintained. This class becomes a critical production dependency that must be tested, deployed, and registered as part of every sharing model change.

## Anti-Patterns

1. **Applying multiple OWD changes one at a time during business hours** — Each individual OWD change triggers a separate full recalculation job. On objects with millions of records, N changes = N full recalculation cycles = N multi-hour background jobs. The correct pattern is to use Defer Sharing Calculations to collapse all changes into one job, run during a maintenance window.

2. **Deploying Apex managed sharing without a registered recalculation batch class** — This is the most common Apex sharing anti-pattern. The org runs for months without incident, then an admin makes a routine OWD adjustment or clicks "Recalculate" in Sharing Settings, and all Apex grants are silently deleted. Recovery requires manually executing the batch class. Prevention requires registering the class before any structural change.

3. **Writing criteria-based sharing rules on frequently-updated fields such as Status, Stage, or Rating** — These fields are often updated in bulk by integrations and batch jobs. Each mass update re-evaluates the criteria-based rule against all affected records, generating unpredictable background recalculation load. This anti-pattern is often invisible in development (low record volume) and only surfaces in production when bulk operations begin.

## Official Sources Used

- Salesforce Help — Recalculate Sharing Rules Manually: https://help.salesforce.com/s/articleView?id=sf.security_sharing_recalculate.htm&type=5
- Salesforce Help — Defer Sharing Rule Calculations: https://help.salesforce.com/s/articleView?id=sf.security_sharing_defer.htm&type=5
- Designing Record Access for Enterprise Scale (DRAES) Guide — Group Membership Operations: https://developer.salesforce.com/docs/atlas.en-us.draes.meta/draes/draes_group_membership.htm
- Salesforce Help — Minimize the Impact of Sharing Rule Recalculation: https://help.salesforce.com/s/articleView?id=sf.security_sharing_minimize_impact.htm&type=5
- Apex Developer Guide — Apex Managed Sharing: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_creating_with_apex.htm
