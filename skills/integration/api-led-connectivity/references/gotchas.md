# Gotchas -- API-Led Connectivity

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Salesforce Callout Timeout Covers the Entire Chain, Not Each Hop

**What happens:** Salesforce enforces a 120-second maximum timeout on a single HTTP callout. When an Experience API calls a Process API which calls a System API, the entire chain must complete within 120 seconds as measured from Salesforce. There is no way to extend this limit.

**When it occurs:** Deep API chains with slow backends (mainframes, batch-oriented ERPs) or high-latency networks. Adding a third layer can push the total round-trip time past the 120-second wall.

**How to avoid:** Measure end-to-end latency across all API layers before going live. If the chain approaches the timeout, consider collapsing layers, caching at the Process layer, or switching to an asynchronous pattern (fire-and-forget with Platform Events or callback).

---

## Gotcha 2: External Services Schema Size Limit Blocks Large API Specs

**What happens:** Salesforce External Services requires an OpenAPI 2.0 or 3.0 spec to register an API. The spec must be under approximately 100,000 characters. API specs for Process or Experience APIs with many operations, deeply nested schemas, or verbose descriptions exceed this limit and fail to register.

**When it occurs:** When a Process API aggregates many System APIs and exposes a broad surface area. The OpenAPI spec grows large even if Salesforce only needs a few operations.

**How to avoid:** Build Experience APIs with a minimal spec that exposes only the operations Salesforce needs. Do not register the full Process API spec in External Services -- create a consumer-specific subset. Alternatively, use Apex callouts with manual JSON parsing if the spec cannot be reduced.

---

## Gotcha 3: Rate Limits Are Per-API, Not Per-Layer -- Cascading Exhaustion

**What happens:** MuleSoft Anypoint API Manager enforces rate limits (via SLA-based policies) at individual API endpoints. A burst of traffic to an Experience API generates amplified traffic to the Process API (if it fans out to multiple System APIs). The Process or System API rate limit is exhausted before the Experience API limit is reached.

**When it occurs:** Fan-out patterns where one Experience API call triggers multiple Process or System API calls. Also occurs when multiple Experience APIs share the same Process API.

**How to avoid:** Design rate limits top-down. The Experience API limit should be set so that worst-case amplification does not exceed downstream limits. Use circuit breakers at the Process layer to fail fast when a System API is throttled rather than queuing requests.

---

## Gotcha 4: API Version Drift Across Layers Causes Silent Field Omission

**What happens:** A System API that wraps Salesforce REST API is pinned to API version v58.0. A new custom field added in v62.0 is included in the Process API's data model. The System API silently excludes the field because v58.0 does not know about it. The Experience API returns null for the field with no error.

**When it occurs:** When API layers are maintained by different teams with independent release cycles, and there is no cross-layer version compatibility check.

**How to avoid:** Establish a version policy: all layers referencing Salesforce APIs must use the same API version or a version no more than two releases behind the current release. Include version validation in CI/CD pipeline tests.

---

## Gotcha 5: Named Credential Per-User vs. Per-Org Auth Breaks in Multi-Layer Chains

**What happens:** When Salesforce calls an Experience API using a Named Credential configured for per-user OAuth, the credential maps to the running user's token. In headless contexts (scheduled jobs, Platform Event triggers, Agentforce agent actions), there is no interactive user to authorize the credential, and the callout fails with an authentication error.

**When it occurs:** Architectures that use per-user Named Credentials for API-led callouts and then extend the integration to asynchronous or agent-driven contexts.

**How to avoid:** Use per-org (Named Principal) credentials for API-led integrations unless user-level authorization is a hard requirement. If per-user auth is needed, ensure that the running context always has a valid authorized user, or fall back to a service account credential for headless execution paths.
