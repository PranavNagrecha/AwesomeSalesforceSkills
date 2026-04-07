# Well-Architected Notes — Contract and Renewal Management

## Relevant Pillars

- **Reliability** — The contract lifecycle is highly stateful. A failed amendment or renewal that leaves the Contract and Subscription records in an inconsistent state is difficult to recover from without data correction. Reliable contract management requires transactional consistency: always use CPQ's built-in amendment and renewal flows rather than direct record edits. For large-scale amendments, use the async API path to prevent governor limit failures that leave the contract in a partial state.

- **Operational Excellence** — Amendment and renewal processes that are well-defined and repeatable reduce manual errors. Configure CPQ Settings (renewal term, co-termination behavior, auto-renewal) deliberately and document the choices. Build monitoring for async amendment jobs so failures surface immediately rather than silently. Include the amendment/renewal flow in end-to-end UAT for any CPQ deployment.

- **Performance** — Synchronous amendment processing has a practical ceiling of ~200 subscription lines before governor limits become a risk. Contracts at scale (enterprise accounts with hundreds of subscribed products) require the async `SBQQ.ContractManipulationAPI.amend()` path. Failing to plan for scale results in amendment failures during business-critical renewal events — a high-impact operational outage.

## Architectural Tradeoffs

**Auto-Renewal vs. Manual Renewal:** Auto-renewal (CPQ Setting) reduces process friction but removes the negotiation step. In B2B contexts with custom pricing, manual renewal is preferred because it allows the renewal quote to be reviewed and negotiated before the customer is committed. Auto-renewal is appropriate for consumer or SMB contexts where standard list pricing and fixed terms are the norm.

**Co-Termination: Earliest End Date vs. End of Term:** CPQ's default co-termination mode ("Earliest End Date") simplifies the contract by converging all lines to a single end date. This works well when contracts are expected to renew as a unit. However, for accounts with products on different lifecycle tracks (e.g., a 12-month support subscription and a 36-month platform license), co-termination can force premature renewal of long-term lines. In these cases, consider splitting products across separate contracts rather than co-terming them, or change the CPQ co-termination setting to "End of Term" (which appends lines rather than shortening them).

**Contracted Prices vs. Manual Renewal Negotiation:** Using `SBQQ__ContractedPrice__c` records to lock in renewal pricing is the cleanest architectural solution for accounts with negotiated rates. It is maintainable and auditable. The alternative — manually editing the renewal quote each cycle — is error-prone and does not scale. Establish a process to create contracted price records at the time of initial contract activation, not as a one-off fix at renewal time.

## Anti-Patterns

1. **Directly modifying SBQQ__Subscription__c records** — Editing subscription records outside the amendment flow corrupts the data model that CPQ relies on for renewal generation. The correct path is always an Amendment Quote, even for small corrections. Direct edits save time in the moment but create reconciliation work that is significantly more expensive.

2. **Cloning quotes to create renewals** — A cloned quote lacks the `SBQQ__RenewedContract__c` relationship on the associated Opportunity. This breaks contract history chaining, makes revenue reporting inaccurate, and can cause contracted price inheritance to fail on the next contract cycle. Always use the Renew button or set the lookup programmatically.

3. **Skipping monitoring for async amendments** — Assuming an async amendment succeeded because no immediate error appeared is a production risk. Async batch failures are silent from the user's perspective. Any org running large-scale amendments should have a monitoring process (Apex post-processing notification, scheduled job to check `AsyncApexJob` status, or Flow-based alert) to surface failures proactively.

## Official Sources Used

- Salesforce CPQ Contract Fields Reference — https://help.salesforce.com/s/articleView?id=sf.cpq_contract_fields.htm
- Amend Your Contracts and Assets (Salesforce CPQ) — https://help.salesforce.com/s/articleView?id=sf.cpq_amend_contracts.htm
- CPQ Amendment Fields and Settings — https://help.salesforce.com/s/articleView?id=sf.cpq_amendment_fields.htm
- Salesforce CPQ Large-Scale Amendment and Renewal (KA-000384875) — https://help.salesforce.com/s/articleView?id=000384875&type=1
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- SBQQ__Subscription__c Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_sbqq__subscription__c.htm
