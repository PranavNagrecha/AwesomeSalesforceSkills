# Well-Architected Alignment — limits-and-scalability-planning

## Pillar: Scalability

Governor limits are the primary mechanism Salesforce uses to enforce scalability on a multi-tenant platform. A well-architected org treats limits not as obstacles but as design constraints that force good architecture decisions: bulkification, async offloading, selective queries, and data ownership distribution.

**Scalability patterns this skill enforces:**
- Batch Apex for large data set operations — limits force chunking, which is inherently scalable.
- SOQL selectivity — queries that use indexed filters scale with data volume; full table scans do not.
- Async offloading — moving non-user-facing work out of synchronous transactions allows the user experience to scale independently of back-end processing time.
- Org metadata headroom management — staying below 80% of metadata limits ensures the org can accommodate future growth without a governance emergency.

**Anti-patterns this skill catches:**
- SOQL inside loops — does not scale; O(n) queries cause limit failure at moderate record volumes.
- DML inside loops — same problem; fails when the loop body repeats more than 150 times.
- Hard-coded selectivity assumptions — queries that are selective at 10,000 records become non-selective at 1,000,000 records; design for projected volume, not current volume.

---

## Pillar: Performance

Governor limits intersect directly with user-perceived performance. A transaction that consumes 9,500ms of CPU is 9.5 seconds of wait time for the user before the page responds. A non-selective SOQL query on a large object can take 10–60 seconds and time out before returning results.

**Performance guidance this skill provides:**
- Skinny table consideration for objects > 5M records — reduces query I/O significantly for frequently queried field subsets.
- Data skew identification — sharing recalculation delays that manifest as slow record saves are caused by skewed ownership, not code bugs.
- Heap reduction strategies — reducing SELECT field lists and chunking data processing reduces peak heap and avoids the GC overhead that inflates CPU time.

---

## Pillar: Reliability

Limit violations cause immediate transaction failures with no graceful degradation. A production `LimitException` means the user action failed, the record was not saved, and the integration message was not delivered. Reliability in a Salesforce context means designing ahead of limit risk so that failures are caught in testing rather than production.

**Reliability practices this skill mandates:**
- Full-volume sandbox testing — limit risks that are invisible at 1,000 records become failures at 1,000,000. Test in a sandbox seeded with production-scale data.
- Debug log checkpoints — `System.debug(Limits.getQueries())` instrumentation in high-risk transactions gives early warning before limits are reached.
- Batch job queue planning — ensuring the 5-job limit is not saturated during peak periods prevents jobs from failing to start.
- Platform event monitoring — tracking delivery consumption against the 250,000/24hr ceiling prevents silent event drops that create data inconsistency.

---

## Pillar: Operational Excellence

Scalability planning is an ongoing operational practice, not a one-time design activity. Limits change across Salesforce releases, data volumes grow, new packages add resource consumption, and new teams add automation without awareness of existing overhead.

**Operational practices this skill recommends:**
- Regular storage audits (quarterly minimum) using Setup > Storage Usage.
- Metadata limit reviews before each major release — custom object and field headroom as part of the release checklist.
- Apex Jobs monitoring for batch queue saturation during peak business periods.
- Governance policies for new custom object and new custom field requests above threshold counts.
- Limit consumption documentation in deployment runbooks for batch-heavy releases.

---

## Official Sources Used

- Salesforce Apex Developer Guide: Apex Governor Limits — transaction and async limit values, heap and CPU specifications
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm

- Salesforce Help: General Limits — org-wide limits for custom objects, fields, flows, tabs, storage
  https://help.salesforce.com/s/articleView?id=sf.limits_general.htm

- Salesforce Apex Developer Guide: Batch Apex — batch interface contract, scope size, 50M record limit, queue behavior
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm

- Salesforce Help: Platform Events Considerations — delivery limits, message size, replay window
  https://help.salesforce.com/s/articleView?id=sf.platform_events_considerations.htm

- Salesforce Well-Architected Overview — quality model framing for Scalability, Performance, Reliability, and Operational Excellence pillars
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
