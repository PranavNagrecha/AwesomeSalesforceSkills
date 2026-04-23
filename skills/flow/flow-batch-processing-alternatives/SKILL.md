---
name: flow-batch-processing-alternatives
description: "Use when a Scheduled Flow or Record-Triggered Flow needs to process more records than Flow can safely handle in a single run. Covers Flow limit realities, scheduled-path chunking, Data Cloud batch transforms, and Apex Queueable/Batch escalation. Does NOT cover choosing async across a general workflow (see async-selection decision tree)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "scheduled flow hitting limits"
  - "flow batch alternative"
  - "process thousands of records in flow"
  - "flow vs queueable batch"
  - "flow interview limit"
tags:
  - flow
  - scale
  - batch
  - async
  - limits
inputs:
  - Current Scheduled Flow or Record-Triggered Flow
  - Volume of records per run (today and projected)
  - Governor / DML / CPU limits currently observed
outputs:
  - Decision on continuing in Flow, chunking in Flow, or escalating to Apex
  - Implementation pattern (scheduled path, Platform Event, Queueable)
  - Monitoring and retry plan
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Flow Batch Processing Alternatives

## Purpose

Flow can process a lot of records — until it can't. Admin teams often build a
Scheduled Flow expecting it to handle "whatever comes," then hit a CPU or DML
limit silently, with no retry. This skill lays out the real limits,
chunking patterns that extend Flow's reach, and the clean escalation path to
Apex Queueable or Batch when the workload outgrows Flow.

## When To Use

- A Scheduled Flow has started failing at high volume.
- Record-Triggered Flow fires in bulk (data loads, mass updates) and breaks.
- Stakeholders want a nightly job that scans > 50,000 records.
- Evaluating whether to keep a Flow or rewrite.

## Recommended Workflow

1. **Measure today.** Pull Flow interview logs / Setup Audit Trail to see
   actual record volumes, DML counts, and CPU usage.
2. **Classify workload.** One-shot scan? Recurring? Triggered by record
   change? This determines the target pattern.
3. **Apply chunking if workload is moderate.** For <= ~50k records processed
   nightly, use Scheduled Paths or Platform Events to chunk.
4. **Escalate to Apex if workload is large.** For > ~50k or complex logic,
   use Queueable with finalizer or Database.Batchable.
5. **Add monitoring.** Every batched workload needs a log row per chunk and
   an alert on failure.
6. **Add retry.** One failed chunk should not kill the whole run.

## Real Flow Limits That Bite

- Per-transaction governor limits apply per Flow interview — not per run.
- Scheduled Flow runs one interview per matching record by default; 250,000
  records = 250,000 interviews per schedule.
- CPU time across a Flow interview can silently spike via formula-heavy Get
  Records on related records.
- DML Volume and SOQL query rows are real ceilings; no graceful partial
  retry exists inside Flow.

## Chunking Patterns Inside Flow

- **Scheduled Path on Record-Triggered Flow:** defer logic to a later time to
  spread load.
- **Platform Event fan-out:** Flow publishes N events, each triggering a
  smaller flow.
- **Chunk Record ID via a "batch tag" field:** update a control record with
  the last processed Id; next run resumes.
- **Invocable Apex as a pure splitter:** Flow delegates the chunking math to
  Apex but keeps orchestration.

## When To Move To Apex

Move out of Flow when:

- Per-run volume reliably exceeds ~50,000 records.
- You need precise retry semantics (Queueable finalizer).
- You need chained steps that must survive partial failure.
- Data transformations are complex enough that formula errors dominate.

The decision tree `standards/decision-trees/async-selection.md` formalizes this.

## Target Apex Patterns

- **Queueable + Finalizer:** for 10k–200k records with custom chaining.
- **Database.Batchable:** for million-record scans with stable logic.
- **Platform Events + Apex Triggered Flow:** for asynchronous fan-out.

Link the Apex implementation back to Flow through an Invocable Action so
admins keep an orchestration view.

## Monitoring Plan

- Log each chunk's start, end, record count, and status to a custom object.
- Emit a Platform Event on failure for ops dashboards.
- Alert when chunks skipped or CPU used > 80% of limit.

## Anti-Patterns (see references/llm-anti-patterns.md)

- "We'll just raise the Scheduled Flow batch size."
- Sequential Get Records across related objects instead of a collection.
- Flow-only retries ("schedule again tomorrow") that mask bugs.
- Moving to Apex Batch for a job that runs on 500 records.

## Official Sources Used

- Flow Limits and Considerations — https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm
- Scheduled Paths — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_schedule.htm
- Apex Batch — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm
- Queueable Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- Salesforce Well-Architected Resilient — https://architect.salesforce.com/docs/architect/well-architected/resilient/resilient
