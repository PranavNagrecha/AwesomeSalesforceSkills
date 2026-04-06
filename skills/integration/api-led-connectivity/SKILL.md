---
name: api-led-connectivity
description: "Use when designing a multi-system integration architecture using the three-layer API-led connectivity pattern (System, Process, Experience APIs), deciding how many layers to apply, mapping Salesforce as a system-layer endpoint or experience-layer consumer, or evaluating how Agentforce and MuleSoft Agent Fabric leverage API-led patterns. Triggers: 'API-led connectivity', 'system API process API experience API', 'MuleSoft integration layers', 'application network'. NOT for configuring MuleSoft Anypoint Salesforce Connector flows (use mulesoft-salesforce-connector). NOT for Salesforce REST API CRUD patterns (use rest-api-patterns). NOT for event-driven architecture without an API layer (use event-driven-architecture-patterns)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Security
triggers:
  - "how do I structure my integration layers so Salesforce is not point-to-point with every backend"
  - "should I always build all three API layers or can I skip the process layer"
  - "how does Agentforce consume APIs through MuleSoft Agent Fabric"
  - "how do I expose SAP or ERP data to Salesforce through a reusable API layer"
  - "what is the difference between system API, process API, and experience API"
  - "how do I avoid building a monolithic integration that breaks when one backend changes"
  - "API-led connectivity three layer architecture system process experience API"
  - "three layer API architecture for Salesforce integration"
tags:
  - api-led-connectivity
  - mulesoft
  - system-api
  - process-api
  - experience-api
  - application-network
  - integration-architecture
  - agent-fabric
inputs:
  - "inventory of backend systems (ERP, databases, SaaS) that must participate in the integration"
  - "list of consumer channels (Salesforce UI, mobile app, partner portal, Agentforce agent)"
  - "data volume and latency requirements per integration flow"
  - "reuse expectations: will the same backend data serve more than one consumer"
outputs:
  - "layer assignment map: which APIs belong at System, Process, and Experience tiers"
  - "decision on whether all three layers are needed or a simpler topology is justified"
  - "Salesforce integration touchpoint design: where Salesforce sits in the architecture"
  - "reuse and governance recommendations for the API catalog"
dependencies:
  - mulesoft-salesforce-connector
  - rest-api-patterns
  - named-credentials-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# API-Led Connectivity

Use this skill when designing or reviewing an integration architecture that organizes APIs into layered tiers to connect Salesforce with backend systems and external consumers. This skill activates when the goal is reusable, governed integration across multiple systems rather than a single point-to-point connection.

---

## Before Starting

Gather this context before working on anything in this domain:

- What backend systems need to be connected (ERP, databases, legacy SOAP services, SaaS platforms)? Each system typically maps to one or more System APIs.
- How many distinct consumers will access the same backend data? If only one consumer exists (e.g., a single Salesforce org), the full three-layer architecture may be over-engineering.
- What latency and volume requirements exist? Synchronous request-reply patterns through multiple API layers add latency; high-volume batch flows may bypass the Experience layer entirely.

---

## Core Concepts

### The Three-Layer Model

API-led connectivity organizes APIs into three tiers, each with a distinct responsibility:

| Layer | Responsibility | Typical Owner | Changes When |
|---|---|---|---|
| **System API** | Unlock raw data and operations from a single backend system. Abstracts protocol, auth, and schema details. | Integration / platform team | The backend system changes (upgrade, migration, schema change) |
| **Process API** | Orchestrate data from multiple System APIs, apply business rules, transform and aggregate. | Business technology team | A business process changes or a new cross-system workflow is needed |
| **Experience API** | Tailor data shape and interaction model for a specific consumer channel (Salesforce UI, mobile, portal, agent). | Channel / application team | A consumer's UX or data contract requirements change |

The key architectural benefit is **change isolation**: when a backend system is replaced, only its System API changes. Process and Experience APIs remain stable.

### Salesforce in the Architecture

Salesforce participates in API-led connectivity in two distinct roles:

1. **As a System-layer endpoint** — MuleSoft or another middleware calls Salesforce REST/SOAP/Bulk APIs through a System API that abstracts Salesforce-specific authentication (OAuth, Named Credentials) and object schema. External consumers never call Salesforce directly.

2. **As an Experience-layer consumer** — Salesforce calls a Process or Experience API (via Named Credentials + External Services, Apex callouts, or Flow HTTP Callout) to retrieve aggregated data from multiple backends. Salesforce UI components consume the API response.

In many architectures Salesforce plays both roles simultaneously: it is a system of record for CRM data exposed through a System API, and it consumes aggregated data from other systems through Experience APIs.

### Not All Three Layers Are Always Needed

A common over-engineering mistake is mandating all three layers for every integration. The three-layer model is a reference architecture, not a rigid requirement:

- **Skip the Process layer** when a single System API serves a single consumer with no cross-system orchestration or business rule application.
- **Collapse Experience + Process** when the consumer-specific data shaping is trivial (e.g., field renaming) and does not justify a separate deployment.
- **Add layers only when reuse or change isolation justifies the latency and operational cost** of an additional network hop.

The decision to add or skip a layer should be recorded and justified in the architecture decision log.

### Agentforce and MuleSoft Agent Fabric

Agentforce agents consume APIs through MuleSoft Agent Fabric, which exposes Process and Experience APIs as agent-callable actions. The API-led layering ensures that:

- Agents invoke well-governed, documented Experience APIs rather than raw backend calls.
- System APIs remain decoupled from agent-specific contracts, so agent requirements do not leak into backend integration code.
- Agent actions inherit the security, rate limiting, and error handling already built into the API layers.

---

## Common Patterns

### Pattern: Greenfield Multi-Consumer Architecture

**When to use:** A new integration project where multiple consumers (Salesforce, mobile app, partner portal) need access to the same backend systems (ERP, data warehouse).

**How it works:**

1. Identify each backend system and build a System API per system, exposing CRUD and query operations over a clean REST contract.
2. Build Process APIs that combine data from multiple System APIs and encode shared business logic (e.g., order validation, customer 360 assembly).
3. Build Experience APIs per consumer that shape the Process API output for the consumer's data contract (e.g., Salesforce External Service expects a specific OpenAPI shape).
4. Register each API in Anypoint Exchange with lifecycle state and ownership metadata.

**Why not the alternative:** Point-to-point connections from each consumer to each backend create N x M integration paths. Changing one backend requires updating every consumer, and shared business logic is duplicated.

### Pattern: Salesforce-Only Consumer (Simplified Layering)

**When to use:** Salesforce is the only consumer of a backend system, and no other channels are planned. The integration is request-reply with simple data mapping.

**How it works:**

1. Build a System API for the backend system.
2. Salesforce calls the System API directly via Named Credentials and External Services or an Apex callout. No separate Process or Experience API is needed.
3. Document the decision to skip layers and the conditions that would trigger adding them (e.g., a second consumer appears, or business-rule orchestration is needed).

**Why not the alternative:** Building three layers when only one consumer exists adds two network hops of latency, two additional deployments to maintain, and no reuse benefit. This is the most common over-engineering pattern in API-led adoption.

### Pattern: Retrofit Existing Point-to-Point into API-Led

**When to use:** An org already has multiple direct integrations (Apex callouts, middleware flows) to the same backend, and maintenance cost is rising because backend changes ripple across consumers.

**How it works:**

1. Inventory all existing integration touchpoints to the backend system.
2. Extract the common backend interaction into a System API.
3. Identify shared business logic across consumers and extract it into a Process API.
4. Migrate consumers one at a time to call the Process API instead of the backend directly.
5. Decommission direct connections only after the consumer is fully migrated and tested.

**Why not the alternative:** A big-bang migration of all consumers simultaneously is high risk. Incremental migration lets you validate the API contract consumer by consumer.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Multiple consumers need the same backend data | Full three-layer architecture | Maximizes reuse and change isolation |
| Single consumer, simple data mapping | System API only, consumer calls it directly | Avoid latency and operational cost of unnecessary layers |
| Single consumer, complex cross-system orchestration | System APIs + Process API, skip Experience | Business logic justifies the Process layer; Experience adds no value with one consumer |
| Agentforce agent needs backend data | Experience API exposed through Agent Fabric | Agents need tailored, governed API contracts |
| Existing point-to-point spaghetti | Incremental retrofit starting at System layer | Stabilize backend abstraction first, then add upper layers as consumers migrate |
| High-volume batch integration (millions of records) | System API with Bulk/async pattern, skip Experience | Batch jobs rarely benefit from consumer-specific shaping |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Inventory systems and consumers** -- list every backend system and every consumer channel. Map which consumers need data from which backends.
2. **Assess reuse potential** -- if a backend is consumed by only one channel, flag it as a candidate for simplified (fewer-layer) topology. If multiple consumers share the same data, plan for full layering.
3. **Design System APIs** -- one per backend system. Define the REST contract, authentication method, and error model. For Salesforce as a system endpoint, use OAuth 2.0 JWT Bearer and scope access to the minimum required objects.
4. **Design Process APIs where justified** -- only where cross-system orchestration or shared business rules exist. Document the specific business logic the Process API encodes.
5. **Design Experience APIs where justified** -- only where consumer-specific data shaping is non-trivial. For Agentforce, design the Experience API contract to match agent action input/output schemas.
6. **Validate governance** -- ensure every API is registered in a catalog (Anypoint Exchange or equivalent), has an owner, and has versioning and deprecation policies.
7. **Review with the checklist below** -- confirm the architecture avoids the common anti-patterns before implementation begins.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every backend system has at most one System API (no duplicate abstractions for the same backend).
- [ ] The decision to include or skip Process and Experience layers is documented with justification.
- [ ] Salesforce's role (system endpoint, experience consumer, or both) is explicitly identified.
- [ ] API contracts use OpenAPI or RAML specs registered in a catalog, not ad-hoc endpoint documentation.
- [ ] Authentication between layers uses OAuth 2.0 or mutual TLS, not embedded credentials.
- [ ] Latency budget accounts for each network hop introduced by the layering.
- [ ] Error propagation strategy exists: how does a System API failure surface to the Experience layer consumer?
- [ ] Agentforce agent actions, if applicable, map to Experience API operations with defined input/output schemas.
- [ ] No consumer calls a backend system directly, bypassing the System API layer.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Named Credential callout limits still apply through API layers** -- Salesforce enforces a 120-second timeout on HTTP callouts and a limit of 100 callouts per transaction. If the API-led architecture adds two hops (System + Process), the total round-trip time must stay under 120 seconds, not each hop individually.

2. **External Services has a 100,000-character OpenAPI schema limit** -- When registering a Process or Experience API as an External Service in Salesforce, the OpenAPI spec must be under ~100K characters. Large API specs with many operations or deeply nested schemas hit this ceiling. Prune the spec to the operations Salesforce actually consumes.

3. **Agentforce agent actions inherit the calling user's permissions** -- Even though the agent calls an external Experience API, the Apex or Flow that invokes the callout runs in the context of the user or the configured run-as user. CRUD and sharing rules apply to any Salesforce DML triggered by the API response.

4. **API version mismatch across layers causes silent data loss** -- If a System API exposes a field that was added in API v62.0 but the Salesforce org's Named Credential is pinned to v58.0, the field is silently excluded from responses. Pin API versions consistently across layers.

5. **MuleSoft Anypoint rate limiting is per-API, not per-layer** -- Rate limits (SLA tiers) in Anypoint API Manager apply at the individual API level. A burst of traffic to an Experience API can exhaust the Process API's rate limit downstream if the limits are not aligned. Design rate limits top-down from the Experience layer.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Layer assignment map | Table mapping each backend and consumer to the appropriate API layer(s) |
| Layer justification record | Decision log explaining which layers are included or skipped and why |
| Salesforce integration touchpoint design | Description of how Salesforce connects to the architecture (as system endpoint, experience consumer, or both) |
| API governance checklist | Catalog registration, ownership, versioning, and deprecation policies for each API |

---

## Related Skills

- `integration/mulesoft-salesforce-connector` -- use when the task is configuring a specific MuleSoft Anypoint Salesforce Connector flow, not designing the overall layered architecture.
- `integration/rest-api-patterns` -- use when the task is implementing Salesforce REST API CRUD, Composite, or pagination patterns within a System API layer.
- `integration/named-credentials-setup` -- use when configuring the authentication between Salesforce and an external API layer.
- `integration/event-driven-architecture-patterns` -- use when the architecture needs asynchronous event-driven flows alongside or instead of synchronous API layers.
- `integration/retry-and-backoff-patterns` -- use when designing error handling and retry logic between API layers.
