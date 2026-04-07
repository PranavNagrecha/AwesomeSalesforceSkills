# Well-Architected Notes — LWR Site Development

## Relevant Pillars

- **Security** — LWR sites use Lightning Web Security (LWS), which enforces stricter cross-namespace isolation than Lightning Locker while providing native DOM API access within a namespace. Components must be audited for restricted DOM API usage (`document.domain`, `window.location`, `window.top`) and for guest-user data exposure risks. URL parameter validation is the component's responsibility — the platform does not prevent guest users from accessing record routes for records they cannot access.

- **Performance** — LWR sites are designed for high-performance delivery. Publish-time freezing and HTTP caching of static resources (150-day TTL for framework scripts, 1-day TTL for org assets) enable CDN-level caching. Custom component CSS using `--dxp` hooks avoids runtime style recalculation from inline overrides. Keeping route counts below 250 (hard limit 500) supports optimal performance.

- **Adaptability** — Using `--dxp` styling hooks instead of hardcoded values ensures the entire site responds to Theme panel changes without developer intervention. Configurable `@api` properties exposed through `lightningCommunity__Default` allow non-developer site admins to adapt component content without code changes. Screen-responsive properties with `screenResponsive="true"` support mobile, tablet, and desktop variants from a single component.

- **Reliability** — The publish-time freeze model means the live site always serves a known, tested snapshot. However, any change to component code, labels, or Apex signatures requires explicit republishing — missing this step creates divergence between the developer-verified state and the live site state. Reliable LWR delivery requires republishing to be a formal, checklist-driven step in every deployment.

- **Operational Excellence** — SFDX-based development (source-driven) is the standard model for LWR component authoring. Experience Bundle and Digital Experience Bundle metadata types capture site configuration for version control. Site admins can configure most content through Experience Builder without code changes when components are well-designed with exposed `@api` properties.

---

## Architectural Tradeoffs

**LWR vs. Aura-based templates:** LWR delivers superior performance through publish-time static serving and HTTP caching, but requires all components to be LWC. Aura-based templates support both LWC and Aura components but do not offer the same performance characteristics. If any existing functionality depends on Aura components that cannot be rewritten as LWC, LWR is not the correct template choice.

**Static serving vs. dynamic serving:** LWR's static-serving model means the live site is always a consistent, cached snapshot. This improves performance and CDN cacheability but introduces the publish-cycle discipline requirement. Teams that frequently update component code and expect live site changes without a publish step will find LWR's model counterintuitive. Design deployments to batch component updates and publish as a release, rather than expecting hot-swapping.

**--dxp hooks vs. hardcoded CSS:** Using `--dxp` hooks is initially more abstract but pays dividends when brand colors change, dark/light themes are introduced, or section palettes are needed. Hardcoded values create a maintenance burden that scales with site complexity. Invest in `--dxp` hook usage from the start.

**lightningCommunity__Default exposed properties vs. CMS-driven content:** For content that changes frequently (event dates, headlines, promotional text), CMS-driven content (Salesforce CMS or rich content editor components) is more appropriate than exposed `@api` properties. Exposed properties are best suited for structural and behavioral configuration (layout choices, color overrides, component modes) that changes infrequently.

---

## Anti-Patterns

1. **Using hardcoded hex values for brand colors in component CSS** — This severs the link between the Theme panel and the component. Brand updates require code changes and republishing instead of a single Theme panel update. Use `var(--dxp-g-brand)` and related hooks for all brand-sensitive colors.

2. **Expecting live site changes without republishing** — Treating the Experience Builder preview as the live site. Bug fixes, feature updates, and managed package upgrades are invisible to live site users until the site is republished. Build republishing into every deployment workflow.

3. **Referencing Aura components or using Aura navigation APIs in LWR sites** — Aura components do not render in LWR. Using `comm__namedPage` with `pageName` (deprecated) instead of `name`, or using Aura-specific navigation service patterns, causes navigation failures. Use `lightning/navigation` with `NavigationMixin` and `comm__namedPage` with the `name` attribute exclusively.

---

## Official Sources Used

- LWR Sites for Experience Cloud Developer Guide v66.0 (Spring '26) — `knowledge/imports/exp-cloud-lwr.md` — primary authority for LWR template behavior, limitations, publish model, LWS, component targets, and --dxp theming
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html — LWC design guidelines, composition, and coding best practices
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide — base component behavior and supported usage in LWR context
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Trusted/Easy/Adaptable framing for architectural decisions
