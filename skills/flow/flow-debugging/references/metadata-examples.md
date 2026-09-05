# Metadata Examples — Flow Debugging

The artefacts this skill produces are not "a flow". They are the **capture rig** you put
around a flow that is already misbehaving, plus the flow that proves the rig works:

1. a record-triggered flow with a fault that only fires on some records (§1),
2. the annotated `FLOW_*` debug-log sequence that fault produces (§2),
3. the `DebugLevel` / `TraceFlag` pair that makes those lines appear at all (§3),
4. the SOQL that finds the interview after the log is gone (§4),
5. the `FlowTest` that reproduces the fault on demand (§5),
6. `package.xml`, deploy order and verification (§6–§8).

**Object model is `Inspection__c` → `Facility__c`,** plus the repo-canonical
`Application_Log__c` fault sink. Deliberately different from the models the neighbouring
flow packages use — `flow/flow-testing` (`Warranty_Claim__c`), `flow/fault-handling`
(`Payment__c`), `flow/flow-collection-processing` (`Order__c` / `Order_Line__c`) — so the
packages can be read side by side.

| Object | Field | Type | Why it matters here |
|---|---|---|---|
| `Inspection__c` | `Result__c` | Picklist: `Pass`, `Pass with Notes`, `Fail - Critical Safety Violation` | The longest value is 32 characters. |
| `Inspection__c` | `Facility__c` | Lookup(`Facility__c`) | The parent the flow writes to. |
| `Facility__c` | `Last_Inspection_Result__c` | Text(20) | **20 < 32.** The overflow is the deliberate fault. |
| `Application_Log__c` | `Message__c`, `Source__c`, `Severity__c`, `Related_Record_Id__c` | Text / Long Text | Durable fault sink. |

**Why this fault and not a missing required field.** A required-field fault is visible in
the flow XML — you can read the Update element and see the gap. A `STRING_TOO_LONG`
overflow is invisible in the XML, invisible in a debug run on a `Pass` record, and fires
only for the one picklist value nobody tested. That is the shape of failure this skill
exists to localise, and it is the shape a log excerpt actually earns its keep on.

---

## 1. `Inspection_AfterSave_StampFacilityResult.flow-meta.xml`

The flow under investigation, in its **fixed** form — the `recordUpdates` element carries a
`faultConnector`. The broken form this skill is called about is the same file with
`<faultConnector>` deleted from `Stamp_Facility_Result`; §2 shows that the log tells the
two apart by **event name**, before you ever open the flow.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Stamps Facility__c.Last_Inspection_Result__c from a completed inspection. Fault route logs to Application_Log__c. Covered by Inspection_Stamp_Fits_Short_Result and Inspection_Stamp_Overflows_On_Critical.</description>
    <environments>Default</environments>
    <interviewLabel>Inspection Stamp Facility Result {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Inspection After Save - Stamp Facility Result</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <status>Draft</status>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Get_Facility</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Result__c</field>
            <operator>IsNull</operator>
            <value>
                <booleanValue>false</booleanValue>
            </value>
        </filters>
        <object>Inspection__c</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <recordLookups>
        <name>Get_Facility</name>
        <label>Get Facility</label>
        <locationX>50</locationX>
        <locationY>120</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Stamp_Facility_Result</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Flow_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Facility__c</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <object>Facility__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Stamp_Facility_Result</name>
        <label>Stamp Facility Result</label>
        <locationX>50</locationX>
        <locationY>240</locationY>
        <faultConnector>
            <targetReference>Capture_Fault_Detail</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>Get_Facility.Id</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Last_Inspection_Result__c</field>
            <value>
                <elementReference>$Record.Result__c</elementReference>
            </value>
        </inputAssignments>
        <object>Facility__c</object>
    </recordUpdates>
    <assignments>
        <name>Capture_Fault_Detail</name>
        <label>Capture Fault Detail</label>
        <locationX>310</locationX>
        <locationY>240</locationY>
        <assignmentItems>
            <assignToReference>faultDetail</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Log_Flow_Fault</targetReference>
        </connector>
    </assignments>
    <recordCreates>
        <name>Log_Flow_Fault</name>
        <label>Log Flow Fault</label>
        <locationX>310</locationX>
        <locationY>360</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>faultDetail</elementReference>
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
                <stringValue>Inspection_AfterSave_StampFacilityResult.Stamp_Facility_Result</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <variables>
        <name>faultDetail</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

### How to read it

- **`<status>Draft</status>`** — `FlowVersionStatus` valid values are `Active`, `Draft`,
  `Obsolete`, `InvalidDraft`, `UnderReview`, and "in the UI, `Draft` appears as Inactive"
  (`api_meta.txt` L68416–L68424). Ship Draft; the `FlowTest` in §5 exists to run *before*
  activation.
- **`<interviewLabel>`** is not decoration. It is the "label for the interview… helps users
  and administrators differentiate interviews from the same flow… appears in the Paused
  Flow Interviews component on the user's Home tab and in the list of paused flow
  interviews in Setup" (`api_meta.txt` L68156–L68160). It is the same string that lands in
  `FlowInterview.InterviewLabel` (`object_reference.txt` L139951–L139955), which is the
  only human-readable handle you get in §4's SOQL. A flow with waits or scheduled paths and
  no `interviewLabel` produces a paused-interview list you cannot triage.
- **`<faultConnector>` on `recordLookups` and `recordUpdates`** — both types document the
  field: "specifies which node to execute if the attempt to get records results in an
  error" (`api_meta.txt` L71120) and "…if the attempt to update a record results in an
  error" (L71283). `recordCreates` documents it too (L70965); `Log_Flow_Fault` deliberately
  omits it because it *is* the fault sink. `flow/fault-handling` owns the design of that
  route and its checker enforces the deeper version of this rule; this package only needs
  the connector to exist so §2's log shows `FLOW_ELEMENT_FAULT` rather than
  `FLOW_ELEMENT_ERROR`.
- **`<triggerType>RecordAfterSave</triggerType>`** — "the flow starts after a record is
  saved… available in API version 49.0 and later" (`api_meta.txt` L72524–L72525).
  **UNVERIFIED (2026-09-05): `api_meta.txt` L72458–L72459 says `recordTriggerType` is
  "available only when `triggerType` is `RecordBeforeSave` or `DataCloudDataChange`", yet
  every after-save flow Flow Builder emits carries both.** `flow/record-triggered-flow-patterns`
  owns that discrepancy — read it before arguing about the pairing; retrieve a working
  after-save flow from the target org and match its shape rather than trusting either
  reading.
- **`$Flow.FaultMessage`** — **UNVERIFIED (2026-09-05): the string `FaultMessage` does not
  appear anywhere in `api_meta.txt`, `apexdev.txt` or `object_reference.txt`.** The global
  is documented only on help.salesforce.com, which cannot be fetched. `flow/fault-handling`
  treats it as the canonical fault-capture reference across the repo; this package uses it
  the same way, but the claim rests on that skill and on field observation, not on the
  Metadata API guide.

---

## 2. The debug log for that fault, annotated

This is the artefact the method actually turns on. Every event name and every "fields
logged" phrase below is quoted from the Apex Developer Guide's debug event table; the
**Level** column is the guide's minimum `Workflow` category level for that event.

| # | Event | Fields the guide says it logs | Workflow level | Guide line |
|---|---|---|---|---|
| 1 | `FLOW_START_INTERVIEWS_BEGIN` | Requests | INFO+ | `apexdev.txt` L38856 |
| 2 | `FLOW_CREATE_INTERVIEW_BEGIN` | Organization ID, definition ID, and version ID | INFO+ | L38759 |
| 3 | `FLOW_CREATE_INTERVIEW_END` | Interview ID and flow name | INFO+ | L38762 |
| 4 | `FLOW_START_INTERVIEW_BEGIN` | Interview ID and flow name | INFO+ | L38850 |
| 5 | `FLOW_START_INTERVIEW_LIMIT_USAGE` | Usage toward a limit at the interview's start time | FINER+ | L38874 |
| 6 | `FLOW_BULK_ELEMENT_BEGIN` | Interview ID and element type | FINE+ | L38721 |
| 7 | `FLOW_ELEMENT_BEGIN` | Interview ID, element type, and element name | FINE+ | L38768 |
| 8 | `FLOW_ELEMENT_LIMIT_USAGE` | Incremented usage toward a limit for this element | FINER+ | L38795 |
| 9 | `FLOW_ELEMENT_END` | Interview ID, element type, and element name | FINE+ | L38774 |
| 10 | `FLOW_VALUE_ASSIGNMENT` | Interview ID, key, and value | FINER+ | L38896 |
| 11 | `FLOW_ELEMENT_FAULT` | Message, element type, and element name (fault path taken) | **WARNING+** | L38792 |
| 12 | `FLOW_ELEMENT_ERROR` | Message, element type, and element name (flow runtime exception) | ERROR+ | L38777 |
| 13 | `FLOW_BULK_ELEMENT_DETAIL` | Interview ID, element type, element name, number of records | FINER+ | L38724 |
| 14 | `FLOW_BULK_ELEMENT_END` | Interview ID, element type, element name, number of records, and execution time | FINE+ | L38727 |
| 15 | `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` | Usage toward a limit when the interview finishes | FINER+ | L38821 |
| 16 | `FLOW_START_INTERVIEWS_END` | Requests | INFO+ | L38859 |

**The one distinction the whole method turns on.** Line 11 and line 12 are the same
failure seen from two different flow designs:

- `FLOW_ELEMENT_FAULT` — "fault path taken" (L38792). The element failed and the
  `faultConnector` caught it. The transaction continues.
- `FLOW_ELEMENT_ERROR` — "flow runtime exception" (L38777). Nothing caught it.

`FLOW_ELEMENT_FAULT` logs at **WARNING and above** while `FLOW_ELEMENT_ERROR` logs at
**ERROR and above**. The level list runs "from lowest to highest… NONE, ERROR, WARN, INFO,
DEBUG, FINE, FINER, FINEST" and "the level is cumulative" (`apexdev.txt` L38389–L38403).
So `Workflow` set to `ERROR` — the level an admin reaches for when hunting an error —
captures `FLOW_ELEMENT_ERROR` and **silently drops every `FLOW_ELEMENT_FAULT`**. A
well-built flow with fault paths everywhere logs *nothing* at `Workflow=ERROR`. This is the
single most common way a flow-debugging session ends in "the log is empty, so it isn't the
flow." `flow/flow-testing` documents the same trap from the test-coverage side.

### Annotated excerpt

```text
FLOW_START_INTERVIEWS_BEGIN            1                    <- one entry for the whole DML,
                                                               not one per record (L38856)
FLOW_CREATE_INTERVIEW_BEGIN            00D.../300.../301...
FLOW_CREATE_INTERVIEW_END              Inspection After Save - Stamp Facility Result
FLOW_START_INTERVIEW_BEGIN             Inspection After Save - Stamp Facility Result
FLOW_START_INTERVIEW_LIMIT_USAGE       SOQL queries: 0 out of 100
FLOW_BULK_ELEMENT_BEGIN                recordLookup       <- the interview is bulkified here
FLOW_ELEMENT_BEGIN                     recordLookup  Get_Facility
FLOW_ELEMENT_LIMIT_USAGE               SOQL queries: 1 out of 100
FLOW_ELEMENT_END                       recordLookup  Get_Facility
FLOW_BULK_ELEMENT_DETAIL               recordLookup  Get_Facility  1 record
FLOW_BULK_ELEMENT_END                  recordLookup  Get_Facility  1 record
FLOW_ELEMENT_BEGIN                     recordUpdate  Stamp_Facility_Result
FLOW_ELEMENT_LIMIT_USAGE               DML statements: 1 out of 150
FLOW_ELEMENT_FAULT                     Stamp_Facility_Result: The flow tried to update
                                       these records: ... STRING_TOO_LONG:
                                       Last Inspection Result: data value too large:
                                       Fail - Critical Safety Violation (max length=20)
                                                          <- LOCALISED. Element + reason.
FLOW_ELEMENT_BEGIN                     assignment    Capture_Fault_Detail
FLOW_VALUE_ASSIGNMENT                  faultDetail = "STRING_TOO_LONG: ..."
                                                          <- proves FaultMessage was populated
FLOW_ELEMENT_END                       assignment    Capture_Fault_Detail
FLOW_ELEMENT_BEGIN                     recordCreate  Log_Flow_Fault
FLOW_ELEMENT_LIMIT_USAGE               DML statements: 2 out of 150
FLOW_ELEMENT_END                       recordCreate  Log_Flow_Fault
FLOW_INTERVIEW_FINISHED_LIMIT_USAGE    DML statements: 2 out of 150
FLOW_START_INTERVIEWS_END              1
```

**UNVERIFIED (2026-09-05): the literal column layout above is constructed, not quoted.**
`apexdev.txt` shows a pipe-delimited log line only for `CODE_UNIT_STARTED` (L38186–L38188)
and describes the general `timestamp | event identifier` format (L38423–L38434); its
`FLOW_*` table gives the *fields logged* (columns quoted verbatim in the table above) but
never their formatting or ordering on the line. **Match on the event name and on the field
values, never on a column position** — and never write a log parser that splits on a fixed
index. `FLOW_ELEMENT_FAULT`'s message text (`STRING_TOO_LONG: … max length=20`) is the
platform's DML error string surfaced into the flow, not a quoted example from the guide.

**Reading order when you have the log.** Localise before you theorise:

1. `FLOW_START_INTERVIEWS_BEGIN` present? No → the flow never started. Stop reading the log;
   the problem is entry criteria, active version, or `triggerType`. Go to §4.
2. `FLOW_ELEMENT_FAULT` **or** `FLOW_ELEMENT_ERROR` present? The element name on that line
   is the answer. Everything before it ran.
3. Neither, but `FLOW_START_INTERVIEW_END` present? The flow ran to completion and did the
   wrong thing. Read `FLOW_VALUE_ASSIGNMENT` (L38896) and `FLOW_RULE_DETAIL` — "interview
   ID, rule name, and result" (L38847) — to find the branch that went the wrong way.
4. `FLOW_*_LIMIT_USAGE` climbing toward a ceiling? It is a bulkification problem, not a
   logic problem. Each of these events "displays the usage for one of these limits: SOQL
   queries, SOQL query rows, SOSL queries, DML statements, DML rows, CPU time in ms, heap
   size in bytes, callouts, email invocations, future calls, jobs in queue, push
   notifications" (L38795–L38808). Hand off to `flow/flow-bulkification`.
5. `FLOW_LOOP_DETAIL` — "interview ID, index, and value… the index is the position in the
   collection variable for the item that the loop is operating on" (L38843–L38846) —
   repeating with a `FLOW_ELEMENT_BEGIN` for a `recordLookup` between each index is a Get
   Records inside a loop.

---

## 3. Turning the events on: `DebugLevel` + `TraceFlag`

**These are Tooling API objects, not Metadata API types.** Trace flags are set "in the
Developer Console or in Setup or by using the `TraceFlag` and `DebugLevel` Tooling API
objects" (`apexdev.txt` L39543–L39546) — they have no Metadata API type and therefore
**cannot appear in `package.xml`**. `apex/debug-and-logging` owns the mechanics of trace
flags, log retention and the `ApexLog` queries; this section is only the flow-shaped
configuration of them.

```json
{
  "DebugLevel": {
    "DeveloperName": "Flow_Debugging_Workflow_Finer",
    "MasterLabel": "Flow Debugging - Workflow FINER",
    "ApexCode": "NONE",
    "ApexProfiling": "NONE",
    "Callout": "NONE",
    "Database": "NONE",
    "System": "NONE",
    "Validation": "INFO",
    "Visualforce": "NONE",
    "Workflow": "FINER"
  },
  "TraceFlag": {
    "TracedEntityId": "<User Id of the user who will save the Inspection__c record>",
    "DebugLevelId": "<Id returned by the DebugLevel insert>",
    "LogType": "USER_DEBUG",
    "StartDate": "2026-09-05T09:00:00.000+0000",
    "ExpirationDate": "2026-09-05T10:00:00.000+0000"
  }
}
```

**Why `Workflow` = `FINER` and every other category `NONE`.**

| You set `Workflow` to | You get | You lose |
|---|---|---|
| `ERROR` | `FLOW_ELEMENT_ERROR`, `FLOW_CREATE_INTERVIEW_ERROR`, `FLOW_START_INTERVIEWS_ERROR` | **`FLOW_ELEMENT_FAULT`** (WARNING+), every element boundary, every value |
| `WARN` | adds `FLOW_ELEMENT_FAULT` | element boundaries, values, limit usage |
| `INFO` | adds interview start/end/pause/resume, `FLOW_START_SCHEDULED_RECORDS` | **element boundaries and values** |
| `FINE` | adds `FLOW_ELEMENT_BEGIN` / `_END`, `FLOW_ELEMENT_DEFERRED`, `FLOW_BULK_ELEMENT_BEGIN` / `_END` | values, rule results, limit usage, loop indices, subflow detail |
| `FINER` | adds `FLOW_VALUE_ASSIGNMENT`, `FLOW_RULE_DETAIL`, `FLOW_LOOP_DETAIL`, `FLOW_SUBFLOW_DETAIL`, `FLOW_ACTIONCALL_DETAIL`, `FLOW_ASSIGNMENT_DETAIL`, all `*_LIMIT_USAGE`, all `FLOW_WAIT_*` | nothing this skill needs |

Every row is the guide's own "Level Logged" column for those events (`apexdev.txt`
L38714–L38911). `FINER` is the floor for a real flow-debugging session; `FINEST` buys
nothing extra for the `Workflow` category and costs log size.

**Two traps in that JSON that will cost you the capture.**

1. **The default is `INFO`, and `INFO` is not enough.** With no active trace flag the
   defaults are "DB: INFO, APEX_CODE: DEBUG, APEX_PROFILING: INFO, **WORKFLOW: INFO**,
   VALIDATION: INFO, CALLOUT: INFO, VISUALFORCE: INFO, SYSTEM: DEBUG" (`apexdev.txt`
   L39553–L39560). At `WORKFLOW,INFO` you see the interview start and end and *no elements
   at all*. Confirm what you actually got from the log header, which carries "the log
   category and level used to generate the log" as a semicolon-delimited string, e.g.
   `…;VALIDATION,INFO;VISUALFORCE,INFO;WORKFLOW,INFO` (L38147–L38149). If that header says
   `WORKFLOW,INFO`, your trace flag did not win — re-read the order of precedence
   (L39542–L39546), where "trace flags override all other logging logic".
2. **Setting the other categories to `NONE` is a truncation defence, not tidiness.** "Each
   debug log must be 20 MB or smaller. Debug logs that are larger than 20 MB are reduced in
   size by removing older log lines… **The log lines can be removed from any location, not
   just the start of the debug log**" (`apexdev.txt` L38115–L38118). A truncated log does
   not announce itself as truncated at the point of loss: your `FLOW_ELEMENT_BEGIN` can
   vanish from the middle while the `FLOW_ELEMENT_FAULT` survives, or the reverse. If
   `Apex Code` is at `DEBUG` (its default) on a trigger-heavy object, Apex lines can crowd
   out the flow lines you came for.

Capture and read the log:

```bash
# List recent logs for the traced user, then pull one.
sf apex log list --target-org my-sandbox
sf apex log get --log-id <18-char ApexLog Id> --target-org my-sandbox > inspection-flow.log

# Localise: the two lines that name the failing element.
grep -nE 'FLOW_ELEMENT_(FAULT|ERROR)' inspection-flow.log

# Sequence: element boundaries in order, with nothing else.
grep -nE 'FLOW_(ELEMENT|BULK_ELEMENT)_(BEGIN|END)' inspection-flow.log

# Wrong-branch hunting: which rules evaluated to what.
grep -n 'FLOW_RULE_DETAIL' inspection-flow.log

# Limit pressure, highest first.
grep -n '_LIMIT_USAGE' inspection-flow.log | tail -20
```

**UNVERIFIED (2026-09-05): the `sf apex log list` / `sf apex log get` flags above are not
documented in any guide in the grounding corpus** — the corpus names only `sf flow run
test` (`apexrefguide.txt` L158186). Run `sf apex log get --help` before scripting them. The
`ApexLog` object those commands read *is* documented, and §4 queries it directly.

---

## 4. Finding the run after the log is gone

Debug logs expire fast, and the two Salesforce log surfaces named "flow" cover far less
than their names suggest. Query in this order.

### 4a. Did a log survive at all?

`ApexLog.Location` is a restricted picklist: "`Monitoring` — Log is generated as part of
debug log monitoring. These types of logs are maintained for **seven days** or until a user
deletes them" and "`SystemLog` — Log is generated from the Developer Console. These types
of logs are maintained for **24 hours** or until the user clears them"
(`object_reference.txt` L31308–L31311; the same split is stated at `apexdev.txt` L38118).

```soql
SELECT Id, LogUserId, Operation, Location, Status, LogLength, DurationMilliseconds, StartTime
FROM ApexLog
WHERE StartTime = LAST_N_DAYS:7
ORDER BY StartTime DESC
```

A `LogLength` at or near 20,971,520 is the truncation ceiling from §3 — treat that log as
incomplete regardless of what it appears to show.

### 4b. Paused and errored interviews — `FlowInterview`

`FlowInterview` "represents a flow interview. A flow interview is a running instance of a
flow" (`object_reference.txt` L139861). This is the object behind the paused-interviews
list, and it is **not** the "Flow Interview Log".

```soql
SELECT Id, Name, InterviewLabel, CurrentElement, InterviewStatus, Error,
       Guid, PauseLabel, WasPausedFromScreen, OwnerId, CreatedDate
FROM FlowInterview
WHERE InterviewStatus IN ('Paused', 'Error', 'VersionPaused')
ORDER BY CreatedDate DESC
```

| Field | What the guide says | Line |
|---|---|---|
| `CurrentElement` | "The flow element at which the interview is paused." | L139891 |
| `Error` | "The error message that explains why the flow interview failed. This field is available in API version 62.0 and later." | L139912–L139913 |
| `InterviewLabel` | "Label for the interview. This label helps users and administrators differentiate interviews from the same flow." | L139951–L139952 |
| `InterviewStatus` | `Completed`, `Error`, `Paused`, `Running`, `VersionPaused` (`VersionPaused` = API 60.0+) | L139961–L139975 |
| `Guid` | "Globally unique identifier for the interview." | L139944 |

Two things this buys you that nothing else does. **`Error` is queryable** — for API 62.0
and later you can find failed interviews without an email and without a log.
And **`CurrentElement` localises a paused interview to an element** for free.

`FlowRecordRelation` ties a paused interview back to a record: it "represents a
relationship between a record and a flow interview. When a flow interview is paused,
Salesforce uses the `$Flow.CurrentRecord` global variable in the flow to associate the
interview with a record" (`object_reference.txt` L143527–L143529), with `ParentId` →
`FlowInterview` and `RelatedRecordId` → the record (L143555, L143569).

```soql
SELECT Id, ParentId, Parent.InterviewLabel, Parent.CurrentElement, RelatedRecordId
FROM FlowRecordRelation
WHERE Parent.InterviewStatus = 'Paused'
```

Deleting a flow interview needs the "Manage Flow" user permission; "all other calls require
the 'Run Flows' user permission or the Flow User field enabled on the user detail page"
(`object_reference.txt` L139869–L139872).

### 4c. `FlowInterviewLog` is screen-flow only

This is the correction that saves the most wasted time in this skill. `FlowInterviewLog`
"represents the logs of a **screen flow** interview" (`object_reference.txt` L140059–L140060)
and `FlowInterviewLogEntry` "represents the log of a specific element that's executed by a
**screen flow** interview" (L140207–L140208). A record-triggered flow leaves **nothing**
here. Pointing a record-triggered-flow investigation at this object returns zero rows and
is routinely misread as "the flow never ran".

```soql
SELECT Id, FlowDeveloperName, FlowLabel, FlowVersionNumber, FlowInterviewGuid,
       InterviewStatus, InterviewStartTimestamp, InterviewEndTimestamp,
       InterviewDurationInMinutes
FROM FlowInterviewLog
WHERE InterviewStatus = 'Error'
ORDER BY InterviewStartTimestamp DESC
```

```soql
SELECT Id, ElementApiName, ElementLabel, LogEntryType, LogEntryTimestamp,
       ElementDurationInMinutes, DurationSinceStartInMinutes
FROM FlowInterviewLogEntry
WHERE FlowInterviewLogId = '<Id from the query above>'
ORDER BY LogEntryTimestamp
```

`LogEntryType` is a restricted picklist: `Error`, `FlowFinish-Finished Flow`,
`FlowPause-Paused Flow`, `FlowResume-Resumed Flow`, `FlowStart-Started Flow`,
`ScreenFinish-Clicked Finish`, `ScreenNext-Clicked Next`, `ScreenPrevious-Clicked Previous`
(`object_reference.txt` L140294–L140301). `InterviewStatus` on the log adds `Autosaved` and
`Expired` over the interview object's list, both API 62.0 and later (L140157–L140166).
"By default, only users with the View All Data permission can access the logs for flows
that are run by other users" (L140068–L140070) — a delegated admin querying this and
getting nothing may be hitting that, not an absent log.

No retention period for `FlowInterviewLog` is stated anywhere in the Object Reference.
See the retention gotcha in `references/gotchas.md`.

### 4d. `FlowExecutionErrorEvent` — state the negative

**UNVERIFIED (2026-09-05): `FlowExecutionErrorEvent` appears nowhere in
`object_reference.txt`, `api_meta.txt`, `apexdev.txt` or `api_rest.txt`.** Neither its
existence nor any field name — `ErrorId`, `ElementApiName`, `FlowVersionNumber`,
`InterviewGuid`, `ContextRecordId`, `UserId` — can be confirmed from the grounding corpus.
Do not write a subscriber against a field list taken from this file or from an LLM. Confirm
the object and its exact fields first:

```bash
sf sobject describe --sobject FlowExecutionErrorEvent --target-org my-sandbox
sf data query --query "SELECT QualifiedApiName FROM EntityDefinition WHERE QualifiedApiName LIKE 'Flow%Event'" --use-tooling-api --target-org my-sandbox
```

If the describe succeeds, the subscriber shape is the ordinary platform-event trigger — and
the *design* of that alerting path (routing, thresholds, trend detection, the central log
object) belongs to `flow/flow-error-monitoring`, not here:

```apex
// SHAPE ONLY. Field names below are unconfirmed - replace each with a name the
// describe above actually returned before deploying this.
trigger FlowExecutionErrorEventTrigger on FlowExecutionErrorEvent (after insert) {
    List<Application_Log__c> logs = new List<Application_Log__c>();
    for (FlowExecutionErrorEvent evt : Trigger.new) {
        logs.add(new Application_Log__c(
            Source__c   = 'FlowExecutionErrorEvent',
            Severity__c = 'Error',
            Message__c  = JSON.serialize(evt)   // serialize whole event: no field guessing
        ));
    }
    if (!logs.isEmpty()) {
        insert logs;
    }
}
```

Serializing the whole event is the deliberate choice while the field list is unconfirmed:
it cannot fail to compile on a field that does not exist, and the first delivered event
tells you the real shape.

### 4e. Who got the fault email, and why it was not you

`enableFlowUseApexExceptionEmail` "indicates whether process and flow error emails are sent
to: the user who last modified the process or flow (`false`), the addresses set on the Apex
Exception Email page in Setup (`true`). **By default, the value is `false`.** Corresponds
to the *Send Process or Flow Error Email to* field on the Process Automation Settings page
in Setup" (`api_meta.txt` L116961–L116967).

So on a default org the fault email goes to **whoever last saved the flow** — frequently a
departed consultant or a sandbox-only admin — not to an ops inbox. `flow/flow-governance`
owns `Flow.settings` and the org-wide decision; check it here only to explain a missing
email:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableFlowUseApexExceptionEmail>true</enableFlowUseApexExceptionEmail>
</FlowSettings>
```

---

## 5. Proving the fix: `FlowTest`

"Before you activate a record-triggered, autolaunched, or Data Cloud-triggered flow, you
can test it to verify its expected results and identify flow run-time failures"
(`api_meta.txt` L73961–L73962). Components carry the `.flowtest` suffix and live in the
`flowtests` folder; the type is available in API version 55.0 and later (L73976–L73980).
`flow/flow-testing` owns test strategy and path matrices — this skill needs exactly two
tests: one that reproduces the fault, one that proves the fix.

### 5a. Reproduce the fault

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <flowApiName>Inspection_AfterSave_StampFacilityResult</flowApiName>
    <label>Stamp overflows on critical result</label>
    <description>Reproduces the STRING_TOO_LONG fault: Result__c value is 32 characters, Facility__c.Last_Inspection_Result__c is Text(20).</description>
    <testType>WithAssertion</testType>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Result__c&quot;:&quot;Pass&quot;}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Result__c&quot;:&quot;Fail - Critical Safety Violation&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <elementApiName>Finish</elementApiName>
        <assertions>
            <conditions>
                <leftValueReference>$Record</leftValueReference>
                <operator>HasError</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>Expected the Facility stamp to fault on a 32-character result. If this assertion fails, the overflow has been fixed or the field was widened - retire this test rather than editing it.</errorMessage>
        </assertions>
    </testPoints>
</FlowTest>
```

### 5b. Prove the fix

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <flowApiName>Inspection_AfterSave_StampFacilityResult</flowApiName>
    <label>Stamp fits short result</label>
    <description>Happy path: a 4-character result stamps cleanly and no fault route is taken.</description>
    <testType>WithAssertion</testType>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Result__c&quot;:null}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Result__c&quot;:&quot;Pass&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <elementApiName>Finish</elementApiName>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Result__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Pass</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>Triggering record was not the one the test set up.</errorMessage>
        </assertions>
    </testPoints>
</FlowTest>
```

### How to read them

- **`<testType>WithAssertion</testType>`** is `Required` and its only documented value is
  `WithAssertion` — "specifies whether the test contains assertions. This field is available
  in API version 66.0 and later" (`api_meta.txt` L74041–L74050). Below API 66.0 omit it.
- **`elementApiName` on a test point takes exactly two values**, `Start` and `Finish`
  (`api_meta.txt` L74139–L74147). You cannot assert at `Stamp_Facility_Result`. This is why
  §2's log is not optional: `FlowTest` tells you *that* the flow errored, the log tells you
  *where*.
- **`HasError`** is a `FlowComparisonOperator` value "available in API version 64.0 and
  later" (`api_meta.txt` L74203). It is the operator that lets a test assert a failure
  instead of only a success. **UNVERIFIED (2026-09-05): the guide lists `HasError` among
  the operators but never states which `leftValueReference` it applies to, nor what
  `rightValue` it expects.** `$Record` / `booleanValue` `true` above is the shape that
  matches the surrounding operators; build this test in Flow Builder once and retrieve it
  before trusting the hand-written form. `flow/fault-handling` names the same operator in
  its trigger list and is the other place in the repo this shape appears.
- **`InputTriggeringRecordInitial` / `InputTriggeringRecordUpdated`** — "when `type` is
  `InputTriggeringRecordInitial` or `InputTriggeringRecordUpdated`, the value for
  `leftValueReference` must be `$Record`" (`api_meta.txt` L74305–L74308). Supplying both is
  what makes the test an *update*; supplying only the updated one is a create.
- **Screen flows get none of this.** The FlowTest sentence quoted above lists
  record-triggered, autolaunched and Data Cloud-triggered flows only. For a screen flow the
  reproduction path is §4c's `FlowInterviewLogEntry` plus an Apex `Flow.Interview` driver —
  `flow/flow-testing` §5 owns that driver.

---

## 6. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Inspection__c</members>
        <members>Facility__c</members>
        <members>Application_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Inspection_AfterSave_StampFacilityResult</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Inspection_Stamp_Overflows_On_Critical</members>
        <members>Inspection_Stamp_Fits_Short_Result</members>
        <name>FlowTest</name>
    </types>
    <types>
        <members>Flow</members>
        <name>Settings</name>
    </types>
    <version>66.0</version>
</Package>
```

`FlowTest` members are component full names, not labels: the `<label>` is
`Stamp overflows on critical result`; the member and the file name are
`Inspection_Stamp_Overflows_On_Critical`. **`DebugLevel` and `TraceFlag` from §3 are absent
by necessity** — they are Tooling API objects with no Metadata API type
(`apexdev.txt` L39543–L39546). A manifest that names them fails.

## 7. Deploy order

```bash
# 0. Lint before anything reaches an org. Exits 1 if --manifest-dir does not exist.
python3 skills/flow/flow-debugging/scripts/check_flow_debugging.py \
  --manifest-dir force-app/main/default

# 1. Objects and fields first. A FlowTest whose sobjectValue names a field that does not
#    exist deploys clean and fails at run time.
sf project deploy start --source-dir force-app/main/default/objects --target-org my-sandbox

# 2. The flow, still Draft. FlowTest exists to run before activation.
sf project deploy start --source-dir force-app/main/default/flows --target-org my-sandbox

# 3. FlowTests. flowApiName is a Required reference to a flow that must already exist
#    (api_meta.txt L73994-L73998); components use the .flowtest suffix in flowtests/
#    (api_meta.txt L73976).
sf project deploy start --source-dir force-app/main/default/flowtests --target-org my-sandbox

# 4. Flow.settings LAST and only deliberately - it is org-wide. flow/flow-governance owns
#    this decision; deploying it to fix one missing fault email changes every flow's
#    error-email recipient (api_meta.txt L116961-L116967).
sf project deploy start --source-dir force-app/main/default/settings --target-org my-sandbox

# 5. Trace flags are NOT deployable. Create them through the Tooling API with the §3 bodies.
sf data create record --sobject DebugLevel --use-tooling-api \
  --values "DeveloperName=Flow_Debugging_Workflow_Finer MasterLabel='Flow Debugging - Workflow FINER' Workflow=FINER ApexCode=NONE ApexProfiling=NONE Callout=NONE Database=NONE System=NONE Validation=INFO Visualforce=NONE" \
  --target-org my-sandbox
```

**UNVERIFIED (2026-09-05): the `sf data create record --use-tooling-api` invocation above
is not documented in the grounding corpus.** Only the fact that `DebugLevel` and
`TraceFlag` are Tooling API objects is grounded (`apexdev.txt` L39543–L39546). Confirm the
flag spelling with `sf data create record --help`, or create the pair in Setup, before
scripting it.

## 8. Verification

**1. The capture is live and at the right level.** Reproduce the failing save, pull the
log, and read the header first — it carries "the log category and level used to generate
the log" (`apexdev.txt` L38143–L38149):

```bash
head -3 inspection-flow.log       # expect ...;WORKFLOW,FINER  -- not WORKFLOW,INFO
grep -c 'FLOW_ELEMENT_BEGIN' inspection-flow.log   # 0 here means the level did not apply
```

**2. The fault is localised to an element.**

```bash
grep -E 'FLOW_ELEMENT_(FAULT|ERROR)' inspection-flow.log
```

Exactly one line, naming `Stamp_Facility_Result`. `FLOW_ELEMENT_FAULT` means the fault
route fired; `FLOW_ELEMENT_ERROR` means it did not exist and the transaction rolled back.

**3. The fault route actually wrote.**

```soql
SELECT Id, Source__c, Severity__c, Related_Record_Id__c, Message__c, CreatedDate
FROM Application_Log__c
WHERE Source__c = 'Inspection_AfterSave_StampFacilityResult.Stamp_Facility_Result'
  AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

A `FLOW_ELEMENT_FAULT` in the log with no row here means the fault path ran and its own
`recordCreates` failed — check `flow/fault-handling` for rollback scope.

**4. The reproduction is repeatable without the log.**

```bash
sf flow run test --target-org my-sandbox
```

`Inspection_Stamp_Overflows_On_Critical` must fail before the fix and pass after the field
is widened or the assignment truncated. **UNVERIFIED (2026-09-05): the corpus names
`sf flow run test` (`apexrefguide.txt` L158186) but documents none of its flags or exit
codes** — "for more details about the command, use the Salesforce CLI `--help` flag"
(L158186–L158187). Check the observed exit code before gating CI on it.

**5. Turn the trace flag off.** Leaving it on is not free: "if you generate more than 1,000
MB of debug logs in a 15-minute window, your trace flags are disabled" and "when your org
accumulates more than 1,000 MB of debug logs, we prevent users in the org from adding or
editing trace flags" (`apexdev.txt` L38119–L38126). A forgotten trace flag on a busy
integration user is how the *next* investigation finds it cannot create a trace flag at all.
