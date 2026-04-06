# Well-Architected Notes — Territory Data Alignment

## Relevant Pillars

- **Operational Excellence** — Territory data alignment is an ongoing operational process, not a one-time setup. Well-designed alignment workflows are repeatable, auditable, and low-risk to execute: bulk loads use idempotent patterns, coverage gaps are measured before and after each operation, and manual associations are documented with rationale. Operational excellence failures show up as silent coverage drift, undetected gaps, and brittle migration scripts that cannot be safely re-run.

- **Reliability** — Territory data must be accurate for account access, opportunity territory assignment, and forecast rollup to function correctly. Reliability risks include duplicate associations that inflate counts, stale user memberships that affect forecast calculations, and non-Active model writes that fail silently if not pre-flight checked. The verification checklist in the skill's Recommended Workflow directly supports reliability.

- **Security** — `ObjectTerritory2Association` membership is a record access grant. Inserting an association grants the territory's members Read (or Read/Write, depending on territory settings) access to that account. This means bulk loads are implicitly a sharing event — incorrect bulk inserts create unauthorized data visibility. Security review should be part of any large-scale territory data operation, particularly for associations that cross business unit or data classification boundaries.

- **Scalability** — Coverage analysis SOQL patterns fail at scale if not designed for Bulk API 2.0 from the start. The NOT IN subquery pattern hits governor limits above ~50K rows in synchronous context. Migration scripts must externalize set comparisons for large account populations. The data model is scalable by design (ETM supports up to 1,000+ territories per model with a limit increase), but the tooling patterns must match the data volume.

## Architectural Tradeoffs

**Manual associations vs. rule-driven associations:** Manual associations are immediately effective and precise, but they are maintenance liabilities — they survive rule reruns and can silently diverge from intended coverage. Rule-driven associations are self-healing but require the account's field data to be accurate and the rule criteria to be comprehensive. The right tradeoff depends on the stability of the account population: stable named accounts warrant manual associations; dynamic account sets should be rule-driven.

**Inline Apex vs. Bulk API 2.0 for association management:** Apex triggers and DML can manage `ObjectTerritory2Association` rows programmatically, but they are subject to standard Apex governor limits (10K DML rows per transaction). For large-scale territory realignments (tens of thousands of accounts), Bulk API 2.0 is the correct tool — it processes in parallel, supports job-level retry, and does not consume Apex execution time.

**Single model transition vs. parallel model operation:** Salesforce only supports one Active territory model at a time. A "soft cutover" where both old and new models are accessible simultaneously is not possible. Migrations must be planned as a discrete activation event. This makes pre-activation validation (coverage gap analysis, association count parity checks) critical — there is no easy rollback once the old model is Archived.

## Anti-Patterns

1. **Deleting rule-driven associations without modifying the underlying rule** — Practitioners delete `ObjectTerritory2Association` rows to remove accounts from territories, but rule-driven rows are rebuilt on the next rule run. This creates an invisible cycle of deletion and recreation that masks the real problem (incorrect rule criteria or incorrect account field data). The correct fix is always upstream: fix the rule or the account data.

2. **Treating territory associations as a secondary concern during model migration** — Teams activate a new territory model, run rules, and assume the associations are correct without running a coverage gap analysis. In practice, new models frequently have rule gaps for accounts with unusual field values, recently created accounts, or accounts in edge-case geographies. A post-activation coverage gap audit is non-negotiable before communicating go-live.

3. **Ignoring stale UserTerritory2Association rows at user offboarding** — Inactive users left in territory memberships inflate headcount metrics, affect forecast calculations, and create confusion in territory management reports. This is not automatically remediated by user deactivation and requires an explicit cleanup step.

## Official Sources Used

- ObjectTerritory2Association Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_objectterritory2association.htm
- UserTerritory2Association Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_userterritory2association.htm
- Territory2ModelHistory Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_territory2modelhistory.htm
- Track Historical User Assignments (Territory Management) — https://help.salesforce.com/s/articleView?id=sf.tm2_track_historical_user_assignments.htm&type=5
- Salesforce Help: Setting Up and Managing Territory Assignments — https://help.salesforce.com/s/articleView?id=sf.tm2_set_up_manage_territory_assignments.htm&type=5
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
