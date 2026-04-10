# Well-Architected Notes — Historical Order Migration

## Relevant Pillars

- **Reliability** — This skill is primarily a Reliability concern. A historical CPQ migration that loads records without following the Legacy Data Upload sequence produces a system that appears functional but silently fails at renewal time. Reliability requires that the migrated data produces correct, deterministic outcomes when CPQ processes act on it — specifically, that renewal quotes are generated with the correct products, quantities, and pricing. Any deviation from the prescribed load sequence or field requirements undermines this guarantee.

- **Operational Excellence** — The migration process itself must be operable: reversible in sandbox, documented for auditability, and validated before production execution. Disabling CPQ rules before load and re-enabling them afterward is an operational procedure that must be scripted and tracked, not performed ad hoc. Post-load validation queries are mandatory operational artifacts, not optional steps.

- **Performance** — The batch size 1 requirement has a direct performance impact: a migration of 10,000 subscriptions with batch size 1 takes substantially longer than a batch size 200 run. Teams must plan migration windows accordingly and not attempt to optimize batch size without understanding why the constraint exists.

- **Security** — Historical order data often contains pricing, discount, and revenue figures that are sensitive. The migration process requires temporary expansion of running-user permissions (to insert CPQ objects and update Contract Status) and may require disabling validation rules or triggers. These temporary permission expansions must be tracked and reversed after the migration. Profile or Permission Set audit logs should be reviewed post-migration.

- **Scalability** — For large historical loads (50,000+ subscriptions), batch size 1 combined with standard REST API inserts will approach or exceed API rate limits. Architecture must account for this: stagger loads across multiple days, use longer maintenance windows, or confirm with Salesforce that governor limit exceptions apply. The load plan must document the expected record volume and estimated API call consumption.

## Architectural Tradeoffs

**Batch size 1 vs. throughput:** The batch size 1 requirement for CPQ Legacy Data Upload directly conflicts with the performance optimization principle of maximizing batch size to reduce API call overhead. There is no supported workaround. Teams must choose between correctness (batch size 1, slower load) and speed (higher batch size, broken renewals). Correctness is non-negotiable for this use case.

**Legacy Data Upload vs. standard data load:** Using standard Bulk API 2.0 at default batch sizes is faster and simpler to configure, but produces subscription records that do not participate in CPQ's renewal engine. The CPQ Legacy Data Upload process is more operationally complex (rules bypass, batch size constraint, strict sequencing) but is the only approach that produces renewal-ready records. The architectural decision to use CPQ Legacy Data Upload is not optional for contract-based renewal orgs — it is required.

**Full reload vs. incremental patching:** If post-load validation reveals that subscriptions were loaded incorrectly (wrong pricing, wrong term dates), the correct remediation is to delete and reload the affected records using the correct Legacy Data Upload process — not to update records in place. In-place updates on CPQ Subscription records do not re-execute the renewal-preparation trigger logic. A delete-and-reload approach is architecturally more reliable even though it is more operationally costly.

## Anti-Patterns

1. **Loading CPQ objects via standard Bulk API at default batch size** — Bypasses CPQ's renewal-preparation package logic. Records appear correct in the database but produce blank or incorrect renewal quote lines. Cannot be detected by querying the records themselves; only surfaced when renewal quote generation fails. Correct approach: use batch size 1 for all CPQ Legacy Data Upload objects.

2. **Skipping the Quote and QuoteLine load steps** — Some teams attempt to load only Contracts and Subscriptions, skipping SBQQ__Quote__c and SBQQ__QuoteLine__c because the business "doesn't need the historical quote." Without the approved primary Quote linked to the Contract, CPQ's renewal engine cannot construct the renewal quote correctly even if the Subscription records are perfect. The Quote and QuoteLine records are structural anchors for CPQ's renewal process, not optional historical artifacts.

3. **Leaving CPQ price rules active during load** — Allows CPQ automation to overwrite historically correct pricing with current org pricing configuration. The overwrite is silent and the original prices cannot be recovered without re-running the source extraction. Correct approach: disable price and product rules in CPQ Package Settings before the first insert, document the disabled state, and re-enable only after post-load validation passes.

## Official Sources Used

- CPQ Legacy Data Upload — https://help.salesforce.com/s/articleView?id=sf.cpq_legacy_data_upload.htm&type=5
- Legacy Data Upload with Renewals and Amendments (KA-000384279) — https://help.salesforce.com/s/articleView?id=000384279&type=1
- SBQQ__Subscription__c Object Fields for Legacy Upload — https://help.salesforce.com/s/articleView?id=sf.cpq_subscription_fields.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Data Loader Guide — https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5
