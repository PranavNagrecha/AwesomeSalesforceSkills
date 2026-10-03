---
name: data-cloud-grounding-for-agentforce
description: "Grounding an Agentforce agent with Data Cloud retrievers, DMO selection, chunking, and freshness windows. Triggers: agent grounding, retriever, DMO, data graph, RAG, vector index, citations. NOT for building or tuning the vector index itself — chunk size, embedding model, Query API — use agentforce/data-cloud-vector-search-dev. NOT for the end-to-end Knowledge-article RAG build — use agentforce/rag-patterns-in-salesforce. NOT for Data Cloud ingestion pipelines — use data/data-cloud-data-streams. NOT for identity resolution ruleset tuning — use admin/data-cloud-identity-resolution."
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
  - "set up an Agentforce data library for my knowledge articles"
  - "limit which knowledge articles my agent can search"
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
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
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

> **Terminology.** Agentforce *topics* were renamed **subagents** in April 2026.
> This skill leads with *subagent*. The older term still appears in metadata and
> API names, in older Help articles, and in many orgs; nothing about behaviour
> changed with the rename.

## Questions to Ask Before Configuring

Ask these before creating a library or a retriever. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which content sources, and which data space?" | A library holds Knowledge or files, never both, and its data space and source are fixed at creation (Gotcha 8) | One library per source, in the right data space | No rebuild when the second source arrives |
| "Who may see which content?" | Retriever access follows Data Cloud permission sets, not CRM sharing (Gotcha 1) | Data categories per audience and the permission sets that govern the retriever | Answers that cannot surface content the user should not see |
| "How fresh must answers be?" | Indexing takes time and cannot be changed mid-run (Gotchas 2, 3) | A freshness window per subagent, and actions for live data | Accurate expectations and no stale answers presented as current |
| "How will grounding reach production?" | Retrievers and search indexes do not deploy (Gotcha 10) | A script that creates the library in each org before the template deploys | Repeatable promotions instead of manual rebuilds |
| "What will the retriever search with?" | Search text is limited to 255 characters from globals and prompt inputs (Gotcha 11) | A short question input designed into the template | Queries that fit the limit and are reproducible |
| "Must answers cite sources?" | Source links need the Knowledge domain URL and citations turned on (Gotcha 7) | Citation settings for the library, template and agent runtime | Verifiable answers and a debugging trail |

## Platform Building Blocks

- **Data library.** Created in Setup, Agent Builder, `sf agent adl create` or the ADL Connect API. It provisions the data stream, search index and retriever, and the Answer Questions with Knowledge action uses it. Source types: Knowledge, file upload (SFDRIVE), or an existing active custom retriever (CLI help).
- **Retriever.** "The bridge between search indexes and prompt templates." A default retriever is created with each search index; custom retrievers are built in Einstein Studio. In a prompt template you set Search Text, Output Fields and Number of Results.
- **Agent runtime switches.** In Agent Script, `citation` and `groundedness` in the `runtime` block control citation enrichment and the check of responses against source content.
- **What does not deploy.** Retrievers and search indexes are not in change sets or Metadata API deployments; create them in each org first. `references/metadata-examples.md` shows the script and the template.

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
5. **Enforce access at retrieval time.** Retriever access is controlled by Data
   Cloud permission sets, so scope libraries by data category and data space,
   choose Output Fields narrowly, and never rely on the LLM to redact. Search
   text can use only globals and prompt inputs (255 characters).
6. **Set a freshness SLA.** State how stale data can be before the answer is
   wrong. Align Data Cloud refresh cadence to that SLA, not vice versa.
7. **Return citations.** Every grounded answer should include source doc_ids
   or record Ids the user can open: turn on sources for the library with the
   Knowledge domain URL set, and `isCitationEnabled` on the prompt template.
8. **Script the promotion.** Create the library in each target org with
   `sf agent adl create` and wait for `READY` before deploying the template that
   uses its retriever.

## Retriever Selection

| Question Type | Retriever | Notes |
|---|---|---|
| "What is this customer's status?" | Structured (DMO) | Filter by UnifiedIndividualId |
| "What did we tell the customer last?" | Structured (Engagement DMO) | Order by timestamp DESC limit 5 |
| "How do I handle policy X?" | Vector (Knowledge) | Chunk by section |
| "What does the transcript of the last call say?" | Vector + metadata filter | Filter by call_id |
| Blend ("account summary + last case note") | Hybrid | Two retrievers, ranked and fused |

UNVERIFIED (2026-10-03): the "structured (DMO)" retriever rows above, with record filters such as `UnifiedIndividualId`. The sources read describe retrievers over search indexes that hold structured and unstructured content; for live record facts, an action that reads the record at answer time is the documented-safe choice.

## Grounding Strategy Per Subagent

For each subagent, classify each fact you want the agent to use:

- **Instructional (in subagent prompt):** unchanging, short, domain rules.
- **Grounded (retriever):** account- or case-specific, volatile, or too big
  for a prompt. 
- **Action-derived (from an action call):** live data that must be fetched at
  answer time (balance, entitlement, real-time inventory).

Over-packing the subagent prompt with facts is the #1 token waste.

## Sharing Enforcement

Three layers:

1. **Data Cloud data space and permission sets**: baseline visibility; access to retrievers and their data is controlled by Data Cloud permission sets.
2. **Library scope and retriever settings**: data category rules on Knowledge libraries and narrow Output Fields. UNVERIFIED (2026-10-03): the earlier advice to pass the calling user's identifiers into the retriever filter; search text accepts only globals and prompt inputs, so any such filter must be designed through those.
3. **Agent response scrubbing**: last line of defense, not primary. Trust Layer data masking is disabled for agents.

If the retriever returns data the user should not see, you have a compliance
incident, not a UX bug.

## Freshness

Ingestion latency + retriever cache TTL = worst-case staleness. State this
number explicitly in the subagent design. Examples:

- Subagent for "what's my order status" — SLA = 5 min; Data Cloud stream
  job must run ≤ 3 min.
- Subagent for "what did we email last week" — SLA = 24h; daily batch is
  fine.

## Citation Pattern

Every retriever must emit stable ids back to the agent. The agent's response
template then includes "Source: <title> (<id>)". This enables:

- Transparency for the user.
- Debugging for the designer.
- Measurable retrieval quality (did the cited doc actually contain the fact?).

## Anti-Patterns (see references/llm-anti-patterns.md)

- Stuffing facts into subagent instructions that belong in a retriever.
- Returning answers with no citations.
- Filtering sharing in the agent response instead of at retrieval.
- Setting retriever k to 20+ "just in case."
- Vectorizing everything, including structured data.

## Official Sources Used

See `references/well-architected.md` for the sources read for this revision.
