# Well-Architected Notes — Partner Community Requirements

## Relevant Pillars

- **Security** — PRM portals expose CRM data (Leads, Opportunities, MDF records, co-marketing assets) to external partner users. The sharing model must enforce tier-based record visibility using sharing rules and public groups. Partner users must never access records outside their tier or territory. Guest user access should be disabled for authenticated PRM portals. Security review must happen in the requirements phase, not after the portal is built.

- **Adaptability** — The partner tier hierarchy and deal registration rules are expected to change as the partner program matures (new tiers, new territories, adjusted approval thresholds). Configuration choices that hard-code tier values in profiles or Apex reduce adaptability. Tier-driven logic should live in picklist values, assignment rule criteria, and sharing rules so it can be updated without code changes.

- **Reliability** — The deal registration approval flow is a business-critical path. Approval process design must account for absence coverage (delegated approvers, queue-based routing rather than individual user routing) so that deal registrations are not blocked when a channel manager is out of office. Lead queue-based assignment (rather than user-based) ensures leads remain accessible when partner users are inactive.

- **Operational Excellence** — Partner onboarding (Account setup, user provisioning, tier assignment) should be documented as a repeatable process with a checklist. The `IsPartner` flag dependency, license assignment, and public group membership are steps that are easy to miss in ad-hoc onboarding. A defined runbook reduces errors and support burden.

## Architectural Tradeoffs

**Partner Community vs. Partner Community Plus:** Partner Community Plus adds reporting, dashboard, and broader sharing model capabilities at a higher per-seat cost. The tradeoff is feature richness vs. license spend. Projects that underestimate partners' reporting needs and provision standard Partner Community licenses often face a mid-program license upgrade, which requires re-provisioning all existing users.

**Push vs. Pull Lead Distribution:** Push (assignment rules) provides immediate lead delivery to partners but requires capacity logic to avoid overloading active partners. Pull (shared queue) gives partners agency and eliminates capacity complexity, but requires partners to proactively work the lead pool, which reduces lead response time. The right model depends on partner engagement levels and SLA requirements.

**MDF in Salesforce vs. External System:** Tracking MDF in Salesforce provides portal visibility and audit trail but requires custom object design and ongoing Salesforce administration. An external finance system may already handle budget tracking with better reporting capabilities. The tradeoff is consolidation (Salesforce) vs. leverage of existing tools (external). Define this decision in requirements and size both options before recommending.

## Anti-Patterns

1. **Customer Community license for PRM features** — Assigning Customer Community or Customer Community Plus licenses to partner users in a PRM implementation results in silent feature unavailability. PRM-specific components (deal registration, lead inbox, MDF) are gated to Partner Community license. This is the most expensive mistake to correct post-build because it requires license re-provisioning and potential portal rebuild.

2. **Profile-only tier visibility without sharing rules** — Designing tier-differentiated record visibility using profiles alone. All partner users in the same tier share the same license type, so profile cannot vary record-level access within the tier. Co-marketing assets, lead pools, and MDF records require sharing rules scoped to tier-based public groups to enforce tier visibility correctly.

3. **Individual user-based approval routing and lead assignment** — Routing deal registration approvals to a specific named user (rather than a queue) and assigning leads to individual partner user records (rather than queues). This creates single points of failure: when the named approver or user is inactive, the entire workflow stalls. Queue-based routing provides resilience and auditability.

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing (Trusted/Easy/Adaptable model, anti-pattern guidance)
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- Partner Relationship Management (PRM) — Configure Deal Registration in Partner Central
  URL: https://help.salesforce.com/s/articleView?id=sf.prm_deal_reg_overview.htm

- Configure Lead Distribution — Salesforce Help
  URL: https://help.salesforce.com/s/articleView?id=sf.prm_lead_distribution.htm

- Partner Community License Overview — Salesforce Help
  URL: https://help.salesforce.com/s/articleView?id=sf.networks_partner_license_overview.htm

- Experience Cloud: Set Up a Partner Community — Salesforce Help
  URL: https://help.salesforce.com/s/articleView?id=sf.networks_setup_partner_community.htm
