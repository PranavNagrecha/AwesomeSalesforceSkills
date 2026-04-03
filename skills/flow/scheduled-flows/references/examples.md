# Examples - Scheduled Flows

## Example 1: Nightly Case Reminder With Idempotent Marker

**Context:** Service managers want a nightly reminder for open high-priority Cases with no customer response in seven days.

**Problem:** The first draft sends a reminder every night to the same case owners because nothing marks that the reminder already fired for the current window.

**Solution:**

Use narrow criteria and a date marker that records the last reminder.

```text
Flow API Name: Case_Scheduled_SendStaleReminders
Start criteria:
- Status != Closed
- Priority = High
- Last_Customer_Response__c <= TODAY() - 7
- Last_Reminder_Sent__c < TODAY()

Actions:
- Send email alert
- Update Last_Reminder_Sent__c to TODAY()
```

**Why it works:** The record set is bounded and each run knows whether the reminder already happened today.

---

## Example 2: Scheduled Flow Hands Off Heavy Renewal Processing

**Context:** Finance wants a monthly renewal review process, but the job can touch many contracts and downstream related records.

**Problem:** A single scheduled flow begins accumulating loops, related-record updates, and heavy branching.

**Solution:**

Keep the scheduled flow focused on identification and hand off heavier processing.

```text
Flow API Name: Contract_Scheduled_PrepareRenewalWork
Start criteria:
- EndDate__c <= TODAY() + 30
- Renewal_Review_Queued__c = false

Actions:
- Invoke Apex action to queue renewal processing
- Update Renewal_Review_Queued__c = true
```

**Why it works:** Flow keeps ownership of timing and record selection, while heavy processing moves to the more suitable execution boundary.

---

## Anti-Pattern: Schedule-Triggered Flow As A Backfill Engine

**What practitioners do:** They point a scheduled flow at a very large object and expect it to clean up or migrate data over time.

**What goes wrong:** The flow becomes the wrong tool for large-scale iterative processing and is difficult to operate safely.

**Correct approach:** Use scheduled flows for bounded recurring automation. Use Batch Apex or another batch-focused mechanism when the workload itself is batch-oriented.
