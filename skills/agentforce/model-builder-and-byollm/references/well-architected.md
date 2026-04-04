# Well-Architected Notes — Model Builder and BYOLLM

## Relevant Pillars

- **Security** — The primary pillar for this skill. External LLM credentials (API keys) must be stored exclusively in Named Credentials via External Credentials. Keys must never appear in plaintext in model configuration fields, custom metadata, or debug logs. Named Credential access must be scoped to only the users and processes that require it via Permission Sets. Rotating an API key must be a single, auditable change to the External Credential Principal — not a search-and-replace across multiple configuration records. The Trust Layer (a separate skill) governs how model outputs are inspected, masked, and logged; Model Builder governs the credential and connection layer.

- **Operational Excellence** — The second primary pillar. Model alias configuration is global and immediate; any change must be planned, tested in isolation, and deployed with a runbook. Environment parity (sandbox to production) is a manual responsibility — teams must script or document every registration step to prevent configuration drift. Provider-side rate limits are invisible within Salesforce and require external monitoring. Model capability verification (function calling, context window) must be part of the deployment checklist rather than discovered at runtime.

- **Reliability** — External LLM availability introduces an external dependency into Agentforce and Einstein features. Provider outages, rate limit exhaustion, or credential expiry can silently degrade features that would otherwise function correctly. Reliability patterns include: monitoring provider health dashboards, maintaining a fallback model alias that uses a Salesforce-standard model for critical features, and documenting the blast radius of each alias (which features break if it fails).

- **Performance** — Model selection directly affects latency and throughput. Frontier models (GPT-4o, Claude 3.5 Sonnet) have higher per-call latency than mid-tier models. High-concurrency Agentforce features that call external models must account for provider-side latency variance under load. Context window management (truncating unnecessary prompt content) reduces both latency and token cost.

- **Scalability** — External provider rate limits are the primary scalability ceiling for BYOLLM deployments. Token-per-minute (TPM) and requests-per-minute (RPM) limits must be sized against peak concurrent usage before going live. Salesforce-standard models do not impose the same external rate-limit constraints and may be more appropriate for high-scale, lower-complexity use cases.

---

## Architectural Tradeoffs

**BYOLLM vs. Salesforce-Standard Models:**
Using BYOLLM gives organizations control over model version, provider, and data residency, but introduces operational complexity: credential management, rate limit monitoring, sandbox-to-production deployment, and provider-side SLA dependency. Salesforce-standard models are simpler to operate but offer less control over model version cadence and data routing. Organizations with strict compliance requirements typically accept the BYOLLM operational overhead; organizations prioritizing simplicity should default to standard models.

**Shared Alias vs. Feature-Specific Aliases:**
A single shared alias for all features minimizes configuration surface area but creates a high blast radius — one alias change affects everything. Feature-specific aliases (e.g., separate aliases for agentic tasks, summarization, and classification) increase configuration overhead but enable targeted model optimization and limit the impact of any single alias update. For organizations with more than three distinct AI use cases, feature-specific aliases are the recommended pattern.

**Credential Granularity — Org-Level vs. Per-User Principal:**
Most BYOLLM deployments use an org-level (service account) principal in the External Credential, meaning all calls to the external provider use the same API key. Per-user principals allow individual user-level API key assignment, which supports per-user usage tracking and key scoping, but adds key distribution and rotation complexity. Org-level principals are appropriate for most use cases; per-user principals are warranted only when provider billing or compliance requires per-user attribution.

---

## Anti-Patterns

1. **Storing API keys outside Named Credentials** — Placing provider API keys in custom metadata, custom settings, configuration fields, or any location other than an External Credential Principal. API keys in custom metadata are visible to admins, included in sandbox refreshes, and may appear in debug logs. Named Credentials encrypt key values and enforce them as the exclusive delivery path for outbound authenticated requests. Any key outside Named Credentials violates the Trust Layer security model and creates audit exposure.

2. **Updating the shared production alias without isolated testing** — Using the production model alias as a test target for new models. Because the alias change is global and immediate, this risks degrading all features simultaneously. The correct pattern is always: new alias → sandbox test → production promotion → shared alias update (if appropriate) → verification.

3. **No retrain or model version monitoring** — Registering an external model at a specific version and never reviewing whether the provider has deprecated that version or changed its capabilities. Provider model deprecations typically surface as sudden feature failures rather than gradual degradation. Monitor provider changelogs and deprecation notices, and include model version review in the quarterly architecture review cadence.

---

## Official Sources Used

- Salesforce Help: Model Builder Overview — https://help.salesforce.com/s/articleView?id=sf.model_builder_intro.htm
- Salesforce Developer Guide: Model Builder — https://developer.salesforce.com/docs/einstein/genai/guide/model-builder.html
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services Overview — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help: Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
