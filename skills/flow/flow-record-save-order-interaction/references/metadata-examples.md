# Metadata Examples — What A Flow Can Observe And Mutate At Each Save-Order Step

Five deployable artifacts plus the manifest, the deploy order, and the
verification that proves *where* each flow ran. Every element name and enum
value below is from the Metadata API Developer Guide, `Flow` section; every
step number is from the Apex Developer Guide, *Triggers and Order of
Execution* (`apexdev.txt` L15416–L15489).

Read this file together with `references/gotchas.md` — the XML shows the
shape, the gotchas explain why the shape is the way it is.

## Assumed org model

| Object | Field | Type | Why it is here |
|---|---|---|---|
| `Case` | `Routing_Key__c` | Text(40) | Written at step 3; read by a duplicate rule at step 6 and a validation rule at step 5 |
| `Case` | `Escalation_Logged__c` | Checkbox | Recursion marker for the step-14 flow |
| `Account` | `Last_Case_Escalation__c` | Date/Time | Parent field the step-14 flow writes |
| `Application_Log__c` | `Message__c`, `Context__c` | Long Text, Text(80) | Fault-path landing per `templates/flow/FaultPath_Template.md` |

`Case` is used deliberately: assignment rules (step 9), auto-response rules
(step 10), escalation rules (step 12) and entitlement rules (step 15) only
have anything to do on Case or Lead, so the interleaving is visible.

---

## 1. Step 3 — a before-save flow that mutates `$Record` with no DML element

`Case_BeforeSave_StampRoutingKey.flow-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Stamp_Routing_Fields</name>
        <label>Stamp Routing Fields</label>
        <locationX>176</locationX>
        <locationY>158</locationY>
        <assignmentItems>
            <assignToReference>$Record.Routing_Key__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>Routing_Key</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>$Record.Priority</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>High</stringValue>
            </value>
        </assignmentItems>
    </assignments>
    <description>Step 3 of the save order. Writes Routing_Key__c and Priority onto the Case being saved. There is no recordUpdates element: RecordBeforeSave exists to "make more updates to that record before it is saved to the database" (api_meta.txt L72539-L72542), so the assignment IS the write.</description>
    <environments>Default</environments>
    <formulas>
        <name>Routing_Key</name>
        <dataType>String</dataType>
        <expression>UPPER(TEXT({!$Record.Origin}) &amp; "-" &amp; TEXT({!$Record.Type}))</expression>
    </formulas>
    <interviewLabel>Case BeforeSave Stamp Routing Key {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Case BeforeSave Stamp Routing Key</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Stamp_Routing_Fields</targetReference>
        </connector>
        <filterFormula>ISPICKVAL({!$Record.Origin}, "Web") &amp;&amp; ISBLANK({!$Record.Routing_Key__c})</filterFormula>
        <object>Case</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordBeforeSave</triggerType>
    </start>
    <status>Active</status>
</Flow>
```

**How to read it**

- `<triggerType>RecordBeforeSave</triggerType>` is what puts this flow at
  step 3 — "Executes record-triggered flows that are configured to run before
  the record is saved" (`apexdev.txt` L15440). Nothing in the XML names a step
  number; the trigger type is the only lever.
- `<assignToReference>$Record.Routing_Key__c</assignToReference>` mutates the
  in-flight record. There is no `recordUpdates` node, and adding one would be
  a second write of the same row.
- **What runs after this write, and therefore sees it:** step 4 before
  triggers, step 5 custom validation rules, step 6 duplicate rules, step 7 the
  save itself. All four are strictly later in the list, so a `Routing_Key__c`
  value invented here is the value a validation rule tests and the value a
  duplicate rule matches on.
- **What this flow cannot see:** anything produced at step 8 or later — the
  assignment-rule owner (step 9), a workflow field update (step 11), a
  recalculated roll-up on the parent (step 16), or the record's `Id` on an
  insert (the row is not written until step 7).
- `<filterFormula>` ("a formula that's used to filter what records execute the
  flow during a save… available only in record-triggered flows",
  `api_meta.txt` L72390–L72392) keeps the interview from starting at all on
  saves that do not matter. That is cheaper than a Decision, because the
  interview never begins.
- `<status>Active</status>` deploys the flow active. In production that
  requires the **Deploy processes and flows as active** preference
  (`api_meta.txt` L68038–L68040); without it, ship `Draft` and activate
  separately.

---

## 2. Step 14, run order 10 — an after-save flow that updates the parent, and the two things that stop it looping

`Case_AfterSave_StampAccountEscalation.flow-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Step 14 of the save order, run order 10. Writes the parent Account, then marks the Case so the transition cannot be counted twice. The Case write is a SECOND save procedure, not part of this one.</description>
    <environments>Default</environments>
    <interviewLabel>Case AfterSave Stamp Account Escalation {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Case AfterSave Stamp Account Escalation</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Account_Update_Failure</name>
        <label>Log Account Update Failure</label>
        <locationX>440</locationX>
        <locationY>158</locationY>
        <inputAssignments>
            <field>Context__c</field>
            <value>
                <stringValue>Case_AfterSave_StampAccountEscalation</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordUpdates>
        <name>Mark_Case_Escalation_Logged</name>
        <label>Mark Case Escalation Logged</label>
        <locationX>176</locationX>
        <locationY>278</locationY>
        <faultConnector>
            <targetReference>Log_Account_Update_Failure</targetReference>
        </faultConnector>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Escalation_Logged__c</field>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </inputAssignments>
        <object>Case</object>
    </recordUpdates>
    <recordUpdates>
        <name>Stamp_Account</name>
        <label>Stamp Account</label>
        <locationX>176</locationX>
        <locationY>158</locationY>
        <connector>
            <targetReference>Mark_Case_Escalation_Logged</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Account_Update_Failure</targetReference>
        </faultConnector>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.AccountId</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Last_Case_Escalation__c</field>
            <value>
                <elementReference>$Flow.CurrentDateTime</elementReference>
            </value>
        </inputAssignments>
        <object>Account</object>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Stamp_Account</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Escalated</stringValue>
            </value>
        </filters>
        <filters>
            <field>Escalation_Logged__c</field>
            <operator>EqualTo</operator>
            <value>
                <booleanValue>false</booleanValue>
            </value>
        </filters>
        <object>Case</object>
        <recordTriggerType>Update</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Active</status>
    <triggerOrder>10</triggerOrder>
</Flow>
```

**How to read it — this is the recursion example**

- `Mark_Case_Escalation_Logged` writes back to `Case`, the triggering object.
  A DML from a flow re-enters the order: "When a process or flow executes a
  DML operation, the affected record goes through the save procedure"
  (`apexdev.txt` L15468). So this element starts a fresh pass over steps
  1–8 for the same Case row.
- That second pass is a **recursive save**, and a recursive save is not the
  same shape as the first one: "During a recursive save, Salesforce skips
  steps 9 (assignment rules) through 17 (roll-up summary field in the
  grandparent record)" (`apexdev.txt` L15414–L15415). Step 14 is inside that
  window, so this flow does **not** re-enter itself from its own write. The
  before-save flow in § 1 and both trigger phases *do* run again.
- The two guards are therefore belt and braces, and each does a different job:
  - `<doesRequireRecordChangedToMeetCriteria>true</…>` — "conditions evaluate
    to true only if the record didn't meet the required conditions before the
    triggering update but now meets the conditions after the update"
    (`api_meta.txt` L72322–L72325). This is a *transition* test. It stops the
    flow re-firing when someone edits the Case later while `Status` is still
    `Escalated`.
  - `Escalation_Logged__c = false` in `<filters>` — a marker the flow sets
    itself. This stops the flow re-firing on a *different* update that also
    happens to flip Status back and forth, and it survives across
    transactions where the transition test does not.
- `<triggerOrder>10</triggerOrder>` — "the run order of a record-triggered
  flow, from 1 to 2,000", API 54.0 and later (`api_meta.txt` L68438–L68441).
  It ranks this flow against § 3, which is the only ordering the platform
  offers inside step 14.
- Every `recordUpdates` carries a `faultConnector`; the fault target is a
  `recordCreates` on `Application_Log__c` and deliberately has no fault path
  of its own (a fault path on a fault path never terminates).
- **What this flow can see that the § 1 flow cannot:** the Case `Id`, the
  assignment-rule owner (step 9 precedes step 14), the auto-response outcome
  (step 10), a workflow field update (step 11), and the escalation-rule result
  (step 12). **What it still cannot see:** entitlement processing (step 15),
  its own parent roll-ups (step 16), criteria-based sharing (step 18), and the
  commit (step 19).

---

## 3. Step 14, run order 20 — the second flow on the same object

`Case_AfterSave_CreateFollowUpTask.flow-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Step 14 of the save order, run order 20. Runs after Case_AfterSave_StampAccountEscalation because triggerOrder 20 &gt; 10. Creates a related Task; it never writes Case, so it adds no recursion of its own.</description>
    <environments>Default</environments>
    <interviewLabel>Case AfterSave Create Follow Up Task {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Case AfterSave Create Follow Up Task</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Create_Follow_Up_Task</name>
        <label>Create Follow Up Task</label>
        <locationX>176</locationX>
        <locationY>158</locationY>
        <faultConnector>
            <targetReference>Log_Task_Failure</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>OwnerId</field>
            <value>
                <elementReference>$Record.OwnerId</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Subject</field>
            <value>
                <stringValue>Escalated case follow-up</stringValue>
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
        <name>Log_Task_Failure</name>
        <label>Log Task Failure</label>
        <locationX>440</locationX>
        <locationY>158</locationY>
        <inputAssignments>
            <field>Context__c</field>
            <value>
                <stringValue>Case_AfterSave_CreateFollowUpTask</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Create_Follow_Up_Task</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Escalated</stringValue>
            </value>
        </filters>
        <object>Case</object>
        <recordTriggerType>Update</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Active</status>
    <triggerOrder>20</triggerOrder>
</Flow>
```

**How to read it**

- `OwnerId` here is the **assignment-rule owner** when one fired, because
  assignment rules are step 9 and this flow is step 14. An Apex *after* trigger
  at step 8 reading the same field sees the pre-assignment owner. That single
  step boundary is the whole difference between "the task went to the right
  queue" and "the task went to the record creator".
- Both flows declare `triggerOrder`, so the pair has a defined rank. The save
  order names step 14 once — "Executes record-triggered flows that are
  configured to run after the record is saved" (`apexdev.txt` L15470) — and
  says nothing about ranking flows inside it; `triggerOrder` is the only
  mechanism the Metadata API exposes for that.
- **UNVERIFIED (2026-09-05): whether the run-order-20 flow's `$Record`
  snapshot is refreshed with field values that the run-order-10 flow wrote to
  the same record is not stated in `apexdev.txt`, `api_meta.txt` or
  `object_reference.txt`.** Design the pair so it does not matter — as here,
  where flow 20 reads only fields no other step-14 flow writes. If you need
  flow 20 to consume flow 10's value, put the value on the record at step 3
  instead.
- **UNVERIFIED (2026-09-05): what the platform does when two flows on the same
  object and trigger type declare the *same* `triggerOrder` is not stated in
  any of the three guides; `api_meta.txt` L68439–L68440 defers to "Guidelines
  for Defining the Run Order of Record-Triggered Flows for an Object" in
  Salesforce Help, which cannot be fetched.** Treat a tie as undefined and fix
  it. `flow/flow-governance` owns the portfolio rule and the checker for it.

---

## 4. Step 20 — a scheduled path, and why it sees committed data

`Case_AfterSave_PostCommitPaths.flow-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Two paths that leave the save transaction. The AsyncAfterCommit path runs as post-commit logic (order-of-execution step 20); the scheduled path runs later still, in its own transaction, against committed data.</description>
    <environments>Default</environments>
    <interviewLabel>Case AfterSave Post Commit Paths {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Case AfterSave Post Commit Paths</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Create_Survey_Task</name>
        <label>Create Survey Task</label>
        <locationX>440</locationX>
        <locationY>158</locationY>
        <inputAssignments>
            <field>Subject</field>
            <value>
                <stringValue>Send CSAT survey</stringValue>
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
    <recordUpdates>
        <name>Recalculate_Account_Health</name>
        <label>Recalculate Account Health</label>
        <locationX>176</locationX>
        <locationY>158</locationY>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.AccountId</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Last_Case_Escalation__c</field>
            <value>
                <elementReference>$Flow.CurrentDateTime</elementReference>
            </value>
        </inputAssignments>
        <object>Account</object>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Closed</stringValue>
            </value>
        </filters>
        <object>Case</object>
        <recordTriggerType>Update</recordTriggerType>
        <scheduledPaths>
            <name>Immediately_After_Commit</name>
            <label>Immediately After Commit</label>
            <connector>
                <targetReference>Recalculate_Account_Health</targetReference>
            </connector>
            <maxBatchSize>200</maxBatchSize>
            <pathType>AsyncAfterCommit</pathType>
        </scheduledPaths>
        <scheduledPaths>
            <name>Two_Days_After_Close</name>
            <label>Two Days After Close</label>
            <connector>
                <targetReference>Create_Survey_Task</targetReference>
            </connector>
            <maxBatchSize>100</maxBatchSize>
            <offsetNumber>2</offsetNumber>
            <offsetUnit>Days</offsetUnit>
            <recordField>ClosedDate</recordField>
            <timeSource>RecordField</timeSource>
        </scheduledPaths>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Active</status>
    <triggerOrder>30</triggerOrder>
</Flow>
```

**How to read it**

- `AsyncAfterCommit` — "the scheduled path runs asynchronously after a save"
  (`api_meta.txt` L71414–L71415). Step 20 of the save order is "After the
  changes are committed to the database, executes post-commit logic", and its
  examples include "Asynchronous paths in record-triggered flows"
  (`apexdev.txt` L15479, L15489). That pair of sentences is *why* an async
  path reads committed data: the commit at step 19 has already happened.
- The consequence is the point: an async path cannot roll the save back. There
  is no step left in the list for it to fail into. If
  `Recalculate_Account_Health` throws, the Case stays closed and the Account
  is stale — so the error has to be handled where the path runs, not by
  relying on the transaction.
- `maxBatchSize` is "the maximum number of scheduled path interviews to
  execute in a single batch, from 1 to 200. Default is 200"
  (`api_meta.txt` L71397–L71398). A path that does per-record work with a low
  limit budget wants a smaller batch; that is a limits decision, and
  `flow/flow-bulkification` owns the arithmetic.
- The time-based path uses `<timeSource>RecordField</timeSource>` with
  `<recordField>ClosedDate</recordField>` and a `+2 Days` offset, so it fires
  in a transaction of its own days later. Nothing it reads is part of the
  original save.
- **UNVERIFIED (2026-09-05): `api_meta.txt` L71392–L71424 does not state which
  of `offsetNumber`, `offsetUnit`, `timeSource` and `recordField` are required
  when `pathType` is `AsyncAfterCommit`.** The shape above omits all four for
  the async path; validate with a check-only deploy (§ 7) before trusting it
  in a pipeline.

---

## 5. Proving the transition — `Case_AfterSave_StampAccountEscalation_Test.flowtest-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Proves the flow fires on the transition into Escalated and not on a later edit while Status is already Escalated.</description>
    <flowApiName>Case_AfterSave_StampAccountEscalation</flowApiName>
    <label>Stamps the Account on escalation</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Status&quot;:&quot;Working&quot;,&quot;Escalation_Logged__c&quot;:false}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Status&quot;:&quot;Escalated&quot;,&quot;Escalation_Logged__c&quot;:false}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Escalation_Logged__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>The recursion marker was not set, so the flow would fire again on the next edit.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

**How to read it**

- The `InputTriggeringRecordInitial` / `InputTriggeringRecordUpdated` pair is
  the only mechanism that exercises
  `doesRequireRecordChangedToMeetCriteria`: the "initial" record must fail the
  entry filter and the "updated" record must pass it. A test that supplies
  only the updated state proves nothing about the transition.
- Element API names are constrained: "The element API names for the start of
  the flow and the end of the flow. Possible values are: Start, Finish"
  (`api_meta.txt` L74143–L74146). You assert at `Finish`, not at an arbitrary
  element.
- Shape and field names follow the guide's own `FlowTest` sample
  (`api_meta.txt` L74342–L74390). `FlowTest` is API 55.0 and later
  (`api_meta.txt` L73980).
- Write the second test yourself: same `InputTriggeringRecordUpdated`, but an
  `InputTriggeringRecordInitial` that *already* has `Status = Escalated`. The
  flow must not act. That is the test that fails when someone removes
  `doesRequireRecordChangedToMeetCriteria`.

---

## 6. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_BeforeSave_StampRoutingKey</members>
        <members>Case_AfterSave_StampAccountEscalation</members>
        <members>Case_AfterSave_CreateFollowUpTask</members>
        <members>Case_AfterSave_PostCommitPaths</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Case_AfterSave_StampAccountEscalation_Test</members>
        <name>FlowTest</name>
    </types>
    <version>66.0</version>
</Package>
```

Flows live in the `flows` directory with the suffix `.flow`
(`api_meta.txt` L68049–L68051); the SFDX source form is
`force-app/main/default/flows/<Name>.flow-meta.xml`. `FlowTest` components
"have the suffix `.flowtest`, and Salesforce stores them in the `flowtests`
folder" (`api_meta.txt` L73976) — source form
`force-app/main/default/flowtests/<Name>.flowtest-meta.xml`.

## 7. Deploy order

The order matters because a flow can be *active* before the fields it writes
exist, and because an active flow changes the behaviour of every save on the
object from the moment it lands.

1. **Fields and objects first.** `Routing_Key__c`, `Escalation_Logged__c`,
   `Last_Case_Escalation__c`, `Application_Log__c`. A flow referencing a
   missing field fails the deploy, which is the good case; a flow deployed
   against a field that exists but is not on any permission set fails at
   runtime, which is not.
2. **Run the checker on the source tree.**

   ```bash
   python3 skills/flow/flow-record-save-order-interaction/scripts/check_flow_record_save_order_interaction.py \
       --manifest-dir force-app/main/default
   ```

3. **Validate without deploying.**

   ```bash
   sf project deploy validate --manifest manifest/package.xml --target-org my-sandbox
   ```

4. **Deploy the before-save flow first, then the after-save flows in
   `triggerOrder` sequence.** If the before-save flow lands second, every save
   between the two deploys runs the step-14 flows against a `Routing_Key__c`
   that nothing populates.

   ```bash
   sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
   ```

5. **Deploy `FlowTest` and run it before activating in production.** Tests are
   separate metadata; a flow can be active with no test attached.

Deploying a change to an already-active flow in production requires the
**Deploy processes and flows as active** preference; without it the deploy
lands a new inactive version and "the flow's detail page shows a new flow
version that's active" only when the preference is on
(`api_meta.txt` L68038–L68040).

## 8. Verification — prove where each flow actually ran

### 8a. Confirm the declared run order

```soql
SELECT ApiName, Label, TriggerType, TriggerObjectOrEventLabel,
       TriggerOrder, ProcessType, IsActive, ApiVersion
FROM FlowDefinitionView
WHERE TriggerObjectOrEventId != NULL
  AND TriggerObjectOrEventLabel = 'Case'
  AND IsActive = TRUE
ORDER BY TriggerType, TriggerOrder NULLS FIRST
```

A row with `TriggerOrder = null` alongside another `RecordAfterSave` row on
the same object is the finding — that is the undeclared tie, and it is
invisible in the flow's own XML. `flow/flow-governance` owns the portfolio
query and the merge gate for it.

### 8b. Read the save order out of a debug log

Set a trace flag with the **Workflow** category at `FINE` and the
**Validation** category at `INFO`, save one Case, and pull the log:

```bash
sf apex log list --target-org my-sandbox
sf apex log get --log-id <id> --target-org my-sandbox > save-order.log
```

Then grep for the event names in order. Each event below is from the Apex
Developer Guide's debug event table, with the category and minimum level the
guide gives for it:

| Save-order step | Debug event to look for | Category / level | Guide line |
|---|---|---|---|
| 3 — before-save flow | `FLOW_START_INTERVIEW_BEGIN` (interview ID and flow name) | Workflow / INFO+ | `apexdev.txt` L38850 |
| 3 — element by element | `FLOW_ELEMENT_BEGIN`, `FLOW_VALUE_ASSIGNMENT` | Workflow / FINE+, FINER+ | `apexdev.txt` L38768, L38896 |
| 4 / 8 — Apex triggers | `CODE_UNIT_STARTED` with the trigger name and event, e.g. `MyTrigger on Account trigger event BeforeInsert` | Apex / ERROR+ | `apexdev.txt` L38187, L38533 |
| 5 — validation rules | `VALIDATION_RULE` (rule name), then `VALIDATION_PASS` / `VALIDATION_FAIL` | Validation / INFO+ | `apexdev.txt` L39201–L39210 |
| 7 — the save | `DML_BEGIN` / `DML_END` | DB / INFO+ | `apexdev.txt` L38658, L38662 |
| 11 — workflow field update | `WF_FIELD_UPDATE`, then a second `CODE_UNIT_STARTED` pair for the re-fired update triggers | Workflow / INFO+ | `apexdev.txt` L39325 |
| 14 — after-save flows | a second `FLOW_START_INTERVIEW_BEGIN`, one per flow, in `triggerOrder` sequence | Workflow / INFO+ | `apexdev.txt` L38850 |
| bulk | `FLOW_START_INTERVIEWS_BEGIN` with the request count — one entry for the whole DML, not one per record | Workflow / INFO+ | `apexdev.txt` L38856 |

**What you are checking:** that the first `FLOW_START_INTERVIEW_BEGIN` precedes
every `CODE_UNIT_STARTED` for a before trigger (step 3 before step 4), that
`VALIDATION_RULE` appears *after* it (step 5 after step 3), and that a second
`FLOW_START_INTERVIEW_BEGIN` block appears after the trigger `CODE_UNIT_*`
pairs (step 14 after step 8). Two `FLOW_START_INTERVIEW_BEGIN` entries naming
the *same* flow in one log is the recursion signature.

**UNVERIFIED (2026-09-05): the literal pipe-delimited layout of each log line
is shown in `apexdev.txt` only for `CODE_UNIT_STARTED` (L38186–L38187); the
guide's event table gives the fields logged for `FLOW_*` and `VALIDATION_*`
events but not their formatting.** Match on the event name, not on a
column position.

### 8c. Confirm the before-save write reached the database

```soql
SELECT Id, CaseNumber, Origin, Type, Routing_Key__c, Priority,
       Escalation_Logged__c, OwnerId, Account.Last_Case_Escalation__c
FROM Case
WHERE CreatedDate = TODAY AND Origin = 'Web'
ORDER BY CreatedDate DESC
LIMIT 20
```

`Routing_Key__c` populated with no `Application_Log__c` row and no second
interview in the log is the pass. `Routing_Key__c` populated but
`Account.Last_Case_Escalation__c` null on an escalated Case means the step-14
flow's entry criteria never matched — check
`doesRequireRecordChangedToMeetCriteria` against how the record actually
moved, not against how you assumed it moved.
