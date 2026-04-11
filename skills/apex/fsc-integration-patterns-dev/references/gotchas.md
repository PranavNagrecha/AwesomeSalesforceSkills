# Gotchas — FSC Integration Patterns Dev

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Rollup-by-Lookup Row Locks During Parallel Bulk Loads

**What happens:** Bulk API 2.0 processes FinancialHolding records in parallel server-side batches. When Rollup-by-Lookup is enabled, each FinancialHolding write acquires a row lock on the parent FinancialAccount to update the rollup. Multiple parallel batches loading holdings under the same parent account contend for the same row lock. The losing batches receive `UNABLE_TO_LOCK_ROW` errors and those records fail. In high-volume loads (50,000+ records), this can cause 20–40% record failure rates.

**When it occurs:** Any Bulk API ingest job against `FinancialHolding` or `FinancialAccount` where:
- Rollup-by-Lookup is enabled in Wealth Management Custom Settings for the integration user, AND
- Multiple holdings share the same parent FinancialAccount, AND
- The job processes more than one batch concurrently (default Bulk API behavior).

**How to avoid:** Disable RBL for the integration user in Wealth Management Custom Settings before the bulk load begins. After the load reaches `JobComplete`, use Data Processing Engine to recalculate all household and account-level rollups in a single controlled batch. Do not re-enable RBL between batch chunks or mid-job — doing so reintroduces the contention.

---

## Gotcha 2: Callout-After-DML Exception on FinancialHolding Trigger Paths

**What happens:** Apex enforces a hard rule: once DML has been issued in a transaction, no HTTP callouts may follow. Triggers on FinancialHolding fire after DML on those records, making any subsequent `Http.send()` call illegal. The exception `System.CalloutException: You have uncommitted work pending` is thrown at runtime — not at compile time — so this bug is invisible in unit tests that mock HTTP callouts.

**When it occurs:** Any `after insert`, `after update`, or `after upsert` trigger (or a Flow invoked from one) that attempts to call an external REST endpoint — market data vendor, custodian API, payment processor — after the triggering DML has already occurred.

**How to avoid:** Never place callouts in trigger contexts on FSC financial objects. Move all outbound callout logic to a `Batchable` class marked with `Database.AllowsCallouts`, a `Queueable` that implements `Database.AllowsCallouts`, or an invocable action that runs in a separate transaction invoked from a Platform Event trigger. The Platform Event trigger fires in a new transaction context where no prior DML has occurred.

---

## Gotcha 3: Namespace Mismatch Between Managed-Package and Core FSC

**What happens:** FSC was released in two different deployment architectures. Orgs that implemented FSC before Winter '23 typically use the managed-package deployment with the `FinServ__` namespace — objects are `FinServ__FinancialAccount__c`, `FinServ__FinancialHolding__c`, fields use `FinServ__` prefixes. Orgs on Core FSC (post-Winter '23 standard) use standard object names with no namespace. Integration code written for one fails with `System.QueryException: sObject type 'FinancialAccount' is not supported` or its inverse when deployed to the other.

**When it occurs:** When integration Apex, SOQL queries, or metadata-driven mappings are copied between org types without adjusting the namespace. Also occurs when the integration platform (MuleSoft, Informatica) uses hardcoded object names from a template built for the other FSC variant.

**How to avoid:** At the start of every integration engagement, confirm the FSC deployment type by querying `SELECT Id FROM FinancialAccount LIMIT 1` (Core FSC) and checking for error vs `SELECT Id FROM FinServ__FinancialAccount__c LIMIT 1` (managed-package). Parameterize all object and field API names in integration configuration. Never hardcode a single namespace assumption in shared code.

---

## Gotcha 4: Bulk API Open Job Concurrency Limit Blocks Nightly Reconciliation

**What happens:** Salesforce enforces a limit of 10 open (processing or queued) Bulk API 2.0 jobs per org at any time. Large reconciliation pipelines that split a nightly load into many parallel sub-jobs to maximize throughput can hit this ceiling. New job creation calls return HTTP 400 with `TooManyBatchRequests`. Jobs submitted while the queue is full are rejected entirely — they are not queued for later processing.

**When it occurs:** Nightly reconciliation pipelines that fan out into more than 10 concurrent Bulk API jobs. This is common when a MuleSoft flow creates one job per account segment (e.g., one job per asset class or custodian) and multiple segments run simultaneously.

**How to avoid:** Design the pipeline to maintain a job pool of no more than 8 concurrent open jobs (leaving headroom for ad-hoc admin operations). Poll job status and only submit the next job when the previous one reaches `JobComplete` or `Failed`. Monitor org-level Bulk API usage metrics in the Setup > Bulk Data Load Jobs view.

---

## Gotcha 5: CDC Replay Gaps When Integration Consumer Falls Behind

**What happens:** Salesforce Change Data Capture retains change events for 72 hours in the event bus. If a CDC consumer (e.g., a MuleSoft flow subscribing to `FinancialAccountChangeEvent`) falls behind by more than 72 hours — due to a system outage or maintenance window — events from before the replay window are permanently lost. The consumer cannot recover missed changes by replaying from an older position.

**When it occurs:** Any unplanned CDC consumer downtime exceeding 72 hours. Also occurs if the consumer's stored replay ID becomes invalid (e.g., stored in an external system that was reset).

**How to avoid:** CDC is not a replacement for a reliable batch reconciliation process. Always maintain an independent nightly Bulk API reconciliation job as a backstop. CDC handles incremental replication of Salesforce-side changes; the nightly batch ensures full position accuracy regardless of CDC health. Monitor CDC consumer lag via the Event Bus Monitoring dashboard in Setup.
