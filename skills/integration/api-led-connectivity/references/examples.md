# Examples -- API-Led Connectivity

## Example 1: Multi-Channel Order Fulfillment with Full Three-Layer Architecture

**Context:** A retail company uses SAP for inventory, Salesforce for CRM, and a custom warehouse management system. Orders originate from Salesforce, a mobile app, and a partner portal. All three consumers need real-time stock availability and order placement.

**Problem:** Without layered APIs, each consumer builds its own SAP connector with duplicated authentication, field mapping, and error handling. When SAP upgrades its IDOC interface, all three consumers break simultaneously and must be patched independently.

**Solution:**

```text
Layer Assignment:
  System APIs:
    - sap-inventory-sapi    -> wraps SAP BAPI_MATERIAL_AVAILABILITY, exposes REST
    - sf-order-sapi          -> wraps Salesforce REST API for Order/OrderItem CRUD
    - warehouse-sapi         -> wraps warehouse SOAP service, exposes REST

  Process APIs:
    - order-fulfillment-papi -> orchestrates: check inventory (sap-inventory-sapi),
                                create order (sf-order-sapi),
                                trigger shipment (warehouse-sapi),
                                applies business rules (min order qty, backorder logic)

  Experience APIs:
    - sf-order-xapi          -> shapes order-fulfillment-papi response for Salesforce
                                External Service (flat JSON, Salesforce field names)
    - mobile-order-xapi      -> shapes response for mobile app (paginated, lightweight)
    - partner-order-xapi     -> shapes response for partner portal (includes partner
                                pricing tier, excludes internal cost fields)
```

**Why it works:** When SAP upgrades, only `sap-inventory-sapi` changes. The three Experience APIs and the Process API are untouched. When a new business rule is added (e.g., fraud check), it is added once in the Process API and all consumers inherit it.

---

## Example 2: Salesforce-Only Consumer with Simplified Two-Layer Architecture

**Context:** A financial services firm needs to display customer credit scores from an internal scoring engine in Salesforce. Salesforce is the only consumer. The data mapping is straightforward: one API call returns a score and a risk category.

**Problem:** The team initially plans three API layers because "that is what API-led requires." The two extra hops add 200ms of latency to a screen that sales reps load hundreds of times per day.

**Solution:**

```text
Layer Assignment:
  System API:
    - credit-score-sapi     -> wraps the scoring engine REST endpoint,
                                handles auth (mutual TLS), normalizes error codes

  Salesforce consumes credit-score-sapi directly:
    - Named Credential: CreditScoreAPI (OAuth 2.0 Client Credentials)
    - External Service registered from credit-score-sapi OpenAPI spec
    - Flow calls the External Service action on Account record page load

  Skipped layers:
    - Process API: not needed (no cross-system orchestration, no shared business logic)
    - Experience API: not needed (single consumer, data shape already matches SF needs)

  Documented trigger to add layers:
    - "If a second consumer (e.g., mobile app) needs credit scores, introduce
       an Experience API for each consumer and evaluate whether a Process API
       is needed for shared transformation."
```

**Why it works:** The architecture delivers the latency and simplicity the use case demands. The decision to skip layers is explicit, documented, and reversible.

---

## Example 3: Agentforce Agent Consuming Backend Data Through Agent Fabric

**Context:** An Agentforce service agent needs to look up warranty status from a legacy mainframe system. The mainframe exposes a CICS transaction over TCP/IP. Salesforce cannot call the mainframe directly.

**Solution:**

```text
Layer Assignment:
  System API:
    - warranty-mainframe-sapi -> MuleSoft flow wraps CICS transaction,
                                  exposes REST with JSON request/response

  Process API:
    - warranty-lookup-papi    -> enriches warranty data with customer info
                                  from Salesforce (calls sf-customer-sapi),
                                  applies coverage eligibility rules

  Experience API (Agent Fabric):
    - warranty-agent-xapi     -> tailored for Agentforce agent action:
                                  input: { "serialNumber": "string" }
                                  output: { "coverageStatus": "ACTIVE|EXPIRED",
                                            "expirationDate": "date",
                                            "eligibleForExtension": "boolean" }
                                  registered in Agent Fabric as "Check Warranty"

  Salesforce:
    - Agentforce agent invokes "Check Warranty" action
    - Action maps to warranty-agent-xapi
    - Agent receives structured response and uses it in conversation
```

**Why it works:** The agent gets a clean, purpose-built contract. The mainframe complexity is fully hidden behind the System API. Business eligibility rules live in the Process API and are reusable if a portal consumer is added later.

---

## Anti-Pattern: Mandatory Three Layers for Every Integration

**What practitioners do:** Apply System + Process + Experience APIs to every integration regardless of consumer count or complexity. A simple "Salesforce reads from one REST endpoint" integration gets three deployed APIs with three separate CI/CD pipelines.

**What goes wrong:** Each unnecessary layer adds ~50-100ms of network latency, a separate deployment to maintain, and an additional failure point. The team spends more time maintaining API infrastructure than building business value. Developer productivity drops and the "API-led" initiative gets blamed.

**Correct approach:** Start with a System API for every backend. Add Process and Experience layers only when reuse, cross-system orchestration, or consumer-specific shaping justifies the cost. Document the decision and the trigger conditions for adding layers later.
