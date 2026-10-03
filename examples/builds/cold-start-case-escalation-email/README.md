# Worked example — Case Escalation Email Alert to Account Owner, cold start run 2 (feature tier, status `done`)

Cold-start scenario, run 2: "email the Account Owner when a Case is escalated".

**What was tested.** The same experiment as `examples/builds/cold-start-lead-source/` (a fresh Sonnet
session, no operator context, no org, one client sentence, told only to read `CLAUDE.md` and do what
it says), run again after `CLAUDE.md` gained its "Two Ways In" entry point. Different ask of the same
size: *"When a Case on an account gets escalated, email the Account Owner so they know their customer
is unhappy. Include the case number and subject."* The log is `drivers-log.md` (written by that
session, unedited). The rest of this folder is the exported build directory.

## Result in one line

One paragraph in `CLAUDE.md` was enough: the session found the loop, sized the ask, and drove it to
`status: done` unaided — at four times the wall clock and twice the tokens of run 1.

## Run 1 vs run 2

| | Run 1 (loop not found) | Run 2 (loop found) |
|---|---|---|
| Wall clock | ~7 min | ~31 min |
| Tool calls / tokens | 27 / 177k | 140 / 390k |
| Tier | none | `feature` — the D/S/O/X rule counted two objects (Case, Account); the session noted the ask "felt like" `ask` and followed the printed rule anyway |
| Questions asked | 3, self-chosen | 19 harvested from three skills; 4 blocking answered as the client, 15 defaulted and recorded as such |
| Gates | none | clarifications, plan, milestone — each signed "Client (proxy answer — no live stakeholder)" with the reasoning in the notes |
| Checkers run before "done" | none | the record-triggered-flow checker plus the xml and manifest checks, all clean; two real defects caught by running checkers against fixtures first |
| Record left | a design doc in a scratch directory | `plan.json`, `PLAN.md`, decisions, traceability, a milestone report with merged manifest, envelopes for every stage |
| Design | correct | correct: after-save Flow on `IsEscalated` becoming true, Account Owner resolved with no-Account and queue-owned-Account branches, fault path that logs and alerts an admin; native escalation actions ruled out with the tree branch quoted |

## What the loop still let through

The operator ran the two flow checkers the plan did **not** declare: `fault-handling` is clean;
`flow-element-naming-conventions` reports **3 errors** (a formula, a text template and a variable
carry no resource-type prefix). The planner cited three skills and declared one checker; the naming
skill was not among the three. That is a planner gap, not a session error: a Flow step should declare
every flow checker in the library, not only the pattern skill's. Filed for the planner playbook.

## What the session named as friction (its own words, condensed)

- Its own stage-2 judgement excluded `admin/flow-for-admins`, which held the only `emailSimple` XML
  example; caught later, cost time.
- A skill's checker is scoped much narrower than its prose — visible only by running it on a fixture.
- § 3.1 is ambiguous about where the feature tier's "optional" workbook content should land.
- Bookkeeping volume: envelope, markdown twin and validate, six times over, for a one-step build.

## Verdict for the product question

The library alone produces a correct answer fast. The loop produces a correct answer with a record a
second person can audit, at a real cost in time and tokens, and a cold reader can now find it. The
next cost to attack is the bookkeeping per stage at the small tiers, not discoverability.
