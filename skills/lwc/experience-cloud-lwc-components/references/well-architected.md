# Well-Architected Notes — Experience Cloud LWC Components

## Relevant Pillars

- **Security** — The dominant pillar for this skill. Guest user Apex access, `with sharing` enforcement, `@AuraEnabled` profile grants, and community context module scoping are all security-load-bearing decisions. A misconfiguration here directly enables unauthorized data access or breaks site availability.
- **Adaptability** — Component metadata (JS-meta.xml targets, `targetConfig` design attributes) drives how easily admins can reconfigure or repurpose components across audiences without code changes. Using `basePath` instead of hard-coded URL prefixes makes components portable across environments.
- **Performance** — Use `@AuraEnabled(cacheable=true)` on read-only Apex methods to enable Lightning Data Service caching and reduce redundant server calls. Guest user page loads are typically the highest-traffic scenario; cacheable wire calls reduce Apex execution for common queries.

## Architectural Tradeoffs

**Single component vs. split internal/external components:** The temptation is to build one component with conditional logic for internal vs. Experience Cloud rendering. This works only if the component does not import community context modules (`@salesforce/community/*`, `@salesforce/user/isGuest`). Once those imports are present the component is locked to Experience Builder targets. The well-architected pattern is a context-agnostic base component plus a thin Experience Builder wrapper — it trades a small increase in file count for clean separation of concerns and reliable target compatibility.

**Guest Apex sharing model:** Declaring Apex `without sharing` is never correct for guest-facing components. Even if the immediate query appears safe, `without sharing` creates a hard-to-audit attack surface as the class evolves. Always start with `with sharing` and document any explicit escalation with a code comment and security review sign-off.

**LWR vs Aura target selection:** New Experience Cloud sites default to LWR. Aura-based communities exist for legacy migrations. A component built only with `lightningCommunity__Default` and standard `lightning/navigation` patterns works in both runtimes. Avoid runtime-specific page reference types unless the feature requires them; if so, document the runtime constraint in the component's README.

## Anti-Patterns

1. **Monolithic internal+external component with community imports** — Adding `@salesforce/community/*` imports to a shared component breaks all internal Lightning pages that use it. Separate concerns: base component for logic, wrapper for community context injection. This is the single most common structural mistake when migrating an internal LWC to Experience Cloud.

2. **Assuming `@AuraEnabled` grants public access** — The annotation makes a method callable by the Lightning framework, not by every user. Guest and portal users need explicit Apex Class Access grants per profile or permission set. Omitting this step is a silent failure in testing (developers test as internal users) that surfaces as a production 403 for external users.

3. **Hard-coding site path prefixes in URLs** — Embedding `/myportal/` or `/community/` in `href` attributes or JS string concatenation breaks across environments and is unnecessary given `@salesforce/community/basePath`. Use `basePath` consistently.

## Official Sources Used

- LWC Dev Guide — Configure Component for Experience Builder — https://developer.salesforce.com/docs/platform/lwc/guide/use-component-in-app-builder.html
- LWC Dev Guide — Current Community (community context modules) — https://developer.salesforce.com/docs/platform/lwc/guide/community.html
- LWC Dev Guide — Secure Apex Classes (`with sharing`, `@AuraEnabled` access) — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security
- LWR Sites — Lightning Navigation (`lightning/navigation` in LWR) — https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate-basic.html
- Salesforce Well-Architected Overview — architecture quality framing — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
