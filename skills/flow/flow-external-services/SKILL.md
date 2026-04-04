---
name: flow-external-services
description: "Use when calling external REST APIs from Salesforce Flow without writing Apex: registering API specs as External Services, using generated invocable actions in Flow Builder, using Flow's built-in HTTP Callout action (GA Spring '24+), configuring Named Credentials for authentication, mapping inputs/outputs, and handling fault paths. Trigger keywords: 'External Services', 'HTTP Callout action in Flow', 'call REST API from Flow', 'register OpenAPI spec', 'Flow HTTP action'. NOT for Apex callouts, Apex HttpRequest patterns, OmniStudio Integration Procedures, or Platform Event publishing."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "how do I call an external REST API from a Flow without writing Apex"
  - "how to register an OpenAPI spec as an External Service in Salesforce"
  - "HTTP Callout action in Flow Builder Spring 24"
  - "how to handle errors from External Service actions in Flow"
  - "Named Credential required for Flow HTTP callout"
  - "parsing response from external service in Flow output variables"
  - "External Services invocable action input output mapping"
tags:
  - flow
  - external-services
  - http-callout
  - named-credentials
  - openapi
  - rest-integration
  - invocable-actions
inputs:
  - "Target external REST API endpoint and authentication type"
  - "OpenAPI 2.0 or 3.0 spec for the external service (if registering via External Services)"
  - "Named Credential developer name (required for all HTTP callouts from Flow)"
  - "Flow type: screen flow, autolaunched, or record-triggered"
  - "Expected response structure: fields and types to extract"
outputs:
  - "External Service registration with generated invocable action(s)"
  - "Flow design with HTTP Callout or External Service action, input/output mapping, and fault path"
  - "Named Credential configuration guidance"
  - "Response parsing pattern for output variables and collection variables"
  - "Review checklist for callout flows before production"
dependencies:
  - named-credentials-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Flow External Services

This skill activates when a practitioner needs to call an external REST API directly from Salesforce Flow — either by registering an OpenAPI spec via External Services or using Flow's built-in HTTP Callout action — without writing Apex. It covers registration, action configuration, Named Credential selection, input/output mapping, response parsing, fault handling, and governor limit constraints.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Authentication first:** Every outbound HTTP callout from Flow requires a Named Credential. There is no way to supply a raw URL with hard-coded credentials directly in a Flow HTTP Callout action or External Service action. Confirm a Named Credential (enhanced model recommended) exists or create one first — see the `named-credentials-setup` skill.
- **Spec availability:** External Services registration requires an OpenAPI 2.0 (Swagger) or OpenAPI 3.0 spec. If the external provider does not publish a machine-readable spec, the HTTP Callout action (Flow's built-in declarative callout, GA in Spring '24) is the correct alternative — it does not require a spec file.
- **Flow type matters for callouts:** Autolaunched flows and screen flows can make synchronous callouts. Record-triggered flows (before-save and after-save) cannot make callouts in the same transaction as the triggering DML. Attempting a callout in a record-triggered context without async handling causes a runtime error.
- **Governor limits:** Flows share the same governor limit pool as Apex in the same transaction. Each HTTP callout in a Flow consumes one of the 100 callouts-per-transaction limit (same as Apex callouts). Callout timeout is max 120 seconds. These constraints apply regardless of which mechanism (External Services or HTTP Callout action) is used.

---

## Core Concepts

### External Services: Spec-Driven Invocable Actions

External Services is a Salesforce platform feature under Setup > Integrations > External Services. It ingests an OpenAPI 2.0 or 3.0 spec, validates it against Salesforce's supported subset, and generates strongly-typed invocable actions — one per operation defined in the spec. These actions appear in Flow Builder's Action palette under the external service's label.

**Registration requirements:**
- The spec must be accessible via URL (Salesforce fetches it) or uploaded as a JSON/YAML file.
- Only a subset of OpenAPI features are supported. Polymorphic schemas (`oneOf`, `anyOf`), recursive references (`$ref` cycles), and certain header-defined parameters may fail schema validation or be silently ignored.
- A Named Credential is selected during registration. This determines the base URL and authentication. The spec's `host` or `servers` entry is overridden by the Named Credential URL at runtime.
- Changes to the spec require re-importing or updating the External Service registration. Generated action signatures change when the spec changes — existing Flow references to those actions will break if input/output parameter names change.

**Versioning:** External Services supports multiple spec versions under one registration. When you import an updated spec, Salesforce can maintain the previous version so existing Flow actions continue to work while you migrate.

### Flow's Built-in HTTP Callout Action (Spring '24+ GA)

For situations where an OpenAPI spec is not available or the integration is simple enough not to warrant full External Services registration, Flow Builder (Spring '24 GA) offers a built-in **HTTP Callout** core action. You configure it declaratively:

- **Named Credential:** required — selects the authentication and base URL.
- **Resource path:** relative path appended to the Named Credential URL (e.g., `/v1/customers`).
- **HTTP method:** GET, POST, PUT, PATCH, DELETE.
- **Headers and request body:** set directly in the action configuration.
- **Response handling:** Salesforce provides the raw response body as a text variable. You must parse it using Flow's Transform element or Apex if the response is complex JSON.

The HTTP Callout action is simpler to configure than a full External Services registration but gives less type safety — response fields are not schema-validated and must be manually mapped.

### Named Credentials: Authentication Gateway for Flow Callouts

All Flow callouts — whether via External Service actions or HTTP Callout actions — must reference a Named Credential. The Named Credential:
1. Supplies the base URL (so no hardcoded endpoints in Flow).
2. Handles authentication transparently (OAuth token injection, JWT signing, basic auth headers).
3. Controls which users can call out via External Credential principal and Permission Set assignment.

If the Named Credential's External Credential principal does not have the running user's Permission Set assigned, the callout fails at runtime with a generic authentication error. This is the most common first-run failure.

### Error Handling: Fault Paths Are Mandatory

External Service actions and HTTP Callout actions are fallible elements. Any network failure, timeout, non-2xx HTTP response (for External Services), or malformed response can cause the action to route to its fault path.

In Flow Builder, every External Service action and HTTP Callout action exposes a **fault connector**. If this connector is not wired, a failure terminates the Flow interview and throws a generic platform error — which for screen flows shows a poor user experience, and for autolaunched flows causes the caller to receive an unhandled exception.

Minimum fault pattern:
1. Wire the fault connector to a dedicated fault path.
2. Capture `$Flow.FaultMessage` in a Text variable.
3. Route to a user-safe screen (screen flows) or log/notify (autolaunched flows).
4. Consider whether the failure should be retried, escalated, or silently swallowed based on business requirements.

---

## Common Patterns

### Pattern 1: Register an OpenAPI Spec and Use the Generated Action in Flow

**When to use:** The external API publishes a machine-readable OpenAPI spec and you want typed, auto-generated actions with named input/output fields.

**How it works:**

1. Confirm Named Credential exists for the target service (see `named-credentials-setup`).
2. Navigate to **Setup > Integrations > External Services > Add an External Service**.
3. Provide the spec URL or upload the file. Select the Named Credential. Click **Save**.
4. Salesforce validates the spec. Review any warnings — unsupported schema features are flagged here.
5. Open Flow Builder and add an **Action** element. Search for the external service name. Select the operation.
6. Map required input fields (scalar types, text, number, boolean). For body objects, use a Flow record variable typed to a matching Apex class if one was generated, or individual field assignments.
7. Store output fields in Flow variables of the correct type.
8. Wire the fault connector. Capture `$Flow.FaultMessage`.
9. Test using Flow's debug mode — mock response is not available, so a real endpoint (or a sandbox of the external service) is required.

**Why not the HTTP Callout action:** If the spec is available and the API has multiple operations, External Services gives compile-time field validation, auto-complete in Flow Builder, and easier maintenance when the API contract changes.

---

### Pattern 2: Declarative HTTP Callout Without a Spec

**When to use:** No OpenAPI spec exists, the API has a single simple operation, or you want the fastest path to a working callout without spec maintenance overhead.

**How it works:**

1. Confirm Named Credential exists.
2. In Flow Builder, add a **Core Action** element. Select **HTTP Callout** from the action list.
3. Configure:
   - Named Credential: select from dropdown.
   - Invocable Action Name: a label used to identify this step.
   - Method: GET / POST / etc.
   - Path: resource path relative to Named Credential URL.
   - Headers: add `Content-Type: application/json` for POST/PUT requests.
   - Request Body: paste the JSON template or build it with a Text formula variable.
4. The action outputs: `Response_Body` (Text), `Response_Status_Code` (Number), `Response_Headers` (Text).
5. Parse `Response_Body` using a **Transform** element or a lightweight Apex method if the JSON is deeply nested.
6. Check `Response_Status_Code` in a Decision element — route non-2xx codes to an error path independently of the fault connector (the HTTP Callout action only faults on network/timeout errors, not 4xx/5xx responses).
7. Wire the fault connector for network-level failures.

**Why not External Services:** Speed and simplicity when spec is unavailable, the API surface is small, or the integration is short-lived.

---

### Pattern 3: Parsing Complex JSON Responses

**When to use:** The external service returns a nested JSON object or an array, and you need to extract specific fields into Flow variables.

**How it works:**

External Service invocable actions return output as typed variables that match the spec schema — scalars are directly assignable to Flow variables, and objects/arrays are accessible as Apex-typed variables or Flow sObject-compatible records if they match a custom object structure.

For HTTP Callout action responses (raw text), use:
1. **Flow Transform element** (available in flows alongside HTTP Callout): maps JSON path expressions to Flow variables. Useful for flat or moderately nested responses.
2. **Apex Invocable method**: if the response is deeply nested, polymorphic, or requires conditional extraction, pass `Response_Body` to a lightweight `@InvocableMethod` that parses and returns structured output. Keep the Apex logic minimal — the goal is parsing, not business logic.
3. **Collection variables**: for array responses (e.g., a list of records), use Loop elements over a collection variable populated by the External Service action's list output.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| API has an OpenAPI 2.0/3.0 spec and multiple operations | External Services registration | Typed actions, auto-complete, spec-versioning support |
| API has no spec or only one endpoint | HTTP Callout core action | Faster setup, no spec maintenance |
| Authentication required (always) | Named Credential (Enhanced model) | Platform-managed auth, no hard-coded secrets in Flow |
| Record-triggered flow needs to call external API | Async pattern: Platform Event or Queueable Apex | Synchronous callouts are not allowed in record-triggered transactions |
| Response is a flat JSON object with known fields | Transform element or External Service output mapping | No Apex needed |
| Response is deeply nested or polymorphic JSON | Lightweight Apex `@InvocableMethod` for parsing | Flow Transform cannot handle arbitrary depth |
| Screen flow calling external API | Wrap action in a separate autolaunched subflow | Isolates callout fault path from screen navigation logic |
| Batch / high-volume context | Avoid Flow callouts; use Queueable or Batch Apex | Flow callout limit is per-transaction; high-volume processing exhausts it quickly |
| Flow External Services vs Apex callouts for simple CRUD | Flow External Services if no custom logic needed | Lower maintenance, declarative, no deployment unit for code changes |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Gather context** — confirm the external API endpoint, authentication type, whether a spec file exists, and the Flow type (screen, autolaunched, record-triggered). If record-triggered, identify an async dispatch pattern before proceeding.
2. **Set up Named Credential** — verify or create a Named Credential and External Credential following the `named-credentials-setup` skill. Confirm Permission Set is assigned to the External Credential principal before testing.
3. **Choose registration method** — if an OpenAPI spec is available, register via External Services (Setup > Integrations > External Services). If not, proceed with the HTTP Callout core action in Flow Builder.
4. **Build the Flow** — add the External Service action or HTTP Callout action, map all required inputs, and wire output variables to correctly typed Flow variables. Add a Decision element to check HTTP status code for non-2xx handling (HTTP Callout only).
5. **Wire fault connectors** — connect every External Service or HTTP Callout element's fault path to a dedicated error handling branch. Capture `$Flow.FaultMessage`. For screen flows, display a friendly message. For autolaunched flows, log or notify.
6. **Test end-to-end** — run Flow debug with real credentials against the target environment. Confirm successful response, then deliberately test a failure scenario (wrong path, revoked token) to verify the fault path.
7. **Review checklist** — complete the checklist below before promoting to production.

---

## Review Checklist

Run through these before marking a callout Flow complete:

- [ ] Named Credential exists and has Permission Set assigned to the External Credential principal
- [ ] Flow type is not record-triggered (or an async dispatch pattern is in place if it is)
- [ ] Every External Service action and HTTP Callout action has a fault connector wired
- [ ] `$Flow.FaultMessage` is captured in a Text variable on the fault path
- [ ] HTTP Callout action responses include a Decision element checking `Response_Status_Code` for 4xx/5xx
- [ ] No raw JSON or API error text is displayed directly to end users in screen flows
- [ ] Collection variables used for array responses are initialized before loop elements
- [ ] Callout volume is within the 100-callout-per-transaction limit when invoked in batch contexts
- [ ] External Service spec version is recorded; team knows update procedure if API contract changes
- [ ] Test covers both success and failure paths with real credentials

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Record-triggered flows cannot make synchronous callouts** — Attempting a direct HTTP callout (via External Services action or HTTP Callout action) inside a record-triggered before-save or after-save flow throws a `System.CalloutException: You have uncommitted work pending` error at runtime. The fix is to dispatch work asynchronously via a Platform Event, a scheduled path, or a Queueable Apex job invoked from the flow.

2. **HTTP Callout action does not fault on 4xx/5xx responses** — Unlike External Services invocable actions (which route to the fault path on non-2xx responses depending on the spec configuration), the built-in HTTP Callout action only faults on network errors and timeouts. A `404 Not Found` or `500 Internal Server Error` response is returned with a status code variable and does not automatically trigger the fault connector. You must add an explicit Decision element checking `Response_Status_Code >= 400` to route these to an error path.

3. **External Services does not support all OpenAPI features** — Salesforce validates specs against a supported subset. Schemas using `oneOf`, `anyOf`, `allOf` composition, recursive `$ref` chains, or `enum` arrays on request body parameters may fail to import or produce incomplete action signatures. Always test the spec import in a sandbox before committing an integration design that depends on full spec coverage.

4. **Named Credential URL and path double-slash** — If the Named Credential base URL ends with a trailing slash and the resource path in the HTTP Callout action or spec starts with a `/`, the concatenated URL contains `//`. Some APIs reject this. Always strip the trailing slash from the Named Credential URL and ensure paths start with `/`.

5. **External Service action outputs are Apex-typed, not natively sObject** — Output variables from External Service invocable actions are typed as Apex wrapper classes generated from the spec. They cannot be directly assigned to standard Flow record (sObject) variables unless the field names match exactly. Explicitly map each output field to the target sObject variable's field in a separate Assignment element.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| External Service registration | Registered API spec with generated invocable actions visible in Flow Builder |
| Named Credential configuration | Endpoint + auth setup required before Flow callouts can execute |
| Flow with callout action | Configured External Service or HTTP Callout action with input mapping, output capture, and fault path |
| Response parsing pattern | Transform element mapping or Apex `@InvocableMethod` for structured JSON extraction |
| Review checklist completion | Completed checklist confirming fault paths, auth, status code handling, and limit awareness |

---

## Related Skills

- `named-credentials-setup` (integration) — prerequisite for any Flow callout; covers External Credential configuration, principal types, and permission set assignment
- `callouts-and-http-integrations` (apex) — Apex-based HTTP callouts when Flow External Services is insufficient (complex logic, bulk context, full error control)
- `fault-handling` (flow) — comprehensive fault connector design for all Flow element types, including external service actions
- `auto-launched-flow-patterns` (flow) — async dispatch patterns for triggering callout flows from record-triggered contexts
