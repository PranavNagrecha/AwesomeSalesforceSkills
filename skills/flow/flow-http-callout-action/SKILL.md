---
name: flow-http-callout-action
description: "Call external HTTP APIs directly from Flow using HTTP Callout actions (no Apex), handling auth, schema, and errors. NOT for complex Apex-based integration logic."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Flow HTTP Callout Action

Flow HTTP Callouts (GA) let admins call GET/POST/PATCH endpoints without Apex. You define the action against a Named Credential, supply a sample response for schema, and map inputs/outputs in flow variables. This skill covers auth, schema inference, pagination, and error handling.

## Adoption Signals

Low-volume admin-driven integrations (weather lookup, address verification, single-record enrichment). Not for high-volume or complex transactions.

- Prefer **<200 calls/day**; switch to Apex callouts above that threshold to escape per-Flow concurrency limits.
- Required when the integration must run inside a screen flow without an admin-coded Apex dependency.

## Recommended Workflow

1. Create a Named Credential for auth (JWT, OAuth, or API Key).
2. In Flow → New Action → HTTP Callout. Pick the NC, method, path.
3. Provide a sample request + sample response; Flow infers the schema.
4. Reference the action in your flow; map inputs and consume outputs.
5. Add fault path on the action → handle 4xx/5xx (e.g., message screen on error).

## Key Considerations

- Named Credential must be External Credential + Principal type — the old flavor doesn't work.
- Schema inference is rigid; complex nested JSON may require Apex wrapper.
- No automatic pagination handling — you loop.
- Transaction timeout applies to callouts inside record-triggered flows.

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
