# Well-Architected Notes — Visualforce to LWC Migration

## Relevant Pillars

- **User Experience** — Visualforce pages render through a server-side template engine and return full-page HTML on every viewstate postback. Even simple field updates trigger a full server round-trip and re-render. LWC renders in the browser, mutates only the changed DOM, and uses platform-native components (lightning-record-edit-form, lightning-datatable) that match Lightning Experience styling and behavior. Migrating to LWC removes the visible "VF flash" (the brief unstyled re-render between postbacks), aligns visual language with the rest of Lightning Experience, and makes pages mobile-first by default.

- **Operational Excellence** — Visualforce is in maintenance mode. Salesforce continues to support it but no longer adds features. New base components, new platform APIs (LDS, LMS, NavigationMixin variants), and new DevOps tooling (Jest unit tests, LWS) are LWC-only. Every retained VF page is technical debt that compounds: it requires a separate testing harness, blocks adoption of new Lightning features, and binds the org to Visualforce-era controller patterns (instance state, viewstate, PageReference). Migrating reduces the long-term maintenance surface and aligns with Salesforce's stated direction.

- **Security** — Lightning Web Security (LWS) provides stricter sandboxing than Locker Service: Trusted Types enforcement, secure window proxies, and stricter cross-origin controls. Migration is the moment to eliminate `<apex:outputText escape="false">` patterns and unsanitized `<apex:outputPanel>` rendering — both well-known XSS surfaces in legacy VF code. `lightning-record-edit-form` enforces FLS automatically; an `@AuraEnabled` Apex method with explicit `WITH SECURITY_ENFORCED` SOQL provides equivalent guarantees on the data layer. The migration removes a class of vulnerabilities by construction.

## Architectural Tradeoffs

**Big-bang VF removal vs incremental coexistence:** Big-bang means deploying the LWC and removing the VF page in the same release. This is appropriate for low-traffic, internally-linked pages with a well-understood user base. Incremental coexistence keeps the VF page available via Lightning Out wrappers while the LWC is gradually surfaced via App Builder; appropriate for pages with external callers (button URLs in marketing emails, deep links from other systems) that cannot be updated synchronously. The cost of incremental is the wrapper-VF + Aura runtime overhead during the transition; the cost of big-bang is the broken-link risk for any uncatalogued caller.

**Retain VF for PDF / email / contentType vs build a new rendering service:** Visualforce remains the supported way to render PDFs server-side, build email-template bodies, and serve custom-content-type responses. Replacing this with a Heroku service or a third-party API is a viable architecture, but it adds an integration boundary, separate deployment, and external system dependency. For most orgs, retaining the small number of rendering-only VF pages is the lower-cost choice — these pages have a tiny attack surface (read-only, often output-only) and don't impede LWC adoption elsewhere.

**Apex service granularity:** A single VF page typically had one controller. Migrating, you can preserve that 1:1 mapping (`AccountSummaryService` corresponds to the old `AccountSummaryController`) or re-architect around domain services (`AccountQueryService`, `OpportunityAggregateService`, etc.). The 1:1 mapping is faster and lower-risk; the domain split sets up better reuse for future LWC components but takes longer and risks scope creep. Choose 1:1 unless multiple in-flight LWC migrations would benefit from shared service classes — then consolidate to domain services.

**LWC sub-component decomposition:** A 1,500-line VF page might naturally decompose into 4–6 LWC components (header, summary tile, related list, action panel). Decomposing at migration time gives a cleaner architecture and reusable parts for future pages, but multiplies the migration scope. The pragmatic middle ground is to migrate the page as a single LWC first (parity with VF) and decompose in a follow-up release once the page is stable in production.

## Anti-Patterns

1. **Treating "no VF remaining" as the migration success criterion.** Some VF pages (PDF, email body, custom content type) cannot be migrated without losing capability. Setting "delete every `.page` file" as the goal forces lossy rewrites with third-party libraries that compromise security and fidelity. The right success criterion is "every user-facing UI surface uses LWC; rendering-only VF pages are documented and retained."

2. **Permanent Lightning Out wrappers.** Lightning Out is a transitional bridge. Every wrapper VF page imposes runtime cost (Aura framework + LWC framework loaded together for one component) and operational cost (two frameworks to maintain, debug, and patch). Track every wrapper with a removal date tied to upstream caller updates. If a wrapper exists for more than two release cycles without an active migration plan for the caller, it has become permanent — surface this as a debt item, not a working solution.

3. **Direct controller-to-service rename without sharing/FLS audit.** The VF controller may have been declared `with sharing` on a page that ran in user context, gaining FLS enforcement on `<apex:inputField>` automatically. The migrated `@AuraEnabled` service runs without the page's protection layer. Renaming `Controller` to `Service` is not enough — every method needs an explicit `with sharing` declaration and explicit `WITH SECURITY_ENFORCED` (or `Security.stripInaccessible`) on every SOQL/DML. The migration is the moment to verify, not assume.

4. **Migrating `<apex:outputText escape="false">` to `lwc:dom="manual"` + `innerHTML`.** This recreates the XSS surface in the new code. The migration is the opportunity to close the vulnerability, not preserve it. Use sanitized rendering primitives or an allow-list HTML sanitizer; never set `innerHTML` from user-controlled content.

5. **Skipping the LWS compatibility test pass.** Migrations done in scratch orgs with default settings may pass functionally but fail in customer orgs that have Lightning Web Security enabled (the default for new orgs). Every LWC migration should include a verification run in an LWS-enabled org BEFORE production deployment, focused on every static-resource library load.

## Official Sources Used

- Visualforce Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/
- Lightning Web Components Developer Guide — https://developer.salesforce.com/docs/platform/lwc/guide/
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Web Security — https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-intro.html
- NavigationMixin Reference — https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate.html
- Lightning Data Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-ui-api.html
- Visualforce Security Best Practices — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Architects: Decision Guide — https://architect.salesforce.com/decision-guides/
