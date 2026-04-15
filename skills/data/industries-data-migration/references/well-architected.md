# Well-Architected Notes — Industries Data Migration

## Relevant Pillars

- **Reliability** — The primary pillar for this skill. The multi-tier sequential load pattern is a reliability requirement: each tier must complete with zero errors before the next tier starts. A single failed intermediate tier leaves subsequent tiers with broken parent references. Recovery from a partial load can require deleting and reloading multiple dependent tiers, which is expensive and risky in a cutover window. Designing the load sequence with explicit gate checks and idempotent upsert operations makes the migration recoverable from any point of failure.

- **Performance** — Bulk API 2.0 is the mandated tool for volume loads. Using the SOAP API or Apex DML for large Industries object migrations causes governor limit failures and will not complete in any reasonable window. Within each tier, batch sizes should be tuned to avoid CPU timeout on heavy Industries triggers: 200–500 rows per batch is a safer starting point than the Bulk API 2.0 default of 10,000 for trigger-heavy objects.

- **Operational Excellence** — Load job tracking, explicit gate confirmation at each tier, and a pre-defined rollback procedure are operational requirements. A migration that cannot be restarted from a known good checkpoint is operationally brittle. Using upsert on external ID fields provides idempotency that makes checkpoint-restart possible without data duplication.

## Architectural Tradeoffs

**Sequential tier execution vs parallel load for speed:** Parallel loading of multiple object tiers simultaneously is faster but risks the case-sensitive external ID race condition and makes job failure recovery substantially more complex. The correct architecture accepts the slower sequential approach as a reliability tradeoff. The time saved by parallel loading is typically smaller than the time required to diagnose and recover from a partial parallel failure.

**External ID on every tier vs composite key resolution at load time:** Some ETL tools support dynamic parent ID resolution during load (reading the parent's Salesforce ID after the parent job completes and substituting it into the child file). This can work but introduces a runtime dependency on the ETL tool's ID resolution logic. External ID fields on every tier are the more portable and auditable approach — the load files are self-describing and can be re-submitted to any Salesforce org with the same field schema.

**Automation suppression scope:** Disabling automation at the org level is faster to configure but risks disrupting live users if the migration runs during business hours. Per-user bypass via a dedicated ETL integration user or a bypass flag is the safer scope, at the cost of requiring additional validation rule changes per object.

## Anti-Patterns

1. **Flat single-pass upsert anchored only on Account external ID** — Using Account as the only external ID anchor fails the moment any object below Account (InsurancePolicy, Premise, ServicePoint) needs to be referenced by a child object. Every intermediate object must have its own external ID field. A flat load that attempts to resolve InsurancePolicyCoverage parent lookups without InsurancePolicy external IDs will fail with field type errors on every coverage row.

2. **Starting a child-tier job before confirming parent-tier completion** — Bulk API 2.0 jobs process rows in parallel. A coverage row and its parent policy row submitted simultaneously cannot be guaranteed to commit in order. Starting InsurancePolicyCoverage before InsurancePolicy is confirmed complete produces a probabilistic mix of successes and failures depending on internal batch ordering. The only safe architecture is a confirmed gate between each tier.

3. **Treating Industries objects as generic sObjects** — InsurancePolicy, InsurancePolicyCoverage, Premise, and ServicePoint are not behave like custom objects or simple junction records. They carry platform-enforced referential integrity, domain-specific validation rules, and automation designed for transactional entry. A migration plan that ignores these constraints and treats the load as a generic CSV import will fail in production.

## Official Sources Used

- Insurance Policy Administration — Insurance Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.insurance_developer_guide.meta/insurance_developer_guide/insurance_policy_overview.htm
- Energy and Utilities Cloud Standard Objects — E&U Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.eu_developer_guide.meta/eu_developer_guide/eu_cloud_intro.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Object Reference: sObject Concepts — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
