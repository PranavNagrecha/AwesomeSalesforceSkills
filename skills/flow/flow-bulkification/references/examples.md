# Examples — Flow Bulkification

## Example 1: Collect Then Update Related Records

**Context:** An after-save Opportunity flow must update related renewal `Task` records whenever the stage changes.

**Problem:** The original design loops through tasks and runs `Update Records` for each one, which fails during mass stage updates.

**Solution:**

```text
Start: Opportunity after-save
Get Records: Renewal Tasks for all triggering Opportunity Ids
Loop: Renewal Tasks
Assignment: Set Status = 'Needs Review' on a task collection variable
Update Records: task collection variable
```

**Why it works:** The flow performs one query and one DML operation for the batch instead of repeating both per record.

---

## Example 2: Move Same-Record Enrichment To Before-Save

**Context:** A record-triggered Case flow sets SLA flags and default routing values on the same Case.

**Problem:** The flow was built as after-save and re-updated the Case, triggering extra automation and using unnecessary DML.

**Solution:**

```text
Start: Case before-save
Decision: Is Priority blank or missing SLA?
Assignment: Set Priority and SLA fields on $Record
End
```

**Why it works:** Before-save updates on the triggering record are the most efficient path and avoid a separate database write.

---

## Anti-Pattern: Get Records Inside A Loop

**What practitioners do:** They loop through Accounts and place `Get Records` inside the loop to find Cases or Contacts for each Account.

**What goes wrong:** Query count grows with the number of loop iterations. The flow passes single-record testing and then fails during imports or integrations.

**Correct approach:** Query the related records once outside the loop, then use collection variables and decisions inside the loop to match the relevant records.
