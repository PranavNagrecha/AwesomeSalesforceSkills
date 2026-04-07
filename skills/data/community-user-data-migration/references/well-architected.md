# Well-Architected Notes — Community User Data Migration

## Relevant Pillars

- **Security** — External user migration is a security-sensitive operation. Every migrated user inherits the permissions of their assigned Profile and the sharing model of the destination site. A misconfigured Profile-to-network association can silently grant or deny access to records. Stale NetworkMember records on decommissioned sites create residual access risks. Deactivated-but-not-cleaned users in the system remain security principals until fully removed.

- **Reliability** — Contact/Account pre-staging is a hard prerequisite. A migration that skips pre-validation of the ContactId join will produce partial results that are difficult to detect and error-prone to remediate. Idempotent staging — using External IDs for upserts rather than inserts — ensures reruns do not create duplicate records.

- **Operational Excellence** — A documented, repeatable runbook with explicit pre-flight checks, per-batch error log review, and post-migration validation SOQL reduces the risk of silent failure. License seat management — accounting for the deactivation lag before activating new cohorts — must be part of the operational plan, not an afterthought.

## Architectural Tradeoffs

**Data Loader vs. Apex-based batch migration:**
Data Loader is the appropriate tool for large-volume external user migration because it processes records outside governor limits and produces a per-row error log. Apex Batch is an option for smaller volumes or when complex pre-processing logic is required, but it reintroduces DML governor limit risk (150 DML statements per transaction) and error handling complexity. For migrations above ~200 users, Data Loader or Bulk API 2.0 is the recommended approach.

**In-org license migration vs. new user creation:**
When migrating between license types within the same org, updating the existing User's ProfileId is preferable to deactivating and re-creating the user. Re-creation severs the user's relationship to their owned records, open cases, and activity history. Profile update preserves all relationships while changing the license and site access.

**Staged migration vs. cutover migration:**
Staged migration (migrating users in cohorts with parallel access to old and new sites) reduces risk but requires NetworkMember cleanup across both sites during the transition. Cutover migration (all users in one window) is operationally simpler but requires a longer maintenance window and careful license seat planning.

## Anti-Patterns

1. **Migrating Users without pre-validating the Contact hierarchy** — Skipping the Contact pre-staging validation step causes mass Data Loader failures that are difficult to diagnose. Every external User insert must be preceded by a confirmed Contact upsert with row count validation. This is not optional even when the source system implies a Contact relationship.

2. **Assuming NetworkMember records clean themselves** — Post-migration NetworkMember cleanup for the old network is a required manual step. Treating it as optional leaves users with stale site memberships, inflated license counts on decommissioned sites, and potential access to records they should no longer see. Include explicit NetworkMember cleanup SOQL in every migration runbook.

3. **Planning license seat availability without accounting for deactivation lag** — Deactivating Users does not immediately free license seats. Migration windows that depend on freed seats being available immediately will hit license limit errors on User insert. Always build buffer time or request a temporary license overage from Salesforce Support.

## Official Sources Used

- Salesforce Help — Migrate Community Users Between Licenses — behavioral authority for license migration via Profile update
- Salesforce Help — Import Customer Portal Users — Data Loader field requirements for external user bulk insert
- Salesforce Help — Update Experience Cloud Site Membership Using API — NetworkMember record management and API-based membership updates
- Object Reference — sObject Concepts — User object, NetworkMember object, field semantics and constraints
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Data Loader Guide — https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
