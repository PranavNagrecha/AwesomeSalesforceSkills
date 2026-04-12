# Gotchas — AI Model Integration Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: aiplatform.ModelsAPI Counts Against Einstein Request Entitlements AND Callout Limits

**What happens:** Every call to `aiplatform.ModelsAPI.createGenerations()`, `createChatGenerations()`, or `createEmbeddings()` consumes one Einstein Request entitlement credit in addition to one callout toward the 100-callout-per-transaction governor limit. The External Services wrapper abstracts the authentication but does not abstract the cost. Orgs running high-frequency synchronous AI calls can exhaust hourly Einstein Request limits before they hit the Apex callout limit, making the org appear to be down from a model perspective while all other integrations continue working.

**When it occurs:** Any synchronous Apex code path that calls ModelsAPI once per record in a bulk context — triggers, invocable methods called from Flow with high-volume records, or batch execute methods with a scope larger than safe callout budget.

**How to avoid:** Estimate Einstein Request consumption at the expected transaction volume before deploying. For bulk contexts, use a Queueable chain that processes a small fixed slice per execution (5–10 records), keeping both callout count and entitlement burn proportional to Queueable throughput rather than trigger batch size. Monitor Einstein Request usage via the Einstein Usage dashboard in Setup.

---

## Gotcha 2: Legacy Einstein Vision/Language JWT Tokens Do Not Auto-Refresh; Apex Must Manage Token Lifecycle via Platform Cache

**What happens:** The Einstein Platform Services token endpoint issues a JWT with a fixed validity window (typically 60 minutes). The token does not auto-renew. If Apex fetches a fresh token on every transaction, each AI callout actually burns two callouts: one for the token endpoint and one for the model endpoint. Under concurrent load — 30 users each triggering an AI call — this produces 60 callouts rather than 30, which can double per-hour entitlement burn and leave the org susceptible to hitting Einstein Request limits before the model calls are the bottleneck.

**When it occurs:** Any legacy Einstein Vision or Language integration that constructs the token inline rather than checking a shared cache. Most common in patterns copied from quick-start documentation that omit caching for simplicity.

**How to avoid:** Always wrap token acquisition in a `Cache.Org` cache-aside pattern. Set the cache TTL to 30–60 seconds less than the token's actual validity window to guarantee the cache never serves an expired token. The token string is org-wide and non-sensitive in the context of cache storage (it is short-lived and scoped to the Einstein platform). A single Apex token service class should centralize all token access; no other class should call the token endpoint directly.

---

## Gotcha 3: Bulk AI Processing Must Use Asynchronous Queueable Chains — Not Synchronous Trigger Logic

**What happens:** Developers moving from REST-only integrations often underestimate the callout count impact of per-record AI processing. A trigger on Account processing a batch of 150 inserted records that each needs one `createChatGenerations` call will throw `System.LimitException: Too many callouts: 101` at record 101, rolling back all DML in the transaction and leaving all 150 records without AI enrichment. There is no partial commit — the entire batch fails.

**When it occurs:** Any synchronous trigger, test-level loop, or batch execute block that calls an AI model once per record without checking `Limits.getCallouts()` or constraining the scope.

**How to avoid:** Move bulk AI processing to a Queueable class implementing `Database.AllowsCallouts`. Size each Queueable execution to a slice of 5–10 records, well below the 100-callout limit. Trigger logic should only enqueue the Queueable; it must not make the callout itself. For batch processing, set the batch scope to a value where callouts per execute stay under 100 and add `Database.AllowsCallouts` to the Batch class interface.

---

## Gotcha 4: ModelsAPI Code200 Is Null on Non-200 Model Responses — Null Traversal Produces NPE, Not a Meaningful Error

**What happens:** The External Services-generated response type for `aiplatform.ModelsAPI` routes responses to different typed fields based on HTTP status. A model quota-exceeded response (429), a model error (500), or a throttle response arrives as a non-200 status and populates a different response path, leaving `response.Code200` as null. Code that directly accesses `response.Code200.generation.generatedText` without null-checking throws a NullPointerException that surfaces as a generic Apex exception, obscuring the actual failure reason.

**When it occurs:** Every `aiplatform.ModelsAPI` callout that does not null-check the status-specific response field before accessing nested properties.

**How to avoid:** Always null-check `response.Code200` immediately after the call. Log the full response object when `Code200` is null to capture the actual status code and error detail. Wrap the callout in a try-catch for `aiplatform.ModelsAPI.createChatGenerationsException` (or the equivalent for `createGenerations` and `createEmbeddings`) to handle typed API errors separately from generic exceptions. Treat any non-null Code200 path as the success path only.
