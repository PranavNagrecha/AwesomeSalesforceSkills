# Metadata Examples — Record-Triggered Flow Patterns

Three complete, deployable record-triggered flows on one object — **before-save**,
**after-save with entry conditions plus a scheduled path**, and **before-delete** — plus a
`FlowTest` that pins the after-save transition, the `FlowDefinition` activation form, a
`package.xml`, a deploy order, and the two places you verify what actually landed.

§ 4 adds a fourth flow on a *different* object — a **Create-triggered before-save** flow
on Lead — together with the `FlowTest` that proves a rule the Metadata API Developer Guide
never states: a Create-triggered flow's Start test point takes
`InputTriggeringRecordInitial` only, not the `InputTriggeringRecordInitial` /
`InputTriggeringRecordUpdated` pair the Opportunity example above uses. That rule was
proven live in a check-only deploy (API 67.0, 2026-09-12), not read out of the guide — see
§ 4.2 and `references/gotchas.md`.

Element names, enum values, version floors and limits below come from the Metadata API
Developer Guide (`api_meta.txt`) and the Object Reference (`object_reference.txt`), cited
by `grep -n` line. Save-order positions come from the Apex Developer Guide
(`apexdev.txt` L15402–15490).

Canonical shapes this file deliberately does not re-invent:

- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` — the Start element and
  entry-criteria shape. Sections 1 and 2 below are that skeleton filled in: same
  `<start>` child ordering, same `<processType>AutoLaunchedFlow</processType>`, with the
  skeleton's placeholder `Account`/`Active__c` replaced by a real Opportunity model.
- `templates/flow/FaultPath_Template.md` — what a fault path must *do* once you route to
  it (capture `{!$Flow.FaultMessage}`, write one `Application_Log__c` row, correlate on
  `{!$Flow.InterviewGuid}`). Every `faultConnector` below lands on that shape.
- `flow/subflows-and-reusability` `references/metadata-examples.md` already shows a
  record-triggered **parent that delegates to a child flow**. Nothing here repeats it —
  these three flows own their own logic end to end.

All three flows target one object on purpose: that is what makes `<triggerOrder>` a real
setting rather than a footnote.

---

## Assumed org model

| Component | Type | Used by |
|---|---|---|
| `Opportunity.Deal_Band__c` | Picklist (`Enterprise`, `Standard`) | Flow 1 (written before save) |
| `Opportunity.Pricing_Review_Required__c` | Checkbox | Flow 1 |
| `Account.Renewal_Review_Due__c` | Checkbox | Flow 2 (scheduled path) |
| `Opportunity_Archive__c` | Custom object, fields `Original_Id__c`, `Name`, `Amount__c`, `Close_Date__c`, `Stage__c`, `Account__c` | Flow 3 |
| `Application_Log__c` | Custom object, fields `Source__c`, `Severity__c`, `Message__c`, `Request_Id__c` | every fault path (`templates/flow/FaultPath_Template.md`) |
| `Lead.Intake_Score__c` | Number | § 4.2, written before save |
| `Lead.Priority_Tier__c` | Picklist (`Hot`, `Warm`, `Cold`) | § 4.2 |

---

## 1. Before-save — `Opportunity_BeforeSave_Normalize.flow-meta.xml`

Derives two fields on the record being saved. It has **no `recordCreates`,
`recordUpdates`, `recordDeletes`, `actionCalls`, or `subflows`** — only `decisions` and
`assignments` writing to `$Record`. Those assignments persist because the flow runs at
save-order step 3, before the record is written at step 7 (`apexdev.txt` L15440, L15447);
there is no Update element and no second DML.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Set_Enterprise_Band</name>
        <label>Set Enterprise Band</label>
        <locationX>50</locationX>
        <locationY>350</locationY>
        <assignmentItems>
            <assignToReference>$Record.Deal_Band__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Enterprise</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>$Record.Pricing_Review_Required__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </assignmentItems>
    </assignments>
    <assignments>
        <name>Set_Standard_Band</name>
        <label>Set Standard Band</label>
        <locationX>300</locationX>
        <locationY>350</locationY>
        <assignmentItems>
            <assignToReference>$Record.Deal_Band__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Standard</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>$Record.Pricing_Review_Required__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>false</booleanValue>
            </value>
        </assignmentItems>
    </assignments>
    <decisions>
        <name>Classify_Deal</name>
        <label>Classify Deal</label>
        <locationX>176</locationX>
        <locationY>220</locationY>
        <defaultConnector>
            <targetReference>Set_Standard_Band</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Standard</defaultConnectorLabel>
        <rules>
            <name>Enterprise_Deal</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Amount</leftValueReference>
                <operator>GreaterThanOrEqualTo</operator>
                <rightValue>
                    <numberValue>250000.0</numberValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Set_Enterprise_Band</targetReference>
            </connector>
            <label>Enterprise</label>
        </rules>
    </decisions>
    <description>Before-save. Derives Deal_Band__c and Pricing_Review_Required__c on the triggering Opportunity. No DML elements by design. triggerOrder 10 on Opportunity; see Opportunity_BeforeDelete_Archive for the delete context.</description>
    <environments>Default</environments>
    <interviewLabel>Opportunity BeforeSave Normalize {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Opportunity BeforeSave Normalize</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>176</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Classify_Deal</targetReference>
        </connector>
        <filterFormula>NOT(ISBLANK({!$Record.Amount}))</filterFormula>
        <object>Opportunity</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordBeforeSave</triggerType>
    </start>
    <status>Draft</status>
    <triggerOrder>10</triggerOrder>
</Flow>
```

### How to read it

- `<triggerType>RecordBeforeSave</triggerType>` — "Creating and/or updating a record
  triggers an autolaunched flow to make more updates to that record before it's saved to
  the database", API 48.0+ (`api_meta.txt` L72539–72542).
- `<recordTriggerType>CreateAndUpdate</recordTriggerType>` — one of `Create`, `Update`,
  `CreateAndUpdate`, `Delete`, `None` (`api_meta.txt` L72450–72457).
- `<filterFormula>` — "A formula that's used to filter what records execute the flow
  during a save. Available only in record-triggered flows", API 55.0+ (`api_meta.txt`
  L72390–72392). It is a **separate field from `<filters>`**; the two express entry
  criteria in different shapes, and `doesRequireRecordChangedToMeetCriteria` is described
  against *conditions*, not against a formula (L72322–72325). Flow 2 uses the
  `filters` + `doesRequire…` shape so you can compare them side by side.
- A `>` or `<` inside a `filterFormula` must be XML-escaped (`&gt;` / `&lt;`). The formula
  above avoids the issue; `{!$Record.Amount} &gt; 0` is the escaped form if you need it.
- `<runInMode>DefaultMode</runInMode>` — "How the flow is launched determines whether the
  flow runs in user context or in system context." The alternatives are
  `SystemModeWithSharing` (respects OWD, role hierarchy, sharing rules, manual sharing,
  teams, territories, but **not** object permissions or field-level access) and
  `SystemModeWithoutSharing` ("can access all data"), API 49.0+ (`api_meta.txt`
  L68374–68390).
- `<status>Draft</status>` — valid values are `Active`, `Draft`, `Obsolete`,
  `InvalidDraft`, `UnderReview` (`api_meta.txt` L68416–68424). "Any flow without a
  `status` value is deployed or retrieved with a `status` value of `Draft`"
  (L73187–73188), so setting it explicitly is the only way to know what you shipped.
- `<triggerOrder>10</triggerOrder>` — "The run order of a record-triggered flow, from 1 to
  2,000", API 54.0+ (`api_meta.txt` L68438–68441). Values are spaced by 10 so a later flow
  can be inserted without renumbering.
- Element ordering inside `<Flow>` is alphabetical, matching the guide's own sample
  definition (`api_meta.txt` L73707–73790: `apiVersion`, `assignments`, `environments`,
  `interviewLabel`, `label`, `loops`, `processType`, `recordLookups`, `runInMode`,
  `start`, `status`, `variables`). Inside a node, `name`/`label`/`locationX`/`locationY`
  come first, then the node's own fields alphabetically.

---

## 2. After-save with entry conditions and a scheduled path — `Opportunity_AfterSave_ClosedWon.flow-meta.xml`

Runs at save-order step 14 (`apexdev.txt` L15470), after the record is written at step 7
and after all Apex after-triggers at step 8 — so `$Record` here is the *saved* state, not
what the user typed. The immediate path creates an onboarding Task. The scheduled path
fires 7 days after `CloseDate` and touches the parent Account.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <decisions>
        <name>Check_Account_Still_Active</name>
        <label>Check Account Still Active</label>
        <locationX>500</locationX>
        <locationY>350</locationY>
        <defaultConnectorLabel>Inactive Or Missing</defaultConnectorLabel>
        <rules>
            <name>Account_Found</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>Get_Related_Account.Id</leftValueReference>
                <operator>IsNull</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Flag_Account_For_Renewal_Review</targetReference>
            </connector>
            <label>Account Found</label>
        </rules>
    </decisions>
    <description>After-save on Opportunity. Immediate path creates an onboarding Task; scheduled path runs 7 days after CloseDate and flags the Account for renewal review. Entry criteria use doesRequireRecordChangedToMeetCriteria so the flow fires on the transition into Closed Won, not on every later edit. triggerOrder 20.</description>
    <environments>Default</environments>
    <interviewLabel>Opportunity AfterSave ClosedWon {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Opportunity AfterSave ClosedWon</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Create_Onboarding_Task</name>
        <label>Create Onboarding Task</label>
        <locationX>176</locationX>
        <locationY>220</locationY>
        <faultConnector>
            <targetReference>Log_Immediate_Fault</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>ActivityDate</field>
            <value>
                <elementReference>$Record.CloseDate</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>OwnerId</field>
            <value>
                <elementReference>$Record.OwnerId</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Subject</field>
            <value>
                <stringValue>Kick off onboarding</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>WhatId</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <object>Task</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordCreates>
        <name>Log_Immediate_Fault</name>
        <label>Log Immediate Fault</label>
        <locationX>420</locationX>
        <locationY>220</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Request_Id__c</field>
            <value>
                <elementReference>$Flow.InterviewGuid</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>ERROR</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Opportunity_AfterSave_ClosedWon/Immediate</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordCreates>
        <name>Log_Scheduled_Fault</name>
        <label>Log Scheduled Fault</label>
        <locationX>740</locationX>
        <locationY>350</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Request_Id__c</field>
            <value>
                <elementReference>$Flow.InterviewGuid</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>ERROR</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Opportunity_AfterSave_ClosedWon/Day_7_Renewal_Check</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordLookups>
        <name>Get_Related_Account</name>
        <label>Get Related Account</label>
        <locationX>500</locationX>
        <locationY>220</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Check_Account_Still_Active</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Scheduled_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.AccountId</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <object>Account</object>
        <queriedFields>Id</queriedFields>
        <queriedFields>Renewal_Review_Due__c</queriedFields>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Flag_Account_For_Renewal_Review</name>
        <label>Flag Account For Renewal Review</label>
        <locationX>500</locationX>
        <locationY>480</locationY>
        <faultConnector>
            <targetReference>Log_Scheduled_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.AccountId</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Renewal_Review_Due__c</field>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </inputAssignments>
        <object>Account</object>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>176</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Create_Onboarding_Task</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>StageName</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Closed Won</stringValue>
            </value>
        </filters>
        <object>Opportunity</object>
        <recordTriggerType>Update</recordTriggerType>
        <scheduledPaths>
            <name>Day_7_Renewal_Check</name>
            <connector>
                <targetReference>Get_Related_Account</targetReference>
            </connector>
            <label>Day 7 Renewal Check</label>
            <maxBatchSize>200</maxBatchSize>
            <offsetNumber>7</offsetNumber>
            <offsetUnit>Days</offsetUnit>
            <recordField>CloseDate</recordField>
            <timeSource>RecordField</timeSource>
        </scheduledPaths>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
    <triggerOrder>20</triggerOrder>
</Flow>
```

### How to read it

- `<triggerType>RecordAfterSave</triggerType>` — "The flow starts after a record is
  saved", API 49.0+ (`api_meta.txt` L72524–72525).
- `<doesRequireRecordChangedToMeetCriteria>true</…>` — "If set to `true`, conditions
  evaluate to `true` only if the record didn't meet the required conditions before the
  triggering update but now meets the conditions after the update", API 50.0+
  (`api_meta.txt` L72322–72325). With it, the flow fires on the *transition into*
  `Closed Won`. Without it, every later edit of a record already sitting in `Closed Won`
  re-fires the flow and creates another Task.
- `<recordTriggerType>Update</recordTriggerType>` — `Update` rather than
  `CreateAndUpdate`, because `doesRequireRecordChangedToMeetCriteria` is defined against a
  "triggering **update**"; a create has no prior state for it to compare against.
- **A documentation discrepancy worth knowing about.** Both guides end the
  `recordTriggerType` entry with "Available only when `triggerType` is `RecordBeforeSave`
  or `DataCloudDataChange`" (`api_meta.txt` L72458–72460; the Object Reference repeats a
  shorter form at `object_reference.txt` L139700). That sentence cannot be complete
  as written: the same field's enum includes `Delete`, which only pairs with
  `RecordBeforeDelete` (L72454–72455). UNVERIFIED (2026-09-05): whether an after-save flow
  *requires* `recordTriggerType` is therefore not settled by these two guides. This file
  and the checker both treat it as required for every record-triggered flow — that is the
  shape Flow Builder produces and the safer default, since the field is what distinguishes
  a create-only from an update-only after-save flow. If a deploy rejects it on an
  after-save flow, that is the discrepancy resolving itself and the checker rule should be
  narrowed, not the flow.
- **Scheduled path.** `FlowScheduledPath` is API 51.0+ (`api_meta.txt` L71389–71390).
  `<offsetNumber>7</offsetNumber>` with `<offsetUnit>Days</offsetUnit>` — valid units are
  `Months` (56.0+), `Days`, `Hours`, `Minutes` (L71405–71411); negative values run
  *before* the source time (L71400–71404). `<timeSource>RecordField</timeSource>` with
  `<recordField>CloseDate</recordField>` — "Field used to determine when the scheduled
  path executes. The field's object is defined in FlowStart" (L71417–71418); the
  alternative is `RecordTriggerEvent` (L71420–71423).
- `<maxBatchSize>200</maxBatchSize>` — "The maximum number of scheduled path interviews to
  execute in a single batch, from 1 to 200. Default is 200" (`api_meta.txt`
  L71397–71398). Set it explicitly and lower it when the path does per-record DML or
  callouts: 200 interviews sharing one transaction's limits is the default, not a
  guarantee that 200 fit.
- `<pathType>` is omitted, which the guide defines as the time-triggered case: "null is
  used for time-triggered and record-triggered paths. The default value is null"; the only
  other value is `AsyncAfterCommit` (`api_meta.txt` L71412–71415). An `AsyncAfterCommit`
  path runs at save-order step 20 as post-commit logic — "Asynchronous paths in
  record-triggered flows" (`apexdev.txt` L15489) — outside the triggering transaction, so
  it cannot roll the save back.
- **Every fault-capable element has a `faultConnector`**: `Create_Onboarding_Task`,
  `Get_Related_Account`, `Flag_Account_For_Renewal_Review`. `FlowRecordCreate`,
  `FlowRecordLookup`, `FlowRecordUpdate` and `FlowRecordDelete` each declare the field
  (`api_meta.txt` L70965, L71120, L71283, L71046). The two `Log_*_Fault` creates are
  themselves the fault landing elements and deliberately carry none — a fault path on a
  fault path is an unbounded chain.
- `<queriedFields>` are listed explicitly rather than relying on the automatic output, so
  the Get returns two columns instead of the whole Account.
- **No Loop element anywhere.** The interview already runs per record in the triggering
  DML; a `Get Records` reachable from a `<loops>` element's `<nextValueConnector>` would
  multiply queries per record. `scripts/check_record_triggered_flow_patterns.py` walks the
  connector graph from every loop and fails on that shape.

---

## 3. Before-delete — `Opportunity_BeforeDelete_Archive.flow-meta.xml`

Copies the record into an archive object *while it still exists*. This is the only
record-triggered delete context that exists: `FlowTriggerType` offers `RecordBeforeDelete`
and no after-delete value (`api_meta.txt` L72536–72538; full `FlowTriggerType` enum L72495–72547).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Before-delete on Opportunity. Snapshots Closed Won opportunities into Opportunity_Archive__c before the row disappears. There is no after-delete record-triggered flow, so the snapshot has to happen here. triggerOrder 10 in the delete context.</description>
    <environments>Default</environments>
    <interviewLabel>Opportunity BeforeDelete Archive {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Opportunity BeforeDelete Archive</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Archive_Opportunity</name>
        <label>Archive Opportunity</label>
        <locationX>176</locationX>
        <locationY>220</locationY>
        <faultConnector>
            <targetReference>Log_Archive_Fault</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Account__c</field>
            <value>
                <elementReference>$Record.AccountId</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Amount__c</field>
            <value>
                <elementReference>$Record.Amount</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Close_Date__c</field>
            <value>
                <elementReference>$Record.CloseDate</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Name</field>
            <value>
                <elementReference>$Record.Name</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Original_Id__c</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Stage__c</field>
            <value>
                <elementReference>$Record.StageName</elementReference>
            </value>
        </inputAssignments>
        <object>Opportunity_Archive__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordCreates>
        <name>Log_Archive_Fault</name>
        <label>Log Archive Fault</label>
        <locationX>420</locationX>
        <locationY>220</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Request_Id__c</field>
            <value>
                <elementReference>$Flow.InterviewGuid</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>ERROR</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Opportunity_BeforeDelete_Archive</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>176</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Archive_Opportunity</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>StageName</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Closed Won</stringValue>
            </value>
        </filters>
        <object>Opportunity</object>
        <recordTriggerType>Delete</recordTriggerType>
        <triggerType>RecordBeforeDelete</triggerType>
    </start>
    <status>Draft</status>
    <triggerOrder>10</triggerOrder>
</Flow>
```

### How to read it

- `<triggerType>RecordBeforeDelete</triggerType>` — "Deleting a record triggers an
  autolaunched flow before the record is deleted from the database", API 50.0+
  (`api_meta.txt` L72536–72538). Paired with `<recordTriggerType>Delete</recordTriggerType>`
  — "When a record is deleted", also API 50.0+ (L72454–72455).
- **No `doesRequireRecordChangedToMeetCriteria`.** The field is defined against "the
  triggering update" (`api_meta.txt` L72322–72325); a delete has no post-state to compare
  against, so the entry criteria here are plain `<filters>` on the record as it stands.
- **No `$Record__Prior` and no post-delete read.** Everything the archive needs is copied
  out of `$Record` inside this flow. Once the delete completes there is no later
  record-triggered context to run in.
- The Apex Developer Guide notes two delete paths that never reach a trigger evaluation on
  the child: "Cascading delete operations. Only records that initiate a delete cause
  trigger evaluation" and "Cascading updates of child records that are reparented as a
  result of a merge operation" (`apexdev.txt` L15523–15524). Deleting an Account therefore
  will not archive its Opportunities through this flow. UNVERIFIED (2026-09-05): that list
  is written for Apex triggers; neither `api_meta.txt` nor `apexdev.txt` states explicitly
  whether record-triggered delete flows follow the same rule. Treat cascade coverage as
  something to prove in a sandbox before relying on it.
- Merges *do* produce delete events: "A single merge operation fires a single delete event
  for all records that are deleted in the merge" (`apexdev.txt` L15356–15357) — relevant
  when the archived object is one users merge.

---

## 4. FlowTest — Start test point parameters by `recordTriggerType`

`FlowTest` is how you prove the entry criteria before activating: "Before you activate a
record-triggered, autolaunched, or Data Cloud-triggered flow, you can test it to verify
its expected results and identify flow run-time failures" (`api_meta.txt` L73961–73963).
Components have the suffix `.flowtest` and live in the `flowtests` folder (L73976);
in SFDX source format that is `.flowtest-meta.xml`. Available API 55.0+ (L73980).

**The rule this section exists to state.** A Start test point's `$Record` parameters must
match the flow's `recordTriggerType`, and the guide is silent about it —
`FlowTestParameter` documents `leftValueReference`, `type`, and `value` (`api_meta.txt`
L74305–74306 for the field; the `FlowTestParameterType` enum at L74326–74327), and the
guide's own sample (L74351–74365) pairs both `InputTriggeringRecordInitial` and
`InputTriggeringRecordUpdated` on an update-triggered flow — but nowhere does either guide
say a **Create**-triggered flow rejects the `Updated` half of that pair. This was proven
live, not read: a check-only deploy (`sf project deploy start --dry-run`, API 67.0,
2026-09-12) against a Create-triggered flow produced errors that neither guide predicts.
**Rule: Create → `InputTriggeringRecordInitial` only. Update → both (§ 4.1, the guide's own
shape). `CreateAndUpdate` → UNVERIFIED — not observed either way; see
`references/gotchas.md`.** `scripts/check_record_triggered_flow_patterns.py` rule 9
enforces the Create case as an ERROR and flags the CreateAndUpdate case as INFO only.

### 4.1 Update-triggered — both parameters (the guide's own shape)

`Opportunity_AfterSave_ClosedWon_WinsDeal.flowtest-meta.xml` targets the after-save flow in
§ 2, whose `recordTriggerType` is `Update`. The two `$Record` parameters below are what
makes this a *transition* test rather than a state test — `InputTriggeringRecordInitial`
is the prior record, `InputTriggeringRecordUpdated` is the record after the save
(`api_meta.txt` L74326–74327). A flow whose Start lacks
`doesRequireRecordChangedToMeetCriteria` passes this test *and* fires on records that were
already Closed Won, which is exactly the bug the pair is there to catch.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Opportunity moves from Proposal to Closed Won. Asserts the onboarding Task was created and the deal band survived the before-save flow.</description>
    <flowApiName>Opportunity_AfterSave_ClosedWon</flowApiName>
    <label>Closed Won transition creates onboarding task</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;Northwind Renewal&quot;,&quot;StageName&quot;:&quot;Proposal/Price Quote&quot;,&quot;Amount&quot;:300000,&quot;CloseDate&quot;:&quot;2026-09-30&quot;}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;Northwind Renewal&quot;,&quot;StageName&quot;:&quot;Closed Won&quot;,&quot;Amount&quot;:300000,&quot;CloseDate&quot;:&quot;2026-09-30&quot;}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>ScheduledPathApiName</leftValueReference>
            <type>ScheduledPath</type>
            <value>
                <stringValue>Day_7_Renewal_Check</stringValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>$Record.StageName</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Closed Won</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>Stage did not land on Closed Won.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Deal_Band__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Enterprise</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>Before-save flow did not band this deal as Enterprise.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>Create_Onboarding_Task</leftValueReference>
                <operator>IsNull</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>Onboarding Task was not created.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

### How to read it

- `<elementApiName>` accepts only `Start` and `Finish` — "The element API names for the
  start of the flow and the end of the flow" (`api_meta.txt` L74143–74147). You cannot
  assert on a mid-flow element.
- The sObject payload is JSON inside `<sobjectValue>`, XML-escaped, exactly as the guide's
  own sample does it (`api_meta.txt` L74342–74380).
- `<type>ScheduledPath</type>` requires `leftValueReference` to be the literal
  `ScheduledPathApiName` (`api_meta.txt` L74304–74308); it selects which path the test
  exercises. Available API 56.0+ (L74329).
- `IsChanged` is a valid `FlowComparisonOperator` for assertions (`api_meta.txt`
  L74206) — useful when the thing under test is the transition itself.
- `<testType>WithAssertion</testType>` is documented Required but is available only in API
  version 66.0 and later (`api_meta.txt` L74041–74048); the guide's own sample omits it.
  Drop this element if your manifest targets an earlier API version.
- "If one assertion evaluates to `false`, the test run fails" (`api_meta.txt`
  L74158), and each test point is evaluated in the order listed (L74131).
- Salesforce runs a FlowTest against the org, not against a mock: this is a functional
  test with a controlled input record, not a unit test.
- **The Initial/Updated pair here is for `Update`, not for every record-triggered flow.**
  This flow's `recordTriggerType` is `Update`, so its Start test point takes both
  parameters. A **Create**-triggered flow's Start test point takes
  `InputTriggeringRecordInitial` only — carrying `InputTriggeringRecordUpdated` as well
  fails deploy with `The test point for elementApiName "Start" contains the incompatible
  parameter value "$Record" of type InputTriggeringRecordUpdated. Remove the parameter or
  change the recordTriggerType for the flow.`, and carrying `InputTriggeringRecordUpdated`
  alone (no `InputTriggeringRecordInitial`) fails with `The test point for elementApiName
  "Start" is missing a parameter of type InputTriggeringRecordInitial.` — proven live
  (dry-run, API 67.0, 2026-09-12), not stated in `api_meta.txt`. See § 4.2 for the worked
  Create-triggered example and `references/gotchas.md` for the full narrative.

### 4.2 Create-triggered — `InputTriggeringRecordInitial` only

A different object on purpose — Lead intake scoring, not another Opportunity or Case
variant — so the rule reads as general rather than tied to one org model. The flow is
Create-only: it scores a Lead at the moment it is inserted and has nothing to compare a
prior value against, which is also why `recordTriggerType` is `Create` rather than
`CreateAndUpdate` (see `references/gotchas.md` § "`$Record__Prior` Has No Meaningful Value
On A Create" for the general version of that same point).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <assignments>
        <name>Set_Hot_Tier</name>
        <label>Set Hot Tier</label>
        <locationX>50</locationX>
        <locationY>350</locationY>
        <assignmentItems>
            <assignToReference>$Record.Priority_Tier__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Hot</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>$Record.Intake_Score__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <numberValue>90.0</numberValue>
            </value>
        </assignmentItems>
    </assignments>
    <assignments>
        <name>Set_Cold_Tier</name>
        <label>Set Cold Tier</label>
        <locationX>300</locationX>
        <locationY>350</locationY>
        <assignmentItems>
            <assignToReference>$Record.Priority_Tier__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Cold</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>$Record.Intake_Score__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <numberValue>20.0</numberValue>
            </value>
        </assignmentItems>
    </assignments>
    <decisions>
        <name>Classify_Lead</name>
        <label>Classify Lead</label>
        <locationX>176</locationX>
        <locationY>220</locationY>
        <defaultConnector>
            <targetReference>Set_Cold_Tier</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Cold</defaultConnectorLabel>
        <rules>
            <name>Enterprise_Revenue</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.AnnualRevenue</leftValueReference>
                <operator>GreaterThanOrEqualTo</operator>
                <rightValue>
                    <numberValue>1000000.0</numberValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Set_Hot_Tier</targetReference>
            </connector>
            <label>Enterprise Revenue</label>
        </rules>
    </decisions>
    <description>Before-save, Create only. Scores a newly inserted Lead's Intake_Score__c and Priority_Tier__c on the record being inserted. No recordCreates/recordUpdates/recordDeletes/actionCalls/subflows by design (rule 2). recordTriggerType is Create, not CreateAndUpdate: $Record__Prior has no prior state to compare against on an insert, and the FlowTest below proves a Create-triggered flow's Start test point takes InputTriggeringRecordInitial only.</description>
    <environments>Default</environments>
    <interviewLabel>Lead BeforeSave ScoreIntake {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Lead BeforeSave ScoreIntake</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>176</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Classify_Lead</targetReference>
        </connector>
        <object>Lead</object>
        <recordTriggerType>Create</recordTriggerType>
        <triggerType>RecordBeforeSave</triggerType>
    </start>
    <status>Draft</status>
    <triggerOrder>10</triggerOrder>
</Flow>
```

`Lead_BeforeSave_ScoreIntake_Test.flowtest-meta.xml` — the passing shape:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>A new Lead is inserted with AnnualRevenue at enterprise scale. Asserts the before-save flow scored it Hot. Start test point carries InputTriggeringRecordInitial ONLY: this flow's recordTriggerType is Create, and a Create-triggered flow's Start test point does not accept InputTriggeringRecordUpdated (see § 4.1's last "How to read it" bullet and references/gotchas.md).</description>
    <flowApiName>Lead_BeforeSave_ScoreIntake</flowApiName>
    <label>New enterprise lead scores Hot</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;LastName&quot;:&quot;Vandelay&quot;,&quot;Company&quot;:&quot;Vandelay Industries&quot;,&quot;AnnualRevenue&quot;:2500000,&quot;LeadSource&quot;:&quot;Web&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Priority_Tier__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Hot</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>Priority_Tier__c did not land on Hot.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Intake_Score__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <numberValue>90.0</numberValue>
                </rightValue>
            </conditions>
            <errorMessage>Intake_Score__c did not land on 90.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

### How to read it

- **The rule, stated once more with the receipts.** Create → `InputTriggeringRecordInitial`
  only (this example). Update → both parameters (§ 4.1). `CreateAndUpdate` → UNVERIFIED —
  not observed live in either direction, and neither guide states a requirement either
  way; do not guess which shape it wants.
- **Both error texts, verbatim, from the live dry-run (API 67.0, 2026-09-12):**
  - With only `InputTriggeringRecordUpdated` on the Start test point: `The test point for
    elementApiName "Start" is missing a parameter of type InputTriggeringRecordInitial.`
  - With **both** `InputTriggeringRecordInitial` and `InputTriggeringRecordUpdated`: `The
    test point for elementApiName "Start" contains the incompatible parameter value
    "$Record" of type InputTriggeringRecordUpdated. Remove the parameter or change the
    recordTriggerType for the flow.`
  - With `InputTriggeringRecordInitial` only (the shape above): validates.
- **The "missing Initial" message is satisfied by two different shapes, and only one is
  right.** Both "carries `InputTriggeringRecordUpdated` instead of `InputTriggeringRecordInitial`"
  and "carries neither parameter" produce the identical missing-Initial error text. Reading
  that message and adding `InputTriggeringRecordInitial` *alongside* the existing
  `InputTriggeringRecordUpdated` — rather than replacing it — walks straight into the
  second error instead of fixing the test. The fix is always to end up with
  `InputTriggeringRecordInitial` and nothing else in that pair, never to end up with both.
- Nothing else about this flow or test is different from § 1 / § 4.1 — same `apiVersion`,
  same before-save DML-free shape (rule 2), same `<elementApiName>` restriction to `Start`
  and `Finish`. The only thing this example demonstrates is the parameter pairing.
- `scripts/check_record_triggered_flow_patterns.py` rule 9 checks this by reading the
  `FlowTest`'s `<flowApiName>` (the element that names the target flow — confirmed against
  a real `.flowtest-meta.xml` sample, sitting at the top level next to `<label>`, not
  inside `<testPoints>`), resolving it to the matching `*.flow-meta.xml` in the same
  manifest, and comparing that flow's `<recordTriggerType>` against the Start test point's
  parameter types.

---

## 5. Activation — `FlowDefinition`, and why you probably should not use it

Two ways to make a version active, and they fight each other.

**The current way** — set `<status>Active</status>` on the Flow itself. The guide's
API 44.0 upgrade checklist says exactly that: "For each active flow, the `status` field is
`Active`" and "The `flowDefinitions` directory is empty" (`api_meta.txt` L73187–73189).

**The legacy way** — a `FlowDefinition` component, API 34.0+ (`api_meta.txt`
L73940), stored in the `flowDefinitions` directory with extension `.flowDefinition`
(L73935–73936):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <activeVersionNumber>1</activeVersionNumber>
    <description>Legacy activation record for Opportunity_AfterSave_ClosedWon. Present only for orgs still on the pre-44.0 flow file layout.</description>
    <masterLabel>Opportunity AfterSave ClosedWon</masterLabel>
</FlowDefinition>
```

Setting `<activeVersionNumber>0</activeVersionNumber>` deactivates the definition.

The guide states two things about this file that decide whether you ship it:

1. "In API version 44.0, we recommend upgrading your flows to flow metadata file names
   without version numbers and discontinue using the FlowDefinition object to activate or
   deactivate a flow. Then use the Flow object to activate or deactivate a flow"
   (`api_meta.txt` L73925–73928).
2. "If you deploy with flow definitions, the active version numbers in the flow
   definitions override the status fields in the flows. For example, the active version
   number in the flow definition is version 3, and the latest version of the flow is
   version 4 with the status field as `Active`. After you deploy your flow, the active
   version is version 3" (`api_meta.txt` L73929–73932, repeated L73198–73201).

Point 2 is the trap: a stale `FlowDefinition` left in the repo silently pins production to
an older version while the deploy reports success. Ship `<status>` on the Flow, keep
`flowDefinitions/` empty, and treat the block above as something you delete during a
44.0 cleanup rather than something you write.

Deploying an active flow into production also has a precondition: "You can deploy changes
to an active flow if in a non-production org, such as a scratch or sandbox org. To deploy
changes in a production org, you must enable the **Deploy processes and flows as active**
preference" (`api_meta.txt` L68038–68040).

---

## 6. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity_BeforeSave_Normalize</members>
        <members>Opportunity_AfterSave_ClosedWon</members>
        <members>Opportunity_BeforeDelete_Archive</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Opportunity_AfterSave_ClosedWon_WinsDeal</members>
        <name>FlowTest</name>
    </types>
    <types>
        <members>Opportunity_Archive__c</members>
        <members>Application_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Opportunity.Deal_Band__c</members>
        <members>Opportunity.Pricing_Review_Required__c</members>
        <members>Account.Renewal_Review_Due__c</members>
        <name>CustomField</name>
    </types>
    <version>66.0</version>
</Package>
```

`FlowDefinition` supports the wildcard `*` in the manifest (`api_meta.txt`
L73955–73957); `Flow` and `FlowTest` are listed by member here so the manifest states
exactly which three flows and which test are in scope. No `FlowDefinition` entry, per
section 5.

---

## 7. Deploy order

```bash
# 0. lint the flows before anything reaches an org
python3 skills/flow/record-triggered-flow-patterns/scripts/check_record_triggered_flow_patterns.py \
  --manifest-dir force-app/main/default

# 1. check-only validation of the whole manifest — nothing is committed
sf project deploy validate \
  --manifest manifest/package.xml \
  --target-org my-sandbox \
  --test-level RunLocalTests

# 2. fields and objects first: a flow referencing a field that does not exist yet
#    fails at deploy, not at runtime
sf project deploy start \
  --metadata "CustomObject:Opportunity_Archive__c" \
  --metadata "CustomObject:Application_Log__c" \
  --metadata "CustomField:Opportunity.Deal_Band__c" \
  --metadata "CustomField:Opportunity.Pricing_Review_Required__c" \
  --metadata "CustomField:Account.Renewal_Review_Due__c" \
  --target-org my-sandbox

# 3. the three flows, as Draft
sf project deploy start --metadata "Flow" --target-org my-sandbox

# 4. the FlowTest, then run it from Setup > Flows > (flow) > View Tests
sf project deploy start --metadata "FlowTest" --target-org my-sandbox

# 5. activate deliberately: flip <status> to Active, redeploy, and confirm the
#    triggerOrder values in Flow Trigger Explorer before anyone saves a record
sf project deploy start --metadata "Flow:Opportunity_BeforeSave_Normalize" --target-org my-sandbox

# retrieve the set back to see what actually landed, including the version number
sf project retrieve start --manifest manifest/package.xml --target-org my-sandbox
```

Step 1 is the only place a bad `<object>`, a misspelled `<field>`, or a
`<targetReference>` pointing at a nonexistent element surfaces before a user hits it.
Run it on every change, not only the first.

---

## 8. Verification

**Setup.** Setup > Process Automation > Flows > **Flow Trigger Explorer**, filtered to
Opportunity. Confirm three things:

1. Each of the three flows appears in the save context you expect — before-save,
   after-save, before-delete — and none appears twice.
2. The run-order numbers match the `<triggerOrder>` you deployed (10, 20, 10).
3. `Opportunity AfterSave ClosedWon` shows its scheduled path, and the version marked
   *Active* is the version number you intended.

**SOQL.** `FlowDefinitionView` is queryable (`describeSObjects()`, `query()`) from API 46.0
and later (`object_reference.txt` L139267–139273). This is the machine-readable form of
the Trigger Explorer screen, so it is what a deploy pipeline should assert on:

```sql
SELECT ApiName, Label, IsActive, ActiveVersionId, ProcessType,
       TriggerType, RecordTriggerType, TriggerObjectOrEventLabel,
       TriggerOrder, HasAsyncAfterCommitPath, IsOutOfDate
FROM FlowDefinitionView
WHERE TriggerObjectOrEventLabel = 'Opportunity'
  AND TriggerType IN ('RecordBeforeSave', 'RecordAfterSave', 'RecordBeforeDelete')
ORDER BY TriggerType, TriggerOrder
```

Field grounding: `RecordTriggerType` (`object_reference.txt` L139689),
`TriggerObjectOrEventLabel` (L139755), `TriggerOrder` — "from 1 to 2,000 … Available in
API version 54.0 and later" (L139763–139769), `TriggerType` (L139772).

Read the result for two failure shapes:

- **A null `TriggerOrder` on any row where more than one row shares the same
  `TriggerType`.** That is the tie case — two flows in the same save context with no
  declared order.
- **`IsOutOfDate = true`.** The active version is not the latest version; someone saved a
  draft and never activated it.

**Runtime.** Move an Opportunity from Proposal to Closed Won, then read the two channels
the flows write to:

```sql
SELECT Id, Subject, WhatId, OwnerId, ActivityDate, CreatedDate
FROM Task
WHERE Subject = 'Kick off onboarding' AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

```sql
SELECT Id, CreatedDate, Source__c, Severity__c, Message__c, Request_Id__c
FROM Application_Log__c
WHERE Source__c LIKE 'Opportunity_%' AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

Exactly one Task and an empty log is the pass. **Two Tasks for one deal is the
`doesRequireRecordChangedToMeetCriteria` bug** — the record was edited again while already
Closed Won and the after-save flow ran a second time. Rows in the log are fault paths
firing, which means the design worked: the alternative was a silent stop.
