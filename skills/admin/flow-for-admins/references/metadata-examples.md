# Metadata Examples — Flow for Admins

A Flow is one metadata component (`Flow`) whose XML carries the entire automation: the trigger, the
entry criteria, every element, and the activation status. Nothing about a Flow lives outside this
file except the optional `FlowDefinition` activation pointer and the optional `.flowtest` file.

Metadata API Developer Guide, *Flow* → Declarative Metadata File Suffix and Directory Location
(api_meta.txt:68050–68051): "Flows are stored in the `Flow` directory of the corresponding package
directory. The file name matches the flow's unique full name, and the extension is `.flow`."
Salesforce CLI source format decomposes the same component to `flows/<FullName>.flow-meta.xml` — the
guide's own upgrade instructions name that path shape ("change `myflow-1.flow-meta.xml` to
`myflow.flow-meta.xml`", api_meta.txt:73197–73198). Element names are identical in both forms; the
examples below use the DX form.

## The seven elements that decide what a Flow *is*

| Element | Type | What the guide says |
|---|---|---|
| `processType` | `FlowProcessType` | The flow's type. `AutoLaunchedFlow` = no user interaction (this is what every record-triggered and scheduled flow is); `Flow` = a screen flow. "Across flow versions, you can change the type only from `Flow` to `AutoLaunchedFlow` or vice versa" (api_meta.txt:68343–68345) |
| `start.triggerType` | `FlowTriggerType` | `RecordBeforeSave`, `RecordAfterSave`, `RecordBeforeDelete`, `Scheduled`, `PlatformEvent`, … "Available only when `processType` is `AutoLaunchedFlow` or `PromptFlow`" (api_meta.txt:72551–72553) |
| `start.recordTriggerType` | `RecordTriggerType` | `Create`, `Update`, `CreateAndUpdate`, `Delete`, `None` (api_meta.txt:72450–72457) |
| `start.object` | string | "The object whose records you want to retrieve from the database. A flow interview starts for each record that meets the filter conditions" (api_meta.txt:72425–72427) |
| `start.filterFormula` / `start.filters` + `start.filterLogic` | string / `FlowRecordFilter[]` | The two mutually-exclusive ways to write entry criteria. `filterFormula` is "a formula that's used to filter what records execute the flow during a save. Available only in record-triggered flows" (api_meta.txt:72390–72392) |
| `status` | `FlowVersionStatus` | `Active`, `Draft`, `Obsolete`, `InvalidDraft`, `UnderReview` (api_meta.txt:68416–68423). "Any flow without a `status` value is deployed or retrieved with a `status` value of `Draft`" (api_meta.txt:73187–73188) |
| `apiVersion` | number | "The API version that defines the execution behavior of the flow… available in API version 50.0 and later. Flows created before API version 50.0 show an API version of 0 on the Flows list view in Setup" (api_meta.txt:68075–68080) |

Child elements appear in the file in **alphabetical order of element name** — that is the order in
the guide's own sample definitions (api_meta.txt:73613–73708 and 73709–73827). Retrieve rewrites your
file into that order anyway, so author it that way and your diffs stay readable.

---

## Example 1 — Before-save record-triggered Flow (Case, formula-derived field)

Sets a numeric field on the triggering Case from a Flow formula. No DML, no Get Records, no fault
path — because there is nothing here that can fail at the element level.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <assignments>
        <name>Set_Escalation_Score</name>
        <label>Set Escalation Score</label>
        <locationX>176</locationX>
        <locationY>287</locationY>
        <assignmentItems>
            <assignToReference>$Record.Escalation_Score__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>Escalation_Score</elementReference>
            </value>
        </assignmentItems>
    </assignments>
    <description>Before-save. Derives Escalation_Score__c on open Cases. Owner: Service Ops. No DML — do not add a Create/Update Records element to this flow.</description>
    <environments>Default</environments>
    <formulas>
        <name>Escalation_Score</name>
        <dataType>Number</dataType>
        <expression>IF(ISPICKVAL({!$Record.Priority}, "High"), 50, 0) + IF({!$Record.IsEscalated}, 30, 0)</expression>
        <scale>0</scale>
    </formulas>
    <interviewLabel>Case Escalation Score {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Case Escalation Score</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Set_Escalation_Score</targetReference>
        </connector>
        <filterFormula>NOT(ISPICKVAL({!$Record.Status}, "Closed"))</filterFormula>
        <object>Case</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordBeforeSave</triggerType>
    </start>
    <status>Active</status>
</Flow>
```

How to read it:

- `processType` is `AutoLaunchedFlow`, not some "RecordTriggered" value. There is no such process
  type. What makes this record-triggered is `start.triggerType`; `processType` only says "no user
  interaction". Getting this wrong is the single most common hand-authored Flow XML error.
- `triggerType` `RecordBeforeSave` + `recordTriggerType` `CreateAndUpdate` is the before-save
  contract: "Creating and/or updating a record triggers an autolaunched flow to make more updates to
  that record before it's saved to the database" (api_meta.txt:72539–72542). *More updates to that
  record* — the guide's own wording is the restriction. There is no `recordCreates`, `recordUpdates`,
  `recordDeletes`, or callout `actionCalls` element in this file and there cannot be one.
- The write target is `$Record.Escalation_Score__c` through an **Assignment**, not an Update Records
  element. In a before-save flow the triggering record is still in memory; assigning to `$Record`
  *is* the write.
- `formulas` is a `FlowFormula` resource: `dataType` (defaults to `Number` when omitted),
  `expression` (required), and `scale` — "available only when the data type is `Number` or
  `Currency`" (api_meta.txt:70624–70627).
- `filterFormula` is the entry gate. Records that fail it never start an interview at all, which is
  cheaper than starting an interview and exiting at a Decision.
- `runInMode` `DefaultMode` means "how the flow is launched determines whether the flow runs in user
  context or in system context" (api_meta.txt:68375–68377). Set it deliberately; see
  `flow/flow-runtime-context-and-sharing`.

---

## Example 2 — After-save record-triggered Flow with a fault path

Creates a follow-up Task when a Case transitions **into** Closed, and routes the DML fault to an
Assignment that captures the fault message and then to an email action.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionCalls>
        <name>Notify_Service_Ops</name>
        <label>Notify Service Ops</label>
        <locationX>440</locationX>
        <locationY>430</locationY>
        <actionName>emailSimple</actionName>
        <actionType>emailSimple</actionType>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>emailAddresses</name>
            <value>
                <stringValue>service-ops@example.com</stringValue>
            </value>
        </inputParameters>
        <inputParameters>
            <name>emailSubject</name>
            <value>
                <stringValue>Case Close Followup flow fault</stringValue>
            </value>
        </inputParameters>
        <inputParameters>
            <name>emailBodyRichText</name>
            <value>
                <elementReference>faultDetail</elementReference>
            </value>
        </inputParameters>
    </actionCalls>
    <apiVersion>62.0</apiVersion>
    <assignments>
        <name>Capture_Fault</name>
        <label>Capture Fault</label>
        <locationX>440</locationX>
        <locationY>310</locationY>
        <assignmentItems>
            <assignToReference>faultDetail</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Notify_Service_Ops</targetReference>
        </connector>
    </assignments>
    <description>After-save. Creates a follow-up Task when a Case enters Closed. Fault path emails Service Ops. Owner: Service Ops.</description>
    <environments>Default</environments>
    <interviewLabel>Case Close Followup {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Case Close Followup</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Create_Followup_Task</name>
        <label>Create Followup Task</label>
        <locationX>176</locationX>
        <locationY>310</locationY>
        <faultConnector>
            <targetReference>Capture_Fault</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Subject</field>
            <value>
                <stringValue>Post-closure quality review</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>WhatId</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>OwnerId</field>
            <value>
                <elementReference>$Record.OwnerId</elementReference>
            </value>
        </inputAssignments>
        <object>Task</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Create_Followup_Task</targetReference>
        </connector>
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
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Active</status>
    <variables>
        <name>faultDetail</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

How to read it:

- `doesRequireRecordChangedToMeetCriteria` is the delta check, and it is the reason this flow does
  not fire on every edit to an already-Closed Case: "If set to `true`, conditions evaluate to `true`
  only if the record didn't meet the required conditions before the triggering update but now meets
  the conditions after the update" (api_meta.txt:72322–72325). It is a `start` field, so it applies
  to the whole `filters` block, not to one filter row.
- `filters` + `filterLogic` and `filterFormula` are alternatives. `filters` is what makes
  `doesRequireRecordChangedToMeetCriteria` meaningful, which is why this example uses it and
  Example 1 uses the formula.
- The `faultConnector` on `recordCreates` is a plain `FlowConnector`: "Specifies which node to
  execute if the attempt to create a record results in an error" (api_meta.txt:70965–70966). Its
  only child is `targetReference`. There is no per-element "on error continue" switch — a DML
  element with no `faultConnector` throws an unhandled fault and the whole triggering transaction
  rolls back.
- `$Flow.FaultMessage` is only populated on a fault path. Reading it anywhere else returns nothing.
- `inputAssignments` here is `FlowInputFieldAssignment`: `field` (required) + `value`
  (api_meta.txt:70679–70682). It is a different type from the `inputAssignments` on a `subflows`
  element, which carries `name` instead.
- UNVERIFIED (2026-09-04): the Metadata API guide documents `emailSimple` as a valid
  `InvocableActionType` ("Sends an email by using flow resources", api_meta.txt:68731–68732) but
  does not list its input parameter names. `emailAddresses` / `emailSubject` / `emailBodyRichText`
  are the names Flow Builder emits; confirm against a retrieved flow from your own org before
  deploying this block verbatim.
- UNVERIFIED (2026-09-04): the guide's `recordTriggerType` entry says "Available only when
  `triggerType` is `RecordBeforeSave` or `DataCloudDataChange`" (api_meta.txt:72458–72460), yet
  after-save flows retrieved from an org carry `recordTriggerType`. Treat the guide sentence as
  incomplete rather than as a prohibition; the value above matches what Flow Builder writes.

---

## Activation: `FlowDefinition`, and why you probably should not write one

`FlowDefinition` carries exactly one interesting field — `activeVersionNumber`, "the version number
of the active flow" (api_meta.txt:73943). The guide's own recommendation, verbatim
(api_meta.txt:73926–73928):

> In API version 44.0, we recommend upgrading your flows to flow metadata file names without version
> numbers and discontinue using the FlowDefinition object to activate or deactivate a flow. Then use
> the Flow object to activate or deactivate a flow.

And the override rule that bites people who keep both (api_meta.txt:73929–73932):

> If you deploy with flow definitions, the active version numbers in the flow definitions override
> the status fields in the flows. For example, the active version number in the flow definition is
> version 3, and the latest version of the flow is version 4 with the status field as `Active`.
> After you deploy your flow, the active version is version 3.

So: set `<status>Active</status>` in the `.flow-meta.xml` and leave `flowDefinitions/` empty. The
file below exists only for the legacy case where you must pin an older version as active.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <activeVersionNumber>3</activeVersionNumber>
    <description>Pins version 3 active. Remove once the org is on the API 44.0+ activation model.</description>
</FlowDefinition>
```

Path: `flowDefinitions/Case_Close_Followup.flowDefinition-meta.xml` — "FlowDefinitions are stored in
the `flowDefinitions` directory… the extension is `.flowDefinition`" (api_meta.txt:73935–73937).
Setting `activeVersionNumber` to `0` deactivates. UNVERIFIED (2026-09-04): the `0` = deactivate
convention is widely used but the guide documents only "the version number of the active flow".

---

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_Escalation_Score</members>
        <members>Case_Close_Followup</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Flow</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

`Flow` supports the `*` wildcard (api_meta.txt:73831–73833). The second `types` block retrieves
`FlowSettings` as `settings/Flow.settings-meta.xml` — that is where
`enableFlowDeployAsActiveEnabled` lives, and you need to read it before you can predict whether a
production deploy will land Active or Draft. All settings types are addressed as `Settings` in the
manifest (api_meta.txt:116819).

---

## Retrieve and deploy

```bash
# Retrieve an existing flow plus the org's process-automation settings
sf project retrieve start \
  --metadata "Flow:Case_Close_Followup" --metadata "Settings:Flow" \
  --target-org myOrgAlias

# Check what activation behaviour the target org actually has
grep enableFlowDeployAsActiveEnabled force-app/main/default/settings/Flow.settings-meta.xml

# Validate against production without committing (run local tests only)
sf project deploy validate \
  --source-dir force-app/main/default/flows \
  --test-level RunLocalTests --target-org prod

# Deploy
sf project deploy start \
  --source-dir force-app/main/default/flows --target-org prod
```

**The activation caveat, in the guide's words** (api_meta.txt:68037–68040): "You can deploy changes
to an active flow if in a non-production org, such as a scratch or sandbox org. To deploy changes in
a production org, you must enable the **Deploy processes and flows as active** preference." And the
setting itself (api_meta.txt:116877–116886): `enableFlowDeployAsActiveEnabled` — "When the value is
`false`, all processes and flows are deployed as inactive. When the value is `true`, deploying an
active process or flow in a production org causes your Apex tests to run. If Apex tests don't launch
your org's required percentage of active processes and autolaunched flows, the deployment is rolled
back. The default value is `false` for production orgs and is `true` for non-production orgs."

Read that twice. `<status>Active</status>` deploys clean to your sandbox and lands as **Draft** in
production unless someone turned the preference on — and once it *is* on, the same deploy can be
rolled back for a coverage reason that has nothing to do with your flow. Both outcomes are silent
from the flow file's point of view. Two other deploy-time rules from the same list: a flow installed
from a managed package is unreachable through Metadata API unless it is a template
(api_meta.txt:68035), and "spaces in a flow file name can lead to errors when you deploy the
flow" (api_meta.txt:68036–68037).

---

## Verification

`FlowDefinitionView` "represents the description of a flow definition" and supports
`describeSObjects()` and `query()` (object_reference.txt:139268–139273). Run this immediately after
the deploy — it is the only cheap way to prove the flow landed *and* landed active.

```sql
SELECT ApiName, Label, ProcessType, TriggerType, RecordTriggerType,
       TriggerObjectOrEventLabel, TriggerOrder, ApiVersion,
       ActiveVersionId, LatestVersionId, VersionNumber, IsActive, IsOutOfDate
FROM FlowDefinitionView
WHERE ApiName IN ('Case_Escalation_Score', 'Case_Close_Followup')
```

| Column | Read it as |
|---|---|
| `IsActive` | "Indicates whether the latest version of the flow definition is the active flow version" (object_reference.txt:139402–139405). `false` here after a production deploy is the deploy-as-inactive outcome above |
| `IsOutOfDate` | "Indicates whether the active flow version is the latest version of the flow definition" (object_reference.txt:139410–139413) — `true` means users are running an older version than the one you just deployed |
| `ActiveVersionId` vs `LatestVersionId` | Unequal ids say the same thing as `IsOutOfDate`, but give you the version id to query next |
| `TriggerType` / `RecordTriggerType` | Confirms before- vs after-save survived the deploy. `RecordTriggerType` is documented on this view as "Available only when `triggerType` is `RecordBeforeSave`" (object_reference.txt:139700–139701) |
| `TriggerOrder` | "The run order of a record-triggered flow, from 1 to 2,000" (object_reference.txt:139768–139770). Null means unordered relative to other flows on the object |

To list every version and its status, query `FlowVersionView` — but note the hard constraint in its
Usage note (object_reference.txt:145295–145296): "A query must be filtered by `DurableId` or
`FlowDefinitionViewId` to get results." An unfiltered query returns nothing, not an error.

```sql
SELECT VersionNumber, Status, Label, ApiVersion, ApiVersionRuntime
FROM FlowVersionView
WHERE FlowDefinitionViewId = '300xx0000000001AAA'
ORDER BY VersionNumber DESC
```

`Status` values are `Active`, `Draft`, `Obsolete`, `InvalidDraft`, `UnderReview`
(object_reference.txt:145269–145275). Anything other than one `Active` and the rest `Obsolete` /
`Draft` is version debt worth pruning — and the guide notes you can only delete a version that "isn't
active and doesn't have any paused interviews" (api_meta.txt:68041–68042).

## Flow tests are deployable metadata too

`FlowTest` "represents the metadata associated with a flow test. Before you activate a
record-triggered, autolaunched, or Data Cloud-triggered flow, you can test it to verify its expected
results and identify flow run-time failures" (api_meta.txt:73960–73962). Components "have the suffix
`.flowtest`, and Salesforce stores them in the `flowtests` folder", available in API version 55.0
and later (api_meta.txt:73975–73980). Required fields are `flowApiName`, `label`, and — from API
66.0 — `testType`, whose documented value is `WithAssertion`, "the automated comparison of the actual
flow outcome with the user-defined expected outcome that assertions define"
(api_meta.txt:74042–74049). Flow tests are *not* Apex tests: they do not contribute to the org
coverage percentage that `enableFlowDeployAsActiveEnabled` checks. See `flow/flow-testing`.
