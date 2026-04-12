# Well-Architected Notes — Digital Storefront Requirements

## Relevant Pillars

- **Performance** — Storefront architecture choice directly determines rendering performance. SFRA uses server-side rendering (SSR), which reduces Time to First Byte on simple pages but can bottleneck under high concurrency. PWA Kit with Managed Runtime uses SSR + client-side hydration and benefits from CDN-layer caching via Managed Runtime's edge infrastructure. Content slot configurations, Einstein Recommender API latency, and cartridge path resolution depth all affect page load time in SFRA. Performance requirements must be quantified (Core Web Vitals targets) before architecture selection.

- **Security** — SFRA overlay cartridges inherit the SFCC security model but custom JavaScript and API integrations introduce risk. CSP headers, HTTPS enforcement, and PCI scope for checkout pages must be explicitly reviewed. Accessibility compliance (WCAG AA) has a legal security dimension — non-compliance creates regulatory exposure. PWA Kit storefronts communicate with SCAPI, which uses OAuth 2.0 SLAS (Shopper Login and API Access Service) — token management must be handled correctly to prevent shopper session leakage.

- **Adaptability** — The architecture choice determines long-term adaptability. SFRA's cartridge model allows incremental customization but creates accumulating technical debt as the cartridge inventory grows. PWA Kit's component model and SCAPI-driven data layer provide better long-term composability, allowing swaps of individual storefront sections or backend services without full rebuilds. Merchant requirements that include future headless CMS integration or multi-touchpoint distribution (kiosks, native apps) favor PWA Kit's decoupled architecture.

## Architectural Tradeoffs

**SFRA Branding Depth vs. Upgrade Safety:** The more ISML templates an overlay cartridge overrides, the harder it is to take SFRA upgrades. Each template override in `app_custom_*` is a potential merge conflict when SFRA's base templates change. The tradeoff is customization depth versus upgrade velocity. Well-Architected practice is to minimize the override surface area — only override the files that genuinely differ, and prefer CSS/SCSS overrides over template overrides where possible.

**Page Designer vs. Headless CMS:** Page Designer provides low-code authoring with tight SFCC integration but is proprietary — content is locked in the SFCC instance. A headless CMS (Contentful, Contentstack) provides platform-portable content and richer authoring workflows but adds an external system dependency and integration complexity. Merchants who anticipate platform migration or multi-channel content distribution should evaluate a headless CMS, accepting the added operational overhead.

**Accessibility Compliance Investment:** Merchants often underestimate the effort required to achieve and maintain WCAG 2.1 AA compliance. The Well-Architected approach is to treat accessibility as a non-functional requirement with its own sprint allocation, automated regression testing in CI, and a post-launch quarterly review cadence — not a one-time pre-launch checkbox.

## Anti-Patterns

1. **Modifying app_storefront_base directly** — This is the single most common architectural anti-pattern in SFRA projects. It appears harmless during initial development but compounds into a permanent deviation from the Salesforce-maintained upgrade path, blocking security patches and feature releases. Mitigation: enforce overlay-cartridge-only customization via code review gates and document the convention in the project ADR.

2. **Assuming a framework satisfies accessibility compliance** — Both Bootstrap 4 (SFRA) and React component libraries (PWA Kit) provide accessibility primitives, but neither certifies WCAG compliance for a specific storefront implementation. Treating framework adoption as equivalent to compliance bypasses the merchant's legal obligation and delays remediation work until after launch, when it is more expensive and disruptive.

3. **Over-scoping day-1 personalization without data warm-up planning** — Projects that commit to Einstein Recommenders as launch features without accounting for the behavioral data warm-up period create a launch-day gap where recommendation zones are empty. This damages trust with the merchant and requires emergency content backfills. The Well-Architected approach is to launch with fallback content in recommendation zones and phase in ML-driven recommendations 3–4 weeks post-launch.

## Official Sources Used

- B2C Commerce Developer Guide — Storefront Architectures: https://developer.salesforce.com/docs/commerce/b2c-commerce/guide/b2c-storefront-architectures.html
- SFRA Developer Guide — Cartridge Standards and Compliance: https://developer.salesforce.com/docs/commerce/b2c-commerce/guide/sfra-standards-compliance.html
- SFRA Developer Guide — Features and Components: https://developer.salesforce.com/docs/commerce/b2c-commerce/guide/sfra-features-and-components.html
- PWA Kit Developer Guide — Getting Started: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/getting-started.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Commerce Cloud Einstein Recommenders — https://developer.salesforce.com/docs/commerce/b2c-commerce/guide/Einstein.html
