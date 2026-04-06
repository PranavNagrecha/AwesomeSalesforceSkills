# LLM Anti-Patterns -- API-Led Connectivity

Common mistakes AI coding assistants make when generating or advising on API-led connectivity architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Always Prescribing Three Layers Regardless of Context

**What the LLM generates:** A three-layer architecture diagram with System, Process, and Experience APIs for every integration scenario, even when a single consumer calls a single backend with trivial data mapping.

**Why it happens:** Training data overwhelmingly presents API-led connectivity as a mandatory three-layer pattern. LLMs learn the canonical form and default to it without evaluating whether the complexity is justified.

**Correct pattern:**

```text
Decision: Does this integration need all three layers?

IF only one consumer AND no cross-system orchestration AND simple data mapping:
  -> System API only. Document skip justification.

IF multiple consumers OR cross-system orchestration needed:
  -> System APIs + Process API. Add Experience APIs only if consumer-specific
     shaping is non-trivial.

IF multiple consumers WITH distinct data contracts:
  -> Full three-layer architecture.
```

**Detection hint:** Look for three-layer recommendations without a justification step or consumer-count analysis.

---

## Anti-Pattern 2: Conflating API-Led Connectivity with MuleSoft Product Features

**What the LLM generates:** Advice that treats API-led connectivity as a MuleSoft-specific capability, using MuleSoft product terminology (Anypoint Platform, API Manager policies, CloudHub) as if they are part of the pattern definition rather than one implementation option.

**Why it happens:** Most training material about API-led connectivity comes from MuleSoft documentation and blogs. The LLM conflates the architectural pattern with the product that popularized it.

**Correct pattern:**

```text
API-led connectivity is an architectural pattern that can be implemented with:
  - MuleSoft Anypoint Platform
  - Dell Boomi
  - AWS API Gateway + Lambda
  - Azure API Management
  - Custom middleware
  - Salesforce-native tools (Named Credentials + External Services + Apex)

When advising on the pattern, separate the architectural decision (how many layers,
what goes where) from the platform decision (which tool implements each layer).
```

**Detection hint:** Check if the advice uses MuleSoft-specific terms (CloudHub, Anypoint Exchange, API Manager) when the user has not specified MuleSoft as their platform.

---

## Anti-Pattern 3: Treating Salesforce as Only an Experience-Layer Consumer

**What the LLM generates:** Architecture where Salesforce is positioned exclusively as a consumer of Experience APIs, ignoring that Salesforce is also a system of record whose data must be exposed to other consumers through a System API.

**Why it happens:** LLMs see Salesforce primarily as a CRM "front end" in training data. They default to the consumer role and forget that Salesforce holds canonical data (Accounts, Contacts, Opportunities, Cases) that other systems need.

**Correct pattern:**

```text
Salesforce plays DUAL roles in most API-led architectures:

1. System-layer endpoint:
   - A System API wraps Salesforce REST/SOAP/Bulk APIs
   - External consumers access Salesforce data through this API
   - The System API abstracts Salesforce auth and schema

2. Experience-layer consumer:
   - Salesforce calls Process/Experience APIs via Named Credentials
   - Salesforce UI components display data from external systems

Always ask: "Does any other system need Salesforce data?" If yes,
Salesforce needs a System API, not just consumer-side integration.
```

**Detection hint:** Check if the architecture diagram shows arrows going only INTO Salesforce, never OUT through an API layer.

---

## Anti-Pattern 4: Ignoring Salesforce Callout Limits in Multi-Layer Designs

**What the LLM generates:** A multi-layer API architecture with no mention of Salesforce's 120-second callout timeout, 100 callouts per transaction limit, or External Services schema size constraints. The design assumes unlimited callout capability.

**Why it happens:** LLMs generate API architectures from general middleware knowledge. Salesforce-specific callout constraints are not prominent in generic integration training data.

**Correct pattern:**

```text
Salesforce callout constraints that affect API-led layer count:

1. 120-second timeout per callout (covers entire chain, not per hop)
2. 100 callouts per Apex transaction
3. ~100,000 character limit on External Services OpenAPI spec
4. 6 MB maximum response size for synchronous callouts
5. Callouts not allowed after DML in the same transaction (unless using continuation)

Design implication: Each additional API layer adds latency. If the chain
approaches 120 seconds, collapse layers or switch to async patterns.
```

**Detection hint:** Search for "120 second", "callout limit", or "timeout" in the architecture advice. If absent, the advice is incomplete for Salesforce.

---

## Anti-Pattern 5: Recommending Synchronous API Chains for High-Volume Batch Scenarios

**What the LLM generates:** A synchronous request-reply pattern through all three API layers for bulk data migration or high-volume nightly sync scenarios (e.g., syncing 500,000 records from ERP to Salesforce).

**Why it happens:** API-led connectivity documentation focuses on synchronous request-reply patterns. LLMs extrapolate the pattern to all integration scenarios, including batch, where it is a poor fit.

**Correct pattern:**

```text
Pattern selection by volume:

Synchronous API chain (System -> Process -> Experience):
  - Appropriate for: real-time, low-volume interactions (< 1000 records/call)
  - Examples: record lookup, order placement, agent action

Asynchronous / event-driven:
  - Appropriate for: high-volume batch, near-real-time sync, fire-and-forget
  - System API exposes batch endpoint or event stream
  - Process layer uses async orchestration (queue, batch job)
  - Salesforce ingests via Bulk API 2.0, Platform Events, or Change Data Capture

Do NOT route 500K records through synchronous Experience -> Process -> System
API chains. Use Bulk API patterns at the System layer and async orchestration
at the Process layer.
```

**Detection hint:** Look for record volumes > 10,000 combined with synchronous API chain recommendations. Flag as likely incorrect.

---

## Anti-Pattern 6: Generating Fictional API Specifications Without Real Contracts

**What the LLM generates:** Detailed OpenAPI specs or RAML definitions for System, Process, and Experience APIs that look plausible but contain invented endpoints, field names, and response structures that do not match any real backend system.

**Why it happens:** LLMs are generative by nature and will produce convincing but fabricated API specs when asked to "design the API." Without access to the actual backend system's documentation, the specs are pure hallucination.

**Correct pattern:**

```text
When designing API-led layers:

1. Start with the REAL backend system's API documentation or schema
2. Design the System API contract based on actual available operations
3. Design the Process API contract based on actual business rules
4. Design the Experience API contract based on the actual consumer's data model

NEVER generate a complete OpenAPI spec without first confirming the actual
operations, fields, and error codes of the backend system. Instead, generate
a SKELETON with clearly marked placeholders:

  paths:
    /customers/{id}:
      get:
        summary: "PLACEHOLDER: Confirm endpoint path with ERP team"
        responses:
          200:
            description: "PLACEHOLDER: Map actual ERP response fields"
```

**Detection hint:** Check if generated API specs reference specific backend field names or operations. If they look generic or plausible-but-unverified, flag them as requiring validation against actual backend documentation.
