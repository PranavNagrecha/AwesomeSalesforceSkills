# Well-Architected Notes — FSC Referral Management

## Relevant Pillars

- **Trusted** — Referral data contains PII (customer names, financial interest, contact details). Field-level security for the 11 referral custom fields must be explicitly configured per profile. Community profile access to `ReferrerScore__c` must be read-only; no community user should have edit access to the score field. `ReferredBy__c` lookups to Contact records for partner referrals introduce a data-access boundary: community users should only see referral records they submitted, not other partners' records. Sharing rules and Experience Cloud sharing settings must enforce this boundary.

- **Adaptable** — Referral types are registered via `ReferralRecordTypeMapping__mdt` custom metadata, which is deployable and versionable. This decouples referral type configuration from code and from manual setup, enabling new business lines to be added through a metadata deployment without org reconfiguration. Expressed Interest picklist values and Lead Assignment Rules provide a second layer of adaptable routing logic that does not require deployment.

- **Resilient** — Routing failures in FSC Referral Management are silent by default. A resilient implementation adds a scheduled report or monitoring query that detects referral Leads with no queue assignment after a threshold time window. Because the `ReferralRecordTypeMapping__mdt` gate is the primary failure point, any deployment that adds or modifies referral record types must include a post-deployment smoke test: create one test referral per new type and verify queue assignment via the Lead Assignment Log before going live.

- **Performance** — At high referral volumes, Lead Assignment Rule evaluation with many entries can add latency to Lead creation. Keep rule entries focused on `Expressed Interest` picklist values (indexed) rather than formula criteria where possible. Avoid complex formula criteria on the Lead Assignment Rule entries as they evaluate synchronously at record creation.

- **Operational Excellence** — The `ReferralRecordTypeMapping__mdt` registry, the Expressed Interest picklist values, and the Lead Assignment Rule entries form a three-part configuration dependency. All three must be kept in sync. A change in one without corresponding changes in the others causes routing gaps. Version control all three: deploy picklist and metadata changes together; document Assignment Rule entries in a routing matrix that can be reviewed during audits.

## Architectural Tradeoffs

**Metadata-driven routing vs. code-driven routing:** FSC Referral Management uses custom metadata + Lead Assignment Rules as the routing engine. This keeps routing configuration declarative and deployable, but it means routing logic is spread across two different setup areas (custom metadata and Assignment Rules) that must be maintained in sync. A code-based routing approach (Flow or Apex) would centralize logic but would not use the FSC-native routing pipeline, potentially missing platform behaviors.

**Contact-based vs. User-based referrer credit:** The platform decision to credit partner referrals to Contact records (not Users) aligns with the FSC data model where external partners are modeled as Contacts in a household or relationship group. However, it increases implementation complexity for community pages and reporting: queries and reports must handle both User and Contact as possible `ReferredBy__c` parent types. There is no configuration option to change this behavior; it must be accommodated in the design.

**Intelligent Need-Based Referrals vs. custom scoring:** The platform-provided Referrer Score is a black-box calculation based on historical conversion rates. Orgs needing custom scoring logic (e.g. weighted by referral value, recency, or product mix) must build a separate scoring mechanism and surface it via a custom field. Do not attempt to override `ReferrerScore__c` — it is read-only and will be overwritten by the platform.

## Anti-Patterns

1. **Building on Einstein Referral Scoring** — Configuring or documenting Einstein Referral Scoring as a current capability is an architectural anti-pattern because the feature is retiring. Any org that builds workflows, reports, or integrations dependent on Einstein Referral Scoring will face forced migration and potential data loss at the retirement date. Use Intelligent Need-Based Referrals as the scoring foundation and build reporting on `ReferrerScore__c`.

2. **Treating routing as only an Assignment Rule concern** — Designing routing logic solely in Lead Assignment Rules without managing `ReferralRecordTypeMapping__mdt` creates a fragile configuration where adding new referral types (a common ongoing business request) silently breaks routing. The correct pattern treats the metadata registry and the assignment rules as a single configuration unit that must be deployed and tested together.

3. **Assuming all referrers are Users** — Building SOQL queries, Flow logic, or page layouts that assume `ReferredBy__c` always resolves to a User will fail silently or produce null results for all partner-submitted referrals. Always handle both User and Contact as valid `ReferredBy__c` targets in any downstream logic.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Trailhead — Intelligent Referrals and Scoring with Financial Services Cloud — https://trailhead.salesforce.com/content/learn/modules/intelligent-referrals-and-scoring-with-financial-services-cloud
- Salesforce Help — Intelligent Need-Based Referrals and Scoring — https://help.salesforce.com/s/articleView?id=ind.fsc_referral_management_intelligent_referrals.htm
- Salesforce Help — Referral Scoring Feature for Financial Services Retirement Notice — https://help.salesforce.com/s/articleView?id=ind.fsc_referral_scoring_retirement.htm
