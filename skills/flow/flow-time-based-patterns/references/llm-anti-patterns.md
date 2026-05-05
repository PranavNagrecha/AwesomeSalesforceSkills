# LLM Anti-Patterns — Flow Time-Based Patterns

Mistakes AI coding assistants commonly make when advising on
time-based Flow patterns.

---

## Anti-Pattern 1: Recommending a Wait element in a record-triggered flow

**What the LLM generates.** "Add a Wait element to your record-triggered
flow with a 2-day duration to schedule the reminder."

**Why it happens.** "Flow has a Wait element" is the surface fact;
the runtime restriction (autolaunched / orchestration only) isn't
salient.

**Correct pattern.** Record-triggered flows pause via Scheduled Paths
off the trigger event. Wait is autolaunched / orchestration only.

**Detection hint.** Any record-triggered-flow recommendation with a
Wait element is wrong by construction.

---

## Anti-Pattern 2: Scheduled Path "+1 day at 9 AM" without time-zone disclosure

**What the LLM generates.** "Set a Scheduled Path to fire at 9 AM
the next day."

**Why it happens.** "9 AM" is a familiar-sounding time. Doesn't
surface that "9 AM in *whose* time zone" is the real question.

**Correct pattern.** Always disclose the time-zone basis: running
user (Scheduled Path), org default (Scheduled Flow), UTC (DateTime
literal). Match to the requirement.

**Detection hint.** Any "fire at HH:MM" recommendation without
specifying whose time zone is incomplete.

---

## Anti-Pattern 3: Forgetting to enable recheck-entry-condition

**What the LLM generates.** Setup steps for a reminder Scheduled
Path that don't mention the recheck toggle.

**Why it happens.** Recheck is off by default; setup tutorials skip
it; the LLM doesn't surface why it matters.

**Correct pattern.** For any Scheduled Path with a delay > a few
minutes, recommend enabling recheck-entry-condition. Document the
recheck criteria explicitly (`Status != 'Closed' AND IsDeleted =
FALSE`).

**Detection hint.** Any reminder-Path recommendation that doesn't
discuss "what should happen if the record changes" is missing the
core reliability decision.

---

## Anti-Pattern 4: Path with negative offset against possibly-past dates

**What the LLM generates.** "Use `-2 days from PromotionEnd__c` to
remind 2 days before."

**Why it happens.** Looks like the right offset. Doesn't surface
that past-dated records fire immediately.

**Correct pattern.** Combine with entry condition `<DateField> >=
TODAY` (or appropriate buffer) so past-dated records don't enter the
flow.

**Detection hint.** Any negative-offset Scheduled Path
recommendation without an "and the date hasn't already passed"
guard is going to surprise on backfilled or revised records.

---

## Anti-Pattern 5: Workflow Rule migration that loses "or updated"

**What the LLM generates.** "Migrate this Workflow Rule to a
record-triggered flow set to 'Run when a record is created'."

**Why it happens.** "Created" is the simpler trigger; the LLM picks
the simpler option without confirming the original WFR's "every
time it's edited" clause.

**Correct pattern.** Confirm the original WFR's evaluation setting:
"created", "edited", or "created and any time edited". Map to the
flow's "Run when a record is created" / "updated" / "created or
updated" appropriately.

**Detection hint.** Any WFR-to-Flow migration that doesn't surface
the trigger-evaluation choice is going to drop half the original
behavior.

---

## Anti-Pattern 6: Suggesting Scheduled Apex when Scheduled Flow fits

**What the LLM generates.** "Implement a `Schedulable` Apex class to
run nightly cleanup."

**Why it happens.** Apex is the canonical Salesforce scheduling
answer in older docs; Scheduled Flow is newer and underrepresented.

**Correct pattern.** For modest-volume admin-owned work, Scheduled
Flow is the simpler answer — no Apex test class, no deploy of code,
configurable by admins. Reach for Scheduled Apex only when:
- Volume justifies Batch Apex chunking.
- Logic is complex enough that Flow becomes hard to read.
- Existing scheduled Apex jobs already do similar work.

**Detection hint.** Any "schedule this work nightly" recommendation
that defaults to Apex without weighing Scheduled Flow is missing the
admin-owned option.

---

## Anti-Pattern 7: Treating Scheduled Path queue as cancellable via UI

**What the LLM generates.** "If you need to cancel a queued
Scheduled Path, navigate to Setup → Paused and Failed Flows and
delete it."

**Why it happens.** Mixed metaphor — Paused Flows (Wait elements)
ARE cancellable that way; queued Scheduled Paths are not.

**Correct pattern.** Scheduled Paths can't be cancelled directly.
Use a kill-switch on the source record (a `Cancel_Path__c` boolean
that the Path body checks first and early-exits on). Document this
as the cancel mechanism upfront.

**Detection hint.** Any "delete the queued path" recommendation for
Scheduled Paths is wrong; the cancel pattern is recheck-condition
driven.
