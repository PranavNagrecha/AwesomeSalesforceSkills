# RAG Patterns in Salesforce — Work Template

Use this template when implementing or auditing a RAG grounding configuration for an Agentforce agent or Einstein Copilot.

---

## Scope

**Skill:** `rag-patterns-in-salesforce`

**Request summary:** (fill in what the practitioner or stakeholder asked for)

**Agent / topic name:**

**Org type:** Production / Sandbox / Scratch

---

## Context Gathered

Answer these before taking action:

| Question | Answer |
|---|---|
| Data Cloud provisioned and Vector Search feature enabled? | Yes / No / Unknown |
| Source content type (Knowledge, DMO, file-based, custom)? | |
| HTML or markup present in source text fields? | Yes / No |
| Embedding model preference (Salesforce-managed / BYO via Model Builder)? | |
| Metadata fields available for filtering (list field API names)? | |
| Refresh cadence requirement (near-real-time / scheduled batch)? | |
| PII or sensitive fields present in source content? | Yes / No — fields: |
| Agent latency SLA (if customer-facing)? | |
| Packaging required (2GP Data Kit)? | Yes / No |

---

## Design Decisions

### Vector Index Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Index name | | |
| Source DMO and field | | |
| Embedding model | | |
| Chunk size (tokens) | | |
| Chunk overlap (tokens) | | |
| Refresh mode | | |
| Metadata pre-filter (if any) | | |

### Grounding Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Top-K | | |
| Metadata filter expression | | |
| Agent topic / prompt template attached to | | |
| Fallback behavior if zero chunks returned | | |

---

## Approach

Which pattern from SKILL.md applies? (check all that apply)

- [ ] Pattern 1: Knowledge Article Grounding for a Service Agent
- [ ] Pattern 2: Filtered Retrieval by Product Line
- [ ] Pattern 3: Prompt Template with Explicit Retrieval Merge Fields
- [ ] Custom pattern (describe below)

Custom pattern notes:

---

## Implementation Checklist

- [ ] Data Cloud Vector Search feature confirmed enabled
- [ ] Data Stream created with correct source connector and field mappings
- [ ] HTML / markup stripped from source text field before indexing (if applicable)
- [ ] Metadata filter fields populated with consistent casing during ingest
- [ ] Vector search index created with documented chunk size, overlap, embedding model
- [ ] Grounding configuration record created and linked to agent topic or prompt template
- [ ] Top-K set to documented value with rationale
- [ ] Metadata pre-filter tested with at least one known-matching and one known-non-matching value
- [ ] Agent Preview Grounding tab reviewed — chunks visible and relevant for 5+ test queries
- [ ] Einstein Trust Layer audit log reviewed — no unexpected masking events
- [ ] Data Stream refresh cadence confirmed and documented in runbook
- [ ] Prompt template `{!grounding.chunks}` merge field placed after role-framing, before task instruction (if using Prompt Builder)
- [ ] Total prompt token consumption measured and within model context window budget
- [ ] Data Kit includes vector index configuration (if packaging to scratch org or sandbox)

---

## Content Quality Gate

Before enabling the index for production agent traffic, verify source content quality:

| Check | Status |
|---|---|
| Only published (Online) Knowledge articles are indexed | Pass / Fail |
| Archived articles excluded from Data Stream filter | Pass / Fail |
| No draft or outdated documents present in DMO | Pass / Fail |
| HTML stripped from all text columns used for chunking | Pass / Fail |
| Sensitive fields excluded from chunked text columns | Pass / Fail |

---

## Trust Layer Review

| Check | Status | Notes |
|---|---|---|
| Audit log exported for QA retrieval session | Done / Pending | |
| Masking events reviewed — no content-critical fields masked | Pass / Fail / N/A | |
| Retrieval of records beyond agent user's intended access confirmed absent | Pass / Fail | |
| Token counts per call within expected range | Pass / Fail | |

---

## Notes and Deviations

Record any deviations from the standard patterns documented in SKILL.md and the reason for them:

(free text)

---

## Related Skills Invoked

- [ ] `prompt-builder-templates` — prompt template construction and merge field placement
- [ ] `einstein-trust-layer` — masking policy review and audit log analysis
- [ ] `agentforce-agent-creation` — prerequisite agent and topic setup
- [ ] `model-builder-and-byollm` — custom embedding model registration
- [ ] `agent-topic-design` — context variable design for metadata filter merge fields
