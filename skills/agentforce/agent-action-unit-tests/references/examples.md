# Examples — Agent Action Unit Tests

## Example 1: Per-reason-code test matrix

**Context:** CloseCaseAction returns OK | VALIDATION_BLOCKED | UNKNOWN.

**Problem:** Test only covers the happy path; DML failures never surface until production.

**Solution:**

```apex
@IsTest
static void ok_when_status_can_update() { /* insert Case, call, assert reason_code='CLOSED' */ }
@IsTest
static void validation_blocked_when_required_field_missing() { /* deploy validation rule, call, assert='VALIDATION_BLOCKED' */ }
@IsTest
static void unknown_on_unexpected() { /* force exception with mock, assert='UNKNOWN' */ }
```

**Why it works:** One test per branch forces the engineer to think about every error path.


---

## Example 2: Bulk-safety harness

**Context:** Agent batches 200 requests into one action invocation.

**Problem:** Per-record SOQL inside the loop blows SOQL limit at 101.

**Solution:**

```apex
@IsTest static void bulk_200() {
    List<CloseCaseAction.Request> rs = new List<CloseCaseAction.Request>();
    for (Integer i=0;i<200;i++) rs.add(new CloseCaseAction.Request());
    Test.startTest();
    List<CloseCaseAction.Response> out = CloseCaseAction.run(rs);
    Test.stopTest();
    System.assertEquals(200, out.size());
}
```

**Why it works:** Bulk assertion catches un-bulkified SOQL/DML early.

