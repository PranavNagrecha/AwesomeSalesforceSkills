# Well-Architected — ADRs

## Relevant Pillars

- **Operational Excellence** — decisions with recorded rationale are
  auditable and reversible with eyes-open.
- **Reliability** — superseded decisions documented forward prevent
  teams re-trying a path that previously failed.

## Architectural Tradeoffs

- **Lightweight (Nygard) vs heavyweight (full RFC):** Nygard ADRs are
  one page and read fast. Heavyweight RFCs cover spec-level detail but
  slow the decision. Default to Nygard; escalate to RFC only for
  feature spec.
- **Central repo vs per-project:** one repo per team is best for
  discoverability. A single org-wide ADR repo gets skipped.
- **Proposed status vs direct-Accepted:** Proposed is valuable when a
  review cycle exists. Skip it when the decision has already been made
  and you are retroactively recording.

## Hygiene

- `docs/adr/INDEX.md` one-line summary per ADR, updated on every
  addition.
- Supersession links work both ways.
- Quarterly review to close out stale Proposed ADRs.
- Named deciders on every Accepted ADR.

## Official Sources Used

- Nygard — Documenting Architecture Decisions —
  https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- ThoughtWorks Technology Radar — ADRs —
  https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records
