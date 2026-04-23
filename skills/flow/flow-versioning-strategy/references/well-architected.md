# Well-Architected Notes — Flow Versioning

## Relevant Pillars

- **Reliability** — paused-interview-safe versioning prevents the
  "resume fails six months later" class of bug.
- **Operational Excellence** — cleanup cadence + changelog keeps the
  version list reviewable rather than sprawling.

## Architectural Tradeoffs

- **New version vs new flow:** new version is cheaper for non-breaking
  changes; new flow is the only safe path for breaking changes that
  span paused interviews or long-scheduled jobs.
- **Retention depth vs clutter:** 3 inactive versions is the sweet spot
  — enough for rollback, few enough to reason about.
- **Auto-cleanup vs manual:** auto is efficient but risky in the
  presence of paused interviews; manual with a weekly cadence balances
  speed and safety.

## Hygiene

- Per-flow changelog.
- Paused-interview age alert.
- Activation checklist on PRs.

## Official Sources Used

- Flow Versioning —
  https://help.salesforce.com/s/articleView?id=sf.flow_distribute_version.htm
- Paused Interviews —
  https://help.salesforce.com/s/articleView?id=sf.flow_concepts_runtime_paused.htm
