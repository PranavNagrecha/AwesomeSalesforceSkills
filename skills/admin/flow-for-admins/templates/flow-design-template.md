# Flow Design Template

Complete this before building any non-trivial Flow. It forces the design decisions upfront — before you've committed to a structure in Flow Builder that's hard to change.

---

## Flow Overview

| Property | Value |
|----------|-------|
| **Flow Name (Label)** | TODO: e.g. "Update Account on Case Close" |
| **Flow API Name** | TODO: e.g. `Update_Account_On_Case_Close` |
| **Flow Type** | TODO: Record-Triggered / Screen / Scheduled / Autolaunched / Platform Event |
| **Author** | TODO |
| **Design Date** | TODO: YYYY-MM-DD |
| **Target Object** | TODO: e.g. Case |
| **Status** | Design / In Build / Testing / Active |

---

## Business Requirement

**Problem being solved:**
TODO: One paragraph. What business process does this automate? What manual work does it replace?

**Success criteria:**
TODO: How do you know the Flow is working correctly?
e.g. "When a Case Status changes to Closed, the parent Account's Last_Case_Closed_Date__c is updated within 5 seconds."

---

## Trigger Configuration (Record-Triggered Flows)

| Property | Value |
|----------|-------|
| **Object** | TODO |
| **Trigger when** | A record is: ☐ Created / ☐ Updated / ☐ Created or Updated / ☐ Deleted |
| **Run when** | ☐ Record is created / ☐ Record is created or updated |
| **Save type** | ☐ Before Save / ☐ After Save |
| **Entry criteria** | TODO: What conditions must be TRUE for the Flow to run? |
| **Delta check (changes only)** | ☐ Yes: `{!$Record.Field} <> {!$Record__Prior.Field}` / ☐ N/A |

**Entry criteria formula:**
```
TODO: e.g. AND(
  ISPICKVAL({!$Record.Status}, "Closed"),
  NOT(ISPICKVAL({!$Record__Prior.Status}, "Closed"))
)
```

---

## Schedule Configuration (Scheduled Flows)

| Property | Value |
|----------|-------|
| **Frequency** | Daily / Weekly / Monthly |
| **Start date/time** | TODO |
| **Object queried** | TODO |
| **Query filter criteria** | TODO |
| **Estimated record count** | TODO: affects whether Flow or Batch Apex is appropriate |

---

## Variables

| Variable Name | Type | Input/Output/Local | Default Value | Purpose |
|--------------|------|-------------------|---------------|---------|
| TODO: e.g. `accountToUpdate` | Record (Account) | Local | — | Stores Account record for DML |
| TODO | TODO | TODO | TODO | TODO |

---

## Flow Elements (Logical Design)

List the key elements in order. You don't need every element — capture the logic structure.

| Step | Element Type | Element Name | Purpose | Fault Connector? |
|------|-------------|-------------|---------|-----------------|
| 1 | Get Records | `getParentAccount` | Get Account by AccountId | ✅ Required |
| 2 | Decision | `checkAccountExists` | Null check on Account result | N/A |
| 3 | Assignment | `setAccountDate` | Set Last_Case_Closed_Date__c | N/A |
| 4 | Update Records | `updateAccount` | DML on Account | ✅ Required |
| TODO | TODO | TODO | TODO | TODO |

---

## DML Operations

| Operation | Object | When | Records Affected | In a Loop? |
|-----------|--------|------|-----------------|-----------|
| TODO: e.g. Update | Account | After Get Records | 1 per transaction | ❌ No |
| TODO | TODO | TODO | TODO | ❌ No (flag if YES) |

**Bulk safety check:**
If any operation is in a loop: ⚠️ STOP — redesign to collect records first, DML after the loop.

---

## Callouts (if applicable)

| Callout | Target System | Synchronous/Async | Fault Connector? | Timeout Handling? |
|---------|--------------|-------------------|-----------------|------------------|
| TODO | TODO | TODO | ✅ Required | TODO |

---

## Fault Path Design

| Element | Fault Path Action | Who Gets Notified | Error Logged? |
|---------|------------------|-------------------|--------------|
| TODO: `getParentAccount` | Send email to admin | TODO: admin email | ☐ Yes / ☐ No |
| TODO: `updateAccount` | Send email to admin + Log to Error_Log__c | TODO | ✅ Yes |

**Fault email template content:**
```
Subject: Flow Error: [Flow Name] — [Object] [Record ID]

Body:
Flow: [Flow Name]
Record: {!$Record.Id}
Error: {!$Flow.FaultMessage}
Time: {!$Flow.CurrentDateTime}

Action required: Investigate and reprocess this record.
```

---

## Governor Limit Risk Assessment

| Risk | Assessment | Mitigation |
|------|-----------|-----------|
| SOQL queries | TODO: How many per Flow interview? | TODO |
| SOQL in loops | ☐ None / ☐ Risk: TODO | Remove from loop |
| DML in loops | ☐ None / ☐ Risk: TODO | Collect + DML after loop |
| Large record sets | ☐ Expected max: TODO records | TODO if > 2000 |

---

## Test Scenarios

| Scenario | Setup | Expected Result | Pass/Fail |
|----------|-------|----------------|-----------|
| Happy path — trigger fires, update succeeds | TODO | TODO | |
| Entry criteria not met — flow should NOT run | TODO | No action taken | |
| Fault path — Get Records fails | Simulate: TODO | Admin email sent | |
| Bulk test — 200 records simultaneously | Mass update via report | All 200 processed, no errors | |
| Integration — API update triggers flow | REST API update | Flow runs correctly | |

---

## Deployment Notes

| Property | Value |
|----------|-------|
| **Deploy to Sandbox first** | ☐ Yes — target sandbox: TODO |
| **Integration testing required** | ☐ Yes / ☐ No |
| **Version to deactivate after deploy** | TODO: previous version number |
| **Rollback plan** | TODO: Deactivate new version, reactivate version [N] |
