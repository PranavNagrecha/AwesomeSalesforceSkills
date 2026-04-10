# Well-Architected Notes — Subscription Management Architecture

## Relevant Pillars

### Reliability

Subscription management architecture is most directly a Reliability concern. The CPQ ledger model (amendments as immutable delta records) is itself a reliability pattern — it avoids in-place mutation of financial records, which prevents data loss from failed partial updates. Architects must preserve this property by ensuring no custom code, Flow, or integration directly modifies existing `SBQQ__Subscription__c` records post-activation.

Reliability risks in this domain:
- Custom triggers that update existing subscription records in response to amendment events, silently corrupting the ledger.
- Async amendment jobs that complete with errors but are not monitored, leaving contracts in a partially-amended state.
- Billing schedule generation racing with async amendment completion, producing billing records against stale subscription data.

Reliability design principles to apply:
- Treat `SBQQ__Subscription__c` records as append-only. Add guards against update DML on activated subscription records.
- Implement `AsyncApexJob` monitoring with alerting on `Status = 'Failed'` for `SBQQ.AmendmentBatchJob`.
- Use a completion gate (platform event or scheduled poll) before triggering billing activation after async amendments.

### Performance

Performance is the primary driver of the Legacy vs Large-Scale amendment mode decision. CPQ's synchronous amendment processing is bounded by Apex governor limits: 10,000 ms CPU time and SOQL row limits. These limits are reached at approximately 200–1,000 subscription lines depending on trigger and integration complexity on the org.

Performance design principles:
- Evaluate subscription line count projections for the next 3 years, not just current state. An org with 150 lines today that adds 100 lines per quarter needs Large-Scale mode within 18 months.
- Reduce trigger complexity on `SBQQ__Subscription__c` to extend the practical ceiling for synchronous processing.
- In Large-Scale mode, batch chunk size (default 200) can be tuned but requires CPQ support involvement.

### Operational Excellence

The co-termination anchor immutability rule and the renewal automation configuration are operational excellence concerns. Subscription lifecycle state must be predictable and auditable. Fields that drive proration must be treated as write-once to maintain the auditability of billing calculations.

Operational excellence design principles:
- Document the amendment service mode, date field mapping (Legacy: Quote start date; Large-Scale: Contract amendment start date), and co-termination anchor in a solution design document.
- Implement validation rules preventing edits to `SBQQ__SubscriptionStartDate__c` and `SBQQ__CoTerminationDate__c` after contract activation.
- Log all async amendment job outcomes to a custom object or external monitoring system for auditability.
- Standardize renewal automation settings (`SBQQ__RenewalForecast__c`, `SBQQ__RenewalQuoted__c`) at the CPQ Settings level so Contract-level overrides are exceptions, not the norm.

### Security

Security is a secondary concern in this domain but relevant at the data access layer. Subscription records contain pricing and commercial terms that must be restricted to appropriate internal users.

Security design principles:
- Use Object-Level Security (OLS) and Field-Level Security (FLS) on `SBQQ__Subscription__c` to prevent end users from reading or editing contracted prices directly.
- Restrict the "Allow Price Override" permission on subscription products to avoid unauthorized price changes outside the approved swap pattern.
- Audit sharing rules on Contract and `SBQQ__Subscription__c` to ensure external community users (if any) cannot access subscription pricing data.

---

## Architectural Tradeoffs

### Synchronous vs Asynchronous Amendment Processing

**Tradeoff:** Legacy synchronous mode is simpler to implement, monitor, and debug. Large-Scale async mode is required at scale but introduces eventual consistency: the amendment quote is not immediately available, billing cannot be triggered until the job completes, and error handling requires async monitoring patterns.

**Recommendation:** Default to Legacy mode for new implementations. Design async monitoring infrastructure (job status polling, platform events) upfront so the switch to Large-Scale mode at higher volume is an operational change rather than a development project.

### Ledger Integrity vs Reporting Simplicity

**Tradeoff:** The CPQ ledger model produces accurate amendment history but makes reporting and integration queries more complex. "Combine Subscription Quantities" simplifies the data model but breaks bundle architecture and eliminates amendment audit trail at the subscription record level.

**Recommendation:** Preserve the ledger model. Build reporting and integration aggregations that sum delta records. Do not enable Combine Subscription Quantities on orgs with bundle products or audit requirements.

### Auto-Renewal vs Deferred Renewal Quote

**Tradeoff:** Full auto-renewal (`RenewalForecast=true`, `RenewalQuoted=true`) creates a pipeline-visible renewal Opportunity and Quote immediately on contract activation. This maximizes automation but locks pricing at list and requires AE overrides for every negotiated account. Deferred renewal (`RenewalQuoted=false`) adds a manual step but prevents incorrect price anchors.

**Recommendation:** Use deferred renewal for enterprise accounts with negotiated pricing. Use full auto-renewal only for volume/SMB segments where list price renewals are standard.

---

## Anti-Patterns

1. **Direct mutation of SBQQ__Subscription__c records** — Writing to existing subscription records from custom Apex, Flow, or a data loader violates the CPQ ledger model. The mutation is overwritten by the next amendment, the change is invisible to CPQ's pricing engine, and billing integration produces incorrect schedules. The correct pattern is always to initiate an amendment quote through CPQ's API, never to write directly to subscription records.

2. **Enabling both Preserve Bundle Structure and Combine Subscription Quantities** — This creates a silent configuration conflict with no error feedback. The safer architectural rule is to treat these as mutually exclusive and add a custom validation or monitoring job to alert if both are ever enabled simultaneously.

3. **Treating renewal quote generation as a fire-and-forget automation** — Auto-generated renewal quotes reprice at list. Sending them to customers without a review step exposes negotiated accounts to unexpected price increases. The correct pattern is to include a "review and approve renewal quote" step in every renewal workflow, whether the quote is auto-generated or manually initiated.

---

## Official Sources Used

- Amend Your Contracts and Assets — Salesforce CPQ: https://help.salesforce.com/s/articleView?id=sf.cpq_amend_contracts.htm
- CPQ Amendment Fields and Settings: https://help.salesforce.com/s/articleView?id=sf.cpq_amendment_settings.htm
- Subscription and Renewal Package Settings: https://help.salesforce.com/s/articleView?id=sf.cpq_subscription_renewal_settings.htm
- Salesforce CPQ Large-Scale Amendment and Renewal (KA-000384875): https://help.salesforce.com/s/articleView?id=000384875
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
