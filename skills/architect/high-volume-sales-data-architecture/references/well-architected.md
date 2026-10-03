# Well-Architected Notes — High Volume Sales Data Architecture

## Relevant Pillars

- **Performance** — This is the primary pillar. High-volume sales data architecture is fundamentally about keeping query response times, report load times, and batch processing durations within acceptable thresholds as record counts grow. Every recommendation in this skill (indexes, skinny tables, selective filters, archival) targets the Performance pillar directly. The Salesforce Well-Architected Performance guidance explicitly calls out query optimization and data lifecycle management as key practices.

- **Scalability**: Well-Architected (Trusted > Reliable, Data Volume) names the structural levers: distribute child records and ownership below 10,000 per parent or owner, reduce record data through archiving and purging (Bulk API 2.0 hard delete), aggregation objects populated by batch Apex, and data tiering. It classes custom indexes and skinny tables as short-term workarounds that can add technical debt. Sales data grows continuously as pipeline activity increases. Architecture decisions made at 500K Opportunities must hold at 5M. Scalability in this context means choosing patterns (Big Object archival, ownership distribution, index-backed queries) that degrade gracefully rather than cliff at volume thresholds. Skinny tables and custom indexes are scaling mechanisms that maintain constant-time query behavior as tables grow.

- **Reliability** — Data skew and non-selective queries do not just slow the org down; they cause lock contention failures, sharing recalculation timeouts, and silently truncated report results. A reliability lens means preventing these failure modes proactively through ownership caps, selective query enforcement, and validated archival pipelines. An unreliable pipeline report that shows $2M when the real number is $8M is a business-critical data integrity problem.

- **Security** — Sharing model performance is a security concern. When sharing recalculation is too slow, administrators defer sharing rule changes, leaving overly permissive access in place. Proper ownership distribution ensures that sharing rules can be updated promptly, keeping record visibility aligned with the intended security model.

- **Operational Excellence** — Monitoring ownership distribution, index health, and record growth rates requires operational discipline. Post-refresh index verification, quarterly skew audits, and archival batch monitoring are operational practices that keep the architecture healthy over time.

## Architectural Tradeoffs

1. **Active query performance vs. historical data availability.** Archiving to Big Objects improves active table query speed but makes historical data harder to access (Async SOQL only). The summary custom object pattern mitigates this but adds maintenance cost.

2. **Ownership simplicity vs. sharing performance.** Centralizing ownership to a single user simplifies permission logic but creates catastrophic sharing recalculation costs. Distributing ownership adds complexity to assignment rules but keeps sharing performant.

3. **Custom index maintenance vs. query flexibility.** Custom indexes lock the org into specific query patterns. If business requirements change and new filter fields emerge, new index requests are needed. Over-indexing is not possible (Salesforce controls this), but under-indexing means new reports require Support cases with turnaround time.

4. **Skinny table column selection vs. report evolution.** Skinny tables are fixed column subsets. Adding a column requires a new Support request. If report requirements change frequently, the skinny table benefit is offset by the maintenance cycle.

## Anti-Patterns

1. **Treating all data volume problems as storage problems** — Buying more storage or deleting unrelated records does not fix query selectivity or sharing recalculation performance. The correct response to a slow query is index analysis, not storage cleanup.

2. **Deferring archival until storage runs out** — By the time storage is full, the Opportunity table has degraded query performance for months or years. Archival should be triggered by performance thresholds (query times, report load times) not storage utilization percentages.

3. **Adding sharing rules to compensate for poor ownership distribution** — When records are concentrated under one owner, administrators sometimes add more sharing rules to grant access to other teams. Each new sharing rule increases recalculation cost on the skewed owner's record set, compounding the original problem.

## Official Sources Used

Read for this revision (2026-10-03):

- Best Practices for Deployments with Large Data Volumes (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_large_data_volumes_bp.pdf. Tiered index thresholds; custom index creation paths and sandbox copy; External IDs; null rows; skinny tables (objects, field types, encrypted data, 200 columns, sandbox copy); defer sharing calculation; Best Practices > General (10,000 owned records; 10,000 children per parent).
- Big Objects Implementation Guide, Version 66.0 (Spring '26): local corpus `knowledge/imports/salesforce-big-objects-guide.md`. Behavioral constraints (object and field permissions only; no triggers or flows; idempotent writes); API support (SOQL, Bulk, Chatter, SOAP; no REST); no encryption; 100 big objects per org; aggregate queries via batch Apex; `insertImmediate()` returns SaveResults; reporting through an extracted custom object.
- SOQL and SOSL Reference, Version 66.0: local corpus `knowledge/imports/salesforce-soql-sosl.md`. Big object query rules (index order, operators allowed on the last field, unsupported operators).
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. CustomIndex type (API 50.0+, `allowNullValues`, contact Support).
- Salesforce Data Loader Guide (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf. The assignment rule setting applies to cases and leads and overrides CSV Owner values.
- Salesforce Well-Architected: Trusted > Reliable: https://architect.salesforce.com/docs/architect/well-architected/guide/reliable.html (a direct fetch does not return the guide page; read via Wayback snapshot 2026-06-13). Data Volume levers, ownership skew across users, queues, roles, and groups, and custom indexes and skinny tables as short-term workarounds.

Listed in the original version and not re-read (the atlas page returns a script shell without content; the Architects path was not opened); no claim in this revision rests on them alone:

- Salesforce Large Data Volumes Best Practices (atlas HTML): https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_introduction.htm (same content read from the PDF above)
- Salesforce Well-Architected: Performance — https://architect.salesforce.com/well-architected/easy/performance
