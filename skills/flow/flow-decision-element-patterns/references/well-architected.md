# Well-Architected — Decision Element

## Relevant Pillars

- **Reliability** — null-safe, ordered outcomes eliminate a large
  fraction of "why did it go down the wrong branch" incidents.
- **Operational Excellence** — named default + logged outcome ID makes
  triage minutes instead of hours.

## Architectural Tradeoffs

- **One big Decision vs many nested:** a flat decision with N outcomes
  is easier to reason about than a tree of depth 3; more outcome logic
  to maintain but less branching confusion.
- **Formula resource vs inline condition:** formula reuse is cleaner
  but recomputes each time. For hot paths benchmark before using.
- **Decision vs Sub-Flow dispatch:** if outcomes are heavyweight
  actions, split each into a sub-flow so the top-level flow is a
  router.

## Hygiene

- Default outcome is always named.
- Null checks are explicit, not absorbed in default.
- No Decision element nested more than 2 deep.
- Pick-list comparisons use API value.

## Official Sources Used

- Decision Element —
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_decision.htm
- Flow Operators —
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_operators.htm
