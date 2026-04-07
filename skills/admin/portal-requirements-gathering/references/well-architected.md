# Well-Architected Notes — Portal Requirements Gathering

## Relevant Pillars

- **Trusted** — Access architecture (public / authenticated / hybrid) and license selection directly govern what data external users can read and write. Getting these wrong creates data exposure risk. Requirements must lock the access model and include guest user profile lockdown as a named deliverable.
- **Adaptable** — License type and access architecture are difficult to change at scale. Requirements must make forward-looking decisions that accommodate the business's likely phase 2 needs without over-engineering phase 1.
- **Easy** — Portal requirements should translate directly to a clear, prioritized feature scope that a build team can execute without ambiguity. The top-3 jobs model keeps scope manageable and measurable.

## Architectural Tradeoffs

**License cost vs. capability headroom**
Customer Community is lower cost per user but lacks advanced sharing and custom object flexibility. Customer Community Plus adds cost but removes the need for a future migration. The right answer depends on the sharing requirements identified during contact reason analysis and use case definition. Do not default to the cheapest license without confirming capability coverage.

**Hybrid access vs. authenticated-only**
Hybrid access increases reach (anonymous visitors can access public pages) but introduces guest user profile risk and adds complexity to the sharing model. Authenticated-only is simpler to govern and audit. Only choose hybrid if there is a clear, signed-off business case for public pages (e.g., a public knowledge base that reduces search engine-driven contacts).

**Phase 1 deflection focus vs. full community vision**
Full community portals (with social, gamification, and idea exchange) have higher long-term value but require the core self-service loop to work first. Phasing correctly means phase 1 delivers a measurable business outcome (deflection) before phase 2 adds community engagement features. Collapsing both phases into one produces a portal that is large in scope and difficult to measure.

## Anti-Patterns

1. **Feature-first requirements** — Selecting portal features before running contact reason analysis produces a portal that does not match what customers actually need. The Well-Architected principle of building for customer outcomes requires starting with evidence of what customers are trying to do, not what stakeholders believe they want.

2. **License selection as afterthought** — Treating license selection as an IT procurement task rather than an architectural decision delays it until build. Because license type governs sharing model, object access, and feature availability, a late or wrong license decision requires rework that impacts every other build decision made before it.

3. **Unscoped hybrid access** — Choosing a hybrid access model without explicitly documenting which pages are public, what the guest user profile permits, and how record-level access is controlled. This creates a trusted architecture risk (data exposure) that is invisible during requirements and expensive to fix post-launch.

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing (Trusted, Adaptable, Easy pillars)
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help: Plan and Prepare for Experience Cloud — access architecture, license types, and site planning guidance
  https://help.salesforce.com/s/articleView?id=sf.networks_overview.htm
- Salesforce Help: Experience Cloud User Licenses — license type comparison and object access matrix
  https://help.salesforce.com/s/articleView?id=sf.users_license_types_communities.htm
