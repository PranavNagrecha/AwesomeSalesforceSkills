---
name: flow-http-callout-action
description: "Call external HTTP APIs directly from Flow using HTTP Callout actions (no Apex), handling auth, schema, and errors. NOT for registering an OpenAPI spec as an External Service — use flow/flow-external-services. NOT for Apex callout logic and mock tests — use apex/callouts-and-http-integrations."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "flow http callout"
  - "call rest api from flow"
  - "flow without apex integration"
  - "named credential flow callout"
  - "set up an HTTP callout action in a flow"
  - "fix an HTTP callout that fails for other users"
tags:
  - flow
  - callout
  - rest
inputs:
  - "target endpoint + Named Credential"
  - "sample request/response"
outputs:
  - "Flow HTTP Callout action with schema + fault path"
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Flow HTTP Callout Action

Flow HTTP Callouts let admins call endpoints without Apex (UNVERIFIED (2026-10-20): "GA" and the GET/POST/PATCH method list are not in any corpus guide; the only HTTP Callout mention is the `SchemaInferred` API-specification source, "provided during the HTTP Callout configuration process", api_meta 264 L66635). You define the action against a Named Credential, supply a sample response for schema, and map inputs/outputs in flow variables. This skill covers auth, schema inference, pagination, and error handling.

## Adoption Signals

Low-volume admin-driven integrations (weather lookup, address verification, single-record enrichment). Not for high-volume or complex transactions.

- Prefer **<200 calls/day**; switch to Apex callouts above that threshold to escape per-Flow concurrency limits. UNVERIFIED (2026-10-20): neither the 200-calls/day figure nor any per-Flow concurrency limit appears in the corpus; treat it as a rule of thumb, not a platform limit.
- Required when the integration must run inside a screen flow without an admin-coded Apex dependency.

## Recommended Workflow

1. Create an External Credential and a Named Credential for auth. Valid `authenticationProtocol` values are `AwsSv4`, `Basic`, `Custom`, `Oauth` and others; the value list marks `Jwt` "Reserved for future use" (L66193) while the next paragraph says "For connections using a direct token system, select Jwt" (L66199), so confirm `Jwt` in the target org before using it; an API key is a `Custom` protocol with an `AuthParameter` (api_meta 264 L66186-66197, `AuthParameter` in the sample at L66409).
2. In Flow → New Action → HTTP Callout. Pick the NC, method, path.
3. Provide a sample request + sample response; Flow infers the schema.
4. Reference the action in your flow; map inputs and consume outputs.
5. Add fault path on the action → handle 4xx/5xx (e.g., message screen on error).

## Key Considerations

- The Named Credential must use the current model: `namedCredentialType` `SecuredEndpoint` "uses external credentials to control authentication and permissions" (api_meta 264 L92881-92882); `Legacy` "doesn't use the schema introduced in the Winter '23 release" (api_meta 264 L92875-92876). UNVERIFIED (2026-10-20): the corpus does not say the HTTP Callout action rejects a `Legacy` credential; that is the field-reported symptom.
- Every running user's permission set needs access to the External Credential principal: `PermissionSetExternalCredentialPrincipalAccess` — "Users assigned to the permission set can make callouts using a named credential that references the external credential" (api_meta 264 L97688-97689, available in API version 59.0 and later).
- Schema inference is rigid; complex nested JSON may require Apex wrapper. UNVERIFIED (2026-10-20): schema inference is described only by the `SchemaInferred` source name (api_meta 264 L66635); its limits on nesting are not in the corpus.
- No automatic pagination handling — you loop. UNVERIFIED (2026-10-20): the corpus does not describe the action's paging behaviour.
- Callout limits are 100 callouts per transaction and 120 seconds cumulative (apexdev 264 L19766, L19768, the Per-Transaction Apex Limits table; the single-transaction wording is L36335). UNVERIFIED (2026-10-20): the guides print these for Apex and do not state that a flow's HTTP Callout counts against the same two counters.
- Run the callout from the asynchronous path of a record-triggered flow: "Asynchronous paths in record-triggered flows" are post-commit logic: "After the changes are committed to the database, executes post-commit logic" and the examples list "Asynchronous paths in record-triggered flows" (apexdev 264 L15682, L15692).

## Questions to Ask Before Configuring

Ask these before building the action. Each one maps to a gotcha or anti-pattern in this package.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is the Named Credential `SecuredEndpoint` with an External Credential, or `Legacy`?" | A `Legacy` credential does not use the Winter '23 schema (api_meta 264 L92875-92876); that the action then fails is field-reported and UNVERIFIED (2026-10-20) (gotcha 1) | The credential type, read from the metadata rather than remembered |
| "Which permission sets grant principal access, and were they tested with a non-admin user?" | Principal access is granted per permission set (api_meta 264 L97688-97689); the builder can authenticate and nobody else can (anti-pattern 2) | A named permission set and a test run as a user who is not the builder |
| "What does the endpoint return for a partial match, an empty result and an error body?" | Fields absent from the pasted sample do not become flow resources (gotcha 2, anti-pattern 3; UNVERIFIED (2026-10-20): schema inference is named only as `SchemaInferred`, api_meta 264 L66635) | A captured non-ideal response to paste as the sample |
| "What should the user or the record see when the call fails?" | An action with no fault connector ends the flow with an unhandled error (gotcha 3, anti-pattern 4; UNVERIFIED (2026-10-20): the unhandled-fault outcome is not in the corpus) | A message screen or an `Unavailable` marker value, decided before the build |
| "How many records can reach the action in one transaction?" | 100 callouts and 120 seconds cumulative per transaction (apexdev 264 L19766, L19768; anti-pattern 5) | A batch size or a move to a scheduled flow or Apex |
| "Is this record-triggered, and may the user wait for the vendor?" | A synchronous callout adds the vendor's latency to the save; the asynchronous path runs post-commit (apexdev 264 L15682, L15692; anti-pattern 6) | The asynchronous path chosen, with an entry condition that stops re-triggering |
| "Does the API page its results?" | Hand-rolled paging multiplies the callout count against the 100-per-transaction limit (apexdev 264 L19766; anti-pattern 7) | A page size that fits one call, or the decision to use Apex |

A proper configuration adds a credential every user can reach, a schema taken from a real non-ideal response, and a failure path for both the transport error and the unhelpful success, none of which "just adding the action" provides.

## Worked Examples (see `references/examples.md`)

- *Address verification* — Lead capture
- *Weather lookup* — Field service dispatch

## Common Gotchas (see `references/gotchas.md`)

- **NC version mismatch** — Callout fails auth.
- **Complex JSON** — Schema infer misses nested fields.
- **No fault path** — Flow fails to user.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Apex for trivial GET
- Legacy Named Credential
- No fault path

## Official Sources Used

- Flow Builder Guide — https://help.salesforce.com/s/articleView?id=sf.flow.htm
- Flow Best Practices — https://help.salesforce.com/s/articleView?id=sf.flow_best_practices.htm
- Reactive Screens — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_reactive.htm
- Flow HTTP Callout Action — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_callout.htm
