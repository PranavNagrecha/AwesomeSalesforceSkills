---
name: flow-interview-debugging
description: "Diagnose Flow failures using the Debug Log, Flow Error emails, and the Debug panel; instrument flows so production issues are triageable. NOT for Apex debugging."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "flow error email"
  - "flow debug log"
  - "flow failing in production"
  - "flow interview paused"
tags:
  - flow
  - debug
  - error-handling
inputs:
  - "failing flow + error email"
  - "repro data"
outputs:
  - "root cause + remediation + logging upgrade"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Flow Interview Debugging

Flow failures can be invisible. Error emails go to the flow owner by default, not a shared alias. This skill sets up centralized error routing, Debug panel usage, fault-path patterns, and the Log__c instrumentation that turns production flow failures from silent into triageable.

## When to Use

Any flow running in production, and before go-live for mission-critical flows.

Typical trigger phrases that should route to this skill: `flow error email`, `flow debug log`, `flow failing in production`, `flow interview paused`.

## Recommended Workflow

1. Setup → Process Automation Settings → set 'Email for flow errors' to a shared alias or queue.
2. For each flow: add a Fault connector on every element that can fail (DML, Action, Subflow) → custom Log__c with context + ScreenError screen or rollback.
3. In dev: use the Flow Debug panel; toggle 'Run flow as user' vs system; check resource values on each step.
4. For triggered flows: use `?flow_debug=true` URL param on related list or observe via the Flow Debug view in Record Triggered.
5. Establish SLA — review Log__c daily; add alert on error count spike.

## Key Considerations

- Flow errors in async-triggered flows surface as email-only unless instrumented.
- Fault path on Get with 0 results is NOT an error — 0 rows is success; use Decision.
- Debug panel doesn't show async (scheduled path) execution; test those in sandbox.
- `$Flow.FaultMessage` provides the platform error text; log it.

## Worked Examples (see `references/examples.md`)

- *Central error log* — 12 flows, scattered errors
- *Debug 'field not writable'* — Screen save failure

## Common Gotchas (see `references/gotchas.md`)

- **Fault on 'no results'** — Flow errors when Get returns 0.
- **Email to owner only** — No one notices in prod.
- **Async not in Debug** — Only sync path works in panel.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- No fault connectors
- Owner-only error email
- Silent subflow failures

## Official Sources Used

- Flow Builder Guide — https://help.salesforce.com/s/articleView?id=sf.flow.htm
- Flow Best Practices — https://help.salesforce.com/s/articleView?id=sf.flow_best_practices.htm
- Reactive Screens — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_reactive.htm
- Flow HTTP Callout Action — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_callout.htm
