# Well-Architected Notes — Payer vs Provider Architecture

## Relevant Pillars

- **Security** — Payer and provider data carry distinct HIPAA handling requirements. Insurance enrollment records (MemberPlan, ClaimHeader) and clinical records (ClinicalEncounter, HealthCondition) must not be accessible to users who have no need to see them. In dual-sector orgs, the primary security risk is cross-sector data exposure: a claims processor accessing a member's clinical diagnoses, or a nurse accessing insurance billing records. Object-level permissions, field-level security, and sharing rules must enforce sector boundaries. Minimum necessary access is a HIPAA requirement, not a design preference. The PSL matrix is both a licensing artifact and a security control — users should receive the minimum PSL set required for their role.

- **Scalability** — Health Cloud payer orgs managing large member populations (hundreds of thousands to millions of `MemberPlan` records, `ClaimLine` records, and `CoverageBenefitItem` records) must be designed for high record volume from the start. Relationship structures between `MemberPlan`, `PurchaserPlan`, and `CoverageBenefit` should be evaluated for query performance at scale. Provider orgs managing high-volume clinical encounters must design `ClinicalEncounter` rollup and reporting strategies that do not rely on cross-object formula fields or SOQL patterns that degrade under large record volumes. The choice of deployment type determines which scalability limits apply — payer and provider object models have different governor limit exposure profiles.

- **Reliability** — Misclassifying the deployment type produces an org that cannot serve its core business function reliably. A payer org built on provider objects will fail to support claims processing. A provider org activated with payer PSLs but no clinical data model will fail to support care delivery documentation. Architecture reliability in this domain begins with accurate deployment type classification and ends with a PSL matrix that is validated before go-live, not discovered to be incomplete after.

- **Operational Excellence** — The "provider" terminology ambiguity is a persistent operational risk. Without explicit documentation of what "provider" means in the context of a specific implementation, future administrators, developers, and implementation partners will make incorrect assumptions. Operational excellence in this domain requires that the architecture decision — deployment type, object model, PSL matrix, and provider term disambiguation — is captured in durable documentation that survives team turnover.

## Architectural Tradeoffs

**Single org (dual-sector) vs two orgs (one payer, one provider):**

A single dual-sector org provides a unified member/patient identity and eliminates the need for cross-org identity resolution integration. The cost is architectural complexity: dual PSL tracks, object-level permission separation, and a more complex security model to audit for HIPAA compliance. Two separate orgs reduce security model complexity and allow each org to be optimized for its sector, at the cost of integration overhead for shared identity and cross-sector reporting.

The correct choice depends on whether unified member/patient identity is a hard business requirement. If the IDN's care management processes require real-time correlation of insurance coverage with clinical data in a single UI context, the single-org dual-sector pattern is appropriate. If the payer and provider operations are organizationally separate with no cross-sector reporting requirement, two orgs with a shared identity integration is architecturally cleaner.

**Activating all Health Cloud features vs activating only sector-specific features:**

Activating all available Health Cloud features (payer objects, provider objects, FHIR settings, Utilization Management) in every Health Cloud org simplifies initial setup but creates long-term governance problems. Unused objects and features expand the attack surface, complicate permission set management, and mislead future administrators about what the org is supposed to do. The recommended pattern is to activate only the features that correspond to the classified deployment type and explicitly document what was intentionally excluded.

## Anti-Patterns

1. **Sector-agnostic Health Cloud setup** — Treating Health Cloud as a generic platform and activating all available objects and PSLs for all users, regardless of deployment type. This creates a mixed data model where payer and provider objects coexist without governance, cross-sector data exposure is structurally inevitable, and the HIPAA minimum necessary principle cannot be enforced. The Well-Architected remedy is deployment type classification before any setup decisions are made.

2. **PSL assignment based on object schema presence** — Assuming that because `MemberPlan` or `ClinicalEncounter` appears in the Object Manager, users can access it. PSL assignment is the actual control gate. Validating feature availability through Object Manager inspection rather than end-to-end PSL testing leaves critical feature gaps undiscovered until go-live. The Well-Architected remedy is a PSL validation checklist that must be executed with a real test user before UAT begins.

3. **Provider Relationship Management as a clinical provider directory** — Activating Provider Relationship Management in a clinical provider org to manage the hospital's provider directory or referring physician network. This is architecturally incorrect: Provider Relationship Management is a payer-side feature with insurance network semantics. Using it in a clinical context produces a provider directory that models insurance credentialing workflows instead of clinical affiliation relationships. The Well-Architected remedy is to design provider directories in clinical orgs using standard Account/Contact relationship models, not the payer-specific Provider Relationship Management feature set.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Health Cloud in the Payer Sector (Salesforce Help) — https://help.salesforce.com/s/articleView?id=ind.hc_payer_sector.htm
- Health Cloud Developer Guide: Clinical Data Model — https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/hco_object_reference_intro.htm
- Utilization Management in Health Cloud (Salesforce Help) — https://help.salesforce.com/s/articleView?id=ind.hc_utilization_management.htm
