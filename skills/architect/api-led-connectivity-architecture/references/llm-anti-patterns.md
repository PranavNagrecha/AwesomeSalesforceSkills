# LLM Anti-Patterns — API-Led Connectivity Architecture

Common mistakes AI assistants make when generating or advising on API-led connectivity architecture for Salesforce integrations.

## Anti-Pattern 1: Prescribing All Three Tiers for Every Integration

**What the LLM generates:**
```
API-led connectivity architecture for this integration:
- System API: system-product-catalog-api (abstracts product database)
- Process API: process-product-sync-api (orchestrates product data enrichment)
- Experience API: experience-salesforce-product-api (shapes for Salesforce consumer)
```

**Why it happens:** LLMs model API-led connectivity as a universal three-tier pattern. Training material consistently presents all three tiers as the correct answer. LLMs do not model that single-consumer, pass-through integrations have no orchestration need and no consumer differentiation — conditions where Process and Experience layers add only cost.

**Correct pattern:**
```
Before recommending tiers, evaluate:
1. Consumer count — is there more than one consumer now or anticipated?
2. Orchestration — does the integration span multiple backend systems?
3. Response shaping — does the consumer need a different shape than the System API provides?

If all three answers are NO → System API only. Document the decision in the ADL.
If consumer count > 1 with different needs → add Experience APIs per consumer type.
If orchestration across systems → add Process API.
```

**Detection hint:** Any recommendation of all three tiers for an integration described as "one consumer, simple read/write" without evaluating consumer count or orchestration complexity.

---

## Anti-Pattern 2: Rate Limits Designed Bottom-Up

**What the LLM generates:**
```
The ERP system supports 1,000 req/min.
Set System API rate limit: 1,000 req/min
Set Process API rate limit: 1,000 req/min  
Set Experience API rate limit: 500 req/min (50% of System capacity)
```

**Why it happens:** LLMs model rate limits as capacity constraints flowing from the backend outward. They start with the known constraint (backend capacity) and divide it. They do not model that multiple Experience APIs fan into the same Process API and System API simultaneously, causing cascade exhaustion even when each individual Experience API appears within limit.

**Correct pattern:**
```
Top-down rate limit design:
1. Set Experience API limits per consumer type based on expected peak traffic:
   - experience-salesforce-orders-api: 500 req/min
   - experience-mobile-orders-api: 200 req/min
   - experience-agent-orders-api: 300 req/min (agents burst)
2. Sum all Experience API limits into Process API: (500 + 200 + 300) × 1.10 headroom = 1,100 req/min
3. Sum all Process API limits into System API: add further headroom
4. Validate resulting System API limit against backend capacity; revise if needed
```

**Detection hint:** Rate limit recommendations that start from "the backend supports X req/min" rather than from consumer traffic patterns.

---

## Anti-Pattern 3: Agentforce Agents Calling System or Process APIs Directly

**What the LLM generates:**
```apex
// Agentforce Action callout to Process API
HttpRequest req = new HttpRequest();
req.setEndpoint('https://mulesoft-process-api.company.com/order-fulfillment/orders/' + orderId);
req.setMethod('GET');
Http h = new Http();
HttpResponse res = h.send(req);
```

**Why it happens:** LLMs model Agentforce agent actions as HTTP callouts to any API the agent needs. They do not model the governance requirement that agents must go through the Experience API layer (via Agent Fabric) for security isolation, rate limit control, and audit logging.

**Correct pattern:**
```
Agentforce agents call Experience APIs via Agent Fabric — never Process or System APIs directly.

Architecture:
  Agent Action → Agent Fabric → experience-agent-orders-api → process-order-fulfillment-api → system-erp-orders-api

Agent Fabric provides:
- Per-agent OAuth 2.0 client credentials (one per agent, not shared)
- Agent-specific rate limits on the Experience API
- Audit log of every agent callout (required for agent governance)

The Experience API designed for the agent consumer has the tool-schema shape the agent expects.
Calling a Process or System API directly bypasses all of these controls.
```

**Detection hint:** Agentforce action code that calls a Process API or System API URL directly rather than routing through an Experience API endpoint designed for agent consumption.

---

## Anti-Pattern 4: Shared OAuth Credentials Across Consumers

**What the LLM generates:**
```
Configure Connected App: integration-shared-client
Grant access to:
- Salesforce CRM integration
- Mobile app integration  
- Agentforce agent
```

**Why it happens:** LLMs model OAuth credentials as a single credential that grants access to an API. They simplify the setup by using one client ID across all consumers. They do not model that shared credentials eliminate per-consumer rate limiting, audit traceability, and independent revocation.

**Correct pattern:**
```
One OAuth 2.0 client credential per consumer type:
- salesforce-crm-client         → experience-salesforce-orders-api
- mobile-app-client             → experience-mobile-orders-api  
- agentforce-fulfillment-client → experience-agent-orders-api (via Agent Fabric)

Each client has:
- Its own rate limit policy
- Its own audit log entries (filter by client_id to isolate agent traffic)
- Independent revocation (disable agent client without impacting CRM or mobile traffic)
```

**Detection hint:** Architecture designs with a single Connected App or OAuth client used by both human-driven integrations and Agentforce agents.

---

## Anti-Pattern 5: Missing Salesforce System API — Salesforce Treated as Consumer Only

**What the LLM generates:**
```
API-led connectivity architecture:
Salesforce → [Experience APIs] → [Process APIs] → [System APIs] → ERP / Billing / Warehouse
```

(No design for external systems reading FROM Salesforce)

**Why it happens:** LLMs model API-led connectivity from the Salesforce architect's perspective — Salesforce consuming external data. They don't model that Salesforce is simultaneously a backend that other systems need to read. ERP, billing, and analytics platforms often need to read Salesforce account status, contract terms, or opportunity stage — these flows require a Salesforce System API.

**Correct pattern:**
```
Integration architecture is bidirectional. For every external system that reads Salesforce:
- Design a Salesforce System API: system-salesforce-accounts-api, system-salesforce-contracts-api
- This API abstracts the Salesforce REST API behind a stable contract
- External consumers call this System API, not the Salesforce REST API directly
- Schema changes in Salesforce (field renames, object restructuring) are absorbed by the System API

Without this:
- ERP team hardcodes Salesforce REST API endpoint + credentials
- Salesforce field rename breaks ERP integration silently
- No integration team visibility into external consumers of Salesforce data
```

**Detection hint:** API-led architecture diagrams where all arrows flow INTO Salesforce but no System API is designed for systems that need to read FROM Salesforce.
