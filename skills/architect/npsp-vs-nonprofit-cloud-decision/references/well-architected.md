# Well-Architected Notes — NPSP vs. Nonprofit Cloud Decision

## Relevant Pillars

- **Adaptability** — This decision is fundamentally about long-term platform adaptability. Staying on a feature-frozen platform (NPSP) reduces the organization's ability to adopt new Salesforce capabilities, integrate with AI and Agentforce, and benefit from the Nonprofit Cloud innovation roadmap. Moving to NPC restores adaptability but requires a significant one-time investment. The Well-Architected principle of designing for change applies directly: NPSP's frozen state is a structural adaptability risk that worsens over time.

- **Operational Excellence** — The migration path (net-new org, full data migration, configuration rebuild) is operationally complex. A Well-Architected approach ensures the migration is planned with operational continuity in mind: parallel operations during cutover, data validation gates, rollback criteria, and post-migration monitoring. Rushing a migration to meet a self-imposed deadline without these safeguards is an operational excellence anti-pattern.

- **Trustworthiness** — Donor data, program beneficiary records, and financial giving histories are the core assets of a nonprofit Salesforce org. The migration must preserve data integrity — no records lost, no giving totals corrupted, no duplicate constituents created. Trustworthiness requires formal data validation at each migration stage, not just a post-load spot-check.

- **Scalability** — NPC's native object model (Person Accounts, Gift Transactions, native Program Management) is designed for Salesforce's current platform scale capabilities. NPSP's managed package architecture (managed triggers, CRLP rollups, custom metadata rollup definitions) introduces overhead that does not scale as gracefully with large data volumes. Organizations projecting significant constituent or transaction growth have a scalability reason to prefer NPC.

- **Security** — NPSP's open-source managed package model means its code is publicly visible. Security patches are applied by Salesforce but at a slower cadence than a native product. NPC, as a native product, receives security updates through the standard Salesforce platform release cycle. For organizations with strict compliance requirements (HIPAA-adjacent, financial data), this difference should be noted even if it is not usually the primary decision driver.

## Architectural Tradeoffs

**Stability vs. Adaptability:** Staying on NPSP offers maximum near-term operational stability — no migration risk, no org disruption, no configuration rebuild. But it trades long-term adaptability for that stability. Each passing Salesforce release widens the feature gap between NPSP and NPC. Organizations that delay the decision do not avoid the migration; they defer it while accumulating technical debt.

**Migration Cost vs. Innovation Access:** Moving to NPC incurs a significant one-time project cost (professional services, internal staff time, cutover risk). The return on that investment is access to the full Nonprofit Cloud innovation roadmap, including Agentforce for Nonprofits, Einstein features, and native grantmaking — none of which will ever be available on NPSP.

**Person Accounts vs. Household Accounts:** NPC's Person Account model is simpler for orgs where the constituent is the primary record. The Household Account model is better for orgs where household-level giving and household relationship tracking are central to program and fundraising design. Orgs with complex household structures (multiple giving households per family, complex household merges, household-level grant eligibility) should validate NPC's Person Account capabilities carefully before migrating.

**Feature Completeness of PMM Replacement:** NPC's Program Management is the intended replacement for the Program Management Module add-on. It is not a drop-in replacement. Organizations running complex PMM configurations (community portals, custom service delivery workflows, third-party integrations with the PMM data model) face additional migration complexity that must be scoped before a final decision is made.

## Anti-Patterns

1. **Reactive Migration Without a Business Driver** — Migrating to NPC because "NPSP is going away" without a specific feature gap or strategic need is an anti-pattern. It creates org disruption, budget pressure, and implementation risk for an organization that could remain productively on NPSP. A Well-Architected decision is always driven by a concrete requirement, not by fear or community rumor.

2. **Treating Migration as a Configuration Task** — Scoping an NPSP-to-NPC migration as a "data migration and configuration update" underestimates the project significantly. It is a full reimplementation: a new org, new data model, new rollup definitions, new integration endpoints, new user training. Treating it as anything less leads to budget overruns and failed deliveries.

3. **Assuming CRLP and PMM Transfer Automatically** — Planning a migration without explicitly scoping the rebuild of CRLP rollup summaries and PMM Program Management configurations in NPC leaves significant functional gaps post-migration. These are non-trivial workstreams that must be explicitly identified and resourced.

## Official Sources Used

- Nonprofit Cloud Migration and Implementation Guides — https://help.salesforce.com/s/articleView?id=sfdo.NPC_Migration_Guide.htm
- Nonprofit Cloud Developer Guide: Introduction to Nonprofit Cloud — https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud_dev.meta/nonprofit_cloud_dev/nonprofit_cloud_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Nonprofit Cloud: Key Concepts — https://help.salesforce.com/s/articleView?id=sfdo.NPC_Key_Concepts.htm
- NPSP Documentation Overview — https://powerofus.force.com/s/article/NPSP-Documentation
