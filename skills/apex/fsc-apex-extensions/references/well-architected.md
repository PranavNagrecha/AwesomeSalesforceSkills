# Well-Architected Notes — FSC Apex Extensions

## Relevant Pillars

- **Security** — Compliant Data Sharing is the FSC mechanism for enforcing field-level and record-level security in regulated financial environments. Bypassing CDS with manual Apex sharing breaks the security model even when the workaround succeeds technically. All sharing Apex must go through the CDS participant/role model to remain compliant with the security architecture.
- **Reliability** — The FSC rollup recalculation dependency is a reliability concern. If bulk loads are not followed by explicit `FinServ.RollupRecalculationBatchable` invocations, financial totals are silently incorrect. Household net worth figures used for reporting, advisor dashboards, and client portals will reflect stale or wrong values until the next recalculation. Reliability design must treat post-bulk-load recalculation as a required step, not an optional optimization.
- **Performance** — The managed package API version lock is a latent performance and stability risk. Running FSC Apex extension code at a newer API version than the package's compiled version can cause runtime type resolution failures that have no compile-time signal. Performance-aware deployments validate against a full-copy sandbox that matches production's exact package version.
- **Operational Excellence** — FSC trigger management through `FinServ__TriggerSettings__c` is a shared infrastructure resource. Custom code that disables FSC triggers and fails to re-enable them (missing finally block, uncaught exception path) breaks rollup and event behavior org-wide for all subsequent transactions in the same org. Operational excellence requires the try/finally pattern to be treated as non-negotiable for any code touching trigger settings.

## Architectural Tradeoffs

**Trigger co-existence vs. trigger consolidation.** The `FinServ__TriggerSettings__c` guard pattern enables custom triggers and FSC built-in triggers to coexist with selective disablement. The alternative — extracting all logic into a single consolidated trigger handler that fully replaces the FSC built-in — provides cleaner separation but requires reimplementing FSC rollup logic in custom code, which introduces a maintenance burden across every FSC release. The guard pattern is preferred unless the FSC trigger logic itself needs to be replaced (e.g., the FSC trigger has a known bug in the installed version).

**CDS participant model vs. permission sets for access control.** CDS provides fine-grained record-level sharing based on participant roles. Permission sets provide broader object-level access. For FSC financial records in regulated environments, CDS is the correct layer — it ensures access is driven by business relationships (advisor assigned to account) rather than static permissions. Custom Apex must not attempt to replicate CDS behavior with manual sharing, because the CDS engine will always win at recalculation time.

**Synchronous rollup vs. batch recalculation.** For transactional DML (single record updates from UI), FSC rollups fire synchronously in the trigger chain and are immediately consistent. For bulk DML, the batch path is the only option. Architects should document which data paths in the system are "bulk" and build the post-load recalculation step into those pipeline definitions explicitly rather than discovering the gap after go-live.

## Anti-Patterns

1. **Permanent FSC Trigger Disablement** — Setting `FinServ__TriggerSettings__c` flags to `false` at the org level (not within a transaction's try/finally) to avoid trigger conflicts is an anti-pattern. It disables FSC rollup and data integrity logic globally, silently degrading all subsequent transactions. The correct approach is per-transaction disablement scoped to the records being processed.

2. **Direct Share Record Manipulation on CDS Objects** — Writing Apex that inserts or deletes `AccountShare`/`FinancialAccountShare` records on CDS-governed objects gives a false sense of control. The CDS recalculation job treats these as orphans and removes them. This anti-pattern is particularly risky because the Apex insert succeeds, passing unit tests, but the share is removed in production on a schedule. All sharing changes must go through the participant model.

3. **Assuming Rollup Consistency After Bulk Load Without Verification** — Deploying bulk data integrations into FSC without a mandatory post-load rollup recalculation step, and without a validation query to spot-check household totals, leaves the system in a silently incorrect state. Rollup verification must be built into the migration runbook as a blocking gate, not an afterthought.

## Official Sources Used

- FSC Developer Guide (Apex Reference section) — rollup recalculation batchable invocation, trigger settings pattern, CDS participant model — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/fsc_apex_reference.htm
- FSC Admin Guide — Record Rollup Batch Jobs — recommended batch size, post-load recalculation requirement — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_record_rollups.htm
- Apex Developer Guide — transaction control, try/finally pattern, custom settings usage — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — `Database.executeBatch`, `FinServ` namespace classes — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — security and reliability pillar framing — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Compliant Data Sharing documentation — participant model, RowCause behavior, recalculation job — https://help.salesforce.com/s/articleView?id=sf.fsc_compliant_data_sharing.htm
