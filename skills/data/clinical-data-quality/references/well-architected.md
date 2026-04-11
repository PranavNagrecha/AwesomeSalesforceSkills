# Well-Architected Notes — Clinical Data Quality

## Relevant Pillars

- **Reliability** — Patient record deduplication directly impacts care delivery reliability. Orphaned clinical records after an incorrect or incomplete merge mean care teams are working from an incomplete patient view. Pre-merge reassignment and post-merge audits are reliability controls that prevent silent data loss from reaching clinical workflows.
- **Security** — Patient identity is Protected Health Information (PHI) under HIPAA. Merging the wrong patient records, or leaving clinical records accessible under a deleted Account ID, creates PHI exposure and audit trail gaps. Duplicate Rule configuration, merge decision logging, and pre-merge validation are all security-layer controls in a Health Cloud deployment.
- **Operational Excellence** — The absence of a native MPI means deduplication is an ongoing operational process, not a one-time setup. Orgs need runbooks for merge decision review, bulk deduplication campaigns, and post-merge audit queries. Automating the pre-merge reassignment batch and standardizing the merge workflow reduces operator error.
- **Scalability** — Standard Duplicate Rules operate record-by-record at intake. At high data volume or with multi-source patient feeds, field-level fuzzy matching degrades in precision. Organizations that outgrow native rules need a third-party MPI capable of probabilistic matching and cross-system record linkage without imposing per-record API overhead on Salesforce DML.

## Architectural Tradeoffs

**Native Duplicate Rules vs. Third-Party MPI:**
Native Duplicate Rules are zero-cost, simple to configure, and sufficient for single-source low-volume orgs. They are limited to field-level comparison within Salesforce — no probabilistic scoring, no cross-system identity, no survivorship rules. A third-party MPI adds significant licensing and integration complexity but is the only viable path for enterprise healthcare organizations with multi-source patient data.

**Alert Mode vs. Block Mode on Duplicate Rules:**
Alert mode allows intake to proceed and surfaces the match for human review. Block mode prevents record creation. Block mode is safer for data integrity but can disrupt intake workflows if match quality is poor during initial rollout. The recommended approach is to launch in Alert mode, measure false-positive rate for 30–60 days, then switch to Block after match quality is validated.

**Pre-Merge Reassignment Batch vs. Post-Merge Recovery:**
Pre-merge reassignment is the only safe approach. Post-merge recovery of orphaned clinical records is not reliably possible through standard Salesforce APIs because the deleted Account ID cannot be queried against. Pre-merge adds a step to the merge workflow but eliminates the risk of permanent data loss entirely.

## Anti-Patterns

1. **Merging Person Accounts without a pre-merge clinical reassignment step** — Any merge workflow that executes the Account merge DML without first reassigning clinical records will silently orphan EpisodeOfCare, PatientMedication, ClinicalEncounter, and similar objects. Recovery is extremely difficult post-merge. This is the most common and highest-impact anti-pattern in Health Cloud deduplication.

2. **Treating Contact Duplicate Rules as equivalent to Person Account Duplicate Rules** — Person Accounts are deduplicated on the Account object. A Contact-scoped Duplicate Rule produces no alerts or blocks for Person Account patients. Teams that set up Contact-level deduplication and believe their patient intake is protected are exposed to duplicate patient creation.

3. **Assuming native Duplicate Rules constitute HIPAA-sufficient patient identity management** — Standard Duplicate Rules flag potential duplicates but do not log merge decisions, capture reviewer identity, or produce an audit trail. Healthcare organizations subject to HIPAA patient record integrity requirements need an additional audit logging layer on top of native deduplication tooling.

## Official Sources Used

- Salesforce Health Cloud Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_ref.meta/health_cloud_object_ref/hc_dev_guide.htm
- Salesforce Help — Duplicate Management Overview — https://help.salesforce.com/s/articleView?id=sf.duplicate_rules_overview.htm
- Salesforce Help — Merge Person Accounts — https://help.salesforce.com/s/articleView?id=sf.contacts_person_accounts_merge.htm
- Salesforce Help — Set Up Duplicate Rules — https://help.salesforce.com/s/articleView?id=sf.duplicate_rules_map_of_reference.htm
- Salesforce Object Reference — Account — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_account.htm
