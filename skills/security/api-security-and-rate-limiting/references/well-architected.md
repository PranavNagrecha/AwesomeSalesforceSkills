# Well-Architected Notes — API Security and Rate Limiting

## Relevant Pillars

- **Security** — Core pillar for this skill. Connected App scope restriction and IP enforcement directly reduce the attack surface of API integrations. Overly broad scopes and absent IP restrictions are the two most common API-layer security weaknesses. Principle of least privilege applies to both OAuth scopes (grant minimum required) and network access (enforce IP ranges for all server-to-server apps). Session policies (IP locking, short timeouts) add defense-in-depth in case credentials are compromised.

- **Operational Excellence** — API usage monitoring, 429 retry strategies, and daily limit management are operational concerns that directly affect integration reliability. Proactive monitoring via Event Log Files and Setup metrics enables teams to detect limit exhaustion before it causes downstream failures. Bounded retry logic with `Retry-After` respect prevents integrations from amplifying a limit problem into a full outage.

- **Reliability** — Rate limit handling directly affects integration reliability. An integration that retries indefinitely on `REQUEST_LIMIT_EXCEEDED` will not recover without human intervention. An integration that ignores `Retry-After` headers will continue to fail until the rate spike clears on its own schedule. Resilient integrations differentiate transient limits (429) from terminal limits (daily exhaustion) and respond appropriately to each.

- **Performance** — Concurrent API limit management intersects with performance. Long-running API requests (over 20 seconds) consume the concurrent limit budget. Optimizing query performance and automating with Bulk API for high-volume operations reduces concurrent limit exposure.

## Architectural Tradeoffs

**Strict IP restriction vs. operational flexibility:** Enforcing login IP ranges on every request is the strongest control but requires all integration servers to have static, predictable IPs. Cloud-native or serverless integrations (AWS Lambda, Azure Functions, GCP Cloud Run) run from dynamic IPs and cannot use strict IP restriction without adding a NAT gateway or proxy. Teams must decide whether the operational cost of static IPs or NAT infrastructure is justified by the security gain. For integrations handling PII or sensitive financial data, the cost is generally justified.

**Short session timeout vs. long-running operations:** Short access token lifetimes (15–60 minutes) reduce the window during which a stolen token is usable. But long-running batch jobs may need a session that outlasts the typical timeout. The right resolution is to implement re-authentication via refresh tokens at job checkpoints, not to simply raise the session timeout to accommodate the worst-case job duration. Re-auth at checkpoints is more complex to implement but does not sacrifice the security benefit of short session lifetimes.

**Event Monitoring cost vs. observability depth:** Event Log Files require the Event Monitoring add-on, which has a licensing cost. Without it, API monitoring is limited to summary-level counters. For orgs handling significant API volume or sensitive data, the cost of Event Monitoring is justified by the ability to trace every API call to a specific user, app, and endpoint. Without this visibility, API limit incidents and potential unauthorized access are difficult or impossible to investigate.

## Anti-Patterns

1. **Granting `full` OAuth scope to all integrations** — `full` scope is functionally equivalent to granting the integration user's entire permission set, including any future permission additions. It also enables access to some administrative capabilities beyond pure data access. Correct approach: default to `api` + `refresh_token offline_access` for all headless integrations; add narrower scopes only when a specific technical requirement demands them.

2. **Using "Relax IP restrictions" for server-to-server integrations** — this effectively disables network-level API access control for the Connected App. Relaxation policies exist for user-facing apps where users travel and connect from varied IPs. Server-to-server integrations always run from known networks and have no legitimate reason to relax IP enforcement. Correct approach: always use "Enforce login IP ranges on every request" for machine integrations, paired with explicit CIDR ranges on the Connected App.

3. **Treating all non-200 API responses as retriable** — integrations that retry on any error without inspecting the error code will loop indefinitely when the daily limit is exhausted, amplify concurrent limit problems, and generate misleading monitoring noise. Correct approach: classify errors at the response level — 429 is retriable with backoff; `REQUEST_LIMIT_EXCEEDED` is not retriable within the same day; 5xx errors may be retriable depending on type.

## Official Sources Used

- Salesforce Security Guide — Connected Apps, OAuth scope definitions, IP restrictions, and session policies: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- REST API Developer Guide — API request limits, rate limiting behavior, concurrent limits, and 429 handling: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Salesforce Well-Architected Overview — Security pillar (least privilege, credential protection) and Operational Excellence pillar (monitoring, resilience): https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Event Monitoring documentation — EventLogFile object, API event type, and monitoring patterns: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/using_resources_event_log_files.htm
- Salesforce Help: API Request Limits and Allocations — https://help.salesforce.com/s/articleView?id=sf.integrate_api_rate_limiting.htm&type=5
- Salesforce Help: Connected App OAuth Policies — https://help.salesforce.com/s/articleView?id=sf.connected_app_manage_oauth.htm&type=5
