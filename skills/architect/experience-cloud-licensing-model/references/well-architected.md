# Well-Architected Notes — Experience Cloud Licensing Model

## Relevant Pillars

- **Trusted** — License selection directly affects the security and data visibility model. Choosing a license tier that cannot support the required sharing model leads to over-permissive workarounds (e.g., custom Apex sharing that bypasses intended access controls) or under-permissive configurations that break portal functionality. Selecting the correct tier enforces the platform's native security model.

- **Adaptable** — License tier is difficult to change after deployment because it is tied to user profiles. Selecting a tier with appropriate headroom for the expected 12–18 month roadmap reduces the cost and risk of future migrations. Starting too low optimizes for current cost but creates architectural debt the moment requirements evolve.

- **Efficient** — Login-based vs member-based selection is primarily an efficiency concern. Purchasing member seats for a low-activity user base wastes license spend. Purchasing login credits for a high-activity user base creates unpredictable overage cost. The break-even model ensures the licensing investment matches actual platform utilization patterns.

## Architectural Tradeoffs

**Cost optimization vs upgrade risk:** Customer Community is the cheapest tier, but if any requirement emerges that requires reports or role-based sharing, a profile migration is mandatory. Choosing Customer Community Plus for a portal that "might" need reports later is a hedge that costs more upfront but avoids a potentially expensive future migration. The right answer depends on how confident the team is in the requirements being stable.

**Login-based flexibility vs credit burn risk:** Login-based licensing aligns cost to usage, which is economical during ramp-up. However, if a portal becomes more heavily used than projected, the login credit pool can be exhausted — which in some org configurations results in users being unable to log in until more credits are purchased. Member-based licenses have no such throttle risk. High-criticality portals with unpredictable load patterns should bias toward member-based to eliminate usage ceiling risk.

**Single community vs multiple communities:** Mixing B2C (Customer Community license) and B2B partner users (Partner Community license) in a single Experience Cloud site is technically possible using different profiles, but it complicates navigation, component visibility, and sharing configuration. Two separate Experience Cloud sites on the same org — each configured for its license type — is the preferred architecture for mixed-audience scenarios.

## Anti-Patterns

1. **Defaulting to Customer Community for all portals** — The cheapest tier is not always appropriate. Applying Customer Community universally results in missing sharing capabilities (no roles, no criteria-based rules) or missing feature access (no reports), and ultimately triggers license migrations when requirements mature. The correct approach is to run the decision framework in SKILL.md for every portal project.

2. **Selecting license tier without modeling login economics** — Choosing member-based by default "because it's simpler" ignores the substantial cost difference at high user volumes with low activity ratios. For portals with tens of thousands of users who log in infrequently, login-based licenses can be dramatically cheaper. Equally, recommending login-based without a usage model risks credit exhaustion on a high-activity portal.

3. **Treating license upgrade as a configuration change** — Teams sometimes plan a "start with Customer Community, upgrade later" strategy without accounting for the profile migration effort. For large user populations, migrating profiles is a bulk data operation with testing, rollback planning, and downstream permission audit requirements. This risk must be explicitly documented in the architecture decision record if a phased license strategy is chosen.

## Official Sources Used

- Salesforce Help — Experience Cloud Licenses — license tier capabilities, sharing model support, object access per tier
  URL: https://help.salesforce.com/s/articleView?id=sf.networks_license_types_overview.htm

- Salesforce Help — License Limitations — hard constraints by license type (reports, objects, sharing)
  URL: https://help.salesforce.com/s/articleView?id=sf.networks_license_types.htm

- Salesforce Help — Login-Based Licensing — login credit mechanics, daily unique login definition, rollover policy
  URL: https://help.salesforce.com/s/articleView?id=sf.networks_login_based_licensing.htm

- Salesforce Well-Architected Overview — Trusted, Adaptable, and Efficient pillars framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
