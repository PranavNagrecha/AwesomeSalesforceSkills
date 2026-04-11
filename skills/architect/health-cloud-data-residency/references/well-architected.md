# Well-Architected Notes — Health Cloud Data Residency

## Relevant Pillars

- **Security** — Data residency is fundamentally a security and compliance concern. PHI stored or processed outside the contractually and legally required boundary is a security failure with regulatory consequences. Applying Salesforce Shield Platform Encryption to sensitive Health Cloud fields, scoping HIPAA BAA coverage correctly, and controlling PHI access to non-BAA-covered features are direct Security pillar responsibilities. The Security pillar's principle of defense-in-depth applies: regional selection is the first control layer; BAA coverage, field-level encryption, and Data Mask configuration are additional layers.

- **Reliability** — Hyperforce regional selection affects not only data residency but also disaster recovery and backup behavior. Architects must understand that Hyperforce DR replication may involve cross-region data movement, and this must be considered alongside data residency requirements. For AU orgs subject to My Health Records Act, the cross-border restriction applies to DR replication as well — confirm Salesforce's documented DR approach for AU Hyperforce before finalising the architecture.

- **Trust** — Trust is the foundational pillar for Health Cloud data residency work. Patients and healthcare organisations extend trust to the platform on the basis of regulatory compliance and contractual commitments. An undocumented BAA gap or unacknowledged transient processing exception is a trust failure even if no breach occurs. Proactively documenting known exceptions and obtaining stakeholder sign-off is the architectural behaviour that sustains trust over time. The Salesforce Well-Architected Trust pillar emphasises transparency with customers about platform capabilities and limitations — the transient processing exception disclosure practice embodies this principle.

- **Operational Excellence** — The compliance artefacts produced by this skill (BAA coverage matrix, transient processing exception log, ADR) must be maintained as living documents. As the Health Cloud feature set evolves and Salesforce expands Hyperforce regional coverage (including adding regional inference for Einstein features), previously documented exceptions may be resolved. Operational Excellence in this domain means establishing a review cadence — at minimum annually and at each major Salesforce release — to update the compliance register and retract exceptions that Salesforce has resolved.

## Architectural Tradeoffs

**Feature richness vs. data residency completeness:** Health Cloud Intelligence, Einstein for Health, and MuleSoft integrations substantially increase the platform's clinical and operational capability. Each also introduces data residency complexity through separate BAA requirements or transient processing gaps. The tradeoff is between maximising platform feature adoption and achieving the simplest, most defensible data residency posture (which would exclude these features or de-identify data before they touch them). The correct resolution is not to choose one extreme but to document the tradeoff explicitly, apply minimum-necessary PHI scoping to each feature, and obtain compliance team acceptance for any residual risk.

**Agility vs. compliance governance:** Sandbox provisioning with Data Mask is slower and more operationally complex than simply creating a full sandbox and sharing access. Development teams often apply pressure to skip or simplify the de-identification step to accelerate sprints. The Reliability and Security pillars both require that this pressure be resisted: a single sandbox PHI exposure can constitute a HIPAA breach reportable to HHS, with penalties that dwarf the sprint time saved.

**Hyperforce regional selection timing:** Regional selection must be correct at provisioning. There is no architectural option to "migrate" a Hyperforce org to a different region post-provisioning without a full re-implementation. This tradeoff means that if regulatory requirements expand (e.g., a US-only health org acquires a European practice), a new org in the EU region must be provisioned, data migrated, and all integrations re-pointed. Architects should anticipate geographic expansion scenarios and consider whether a multi-org topology provides better long-term flexibility.

## Anti-Patterns

1. **Treating Hyperforce regional selection as a complete data residency solution** — Selecting an EU or AU Hyperforce region satisfies primary data-at-rest residency for core Health Cloud objects but does not address transient processing by Einstein, CRM Analytics, or MuleSoft. Architects who treat regional selection as sufficient create undocumented compliance gaps that surface during audits. The correct pattern is to combine regional selection with BAA coverage mapping, transient processing exception documentation, and field-level encryption for the most sensitive data elements.

2. **Relying on default Data Mask configuration for HIPAA-compliant sandbox de-identification** — Data Mask's default profile does not know which fields contain PHI. Treating Data Mask as a self-configuring PHI removal tool results in sandboxes that appear de-identified but contain real patient data in custom fields, managed package fields, ContentDocument bodies, and rich-text fields. The correct pattern is an explicit, field-by-field Data Mask profile built against a complete PHI field inventory, validated by spot-checking after each sandbox creation.

3. **Assuming all Salesforce products under a single contract share the same HIPAA BAA coverage** — Health Cloud, CRM Analytics, MuleSoft, and Marketing Cloud are separate products with separate BAA addendum requirements. Assuming a single HIPAA BAA covers all Salesforce products used in a Health Cloud implementation is the most common contractual gap. The correct pattern is to produce a BAA coverage matrix at project initiation and update it whenever a new product or feature is activated.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Hyperforce Overview — https://help.salesforce.com/s/articleView?id=sf.hyperforce_overview.htm
- Salesforce Trust and Compliance Documentation (HIPAA BAA scope, addenda) — https://www.salesforce.com/company/legal/compliance/
- Salesforce Health Cloud HIPAA Documentation — https://help.salesforce.com/s/articleView?id=sf.health_cloud_hipaa.htm
- Salesforce Data Processing Addendum (GDPR) — https://www.salesforce.com/company/legal/agreements/
- EU GDPR Article 9 — Special Categories of Personal Data — https://gdpr-info.eu/art-9-gdpr/
- Australia My Health Records Act 2012 — https://www.legislation.gov.au/Series/C2012A00063
