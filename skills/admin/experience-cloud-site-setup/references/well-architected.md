# Well-Architected Notes — Experience Cloud Site Setup

## Relevant Pillars

- **Security** — Experience Cloud sites expose Salesforce data and functionality to external users, including unauthenticated guests. The guest user profile is the primary attack surface: it must be scoped to minimum necessary permissions. Object- and field-level security on the guest profile must be explicitly reviewed before go-live. Sharing settings determine which records partners or customers can see; overly permissive sharing (e.g., Public Read/Write on sensitive objects) can expose data to unintended audiences. Custom domains must be configured with HTTPS; Salesforce enforces HTTPS on `*.my.site.com` domains by default.
- **Performance Efficiency** — LWR templates deliver the primary performance advantage in Experience Cloud. Publish-time page freezing and HTTP caching at the CDN layer reduce per-request org compute significantly for high-traffic public sites. Using LWR for public-facing portals is the architecturally sound default. Choosing Aura for a high-traffic site sacrifices this caching layer.
- **Scalability** — For high-traffic sites, LWR's CDN caching model reduces load on Salesforce servers by serving cached pages for unauthenticated sessions. Authenticated sessions still hit Salesforce for data. For authenticated-heavy sites, consider data access patterns carefully (LDS wire adapters, caching within components) rather than relying solely on the template choice.
- **Reliability** — The publish model on LWR sites is a reliability consideration: changes do not propagate until explicitly published. A broken publish does not affect the currently serving version (the last published build remains live). This is a safety feature but also means practitioners must maintain an explicit publish workflow to avoid serving stale content.
- **Operational Excellence** — Documenting the template selection decision (LWR vs Aura) and the component inventory used to make it is critical for long-term maintainability. Template decisions cannot be reversed; undocumented choices lead to confusion when teams grow or ownership changes.

## Architectural Tradeoffs

**LWR vs Aura:** The LWR template is the strategic direction for Experience Cloud. It offers superior performance through publish-time caching, clean URL paths, and a modern component model (LWC-only). The tradeoff is that it requires all components to be LWC — any existing Aura component investment must be migrated or left behind. For greenfield projects, LWR is the correct default. For projects with significant Aura component debt, the Aura template may be necessary as a transitional choice, but teams should plan for eventual migration.

**Pre-built templates vs Build Your Own:** Pre-built templates (Partner Central, Customer Account Portal) deliver faster time to value for standard use cases at the cost of flexibility. Build Your Own (LWR or Aura) gives full control over page structure and component composition at the cost of more upfront build effort. The right choice depends on how closely the use case maps to the pre-built template's assumptions.

**Custom domain vs default site URL:** Using My Domain (`MyDomainName.my.site.com`) is the standard production pattern. Salesforce-hosted default URLs can be used for development but should not be the primary URL for a production site as they are harder to brand and may change.

## Anti-Patterns

1. **Creating a site with the wrong template and iterating on it** — Because template selection is permanent, starting with a quick "exploratory" site creation and then building on top of it is risky. If the template turns out to be wrong, everything built must be rebuilt. Always confirm the template decision before creating the site, even for a proof of concept. If a throwaway site is needed for exploration, name it clearly as temporary and delete it before the production site is created.

2. **Granting broad guest user permissions for speed** — Granting the guest user profile object-level read access to all standard objects, or enabling "View All" on the guest profile to quickly get pages rendering, is a security anti-pattern. This exposes sensitive Salesforce data to unauthenticated internet users. Scope guest user permissions to only the objects and fields genuinely required for public pages. Test explicitly as an unauthenticated user before go-live.

3. **Hardcoding styles in component CSS instead of using --dxp- tokens** — When LWC components embedded in LWR sites use hardcoded color values or font sizes in their CSS instead of consuming `--dxp-*` CSS custom property tokens, the components become disconnected from the site's branding set. A branding change in Experience Builder will not cascade to those components. All component styles for Experience Cloud should consume the relevant `--dxp-*` tokens so the branding system remains coherent.

## Official Sources Used

- LWR Sites for Experience Cloud (v66.0, Spring '26) — LWR vs Aura template comparison, publish model, performance behavior, LWR template limitations
- Salesforce Help: Custom Domain for Experience Cloud — Custom domain pattern (`MyDomainName.my.site.com`), My Domain requirement
- Salesforce Help: Experience Builder — Page builder, navigation menu configuration, branding sets, site publishing
- Salesforce Well-Architected Overview — Architecture quality framing (Security, Performance Efficiency pillars) — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
