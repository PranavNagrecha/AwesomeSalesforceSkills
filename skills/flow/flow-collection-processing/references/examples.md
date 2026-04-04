# Examples — Flow Collection Processing

## Example 1: Bulk Status Update Using Loop-and-Accumulate

**Context:** A record-triggered after-save Flow fires when `Order__c` records are marked `Submitted`. It must set `Status__c = 'Pending Review'` on all related `Order_Line__c` records.

**Problem:** The naive design queries Order Lines inside the loop for each Order and issues an `Update Records` per iteration. With a data load of 200 Orders, this executes up to 200 SOQL queries and 200 DML statements — both hit governor limits.

**Solution:**

```text
[Get Records: OrderLines]
  Filter: Order__c IN {!$Record.Id}  ← single query outside loop

[Loop: OrderLines]
  Current Item → {!currentLine}

  [Assignment: Set Status]
    {!currentLine.Status__c} = "Pending Review"   (Set operator)
    {!updatedLines} Add {!currentLine}            (Add operator)

  → Next Iteration

[After Last] →

[Update Records: updatedLines]   ← single DML for entire collection
```

**Why it works:** `Get Records` outside the loop executes exactly one query regardless of how many Orders triggered the flow. The Assignment inside the loop accumulates the modified records. The single `Update Records` after the loop consumes one DML statement and one row per line — the minimum possible cost.

---

## Example 2: Collection Filter + Transform + Create Records for Follow-Up Tasks

**Context:** An autolaunched Flow is called after a batch of `Lead` records are converted. For each converted Lead with `Rating = 'Hot'`, the flow must create a follow-up `Task` assigned to the Lead owner.

**Problem:** The original design uses a Loop with an `if/then` decision element to check `Rating`, then builds a Task inside the loop with multiple Assignment elements, then calls `Create Records` inside the same loop — one DML per Hot lead.

**Solution:**

```text
[Collection Filter: HotLeads]
  Source: {!ConvertedLeads}
  Condition: Rating Equals "Hot"
  Output: {!hotLeadCollection}

[Transform: LeadsToTasks]
  Source Collection: {!hotLeadCollection}  (Lead)
  Target SObject: Task
  Field Mappings:
    WhoId     ← Lead.Id
    OwnerId   ← Lead.OwnerId
    Subject   ← "Follow up with converted lead"  (literal)
    ActivityDate ← {!$Flow.CurrentDate}
  Output: {!taskCollection}

[Create Records: taskCollection]   ← single DML for all tasks
```

**Why it works:** The Collection Filter declaratively removes Cold and Warm leads without a Loop. The Transform produces a correctly typed Task collection in one element. A single `Create Records` on the collection inserts all tasks in one DML call.

---

## Example 3: Collection Sort Before Screen Flow Display

**Context:** A Screen Flow shows a data table of open `Opportunity` records for the current user. Users complained that records appear in unpredictable order.

**Problem:** There is no native sort option on the `Get Records` element for Screen Flows prior to the Collection Sort element being available. Developers were sorting inside a Loop — an unnecessary and fragile approach.

**Solution:**

```text
[Get Records: OpenOpps]
  Filter: OwnerId = {!$User.Id}, IsClosed = false
  Output: {!oppCollection}

[Collection Sort: SortByCloseDate]
  Collection: {!oppCollection}
  Sort Field: CloseDate
  Order: Ascending

[Screen: ShowOpportunities]
  Data Table source: {!oppCollection}
```

**Why it works:** The Collection Sort element reorders `{!oppCollection}` in place before the Screen element renders. No Loop is required. The single Collection Sort element replaces what would otherwise be a multi-element manual sort pattern.

---

## Anti-Pattern: DML Inside A Loop

**What practitioners do:** They place an `Update Records` or `Create Records` element directly inside a Loop body to write each record as it is processed.

**What goes wrong:** Each iteration of the loop executes one DML statement. Salesforce allows 150 DML statements per transaction. A loop over 200 records blows this limit by 25%, causing an uncaught exception that rolls back the entire transaction.

**Correct approach:** Accumulate modified records into an output SObject Collection variable using an Assignment with the `Add` operator, then place a single DML element after the "After Last" exit of the loop. This converts N DML statements into 1.

---

## Anti-Pattern: Loop With Conditional Accumulation Instead Of Collection Filter

**What practitioners do:** They build a Loop that checks a condition, uses a Decision element, and only adds matching records to an output collection — effectively reimplementing what the Collection Filter element does natively.

**What goes wrong:** The resulting flow has four to six elements doing the work of one. Future maintainers cannot quickly understand the intent, and adding a second filter condition requires adding another Decision and branch.

**Correct approach:** Use the Collection Filter element with condition logic directly. This communicates intent in one element, is easier to read during review, and is supported from Spring '23 onward.
