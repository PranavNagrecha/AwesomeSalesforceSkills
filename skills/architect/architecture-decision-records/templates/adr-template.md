# ADR-XXXX: <one-line decision, active voice>

<!--
CANDIDACY CHECK — delete this block before committing.

Promote to an ADR only if ANY holds:
  [ ] Multi-quarter impact (platform choice, pattern adoption, org topology,
      integration approach, sharing model, licensing posture)
  [ ] Reverses an earlier recorded choice
  [ ] The 6-month test: a joiner will ask "why did we do this?"

Stop if EITHER holds:
  [ ] It fits in a PR description  -> write it there, citing the existing ADR
  [ ] You cannot name two alternatives a competent person could have chosen
      -> you are documenting a standard, not deciding
-->

## Status

Proposed | Accepted | Rejected | Superseded by ADR-YYYY on YYYY-MM-DD

<!-- Use Proposed only if a real review forum exists and will close it.
     Otherwise write Accepted retrospectively — a legitimate mode, not a
     degraded one. A directory of year-old Proposed ADRs teaches readers to
     stop trusting the index. -->

## Context

What forces are at play? What constraints? What pushed us to this decision
point?

### Inputs at the time of this decision

<!-- THE MOST IMPORTANT SECTION. A future reader re-tests these to decide
     whether the decision still holds. Without them, revisiting means
     re-litigating from scratch. Be numeric where you can. -->

- Volume / scale:
- Governor or platform limits that bind:
- Business requirement (latency, freshness, availability):
- Org / licensing context:
- Team capacity or skills constraint, if it shaped the choice:

### Platform claims and their sources

<!-- Every lifecycle, retirement, GA, or limit claim needs a Salesforce-hosted
     URL, or a named person plus the date they confirmed it. Consultancy blogs
     are not sources for an architecture record. An ADR is never updated, so an
     unsourced date here is load-bearing forever. -->

| Claim | Source (Salesforce URL, or name + date confirmed) |
|---|---|
|  |  |

<!-- Mark anything you could not verify, rather than asserting it:
     <!-- UNVERIFIED: <claim>. Circulates in community writing; not confirmed
     from a Salesforce source as of YYYY-MM-DD. -->

### Managed package constraints, if any

| Package | Version tested | Constraint | How established (ticket #, doc URL, scratch-org test) |
|---|---|---|---|
|  |  |  |  |

## Decision Trees Consulted

<!-- Cite the branch. Do NOT re-derive the tree's reasoning — that creates a
     second source for the same rule, and they diverge on the first update. -->

- `standards/decision-trees/<tree>.md` — Q_ (<condition>) → Q_ → <outcome>
- (or) No tree covers this scenario. Gap raised: <link / issue>

<!-- Deviating from a tree? That is precisely an ADR. State the branch, why
     this situation is the exception, and what would have to be true for the
     exception to end. -->

## Decision

The choice, stated clearly and in the active voice.

## Consequences

### Positive

- ...

### Negative

<!-- At least one, and make it specific enough to be checkable.
     Not "some added complexity" — "two code paths instead of one", or
     "the admin team can no longer change this without a developer".
     Forcing question: what will the team writing the SUPERSEDING ADR
     complain about? If nothing comes to mind, this was not a tradeoff. -->

- ... (at least one required)

### Licensing and org-limit consequences

<!-- Required for org-topology, environment-strategy, and platform-boundary
     decisions — these bind more often than the topology does. Delete this
     subsection if genuinely not applicable. -->

- Licence counts / types:
- Sandbox allocation and refresh intervals:
- Org-level limits now shared rather than per-team:
- Data residency:
- New integration surface between orgs:

## Alternatives Considered

<!-- Each must be something a competent person could actually have chosen.
     "We could have hardcoded it" is a strawman, not an alternative.
     The strongest ADRs reject an option that was genuinely viable. -->

### Alternative A

Why rejected — and what would have had to be different for it to win:

### Alternative B

Why rejected — and what would have had to be different for it to win:

## Review Trigger

<!-- Required when the decision rests on a CURRENT PLATFORM LIMITATION rather
     than an architectural principle. Salesforce ships three releases a year;
     "Flow cannot do X yet" expires, "this needs assertion-style tests behind a
     coverage gate" does not.

     Also required for any "decide to wait" decision.

     A calendar date is NOT a trigger — nothing fires it. Use a CONDITION,
     and name an owner. Then surface it in INDEX.md's open-triggers table. -->

- Trigger A: <condition>
- Trigger B: <condition>
- Owner of the trigger watch: <name (role)>
- Review cadence: <forum, frequency>

## Date

YYYY-MM-DD

<!-- The date the DECISION was made. Never updated. If wording changes later,
     add a "Last edited: YYYY-MM-DD" footer instead. Status transitions carry
     their own dates in the Status line. -->

## Deciders

<!-- Named people with the role they held AT THE TIME, plus the forum.
     "Tech Lead" loses information the moment the role changes hands, and the
     fastest way to revisit a decision is usually a five-minute conversation
     with whoever made it. -->

- Name (role), Name (role), Forum (e.g. Architecture Review Board / CAB)

---

<!--
ON SUPERSESSION — for the person who eventually replaces this ADR.

Write a NEW ADR. The ONLY edit to this file is its Status line:

    ## Status
    Superseded by ADR-NNNN on YYYY-MM-DD.

Everything else here is frozen. Its value is entirely historical: it records
what was true when, which is the only thing that lets a reader judge whether
today's premises still hold.

In the NEW ADR, state WHY: a premise EXPIRED, or a mistake was FOUND.
Those teach different lessons.

Never delete an ADR. A missing number reads as an error; a superseded one
reads as history.
-->
