# Well-Architected Notes — Grant Management Setup

## Relevant Pillars

- **Reliability** — Grant management setup directly affects Reliability. Award disbursement status lifecycles and requirement gating automation must produce consistent, predictable outcomes. A misconfigured status Flow or a disbursement gating validation rule with logic gaps can result in payments being released without fulfilled deliverables — or correct disbursements being blocked indefinitely. Reliability requires that the FundingAwardRequirement lifecycle (Open → Submitted → Approved) and FundingDisbursement status transitions are enforced by platform automation, not by manual process discipline.

- **Operational Excellence** — Grant programs require ongoing operational oversight: disbursement schedules, reporting deadlines, compliance deliverables, and funder audits. Operational Excellence in this domain means building reports and dashboards that surface the grant pipeline accurately, automating notifications at key lifecycle transitions, and maintaining documentation of the platform path choice so future administrators understand the data model without reverse-engineering it.

- **Security** — Grant data is financially sensitive. FundingAward amounts, grantee relationships, and disbursement records may be subject to funder confidentiality requirements. Object-level and field-level security should be configured so that external portal users (grantees) can access only their own requirement submissions, while internal grants staff have full edit access. Permission Set-based access is preferred over profile-based, given the Grantmaking license model.

- **Performance** — For large grant portfolios (hundreds of awards, thousands of disbursements), roll-up summary fields on FundingAward can create lock contention if many disbursement records are updated simultaneously (e.g., batch year-end status updates). For high-volume orgs, consider Flow-based aggregation with asynchronous processing rather than declarative roll-up summaries.

- **Scalability** — The FundingAward / FundingDisbursement / FundingAwardRequirement data model scales well for typical nonprofit grant portfolios. For community foundations or government grantmakers managing thousands of concurrent awards, ensure record type segmentation is planned early — retrofitting record types on FundingAward after awards are live requires data migration.

## Architectural Tradeoffs

**OFM vs. NC Grantmaking:** The fundamental tradeoff is platform reach vs. purpose-built functionality. OFM works on NPSP without a separate license but requires heavy customization to achieve deliverable tracking, multi-tranche scheduling, and status governance. NC Grantmaking provides all of this natively but requires a separate license and an NPC base. The right choice depends on licensing economics, existing org platform, and the complexity of grant programs managed.

**Declarative vs. Apex automation for lifecycle governance:** Using Flows to enforce FundingAwardRequirement status transitions is the recommended approach for most orgs. Apex trigger-based enforcement provides more control over error handling and bulk behavior but adds technical debt. For orgs with dedicated Apex developers managing complex grant programs, Apex validation in a trigger handler may be more robust than a complex multi-branch Flow.

**Custom portal for grantee access vs. internal-only tracking:** If grantees are expected to submit deliverables directly in Salesforce (via Experience Cloud), the data model must accommodate external user permissions on FundingAwardRequirement. If grant tracking is purely internal staff operations, this complexity is unnecessary.

## Anti-Patterns

1. **Conflating OFM and NC Grantmaking in a single implementation** — Attempting to use both `outfunds__Funding_Request__c` and `FundingAward` in the same org creates two parallel data models for grant tracking with no integration, double-maintenance, and reporting that cannot be unified without custom middleware. Choose one platform path and commit to it.

2. **Treating the grant platform as an accounting system** — Salesforce Grantmaking tracks grant lifecycle and relationships, not financial accounting (general ledger, accounts payable, or tax reporting). Attempting to replicate AP workflows on FundingDisbursement (e.g., invoice numbers, GL codes, payment runs) overloads the object model and creates data integrity problems when reconciling against the actual financial system of record.

3. **Skipping platform path documentation** — Omitting written documentation of the chosen platform (OFM vs. NC Grantmaking), its licensing requirements, and the customizations made to the standard lifecycle produces an org that the next administrator cannot maintain without reverse-engineering every Flow and validation rule.

## Official Sources Used

- Grants Management Product Documentation — https://help.salesforce.com/s/articleView?id=sfdo.Grants_Management.htm
- Manage Funding Awards and Disbursements (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/nonprofit-cloud-for-grantmaking
- Fund Management Requirements and Disbursements Guide (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/nonprofit-cloud-grantmaking-requirements
- Grantmaking and Budget Management Data Model (Salesforce Developers) — https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud.meta/nonprofit_cloud/npc_grantmaking_data_model.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
