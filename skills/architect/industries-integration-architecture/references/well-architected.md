# Well-Architected Notes — Industries Integration Architecture

## Relevant Pillars

- **Reliability** — Industries integration architectures must decouple Salesforce UI availability from external backend availability. The one-way CIS sync pattern and async IP callout designs directly implement this principle: agents can complete service enrollments even when CIS or the policy admin system is in a maintenance window. Error handling IP elements on every external callout path ensure that transient backend unavailability produces a graceful user message rather than a hard OmniScript failure.
- **Security** — All external callouts from Integration Procedures must use Named Credentials (not hardcoded URLs or credentials in IP metadata). OAuth 2.0 client_credentials or JWT-based auth should be used for machine-to-machine calls to policy admin systems and BSS/OSS endpoints. CIS-sourced fields must be locked via Field-Level Security to prevent unauthorized Salesforce edits from corrupting data that the CIS owns. Named Credential scopes should follow least-privilege: one credential per system and API family, not a single broad-scope credential for all external calls.
- **Performance** — Synchronous Integration Procedure HTTP Actions are subject to Salesforce callout governor limits and OmniScript session timeouts. Long-running external calls must be moved to async patterns (Async Apex + Platform Events) to prevent session timeouts. The CIS rate plan local-sync pattern eliminates per-OmniScript-step callouts to CIS, improving guided process render times from seconds to sub-100ms SOQL.
- **Adaptability** — Using the correct forward-compatible pattern for Communications Cloud (Direct TM Forum API Access) ensures the architecture does not require forced re-design at Winter '27. Keeping Salesforce as an engagement-only layer for insurance and E&U makes it possible to swap the external backend (e.g., migrate from one policy admin system to another) without changing Salesforce data models — only the Named Credential and IP action chain need updating.

## Architectural Tradeoffs

**Engagement-layer read-only vs. dual-write:**
Making Salesforce a read-only projection of backend operational data (policy state, rate plans) eliminates dual-write conflicts at the cost of a sync latency window. For most insurance and E&U use cases, a daily or event-driven sync is acceptable — agents understand that data reflects the last sync. If real-time policy state is required, design the OmniScript read path as a live IP callout (accepting the callout latency) rather than a stale local cache, and keep the local Salesforce record out of the picture entirely.

**Integration Procedure vs. Apex for external callouts:**
Integration Procedures are preferred for standard synchronous callouts because they are declarative, deployable as OmniStudio metadata, and do not require Apex test coverage. Apex is required when callout behavior needs branching logic that exceeds IP action chain capabilities, or when callouts must be async. When Apex is chosen, it must be invoked from the IP as an `Apex Action` element — the IP remains the integration runtime entry point from the OmniScript layer.

**Direct TM Forum API vs. MuleSoft Gateway (Communications):**
The MuleSoft Gateway provided a mediation layer for protocol transformation and API virtualization. Direct Access removes this layer, which means the BSS/OSS TM Forum API must be reachable from Salesforce's IP range and must expose standard TM Forum API contracts without Salesforce-specific transformation. For BSS/OSS systems that do not natively support TM Forum APIs, a lightweight API adapter is still required — but it should not be the deprecated MuleSoft Gateway pattern; it should be an independently managed adapter service with its own lifecycle.

## Anti-Patterns

1. **Salesforce Industries as operational system of record** — Attempting to make Salesforce the authoritative owner of policy premiums, rate plan definitions, order fulfillment status, or billing balances in addition to or instead of the backend system. This creates dual-write conflicts, requires complex reconciliation logic, and violates the architectural intent of every Salesforce Industries cloud. The external backend (PAS, BSS, CIS) is always the authority for its operational domain.

2. **MuleSoft Gateway path for new Communications Cloud integrations** — Starting a new Communications Cloud ↔ BSS/OSS integration on the MuleSoft API Gateway path after the deprecation announcement. This requires a full re-architecture to Direct Access before Winter '27, which is a high-cost migration at a forced deadline. All new Communications Cloud BSS/OSS integrations must use Direct TM Forum API Access.

3. **Synchronous live callout to CIS or PAS on every OmniScript step render** — Calling an external backend system synchronously on every OmniScript step render (e.g., for rate plan lookup on a service enrollment form) makes the Salesforce guided process dependent on backend availability and response time. Use the local-sync pattern for reference data and reserve live callouts for transactional writes.

## Official Sources Used

- Energy and Utilities Cloud Developer Guide Spring '26 — E&U architecture, CIS integration, ServicePoint and RatePlan objects — https://developer.salesforce.com/docs/atlas.en-us.energy_and_utilities.meta/energy_and_utilities/eu_overview.htm
- Communications Cloud TM Forum API Overview — TM Forum API layer, Direct Access pattern, BSS/OSS integration — https://developer.salesforce.com/docs/industries/communications/guide/get-started.html
- OmniStudio Integration Architectures (Salesforce Architects) — Integration Procedure patterns, OmniStudio integration topology diagrams — https://architect.salesforce.com/diagrams/reference-architectures/omnistudio-integrations
- OmniStudio Integration Procedure Developer Guide — IP action chains, HTTP Action, DataRaptor, error handling, versioning — https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omniintegrationprocedure.htm
- Salesforce Well-Architected Overview — Architecture quality framing, reliability, adaptability, security pillars — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Integration Patterns (Salesforce Architects) — Synchronous vs asynchronous integration tradeoffs, system-of-record selection — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
