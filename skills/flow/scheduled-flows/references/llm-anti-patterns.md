# LLM Anti-Patterns — Scheduled Flows

Common mistakes AI coding assistants make when generating or advising on schedule-triggered flows.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not bounding the record set in the Start element

**What the LLM generates:**

```
Object: Contact
Schedule: Daily at 2:00 AM
Conditions: None — processes all Contacts
```

**Why it happens:** LLMs create the broadest possible scope to ensure all records are covered. Without filter conditions, the flow attempts to process every record in the object, which can be millions of records and will hit governor limits.

**Correct pattern:**

```
Object: Contact
Schedule: Daily at 2:00 AM
Conditions:
  Status__c equals "Pending Review"
  AND LastModifiedDate > LAST_N_DAYS:7
```

Always add filter conditions in the Start element to limit the record set to only records that need processing.

**Detection hint:** Scheduled flow Start element with no filter conditions or with conditions that match the entire object's records.

---

## Anti-Pattern 2: Not designing for idempotent processing

**What the LLM generates:**

```
[For each record in batch]
    [Create Task: "Follow up with Contact"]
```

**Why it happens:** LLMs assume the flow runs exactly once per record. If the flow fails partway through and retries, or if the schedule runs before the previous batch completes, records may be processed twice, creating duplicate Tasks.

**Correct pattern:**

Mark records as processed to prevent reprocessing:

```
[For each record in batch]
    [Decision: Has this record already been processed?]
        No --> [Create Task] --> [Assignment: Set Processed__c = true, add to updateCollection]
        Yes --> (skip)
[Update Records: All records in updateCollection]
```

Or use the entry conditions to exclude already-processed records:

```
Entry Conditions: Processed__c = false
```

**Detection hint:** Scheduled flow that creates or modifies related records without checking if the operation already occurred.

---

## Anti-Pattern 3: Recommending scheduled flows for high-volume batch processing

**What the LLM generates:**

```
"Use a scheduled flow to process 100,000 inactive accounts every night."
```

**Why it happens:** LLMs recommend Flow for everything because it is declarative. Scheduled flows process records in batches of 200, and the total records per schedule is limited. For very high volumes, Batch Apex is more appropriate.

**Correct pattern:**

Volume decision matrix:
- **< 2,000 records**: Scheduled flow is appropriate
- **2,000 - 50,000 records**: Evaluate carefully; consider Batch Apex
- **> 50,000 records**: Use Batch Apex with configurable scope size

```apex
global class InactiveAccountBatch implements Database.Batchable<SObject> {
    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id FROM Account WHERE IsActive__c = false');
    }
    // ...
}
```

**Detection hint:** Scheduled flow advice for record sets described as "all records," "tens of thousands," or "nightly cleanup of entire object."

---

## Anti-Pattern 4: Not handling partial failures in the batch

**What the LLM generates:**

```
[Scheduled Flow processes 200 records per batch]
[If one record fails, the entire batch rolls back]
```

**Why it happens:** LLMs describe the rollback behavior but do not design around it. If one record in a batch of 200 causes a DML failure, all 200 records in that batch fail.

**Correct pattern:**

Add fault handling to isolate failures:

```
[Loop: For each record]
    [Update Records] --fault--> [Assignment: Add failed record to errorCollection]
[After loop: Create Error_Log__c records for errorCollection]
```

Or design the flow so that individual record failures do not block the batch:
- Validate data before DML
- Use Decision elements to skip records that would fail
- Log errors without re-throwing

**Detection hint:** Scheduled flow with DML elements but no fault connectors or error handling strategy.

---

## Anti-Pattern 5: Setting the schedule without considering time zones

**What the LLM generates:**

```
"Schedule the flow to run at midnight."
```

**Why it happens:** LLMs specify a time without clarifying the time zone. Salesforce scheduled flows run in the org's default time zone, which may not be the intended time zone for the business process.

**Correct pattern:**

1. Specify the time zone explicitly: "Run at 2:00 AM PST (org default time zone)"
2. Account for daylight saving time shifts
3. Choose a time that avoids peak usage hours in the org's primary time zone
4. Consider that batches started at 2:00 AM may still be running at 3:00 AM if the record set is large

**Detection hint:** Schedule configuration advice that specifies a time without mentioning the time zone or org default.

---

## Anti-Pattern 6: Using a scheduled flow as a replacement for time-based workflow without migration testing

**What the LLM generates:**

```
"Replace your time-dependent workflow rule with a scheduled flow
that runs hourly and checks for records that are 24 hours old."
```

**Why it happens:** LLMs correctly advise migrating from workflow rules to flows. But the polling-based scheduled flow has different timing behavior than the event-based time-dependent workflow action.

**Correct pattern:**

Understand the behavioral differences:
- **Time-dependent workflow**: fires at the exact time offset from the triggering event
- **Scheduled flow**: fires on a fixed schedule (hourly, daily) and picks up qualifying records

Migration steps:
1. Document the exact timing requirements
2. If exact timing matters, use a record-triggered flow with a scheduled path instead of a scheduled flow
3. If polling is acceptable, set the schedule frequency appropriately
4. Test both approaches in sandbox with realistic data

**Detection hint:** Migration advice from time-dependent workflows to scheduled flows without discussing the timing behavior difference.
