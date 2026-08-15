# Examples — Salesforce ADRs

Five worked ADRs for decisions that actually recur on Salesforce programmes,
plus the index format and one worked example of a decision that should *not*
have become an ADR.

The distinguishing feature of a good Salesforce ADR is that its **Context**
cites the constraint that forced the decision — a governor limit, a licensing
boundary, a platform lifecycle date — rather than a preference. When a
`standards/decision-trees/` tree already routes the choice, the ADR's job is
not to re-derive the answer but to record which branch applied *here* and what
was true that made it apply.

---

## Example 1: A Decision The Tree Already Answers — Record The Branch, Not The Reasoning

**Why this one is first:** it is the most common Salesforce ADR and the one
most often written badly. Teams re-argue Flow vs Apex from first principles in
every ADR, producing three pages that a decision tree answers in one line — and
producing inconsistency, because each ADR's re-derivation lands somewhere
slightly different.

```markdown
# ADR-0014: Nightly account-hierarchy rollup runs as Batch Apex, not Scheduled Flow

## Status
Accepted — 2026-05-12 — Architecture Review Board

## Context
Finance needs a nightly rollup of child-account revenue onto the ultimate
parent. Volume today is ~1.9M Account rows; the acquisition closing in Q3
takes it to ~3.4M.

Two teams proposed different implementations in the same sprint, which is
what triggered this ADR rather than a PR comment.

Routing per `standards/decision-trees/automation-selection.md`:
  - Q1: trigger is "a scheduled clock" → Q10
  - Q10: "> 50k records or run > 5 minutes?" → yes → Batch Apex

Cross-checked against `standards/decision-trees/async-selection.md` Q1
("How many records / how long?") which routes the same way.

The cheat sheet in automation-selection.md is explicit for this shape:
"Process 2M records nightly → Batch Apex; second choice Queueable chain;
never Scheduled Flow."

## Decision
Implement as Batch Apex following `templates/apex/` conventions, scheduled
via a Schedulable wrapper so the job is also runnable ad hoc
(async-selection.md Q9).

## Consequences

### Positive
- Chunked transactions keep each scope inside per-transaction governor
  limits rather than relying on one interview surviving 3.4M rows.
- Failure isolation per scope: one bad batch does not lose the run.
- Re-runnable ad hoc for finance's month-end corrections.

### Negative
- Requires Apex test coverage (75% org-wide gate to deploy) that a Flow
  would not have required. Estimated 2 days of the 5-day build.
- The admin team cannot modify the rollup logic without a developer.
  Accepted: the rollup definition is stable and the fields are
  configuration-driven via Custom Metadata.
- Debugging is developer-side; there is no Flow debug UI equivalent.

## Alternatives Considered

### Scheduled Flow
Rejected: automation-selection.md routes explicitly away from this at the
stated volume. The specific failure is the 24-hour interview allocation,
which the tree calls out for mass-reparent/reassign shapes.

### Queueable chain
Rejected as first choice, retained as the documented fallback. It handles
the volume but gives worse operational visibility than Batch's job status
records, and finance wants a per-run status they can look at.

## Decision Trees Consulted
- `automation-selection.md` — Q1 → Q10
- `async-selection.md` — Q1, Q9

## Date
2026-05-12

## Deciders
- R. Patel (Platform Architect), J. Okafor (Finance Systems Lead),
  Architecture Review Board
```

**What makes this ADR good:** it is short because the tree did the reasoning.
It records *which branch* and *what was true* (1.9M rows today, 3.4M after Q3)
so a future reader can check whether the input still holds. If volume ever
drops below the threshold, the ADR tells you exactly which fact to re-test.

**What would make it bad:** three paragraphs re-arguing Flow versus Apex in
general terms. That belongs in the tree, and duplicating it there means the two
can drift.

---

## Example 2: A Sharing Model Decision — The Ordering Is The Decision

**Context:** A new `Claim__c` object. Adjusters must see their own claims;
supervisors must see their team's; a fraud unit must see everything; external
partners must see a filtered subset.

```markdown
# ADR-0021: Claim__c access model — Private OWD with criteria-based sharing,
#           Apex Managed Sharing deferred

## Status
Accepted — 2026-06-03 — Architecture Review Board

## Context
Four audiences with different needs on one new object. The temptation
raised in design review was Apex Managed Sharing "because the rules are
complicated," which would have been decided before OWD was even set.

`standards/decision-trees/sharing-selection.md` prescribes a 7-step design
sequence and requires it be done in order. Walking it:

  Q1  OWD for Claim__c            → set to Private. Nothing is added
                                    before the default is tight.
  Q2  Role hierarchy              → supervisors sit above adjusters;
                                    "Grant access using hierarchies" ON
                                    covers the supervisor case with zero
                                    configuration.
  Q3  Criteria-describable?       → fraud unit = "anyone in the Fraud role
                                    should see records where
                                    Fraud_Flag__c = true" → Criteria-Based
                                    Sharing Rule.
  Q4  Per-record ad hoc?          → no standing requirement.
  Q5  Apex Managed Sharing        → prerequisites are met (OWD Private,
                                    RowCause understood) but NO requirement
                                    survives Q2 and Q3. Not needed.
  Q9  External users              → partner access handled through the
                                    Experience Cloud sharing model, which
                                    the tree treats as a separate world.

## Decision
OWD Private. Role hierarchy for supervisor access. One criteria-based
sharing rule for the fraud unit. Experience Cloud sharing set separately
for partners. **No Apex Managed Sharing.**

## Consequences

### Positive
- Three of four audiences are served by declarative configuration that
  admins can audit in Setup.
- No `__Share` records to maintain, no recalculation on owner change, no
  custom sharing reason to document.

### Negative
- The fraud unit's rule depends on `Fraud_Flag__c` staying accurate.
  A wrong flag is now an access issue, not just a data issue. Mitigated
  by making the field automation-set and read-only on the layout.
- Criteria-based sharing recalculation has a latency the business must
  accept: a newly flagged claim is not instantly visible to the fraud
  unit.

## Alternatives Considered

### Apex Managed Sharing for all four audiences
Rejected. sharing-selection.md Q5 lists prerequisites, all of which we
meet — so this was viable, not impossible. It loses because Q2 and Q3
resolve three audiences declaratively, and Apex Managed Sharing would put
that access behind code, tests, a recalculation job, and a deployment for
every rule change. The tree's ordering exists precisely to prevent
reaching for Q5 before Q2 and Q3 have been tried.

### Public Read-Only OWD with Restriction Rules
Rejected. The tree is explicit that a loose OWD should be tightened before
anything is added, and that Restriction Rules are for removing access
another layer grants — not a substitute for setting the default correctly.

## Decision Trees Consulted
- `sharing-selection.md` — the 7-step sequence; Q1, Q2, Q3, Q5, Q9

## Date
2026-06-03

## Deciders
- R. Patel (Platform Architect), M. Lindqvist (Security Lead),
  D. Osei (Claims Operations), Architecture Review Board
```

**What makes this ADR good:** the *rejected* alternative was genuinely viable —
the Apex Managed Sharing prerequisites were met — so the ADR has real content.
An ADR whose alternatives were all impossible is a declaration wearing an ADR's
clothes.

---

## Example 3: A Platform Lifecycle Decision — Deciding To Wait, With A Trigger

**Context:** An existing Salesforce CPQ implementation, and a strategic
question about Revenue Cloud Advanced.

```markdown
# ADR-0027: Remain on Salesforce CPQ through FY27; re-evaluate at two
#           named triggers

## Status
Accepted — 2026-07-21 — Architecture Review Board + CFO

## Context
Salesforce CPQ has entered an end-of-sale phase: new customers can no
longer purchase it, and Salesforce's product investment has moved to
Revenue Cloud Advanced. Existing customers retain support and can renew.
Salesforce has NOT announced an end-of-life date; CPQ is described as
being in a maintenance phase — supported and receiving critical fixes,
but not new feature development.

<!-- UNVERIFIED: a specific end-of-sale date of 27 March 2025 circulates
widely in consultancy writing. I could not confirm it from a Salesforce
source: https://www.salesforce.com/sales/cpq/end-of-life/ returns 403 to
a document fetcher. Any real ADR must confirm the date and the current
support commitment with the account team and record what they said,
with the date they said it. -->

Our CPQ implementation is 4 years old, heavily customised (61 price
rules, 14 custom quote-line fields, 3 custom quote calculator plugins).
Migration estimates from three partners cluster around 12-18 months.

This is an ADR rather than a roadmap item because the decision to WAIT is
itself a decision with consequences, and because without a written record
the question gets re-raised every quarter by a different stakeholder.

## Decision
Remain on Salesforce CPQ through FY27. Do not begin migration work.
Re-evaluate immediately if EITHER trigger fires:

  Trigger A: Salesforce announces an end-of-life date for CPQ.
  Trigger B: a business requirement lands that Revenue Cloud Advanced
             supports and CPQ demonstrably cannot.

Owner of the trigger watch: Platform Architect, reviewed quarterly at ARB.

## Consequences

### Positive
- No new feature development on CPQ means our customisation surface stops
  growing, which makes an eventual migration cheaper, not more expensive.
- Avoids committing 12-18 months of capacity against a deadline that has
  not been set.

### Negative
- We accumulate 12-24 months of additional customisation debt if teams
  keep extending CPQ. Mitigated: a change-control gate on new CPQ price
  rules from 2026-09-01.
- If Trigger A fires late, we compress a 12-18 month migration into
  whatever remains. This is the risk being accepted, explicitly, by the
  named deciders.
- Recruiting for CPQ skills gets harder as the market moves.

## Alternatives Considered

### Begin migration to Revenue Cloud Advanced in FY26
Rejected on capacity, not on merit. The same engineers are committed to
the Service Cloud consolidation through Q2 FY27. Doing both produces two
late programmes.

### Replace CPQ with a third-party quoting tool
Rejected: moves us off the platform's data model for the sake of avoiding
one migration, and buys a second integration surface. Reconsider only if
Trigger A fires with a short window.

## Review Trigger
Quarterly at ARB, plus immediately on Trigger A or Trigger B.

## Date
2026-07-21

## Deciders
- R. Patel (Platform Architect), S. Ahmed (CFO),
  L. Byrne (Revenue Operations Director), Architecture Review Board
```

**What makes this ADR good — and it is the least obvious of the five:** it
records a decision *not to act*, with **named triggers** and an **owner for the
trigger watch**. Most "we'll wait and see" decisions are never written down,
which is why they get re-litigated quarterly and why nobody notices when the
conditions change. It also honestly labels the unverified date rather than
laundering a blog post into an architecture record.

---

## Example 4: Supersession Done Properly

**Context:** ADR-0014 (Example 1) is 18 months old. The rollup moved to a
platform-event-driven incremental model.

**The superseding ADR:**

```markdown
# ADR-0039: Account rollup moves to incremental, event-driven updates

## Status
Accepted — 2027-11-04 — Architecture Review Board
Supersedes ADR-0014.

## Context
ADR-0014 chose nightly Batch Apex at ~1.9M rows, correctly per
`automation-selection.md` Q10 at the time. Two inputs it recorded have
changed:

  - Volume is now 4.1M rows and the nightly window no longer fits.
  - The business requirement changed from "accurate each morning" to
    "accurate within 15 minutes", which no nightly job satisfies at any
    volume.

The second change is the decisive one. ADR-0014 was not wrong; its
premise expired.

## Decision
Publish a Platform Event on child-account revenue change; an Apex
subscriber applies an incremental delta to the parent. Retain the batch
job, reduced to a nightly reconciliation pass over the last 24 hours
rather than a full recompute.

## Consequences
### Positive
- Meets the 15-minute freshness requirement.
- Nightly window shrinks from ~6 hours to ~20 minutes.

### Negative
- Two code paths (incremental + reconciliation) instead of one. Accepted:
  the reconciliation pass is the safety net that makes the incremental
  path's at-least-once delivery tolerable.
- Platform Event publish allocation now on the monitoring dashboard.

## Alternatives Considered
### Keep the batch job and shorten the interval
Rejected: hourly full recompute at 4.1M rows does not fit, and does not
meet 15 minutes regardless.

### Rollup summary fields
Rejected: the hierarchy is not a master-detail relationship and
restructuring it is out of scope.

## Date
2027-11-04

## Deciders
- R. Patel (Platform Architect), J. Okafor (Finance Systems Lead)
```

**And the edit to the superseded ADR — the only edit ever made to it:**

```markdown
# ADR-0014: Nightly account-hierarchy rollup runs as Batch Apex, not Scheduled Flow

## Status
Superseded by ADR-0039 on 2027-11-04.

## Context
[unchanged — this is the record of what was true in May 2026]
...
```

**What makes this correct:** the original's Context, Decision, Consequences,
and Alternatives are untouched. Only the Status line changes, and it links
forward. ADR-0014's value now is historical: it tells a future reader that
Batch Apex was the right call at 1.9M rows with a next-morning requirement, so
nobody re-proposes reverting without checking whether those inputs came back.

Note also *why* the supersession happened: **a premise expired**, not a mistake
was found. ADR-0039 says so explicitly. That distinction matters, because
"ADR-0014 was wrong" would teach a future reader to distrust the tree's Q10
routing, which is not the lesson.

---

## Example 5: A Decision That Should Not Have Been An ADR

**The draft someone wrote:**

```markdown
# ADR-0031: Use TriggerHandler for the new Shipment__c trigger

## Status
Proposed

## Context
Shipment__c needs a trigger.

## Decision
Use the repo's TriggerHandler framework.
```

**Why it fails the candidacy test:** ADR-0003 already adopted TriggerHandler
across all trigger code. Applying an existing decision to a new object is not a
new decision — it is compliance with one. Writing it as an ADR does three kinds
of damage:

1. It dilutes the index. A reader scanning 40 ADRs to find the 6 that matter is
   a reader who stops scanning.
2. It implies the choice was open, inviting a future reader to think
   TriggerHandler was optional for `Shipment__c` specifically.
3. It has no Alternatives Considered, because there genuinely were none — which
   is the diagnostic.

**Where it belongs:** the PR description. `"Follows ADR-0003 (TriggerHandler
framework)."` One line, correctly cited, in the place a reviewer will see it.

**The test to apply:** *if this fits in a PR description, it is not an ADR.*
The corollary is more useful: *if you cannot name two alternatives that a
reasonable person could have chosen, the decision is not open — you are
documenting a standard, not deciding.*

---

## The Index

`docs/adr/INDEX.md` is the artifact people actually read. Keep it scannable.

```markdown
# Architecture Decision Records

| # | Decision | Status | Date |
|---|---|---|---|
| [0003](./0003-adopt-trigger-handler-framework.md) | Adopt TriggerHandler across all trigger code | Accepted | 2026-02-14 |
| [0014](./0014-nightly-rollup-batch-apex.md) | Nightly account rollup as Batch Apex | **Superseded by [0039](./0039-incremental-rollup-platform-events.md)** | 2026-05-12 |
| [0021](./0021-claim-access-model.md) | Claim__c: Private OWD + criteria-based sharing | Accepted | 2026-06-03 |
| [0027](./0027-remain-on-cpq-through-fy27.md) | Remain on Salesforce CPQ through FY27 | Accepted — **review trigger active** | 2026-07-21 |
| [0039](./0039-incremental-rollup-platform-events.md) | Incremental event-driven account rollup | Accepted | 2027-11-04 |

## Open review triggers

| ADR | Trigger | Owner | Last checked |
|---|---|---|---|
| 0027 | Salesforce announces a CPQ end-of-life date | Platform Architect | 2027-10-01 |
| 0027 | A requirement lands that RCA supports and CPQ cannot | Revenue Ops Director | 2027-10-01 |
```

The **open review triggers** table is the part most ADR indexes lack and the
part that makes "decide to wait" decisions safe. Without it, a review trigger is
a sentence in a document nobody re-reads.

---

## File Naming And Numbering

```text
docs/adr/
├── 0003-adopt-trigger-handler-framework.md
├── 0014-nightly-rollup-batch-apex.md
├── 0021-claim-access-model.md
├── 0027-remain-on-cpq-through-fy27.md
├── 0039-incremental-rollup-platform-events.md
└── INDEX.md
```

Four-digit zero-padded, globally sequential, kebab-case slug summarising the
decision. Never per-team or per-domain subdirectories: teams reorganise, and a
number that has to be qualified by a folder is a number nobody can cite in a PR
description.

Store them in the repository they describe. An external wiki goes stale because
nothing about changing the code forces anyone to look at it; a file in
`docs/adr/` shows up in a diff.
