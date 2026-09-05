# Metadata Examples — Flow Error Monitoring

Everything here is a deployable artifact. Line citations point at the extracted Summer '26
guides: `api_meta.txt` (Metadata API Developer Guide,
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf),
`object_reference.txt` (Object Reference,
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf),
`apexdev.txt` (Apex Developer Guide,
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf).

## 0. The object model, and what it is deliberately doing wrong

Object model is `Meter_Reading__c` → `Service_Point__c`, plus the repo-canonical
`Application_Log__c` sink from `templates/apex/custom_objects/`. Deliberately different from
the models the neighbouring flow packages use — `flow/flow-debugging` (`Inspection__c` /
`Facility__c`), `flow/fault-handling` (`Payment__c` / `Invoice__c`), `flow/flow-testing`
(`Warranty_Claim__c`), `flow/flow-collection-processing` (`Freight_Quote__c` /
`Quote_Leg__c`) — so an agent reading two packages side by side cannot cross-wire them.

| Object | Field | Type | Role in the example |
|---|---|---|---|
| `Meter_Reading__c` | `Status__c` | Picklist: `Pending`, `Validated`, `Billed` | Entry criterion for the flow. |
| `Meter_Reading__c` | `Reading_Value__c` | Number(12,2) | Stamped onto the parent. |
| `Meter_Reading__c` | `Read_Date__c` | Date | `recordField` for the scheduled path. |
| `Meter_Reading__c` | `Service_Point__c` | Lookup(`Service_Point__c`) | The parent the flow writes to — **nullable, which is the fault**. |
| `Service_Point__c` | `Last_Reading_Value__c` | Number(12,2) | Stamp target. |
| `Service_Point__c` | `Last_Read_Status__c` | Text(10) | Stamp target. |
| `Application_Log__c` | `Source__c`, `Message__c`, `Severity__c`, `Request_Id__c`, `Running_User__c` | ships in `templates/apex/custom_objects/` | The one sink. |
| `Application_Log__c` | `Flow_Element__c`, `Related_Record_Id__c` | **additive — §2 below** | The two fields the shared template does not yet carry. |

The seeded failure is a null `Service_Point__c`: the Update Records element filters on
`Id EqualTo $Record.Service_Point__c`, finds nothing to update, and the element faults. That
is a realistic monitoring case rather than a contrived one — it fails on *some* records and
not others, so it is invisible without a log row.

---

## 1. `MeterReading_AfterSave_StampServicePoint.flow-meta.xml`

Every fault-capable element carries a `faultConnector` and every fault route ends at one
`recordCreates` on `Application_Log__c`. That convention — not the flow's business logic —
is what this skill is asking you to standardise across the portfolio.

Element and enum names come from the guide's `Flow` section: `faultConnector` on
`FlowRecordUpdate` (`api_meta.txt` L71283), on `FlowRecordCreate` (L70965) and on
`FlowActionCall` (L68476); `interviewLabel` (L68156); `scheduledPaths` on `FlowStart`
(L72465) with the `FlowScheduledPath` fields at L71389–L71425; `emailSimple` as an
`InvocableActionType` (L68731); `FlowFormula` `dataType` / `expression` (L70596) with the
`{!…}` merge form shown in the guide's own flow sample at L73377.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <description>Stamps Service_Point__c from a validated meter reading. Every fault-capable element routes to Application_Log__c. Covered by MeterReading_Stamp_Succeeds and MeterReading_Stamp_Faults_When_Orphaned.</description>
    <environments>Default</environments>
    <formulas>
        <name>Ops_Alert_Body</name>
        <dataType>String</dataType>
        <expression>&quot;Meter reading &quot; &amp; {!$Record.Id} &amp; &quot; was still not billed 24h after the read date.&quot;</expression>
    </formulas>
    <interviewLabel>Meter Reading Stamp {!$Record.Id} {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Meter Reading After Save Stamp Service Point</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Stamp_Service_Point</targetReference>
        </connector>
        <object>Meter_Reading__c</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Validated</stringValue>
            </value>
        </filters>
        <scheduledPaths>
            <name>Recheck_24h_After_Read</name>
            <label>Recheck 24h After Read</label>
            <connector>
                <targetReference>Notify_Ops_Of_Unbilled_Read</targetReference>
            </connector>
            <offsetNumber>1</offsetNumber>
            <offsetUnit>Days</offsetUnit>
            <recordField>Read_Date__c</recordField>
            <timeSource>RecordField</timeSource>
        </scheduledPaths>
    </start>
    <status>Draft</status>
    <recordUpdates>
        <name>Stamp_Service_Point</name>
        <label>Stamp Service Point</label>
        <locationX>50</locationX>
        <locationY>160</locationY>
        <faultConnector>
            <targetReference>Log_Flow_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Service_Point__c</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Last_Read_Status__c</field>
            <value>
                <elementReference>$Record.Status__c</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Last_Reading_Value__c</field>
            <value>
                <elementReference>$Record.Reading_Value__c</elementReference>
            </value>
        </inputAssignments>
        <object>Service_Point__c</object>
    </recordUpdates>
    <actionCalls>
        <name>Notify_Ops_Of_Unbilled_Read</name>
        <label>Notify Ops Of Unbilled Read</label>
        <locationX>320</locationX>
        <locationY>160</locationY>
        <actionName>emailSimple</actionName>
        <actionType>emailSimple</actionType>
        <faultConnector>
            <targetReference>Log_Flow_Fault</targetReference>
        </faultConnector>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>emailAddresses</name>
            <value>
                <stringValue>flow-ops@example.com</stringValue>
            </value>
        </inputParameters>
        <inputParameters>
            <name>emailSubject</name>
            <value>
                <stringValue>Unbilled meter reading 24h after read date</stringValue>
            </value>
        </inputParameters>
        <inputParameters>
            <name>emailBody</name>
            <value>
                <elementReference>Ops_Alert_Body</elementReference>
            </value>
        </inputParameters>
    </actionCalls>
    <recordCreates>
        <name>Log_Flow_Fault</name>
        <label>Log Flow Fault</label>
        <locationX>50</locationX>
        <locationY>320</locationY>
        <inputAssignments>
            <field>Flow_Element__c</field>
            <value>
                <stringValue>Stamp_Service_Point or Notify_Ops_Of_Unbilled_Read</stringValue>
            </value>
        </inputAssignments>
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
            <field>Request_Id__c</field>
            <value>
                <elementReference>$Flow.InterviewGuid</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Running_User__c</field>
            <value>
                <elementReference>$User.Id</elementReference>
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
                <stringValue>MeterReading_AfterSave_StampServicePoint</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
</Flow>
```

### How to read it

- **`faultConnector` on both fault-capable elements, and both point at the same node.**
  `Log_Flow_Fault` is the org's single sink. Two fault routes converging on one
  `recordCreates` is the convention the checker enforces; two *different* log objects is the
  anti-pattern it flags.
- **`Flow_Element__c` is a literal string here, not a variable.** A `recordCreates` shared by
  two fault routes cannot know which one sent it, so this example names both. If you need the
  element identified exactly, give each fault-capable element its own `recordCreates` with a
  literal, or place an `assignments` element on each route first. The checker only asks that
  the field is mapped, because "which flow" is recoverable from `Source__c` and "which
  element" is recoverable from the debug log — see `flow/flow-debugging`.
- **`Severity__c` is `ERROR`.** The shipped `Severity__c` in
  `templates/apex/custom_objects/fields/Severity__c.field-meta.xml` is a **restricted**
  picklist whose `fullName` values are `DEBUGL`, `INFOL`, `WARN`, `ERROR`, `FATAL`, and it is
  `required`. Sending anything else makes the fault-path write itself fault (gotcha 3).
- **`interviewLabel` carries the record Id.** This flow has a `scheduledPaths` entry, so it
  produces paused interviews. `interviewLabel` is what surfaces on `FlowInterview.InterviewLabel`
  and, per the guide, "appears in the Paused Flow Interviews component on the user's Home tab
  and in the list of paused flow interviews in Setup" (`api_meta.txt` L68156–L68160). Without
  the Id, the backlog query in §5 returns rows you cannot act on.
- **`status` is `Draft`.** See §8 — deploying it as `Active` needs an org setting that
  defaults to `false` in production.

> **UNVERIFIED (2026-09-05): `$Flow.FaultMessage` appears nowhere in `api_meta.txt`,
> `object_reference.txt`, `apexdev.txt` or `api_rest.txt` (0 hits for the string
> `FaultMessage` in all four).** It is the reference form used by
> `templates/flow/FaultPath_Template.md` and by Salesforce Help, which cannot be fetched.
> The `Message__c` mapping above depends on it. Deploy this flow to a scratch org and confirm
> the log row is non-empty before you standardise the convention across a portfolio.

> **UNVERIFIED (2026-09-05): `$Flow.InterviewGuid` is likewise absent from all four guides.**
> The three `InterviewGuid` hits are unrelated: `FlowInterviewLog.FlowInterviewGuid`
> (`object_reference.txt` L140081) and a REST output variable `Flow__InterviewGuid`
> (`api_rest.txt` L13753). `templates/flow/FaultPath_Template.md` documents
> `{!$Flow.InterviewGuid}` as the correlation handle. If it does not resolve in your org,
> drop the `Request_Id__c` mapping — nothing else in this package depends on it.

> **UNVERIFIED (2026-09-05): `$User.Id` as an `elementReference` inside a flow.** `$User.Id`
> is documented as a merge value in `api_meta.txt` L31153, but for `ListView` filter values,
> not for flow element references. The guide's own flow samples never reference `$User`.

---

## 2. The two additive `Application_Log__c` fields

`templates/apex/custom_objects/Application_Log__c.object-meta.xml` and its `fields/` folder
ship `Exception_Type__c`, `Message__c`, `Quiddity__c`, `Request_Id__c`, `Running_User__c`,
`Severity__c`, `Source__c` and `Stack_Trace__c`. Two more are needed for flow monitoring.
Do not fork the object; add these alongside.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Flow_Element__c</fullName>
    <externalId>false</externalId>
    <label>Flow Element</label>
    <length>80</length>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Related_Record_Id__c</fullName>
    <externalId>false</externalId>
    <label>Related Record Id</label>
    <length>18</length>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

`Message__c` is already `LongTextArea` with `<length>32768</length>`. That matters: the
checker treats an error-log object with no `LongTextArea` or `TextArea` field as an ERROR,
because a truncated fault message is worse than none — it looks like a log row and is not.

---

## 3. `Flow.settings` — the org fence that decides who hears about it

File: `settings/Flow.settings-meta.xml`. Field names and semantics from `api_meta.txt`
L116817–L117055; the shape follows the guide's own sample at L117061–L117080.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableFlowDeployAsActiveEnabled>true</enableFlowDeployAsActiveEnabled>
    <enableFlowInterviewSharingEnabled>true</enableFlowInterviewSharingEnabled>
    <enableFlowUseApexExceptionEmail>true</enableFlowUseApexExceptionEmail>
</FlowSettings>
```

| Field | Guide's wording | Why monitoring cares | Line |
|---|---|---|---|
| `enableFlowUseApexExceptionEmail` | error emails go to "the user who last modified the process or flow (`false`)" or "the addresses set on the Apex Exception Email page in Setup (`true`)"; "By default, the value is `false`" | At `false` the org has no error-email destination it controls. Every uncaught fault mails one individual. | L116961–L116967 |
| `enableFlowInterviewSharingEnabled` | at `true` (the default) "users can resume interviews that are shared with them"; at `false` "each paused interview can be resumed only by the interview owner or a flow admin who has view access" | Decides whether an ops team can actually clear the paused backlog in §5, or only look at it. | L116918–L116925 |
| `enableFlowDeployAsActiveEnabled` | "When the value is `false`, all processes and flows are deployed as inactive… The default value is `false` for production orgs" | Your monitoring instrumentation ships to production **inactive** unless this is on. | L116877–L116886 |

`flow/flow-governance` owns `Flow.settings` as policy — which values the org standardises on,
who may change them, how the change is reviewed. This skill only states which three fields a
monitoring design reads, and why.

---

## 4. `ApexEmailNotifications` — the destination those emails go to

File: `apexEmailNotifications/apexEmailNotifications.notifications`. Only meaningful once
`enableFlowUseApexExceptionEmail` is `true`. The type "allows you to define users and email
addresses that receive email for unhandled Apex errors. **Flow errors can also use this
metadata type**" (`api_meta.txt` L22415–L22417); each entry carries "an email or a user but
not both" (L22434). Shape from the guide's samples at L22462–L22466 and L22504–L22516.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexEmailNotifications xmlns="http://soap.sforce.com/2006/04/metadata">
    <apexEmailNotification>
        <email>flow-ops@example.com</email>
    </apexEmailNotification>
    <apexEmailNotification>
        <user>platform.oncall@example.com</user>
    </apexEmailNotification>
</ApexEmailNotifications>
```

**This file is replace-on-deploy, not merge-on-deploy.** "Deploying ApexEmailNotifications
deletes all previous notifications in the org" (`api_meta.txt` L22458–L22461), and the type
"isn't supported in `destructiveChanges.xml`" (L22468–L22470) — to remove one recipient you
redeploy the list without them. Keep this file in version control and treat any deploy of it
as a full replacement of the org's error-notification roster. `apex/debug-and-logging` shares
this file; a flow-side deploy that drops the Apex on-call address is a real incident.

---

## 5. The three queries a monitoring rota actually runs

### 5a. Paused and failed interview backlog

`FlowInterview` "represents a flow interview. A flow interview is a running instance of a
flow" (`object_reference.txt` L139861) and supports `query()`, `retrieve()` and `delete()`
(L139864–L139869). `InterviewStatus` is a restricted picklist whose documented values are
`Completed`, `Error`, `Paused`, `Running`, `VersionPaused` (`object_reference.txt`
L139956–L139971).

```sql
SELECT Id, InterviewLabel, InterviewStatus, CurrentElement, PauseLabel,
       WasPausedFromScreen, OwnerId, Guid, FlowVersionViewId, Error
FROM   FlowInterview
WHERE  InterviewStatus IN ('Paused', 'VersionPaused', 'Error')
ORDER BY InterviewLabel
```

- `CurrentElement` — "the flow element at which the interview is paused" (`object_reference.txt` L139891).
- `PauseLabel` — "information about why the interview was paused. This string is entered by
  the user who paused the flow interview. The label is **Why Paused**" (`object_reference.txt` L140013–L140019). It
  is **user-entered on a screen Pause**, so it is null for a scheduled path. Do not build a
  triage report on it.
- `Error` — "the error message that explains why the flow interview failed", API 62.0 and
  later (`object_reference.txt` L139907–L139913). This is the queryable error string; it
  outlives the debug log.
- `VersionPaused` — "this flow version is paused. No more records are processed until the
  flow is resumed", API 60.0 and later (`object_reference.txt` L139968–L139970). Rows in this state usually mean
  someone deactivated a version with live interviews, not that a flow failed.
- **`Expired` is not a valid `FlowInterview.InterviewStatus`.** It exists only on
  `FlowInterviewLog` (API 62.0+, `object_reference.txt` L140161). Filtering `FlowInterview`
  on `'Expired'` fails against a restricted picklist.

> **UNVERIFIED (2026-09-05): interview *age*.** The Object Reference's `FlowInterview` field
> table (L139875–L140055) does not list `CreatedDate`. If you need "paused for more than N
> days", `describeSObjects()` the object in your org before writing
> `AND CreatedDate < LAST_N_DAYS:30` into a scheduled report.

> **UNVERIFIED (2026-09-05): the Setup page "Paused and Failed Flow Interviews".** The
> guide documents the *objects*; the Setup list view and its bulk-delete action are on
> help.salesforce.com and could not be fetched. The SOQL above is the grounded path.

### 5b. Version drift — active version is not the latest version

```sql
SELECT ApiName, Label, ProcessType, TriggerType, RecordTriggerType,
       IsActive, IsOutOfDate, VersionNumber, ActiveVersionId, LatestVersionId,
       LastModifiedBy
FROM   FlowDefinitionView
WHERE  IsActive = true AND IsOutOfDate = true
ORDER BY ApiName
```

`FlowDefinitionView` "represents the description of a flow definition" and supports
`describeSObjects()` and `query()` (`object_reference.txt` L139268–L139274). `IsOutOfDate`
"indicates whether the active flow version is the latest version of the flow definition"
(L139405–L139412). A `true` row means someone saved a new version and never activated it —
which is exactly the state in which an ops team reads version 7's fault-path design while
version 5 is what actually runs.

**Do not reach for `FlowVersionView` to enumerate versions org-wide.** "A query must be
filtered by `DurableId` or `FlowDefinitionViewId` to get results"
(`object_reference.txt` L145295–L145296). Drive it from the definition view:

```sql
SELECT DurableId, VersionNumber, Status, ApiVersion, ApiVersionRuntime, Description
FROM   FlowVersionView
WHERE  FlowDefinitionViewId = '<DurableId from FlowDefinitionView>'
ORDER BY VersionNumber DESC
```

`Status` valid values are `Active`, `Draft`, `Obsolete`, `InvalidDraft`, `UnderReview`
(`object_reference.txt` L145264–L145275).

### 5c. The central log — the only surface that answers "how often"

```sql
SELECT Source__c, Flow_Element__c, COUNT(Id) error_count, MAX(CreatedDate) last_seen
FROM   Application_Log__c
WHERE  Severity__c IN ('ERROR', 'FATAL')
AND    CreatedDate = LAST_N_DAYS:7
GROUP BY Source__c, Flow_Element__c
ORDER BY COUNT(Id) DESC
```

Screen flows have a second, native surface. `FlowInterviewLog` "represents the logs of a
**screen flow** interview" (`object_reference.txt` L140059–L140060) — it holds nothing for
record-triggered, scheduled or autolaunched flows:

```sql
SELECT FlowDeveloperName, FlowLabel, FlowVersionNumber, InterviewStatus,
       InterviewStartTimestamp, InterviewDurationInMinutes, FlowInterviewGuid
FROM   FlowInterviewLog
WHERE  InterviewStatus IN ('Error', 'Expired')
AND    InterviewStartTimestamp = LAST_N_DAYS:7
ORDER BY InterviewStartTimestamp DESC
```

Access is restricted by default: "only users with the View All Data permission can access the
logs for flows that are run by other users" (`object_reference.txt` L140068–L140070); sharing
is opened up through `FlowInterviewLogOwnerSharingRule`. Plan the ops profile for that before
you promise a dashboard.

---

## 6. The monitoring report

`Report` metadata "only supports custom reports; standard reports aren't supported"
(`api_meta.txt` L103868–L103870), and reports live in a folder — "you can't use the wildcard
(*) symbol with reports in package.xml" (L103880–L103881), so the manifest member is
`<FolderName>/<ReportName>`. Element names below follow the guide's own sample definitions at
L105313–L105495 (`columns`/`field`, `format`, `groupingsDown`, `name`, `reportType`, `scope`,
`showDetails`, `timeFrameFilter`) and L105750–L105763 (the minimal tabular report);
`filter`/`criteriaItems` fields and the `FilterOperation` values are at L104595–L104660;
`ReportFormat` values `Matrix`, `Summary`, `Tabular`, `Joined` at L104676–L104690.

File: `reports/Flow_Operations/Flow_Errors_Last_7_Days.report-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://soap.sforce.com/2006/04/metadata">
    <columns>
        <field>Application_Log__c$Name</field>
    </columns>
    <columns>
        <field>Application_Log__c$Flow_Element__c</field>
    </columns>
    <columns>
        <field>Application_Log__c$Related_Record_Id__c</field>
    </columns>
    <columns>
        <field>Application_Log__c$Message__c</field>
    </columns>
    <description>Flow fault-path log rows by flow, last 7 days. Source of the weekly flow-health review.</description>
    <filter>
        <criteriaItems>
            <column>Application_Log__c$Severity__c</column>
            <columnToColumn>false</columnToColumn>
            <operator>includes</operator>
            <value>ERROR,FATAL</value>
        </criteriaItems>
    </filter>
    <format>Summary</format>
    <groupingsDown>
        <dateGranularity>Day</dateGranularity>
        <field>Application_Log__c$Source__c</field>
        <sortOrder>Asc</sortOrder>
    </groupingsDown>
    <name>Flow Errors Last 7 Days</name>
    <reportType>Application_Log__c</reportType>
    <scope>organization</scope>
    <showDetails>true</showDetails>
    <timeFrameFilter>
        <dateColumn>Application_Log__c$CreatedDate</dateColumn>
        <interval>INTERVAL_CUSTOM</interval>
        <startDate>2026-09-01</startDate>
        <endDate>2026-09-08</endDate>
    </timeFrameFilter>
</Report>
```

> **UNVERIFIED (2026-09-05): report *subscription*.** Scheduled/subscribed report delivery
> — the mechanism most orgs actually use to push this report into an inbox — has no metadata
> type in `api_meta.txt` and is documented only on help.salesforce.com. Configure it in Setup
> and record it in `templates/flow-error-monitoring-template.md`; it will not survive a
> `sf project deploy` and it will not appear in a sandbox refresh.

> **UNVERIFIED (2026-09-05): dashboard refresh cadence.** The `Dashboard` metadata type
> exists, but the guide does not state a refresh interval. Do not build paging on a
> dashboard; page on the log record itself (see the Alerting table in `SKILL.md`).

---

## 7. `FlowTest` — testing the monitoring path, not the happy path

`FlowTest` is what proves the fault route writes the log row. "Before you activate a
record-triggered, autolaunched, or Data Cloud-triggered flow, you can test it to verify its
expected results and identify flow run-time failures" (`api_meta.txt` L73961–L73962); the
type is available from API 55.0 (L73980). Shape from the guide's sample at L74338–L74392.

File: `flowtests/MeterReading_Stamp_Faults_When_Orphaned.flowtest-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>The stamp element faults when Service_Point__c is null. Proves the fault route is reached rather than the flow completing silently.</description>
    <flowApiName>MeterReading_AfterSave_StampServicePoint</flowApiName>
    <label>MeterReading Stamp Faults When Orphaned</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Status__c&quot;:&quot;Pending&quot;,&quot;Reading_Value__c&quot;:41255.00,&quot;Service_Point__c&quot;:null}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Status__c&quot;:&quot;Validated&quot;,&quot;Reading_Value__c&quot;:41255.00,&quot;Service_Point__c&quot;:null}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>Stamp_Service_Point</leftValueReference>
                <operator>HasError</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>Expected Stamp_Service_Point to fault on an orphaned meter reading. If this passes silently the fault route is never exercised and the log row is never written.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
</FlowTest>
```

### How to read it

- **`HasError` is the operator that makes a negative test possible.** It is a
  `FlowComparisonOperator` value available in API version 64.0 and later
  (`api_meta.txt` L74203). On an org below 64.0 this assertion will not save.
- **Test points can only sit at `Start` and `Finish`.** The guide enumerates exactly those
  two values for `FlowTestPoint.elementApiName` (`api_meta.txt` L74141–L74148). There is no
  mid-flow assertion, so a `FlowTest` proves *that* the fault happened; the
  `Application_Log__c` row proves the route wrote it, and the debug log proves *where*.

> **UNVERIFIED (2026-09-05): asserting on the log row itself.** No `FlowTest` field in
> `api_meta.txt` L73960–L74400 queries records created by the flow under test. To assert the
> `Application_Log__c` row exists, wrap the flow in an Apex test — `flow/flow-testing` owns
> that pattern — or verify manually in a scratch org. Do not claim `FlowTest` covers the sink.

The positive-path sibling — same shape, `Service_Point__c` populated, `HasError` `false` —
belongs in the same folder so the pair deploys together. `flow/flow-testing` owns test
strategy and coverage; this skill only requires that the *fault* path has one.

---

## 8. `package.xml`, deploy order, verification

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Application_Log__c</members>
        <members>Meter_Reading__c</members>
        <members>Service_Point__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Application_Log__c.Flow_Element__c</members>
        <members>Application_Log__c.Related_Record_Id__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>apexEmailNotifications</members>
        <name>ApexEmailNotifications</name>
    </types>
    <types>
        <members>Flow</members>
        <name>Settings</name>
    </types>
    <types>
        <members>MeterReading_AfterSave_StampServicePoint</members>
        <name>Flow</name>
    </types>
    <types>
        <members>MeterReading_Stamp_Faults_When_Orphaned</members>
        <members>MeterReading_Stamp_Succeeds</members>
        <name>FlowTest</name>
    </types>
    <types>
        <members>Flow_Operations</members>
        <name>ReportFolder</name>
    </types>
    <types>
        <members>Flow_Operations/Flow_Errors_Last_7_Days</members>
        <name>Report</name>
    </types>
    <version>62.0</version>
</Package>
```

`Settings` is the type name and `Flow` the member — that is the guide's own manifest for
`Flow.settings` (`api_meta.txt` L117084–L117090). `ApexEmailNotifications` takes either the
literal file name or `*` (L22484–L22500).

### Order

| # | Deploy | Because |
|---|---|---|
| 1 | `Application_Log__c` + the two additive fields | The flow's `recordCreates` references fields that must exist first. |
| 2 | `Meter_Reading__c`, `Service_Point__c` | The flow's `start.object` and stamp target. |
| 3 | `Flow.settings` | `enableFlowDeployAsActiveEnabled` must be `true` **before** step 5 if you want an active flow. |
| 4 | `apexEmailNotifications` | Replace-on-deploy: coordinate with whoever owns the Apex side first. |
| 5 | The flow, then the `FlowTest` pair | `FlowTest.flowApiName` is required and must resolve. |
| 6 | `ReportFolder`, then `Report` | The manifest member is `Folder/Report`; the folder must exist. |

```bash
sf project deploy start --manifest manifest/package.xml --target-org <alias> --dry-run
sf project deploy start --manifest manifest/package.xml --target-org <alias>
sf project retrieve start --metadata "Settings:Flow" --target-org <alias>
```

### Verification

1. **The fence took.** `sf project retrieve start --metadata "Settings:Flow"` and confirm
   `enableFlowUseApexExceptionEmail` reads `true` in the retrieved file — a deploy of a
   settings file that the org silently ignored looks identical to one that worked.
2. **The flow is active.** `IsActive` and `IsOutOfDate` both matter:
   ```sql
   SELECT ApiName, IsActive, IsOutOfDate, VersionNumber
   FROM   FlowDefinitionView
   WHERE  ApiName = 'MeterReading_AfterSave_StampServicePoint'
   ```
   `IsActive = false` after a production deploy is the documented default behaviour of
   `enableFlowDeployAsActiveEnabled` (`api_meta.txt` L116877–L116886), not a deploy failure.
3. **The sink actually receives.** Save a `Meter_Reading__c` with `Status__c = 'Validated'`
   and `Service_Point__c` null, then:
   ```sql
   SELECT Source__c, Flow_Element__c, Message__c, Related_Record_Id__c, Running_User__c
   FROM   Application_Log__c
   WHERE  Source__c = 'MeterReading_AfterSave_StampServicePoint'
   ORDER BY CreatedDate DESC
   LIMIT 1
   ```
   An empty `Message__c` here is the signal that `$Flow.FaultMessage` did not resolve —
   see the marker in §1.
4. **The lint passes.**
   `python3 scripts/check_flow_error_monitoring.py --manifest-dir force-app/main/default --strict`
