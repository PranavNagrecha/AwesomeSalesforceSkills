---
name: data-cloud-grounding-for-agentforce
description: "Use when grounding an Agentforce agent with Data Cloud retrievers, DMO selection, chunking, and freshness windows. Triggers: agent grounding, retriever, DMO, data graph, RAG, vector index, citations. Does NOT cover Data Cloud ingestion pipelines or Data Cloud identity resolution tuning."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - User Experience
triggers:
  - "ground agentforce with data cloud"
  - "data cloud retriever for agent"
  - "rag pattern agentforce"
  - "citations in agent response"
  - "freshness sla for retrievers"
tags:
  - agentforce
  - data-cloud
  - grounding
  - retrieval
  - rag
inputs:
  - Use case + expected user questions
  - Data Cloud DMOs and data graphs already in place
  - Field-level sharing requirements
outputs:
  - Retriever design (DMO selection, filters, chunking)
  - Grounding strategy per topic (what retrieves, what is instructional)
  - Freshness SLA and refresh plan
  - Citation / transparency pattern
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Data Cloud Grounding For Agentforce

## Purpose

Agentforce answers are only as good as the data they can reach. Grounding with
Data Cloud lets an agent retrieve context from unified customer profiles,
engagement events, knowledge articles, and structured or unstructured sources,
then cite them in the answer. Without a deliberate grounding design the agent
either hallucinates (too little context), over-retrieves (latency and cost
spike), or leaks data the calling user should not see (sharing ignored at the
retriever level).

This skill covers picking the right DMOs and data graphs, chunking and
filtering for relevance, enforcing field-level and record-level visibility at
query time, setting a freshness SLA that fits the use case, and returning
answers that cite their sources.

## When To Use

- Designing a new Agentforce topic that must reference customer data.
- Replacing a static instruction dump with a retriever for scale.
- Moving from a Knowledge-only retriever to a blended retriever that also hits
  engagement and transactional data.
- Troubleshooting ungrounded or stale answers.

## Recommended Workflow

1. **List the questions the agent must answer.** Work backwards from real user
   utterances. If you cannot list 10 sample questions, grounding is premature.
2. **Map questions to DMOs and data graphs.** For each question, identify the
   DMO(s) and fields required. Promote gaps into Data Cloud ingestion work
   before wiring a retriever.
3. **Pick retriever type per question bucket.** Structured retriever for
   records (account, contact, case). Vector/unstructured retriever for
   Knowledge, call transcripts, documents. Hybrid when both are needed.
4. **Decide chunking.** For unstructured, chunk by semantic boundary (article
   section, call segment) not fixed token count when possible. Preserve a
   stable doc_id + section_id in metadata for citation.
5. **Enforce sharing at retrieval time.** Apply user-context filters so the
   retriever never returns rows the running user cannot see. Never rely on the
   LLM to redact.
6. **Set a freshness SLA.** State how stale data can be before the answer is
   wrong. Align Data Cloud refresh cadence to that SLA, not vice versa.
7. **Return citations.** Every grounded answer should include source doc_ids
   or record Ids the user can open.

## Retriever Selection

| Question Type | Retriever | Notes |
|---|---|---|
| "What is this customer's status?" | Structured (DMO) | Filter by UnifiedIndividualId |
| "What did we tell the customer last?" | Structured (Engagement DMO) | Order by timestamp DESC limit 5 |
| "How do I handle policy X?" | Vector (Knowledge) | Chunk by section |
| "What does the transcript of the last call say?" | Vector + metadata filter | Filter by call_id |
| Blend ("account summary + last case note") | Hybrid | Two retrievers, ranked and fused |

## Grounding Strategy Per Topic

For each topic, classify each fact you want the agent to use:

- **Instructional (in topic prompt):** unchanging, short, domain rules.
- **Grounded (retriever):** account- or case-specific, volatile, or too big
  for a prompt. 
- **Action-derived (from an action call):** live data that must be fetched at
  answer time (balance, entitlement, real-time inventory).

Over-packing the topic prompt with facts is the #1 token waste.

## Sharing Enforcement

Three layers:

1. **Data Cloud data space / sharing rules** — baseline visibility.
2. **Retriever filter** — always pass the calling user's identifiers so the
   retriever limits to rows they are allowed to see.
3. **Agent response scrubbing** — last line of defense, not primary.

If the retriever returns data the user should not see, you have a compliance
incident, not a UX bug.

## Freshness

Ingestion latency + retriever cache TTL = worst-case staleness. State this
number explicitly in the topic design. Examples:

- Agent topic for "what's my order status" — SLA = 5 min; Data Cloud stream
  job must run ≤ 3 min.
- Agent topic for "what did we email last week" — SLA = 24h; daily batch is
  fine.

## Citation Pattern

Every retriever must emit stable ids back to the agent. The agent's response
template then includes "Source: <title> (<id>)". This enables:

- Transparency for the user.
- Debugging for the designer.
- Measurable retrieval quality (did the cited doc actually contain the fact?).

## Anti-Patterns (see references/llm-anti-patterns.md)

- Stuffing facts into topic instructions that belong in a retriever.
- Returning answers with no citations.
- Filtering sharing in the agent response instead of at retrieval.
- Setting retriever k to 20+ "just in case."
- Vectorizing everything, including structured data.

## Official Sources Used

- Agentforce — Ground Your Agent — https://help.salesforce.com/s/articleView?id=sf.agentforce_grounding.htm
- Data Cloud retriever — https://help.salesforce.com/s/articleView?id=sf.c360_a_data_cloud_retriever.htm
- Data Cloud DMOs — https://help.salesforce.com/s/articleView?id=sf.c360_a_data_model_objects.htm
- Salesforce Architects — Data Cloud guidance — https://architect.salesforce.com/
