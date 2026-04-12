# Well-Architected Notes — AI Model Integration Apex

## Relevant Pillars

### Performance

AI model callouts are among the most latency-expensive operations available in Apex. Each callout adds hundreds of milliseconds of wall-clock time to a transaction. The key performance risks are: (1) redundant token fetches for legacy Einstein services when Platform Cache is absent, which doubles callout count per transaction; (2) synchronous per-record AI calls in bulk contexts that exhaust either the callout limit or the wall-clock timeout (120 seconds per callout, 10 minutes total for async jobs); and (3) blocking trigger transactions on AI latency when the AI result is not required before the record is committed. Queueable decoupling and Platform Cache token reuse are the primary performance mitigations.

### Security

The `aiplatform.ModelsAPI` wrapper handles authentication internally via the Einstein Trust Layer, but caller code must still respect data minimization — prompt content sent to the model should contain only the data necessary for the task. Legacy Einstein Platform Services use a JWT bearer token that must be stored and managed safely; the token should be held in Platform Cache (which is org-internal) and never logged, serialized to a field, or exposed via a public REST endpoint. Named Credentials should be used as the callout endpoint for token acquisition rather than hardcoded URLs. Responses from models must not be stored in fields visible to users without appropriate field-level security review, especially if the prompt included PII.

### Reliability

AI model endpoints can fail, throttle, return non-200 status codes, or time out. Any production integration must treat the AI callout as an unreliable external dependency. Reliability design requires: null-safe response parsing, meaningful error logging on non-200 paths, graceful degradation (a default value or a retry signal) when the model is unavailable, and asynchronous processing for bulk workloads so a single model failure does not roll back an entire trigger batch. Queueable chains that record per-record failure state allow partial success rather than all-or-nothing outcomes.

## Architectural Tradeoffs

**Synchronous versus asynchronous:** Synchronous AI calls give immediate results but bind latency and callout limits to the triggering transaction. Asynchronous Queueable processing decouples AI enrichment from the user transaction and scales gracefully, but introduces a delay between record creation and AI result availability. Choose synchronous only when the AI response is required before the record can be considered complete (e.g. a form submission that must validate content with a model before saving).

**Cache granularity:** Caching the token (for legacy Einstein) is always correct. Caching model responses is a more complex tradeoff — cached responses avoid repeated callouts for identical inputs but may serve stale AI results if the model is updated or prompt context changes. Cache model responses only when inputs are deterministic and the response does not need to reflect model version changes within the cache TTL.

**Model API name coupling:** `aiplatform.ModelsAPI` uses a model API name string at call time (e.g. `sfdc_ai__DefaultOpenAIGPT4OmniMini`). Hardcoding this string scatters a configuration value across classes. Store the model API name in a Custom Metadata Type or Custom Setting so it can be changed without a code deployment when the org's model configuration changes.

## Anti-Patterns

1. **Synchronous per-record AI callout in a trigger** — violates the callout-per-transaction limit at scale and couples user transaction latency to external AI response time. Move to async Queueable.
2. **Token fetch without Platform Cache** — doubles callout budget and Einstein Request entitlement burn for every legacy Einstein API transaction. Always use cache-aside token management.
3. **Hardcoded model API name in Apex classes** — makes model changes require a code deployment. Use Custom Metadata or Custom Settings for model configuration values.

## Official Sources Used

- Access Models API with Apex — Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/access-models-api-with-apex.html
- Einstein Platform Services Developer Guide — https://metamind.readme.io/docs/intro-to-einstein-platform-services
- Apex Developer Guide — Named Credentials as Callout Endpoints — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
