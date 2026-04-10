# Well-Architected Notes — Campaign Planning And Attribution

## Relevant Pillars

- **Operational Excellence** — Campaign attribution models and hierarchy designs must be explicitly documented so revenue operations teams can interpret reports consistently. Undocumented model choices (e.g., why first-touch was chosen over even-distribution) cause re-work when attribution data is questioned by stakeholders. The skill's recommended workflow includes a documentation step as a required deliverable.

- **Reliability** — Campaign Hierarchy rollup fields update via a batch scheduler, not in real time. Designs that depend on real-time rollup accuracy for automation or alerts are inherently unreliable. Architecture decisions must account for this lag by sourcing live data from Opportunity records directly rather than from parent Campaign aggregates.

- **Scalability** — Campaign Hierarchy is capped at 5 levels. Attribution model configuration scales poorly if Contact Role population is not enforced, since CCI produces no records for opportunities without Contact Roles. Both constraints require early architectural decisions that are difficult to undo at scale.

- **Security** — Campaign Influence records inherit visibility from the underlying Campaign and Opportunity objects. Orgs with complex sharing rules must verify that marketing users can read the CampaignInfluence records their dashboards depend on. Attribution reports that appear blank are often a sharing/visibility problem, not a configuration problem.

- **Performance** — CCI with many active models on a high-volume opportunity org can produce a large number of `CampaignInfluence` records. SOQL queries and reports against this object at scale should use selective filters (ModelId, CloseDate ranges) to avoid full-table scans.

## Architectural Tradeoffs

**Native CCI vs. MCAE Multi-Touch Attribution App**

Native CCI (Customizable Campaign Influence) runs entirely within the Salesforce Campaign and Opportunity data model. It supports first-touch, last-touch, and even-distribution models. It writes `CampaignInfluence` records that are queryable via SOQL and usable in standard Salesforce reports. The tradeoff is that more sophisticated models (time-decay, U-shaped) are not available natively.

The MCAE Multi-Touch Attribution App extends model coverage to time-decay and position-based models but is only available with B2B Marketing Analytics Plus licensing. Its results exist only in CRM Analytics datasets — they cannot be queried from standard Salesforce reports or used in automation. Teams that need attribution data to flow into other systems or automations should not depend on MCAE multi-touch models.

**Campaign Hierarchy depth vs. dimensional encoding**

Using hierarchy levels to encode multiple business dimensions (region, product line, campaign type) exhausts the 5-level limit quickly and creates rigid structures that are expensive to reorganize. The architecturally sound approach is to use hierarchy levels only for true cost/revenue rollup aggregation (program > tactic) and encode other dimensions as Campaign record fields or custom metadata. This preserves hierarchy headroom and allows dimensional filtering in reports without restructuring the hierarchy.

**Enforcing Contact Roles as a reliability prerequisite for CCI**

CCI's reliability is entirely dependent on Contact Role population. An org that enables CCI without enforcing Contact Roles will have partial, misleading attribution data — some deals will show influence, others will show none, with no clear indicator of which is correct. The architectural decision to enforce Contact Roles (via validation rule, Flow automation, or process policy) is a prerequisite for CCI to be a trustworthy data source, and should be made before CCI is enabled.

## Anti-Patterns

1. **Dual-system campaign influence without cleanup** — Enabling CCI while leaving standard Campaign Influence auto-association rules active produces conflicting `CampaignInfluence` records from two systems. Reports aggregate both without model distinction, making attribution unreliable. Always disable standard influence auto-association before relying on CCI.

2. **Real-time automation triggered from Campaign rollup fields** — Building Flows or Apex that fire when a parent Campaign's `AmountWonOpportunities` or `ActualCost` changes treats batch-computed fields as event sources. Because rollups are not updated in real time, automation fires late, inconsistently, or not at all. Automation should be triggered from Opportunity or child Campaign events, not parent Campaign rollup changes.

3. **Attribution reporting without Contact Role governance** — Rolling out CCI dashboards to revenue leadership without ensuring Contact Roles are populated on all in-scope Opportunities produces reports that undercount attribution. Leadership conclusions drawn from incomplete data are worse than no attribution reporting at all. Contact Role governance must be established before CCI data is treated as authoritative.

## Official Sources Used

- Customizable Campaign Influence — https://help.salesforce.com/s/articleView?id=sf.campaigns_influence_about.htm
- Campaign Hierarchy Considerations — https://help.salesforce.com/s/articleView?id=sf.campaign_hierarchy_considerations.htm
- MCAE Multi-Touch Attribution App — https://help.salesforce.com/s/articleView?id=sf.pardot_multi_touch_attribution.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
