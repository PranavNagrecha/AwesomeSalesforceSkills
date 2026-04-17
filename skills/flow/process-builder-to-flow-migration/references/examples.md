# Examples — Process Builder to Flow Migration

## Example 1: Tool-Eligible Field Update Migration

**Context:** An Opportunity Process Builder process updates the `StageName` to "Closed Won" and sends an email alert when `Amount` changes to greater than $100,000. No invocable Apex, no scheduled actions, no ISCHANGED criteria.

**Problem:** The process runs correctly today but will lose bug-fix support by end of 2025. The team wants the fastest, safest migration path.

**Solution:**

1. Go to Setup > Migrate to Flow
2. Locate the Opportunity process, click Convert
3. Tool generates an INACTIVE record-triggered flow — open in Flow Builder
4. Verify the Decision conditions: `{!$Record.Amount} > 100000` (not ISCHANGED — this is a static value comparison, which the tool handles correctly)
5. Add a Fault Path to the Update Records element (tool never generates fault paths)
6. In Flow Trigger Explorer, set priority to match the original process creation order relative to any other Opportunity flows
7. Test in sandbox: run `Database.update` on 200 Opportunities with Amount = 150000 via Execute Anonymous; assert StageName updated
8. Activate flow, immediately deactivate the source Process Builder process

**Why it works:** The Migrate to Flow tool handles static value comparisons and field updates reliably. The critical step is adding Fault Paths — the tool omits them, leaving migrated flows silent on DML failure.

---

## Example 2: Manual Rebuild for ISCHANGED Criteria

**Context:** A Lead process fires when `Status` `ISCHANGED()` is true and Status is now "Working". It creates a Task and updates `Rating` to "Hot".

**Problem:** The Migrate to Flow tool cannot handle `ISCHANGED()` criteria or Task creation. Running the tool produces a flow that fires on every record update, not just Status changes — and the Task action is silently dropped.

**Solution:**

In a new record-triggered flow (trigger: when a record is updated, run after save):

```
// Decision node condition replacing ISCHANGED(Status):
{!$Record.Status} = "Working"
AND
{!$Record__Prior.Status} != "Working"

// Create Records element (replaces task action):
Object: Task
Subject: "Follow up with lead"
WhoId: {!$Record.Id}
OwnerId: {!$Record.OwnerId}
ActivityDate: TODAY + 3

// Update Records element:
Filter: Id = {!$Record.Id}
Field update: Rating = "Hot"
```

**Why it works:** `{!$Record__Prior.FieldName}` is the Flow equivalent of `ISCHANGED()` — it holds the field value before the save. Comparing prior to current explicitly reconstructs the ISCHANGED semantics. Task creation uses a Create Records element which the original tool cannot generate.

---

## Anti-Pattern: Activating a Migrated Flow Without Deactivating the Process

**What practitioners do:** Activate the new Flow, test it looks correct, but leave the original Process Builder process active "just in case" during a monitoring period.

**What goes wrong:** Salesforce executes both the Process Builder process and the record-triggered flow on each qualifying record update. Because Process Builder and Flows execute in separate, unspecified sequences, field updates may be applied twice or in the wrong order. Debugging is extremely difficult because the second execution has no visible trace in standard log viewers.

**Correct approach:** Deactivate the Process Builder process in the same deployment window as the Flow activation. If rollback is needed, re-activate the Process Builder and deactivate the Flow — never run both simultaneously.
