# Well-Architected Notes — Knowledge Article LWC

## Relevant Pillars

- **Security** — The primary security risk is XSS from unsanitized Knowledge article body HTML. Using `lightning-formatted-rich-text` instead of `innerHTML` is mandatory. For Experience Cloud, guest user data category visibility and `without sharing` Apex declarations must be explicitly reviewed to prevent unintended data exposure or denial of access. SOSL injection must be mitigated by escaping user input before embedding it in dynamic SOSL strings.
- **Performance** — Knowledge article retrieval is a high-frequency operation on self-service sites. `@AuraEnabled(cacheable=true)` and `@wire(getRecord)` leverage Lightning Data Service caching to avoid redundant Apex round trips. Client-side debouncing on search inputs prevents cascading Apex calls. SOSL is preferred over SOSL with wildcard-heavy patterns that degrade at scale.
- **Scalability** — Data category-scoped SOQL cannot use aggregate functions, which constrains pagination architectures. Offset-based SOQL pagination degrades beyond 2,000 rows; designs with large article catalogs should use cursor-based navigation or Experience Cloud native search pages.
- **Reliability** — Empty result sets from misconfigured guest visibility silently masquerade as "no articles found." Defensive Apex with explicit error classification (access error vs. genuinely empty result) improves debuggability. Apex test classes must cover the empty-list path to ensure error handling is validated before deployment.
- **Operational Excellence** — Separate cacheable retrieval methods from non-cacheable voting methods in Apex to avoid runtime failures during deployments. Version the Apex controller carefully — changes to `@AuraEnabled` method signatures are breaking changes for wired LWC components in production.

## Architectural Tradeoffs

**getRecord wire vs. custom Apex SOQL**: `getRecord` uses LDS caching and has lower overhead for known single-record retrieval. Custom SOQL Apex is required for filtered lists, search, and any field not surfaced through standard field API. A component that starts as a detail view (getRecord) and evolves into a filtered list should be refactored to Apex-backed retrieval rather than patched.

**with sharing vs. without sharing on Apex controller**: Using `with sharing` on the Apex controller enforces Salesforce record-level security but will fail silently for guest users who lack sharing access to Knowledge. Using `without sharing` bypasses record sharing entirely and relies solely on data category visibility and field-level security. The correct choice depends on the target surface; guest-only controllers typically use `without sharing` with explicit `IsVisibleInPkb = true` filters as the access gate.

**SOSL vs. SOQL for article search**: SOSL respects data category visibility automatically in the running user's context and searches across all indexed fields including body content. SOQL requires explicit `WITH DATA CATEGORY` clauses but gives more control over filtering and field selection. SOSL is preferred for free-text user-driven search; SOQL is preferred for category-scoped programmatic retrieval.

## Anti-Patterns

1. **Rendering rich text body via innerHTML** — Setting article body content directly on a DOM element's `innerHTML` property bypasses Locker Service sanitization and introduces stored XSS risk. Always use `lightning-formatted-rich-text` in the HTML template.
2. **Relying on admin Experience Builder preview to validate guest access** — Admin preview sessions bypass guest user sharing rules and data category visibility. An LWC that works in admin preview can be completely invisible to actual guest users. Guest access must always be validated in an incognito browser session against the live or preview site URL.
3. **Combining DML-equivalent voting with cacheable Apex** — Annotating a voting method `@AuraEnabled(cacheable=true)` causes a runtime exception because `KbManagement.PublishingService.rateKnowledgeArticle` is a DML-equivalent operation. Retrieval and mutation must always reside in separate methods with separate cacheability declarations.

## Official Sources Used

- Knowledge Developer Guide (Spring '26) — https://developer.salesforce.com/docs/atlas.en-us.knowledge_dev.meta/knowledge_dev/
- SOQL WITH DATA CATEGORY Clause — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_with_datacategory.htm
- KbManagement.PublishingService Apex Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_kb_PublishingService.htm
- LWC Wire Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-about.html
- lightning/uiRecordApi getRecord — https://developer.salesforce.com/docs/platform/lwc/guide/reference-wire-adapters-record.html
- Experience Cloud Guest User Access — https://help.salesforce.com/s/articleView?id=sf.networks_guest_user_access.htm
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- lightning-formatted-rich-text Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-formatted-rich-text.html
