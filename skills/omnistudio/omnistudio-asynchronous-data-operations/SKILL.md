---
name: omnistudio-asynchronous-data-operations
description: "Use Integration Procedures queues, DataRaptor Chain, and Remote Actions with async patterns for long-running OmniStudio flows. NOT for simple DataRaptor reads."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
triggers:
  - "integration procedure queue"
  - "dataraptor chain"
  - "omnistudio async"
  - "omniscript long running"
tags:
  - omnistudio
  - integration-procedure
  - async
inputs:
  - "use case with >5s response or multi-system orchestration"
outputs:
  - "IP design with queued steps + error handling"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# OmniStudio Asynchronous Data Operations

OmniStudio Integration Procedures (IPs) can chain DataRaptors, HTTP calls, Apex, and Business Rules into a single orchestration. For operations that exceed the 5-second browser wait or need parallel calls, queue the IP (invoke from Platform Event or Queueable) instead of running synchronously.

## When to Use

Multi-system orchestrations >5s or bulk data transformations driven from an OmniScript.

Typical trigger phrases that should route to this skill: `integration procedure queue`, `dataraptor chain`, `omnistudio async`, `omniscript long running`.

## Recommended Workflow

1. Model the orchestration as an IP; label each step by purpose.
2. For long steps, split: a synchronous IP kicks off a Queueable or publishes a Platform Event; the worker IP runs async.
3. Consumer polls status via a DataRaptor read; show progress screen in the OmniScript.
4. Error path: each IP step has Abort On Error; always catch at top with a retry/fail branch.
5. Observability: log IP execution via custom logger or Salesforce Log Entry framework.

## Key Considerations

- IPs sync limit: 120s overall, 10s per HTTP callout.
- Cache responses where safe (cache-enabled IP) to reduce backend load.
- Parallel Remote Actions reduce wall-clock; IP supports Send/Response parallel.
- Don't put heavy transforms in DataRaptor — use Apex Action for perf-sensitive paths.

## Worked Examples (see `references/examples.md`)

- *Async order placement* — OmniScript checkout
- *Parallel enrichment* — Credit + address verification

## Common Gotchas (see `references/gotchas.md`)

- **Sync >120s kill** — Whole IP aborts.
- **Cache stale** — Users see old data.
- **No error branch** — Silent failure to user.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Everything sync
- No caching on hot IPs
- Heavy Apex in DataRaptor transformations

## Official Sources Used

- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer.meta/omnistudio_developer/
- OmniStudio for Salesforce — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_for_salesforce_overview.htm
- OmniScript to LWC OSS — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer.meta/omnistudio_developer/os_migrate_from_vf_to_lwc.htm
