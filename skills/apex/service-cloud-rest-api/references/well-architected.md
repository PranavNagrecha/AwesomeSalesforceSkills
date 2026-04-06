# Well-Architected Notes — Service Cloud REST API

## Relevant Pillars

- **Security** — The two Knowledge REST API endpoint families have fundamentally different authentication models. `/knowledgeManagement/` requires a valid session and must never be called from a guest/unauthenticated context. `/support/knowledgeWithSEO/` relies on the Experience Cloud site guest profile and data category visibility settings. OAuth access tokens for MIAW Enhanced Chat API must be scoped to the minimum required permissions (typically `chatbot` or `messaging` scopes) and must never be embedded in client-side JavaScript. Legacy Chat REST API session keys (X-LIVEAGENT-SESSION-KEY) must be treated as short-lived credentials and not cached.
- **Trusted (Reliability)** — The permanent retirement of the legacy Chat REST API on February 14, 2026 is an irreversible platform change with no grace period. Orgs that did not complete migration face immediate service disruption. Any integration architecture that uses the Knowledge REST API must handle the empty-array silent-failure case for data category mismatches to avoid presenting blank content to users without any observable error.
- **Adaptable** — Using URL-name-based article lookup (v44+) instead of article ID-based lookup decouples integrations from internal Salesforce record IDs that can change on re-publication. This is the architecturally stable access pattern for article permalinks in Experience Cloud sites and external portals.
- **Performance** — Knowledge REST API calls from Apex count against governor limits for callouts (100 per transaction, 120 seconds total). For Experience Cloud pages that load multiple article-related components, consolidate Knowledge REST calls in a single Apex controller method rather than making per-component callouts. Cache article content in Platform Cache for frequently accessed articles to reduce callout volume.
- **Operational Excellence** — Log the `total` field from Knowledge REST responses to detect silent data category mismatches early. Include API version in endpoint URLs explicitly rather than relying on defaults — this prevents unintended behavior changes when the org's default API version is upgraded.

## Architectural Tradeoffs

**`/knowledgeManagement/` vs. `/support/knowledgeWithSEO/`**

The choice of endpoint family is not a preference — it is determined entirely by the authentication context. Using the authoring endpoint in a guest context is an error, not a tradeoff. Using the guest endpoint in an authenticated context is valid but loses access to draft articles and internal-only fields. The correct architecture: use `/knowledgeManagement/` for agent-assist and case deflection in authenticated Salesforce UIs; use `/support/knowledgeWithSEO/` for all Experience Cloud and external portal surfaces.

**MIAW Enhanced Chat API vs. Apex-Managed Chat Logic**

The MIAW Enhanced Chat API handles conversation state, routing, and persistence as a platform capability. Implementing equivalent logic in Apex (polling for messages, managing session state) re-creates platform functionality that Salesforce already provides and maintains. The correct architecture delegates conversation lifecycle to the MIAW platform and uses Apex only for business logic hooks (e.g., pre-chat data validation, post-chat case creation).

**Data Category Visibility: API-Enforced vs. Apex-Enforced**

Data category visibility for Knowledge articles is enforced by the REST API layer — not by Apex sharing rules. An Apex class with `without sharing` that calls `/support/knowledgeWithSEO/` does not bypass data category visibility. This is architecturally correct: visibility rules are consistently enforced regardless of Apex sharing keywords, but it means that debugging access issues requires checking Setup configuration rather than Apex code.

## Anti-Patterns

1. **Hardcoding Salesforce record IDs for Knowledge article links** — Article IDs change when articles are re-published (new version creates a new record). URL names are the stable, human-readable identifier for article permalinks. All external links and cross-references to Knowledge articles should use URL-name-based lookups via `/support/knowledgeWithSEO/articles?urlName=<slug>` rather than `?id=<recordId>`.

2. **Using SOQL on `Knowledge__kav` as a replacement for the Knowledge REST API in Experience Cloud** — SOQL queries from an Apex controller do not enforce data category visibility for guest users in the same way the REST API does. The REST API's visibility enforcement is the authoritative, officially documented behavior for guest Knowledge access. Using SOQL as a shortcut bypasses this layer and can expose articles that should be restricted by data category visibility.

3. **Maintaining the legacy Chat REST API through a proxy or wrapper post-retirement** — Any proxy layer that forwards requests to the retired `/chat/rest/` endpoint will receive the same errors as direct callers. Wrapping a retired endpoint does not restore functionality; it adds latency and failure surface. The only correct path is migration to the MIAW Enhanced Chat API.

## Official Sources Used

- Knowledge REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.knowledge_dev.meta/knowledge_dev/knowledge_rest_intro.htm
- Enhanced Chat API Overview (Messaging for In-App and Web) — https://developer.salesforce.com/docs/service/enhanced-messaging/overview
- Chat REST API Developer Guide (legacy — retired) — https://developer.salesforce.com/docs/atlas.en-us.live_agent_rest.meta/live_agent_rest/live_agent_rest_intro.htm
- Salesforce REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Salesforce Well-Architected: Adaptable — https://architect.salesforce.com/docs/architect/well-architected/guide/adaptable.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
