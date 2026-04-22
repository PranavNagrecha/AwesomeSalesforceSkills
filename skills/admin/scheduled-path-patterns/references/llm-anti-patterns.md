# LLM Anti-Patterns — Scheduled Path Patterns

Common mistakes AI coding assistants make with record-triggered Flow scheduled paths.

## Anti-Pattern 1: No re-check in the scheduled branch

**What the LLM generates:** Flow queues a reminder 24 hours after Case creation; the scheduled branch emails without checking `Status`.

**Why it happens:** Model treats the scheduled branch as if the trigger state is still current.

**Correct pattern:**

```
Start the scheduled path branch with a Get Records (re-query the
source record by Id) or an Entry Condition check. The record may
have been closed, deleted, or updated in the 24-hour window. Don't
email about a "new open case" that's already resolved.
```

**Detection hint:** Scheduled Path branch that proceeds to action elements without a Get Records or Decision checking current state.

---

## Anti-Pattern 2: Filtering after queuing instead of at entry

**What the LLM generates:** Entry criteria "Any record" with logic in the scheduled branch to drop irrelevant ones.

**Why it happens:** Model optimizes ergonomically, not for queue volume.

**Correct pattern:**

```
Put narrow filter criteria on the Scheduled Path entry so interviews
only queue for relevant records. Millions of no-op queued interviews
consume async capacity and obscure real issues in the Paused
Interview monitor.
```

**Detection hint:** Scheduled Path with no entry condition or an overly broad one, paired with an early-exit Decision.

---

## Anti-Pattern 3: Offset from a field that can change after queue time

**What the LLM generates:** "30 days before `RenewalDate__c`" — but admin changes the date after queue.

**Why it happens:** Model assumes live recomputation.

**Correct pattern:**

```
The scheduled time is computed once when the interview queues. If
the anchor field changes, the scheduled path will NOT reschedule.
For dynamic-date use cases: trigger on field change (so a new
interview queues with the new date) and cancel the stale one via
the Paused Flow Interview monitor or a cleanup Flow.
```

**Detection hint:** Scheduled Path using a mutable date field with no "on update" trigger branch to refresh.

---

## Anti-Pattern 4: Missing monitoring for Paused Interview failures

**What the LLM generates:** Scheduled path deployed with no admin email configured for errors.

**Why it happens:** Model focuses on the happy path.

**Correct pattern:**

```
Set "Error Email Notifications" in Process Automation Settings to a
monitored admin distribution list. Document the Paused Flow Interview
setup page as part of the operations runbook. Failures in scheduled
paths are easy to miss because there's no UI trigger when they fail.
```

**Detection hint:** Flow deployment with scheduled paths and no accompanying admin-email / monitoring configuration.

---

## Anti-Pattern 5: Using Scheduled Path for absolute-time daily jobs

**What the LLM generates:** "Run every Monday at 9 AM" implemented as a Scheduled Path on a dummy record.

**Why it happens:** Model reaches for the available hammer.

**Correct pattern:**

```
For absolute-time recurring jobs, use Scheduled Flow (not Scheduled
Path) or an Apex Schedulable. Scheduled Path is offset-from-record-event,
not cron. A dummy record + scheduled path is brittle: if the dummy
is deleted or the record-trigger version changes, the job stops.
```

**Detection hint:** Record-triggered Flow on a "Singleton__c" or "Trigger__c" object with a Scheduled Path implementing daily cadence.
