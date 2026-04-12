# Well-Architected Notes — Fundraising Process Mapping

## Relevant Pillars

### Adaptability

The fundraising lifecycle is the primary place where Adaptability matters most in nonprofit Salesforce implementations. Stage models that are too rigid — with too many stages or overly specific entry/exit criteria — cannot absorb changes when fundraising strategy evolves, a new development director joins, or the organization launches a new program type. The Well-Architected Adaptability pillar calls for designing for change: stage vocabulary should match how the development team actually works, entry/exit criteria should be consensus-based rather than technically enforced wherever possible, and the stage model should be documented as an artifact that can be reviewed and revised without breaking the platform.

The December 2025 NPSP end-of-new-provisioning event is a real-world example of Adaptability risk: organizations that built deep dependencies on NPSP-specific features (Engagement Plans, namespace fields, NPSP Settings) now face a migration path to NPC. A stage design that is documented, clearly owned, and decoupled from implementation-specific features (i.e., the stage names are not hard-coded into brittle Apex or overly complex picklist dependencies) is far easier to migrate.

### Efficiency

The Efficiency pillar is served by ensuring gift officers can move through the pipeline without friction. Stage designs with too many intermediate stages, unclear exit criteria, or confusing names force gift officers to interpret stages rather than work them. Pipeline report accuracy decays. Stage-change automation must be efficient: overly complex stage-transition Flows that block saves or throw validation errors at unexpected points will cause workarounds that undermine the entire process model.

### Operational Excellence

Operational Excellence requires that the fundraising process is documented, repeatable, and auditable. A stage map produced before configuration — reviewed by development leadership and the fundraising team — is the operational excellence artifact for this skill. Without it, Salesforce becomes a system of record that no one trusts for forecasting. With it, gift officers have a shared vocabulary, pipeline reports reflect reality, and new staff can be onboarded to the process.

## Architectural Tradeoffs

**Specificity vs. flexibility in stage design:** More stages provide more granular pipeline visibility but increase gift officer cognitive load and data quality risk. Fewer stages are easier to maintain but may not support nuanced forecasting. The recommended balance is 5–8 stages per program type, with clear entry/exit criteria for each.

**NPSP four-process model vs. simplified single process:** NPSP ships four separate sales processes (Donation, Grant, In-Kind, Major Gift). Organizations that run multiple program types should maintain separate processes — the stage vocabulary is genuinely different between a grant application lifecycle and a major gift cultivation arc. Consolidating into one process trades accuracy for simplicity and typically produces a worse outcome for both program types.

**Post-close stages (Stewardship) vs. using Engagement Plans:** Adding a Stewardship stage keeps post-close relationships visible in standard pipeline views but requires careful management of the IsClosed flag. Using NPSP Engagement Plans instead keeps the pipeline clean (Closed Won records are closed) while automating stewardship tasks. For NPC orgs, the Engagement Plan option is not available; Flow or Cadences are the alternative. The choice depends on whether the organization needs post-close pipeline visibility or just stewardship task automation.

## Anti-Patterns

1. **Designing stages without development team input** — Salesforce admins who design stage vocabularies from Salesforce defaults rather than from the fundraising team's actual language produce a system that gift officers do not recognize as their work. Adoption fails. Always start with the development team's language and map it to Salesforce, not the reverse.

2. **Building automation before stage design is approved** — Stage-change Flows, validation rules, and rollup configurations that reference specific stage values become technical debt the moment a stage is renamed or removed. Stage design must be signed off and locked before any automation is built against it.

3. **Assuming NPSP is present without verification** — On post-December 2025 orgs, NPSP may not be installed. Any automation, field reference, or configuration step that assumes the `npsp__` namespace exists will fail silently or throw errors. Verify the platform before writing any guidance.

## Official Sources Used

- Salesforce Help — Nonprofit Success Pack (NPSP) Opportunity Settings: https://help.salesforce.com/s/articleView?id=sf.npsp_setup_donations.htm
- Trailhead — Moves Management with Nonprofit Success Pack: https://trailhead.salesforce.com/content/learn/modules/moves-management-with-nonprofit-success-pack
- Trailhead — Opportunity Settings in Nonprofit Success Pack: https://trailhead.salesforce.com/content/learn/modules/npsp-opportunity-settings
- Salesforce Help — Nonprofit Cloud Overview: https://help.salesforce.com/s/articleView?id=sfdo.npc_overview.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Adaptability Pillar: https://architect.salesforce.com/docs/architect/well-architected/guide/adaptability.html
- Salesforce Well-Architected: Operational Excellence Pillar: https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
- Object Reference — Opportunity: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunity.htm
