# LLM Anti-Patterns: Roll-Up Summary Alternatives

Common mistakes AI coding assistants make when advising on roll-up summaries and their alternatives.

## Anti-Pattern 1: Suggesting a native roll-up on a lookup relationship

**What the LLM generates:** "Add a Roll-Up Summary field on Account to sum `Invoice__c` amounts" when `Invoice__c` looks up to Account.

**Why it happens:** Roll-up summary is the most common aggregation answer in training data.

**Correct pattern:**

```text
Native roll-up summary requirements:
- summaryForeignKey must be the master-detail field on the child
  (Metadata API Developer Guide, CustomField).
- summaryOperation: Count, Min, Max, or Sum.
- UNVERIFIED (2026-10-03): the per-object roll-up field limit; it is stated
  only on help.salesforce.com.

For lookups: Apex trigger with aggregate SOQL, record-triggered Flow,
DLRS, or a scheduled recompute.
```

**Detection hint:** "Roll-Up Summary" recommended without confirming master-detail.

---

## Anti-Pattern 2: Non-bulkified Apex rollup triggers

**What the LLM generates:** A trigger that runs an aggregate query per record inside the trigger loop.

**Why it happens:** Single-record examples dominate training data.

**Correct pattern:** Collect parent IDs from `Trigger.new` and `Trigger.old` (old parents too on reparent), run one aggregate query, and update only parents whose value changed. The full trigger, service, repair batch, and test class are in `examples.md`.

**Detection hint:** `[SELECT ... COUNT(` or `SUM(` inside a `for` loop over trigger records.

---

## Anti-Pattern 3: Recommending DLRS without its operating cost

**What the LLM generates:** "Install DLRS and configure your rollup."

**Why it happens:** DLRS is popular and easy to demo.

**Correct pattern:**

```text
DLRS (open-source, BSD-3-Clause; SFDO-Community on GitHub):
- Modes: Realtime, Scheduled, and Developer API.
- Extra operations beyond native: Average, Count Distinct, Concatenate,
  First, Last.
- Operating cost: a package to install and upgrade, deployed triggers or
  scheduled jobs to monitor, and failures that surface in package code.
- UNVERIFIED (2026-10-03): published volume thresholds; size it with your
  own load test.
```

**Detection hint:** A DLRS recommendation with no mention of mode, upgrades, or monitoring.

---

## Anti-Pattern 4: Designing Flow rollups with after-delete and undelete steps

**What the LLM generates:** "Add an after-delete flow and an after-undelete flow to keep the total right."

**Why it happens:** The model maps Apex trigger events onto Flow. Version 1.0.1 of this skill made the same claim.

**Correct pattern:**

```text
Flow trigger types (Metadata API, Flow): RecordAfterSave, RecordBeforeSave,
RecordBeforeDelete. recordTriggerType: Create, Update, CreateAndUpdate,
Delete, None. There is no after-delete and no undelete flow.

- Create and update: after-save flow recounts the parent.
- Delete: before-delete flow recounts with Id != $Record.Id (the row still exists).
- Undelete, merge, cascade delete: scheduled recompute.
```

**Detection hint:** "after delete" or "undelete" attached to a record-triggered flow.

---

## Anti-Pattern 5: Ignoring staleness in scheduled rollups

**What the LLM generates:** "Use a scheduled flow to recalculate rollups every hour," with no note on staleness.

**Why it happens:** Scheduled jobs look simpler than triggers.

**Correct pattern:** Say how stale the total can be, and do not use a scheduled-only total in validation rules, entry criteria, or real-time integrations. Use a scheduled recompute as the repair layer under a real-time trigger or flow.

**Detection hint:** A scheduled-only total referenced by a validation rule or an integration.

---

## Anti-Pattern 6: Trusting triggers to see every child change

**What the LLM generates:** "The after insert, update, delete, and undelete trigger covers every case."

**Why it happens:** The four events look complete.

**Correct pattern:** Merge reparenting, cascaded deletes, and child undeletes under a restored parent do not fire child triggers (Apex Developer Guide, "Operations That Don't Invoke Triggers," "Triggers and Merge Statements," "Triggers and Recovered Records"). Add a repair job.

**Detection hint:** A trigger-maintained total with no recompute job.

---

## Anti-Pattern 7: Assuming one aggregate query is always cheap

**What the LLM generates:** "A single SUM query per transaction is fine at any volume."

**Why it happens:** The model counts queries, not rows.

**Correct pattern:** SUM, MIN, MAX, and AVG count each aggregated row toward the query-row limit; COUNT counts one row per group. Batch the recompute for very large parents.

**Detection hint:** A SUM recompute over a parent with tens of thousands of children in a synchronous trigger.
