# LLM Anti-Patterns — Industries Integration Architecture

Common mistakes AI coding assistants make when generating or advising on Industries Integration Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Salesforce Industries as the System of Record for Backend Operational Data

**What the LLM generates:** Architecture diagrams, Apex classes, or Flow designs that write policy premiums, rate plan tariffs, order fulfillment statuses, or billing balances into Salesforce standard Industries objects (InsurancePolicy, InsurancePolicyCoverage, EnergyRatePlan, ProductOrder) as the primary store — and treat the external PAS/BSS/CIS as a secondary read target.

**Why it happens:** LLMs trained on Salesforce documentation have learned that Salesforce objects are the canonical store for all business data in standard Salesforce implementations. Industries-specific architectural boundaries (Salesforce as engagement layer, external system as operational authority) are an advanced pattern underrepresented in generic Salesforce training data. The LLM defaults to the familiar "everything in Salesforce" pattern.

**Correct pattern:**

```
WRONG: Agent submits policy change → Salesforce updates InsurancePolicyCoverage
       → Salesforce calls PAS to notify

CORRECT: Agent submits policy change → Integration Procedure calls PAS write endpoint
         → PAS confirms → Salesforce creates Interaction__c engagement artifact only
         → Scheduled PAS→Salesforce sync updates InsurancePolicy (read-only projection)
```

**Detection hint:** Look for DML inserts or updates to `InsurancePolicy`, `InsurancePolicyCoverage`, `EnergyRatePlan`, or similar standard Industries objects in OmniScript submission paths, Apex triggers on OmniScript actions, or Flow after-save logic that fires when an agent completes a guided process. Any write to these objects from the Salesforce side (not from a CIS/PAS sync job) is a red flag.

---

## Anti-Pattern 2: Recommending MuleSoft Gateway for New Communications Cloud BSS/OSS Integrations

**What the LLM generates:** Architecture documentation, setup instructions, or implementation plans that configure the MuleSoft API Gateway as the integration path between Communications Cloud and a BSS/OSS system. The LLM may cite official Salesforce documentation that pre-dates the Winter '27 deprecation announcement.

**Why it happens:** The MuleSoft API Gateway pattern for Communications Cloud is well-documented in older official Salesforce sources and community content. The deprecation announcement (Winter '27) is a recent event that may not be fully represented in the LLM's training data, or the LLM may not associate the deprecation with the correct use case.

**Correct pattern:**

```
WRONG: Communications Cloud Setup → TM Forum API Settings → Access Mode: MuleSoft Gateway
       → Configure MuleSoft hosted API proxy → Route all BSS traffic through proxy

CORRECT: Communications Cloud Setup → TM Forum API Settings → Access Mode: Direct Access
         → Named Credential → BSS/OSS TM Forum API base URL
         → External Credential → OAuth 2.0 client_credentials → BSS/OSS auth server
         → Test via TM Forum API Diagnostics
```

**Detection hint:** Any recommendation to set "MuleSoft Gateway" in TM Forum API Settings, or any integration architecture document that includes a MuleSoft-hosted intermediary for Communications Cloud ↔ BSS/OSS traffic on new implementations. Check the phrase "MuleSoft Gateway" or "API Gateway" in any Communications Cloud integration design — it warrants a deprecation check.

---

## Anti-Pattern 3: Placing Long-Running External Callouts Inside Synchronous Integration Procedures Without Async Handling

**What the LLM generates:** Integration Procedure designs that place HTTP Action elements calling policy admin systems, BSS/OSS order endpoints, or CIS APIs directly in the synchronous IP action chain, without any async delegation or timeout handling. The generated IP assumes the external system will always respond within Salesforce governor limits.

**Why it happens:** LLMs generate "happy path" Integration Procedure designs that show the HTTP Action → response mapping → output chain. The governor limit nuance (120-second callout limit, OmniScript session timeout, async delegation requirement for slow backends) is a platform constraint that LLMs frequently omit when generating declarative architecture examples.

**Correct pattern:**

```
WRONG (for slow backends):
  IntegrationProcedure:
    HTTP Action → PAS endpoint (potentially 10–30s response time)
    Set Values → output mapping
    (no timeout handling, no async path)

CORRECT (for slow backends):
  IntegrationProcedure:
    Apex Action → AsyncCalloutDispatcher.dispatch(policyId, requestPayload)
      (Apex queues a @future or Queueable callout)
    Set Values → output:requestId = Apex return value

  OmniScript:
    Display "Processing..." step
    Poll IntegrationProcedure_CheckResult (fast SOQL on result record)
    Continue when result record has status = 'Complete'
```

**Detection hint:** IP action chain that contains an HTTP Action with a target URL pointing to an external system, and no Apex Action element or Platform Event element for async delegation. Also look for no error handling element (Set Values with condition on statusCode != 200) after the HTTP Action.

---

## Anti-Pattern 4: Hardcoding External System URLs or Credentials in Integration Procedure HTTP Actions

**What the LLM generates:** Integration Procedure XML or configuration examples that show the HTTP Action element with a hardcoded `https://policySystem.example.com/api/v1/policies` URL in the endpoint field, or with a hardcoded Authorization header value containing a bearer token or API key.

**Why it happens:** LLMs generating example configurations default to concrete URL strings to make the example tangible. The Named Credential abstraction layer is a Salesforce-specific security pattern that LLMs sometimes omit or apply inconsistently, especially when generating OmniStudio-specific configuration examples where Named Credential syntax is less commonly represented in training data.

**Correct pattern:**

```
WRONG:
  HTTP Action:
    Endpoint: https://policySystem.example.com/api/v1/policies/{policyId}
    Headers:
      Authorization: Bearer hardcoded_token_value_here

CORRECT:
  HTTP Action:
    Named Credential: PAS_PolicySystem   (references Setup > Named Credentials)
    Endpoint: /api/v1/policies/{policyId}
    (auth handled by Named Credential's External Credential — not in IP metadata)
```

**Detection hint:** Any literal `https://` URL in an Integration Procedure HTTP Action endpoint field. Any `Authorization` header with a literal token value in IP XML or configuration. Search IP export XML for `<endpoint>https://` — these should all be Named Credential references (`callout:NamedCredentialName/path`).

---

## Anti-Pattern 5: Designing a Two-Way Rate Plan Sync Between CIS and E&U Cloud

**What the LLM generates:** A data architecture or integration design that proposes syncing rate plan data bidirectionally between CIS (SAP IS-U, Oracle CC&B, or similar) and Salesforce E&U Cloud — allowing Salesforce agents to edit rate plan fields that are then written back to CIS in the next sync cycle.

**Why it happens:** LLMs often propose bidirectional sync as the "complete" or "enterprise-grade" integration pattern, applying general integration best practices (keeping both systems in sync) without understanding that CIS is the single authority for rate plan definitions by architectural intent. The LLM does not distinguish between engagement-layer data (where bidirectional is appropriate) and CIS-owned operational data (where it is not).

**Correct pattern:**

```
WRONG:
  CIS ←→ Salesforce E&U Cloud (bidirectional rate plan sync)
  CIS sends rate plan records to Salesforce
  Salesforce agents can edit RatePlan fields
  Next sync pushes Salesforce edits back to CIS

CORRECT:
  CIS ──► Salesforce E&U Cloud (one-way inbound only for rate reference data)
  CIS is authoritative for all rate plan definitions
  Salesforce EnergyRatePlan__c fields are Read-Only via FLS
  When a customer selects a rate, Salesforce creates a ServiceOrder (engagement artifact)
  CIS reads ServiceOrder and activates the rate — rate data never flows Salesforce → CIS
```

**Detection hint:** Integration design documents that describe rate plan, tariff, or billing data flowing from Salesforce to CIS. Code or configuration that allows Salesforce users to edit CIS-synced fields (no FLS Read-Only lock on those fields). ServiceOrder designs where Salesforce writes the rate value to CIS directly rather than creating an order that CIS fulfills.

---

## Anti-Pattern 6: Conflating OmniStudio Integration Procedure Design with Generic REST Callout Apex

**What the LLM generates:** Apex classes with `@future(callout=true)` methods, HTTP request/response handlers, and manual JSON parsing that replicate what an Integration Procedure HTTP Action + DataRaptor Transform would do declaratively — recommended as the "primary" integration runtime for an OmniScript-triggered call.

**Why it happens:** LLMs have extensive training data on Apex HTTP callouts and may default to code-first solutions when the declarative OmniStudio alternative exists. The LLM may not recognize that the context is an OmniScript guided process where Integration Procedures are the native, platform-preferred integration runtime.

**Correct pattern:**

```
WRONG (for OmniScript-triggered external calls):
  public class PolicyAdminCallout {
    @future(callout=true)
    public static void getPolicyData(String policyId) {
      HttpRequest req = new HttpRequest();
      req.setEndpoint('callout:PAS_System/api/v1/policies/' + policyId);
      // ... manual JSON parsing, DML to store result
    }
  }
  // OmniScript calls Apex via Apex Action element

CORRECT (for standard synchronous callout from OmniScript):
  IntegrationProcedure: Insurance_PolicyRead
    HTTP Action:
      Named Credential: PAS_System
      Method: GET
      Endpoint: /api/v1/policies/{policyNumber}
    DataRaptor Transform:
      Input: HTTP Action response JSON
      Output: OmniScript data JSON keys (coverageType, premium, effectiveDate)
  // OmniScript calls IP directly — no Apex required
  // Apex only needed if callout logic exceeds IP declarative capability
```

**Detection hint:** OmniScript designs that invoke an `Apex Action` element for a straightforward REST GET callout to an external system. If the Apex class does nothing but make an HTTP call and parse JSON with no complex branching logic, it should be replaced with an Integration Procedure HTTP Action + DataRaptor Transform.
