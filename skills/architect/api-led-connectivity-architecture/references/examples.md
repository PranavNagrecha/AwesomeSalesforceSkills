# Examples — API-Led Connectivity Architecture

## Example 1: Order Fulfillment — Full Three-Tier Design

**Context:** A manufacturer uses Salesforce for CRM, an ERP for order management, a billing system for invoicing, and is adding a mobile app for field reps. Multiple consumers need order data in different shapes.

**Problem:** Without API-led connectivity, each consumer (Salesforce, mobile app) calls the ERP and billing system directly. When the ERP migrates from v4 to v5, all consumer integrations break simultaneously and must be updated by separate teams on separate timelines.

**Solution:**

```
Three-tier assignment:
- system-erp-orders-api         — abstracts ERP order schema; one System API per backend
- system-billing-invoices-api   — abstracts billing system invoice schema
- process-order-fulfillment-api — orchestrates system-erp + system-billing for "fulfill order" business process
- experience-salesforce-orders-api — Salesforce-shaped: full order + opportunity fields; OAuth 2.0 for Salesforce Connected App
- experience-mobile-orders-api     — Mobile-shaped: lightweight order summary; includes offline sync hints
- experience-agent-orders-api      — Agentforce-shaped: structured as tool schema for agent action; routed via Agent Fabric

Rate limit design (top-down):
- experience-salesforce-orders-api: 500 req/min
- experience-mobile-orders-api:     200 req/min
- experience-agent-orders-api:      300 req/min (agents can fan out)
- process-order-fulfillment-api:    1,100 req/min (sum of above + 10% headroom)
- system-erp-orders-api:            2,000 req/min (process API + direct ERP tools + headroom)
```

**Why it works:** When the ERP migrates to v5, only `system-erp-orders-api` requires an update. All three Experience APIs and the Process API continue to work without changes. The migration risk is isolated to one team and one API.

---

## Example 2: Single-Consumer Internal Integration — Layer-Skip Decision

**Context:** A Salesforce org needs to read a static product catalog from an internal warehouse system. Only one consumer (Salesforce) will ever read this data. The warehouse system has a stable REST API.

**Problem:** A three-tier design (System + Process + Experience API) adds two network hops, two additional catalog entries, and two additional teams to maintain — for a read-only integration with one consumer and no orchestration logic.

**Solution:**

```
Architecture Decision Log — API-led layer skip

Decision: Build System API only (warehouse-product-catalog-api).
Salesforce calls System API directly — Process and Experience layers skipped.

Rationale:
- Consumer count: 1 (Salesforce CRM only)
- Anticipated new consumers: None (product catalog is internal tooling only)
- Business process orchestration: None (direct read; no cross-system logic)
- Response shaping: None required (Salesforce can consume the System API response directly)

Tradeoff accepted:
- If a second consumer is added in future, an Experience API wrapping this System API
  must be created within 30 days of onboarding the new consumer.
- Salesforce will call the System API with its own Connected App credentials.

Review trigger: New consumer request OR API contract change.
```

**Why it works:** The architecture decision is explicit, documented, and includes a re-evaluation trigger. This is not a governance gap — it is a deliberate, documented tradeoff. The risk of undocumented layer-skipping is that it becomes permanent and unreviewed.

---

## Anti-Pattern: Shared Credentials Across Consumers

**What practitioners do:** To simplify setup, one OAuth 2.0 client ID and secret are shared between the Salesforce Experience API consumer and the Agentforce agent consumer.

**What goes wrong:** When the agent behaves unexpectedly or exhausts the rate limit, audit logs show "client-id-shared" for both the human-initiated Salesforce calls and the agent-initiated calls. It is impossible to determine which calls came from the agent and which from user actions. Rate limit enforcement applies to both together — a spike from agent calls can throttle human-user traffic. Revoking the credential to stop agent traffic also stops Salesforce user traffic.

**Correct approach:** Dedicate one OAuth 2.0 client credential per consumer type. For Agentforce agents: one client per agent (or per agent category if agents are numerous). This provides per-consumer audit trails, isolated rate limits, and the ability to revoke agent access without impacting human-user traffic.

```
Correct credential assignment:
- experience-orders-api — client: salesforce-crm-prod-client
- experience-orders-api — client: agentforce-fulfillment-agent-client
- experience-orders-api — client: mobile-app-prod-client

Each client has:
- Separate rate limit policy
- Separate audit log filter
- Independent revocation capability
```
