# Metadata Examples — Flow Governor Limits Deep Dive

Two parseable `*.flow-meta.xml` files: the same business requirement built once as a single
synchronous transaction, then split so that the expensive half runs on its own budget. Each element
is annotated with **the meter it spends**, and the budget is totalled before and after. Then a
`FlowTest`, the `package.xml`, the deploy order, and how to read the four flow limit-usage events
out of a debug log.

Every numeric limit below is cited to the Apex Developer Guide text
(`apexdev.txt`, Summer '26 / v62 extract of
<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf>);
every element name and enum value to the Metadata API Developer Guide text
(`api_meta.txt`, extract of
<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>);
Apex-surface facts to the Apex Reference Guide (`apexrefguide.txt`). Anything that lives only on
help.salesforce.com — which cannot be fetched — carries an explicit `UNVERIFIED (2026-09-05)`
marker beside the claim, never in a footnote.

The record-triggered skeleton these adapt is
`templates/flow/RecordTriggered_Skeleton.flow-meta.xml`; the fault-route convention is
`templates/flow/FaultPath_Template.md`. Read those rather than re-deriving the `<start>` block.

---

## 0. The schema these flows assume

EHS facility auditing: an audit closes, its critical findings fan out into remediation tasks, the
audit is stamped, an event is published, and a risk score is computed. This object set is not used
by any sibling `flow/` skill, so both files below deploy into a scratch org next to theirs without
a name collision.

| Object | Fields used here |
|---|---|
| `Facility_Audit__c` | `Name`, `Status__c` (picklist: `Open`, `In_Review`, `Closed`), `Risk_Score__c` (Number), `Findings_Processed__c` (Number), `Closed_On__c` (Date) |
| `Audit_Finding__c` | `Facility_Audit__c` (Master-Detail), `Finding_Code__c` (Text), `Severity__c` (picklist: `Low`, `Major`, `Critical`), `Is_Remediated__c` (Checkbox) |
| `Remediation_Task__c` | `Facility_Audit__c` (Lookup), `Audit_Finding__c` (Lookup), `Subject__c` (Text), `Due_On__c` (Date), `Owner_Group__c` (Text) |
| `Audit_Closed__e` | `Audit_Id__c` (Text 18), `Finding_Count__c` (Number) — a platform event; its **publish behavior** decides which meter §1 spends (see the meter table) |
| `Application_Log__c` | `Message__c` (Long Text), `Related_Record_Id__c` (Text 18), `Severity__c` (picklist), `Source__c` (Text) |

`Application_Log__c` is the shared fault-log object the other `flow/` skills also write to; keep one
definition per org.

---

## 1. Which element spends which meter

This is the table the rest of the file is built on. The left column is the **metadata tag**, because
that is what you can grep for; the Flow Builder label is in parentheses.

| Element | Meter(s) it spends | Grounding |
|---|---|---|
| `recordLookups` (Get Records) | SOQL queries **+1**, SOQL query rows **+N** | `apexdev.txt` L19544 (100 sync / 200 async), L19546 (50,000 rows) |
| `recordLookups` with `relatedRecords` (beta) | SOQL queries **+1 per parent-child relationship**, not +1 total | footnote 1, `apexdev.txt` L19613–L19615: "each parent-child relationship counts as an extra query" |
| `recordCreates` / `recordUpdates` / `recordDeletes` | DML statements **+1**, DML rows **+N** | `apexdev.txt` L19554 (150), L19556 (10,000) |
| `recordCreates` on a `__e` set to **Publish After Commit** | DML statements **+1** | footnote 2, `apexdev.txt` L19635; `apexrefguide.txt` L214524–L214526 |
| `recordCreates` on a `__e` set to **Publish Immediately** | the separate publish meter, **150** — *not* the DML meter | `apexdev.txt` L19598–L19599; `apexrefguide.txt` L214526–L214528 |
| `loops`, `assignments`, `decisions`, `collectionProcessors`, `transforms` | CPU time **only** | footnote 5, `apexdev.txt` L19652–L19653: CPU "is calculated for the executing Apex code, and for any processes that are called from this code" |
| `actionCalls` `actionType` `apex` with `flowTransactionModel` `CurrentTransaction` or `Automatic` | **every meter the Apex itself spends**, added to this transaction | `api_meta.txt` L68475–L68476: "Keeps the invocable action running in the same transaction" |
| `actionCalls` `actionType` `apex` with `flowTransactionModel` `NewTransaction` | nothing here — a new transaction with its own meters | `api_meta.txt` L68477–L68478: "Creates a transaction before the invocable action is executed" |
| `actionCalls` `actionType` `emailAlert` / `emailSimple` | email invocations, ceiling **10** | `api_meta.txt` L68729, L68731; `apexdev.txt` L19575; `apexrefguide.txt` L220241 (`Limits.getEmailInvocations()`) |
| `actionCalls` `actionType` `submit` (Submit for Approval) | DML statements **+1** | `api_meta.txt` L68928; footnote 2, `apexdev.txt` L19624 (`Approval.process`) |
| `subflows` | the **parent's** meters | `flowTransactionModel` is a field of `FlowActionCall` only (`api_meta.txt` L68472); `FlowSubflow` has no transactional field, so nothing in Flow metadata lets a subflow open one |
| `screens` | UNVERIFIED (2026-09-05): the developer guides in this corpus never state that a screen ends the transaction. The nearest documented fact is that `FlowRecordRollback` — "Rolls back the current transaction and cancels its pending record changes" — is "available only in screen flows" (`api_meta.txt` L71247–L71250), which implies a screen flow accumulates *pending* record changes across a boundary. The Flow "Per-Transaction Flow Limits" help page is the only stated home for the rule |
| `waits` (Pause) | UNVERIFIED (2026-09-05): `grep -n -i "pause.*transaction\|wait.*transaction" api_meta.txt` returns no statement that a Pause element ends the transaction. What *is* documented is that a paused interview is a distinct lifecycle state — `FLOW_INTERVIEW_PAUSED` and `FLOW_INTERVIEW_RESUMED` are separate debug-log events (`apexdev.txt` L38834–L38841), and a flow version with paused interviews cannot be deleted (`api_meta.txt` L68041–L68042) |
| `scheduledPaths` with `pathType` `AsyncAfterCommit` | nothing in the triggering transaction — the path runs post-commit | `apexdev.txt` L15489 lists "Asynchronous paths in record-triggered flows" as step-20 post-commit logic; `api_meta.txt` L71412–L71414 |

Two meters have **no** Flow element that spends them, which is why they never appear in a flow
budget: `Database.getQueryLocator` rows (10,000, `apexdev.txt` L19548) and SOSL queries (20,
L19550) — Flow has no SOSL element.

---

## 2. `Facility_Audit_Close_Out.flow-meta.xml` — everything in one transaction

Nine elements. Read the `<!-- meter: ... -->` comment above each one; that is the entire point of
this file.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <description>Closes out a facility audit: fans critical findings into remediation tasks, stamps the audit, publishes an event, notifies EHS, and scores risk. Every element annotated with the governor meter it spends. Baseline for the split version in section 3.</description>
    <environments>Default</environments>
    <interviewLabel>Facility Audit Close Out {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Facility Audit Close Out</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <status>Active</status>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Get_Critical_Findings</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Closed</stringValue>
            </value>
        </filters>
        <object>Facility_Audit__c</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <!-- meter: SOQL queries +1, SOQL query rows +N. limit is API 63.0, valid 2-20000
         (api_meta.txt L71173-L71180). Capping here caps the row spend deterministically. -->
    <recordLookups>
        <name>Get_Critical_Findings</name>
        <label>Get Critical Findings</label>
        <locationX>50</locationX>
        <locationY>120</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Loop_Findings</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Facility_Audit__c</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <filters>
            <field>Severity__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Critical</stringValue>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <limit>
            <numberValue>2000.0</numberValue>
        </limit>
        <object>Audit_Finding__c</object>
        <queriedFields>Id</queriedFields>
        <queriedFields>Finding_Code__c</queriedFields>
        <queriedFields>Severity__c</queriedFields>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <!-- meter: CPU time only. A loop issues no query and no DML; it spends application-server
         CPU per iteration (apexdev.txt footnote 5, L19652-L19653). The database time of the
         Get above is NOT charged to CPU (L19655-L19656) - only the iteration over its rows is. -->
    <loops>
        <name>Loop_Findings</name>
        <label>Loop Findings</label>
        <locationX>50</locationX>
        <locationY>240</locationY>
        <collectionReference>Get_Critical_Findings</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Build_Task_Draft</targetReference>
        </nextValueConnector>
        <noMoreValuesConnector>
            <targetReference>Create_Remediation_Tasks</targetReference>
        </noMoreValuesConnector>
    </loops>
    <!-- meter: CPU time only. Staging records in a collection inside the loop is what keeps the
         DML meter at 1 instead of N. The staging pattern itself belongs to
         flow/flow-bulkification; this file only accounts for what it costs. -->
    <assignments>
        <name>Build_Task_Draft</name>
        <label>Build Task Draft</label>
        <locationX>230</locationX>
        <locationY>240</locationY>
        <assignmentItems>
            <assignToReference>taskDraft.Facility_Audit__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>taskDraft.Audit_Finding__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>Loop_Findings.Id</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>taskDraft.Subject__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>Loop_Findings.Finding_Code__c</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>tasksToCreate</assignToReference>
            <operator>Add</operator>
            <value>
                <elementReference>taskDraft</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>findingCount</assignToReference>
            <operator>Add</operator>
            <value>
                <numberValue>1.0</numberValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Loop_Findings</targetReference>
        </connector>
    </assignments>
    <!-- meter: DML statements +1, DML rows +N (apexdev.txt L19554, L19556). One element,
         N rows - the row meter scales with the data, the statement meter does not. -->
    <recordCreates>
        <name>Create_Remediation_Tasks</name>
        <label>Create Remediation Tasks</label>
        <locationX>50</locationX>
        <locationY>360</locationY>
        <connector>
            <targetReference>Stamp_Audit</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <inputReference>tasksToCreate</inputReference>
    </recordCreates>
    <!-- meter: DML statements +1, DML rows +1. This is an after-save flow, so writing back to
         the triggering record is a real DML that re-enters the save order (apexdev.txt L15461:
         "When a process or flow executes a DML operation, the affected record goes through the
         save procedure"). Recursion and stack depth: flow/flow-record-save-order-interaction. -->
    <recordUpdates>
        <name>Stamp_Audit</name>
        <label>Stamp Audit</label>
        <locationX>50</locationX>
        <locationY>480</locationY>
        <connector>
            <targetReference>Publish_Audit_Closed</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Findings_Processed__c</field>
            <value>
                <elementReference>findingCount</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Closed_On__c</field>
            <value>
                <elementReference>$Flow.CurrentDate</elementReference>
            </value>
        </inputAssignments>
        <object>Facility_Audit__c</object>
    </recordUpdates>
    <!-- meter: DEPENDS ON THE EVENT DEFINITION, not on this XML. Publish After Commit spends
         DML statements +1 (apexdev.txt L19635); Publish Immediately spends the separate
         150-call publish meter and NOT the DML meter (apexdev.txt L19598-L19599,
         apexrefguide.txt L214526-L214528). Two identical-looking elements, two different budgets. -->
    <recordCreates>
        <name>Publish_Audit_Closed</name>
        <label>Publish Audit Closed</label>
        <locationX>50</locationX>
        <locationY>600</locationY>
        <connector>
            <targetReference>Notify_EHS</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Audit_Id__c</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Finding_Count__c</field>
            <value>
                <elementReference>findingCount</elementReference>
            </value>
        </inputAssignments>
        <object>Audit_Closed__e</object>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordCreates>
    <!-- meter: email invocations +1, ceiling 10 for the whole transaction (apexdev.txt L19575).
         Ten alerts across every flow, trigger and Apex class on this save, not ten per flow. -->
    <actionCalls>
        <name>Notify_EHS</name>
        <label>Notify EHS</label>
        <locationX>50</locationX>
        <locationY>720</locationY>
        <actionName>Facility_Audit__c.Audit_Closed_Alert</actionName>
        <actionType>emailAlert</actionType>
        <connector>
            <targetReference>Score_Audit_Risk</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>SObjectRowId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputParameters>
    </actionCalls>
    <!-- meter: WHATEVER THE APEX SPENDS, charged here. flowTransactionModel CurrentTransaction
         "Keeps the invocable action running in the same transaction" (api_meta.txt L68475-L68476),
         so the class's own SOQL, DML, callouts and CPU come out of this budget. Read the class
         before you budget the flow. Section 3 flips this to NewTransaction. -->
    <actionCalls>
        <name>Score_Audit_Risk</name>
        <label>Score Audit Risk</label>
        <locationX>50</locationX>
        <locationY>840</locationY>
        <actionName>FacilityAuditRiskScorer</actionName>
        <actionType>apex</actionType>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>auditIds</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputParameters>
    </actionCalls>
    <!-- meter: DML statements +1, DML rows +1 - and only on the fault path. A fault route is
         not free: it spends from the same budget that was already under pressure. It also cannot
         run at all for a limit exception (see "How to read it" below). -->
    <recordCreates>
        <name>Log_Fault</name>
        <label>Log Fault</label>
        <locationX>320</locationX>
        <locationY>840</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Related_Record_Id__c</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>Error</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Facility_Audit_Close_Out</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordCreates>
    <variables>
        <name>findingCount</name>
        <dataType>Number</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <scale>0</scale>
        <value>
            <numberValue>0.0</numberValue>
        </value>
    </variables>
    <variables>
        <name>taskDraft</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Remediation_Task__c</objectType>
    </variables>
    <variables>
        <name>tasksToCreate</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Remediation_Task__c</objectType>
    </variables>
</Flow>
```

### Budget for §2, at a 200-record save

The triggering DML saves 200 `Facility_Audit__c` records. Each record starts its own interview —
"A flow interview starts for each record that meets the filter conditions" (`api_meta.txt`
L72403–L72405) — but all of those interviews run inside the **one** transaction that the save
opened, so they share one set of meters. Assume 6 critical findings per audit.

| Meter | Ceiling (sync) | Spend | % | Grounding for the ceiling |
|---|---|---|---|---|
| SOQL queries | 100 | 1 | 1% | `apexdev.txt` L19544 |
| SOQL query rows | 50,000 | 1,200 | 2% | `apexdev.txt` L19546 |
| DML statements | 150 | 4 | 3% | `apexdev.txt` L19554 |
| DML rows | 10,000 | **1,600** | **16%** | `apexdev.txt` L19556 |
| Email invocations | 10 | 1 | 10% | `apexdev.txt` L19575 |
| Publish-immediately calls | 150 | 1 (or 0, if the event is Publish After Commit) | <1% | `apexdev.txt` L19598–L19599 |
| CPU time | 10,000 ms | 1,200 loop iterations + the Apex action | **unknown until measured** | `apexdev.txt` L19579 |
| Heap | 6 MB | 1,200 findings + 1,200 staged tasks | **unknown until measured** | `apexdev.txt` L19577 |

Notice what the table cannot tell you. Four meters are arithmetic from the metadata; **CPU and heap
are not**, because their spend depends on `FacilityAuditRiskScorer`'s implementation and on field
count per row. Anyone who hands you a CPU number derived from element counts has invented it — the
guides publish no per-element cost. Measure them (§7).

The element that actually threatens this flow is **DML rows at 16%**, not the SOQL statement count
everyone watches. Three more automations of the same shape on `Facility_Audit__c` and the row meter,
not the statement meter, is what breaks.

---

## 3. `Facility_Audit_Close_Out_Split.flow-meta.xml` — the same work, two budgets

Two levers, both documented:

1. **`scheduledPaths` with `pathType` `AsyncAfterCommit`** (`api_meta.txt` L71412–L71414). The path
   runs post-commit — the Apex Developer Guide lists "Asynchronous paths in record-triggered flows"
   among the step-20 post-commit examples (`apexdev.txt` L15489). `maxBatchSize` is "the maximum
   number of scheduled path interviews to execute in a single batch, from 1 to 200. Default is 200"
   (`api_meta.txt` L71397–L71398), so it is also the knob that decides how many interviews share the
   async transaction's meters.
2. **`flowTransactionModel` `NewTransaction`** on the Apex action — "Creates a transaction before
   the invocable action is executed" (`api_meta.txt` L68477–L68478). Available in API 51.0 and later
   (L68480).

Only the differences from §2 are shown; every unchanged element is byte-identical.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <description>Split version of Facility Audit Close Out. The immediate path spends only what the save must be atomic with; notification and risk scoring run on an AsyncAfterCommit scheduled path, and the Apex action opens its own transaction.</description>
    <environments>Default</environments>
    <interviewLabel>Facility Audit Close Out Split {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Facility Audit Close Out Split</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <status>Active</status>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Get_Critical_Findings</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Closed</stringValue>
            </value>
        </filters>
        <object>Facility_Audit__c</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <!-- The transaction-splitting lever. pathType AsyncAfterCommit runs this branch after
             the save commits (api_meta.txt L71412-L71414; apexdev.txt L15489). maxBatchSize caps
             how many interviews share the async transaction's meters (api_meta.txt L71397-L71398).
             timeSource RecordTriggerEvent + offsetNumber 0 = "immediately after commit".
             UNVERIFIED (2026-09-05): whether the async path's transaction is metered at the
             synchronous ceilings (100 SOQL / 10,000 ms CPU) or the asynchronous ones
             (200 / 60,000) is not stated anywhere in apexdev.txt, api_meta.txt or the App Limits
             cheat sheet. Budget it at the SYNCHRONOUS ceilings until you have measured your own
             org's FLOW_INTERVIEW_FINISHED_LIMIT_USAGE line, which prints the actual denominator. -->
        <scheduledPaths>
            <name>Async_Enrichment</name>
            <label>Async Enrichment</label>
            <connector>
                <targetReference>Notify_EHS</targetReference>
            </connector>
            <maxBatchSize>200</maxBatchSize>
            <offsetNumber>0</offsetNumber>
            <offsetUnit>Minutes</offsetUnit>
            <pathType>AsyncAfterCommit</pathType>
            <timeSource>RecordTriggerEvent</timeSource>
        </scheduledPaths>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <recordLookups>
        <name>Get_Critical_Findings</name>
        <label>Get Critical Findings</label>
        <locationX>50</locationX>
        <locationY>120</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Loop_Findings</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Facility_Audit__c</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <filters>
            <field>Severity__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Critical</stringValue>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <limit>
            <numberValue>2000.0</numberValue>
        </limit>
        <object>Audit_Finding__c</object>
        <queriedFields>Id</queriedFields>
        <queriedFields>Finding_Code__c</queriedFields>
        <queriedFields>Severity__c</queriedFields>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <loops>
        <name>Loop_Findings</name>
        <label>Loop Findings</label>
        <locationX>50</locationX>
        <locationY>240</locationY>
        <collectionReference>Get_Critical_Findings</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Build_Task_Draft</targetReference>
        </nextValueConnector>
        <noMoreValuesConnector>
            <targetReference>Create_Remediation_Tasks</targetReference>
        </noMoreValuesConnector>
    </loops>
    <assignments>
        <name>Build_Task_Draft</name>
        <label>Build Task Draft</label>
        <locationX>230</locationX>
        <locationY>240</locationY>
        <assignmentItems>
            <assignToReference>taskDraft.Facility_Audit__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>taskDraft.Audit_Finding__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>Loop_Findings.Id</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>taskDraft.Subject__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>Loop_Findings.Finding_Code__c</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>tasksToCreate</assignToReference>
            <operator>Add</operator>
            <value>
                <elementReference>taskDraft</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>findingCount</assignToReference>
            <operator>Add</operator>
            <value>
                <numberValue>1.0</numberValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Loop_Findings</targetReference>
        </connector>
    </assignments>
    <recordCreates>
        <name>Create_Remediation_Tasks</name>
        <label>Create Remediation Tasks</label>
        <locationX>50</locationX>
        <locationY>360</locationY>
        <connector>
            <targetReference>Stamp_Audit</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <inputReference>tasksToCreate</inputReference>
    </recordCreates>
    <recordUpdates>
        <name>Stamp_Audit</name>
        <label>Stamp Audit</label>
        <locationX>50</locationX>
        <locationY>480</locationY>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Findings_Processed__c</field>
            <value>
                <elementReference>findingCount</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Closed_On__c</field>
            <value>
                <elementReference>$Flow.CurrentDate</elementReference>
            </value>
        </inputAssignments>
        <object>Facility_Audit__c</object>
    </recordUpdates>
    <!-- Moved onto the async path: the immediate transaction no longer spends the publish meter,
         the email meter, or anything the Apex action costs. -->
    <recordCreates>
        <name>Publish_Audit_Closed</name>
        <label>Publish Audit Closed</label>
        <locationX>320</locationX>
        <locationY>240</locationY>
        <connector>
            <targetReference>Score_Audit_Risk</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Audit_Id__c</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Finding_Count__c</field>
            <value>
                <elementReference>$Record.Findings_Processed__c</elementReference>
            </value>
        </inputAssignments>
        <object>Audit_Closed__e</object>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordCreates>
    <actionCalls>
        <name>Notify_EHS</name>
        <label>Notify EHS</label>
        <locationX>320</locationX>
        <locationY>120</locationY>
        <actionName>Facility_Audit__c.Audit_Closed_Alert</actionName>
        <actionType>emailAlert</actionType>
        <connector>
            <targetReference>Publish_Audit_Closed</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>SObjectRowId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputParameters>
    </actionCalls>
    <!-- The second lever. NewTransaction "Creates a transaction before the invocable action is
         executed" (api_meta.txt L68477-L68478, API 51.0+), so FacilityAuditRiskScorer's own SOQL,
         DML, CPU and callouts come out of a fresh set of meters instead of this interview's.
         The cost is atomicity: work already committed is not rolled back if the action fails,
         which is why Log_Fault stays wired. -->
    <actionCalls>
        <name>Score_Audit_Risk</name>
        <label>Score Audit Risk</label>
        <locationX>320</locationX>
        <locationY>360</locationY>
        <actionName>FacilityAuditRiskScorer</actionName>
        <actionType>apex</actionType>
        <faultConnector>
            <targetReference>Log_Fault</targetReference>
        </faultConnector>
        <flowTransactionModel>NewTransaction</flowTransactionModel>
        <inputParameters>
            <name>auditIds</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputParameters>
    </actionCalls>
    <recordCreates>
        <name>Log_Fault</name>
        <label>Log Fault</label>
        <locationX>500</locationX>
        <locationY>480</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Related_Record_Id__c</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>Error</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Facility_Audit_Close_Out_Split</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordCreates>
    <variables>
        <name>findingCount</name>
        <dataType>Number</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <scale>0</scale>
        <value>
            <numberValue>0.0</numberValue>
        </value>
    </variables>
    <variables>
        <name>taskDraft</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Remediation_Task__c</objectType>
    </variables>
    <variables>
        <name>tasksToCreate</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Remediation_Task__c</objectType>
    </variables>
</Flow>
```

### Budget before and after, at the same 200-record save

| Meter | §2 — one transaction | §3 immediate path | §3 async path | §3 `NewTransaction` |
|---|---|---|---|---|
| SOQL queries | 1 | 1 | 0 | whatever the Apex spends |
| SOQL query rows | 1,200 | 1,200 | 0 | whatever the Apex spends |
| DML statements | 4 | 3 | 1 (event, if Publish After Commit) | whatever the Apex spends |
| DML rows | 1,600 | 1,400 | 200 | whatever the Apex spends |
| Email invocations | 1 | **0** | 1 | 0 |
| Publish-immediately calls | 1 | **0** | 1 (if Publish Immediately) | 0 |
| Apex action's own consumption | **added here** | **0** | 0 | **isolated** |
| Rolled back if a later element fails? | yes, all of it | yes | no — the save already committed | no |

The split does not make the work cheaper. It moves three meters out of the transaction the user is
waiting on, and it converts one atomic failure into two independent ones. That trade — atomicity for
budget — is the whole decision, and `references/well-architected.md` frames when to take it.

**What the split does not fix:** if `Get_Critical_Findings` were inside `Loop_Findings`, moving it
to an async path would breach the SOQL meter at the same iteration count, just later and with no
user watching. Async buys a fresh budget, never a smaller spend.

---

## 4. `Facility_Audit_Close_Out_Creates_Tasks.flowtest-meta.xml`

`FlowTest` is available in API 55.0 and later, `testType` in 66.0 (`api_meta.txt` L73977, L74110).
`FlowTestPoint.elementApiName` accepts only `Start` and `Finish` (`api_meta.txt` L74139–L74146), so
the only assertable evidence that the flow stayed inside its budget is a **count that survives to
the end** — here `Findings_Processed__c`, written by `Stamp_Audit`. That is why the count exists.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Closing an audit with critical findings stamps a non-zero processed count, proving the loop ran and the single collection DML committed.</description>
    <flowApiName>Facility_Audit_Close_Out</flowApiName>
    <label>Close Out Creates Remediation Tasks</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;Plant 12 Q3 Audit&quot;,&quot;Status__c&quot;:&quot;In_Review&quot;}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;Plant 12 Q3 Audit&quot;,&quot;Status__c&quot;:&quot;Closed&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Findings_Processed__c</leftValueReference>
                <operator>GreaterThan</operator>
                <rightValue>
                    <numberValue>0.0</numberValue>
                </rightValue>
            </conditions>
            <errorMessage>Findings_Processed__c is 0 - the loop did not run, so the collection DML committed nothing.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
</FlowTest>
```

Two things a `FlowTest` **cannot** do, which is why §7 exists:

- It asserts on flow *data*, not on meter consumption. There is no `FlowTestCondition` operator that
  reads a governor counter (the enum is at `api_meta.txt` L74196–L74232).
- `InputTriggeringRecordInitial` / `InputTriggeringRecordUpdated` describe **one** record
  (`api_meta.txt` L74310–L74316). A `FlowTest` therefore proves correctness at bulk size 1. Bulk
  budget evidence comes from the Apex test in §7 or from a debug log.

To assert against the split flow's async path, add a third parameter with `type` `ScheduledPath`
and `leftValueReference` `ScheduledPathApiName` — that value is fixed by the guide
(`api_meta.txt` L74306–L74309) — set to `Async_Enrichment`.

---

## 5. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Facility_Audit__c</members>
        <members>Audit_Finding__c</members>
        <members>Remediation_Task__c</members>
        <members>Audit_Closed__e</members>
        <members>Application_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>FacilityAuditRiskScorer</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Facility_Audit__c.Audit_Closed_Alert</members>
        <name>WorkflowAlert</name>
    </types>
    <types>
        <members>Facility_Audit_Close_Out</members>
        <members>Facility_Audit_Close_Out_Split</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Facility_Audit_Close_Out_Creates_Tasks</members>
        <name>FlowTest</name>
    </types>
    <version>63.0</version>
</Package>
```

`FlowTest` components "have the suffix `.flowtest`, and Salesforce stores them in the `flowtests`
folder" (`api_meta.txt` L73971–L73972).

---

## 6. Deploy order

Each step fails if the previous one has not landed.

1. **Objects and fields.** `Facility_Audit__c`, `Audit_Finding__c`, `Remediation_Task__c`,
   `Application_Log__c`, and the `Audit_Closed__e` platform event. The event's **publish behavior**
   is set here and it decides which meter §2's `Publish_Audit_Closed` spends — settle it before you
   budget anything.
2. **`FacilityAuditRiskScorer`.** The flow's `actionCalls` fails to deploy against a missing
   `@InvocableMethod`. Budget the class first: its own SOQL and DML are charged to the flow's
   transaction under `CurrentTransaction` (`api_meta.txt` L68475–L68476).
3. **The email alert.** `Facility_Audit__c.Audit_Closed_Alert` — `emailAlert` "Sends an email by
   referencing a workflow email alert" (`api_meta.txt` L68729), so the alert must exist.
4. **The flows**, `status` `Draft` first. Deploy `Facility_Audit_Close_Out_Split` and
   `Facility_Audit_Close_Out` separately, never both `Active` on the same object at once — two
   active flows on the same object and trigger type both fire, and both spend from the same meters.
5. **The `FlowTest`,** then run it.
6. **Flip `status` to `Active`,** and set `triggerOrder` if anything else is active on
   `Facility_Audit__c`. `triggerOrder` is "the run order of a record-triggered flow, from 1 to 2,000"
   (`api_meta.txt` L68438–L68439) — it decides *sequence*, never *budget*: the flow that runs at
   order 2,000 inherits everything orders 1–1,999 already spent.

```bash
# Validate without committing anything.
sf project deploy start --dry-run --source-dir force-app --test-level RunLocalTests

# Deploy.
sf project deploy start --source-dir force-app

# Run this flow's test.
sf flow run test --tests Facility_Audit_Close_Out_Creates_Tasks

# Round-trip: retrieve what the org actually stored and diff it against what you wrote.
sf project retrieve start --metadata Flow:Facility_Audit_Close_Out
sf project retrieve start --metadata Flow:Facility_Audit_Close_Out_Split
```

---

## 7. Verifying the budget in a real transaction

The metadata gives you SOQL, DML and row counts by arithmetic. CPU and heap only come from a run.

### 7a. Read the four limit-usage events out of a debug log

Set the **Workflow** log category to `FINER` or above. At that level the flow engine emits four
distinct limit-usage events, and every one of them enumerates the *same* twelve meters
(`apexdev.txt` L38730–L38744, L38795–L38820, L38821–L38834, L38874–L38888):

| Event | Emitted | Answers |
|---|---|---|
| `FLOW_START_INTERVIEW_LIMIT_USAGE` | at the interview's start | what the transaction had **already** spent before this flow ran |
| `FLOW_ELEMENT_LIMIT_USAGE` | per element | which element spent what |
| `FLOW_BULK_ELEMENT_LIMIT_USAGE` | per bulk element | what one element cost **across every interview in the batch** |
| `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` | at the interview's finish | this interview's total |

The twelve meters each event reports: SOQL queries, SOQL query rows, SOSL queries, DML statements,
DML rows, CPU time in ms, heap size in bytes, callouts, email invocations, future calls, jobs in
queue, push notifications.

**The negative that matters more than the list.** None of the four events reports an *element count*.
Neither does `LIMIT_USAGE_FOR_NS` (`apexdev.txt` L38930–L38948). A flow's own instrumentation reports
against every meter the platform still enforces, and an executed-elements meter is not among them.
`grep -n -i "2,\?000 element|executed elements|number of elements" apexdev.txt api_meta.txt
salesforce_app_limits_cheatsheet.txt` returns four hits and **not one is a limit**: three are
`FlowTestCoverage.numElements` / `numElementsNotCovered`, which count a flow version's elements for
test coverage (`api_meta.txt` L7715, L7727, L7729), and one is a UI display cap
(`maxValuesDisplayed`, L48167). Treat "flows are limited to 2,000 executed elements per interview"
as retired; budget the meters the log actually prints.

The guide ships one real limit-usage log excerpt, and it is an Apex one — `LIMIT_USAGE_FOR_NS`
(`apexdev.txt` L38274–L38287), reproduced verbatim:

```text
16:06:58.49 (49590539)|CUMULATIVE_LIMIT_USAGE
16:06:58.49 (49590539)|LIMIT_USAGE_FOR_NS|(default)|
  Number of SOQL queries: 0 out of 100
  Number of query rows: 0 out of 50000
  Number of SOSL queries: 0 out of 20
  Number of DML statements: 0 out of 150
  Number of DML rows: 0 out of 10000
  Maximum CPU time: 0 out of 10000
  Maximum heap size: 0 out of 6000000
  Number of callouts: 0 out of 100
  Number of Email Invocations: 0 out of 10
  Number of future calls: 0 out of 50
  Number of queueable jobs added to the queue: 0 out of 50
  Number of Mobile Apex push calls: 0 out of 10

16:06:58.49 (49590539)|CUMULATIVE_LIMIT_USAGE_END
```

That block is the **transaction** total, `(default)` namespace, and it is what you compare a flow
budget against — the denominators are the ceilings this skill's table lists. The flow events are the
per-interview and per-element breakdown of the same numbers.

Here is what §2 looks like at Workflow `FINER`, annotated. **UNVERIFIED (2026-09-05): the literal
line layout below is constructed.** The guide documents the event names and the twelve fields each
one logs (`apexdev.txt` L38721–L38900) but ships no sample log line for any flow event; only the
`LIMIT_USAGE_FOR_NS` block above is quoted verbatim. Read the shape as a guide to *what to look for*,
and confirm the exact delimiters against a log from your own org.

```text
|FLOW_START_INTERVIEWS_BEGIN|200
   -> 200 interviews, ONE transaction. The event logs "Requests" (apexdev.txt L38856).

|FLOW_START_INTERVIEW_LIMIT_USAGE|[SOQL queries: 14 out of 100]
   -> The flow has not run an element yet and 14 queries are already gone. Spent by the
      trigger/VR/earlier flow ahead of it in the save order. THIS is the number that a
      sandbox test with no other automation never shows you.

|FLOW_BULK_ELEMENT_BEGIN|recordLookup
|FLOW_BULK_ELEMENT_DETAIL|Get_Critical_Findings|records:1200
|FLOW_BULK_ELEMENT_LIMIT_USAGE|[SOQL queries: 1][SOQL query rows: 1200]
   -> ONE query for all 200 interviews. The engine executed the element once across the batch,
      which is why the Get is +1 and not +200. FLOW_BULK_ELEMENT_DETAIL logs "number of records"
      (apexdev.txt L38724-L38725).

|FLOW_ELEMENT_LIMIT_USAGE|Build_Task_Draft|[CPU time in ms: 43]
   -> An Assignment spends CPU and nothing else. Multiply by iterations, not by elements.

|FLOW_BULK_ELEMENT_LIMIT_USAGE|Create_Remediation_Tasks|[DML statements: 1][DML rows: 1200]
   -> The staging pattern's payoff: 1 statement, 1200 rows. Statement meter 1/150,
      row meter 1200/10000. The row meter is the one under pressure.

|FLOW_ELEMENT_LIMIT_USAGE|Score_Audit_Risk|[SOQL queries: 3][DML statements: 2][CPU time in ms: 890]
   -> The Apex action's own consumption, charged here because flowTransactionModel is
      CurrentTransaction. Under NewTransaction this line reads 0 across the board.

|FLOW_INTERVIEW_FINISHED_LIMIT_USAGE|[SOQL queries: 18 out of 100][DML statements: 6 out of 150]
   -> Interview total INCLUDING what was already spent at start. Compare against the
      CUMULATIVE_LIMIT_USAGE block, not against zero.
```

Three readings that only this log gives you, and each is a decision:

- **`FLOW_START_INTERVIEW_LIMIT_USAGE` is not zero.** The gap between it and zero is your real
  headroom, and it is invisible in a clean sandbox.
- **`FLOW_BULK_ELEMENT_*` vs `FLOW_ELEMENT_*`.** An element that appears as a *bulk* element ran
  once for the whole batch; one that appears as a plain element ran per interview. That distinction
  is what makes "200 interviews" cost 1 SOQL rather than 200. Watch for
  `FLOW_BULK_ELEMENT_NOT_SUPPORTED`, which logs the "operation, element name, and entity name that
  doesn't support bulk operations" (`apexdev.txt` L38746–L38747) — that element is the per-interview
  one, and it is where the batch actually gets expensive.
- **The denominator on the finished line.** It tells you whether this interview was metered at the
  synchronous or asynchronous ceilings — the only way to settle the `AsyncAfterCommit` question
  marked UNVERIFIED in §3.

Reading a debug log in general — trace flags, retention, the non-limit flow events — belongs to
`flow/flow-debugging`. This section only covers the four limit-usage events.

### 7b. Assert the budget in an Apex test

The `FlowTest` in §4 proves correctness at bulk size 1. This proves the budget at 200. `Limits`
method names are from the Apex Reference Guide (`apexrefguide.txt` L220218–L220290).

```apex
@IsTest
private class FacilityAuditCloseOutBudgetTest {

    @IsTest
    static void closingTwoHundredAuditsStaysInsideBudget() {
        List<Facility_Audit__c> audits = new List<Facility_Audit__c>();
        for (Integer i = 0; i < 200; i++) {
            audits.add(new Facility_Audit__c(Name = 'Audit ' + i, Status__c = 'In_Review'));
        }
        insert audits;

        List<Audit_Finding__c> findings = new List<Audit_Finding__c>();
        for (Facility_Audit__c a : audits) {
            for (Integer j = 0; j < 6; j++) {
                findings.add(new Audit_Finding__c(
                    Facility_Audit__c = a.Id,
                    Finding_Code__c = 'F-' + j,
                    Severity__c = 'Critical'
                ));
            }
        }
        insert findings;

        for (Facility_Audit__c a : audits) {
            a.Status__c = 'Closed';
        }

        Test.startTest();
        update audits;
        Integer queries = Limits.getQueries();
        Integer dmlStatements = Limits.getDMLStatements();
        Integer dmlRows = Limits.getDMLRows();
        Integer cpuMs = Limits.getCpuTime();
        Test.stopTest();

        // 70% of each ceiling, so the assertion fails while there is still room to fix it.
        // Ceilings: apexdev.txt L19544 (100), L19554 (150), L19556 (10,000), L19579 (10,000 ms).
        Assert.isTrue(queries < 70,
            'SOQL budget: ' + queries + ' of ' + Limits.getLimitQueries());
        Assert.isTrue(dmlStatements < 105,
            'DML statement budget: ' + dmlStatements + ' of ' + Limits.getLimitDMLStatements());
        Assert.isTrue(dmlRows < 7000,
            'DML row budget: ' + dmlRows + ' of ' + Limits.getLimitDMLRows());
        Assert.isTrue(cpuMs < 7000,
            'CPU budget: ' + cpuMs + ' ms of ' + Limits.getLimitCpuTime());

        Assert.areEqual(
            1200,
            [SELECT COUNT() FROM Remediation_Task__c WHERE Facility_Audit__c IN :audits],
            'Expected one remediation task per critical finding.'
        );
    }
}
```

Two details that decide whether this test is worth anything:

- Use `Assert.isTrue` / `Assert.areEqual`. **There is no `System.assertTrue` method in Apex** —
  `grep -c "assertTrue" apexdev.txt apexrefguide.txt` returns 0 in both guides. The `Assert` class
  is at `apexrefguide.txt` L198622.
- Read the counters **before** `Test.stopTest()`. Limits "apply individually to each testMethod"
  (`apexdev.txt` L19660), and `Test.stopTest` resets the governor context — sampling afterwards
  measures nothing.

### 7c. Confirm what else shares the transaction

```sql
SELECT Id, ApiName, Label, ProcessType, TriggerType, TriggerObjectOrEventLabel, TriggerOrder, IsActive
FROM FlowDefinitionView
WHERE TriggerObjectOrEventLabel = 'Facility Audit'
  AND IsActive = true
ORDER BY TriggerOrder NULLS LAST
```

Every row is a co-tenant of the same meters. UNVERIFIED (2026-09-05): `FlowDefinitionView` and its
fields are documented in the Tooling/Object reference rather than in the extracts used here —
confirm the field list against your org's `sf sobject describe` before scripting on it. The checker
in `scripts/check_flow_governor_limits_deep_dive.py` answers the same question from the source tree,
with no org required, and it is the one to run in CI.
