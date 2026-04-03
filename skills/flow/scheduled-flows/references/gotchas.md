# Gotchas - Scheduled Flows

## Recurring Jobs Need Duplicate Prevention

**What happens:** The same record gets updated, emailed, or tasked over and over again across recurring runs.

**When it occurs:** The design has no processed flag, last-run marker, or other idempotent rule.

**How to avoid:** Make recurring state explicit in the data model and use it in both entry criteria and downstream logic.

---

## Broad Start Criteria Become Operational Problems Quickly

**What happens:** A job that looked harmless in testing grows into an unpredictable nightly sweep.

**When it occurs:** The start criteria are loose, and the worst-case record volume was never modeled.

**How to avoid:** Bound the record set tightly and design for the high-volume day, not just the median day.

---

## Heavy Batch Work Still Wants Apex

**What happens:** The flow keeps absorbing more loops, related-record writes, or expensive logic because it already owns the schedule.

**When it occurs:** Teams confuse ownership of timing with suitability as the execution engine.

**How to avoid:** Keep the schedule in Flow only if the actual work remains a good fit. Otherwise escalate the heavy step.

---

## Not Every Time Requirement Needs A Scheduled Flow

**What happens:** Designers build a schedule-triggered flow even though the logic really depends on a specific record event and a delayed follow-up.

**When it occurs:** The distinction between schedule-triggered flow and scheduled path is not considered early enough.

**How to avoid:** Choose the time primitive that matches the business trigger, not just the one that sounds similar.
