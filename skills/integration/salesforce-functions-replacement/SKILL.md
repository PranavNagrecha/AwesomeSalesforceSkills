---
name: salesforce-functions-replacement
description: "Salesforce Functions is retired (EOL Jan 2025). This skill maps Functions workloads to replacements: Heroku (with Hyperforce), external containers, Apex (where viable), Agentforce Actions, external compute via Named Credentials. NOT for Lambda / Azure Functions tutorials — use agentforce/einstein-bots-to-agentforce-migration."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Security
tags:
  - salesforce-functions
  - heroku
  - external-compute
  - migration
  - hyperforce
  - retirement
triggers:
  - "salesforce functions is retired how do we replace it"
  - "migrate salesforce functions workload to heroku"
  - "alternative to salesforce functions node python go workload"
  - "external compute pattern for salesforce apex heavy compute"
  - "long running compute salesforce replacement for functions"
  - "heroku vs lambda for replacing salesforce functions"
  - "we're having issues with salesforce functions"
inputs:
  - Current Functions workloads (Node.js, Java, Go, Python)
  - Invocation pattern (Apex `Function.get(...).invoke(...)`, process.platform events)
  - Performance + SLA expectations
  - Data access requirements (record data returned to caller)
outputs:
  - Replacement target per workload (Heroku, container, Apex, Agentforce Action)
  - Integration pattern for each (Named Credential + callout, Pub/Sub, event-driven)
  - Migration runbook with cutover sequence
  - Cost + ops comparison
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
status: stub
---

# Salesforce Functions Replacement

Activate when migrating off Salesforce Functions (end-of-life January 2025). Every Functions workload needs a new home, and the right home depends on the workload. Do not assume "one replacement" — Heroku suits long-running; Apex suits simple compute; external containers suit CPU-heavy work. Agentforce Actions are a good fit for LLM-adjacent logic.

## Before Starting

- **Inventory every Function.** List runtime, invocation pattern, average compute time, data dependencies.
- **Classify by driver.** Why was Functions chosen? Apex-unfriendly library? CPU intensity? Language preference? Each reason maps to a different replacement.
- **Set a migration deadline.** Functions stopped accepting new deploys in late 2024; runtime support ends January 2025. Past EOL, any outage is terminal.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Where is every Function invoked from — Apex, Flow, event subscribers? | The inventory lives at invocation sites, not in the project directory (Gotcha 4). | A list that reaches zero rather than "zero that we found". |
| What is the longest observed runtime per Function? | A Heroku web request dies at 30 seconds and the code is not told (Gotcha 1). | A sync-or-worker split decided before the port. |
| How many external calls will the replacement make per transaction, and with what timeouts? | 120 seconds is a cumulative transaction budget (Gotcha 2). | A per-callout timeout budget that sums under 120 s. |
| Is the caller a trigger, or can the entry point move to a Queueable? | A trigger path keeps synchronous CPU and heap (Gotcha 3). | The execution context chosen before the language. |
| How many records does the busiest caller process in one transaction? | The replacement inherits the caller's callout and DML budget (Gotcha 5). | One batched callout per transaction, or an event boundary. |
| Does the Function touch PII or regulated data? | A standard dyno is not a compliance boundary (Gotcha 6). | A written compliance posture for the plan and space. |
| Is any Function still being invoked today? | Functions retired on January 31, 2025 (Gotcha 4). | A triage order that starts with workloads already failing. |

A proper configuration places each workload in the context whose limits it actually fits, instead of porting code and finding the limit in production.

## Core Concepts

### Why Functions existed

Functions offered a managed Node.js / Java / Python runtime tightly integrated with Apex, invoked via `Function.get('ns.name').invoke(payload)`. It filled the gap between Apex limits and external compute without needing to manage a separate platform.

### Heroku as default replacement

Heroku is Salesforce-owned and integrates natively with Hyperforce. It offers Private Spaces, Shield, add-ons. For long-running or language-dependent workloads that Apex can't run, Heroku is the most natural migration target.

### Container-on-Hyperforce patterns

Run containers (AKS, EKS, GKE) or Cloud Run with OAuth-authenticated callouts to Salesforce. Integrate via Named Credentials + Pub/Sub or Platform Events. More ops burden than Heroku; more flexibility.

### Apex (where viable)

Simple compute that fits within Apex limits can move to Apex. CPU-bound Apex is painful (10s CPU limit on sync, 60s on async). Library-dependent work (PDF manipulation, heavy image processing) does not fit Apex.

### Agentforce Actions

LLM / AI-adjacent Functions are a good fit for Agentforce Actions or Agentforce prompt templates. Natural migration for AI-shaped workloads.

## Common Patterns

### Pattern: PDF generation Function → Heroku service

Heroku Node dyno running the same PDF library. Apex calls via Named Credential + REST; Heroku returns the generated PDF. Private Space for PCI/PII workloads.

### Pattern: Heavy compute batch → Heroku + Redis queue

Instead of an Apex-triggered Function, publish a Platform Event → Heroku worker processes job → writes result back via REST. Decouples Apex from long compute.

### Pattern: LLM enrichment → Agentforce Action

Instead of a Function calling OpenAI, define an Agentforce prompt template + Action. Native trust layer, no Heroku dyno to manage.

### Pattern: Simple enrichment → Apex Queueable

If the Function was < 5s of compute and used only standard libraries, rewrite as Queueable Apex and call via `System.enqueueJob`.

## Decision Guidance

| Workload profile | Replacement | Reason |
|---|---|---|
| Long-running, language-specific | Heroku | Native Salesforce path |
| CPU-bound batch | Heroku worker + queue | Decoupled |
| Simple enrichment, <5s | Apex Queueable | Cheapest |
| LLM / AI enrichment | Agentforce Action | Native trust layer |
| Existing container workload elsewhere | Cloud Run / AKS | Leverage existing infra |

## Recommended Workflow

1. Inventory every Function: runtime, calls/day, avg latency, data returned.
2. Classify each Function by driver (language, CPU, library, AI).
3. Assign replacement per Function per decision guidance.
4. Design integration for each: Named Credential + REST, Platform Events, Pub/Sub, Agentforce Action.
5. Build one pilot replacement end-to-end; measure latency and cost.
6. Cut over Function-by-Function; never big-bang.
7. Decommission Functions as each workload moves; track until zero invocations.

## Review Checklist

- [ ] Function inventory captured with drivers
- [ ] Replacement assigned per workload with rationale
- [ ] Named Credentials + OAuth external client apps configured
- [ ] Pilot measured against current Function perf
- [ ] Cost comparison documented
- [ ] Cutover runbook with rollback per workload
- [ ] Functions decommission tracker live

## Salesforce-Specific Gotchas

1. **Heroku Private Space + Shield is required for PCI/PII workloads.** A standard dyno does not meet compliance for protected workloads.
2. **Named Credentials and External Client Apps are the modern auth surface.** Legacy Auth Providers are being deprecated; migrate to External Client Apps during Functions migration.
3. **Pub/Sub API replaces CometD for high-volume eventing.** If the Function was consuming Streaming API, the replacement should use Pub/Sub API.

## Output Artifacts

| Artifact | Description |
|---|---|
| Function inventory | Runtime, driver, replacement target |
| Replacement design per workload | Pattern, endpoints, auth |
| Cost + ops comparison | Functions vs replacement |
| Migration runbook | Per-workload cutover + rollback |

## Related Skills

- `admin/integration-pattern-selection` — integration mechanism choice
- `integration/named-credentials-setup` — auth to Heroku / external
- `agentforce/agent-actions` — AI-adjacent migrations
