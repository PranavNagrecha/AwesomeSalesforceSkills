# Well-Architected Notes — Subscription Lifecycle Requirements

## Relevant Pillars

- **Reliability** — Subscription requirements that correctly reflect the CPQ ledger model prevent integration bugs and billing errors that are difficult to diagnose and expensive to remediate mid-contract. Requirements that assume in-place subscription edits produce unreliable contract history and broken renewal chains.

- **Operational Excellence** — Well-documented subscription lifecycle requirements enable repeatable, auditable contract change processes. When amendment pricing lock, co-termination rules, and proration methods are explicit in requirements, teams can consistently apply them across all amendments without case-by-case judgment calls.

- **Adaptability** — Subscription requirements must be written to accommodate the business's future amendment and renewal scenarios, not just the initial use case. Requirements that lock in one proration method or co-termination behavior without considering future product expansions or price changes reduce the ability to adapt the CPQ configuration later.

- **Security** — Subscription pricing and amendment records carry financial data. Requirements must include field-level security rules that prevent non-admin users from directly editing locked subscription pricing fields or end dates on activated contracts. Bypassing CPQ amendment processing via direct record edits is both a data integrity risk and a financial control risk.

## Architectural Tradeoffs

**Ledger model depth vs. query simplicity:** The CPQ additive ledger model provides a complete audit trail of all subscription changes, which is highly reliable for compliance and billing verification. The tradeoff is that entitlement queries require aggregation across multiple records. Teams can choose to maintain a rollup or summary object that flattens the ledger for reporting, but this introduces a synchronization risk (the rollup can lag behind the ledger). Requirements must decide which source of truth reporting systems read.

**Co-termination on vs. off:** Enabling co-termination simplifies billing (one renewal date per customer) and reduces amendment complexity, at the cost of potentially short prorated terms for new products added to contracts with imminent end dates. Disabling co-termination gives each line its own renewal date, which simplifies per-product pricing but creates complex multi-date renewal management. The right choice depends on the billing system's capability to handle multiple renewal dates per account.

**Automated contracted prices vs. manual maintenance:** Automatically creating `SBQQ__ContractedPrice__c` records on contract activation (via Apex trigger or Flow) ensures renewal quotes always reference contracted rates, but requires maintenance logic when products are discontinued or repriced. Manual contracted price management is simpler to implement but operationally fragile at scale.

## Anti-Patterns

1. **Writing requirements in "edit subscription" language** — Requirements that use language like "update the subscription record" or "modify the existing subscription" imply in-place edits that CPQ does not perform. This language leads development teams to implement direct DML updates that bypass CPQ's amendment engine, producing unreliable contract history and broken renewal downstream. All mid-term change requirements must be expressed in amendment terms (create delta record, prorate to co-termination date).

2. **Assuming pricing consistency across amendment and renewal** — Requirements that state "the price on the amendment should match the renewal price" will not hold in standard CPQ, where amendments lock to contracted price and renewals use list price. Documenting this asymmetry and its business implications is required before configuration begins.

3. **Leaving cancellation and credit requirements undefined** — CPQ creates negative delta subscription records when a product is removed in an amendment, but it does not generate credit memos or initiate refunds. Requirements that omit the credit and cancellation handling leave a gap between the CPQ output and the billing system's input. This gap is frequently discovered in UAT and causes scope creep.

## Official Sources Used

- CPQ Subscription Fields Reference — https://help.salesforce.com/s/articleView?id=sf.cpq_subscription_fields.htm
- Amend Your Contracts and Assets — https://help.salesforce.com/s/articleView?id=sf.cpq_amend_contracts_and_assets.htm
- Things to Know About Amendment and Renewal Services — https://help.salesforce.com/s/articleView?id=sf.cpq_amendment_renewal_services_notes.htm
- Subscription and Renewal Package Settings — https://help.salesforce.com/s/articleView?id=sf.cpq_subscription_renewal_settings.htm
- CPQ Amendment Fields and Settings — https://help.salesforce.com/s/articleView?id=sf.cpq_amendment_settings.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce CPQ Large-Scale Amendment and Renewal (KA-000384875) — https://help.salesforce.com/s/articleView?id=000384875
