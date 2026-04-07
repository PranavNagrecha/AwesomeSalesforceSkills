# Well-Architected Notes — B2B Commerce Store Setup

## Relevant Pillars

- **Security** — The BuyerGroup/EntitlementPolicy model is the primary access control layer for B2B Commerce. Correctly wiring the WebStore → BuyerGroup → EntitlementPolicy chain ensures buyers can only see and purchase products they are entitled to. Missing junction records silently grant zero access (fail-closed by default), but misconfigured group membership can grant a buyer access to a competitor's pricing tier. Treat group membership as security-relevant data requiring change management controls.

- **Scalability** — Two hard platform limits directly constrain store scale: 200 BuyerGroups per EntitlementPolicy and 2,000 BuyerGroups per product for search indexing. Commerce store architecture must be designed around entitlement tiers, not one-group-per-account, to avoid hitting these limits as the customer base grows. Design the group model for 3x current volume before go-live.

- **Reliability** — Entitlement changes do not automatically trigger search re-indexing. Without a reliable index rebuild process (manual trigger, scheduled job, or post-deployment automation), buyers experience stale search results after any catalog update. Reliability requires an operational runbook that includes index rebuild as a mandatory post-change step.

- **Operational Excellence** — Silent failure modes (missing contact role, search indexing exclusion beyond 2,000 groups) require proactive monitoring rather than reactive incident response. Operational excellence means building end-to-end buyer access validation into deployment checklists and using test buyer logins as smoke tests after any change, not just admin-side verification.

## Architectural Tradeoffs

**Tier-based BuyerGroups vs. Account-per-group:** Modeling one BuyerGroup per customer account gives maximum product visibility granularity but hits the 200-groups-per-policy limit quickly and creates operational overhead at scale. Tier-based groups (one group per product entitlement segment) are harder to design upfront but scale to thousands of accounts without hitting platform limits. Recommend tier-based groups for any store expected to exceed 50 customer accounts.

**Single policy vs. multiple policies:** A single policy simplifies administration but cannot enforce product-set segregation between buyer tiers — entitlements are additive. Multiple policies with discrete product sets enforce hard catalog segmentation at the cost of more junction records to maintain. Use one policy per distinct catalog tier; do not use multiple policies for the same tier as a workaround for volume.

**Manual index rebuilds vs. scheduled rebuilds:** Manual rebuilds are appropriate for low-change-frequency catalogs but introduce human error risk. Scheduled nightly rebuilds reduce stale-search risk but add a ~12-hour delay between entitlement changes and buyer visibility. For high-frequency catalog updates, evaluate whether real-time search alternatives (e.g., custom search with filtered SOSL) are warranted.

## Anti-Patterns

1. **One BuyerGroup Per Account** — Modelling individual customer accounts as separate BuyerGroups to achieve per-account product visibility quickly exhausts the 200-groups-per-policy limit. The correct approach is to model groups around distinct entitlement tiers and manage per-account overrides at the pricing or product visibility rule level rather than through group proliferation.

2. **Skipping Contact Role Assignment and Relying on Account Membership** — Assuming that adding a contact to a BuyerAccount grants that contact transactional access. Buyer and Buyer Manager role assignment is a separate, explicit provisioning step. Skipping it results in contacts who can log in but cannot transact, producing support tickets that are misdiagnosed as entitlement or permission set issues.

3. **Not Rebuilding Search Index After Entitlement Changes** — Treating the Commerce admin catalog view as the source of truth for buyer visibility. The admin catalog and the buyer-facing search index are separate data stores; only a completed index rebuild synchronizes them. Deployments that skip this step cause buyer-reported "missing product" incidents that are not reproducible in admin.

## Official Sources Used

- B2B Commerce Developer Guide — Buyer Group Data Limits — https://developer.salesforce.com/docs/atlas.en-us.b2b_comm_dev.meta/b2b_comm_dev/b2b_comm_buyer_group_data_limits.htm
- B2B Commerce Developer Guide — Entitlement Data Limits — https://developer.salesforce.com/docs/atlas.en-us.b2b_comm_dev.meta/b2b_comm_dev/b2b_comm_entitlement_data_limits.htm
- Salesforce Help — Set Up a Storefront — https://help.salesforce.com/s/articleView?id=sf.comm_setup_storefront.htm&type=5
- Trailhead — Organize Commerce Store Access: Buyer Accounts and Groups — https://trailhead.salesforce.com/content/learn/modules/b2b-commerce-store-access
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
