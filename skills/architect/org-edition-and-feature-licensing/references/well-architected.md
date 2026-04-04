# Well-Architected Notes — Org Edition and Feature Licensing

## Relevant Pillars

- **Scalability** — Edition selection determines sandbox availability, API limits, storage, and support tier. An org architected for growth needs an edition that does not become a ceiling as the org scales. Discovering edition limits after implementation starts is a costly constraint.
- **Reliability** — Solutions that depend on add-on features create a reliability dependency on license continuity. If an add-on license lapses or is not renewed, the features it enables will stop working. Document license dependencies in technical designs so renewals are planned.

## Architectural Tradeoffs

**Add-on licenses vs. edition upgrade:** Add-ons are often cheaper and faster than a full edition upgrade, but they add complexity to license management and renewal. An edition upgrade provides a broader capability foundation but has higher base cost and requires more change management. For single-feature gaps, an add-on is usually the right path. For multiple feature gaps, evaluate whether the total add-on cost approaches the edition upgrade price.

**Designing for the customer's edition vs. the ideal edition:** Architects sometimes design solutions for the edition they wish the customer had, then discover the customer is on Professional. Always confirm edition during discovery, not during implementation.

**Feature gating in managed packages:** ISV partners building managed packages must test against the minimum edition their package supports (typically Enterprise). Features that work in Developer Edition or Unlimited may not be available to Enterprise-only customers.

## Anti-Patterns

1. **Designing Apex-dependent solutions without confirming the customer is on Enterprise+** — Apex is not available in Professional Edition. This is a common late-discovery blocker.
2. **Assuming all Einstein/AI features are included in Unlimited** — Unlimited includes some Einstein features but Agentforce, Einstein Copilot, and CRM Analytics are typically add-ons.
3. **Not documenting license dependencies in the technical design** — If the solution requires a Shield or Agentforce add-on, this must be in the design document so procurement can plan renewals.

## Official Sources Used

- Salesforce Editions and Pricing — https://www.salesforce.com/editions-pricing/overview/
- Salesforce Help — Salesforce Editions Feature Overview — https://help.salesforce.com/s/articleView?id=sf.overview_limits_general.htm
- Salesforce Help — Permission Set Licenses — https://help.salesforce.com/s/articleView?id=sf.users_permissionset_licenses_overview.htm
- Salesforce Help — Sandbox Types and Templates — https://help.salesforce.com/s/articleView?id=sf.deploy_sandboxes_parent.htm
- Salesforce Trust — Salesforce Shield Overview — https://www.salesforce.com/products/platform/products/shield/
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
