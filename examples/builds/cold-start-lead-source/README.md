# Worked example — Original Lead Source, cold start run 1 (no tier, status none)

Cold-start scenario, run 1: scenario 5 of the definition of done. The loop was never found, so there is no
`plan.json`, no tier and no build status.

**What was tested.** A fresh Sonnet session with no operator context, no prior conversation and no
org was given the repository path, its `CLAUDE.md`, and one client sentence: *"When a Lead is
converted, the new Opportunity should carry the Lead's Lead Source in a custom field called Original
Lead Source, so marketing can report on it later without it being overwritten."* It was told to do
whatever the repo says to do, to answer any human question as the client would, and to keep a log.
The log is `drivers-log.md` (written by that session, unedited). The deliverable is `deliverable/`.

## Result in one line

The library worked cold; the orchestration loop was invisible cold.

## What the session produced (about 7 minutes wall clock, 27 tool calls)

- Found the on-point skill on the first search (`admin/lead-management-and-conversion`), read it in
  full, and used its metadata example to avoid a real trap: Map Lead Fields accepts custom Lead fields
  only, so the literal ask ("map Lead Source") is not a mechanism. It designed a custom field plus a
  before-save record-triggered Flow that snapshots `LeadSource` once at Opportunity creation, cited
  the automation-selection tree branch, and copied the Flow skeleton template.
- Answered three client questions on the client's behalf with a confidence level each (scope: every
  Opportunity, not conversion-only, since no declarative signal distinguishes them; Text(255) not
  picklist, per the skill's value-set-drift gotcha; history tracking on).
- Wrote a design document with a sandbox test plan, a review checklist, process observations and
  citations. It never deployed and never wrote into the repo.

## What it missed, graded against the loop it never found

| The loop would have | The cold session | Weight |
|---|---|---|
| Sized the ask (`scale: ask`) and asked the skill's question table — ~13 questions, one gate | Asked 3 of its own, answered them itself, recorded that it did | medium: the three it chose were the right three; the ten it skipped are the ones a client rarely thinks of (who owns the field, reporting on converted-from-lead only, backfill) |
| Run every cited skill's checker before claiming done | Ran none ("could not run the lead checker meaningfully") | **high** — run after the fact by the operator: record-triggered-flow checker 0 issues; fault-handling 0; element-naming 0 errors, 1 INFO (label echoes API name); lead-conversion checker 1 advisory (no `LeadConvertSettings` in the package — a false positive here, the package adds no Lead field) |
| Left a record: `plan.json`, `RUN.md`, decisions, an envelope | A design doc and a log in a scratch directory | medium: fine for one field; nothing to hand a second person |
| Stopped at a human gate | Stopped at "nothing more is possible without an org" | low: same stopping point in practice |

Quality of the design itself: correct. The operator confirmed the platform claim it rests on against
the skill's metadata example and the checkers above; nothing in the deliverable is wrong.

## Why it missed the loop

`CLAUDE.md`'s first workflow section is "Required Workflow For Skill Creation Or Skill Updates"; the
session correctly recognised its task was not that, inferred "run-time agent" from the roster
section, found no agent scoped to one field, and applied the skill directly. The Build Orchestration
section sat 260 lines down and read as a description of a layer, not as the entry point for a client
ask. Its own words: *"nothing in CLAUDE.md names which document to read for the latter case."*

## Fix applied (same day)

`CLAUDE.md` now opens with **"Two Ways In"**: (1) you were asked to make a Salesforce change → start
the loop at the tier § 3.1 prints; (2) you are changing the library → the authoring workflow. A second
cold-start run on a different ask of the same size (`examples/builds/cold-start-case-escalation-email/`
if it lands) tests whether that paragraph is enough.

## Other friction the session named

- `scripts/bootstrap.py --verify-only` exits 1 with "BOOTSTRAP FAILED" when only the local
  slash-command install is stale while retrieval verifies OK; the headline should not outrank the
  detail. Queued.
- No run-time agent owns "one field plus one Setup nuance"; the roster is object-, process- or
  audit-shaped. The loop's ask tier is the intended home for that size — which is the discoverability
  point above, not a roster gap.
