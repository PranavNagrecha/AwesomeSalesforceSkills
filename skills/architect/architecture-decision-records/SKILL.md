---
name: architecture-decision-records
description: "Author and maintain Architecture Decision Records (ADRs) for Salesforce implementations: capture chosen approach, rejected alternatives, constraints, and consequences. Trigger keywords: adr, architecture decision record, design decision log, technical decision. Does NOT cover project roadmap planning, release notes, or RFC workflow for features."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - architecture decision record
  - adr template
  - design decision log
  - technical rationale document
tags:
  - architect
  - adr
  - governance
  - documentation
  - decision-log
inputs:
  - A non-trivial technical decision (platform choice, pattern adoption, org topology)
  - Alternatives considered and the evaluation criteria
outputs:
  - One ADR file per decision, numbered, dated, statused
  - Index updated with new entry + any superseded links
dependencies:
  - architect/solution-design-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Architecture Decision Records

## When To Use

- A decision with multi-quarter impact: platform choice (e.g. Flow vs
  Apex vs Agentforce), pattern adoption (Trigger Handler, Selector
  Layer), org topology (single-org vs multi-org), integration approach
  (Pub/Sub vs REST).
- A decision reversing an earlier one — always writes a new ADR that
  supersedes the old.
- A decision you expect someone in 6 months to ask "why did we do
  this."

## When NOT To Use

- Day-to-day implementation choices covered by existing patterns.
- Task-level tradeoffs that belong in a PR description.
- Anything fully internal to one feature's lifecycle.

## ADR Structure

Each ADR is one markdown file in `docs/adr/` with a number prefix:

```
docs/adr/
├── 0001-use-trigger-handler-framework.md
├── 0002-async-via-platform-events-not-future.md
└── INDEX.md
```

Required sections:

1. **Title** — `ADR-XXXX: <one-line decision>`.
2. **Status** — Proposed / Accepted / Deprecated / Superseded by
   ADR-YYYY.
3. **Context** — the forces at play; what pushed us to decide.
4. **Decision** — the choice, stated clearly.
5. **Consequences** — positive and negative outcomes, with named
   tradeoffs.
6. **Alternatives Considered** — at least two rejected options with
   why they lost.
7. **Date** — decision date (ISO-8601).
8. **Deciders** — the people and the forum (CAB, architecture review,
   tech lead).

## Recommended Workflow

1. Scope the decision. If it fits in a PR description, it is not an
   ADR candidate.
2. Draft the ADR from the template. Status = Proposed.
3. Circulate for review (named deciders). Capture alternatives
   considered.
4. Mark Accepted with date and deciders on approval.
5. Update `docs/adr/INDEX.md` with one-line summary.
6. When superseding: new ADR sets Status = Accepted; old ADR flipped
   to Status = Superseded by ADR-NNNN with a link. Never delete.
7. Reference ADR numbers in subsequent PR descriptions and design
   docs.

## Official Sources Used

- Michael Nygard, "Documenting Architecture Decisions" —
  https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- Salesforce Architects — Solution Design Fundamentals —
  https://architect.salesforce.com/
