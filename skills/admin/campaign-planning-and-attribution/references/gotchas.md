# Gotchas — Campaign Planning And Attribution

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Campaign Hierarchy Rollup Fields Are Batch-Computed — Not Real-Time

**What happens:** Fields like `AmountWonOpportunities`, `ActualCost`, `NumberOfLeads`, and `NumberOfResponses` on a parent Campaign record do not update when a child Campaign or its associated Opportunity changes. They are updated by a Salesforce background scheduler on an unpredictable cadence (typically within a few hours but without a guaranteed SLA). During an active campaign, the parent record can show stale data for hours.

**When it occurs:** Any time a team builds a live dashboard, an alert automation, or an executive report that reads rollup fields from a parent Campaign during an active program. The issue also surfaces when someone checks a parent Campaign immediately after closing a child opportunity and sees the old totals.

**How to avoid:** Build live reporting from child Campaign records or directly from Opportunity records linked to the campaign. Use parent Campaign rollup fields only for historical or retrospective analysis where a few hours of lag is acceptable. Document the lag explicitly in dashboard titles (e.g., "Program ROI — updates every few hours"). Never build Apex triggers or Flows that depend on a Campaign rollup field as a change event source.

---

## Gotcha 2: Standard Campaign Influence and Customizable Campaign Influence Conflict

**What happens:** Salesforce ships with two distinct Campaign Influence systems: the legacy "standard" Campaign Influence (auto-association based on configurable time window and campaign type rules) and Customizable Campaign Influence (CCI, explicit multi-model attribution). When both are partially active simultaneously, duplicate or conflicting `CampaignInfluence` records appear. Attribution revenue figures become unreliable because records from both systems are aggregated in reports without clear model labeling.

**When it occurs:** An org that has had standard Campaign Influence configured for years then enables CCI without first reviewing and disabling the standard auto-association rules. Both systems write `CampaignInfluence` records; the standard system's auto-created records appear alongside CCI model records with no visual distinction unless the `ModelId` field is explicitly filtered.

**How to avoid:** Before enabling CCI, audit existing `CampaignInfluence` records and document the current auto-association rule configuration. Disable standard Campaign Influence auto-association rules (Setup > Campaign Influence > Auto-Association Rules > disable all). Then enable CCI and configure models from scratch. Accept that existing standard influence records will remain in the system but will not be updated going forward — plan a data hygiene step if historical accuracy matters.

---

## Gotcha 3: CCI Produces No Records If Opportunities Lack Contact Roles

**What happens:** CCI attributes campaigns to opportunities by traversing the chain: Opportunity > Contact Role > Contact > Campaign Member > Campaign. If an Opportunity has no Contact Roles, CCI cannot determine which contacts (and therefore which campaigns) are associated with that opportunity. The result is zero `CampaignInfluence` records for that opportunity, even if campaigns were clearly involved in the deal.

**When it occurs:** Orgs where Contact Roles are optional or not enforced via validation. Common in SMB-oriented orgs or orgs that use Lead conversion without mapping to Contacts on the Opportunity. Also common when Opportunities are created directly from an API integration that does not populate Contact Roles.

**How to avoid:** Make Contact Role population mandatory for all Opportunities at risk of attribution gaps. Options: (1) add a validation rule requiring at least one Contact Role before stage advances past a certain point, (2) build a Flow that auto-populates a Contact Role when an Opportunity is linked to an Account with an existing Contact who is a Campaign Member, or (3) use the Opportunity Contact Role related list as part of the sales team's qualification checklist. Audit existing open Opportunities for missing Contact Roles before going live with CCI.

---

## Gotcha 4: Campaign Hierarchy Depth Is Hard-Limited to 5 Levels

**What happens:** Salesforce enforces a maximum of 5 levels in a Campaign Hierarchy (root + 4 children levels). Attempting to create a 6th-level child Campaign via the UI or API returns an error. Teams that design hierarchies without this constraint in mind — for example, region > sub-region > program > sub-program > campaign type > tactic — hit the wall late in implementation.

**When it occurs:** Enterprise or multi-market marketing teams that have complex program taxonomies and try to model every dimension of the taxonomy in the Campaign hierarchy. Also occurs when teams use hierarchy levels to encode dimensions (e.g., region AND product line AND campaign type) that would be better served by Campaign record fields or custom fields.

**How to avoid:** Use Campaign custom fields (e.g., Region, Product Line, Campaign Theme) to encode dimensional attributes rather than hierarchy levels. Reserve hierarchy levels for true parent-child rollup relationships where cost and revenue aggregation is needed. Validate the design against the 5-level limit before building.

---

## Gotcha 5: MCAE Multi-Touch Attribution App Models Are Reporting-Layer Only — They Do Not Write CampaignInfluence Records

**What happens:** The MCAE B2B Marketing Analytics Plus Multi-Touch Attribution App displays time-decay and position-based attribution in CRM Analytics dashboards. Teams assume these models are writing new `CampaignInfluence` records with updated weighting in the Salesforce database. They are not. The models are applied at query/display time within the CRM Analytics dataset — the underlying `CampaignInfluence` records in Salesforce remain unchanged.

**When it occurs:** When a team tries to use time-decay attribution figures in a Salesforce native report (not a CRM Analytics dashboard), or tries to build a Flow that reads "time-decay influenced revenue" from a Campaign field. The data they expect does not exist in the Salesforce object layer.

**How to avoid:** Treat MCAE multi-touch attribution as a reporting-only capability. Keep CRM Analytics dashboards as the system of record for time-decay and U-shaped model outputs. If other systems need this data, export from CRM Analytics via Data Cloud or a scheduled dataflow — do not attempt to back-fill it into standard Salesforce Campaign or CampaignInfluence fields.
