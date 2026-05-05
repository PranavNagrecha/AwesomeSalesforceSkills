# Gotchas — Flow Time-Based Patterns

Non-obvious time-based Flow behaviors that cause real production
incidents.

---

## Gotcha 1: Scheduled Path uses the running user's time zone, not the org's

**What happens.** A "+1 day at 9 AM" Scheduled Path on a global
record-triggered flow fires at 9 AM **in each saving user's time
zone**. EMEA-saved records → 9 AM London. APAC → 9 AM Tokyo.

**When it occurs.** Multi-region teams using a single Scheduled
Path with an "at 9 AM" offset.

**How to avoid.** Either store a UTC fire time on the record and
schedule against that field, or move the logic to a Scheduled Flow
(which uses the org default TZ instead).

---

## Gotcha 2: Negative offset against past date fires immediately

**What happens.** Path with `-2 days from Promotion_End__c` against
a record whose `Promotion_End__c` is already in the past — fires
immediately, not "doesn't fire".

**When it occurs.** Backfilled records, or records whose date was
revised to a past value.

**How to avoid.** Entry condition checks `<DateField> >= TODAY` (or
appropriate buffer) so past-dated records don't enter the flow at
all. Or check inside the Path body and early-exit.

---

## Gotcha 3: Recheck-entry-condition is OFF by default

**What happens.** Scheduled Path queued at trigger fire time fires
when its scheduled time arrives, regardless of whether the source
record still meets the entry criteria.

**When it occurs.** Default Scheduled Path setup with no toggle
flipped.

**How to avoid.** Enable "Recheck the entry condition" on every
Scheduled Path where the source record can change between queue and
execution. This is almost always the case for any path with a
delay > a few minutes.

---

## Gotcha 4: Wait elements are NOT available in record-triggered flows

**What happens.** Admin builds a record-triggered flow and looks for
the Wait element. It doesn't exist in the toolbox.

**When it occurs.** Mental model that "Flow has Wait" — true for
autolaunched / orchestration only.

**How to avoid.** Record-triggered flows pause via Scheduled Paths
off the trigger event. To use a Wait element, the work has to live
in an autolaunched flow that the record-triggered flow invokes.

---

## Gotcha 5: Scheduled Flows use org-default TZ, not the configurer's

**What happens.** Admin in San Francisco configures a Scheduled
Flow "daily at 6 AM". Org's default TZ is London. Flow fires at
6 AM London (10 PM PT the night before, from admin's perspective).

**When it occurs.** Admin's local TZ ≠ org default TZ.

**How to avoid.** Confirm the org-default TZ before configuring a
Scheduled Flow. If admin's TZ matters, document the schedule in
the org's TZ and convert.

---

## Gotcha 6: Source record deletion doesn't cancel queued Scheduled Paths

**What happens.** Record is deleted. Scheduled Path remains queued
and fires at scheduled time. The Path body's Get Records / Update
Records / Send Email runs against a deleted record — most operations
fail; some surface confused errors.

**When it occurs.** Cleanup deletes, merge operations, or
sandbox-refresh post-cleanup automation.

**How to avoid.** Recheck condition includes `IsDeleted = FALSE`.
Or wrap Path body in IsDeleted decision branch that early-exits.

---

## Gotcha 7: "Created or updated" Workflow Rule maps to flow run-trigger configuration

**What happens.** Admin migrates a Workflow Rule that "evaluates
every time a record is created or edited" to a record-triggered
flow. Picks "Run when a record is created" only. Lose the "or
updated" half — the new flow fires only on insert.

**When it occurs.** Workflow Rule → Flow migrations following the
deprecation timeline.

**How to avoid.** "Created and updated" maps to **Run when: A
record is created or updated** in the flow start. Verify the
specific WFR option ("created" / "edited" / "created and any time
edited") and pick the matching flow trigger.

---

## Gotcha 8: Scheduled Paths can't be cancelled directly

**What happens.** Admin discovers a Scheduled Path was misconfigured
(wrong recipient, wrong message). Wants to cancel queued instances
before they fire. There's no UI to cancel them.

**When it occurs.** Production hotfix scenarios.

**How to avoid.** Recheck condition + a kill-switch on the source
record (e.g. a `Cancel_Path__c` boolean checked in the Path body's
first decision). When the admin needs to cancel, they update all
affected records to set the kill switch, and the Paths early-exit
at execution time.

---

## Gotcha 9: Wait element in autolaunched flow doesn't survive a release

**What happens.** A Wait element in an autolaunched flow paused for
3 days on Aug 1. The flow definition is updated and re-deployed on
Aug 2. The paused interview's element references may be stale; the
resume on Aug 4 may fail.

**When it occurs.** Long-running Wait elements in flows that get
deployed mid-pause.

**How to avoid.** Keep Wait pause durations short (hours, not days)
when the flow definition might be updated. For long pauses, prefer
Scheduled Paths in record-triggered flows or Scheduled Flows on
cron — both re-resolve their definition at execution time.
