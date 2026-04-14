---
name: api-led-connectivity-architecture
description: "Use this skill when designing API-led connectivity architecture for Salesforce integrations — covering System/Process/Experience layer separation, governance policy (catalog, versioning, deprecation, rate limits), multi-consumer strategy, and Agentforce Agent Fabric integration. Trigger keywords: API-led connectivity, MuleSoft three-tier, System API, Process API, Experience API, integration layer governance, API versioning policy, Agent Fabric. NOT for individual Apex callout implementation (use integration-pattern-selection), HTTP error response contracts (use api-error-handling-design), or retry backoff mechanics (use retry-and-backoff-patterns)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "need to design a three-tier API architecture with MuleSoft for Salesforce integrations"
  - "multiple consumers need the same backend data and each wants a different response shape"
  - "how should we govern API versioning, deprecation, and rate limits across our integration platform"
  - "Agentforce agents need to call external systems — how do we structure the API layer"
  - "direct system-to-system integrations are creating tight coupling and change management risk"
tags:
  - integration
  - api-led-connectivity
  - mulesoft
  - architecture
  - governance
  - agentforce
  - api-led-connectivity-architecture
inputs:
  - "Number and type of backend systems being integrated (ERP, billing, external SaaS)"
  - "Number and type of consumers (Salesforce UI, mobile apps, Agentforce agents, partner portals)"
  - "Existing API governance maturity (catalog, versioning policies, rate limits)"
  - "Team structure: is there a dedicated integration team or does each project own its integrations"
outputs:
  - "Three-tier API layer assignment for each integration (System / Process / Experience)"
  - "Governance policy: catalog entry requirements, versioning rules, deprecation timeline"
  - "Rate limit design across layers"
  - "Multi-consumer strategy: when to build separate Experience APIs vs share one"
  - "Architecture decision log entry for any layer-skipping decisions"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-14
---

# API-Led Connectivity Architecture

This skill activates when an architect needs to design or evaluate an API-led connectivity architecture for Salesforce integrations using MuleSoft or equivalent middleware. It covers layer assignment, governance policy, multi-consumer strategy, and Agentforce Agent Fabric integration — distinct from the mechanics of individual callout implementation or retry backoff patterns.

---

## Before Starting

Gather this context before designing API layer architecture:

- API-led connectivity assigns every integration to one of three layers: System (backend abstraction), Process (cross-system orchestration), Experience (consumer-tailored). The primary benefit is change isolation: a backend system change requires only a System API update; consumers are shielded.
- Governance is the architect-level concern in this domain. A technically correct three-tier design fails in production if there is no catalog, no versioning policy, and no deprecation timeline. All three are required.
- Agentforce agents consume backends via Experience APIs through MuleSoft Agent Fabric. Agents do not call System or Process APIs directly; routing through Experience APIs provides security control, rate limiting, and schema stability for agent consumers.
- The most common wrong assumption: all integrations require all three layers. Single-consumer, simple pass-through integrations justify a System API only. Adding Process and Experience layers for every integration introduces latency and maintenance overhead without benefit.
- Salesforce acts as BOTH a System-layer endpoint (when other consumers read Salesforce data via a System API) AND an Experience-layer consumer (when Salesforce calls Experience APIs to retrieve or write data to external backends).

---

## Core Concepts

### Three-Tier Layer Model

**System APIs** abstract a single backend system. They expose a stable contract regardless of the underlying system's protocol, schema, or version. One System API per backend system. They are generic — they do not know who is calling or why.

**Process APIs** orchestrate across multiple System APIs to implement a business process. A "Create Order" Process API might call an ERP System API (to create the order), a billing System API (to create an invoice), and a Salesforce System API (to update the opportunity). Process APIs know about business logic; they do not know about the shape the consumer needs.

**Experience APIs** adapt the output of Process or System APIs to the specific needs of one consumer type (mobile app, Salesforce UI, partner portal, Agentforce agent). Experience APIs are consumer-specific: the same underlying Process API may have multiple Experience APIs wrapping it for different consumers. This is where response shaping, field filtering, and consumer-specific rate limits live.

### Governance Requirements

Every API regardless of tier requires four governance artifacts before going to production:

1. **Exchange catalog entry** — discoverable name, description, SLA, owner, contact
2. **Versioning policy** — semantic versioning (MAJOR.MINOR.PATCH); MAJOR version bumps break contract and require consumer migration
3. **Deprecation timeline** — minimum 90 days notice before decommissioning any version; consumers must be notified directly
4. **Rate limits** — designed top-down from Experience API consumer needs; Process and System API limits set to accommodate peak Experience API load plus 20% headroom

Governance without tooling is not governance: every Exchange catalog entry must be enforced at deploy time, not documented in a spreadsheet.

### Agentforce Agent Fabric

Agentforce agents call external systems through MuleSoft Agent Fabric, which connects agents to Experience APIs. The architecture:

- Agent Action → Agent Fabric → Experience API → Process API → System API → Backend
- Experience APIs exposed via Agent Fabric must have explicit agent-specific rate limits (agents can fire many concurrent requests during autonomous task execution)
- Authentication uses OAuth 2.0 with dedicated client credentials per agent — shared credentials are a security anti-pattern
- Agent Fabric provides audit logging of every agent callout; this log is the primary evidence trail for agent governance

### Rate Limit Design (Top-Down)

Rate limits cascade top-down. Design in this order:
1. Set Experience API consumer limit (e.g., mobile app: 1,000 req/min, Agentforce: 500 req/min)
2. Sum all Experience API limits that fan into the Process API; add 20% headroom → Process API limit
3. Sum all Process API limits that call the System API; add 20% headroom → System API limit
4. Validate System API limit is within the backend system's published capacity

Designing bottom-up (starting at the backend) results in System API limits that look correct but allow cascading exhaustion when multiple Experience APIs call the same Process API simultaneously.

---

## Common Patterns

### Pattern: Multi-Consumer with Separate Experience APIs

**When to use:** Multiple consumers (Salesforce UI, mobile, partner portal, Agentforce agent) need data from the same backend but with different response shapes, authentication, or rate limits.

**How it works:**
- One System API per backend system (e.g., `system-erp-orders-api`)
- One Process API per business process (e.g., `process-order-fulfillment-api`)
- One Experience API per consumer type:
  - `experience-salesforce-orders-api` — full order detail for CRM reps
  - `experience-mobile-orders-api` — lightweight summary for mobile app
  - `experience-agent-orders-api` — structured for Agentforce tool schema
- Each Experience API has its own rate limit, authentication client, and catalog entry
- Backend change (ERP schema update) requires updating only `system-erp-orders-api` — all consumers are shielded

**Why not one API for all consumers:** A single shared API requires every consumer to accept the most complex response shape; rate limits apply uniformly and cannot be tuned per consumer; one consumer's traffic pattern can starve others.

### Pattern: Layer-Skip with Architecture Decision Log Entry

**When to use:** A single-consumer, simple read-only integration where a full three-tier stack introduces latency and maintenance cost with no benefit. Example: one Salesforce org reads a single product catalog endpoint from an internal system, with no other consumers and no anticipated consumers.

**How it works:**
- Build a System API only (backend abstraction layer)
- Salesforce calls the System API directly (skipping Process and Experience layers)
- Document the skip decision in the Architecture Decision Log (ADL):
  - Which layers were skipped and why
  - Consumer count (single) and anticipated growth (none)
  - Trigger for re-evaluation (if a second consumer is added, add Experience API within 30 days)

**Why this is acceptable:** Layer-skipping for genuinely simple, single-consumer integrations is not an anti-pattern — it is a documented, intentional tradeoff. The risk is undocumented layer-skipping that never gets revisited when a second consumer appears and the System API is directly exposed to multiple consumers without governance.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single consumer, simple pass-through | System API only; document layer-skip in ADL | All three layers add maintenance cost with no isolation benefit for one consumer |
| Multiple consumers needing same data in different shapes | One Process API + one Experience API per consumer type | Experience APIs isolate consumer-specific shaping and rate limits |
| Agentforce agent calling external backend | Experience API via Agent Fabric; dedicated OAuth client per agent | Agent Fabric provides audit, rate limiting, and security isolation required for autonomous agents |
| Backend system migration (ERP v1 → v2) | Update System API only; no consumer changes required | This is the primary value of System layer — consumers are shielded from backend change |
| Breaking API contract change required | MAJOR version bump; maintain old version for 90-day deprecation window | Semantic versioning + deprecation timeline prevents breaking consumers on surprise |
| Teams asking "do we need all three layers" | Evaluate consumer count and anticipated growth; document decision | Prescribing all three layers always is an LLM anti-pattern — use ADL to make the tradeoff explicit |

---

## Recommended Workflow

1. **Inventory integrations and consumers.** List every backend system being integrated and every consumer type (Salesforce apps, mobile, agents, partners). Identify which consumers share the same backend and whether their response shape requirements differ.
2. **Assign each integration to a tier.** Apply the three-tier model: one System API per backend; one Process API per cross-system business process; one Experience API per distinct consumer type. For single-consumer pass-through integrations, document the layer-skip decision in the ADL.
3. **Design rate limits top-down.** Start from Experience API consumer limits; calculate Process and System API limits by summing consumer fanout plus 20% headroom. Validate against backend system capacity.
4. **Define governance requirements for each API.** For every API: create Exchange catalog entry with owner and SLA, define versioning policy (semantic versioning), document deprecation timeline (minimum 90 days), and set rate limits.
5. **Design Agentforce integration points.** For any Agentforce agent that calls external systems: route through Agent Fabric to an Experience API with dedicated OAuth client credentials and agent-specific rate limits; confirm audit logging is enabled.
6. **Review for anti-patterns.** Check: no layer-skipping without ADL entry; no shared credentials across consumers; no rate limits designed bottom-up; no Experience APIs exposing raw System API responses without shaping.
7. **Document architecture decisions.** Record every layer-skip decision, versioning policy exception, and rate-limit tradeoff in the ADL so future maintainers understand why the architecture looks the way it does.

---

## Review Checklist

- [ ] Every integration assigned to correct tier (System / Process / Experience) or layer-skip documented in ADL
- [ ] One System API per backend system (not per consuming team)
- [ ] Separate Experience APIs for consumers with different response shape, rate limit, or auth requirements
- [ ] Agentforce agents routed via Agent Fabric with dedicated OAuth client per agent
- [ ] Rate limits designed top-down (Experience → Process → System)
- [ ] Exchange catalog entry exists for every API (name, owner, SLA, contact)
- [ ] Versioning policy defined (semantic versioning, MAJOR = breaking change)
- [ ] Deprecation timeline documented (minimum 90 days) for any API being decommissioned
- [ ] No undocumented layer-skipping

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **LLMs prescribe all three layers for every scenario** — Applying System + Process + Experience to a single-consumer, simple pass-through integration is over-engineering that adds latency (three network hops instead of one) and three times the maintenance surface. For single-consumer integrations with no anticipated second consumer, a System API only is the correct architecture. Document it in the ADL so it is not mistaken for a governance gap later.

2. **Salesforce is both a System-layer endpoint AND an Experience-layer consumer** — Teams that treat Salesforce as only a consumer miss the requirement to expose Salesforce data through a System API for other systems to consume. If the ERP needs to read Salesforce opportunity data, that flow requires a Salesforce System API. Failing to design this layer forces the ERP to call Salesforce directly with its own credentials and schema assumptions — creating hidden coupling.

3. **Rate limits not propagated down — cascade exhaustion** — If Experience API rate limits are set without calculating the Process and System API load they generate, a peak usage event can exhaust Process or System API limits while all Experience APIs appear within limit. Top-down rate limit design prevents this. This is particularly acute when Agentforce agents fan out many concurrent Experience API calls during autonomous task execution.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| API layer assignment matrix | Table mapping each integration to System / Process / Experience tier with rationale |
| Governance policy document | Exchange catalog requirements, versioning policy, deprecation timeline per API |
| Rate limit design | Top-down calculation from consumer limits to System API limits |
| Architecture Decision Log entries | ADL entries for every layer-skip decision and policy exception |
| Agentforce integration design | Agent Fabric route, OAuth client assignments, rate limits for agent consumers |

---

## Related Skills

- `integration/integration-pattern-selection` — upstream pattern selection before layer design
- `integration/api-error-handling-design` — HTTP error response contracts within API layers
- `integration/error-handling-in-integrations` — orchestration-layer error handling after the API layer is designed
- `integration/retry-and-backoff-patterns` — HTTP retry backoff for callouts within Experience or System APIs
