# Flow Design Template

Complete this before building any non-trivial Flow. It forces the design decisions upfront — before
you've committed to a structure in Flow Builder that's hard to change.

Every row is filled with a worked example on the left of the `→` and the rule for your own answer on
the right. Replace the example; keep the rule in mind. Rows marked **must** are the ones that decide
whether the flow is correct rather than merely working.

---

## Flow Overview

| Property | Example → How to fill it |
|----------|--------------------------|
| **Flow Name (Label)** | `Case Close Followup` → verb-object naming, no version number, no team name |
| **Flow API Name** | `Case_Close_Followup` → underscores only, begins with a letter, no trailing or doubled underscore |
| **Flow Type** | Record-Triggered (After Save) → the branch that `standards/decision-trees/flow-pattern-selector.md` Q1–Q9 resolved to. Record the Q number |
| **Author** | Name of the person accountable for this flow in six months, not whoever clicked Save |
| **Design Date** | 2026-09-04 → ISO date; this document is the record of what was decided when |
| **Target Object** | `Case` → the `start.object` value, API name not label |
| **Status** | Design / In Build / Testing / Active |
| **Deploy-as-active check (must)** | Sandbox `true`, prod `?` → read `enableFlowDeployAsActiveEnabled` from `Settings:Flow` in the *target* org before the release plan is written |

---

## Business Requirement

**Problem being solved:**
One paragraph. What business process does this automate, and what manual work does it replace? Name
the people who do the work today. If you cannot name them, the requirement is not ready.

*Example: "Support agents are supposed to log a quality-review task when they close a Case. They
forget on roughly a third of closures, so the QA sample is biased toward the agents who remember."*

**Success criteria:**
A statement someone could verify by looking at data, with a number and a time bound in it.

*Example: "Every Case whose Status transitions to Closed has exactly one open Task with Subject
'Post-closure quality review' within the same transaction. Zero duplicate tasks on re-saves of an
already-closed Case."*

**Explicit non-goals:**
What this flow deliberately does not do. This is what stops the next person from bolting a second
purpose onto it.

*Example: "Does not close the review task, does not touch the Account, does not email the customer."*

---

## Trigger Configuration (Record-Triggered Flows)

| Property | Example → How to fill it |
|----------|--------------------------|
| **Object** | `Case` → API name |
| **Trigger when** | ☐ Created / ☑ Updated / ☐ Created or Updated / ☐ Deleted → maps to `start.recordTriggerType` |
| **Save type (must)** | ☐ Before Save / ☑ After Save → Before Save only if the flow writes nothing but fields on the triggering record. Any DML, action, callout, or email forces After Save |
| **Entry criteria** | `Status Equals Closed` → the narrowest condition that is still correct. Records that fail it never start an interview |
| **Delta check (must)** | ☑ Transition gate (`doesRequireRecordChangedToMeetCriteria` = `true`) / ☐ `ISCHANGED()` in a `filterFormula` / ☐ N/A. These are different: the transition gate asks "did the record just enter this state", `ISCHANGED()` asks "did this field change" |
| **Run order** | `triggerOrder` 1–2,000, or blank → set it only if another record-triggered flow on this object must run before or after. Blank means unordered |
| **Other automation on this object** | List every other record-triggered flow, Apex trigger, workflow field update, validation rule, and duplicate rule. A before-save flow's writes feed the validation and duplicate rules that run after it |

**Entry criteria expression:**

Use `filters` + `filterLogic` when you want the transition gate (it applies to the whole block), or
`filterFormula` when you need formula functions.

```
Filters form (enables the transition gate):
  Status  EqualTo  Closed
  filterLogic: and
  doesRequireRecordChangedToMeetCriteria: true

Formula form (per-field change detection, no transition gate):
  AND(
    ISCHANGED({!$Record.Status}),
    ISPICKVAL({!$Record.Status}, "Closed")
  )
```

---

## Schedule Configuration (Scheduled Flows)

Skip this table unless the flow type is Scheduled.

| Property | Example → How to fill it |
|----------|--------------------------|
| **Frequency** | Weekly → `Once` / `Daily` / `Weekly` (`FlowSchedule.frequency`) |
| **Start date/time** | 2026-09-08 06:00 → runs in the org's default time zone, not the author's |
| **Object queried** | `Lead` → the `start.object`; each returned record starts one interview |
| **Query filter criteria** | `LastActivityDate < LAST_N_DAYS:30 AND Status NOT IN (...)` → written so the result set shrinks as the flow does its job, otherwise every run reprocesses the same records |
| **Estimated record count** | ~1,800/run → count it in a report first. Above roughly 50k per run, `flow-pattern-selector.md` Q6 routes you to Batch Apex |
| **Scheduled-path batch size** | Only applies to After-Save scheduled paths: `maxBatchSize` is 1–200, default 200. Lower it only when per-interview work is heavy |

---

## Variables

One row per variable. Anything named `var1` fails review.

| Variable Name | Type | Input/Output/Local | Default Value | Purpose |
|--------------|------|-------------------|---------------|---------|
| `faultDetail` | Text | Local | — | Holds `$Flow.FaultMessage` on the fault path so the notification can carry it |
| `accountToUpdate` | Record (Account) | Local | — | Single Account record staged for DML after the loop |
| `caseIdsToProcess` | Text collection | Local | — | Ids gathered in the loop, queried once outside it |
| *(add rows)* | | | | Name says what it holds; Purpose says why it exists, not what its type is |

Rules: mark a variable Input or Output only if a caller actually reads or writes it — `isInput` /
`isOutput` are part of the flow's public contract and turning one off later breaks callers. Record
collection variables exist to hold DML batches; if you have one and no post-loop DML element, you
have a leak.

---

## Flow Elements (Logical Design)

List the key elements in order. You don't need every element — capture the logic structure. The
Fault Connector column is the point of the table.

| Step | Element Type | Element Name | Purpose | Fault Connector? |
|------|-------------|-------------|---------|-----------------|
| 1 | Get Records | `getParentAccount` | Get Account by `AccountId` | Required |
| 2 | Decision | `checkAccountExists` | Null check on the Get result before anything reads it | N/A |
| 3 | Assignment | `setAccountDate` | Set `Last_Case_Closed_Date__c` in memory | N/A |
| 4 | Update Records | `updateAccount` | One DML on Account | Required |
| 5 | Assignment | `captureFault` | Store `$Flow.FaultMessage` into `faultDetail` | N/A — this *is* the fault path |
| 6 | Action / Create Records | `notifyOwner` | Email or `Flow_Error_Log__c` record | N/A |

Fill the column with **Required** for every Get Records, Create Records, Update Records, Delete
Records, Action, and callout element; **N/A** for Decision, Assignment, Loop, and Screen. A
"Required" with no destination in the Fault Path Design table below is an incomplete design.

---

## DML Operations

| Operation | Object | When | Records Affected | In a Loop? |
|-----------|--------|------|-----------------|-----------|
| Update | `Account` | After the Get and the null check | 1 per interview | No |
| Create | `Task` | After the entry criteria pass | 1 per interview | No |
| *(add rows)* | | | State the max, not the typical | No — flag if Yes |

**Bulk safety check:** any Yes in the last column means stop and redesign — collect into a
collection variable inside the loop, then place a single DML element after it. The transaction budget
is 100 SOQL and 150 DML statements shared with every other automation on the object, so a per-record
DML fails partway through a 200-record load and leaves the batch half-processed.

---

## Callouts (if applicable)

| Callout | Target System | Synchronous/Async | Fault Connector? | Timeout Handling? |
|---------|--------------|-------------------|-----------------|------------------|
| `postToBillingApi` | Billing (REST, Named Credential `Billing_API`) | Async (scheduled path) | Required | `timeoutConnector` to a retry-or-log path |
| *(add rows)* | Name the Named Credential, never a literal endpoint | Async unless you can prove it must be inline | Required | Say what happens on timeout, not "handled" |

Callouts are not available in a before-save flow. A real callout belongs on an async path so it does
not spend the triggering transaction's 120-second cumulative callout budget.

---

## Fault Path Design

| Element | Fault Path Action | Who Gets Notified | Error Logged? |
|---------|------------------|-------------------|--------------|
| `getParentAccount` | Assignment captures `$Flow.FaultMessage` → email | Service Ops distribution list (a role, not a person) | No |
| `updateAccount` | Assignment → email + create `Flow_Error_Log__c` | Service Ops distribution list | Yes |
| *(one row per "Required" above)* | Every fault path ends somewhere a human or a query will find | Named owner or list; a departed admin's address is not a fault path | Yes for anything that must be reprocessed |

Canonical shape: `templates/flow/FaultPath_Template.md` at the repo root. Do not invent a different
one; reference that file by path.

**Fault notification content:**

```
Subject: Flow Error: [Flow Label] — [Object] [Record ID]

Body:
Flow:    [Flow Label] (API name)
Element: [element that faulted]
Record:  {!$Record.Id}
Error:   {!$Flow.FaultMessage}
Time:    {!$Flow.CurrentDateTime}

Action required: investigate and reprocess this record.
```

`{!$Flow.FaultMessage}` is populated only on a fault path. Reading it anywhere else returns nothing.

---

## Governor Limit Risk Assessment

| Risk | Assessment | Mitigation |
|------|-----------|-----------|
| SOQL queries | Count Get Records elements per interview: 1 → multiply by the largest realistic batch size | Query once outside the loop; pass data in rather than re-querying |
| SOQL in loops | ☑ None / ☐ Risk: name the element | Move the Get outside the loop and filter in memory |
| DML in loops | ☑ None / ☐ Risk: name the element | Collect into a collection variable; one DML after the loop |
| Large record sets | Expected max per transaction: 200 (Data Loader default batch) | Above ~50k per run for a scheduled flow, route to Batch Apex per `flow-pattern-selector.md` Q6 |
| Shared budget | Other automation on this object consumes the same 100 SOQL / 150 DML | List it in the Trigger Configuration table and add its cost here |

---

## Test Scenarios

| Scenario | Setup | Expected Result | Pass/Fail |
|----------|-------|----------------|-----------|
| Happy path | Close one Case through the UI | One Task created, correct owner and subject | |
| Entry criteria not met | Edit the Description on an open Case | No Task, no interview | |
| Already in target state | Save an already-Closed Case again | No second Task — proves the transition gate works | |
| Fault path | Deactivate the target object's required field or revoke create on Task for the running user | Notification received carrying `$Flow.FaultMessage` | |
| Bulk | Data Loader 200+ records through the flow's object | All processed, no `Too many SOQL queries`, no partial batch | |
| Integration | Same change via REST API rather than the UI | Identical result — flows fire on API saves too | |
| Post-deploy in target org | `SELECT ApiName, IsActive, IsOutOfDate FROM FlowDefinitionView WHERE ApiName = '...'` | `IsActive = true`, `IsOutOfDate = false` | |

---

## Deployment Notes

| Property | Example → How to fill it |
|----------|--------------------------|
| **Deploy to sandbox first** | Target sandbox alias, e.g. `uat` → and note that its deploy-as-active default differs from production |
| **Integration testing required** | Yes if any other system writes to this object; No otherwise. "No" needs a reason |
| **`<status>` in the file** | `Active` → and the activation plan for production if `enableFlowDeployAsActiveEnabled` is `false` there |
| **Version to deactivate after deploy** | Previous active version number, from `FlowVersionView` — a version with paused interviews cannot be deleted |
| **Rollback plan** | Reactivate version N, and state how: Setup activation, or a redeploy with `<status>Active</status>` on the old file. "Roll back the deploy" is not a plan for a flow |
| **Post-deploy verification** | The `FlowDefinitionView` query above, run and pasted into the release record |
