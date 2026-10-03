---
name: salesforce-learning-research
description: "Research a Salesforce topic for a learner using a citation-first, release-aware evidence workflow: bound the question, prioritize official sources, build a claim ledger, resolve contradictions, and produce a research packet for teaching. Trigger keywords: research Salesforce topic, find official Salesforce docs, prepare learning sources, verify Salesforce concept, release-aware research. Repository package authoring and upstream intake remain outside this package. NOT for the final learner-facing explanation — use admin/salesforce-learning-brief."
category: architect
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Operational Excellence
triggers:
  - "research this Salesforce concept using official sources before teaching it"
  - "find current documentation and release context for this Salesforce topic"
  - "build a claim ledger for a Salesforce learning question"
  - "verify whether this Salesforce guidance is current or retired"
  - "collect evidence for a source-grounded Salesforce lesson"
tags:
  - learning-research
  - source-hierarchy
  - citations
  - freshness
  - evidence-ledger
  - contradiction-resolution
inputs:
  - "Learning question, learner role, current level, and intended outcome"
  - "Relevant cloud, product, org/release/API context, and desired depth"
  - "Allowed sources or supplied material, if the answer must be bounded"
outputs:
  - "Research packet with scope, terminology, claim ledger, source inventory, contradictions, freshness, and teaching implications"
  - "List of verified facts, recommendations, assumptions, unknowns, and unsupported claims"
  - "Handoff contract for admin/salesforce-learning-brief"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-09-01
---

# Salesforce Learning Research

Use this skill to establish what can responsibly be taught about a Salesforce topic **before** writing the lesson. It separates evidence acquisition from explanation so the final learning brief cannot turn stale release guidance, org assumptions, or community opinion into timeless platform fact.

This is an end-user research workflow. It does not replace the repository's build-time `content-researcher` agent, upstream intake, source manifest, or skill-authoring validation.

---

## Research Packet Contract

| Section | Required content |
|---|---|
| Research question | Learner's question, role/level, desired outcome, and explicit boundaries |
| Context identity | Cloud/product, release/API version, org/package context, and observed date when relevant |
| Terminology | Official names, aliases, renamed products, deprecated terms, and disambiguation |
| Source inventory | Source ID, title, owner, tier, publication/update date, retrieval date, scope, and URL/reference |
| Claim ledger | Atomic claim, state, evidence IDs, applicability, confidence, and teaching implication |
| Contradictions | Conflicting statements, winner under source hierarchy, and unresolved conditions |
| Freshness | Current, preview/beta, retired, historical, or unknown status for release-sensitive content |
| Gaps | Questions the sources do not support and evidence still needed |
| Brief handoff | Ordered concepts, examples safe to teach, caveats, and knowledge-check targets |

Do not copy large passages into the packet. Record concise original summaries and stable citations.

---

## Bound the Learning Question

Capture:

- learner role and current experience;
- what they should be able to explain or do afterward;
- whether the topic is conceptual, procedural, architectural, diagnostic, or release-specific;
- relevant Salesforce cloud, product, edition, license, API version, package, or org context;
- exclusions and neighboring concepts that should route to another brief;
- supplied sources that must remain the sole basis, when the user requests source-bounded work.

A broad prompt such as "teach me Flow" needs a narrower outcome before research. A bounded prompt such as "explain before-save versus after-save record-triggered Flow to an admin who knows formulas" has a researchable evidence surface.

---

## Source Hierarchy

Apply `standards/source-hierarchy.md`. Use the source best suited to the claim rather than treating every Salesforce-owned page as interchangeable.

| Claim type | Preferred evidence |
|---|---|
| Current behavior, limits, API, metadata, security contract | Salesforce product/developer documentation and current release notes |
| Architecture patterns and tradeoffs | Salesforce Architects guidance, then official developer guidance |
| Guided learning sequence | Trailhead or official learning content, verified against product docs for exact behavior |
| Current tooling command or option | Official CLI/tool documentation for the installed major version |
| Feature availability or lifecycle | Current release notes and official product availability documentation |
| Org-specific state | Read-only evidence from the explicitly identified org or user-provided snapshot |
| Practitioner nuance absent from official sources | Named expert source, explicitly lower confidence, corroborated per repository policy |

Rules:

1. A lower-tier source never overrides a higher-tier source on platform behavior.
2. Current release notes override older product documentation when behavior changed.
3. Documentation proves platform capability, not target-org entitlement or activation.
4. Search snippets are discovery aids, not final evidence; open the source before recording the claim.
5. AI-generated summaries, including this repository's own skills, are navigation aids unless their underlying sources are inspected.
6. When the user says to use only attached material, do not silently fill gaps from the web or general knowledge.

---

## Atomic Claim Ledger

Each row should make one testable statement.

| Field | Meaning |
|---|---|
| `claim_id` | Stable identifier such as `C-01` |
| `claim` | One factual or recommendation statement in original wording |
| `state` | `verified-fact`, `official-recommendation`, `inference`, `assumption`, `unknown`, or `unsupported` |
| `evidence_ids` | One or more source or org evidence identifiers |
| `applicability` | Product, edition, release/API version, environment, persona, or file type |
| `freshness` | `current`, `preview`, `beta`, `retired`, `historical`, or `unknown` |
| `confidence` | `HIGH`, `MEDIUM`, or `LOW` with a short reason |
| `teaching_implication` | What the final brief may say, must qualify, or must omit |

Never combine a verified platform behavior and an inferred best practice in one row. Split them so the final brief can label each correctly.

---

## Freshness and Lifecycle

For every release-sensitive claim, record:

- publication or last-updated date when visible;
- retrieval date;
- Salesforce release or API version;
- feature status such as GA, beta, developer preview, retired, or announced;
- enforcement or rollout date when the official source states one;
- whether the target org can be assumed to have received the release.

Use absolute dates in the packet. Do not write "recently", "now", or "next release" without anchoring the date and release.

A repository skill may summarize an older behavior accurately for its stated version. Do not label it wrong solely because it is historical; label its applicability and keep it out of a current brief unless history is relevant.

---

## Contradiction Resolution

1. Confirm that the sources discuss the same product, release, API, license, and context.
2. Prefer the higher source tier; within Tier 1, prefer the more current and more specific source.
3. Check whether one source is preview/beta while the other describes GA behavior.
4. Separate a product guarantee from an implementation recommendation.
5. Record the losing statement and why it does not control; do not silently discard it.
6. When authoritative sources still conflict, mark the claim `unknown`, explain the conflict, and prevent the final brief from asserting either side as settled.

---

## Recommended Workflow

1. **Bound the learning question** by defining the learner outcome, mapping ambiguous/renamed terminology, and recording product, release, API, org, and source boundaries.
2. **Plan and retrieve evidence** by claim type—behavior, limit, procedure, architecture, lifecycle, or org state—and search the strongest authorized sources first.
3. **Build the evidence packet** with source inventory, observed dates, stable references, atomic claims, applicability, freshness, and confidence. Use original synthesis rather than copied upstream expression.
4. **Resolve contradictions and gaps** using repository policy. Preserve unsupported, stale, inaccessible, or conflicting claims instead of silently choosing a convenient answer.
5. **Design the teaching handoff** with concept order, safe examples, caveats, checks for understanding, and the claim IDs that must remain cited.
6. **Validate and hand off** the packet with the bundled checker, then pass it to `admin/salesforce-learning-brief` for learner-facing synthesis.

---

## Quality Gates

- [ ] Learner role, level, outcome, and scope are explicit
- [ ] Product/cloud and release/API context are pinned where material
- [ ] Terminology and product renames are resolved
- [ ] Every source has owner, tier, date/retrieval date, scope, and reference
- [ ] Every material statement is an atomic claim with a state
- [ ] Release-sensitive claims carry freshness and applicability
- [ ] Recommendations are not labeled as platform guarantees
- [ ] Org-specific claims use identified org evidence or remain unknown
- [ ] Contradictions and unsupported claims are preserved, not hidden
- [ ] Search snippets and AI summaries are not the sole evidence
- [ ] The handoff tells the learning brief what it may teach and what it must qualify

---

## Output and Validation

Create the packet from `templates/salesforce-learning-research-template.md`, then run:

```bash
python3 skills/architect/salesforce-learning-research/scripts/check_salesforce_learning_research.py --input path/to/research-packet.md
```

A passing packet is evidence-ready, not automatically correct. Review source relevance and claim interpretation before teaching.

---

## Related Skills and Boundaries

- `admin/salesforce-learning-brief` — turn the verified packet into a learner-facing explanation and practice sequence.
- Repository `content-researcher` agent — research and author canonical SfSkills content; it has provenance, licensing, and repository-specific responsibilities this skill does not perform.
- `architect/salesforce-decision-analysis` — compare viable options; use learning research only to supply evidence for concepts the decision depends on.
- Domain skills — supply bounded practitioner guidance after their sources and release applicability are verified.

See the bundled references for example packets, contradiction cases, and common research failures.
