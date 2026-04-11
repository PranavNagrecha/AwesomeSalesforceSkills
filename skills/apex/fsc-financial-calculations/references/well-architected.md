# Well-Architected Notes — FSC Financial Calculations

## Relevant Pillars

- **Reliability** — The most critical pillar for this skill. Financial aggregation must produce correct, consistent results across bulk loads, nightly batch runs, and concurrent API writes. The disable/re-enable trigger pattern and the `RollupRecalculationBatchable` post-load step exist specifically to maintain data integrity under real-world operational conditions. A failure here directly produces incorrect client-facing financial data.

- **Performance** — Bulk data loads and nightly performance metric batches must be scoped and designed to stay within Apex governor limits. Poorly scoped batches (too large a chunk size, SOQL inside loops, uncontrolled `Database.Stateful` accumulation) cause timeouts, partial completion, and stale aggregates — all of which impact report latency and system throughput.

- **Security** — The `WealthAppConfig__c` custom setting disable/re-enable pattern should be limited to integration API users with a specific permission set. Granting this capability broadly could allow unintended suppression of rollup integrity checks. Custom Apex batch classes should run `with sharing` unless a documented business case justifies elevated access. Any custom performance metric object should respect record-level sharing rules consistent with client data sensitivity.

- **Scalability** — RBL triggers scale well for single-record or low-volume DML but degrade significantly past a few hundred concurrent parent records. DPE and custom Apex batches are the scalable paths. Design decisions (trigger vs. DPE vs. batch) must account for projected data volume at 3–5 years of growth, not just current load.

- **Operational Excellence** — Recalculation batch jobs must have monitoring, logging, and alerting. A batch that silently fails after a bulk load leaves rollup totals stale with no indication to operations. Implement `finish()` logging, email alerts on batch failure, and a monitoring dashboard that compares expected vs. actual rollup recalculation frequency.

---

## Architectural Tradeoffs

**Synchronous triggers vs. asynchronous batch:** Native FSC RBL triggers give real-time aggregate consistency but create contention at bulk scale. Switching to DPE or batch sacrifices real-time accuracy for throughput. For wealth management use cases where household balance is displayed in real time on advisor dashboards, this tradeoff must be explicit in the design. If real-time accuracy is required, keep RBL triggers active and implement the bulk-load safety protocol. If batch-mode accuracy (next-day totals) is acceptable, DPE is the better long-term path.

**Single DPE recipe vs. multiple targeted recipes:** One comprehensive DPE recipe that aggregates all financial object types is simpler to monitor and schedule, but harder to extend and debug. Multiple targeted recipes are easier to maintain in isolation but create scheduling complexity and lock-contention risk if they share target fields. For orgs with complex financial data models, a single recipe with clearly named transformation stages is preferred.

**Custom Apex batch vs. Flow/DPE for performance metrics:** Custom Apex batch is the only viable mechanism for iterative multi-step calculations like IRR (which requires Newton-Raphson or similar iteration). DPE does not support conditional iteration loops. Flow is unsuitable for bulk financial computation. Document this constraint early to prevent scope creep toward declarative-only approaches.

---

## Anti-Patterns

1. **Leaving RBL triggers enabled during bulk loads** — This is the leading cause of data integrity failures in FSC migrations. The row-lock errors cause silent partial rollbacks that result in some households showing incorrect balances. The correct pattern is always: disable triggers, load, re-enable, run recalculation batch.

2. **Using the RBL-to-DPE auto-conversion wizard and scheduling all generated definitions** — The wizard generates valid individual definitions, but running them concurrently against the same target records replicates the lock contention problem. DPE recipes for FSC should be designed holistically, not mechanically converted from RBL.

3. **Treating `FinServ.RollupRecalculationBatchable` as a catch-all recalculation tool** — This batch covers only FSC-native objects. Custom objects, external custodian feeds, and performance metric fields require separate, explicitly designed recalculation paths. Assuming the FSC-native batch covers everything leaves custom financial data permanently stale after migrations or corrections.

---

## Official Sources Used

- FSC Developer Guide (Spring '26) — RBL trigger behavior, `FinServ.RollupRecalculationBatchable`, Wealth Application Config custom setting
  https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/fsc_dev_guide.htm

- Apex Developer Guide — Batchable interface, `Database.Stateful`, governor limits, scheduled Apex
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm

- Apex Reference Guide — `Database.Batchable`, `Database.BatchableContext`, `System.scheduleBatch`
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm

- Salesforce Well-Architected Overview — Reliability and Performance pillar framing for bulk processing and data integrity
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- Salesforce Trailhead — Summarize Financial Data in FSC — rollup configuration, RBL overview, recalculation batch
  https://trailhead.salesforce.com/content/learn/modules/fsc-rollup
