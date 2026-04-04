# LLM Anti-Patterns — Flow External Services

Common mistakes AI coding assistants make when generating or advising on Flow External Services.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Advising a Callout Directly Inside a Record-Triggered Flow

**What the LLM generates:** A design that places an External Service action or HTTP Callout action directly in the main interview path of a record-triggered (before-save or after-save) flow, e.g., "Add an External Service action after the Get Records element in your record-triggered flow."

**Why it happens:** LLMs conflate all flow types. Autolaunched flows, screen flows, and record-triggered flows all use the same action palette in Flow Builder. The restriction on callouts in record-triggered contexts is a runtime enforcement not visible in the UI, so training data that describes "adding a callout action to a flow" applies incorrectly to record-triggered contexts.

**Correct pattern:**

```
Record-Triggered Flow (after save):
  → Publish Platform Event (e.g., OrderCreated__e)

Separate Autolaunched Flow (triggered by Platform Event):
  → HTTP Callout or External Service Action
  → Fault connector wired
```

Or use a Scheduled Path within the record-triggered flow (runs asynchronously after the transaction completes).

**Detection hint:** If the generated design includes an HTTP Callout or External Service action inside a flow labeled as record-triggered, after-save, or before-save — flag it for async dispatch review.

---

## Anti-Pattern 2: Forgetting the Named Credential Requirement

**What the LLM generates:** Instructions to configure an HTTP Callout action with a full URL in the endpoint field, such as `https://api.example.com/v1/orders`, without mentioning Named Credentials. Or, instructions to store the API key in a Flow Text variable and append it as a query parameter.

**Why it happens:** LLMs trained on generic REST API integration content default to the pattern of "endpoint URL + API key". Salesforce's Named Credential requirement is a platform-specific constraint that is frequently omitted in general-purpose training data about REST APIs and HTTP requests.

**Correct pattern:**

```
Step 1: Create External Credential in Setup
  Protocol: Custom Header (or OAuth 2.0)
  Principal: Named Principal
  Permission Set: assigned

Step 2: Create Named Credential
  URL: https://api.example.com  (no trailing slash)
  External Credential: <created above>

Step 3: In Flow Builder HTTP Callout action
  Named Credential: <select from dropdown>
  Path: /v1/orders
```

**Detection hint:** Any Flow integration guidance that includes a full URL in the HTTP Callout Path field or references storing API credentials in Flow variables or Custom Settings is missing Named Credential setup.

---

## Anti-Pattern 3: Treating the Fault Connector as Sufficient Error Handling for HTTP Callout Actions

**What the LLM generates:** "Wire the fault connector on the HTTP Callout action to handle errors." No mention of checking `Response_Status_Code`.

**Why it happens:** In many integration frameworks and HTTP libraries, errors are thrown as exceptions for any non-2xx response. LLMs assume the same behavior for Salesforce Flow's HTTP Callout action. However, the built-in HTTP Callout action only faults on network/timeout errors — not on 4xx/5xx HTTP responses.

**Correct pattern:**

```
HTTP Callout Action
  → Response_Status_Code → varStatusCode
  → Response_Body → varResponseBody
  [Fault Connector] → Network/Timeout Error Path

Decision: varStatusCode >= 400
  True → Server Error Path (log, notify, display message)
  False → Success Path (process varResponseBody)
```

**Detection hint:** Any design that has only a fault connector on an HTTP Callout action and no Decision element checking the status code is incomplete error handling.

---

## Anti-Pattern 4: Mapping External Service Outputs Directly to sObject Variables Without Explicit Field Assignment

**What the LLM generates:** "Map the External Service action output directly to your Account sObject variable," implying a bulk assignment of the response object to an sObject variable in one step.

**Why it happens:** External Service outputs look like typed objects in Flow Builder, and LLMs conflate them with sObject record variables because both appear as structured types with dot-notation fields. However, External Service outputs are Apex wrapper types generated from the spec, not sObjects. They cannot be bulk-assigned to an sObject variable.

**Correct pattern:**

```
External Service Action
  Outputs:
    responseObj.account_name → (do not assign to Account sObject directly)

Assignment Element (explicit field-by-field mapping):
  Account.Name = {!responseObj.account_name}
  Account.Phone = {!responseObj.phone_number}
  Account.BillingCity = {!responseObj.city}
```

**Detection hint:** Any advice that suggests directly assigning an External Service action's output object to an sObject record variable without an explicit field-mapping Assignment element is incorrect.

---

## Anti-Pattern 5: Recommending External Services for Record-Triggered Automation Without Acknowledging Async Constraint

**What the LLM generates:** "To call an external API when an Opportunity is updated, use External Services. Add the External Service action in your record-triggered flow after the Update Records element."

**Why it happens:** External Services is prominently featured in Salesforce automation documentation, and LLMs frequently recommend it as the first-choice solution for any Flow-based integration. The async requirement for record-triggered contexts is a constraint that requires domain-specific knowledge to apply correctly.

**Correct pattern:**

```
If trigger: record save (Opportunity updated)
  → Cannot use synchronous callout in this transaction
  → Option A: Record-Triggered Flow publishes Platform Event
               Platform Event-Triggered Autolaunched Flow contains External Service action
  → Option B: Record-Triggered Flow uses Scheduled Path (runs post-transaction)
               Scheduled Path contains External Service action
  → Option C: Apex Trigger invokes @future callout method
```

**Detection hint:** Any recommendation to add an External Service or HTTP Callout action to a record-triggered (before-save, after-save) flow without an explicit async dispatch mechanism is incomplete and will cause a runtime `CalloutException`.

---

## Anti-Pattern 6: Claiming External Services Supports All OpenAPI Features

**What the LLM generates:** "Register your OpenAPI 3.0 spec and all endpoints and schemas will be available as Flow actions," without noting that Salesforce's External Services validation rejects or silently drops unsupported schema constructs.

**Why it happens:** OpenAPI 3.0 support is well-documented at the headline level, but the supported-subset limitations are in fine print. LLMs reproduce the headline claim without the qualifications.

**Correct pattern:**

```
Before registering:
  - Flatten oneOf/anyOf/allOf schemas
  - Remove recursive $ref chains
  - Replace enum arrays on request body parameters with simple string types if needed
  - Test in a sandbox; verify generated action parameters match expected spec fields
  - Document which spec sections were simplified and why
```

**Detection hint:** Any External Services registration advice that does not mention spec validation, supported subset constraints, or sandbox testing before production registration may produce unexpected missing fields at runtime.
