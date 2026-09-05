# Metadata Examples - Subflows And Reusability

A complete, deployable reuse pair: one **autolaunched child flow** that owns a routing
decision, one **record-triggered parent flow** that calls it and owns every DML, plus a
`FlowTest` that pins the child's contract before anyone activates it.

Element names, enum values, and field semantics below come from the Metadata API
Developer Guide (`api_meta.txt`, cited by line). Canonical shapes this file deliberately
does not re-invent: `templates/flow/Subflow_Pattern.md` (the input/output contract table
and the call-site XML), `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` (the
Start element and entry-criteria shape), `templates/flow/FaultPath_Template.md` (what a
fault path must do once you route to it).

---

## 1. The child - `Resolve_Case_Routing.flow-meta.xml`

Read-only by design: it derives a queue name and reports whether it succeeded. It never
writes. Side-effect tier "Lookup / derivation" in the SKILL.md reuse-safety table.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Reusable routing decision. Contract v2: in=inCaseId,inCustomerTier out=outQueueDeveloperName,outRoutingReason,outSucceeded. Callers: Case_AfterSave_Route, Escalation_Request_Submit.</description>
    <environments>Default</environments>
    <interviewLabel>Resolve Case Routing {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Resolve Case Routing</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Get_Case_Context</targetReference>
        </connector>
    </start>
    <status>Draft</status>
    <recordLookups>
        <name>Get_Case_Context</name>
        <label>Get Case Context</label>
        <locationX>50</locationX>
        <locationY>120</locationY>
        <connector>
            <targetReference>Route_By_Tier</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Set_Failure_Outputs</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>inCaseId</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <object>Case</object>
        <queriedFields>Id</queriedFields>
        <queriedFields>Priority</queriedFields>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <decisions>
        <name>Route_By_Tier</name>
        <label>Route By Tier</label>
        <locationX>50</locationX>
        <locationY>240</locationY>
        <defaultConnector>
            <targetReference>Set_Standard_Outputs</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Standard</defaultConnectorLabel>
        <rules>
            <name>Premium_Tier</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>inCustomerTier</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Premium</stringValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Set_Premium_Outputs</targetReference>
            </connector>
            <label>Premium</label>
        </rules>
    </decisions>
    <assignments>
        <name>Set_Premium_Outputs</name>
        <label>Set Premium Outputs</label>
        <locationX>176</locationX>
        <locationY>360</locationY>
        <assignmentItems>
            <assignToReference>outQueueDeveloperName</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Premium_Support_Queue</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>outRoutingReason</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Customer tier is Premium</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>outSucceeded</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </assignmentItems>
    </assignments>
    <assignments>
        <name>Set_Standard_Outputs</name>
        <label>Set Standard Outputs</label>
        <locationX>50</locationX>
        <locationY>360</locationY>
        <assignmentItems>
            <assignToReference>outQueueDeveloperName</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Standard_Support_Queue</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>outRoutingReason</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Default tier</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>outSucceeded</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </assignmentItems>
    </assignments>
    <assignments>
        <name>Set_Failure_Outputs</name>
        <label>Set Failure Outputs</label>
        <locationX>300</locationX>
        <locationY>240</locationY>
        <assignmentItems>
            <assignToReference>outSucceeded</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>false</booleanValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>outRoutingReason</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </assignmentItems>
    </assignments>
    <variables>
        <name>inCaseId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>inCustomerTier</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>outQueueDeveloperName</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
    </variables>
    <variables>
        <name>outRoutingReason</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
    </variables>
    <variables>
        <name>outSucceeded</name>
        <dataType>Boolean</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <value>
            <booleanValue>false</booleanValue>
        </value>
    </variables>
</Flow>
```

### How to read it

- `<processType>AutoLaunchedFlow</processType>` - "A flow that doesn't require user
  interaction" (`api_meta.txt` L68222). A child called through `<subflows>` must be an
  autolaunched flow: the guide's `FlowActionCall` `actionType` value `flow` "Invokes an
  autolaunched flow. This action type isn't available for flows with a processType of
  `Flow` or `AutolaunchedFlow`. To invoke an autolaunched flow from one of those types,
  use FlowSubflow" (L68751-68754).
- No `<start><object>` / `<triggerType>` here. `triggerType` is what makes a flow
  record-triggered, and it is "Available only when processType is AutoLaunchedFlow or
  PromptFlow" (L72551-72552) - so a record-triggered flow shares this child's
  `processType` but is not itself reusable as a child.
- **`isInput` / `isOutput` are the entire public contract.** `isInput` "Indicates
  whether the variable can be set at the start of the flow using URL parameters,
  Visualforce controllers, or subflow inputs" (L72886-72888); `isOutput` "Indicates
  whether the variable's value can be accessed from Visualforce controllers and other
  flows" (L72914-72916). Both default to **False** for any variable created in API 25.0
  or later (L72891-72897, L72918-72924) - an unflagged variable is invisible to the
  caller, not private-by-accident.
- The guide warns in both field descriptions: "Disabling input or output access for an
  existing variable can break the functionality of applications and pages that call the
  flow and access the variable" (L72898-72903). That is the versioning rule stated by
  Salesforce, not by convention.
- `outSucceeded` is the child's error channel. `<faultConnector>` on `Get_Case_Context`
  routes to `Set_Failure_Outputs` rather than letting the fault escape - `faultConnector`
  "Specifies which node to execute if the attempt to get records results in an error"
  (`FlowRecordLookup`, L71120-71122). The child must self-handle because the caller
  cannot: see the parent's notes below.
- `runInMode` is declared per flow (L68374-68390). `DefaultMode` = "How the flow is
  launched determines whether the flow runs in user context or in system context." Leave
  the child on `DefaultMode` so it inherits the launch context instead of silently
  widening record access for every caller.

---

## 2. The parent - `Case_AfterSave_Route.flow-meta.xml`

Record-triggered, after-save. It owns the Get, the Update, the log record, and every
fault path. The child owns only the decision.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>After-save Case routing. Delegates the routing decision to Resolve_Case_Routing and performs all DML itself.</description>
    <environments>Default</environments>
    <interviewLabel>Case After Save Route {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Case After Save Route</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Call_Resolve_Case_Routing</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>New</stringValue>
            </value>
        </filters>
        <object>Case</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
    <subflows>
        <name>Call_Resolve_Case_Routing</name>
        <label>Call Resolve Case Routing</label>
        <locationX>50</locationX>
        <locationY>120</locationY>
        <connector>
            <targetReference>Check_Routing_Succeeded</targetReference>
        </connector>
        <flowName>Resolve_Case_Routing</flowName>
        <inputAssignments>
            <name>inCaseId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>inCustomerTier</name>
            <value>
                <elementReference>$Record.Account.Type</elementReference>
            </value>
        </inputAssignments>
        <outputAssignments>
            <assignToReference>varQueueDeveloperName</assignToReference>
            <name>outQueueDeveloperName</name>
        </outputAssignments>
        <outputAssignments>
            <assignToReference>varRoutingReason</assignToReference>
            <name>outRoutingReason</name>
        </outputAssignments>
        <outputAssignments>
            <assignToReference>varRoutingSucceeded</assignToReference>
            <name>outSucceeded</name>
        </outputAssignments>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </subflows>
    <decisions>
        <name>Check_Routing_Succeeded</name>
        <label>Check Routing Succeeded</label>
        <locationX>50</locationX>
        <locationY>240</locationY>
        <defaultConnector>
            <targetReference>Log_Routing_Failure</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Routing Failed</defaultConnectorLabel>
        <rules>
            <name>Routing_Resolved</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>varRoutingSucceeded</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Get_Target_Queue</targetReference>
            </connector>
            <label>Routing Resolved</label>
        </rules>
    </decisions>
    <recordLookups>
        <name>Get_Target_Queue</name>
        <label>Get Target Queue</label>
        <locationX>50</locationX>
        <locationY>360</locationY>
        <connector>
            <targetReference>Update_Case_Owner</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Routing_Failure</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>DeveloperName</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>varQueueDeveloperName</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <object>Group</object>
        <queriedFields>Id</queriedFields>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Update_Case_Owner</name>
        <label>Update Case Owner</label>
        <locationX>50</locationX>
        <locationY>480</locationY>
        <faultConnector>
            <targetReference>Log_Routing_Failure</targetReference>
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
            <field>OwnerId</field>
            <value>
                <elementReference>Get_Target_Queue.Id</elementReference>
            </value>
        </inputAssignments>
        <object>Case</object>
    </recordUpdates>
    <recordCreates>
        <name>Log_Routing_Failure</name>
        <label>Log Routing Failure</label>
        <locationX>300</locationX>
        <locationY>480</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>varRoutingReason</elementReference>
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
                <stringValue>Case_AfterSave_Route</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
    </recordCreates>
    <variables>
        <name>varQueueDeveloperName</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varRoutingReason</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varRoutingSucceeded</name>
        <dataType>Boolean</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <value>
            <booleanValue>false</booleanValue>
        </value>
    </variables>
</Flow>
```

### How to read it

- **`<flowName>` cannot be version-pinned.** "References the flow to call at runtime. The
  value must be an API name of a flow and it **can't contain an appended hyphen and
  version number**" (L72638-72643). Contrast `Flow.fullName`, where `sampleFlow-3`
  *does* specify version 3 for deploy/retrieve (L68147-68151). So the parent always calls
  whichever version of `Resolve_Case_Routing` is **active in the target org** - you pin a
  version for deployment, never for invocation. That asymmetry is the whole reason the
  child's contract is release-managed.
- **The two ends of an assignment point in opposite directions.** In
  `<inputAssignments>`, `name` is "Unique name for the variable in the referenced flow"
  (L72668-72669) and `value` is what the parent supplies. In `<outputAssignments>`,
  `name` is again "Unique name for the variable in the **referenced** flow" (L72681) and
  `assignToReference` is "Unique name for the variable in the **parent** flow" (L72679).
  Swapping them is the single most common hand-edit bug in subflow XML.
- **`$Record` is not visible inside the child.** The parent passes `$Record.Id` and
  `$Record.Account.Type` explicitly through `<inputAssignments>`; the child has its own
  variable scope and its own (absent) Start object. Anything the child needs must appear
  as an `isInput` variable.
- **There is no fault path on `<subflows>`.** The `FlowSubflow` field table lists exactly
  `connector`, `flowName`, `inputAssignments`, `outputAssignments`,
  `storeOutputAutomatically` (L72628-72660) - no `faultConnector`, unlike
  `FlowRecordCreate` (L70965), `FlowRecordDelete` (L71046), `FlowRecordLookup` (L71120),
  `FlowRecordUpdate` (L71283), `FlowActionCall` (L68476) and `FlowApexPluginCall`
  (L69688). Hence the `outSucceeded` + `Check_Routing_Succeeded` shape: a **status
  output plus a Decision is the caller's fault path**.
- `storeOutputAutomatically` is set to `false` deliberately (default is `false`,
  L72651-72658). With `true` you reference outputs as `Call_Resolve_Case_Routing.outX`
  and never declare parent variables - convenient, but it removes the one place where a
  reviewer can see the caller's half of the contract.
- The Start element mirrors `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`.
  `RecordAfterSave` = "The flow starts after a record is saved" (L72562-72563);
  after-save is step **14** of the save order and the commit is step **19**
  (`apexdev.txt` L15470, L15478) - parent and child both run before that single commit.

---

## 3. The child's regression test - `Resolve_Case_Routing_Premium.flowtest-meta.xml`

The guide is explicit that autolaunched flows are testable: "Before you activate a
record-triggered, autolaunched, or Data Cloud-triggered flow, you can test it to verify
its expected results and identify flow run-time failures" (`FlowTest`, L73961-73962).
`FlowTest` is available in API version 55.0 and later (L73980).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Pins the Resolve_Case_Routing contract: Premium tier resolves to Premium_Support_Queue and reports success.</description>
    <flowApiName>Resolve_Case_Routing</flowApiName>
    <label>Premium tier routes to the premium queue</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>inCustomerTier</leftValueReference>
            <type>InputVariable</type>
            <value>
                <stringValue>Premium</stringValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>outQueueDeveloperName</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Premium_Support_Queue</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>Premium tier did not resolve to Premium_Support_Queue.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>outSucceeded</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>Subflow reported failure for a valid Premium Case.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

### How to read it

- `elementApiName` accepts only `Start` and `Finish` (L74144-74149). Inputs go on the
  `Start` test point, assertions on the `Finish` one.
- `type` = `InputVariable` feeds a subflow input variable, and `leftValueReference` is
  that variable's API name. The guide's isolated-data sample does exactly this -
  `<leftValueReference>Accounts</leftValueReference><type>InputVariable</type>`
  (L74415-74417). `InputVariable` is available in API version 66.0 and later
  (L74328), which is why `<apiVersion>66.0</apiVersion>` above is a floor, not a
  preference. On API 55.0-65.0 only `InputTriggeringRecordInitial`,
  `InputTriggeringRecordUpdated` and `ScheduledPath` exist (L74325-74329) - meaning a
  pure autolaunched subflow could not be given inputs by a FlowTest before 66.0.
- Assertions read the child's `isOutput` variables by name, so **the test file is a
  machine-readable copy of the contract**. Change `outSucceeded` to `outStatus` and this
  file fails before any caller does.
- `testType` is `Required` in API version 66.0 and later; the only documented value is
  `WithAssertion` (L74117-74129).
- File suffix and location: "FlowTest components have the suffix `.flowtest`, and
  Salesforce stores them in the `flowtests` folder" (L73976-73977). In SFDX source format
  that is `force-app/main/default/flowtests/<Name>.flowtest-meta.xml`.
  UNVERIFIED (2026-09-05): the `-meta.xml` source-format spelling is a Salesforce CLI
  convention; the Metadata API guide documents only the MDAPI `.flowtest` suffix.
- To exercise the child's `Get_Case_Context` fault path you need seeded data. API 66.0+
  supplies it declaratively: `flowTestDataSources` (`dataSourceType` `ApexClass` plus the
  `apexClass` name, L74070-74090) and `isolatedObjectExternalKeys` (`objectType` plus
  `keyFields`, L74092-74115), with the record body as a `jsonValue` (L74302-74306).

---

## 4. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Resolve_Case_Routing</members>
        <members>Case_AfterSave_Route</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Resolve_Case_Routing_Premium</members>
        <name>FlowTest</name>
    </types>
    <version>66.0</version>
</Package>
```

Both flows are members of the same `Flow` type - `FlowDefinition` is deliberately absent.
Since API 44.0 the guide's upgrade instructions say "The `flowDefinitions` directory is
empty" and "flow definitions are no longer necessary when you deploy or retrieve via
Metadata API" (L73186-73200). Include one anyway and you get a silent override: "If you
deploy with flow definitions, the active version numbers in the flow definitions override
the status fields in the flows... the active version number in the flow definition is
version 3, and the latest version of the flow is version 4 with the status field as
`Active`. After you deploy your flow, the active version is version 3" (L73929-73934,
duplicated at L73198-73202). `FlowDefinition.activeVersionNumber` is "The version number
of the active flow" (L73943).

---

## 5. Deploy order and activation semantics

| Step | Command | Why this order |
|---|---|---|
| 1 | `sf project deploy validate --manifest manifest/package.xml --target-org uat` | Check-only. Nothing is written. |
| 2 | Deploy the **child** first (`Resolve_Case_Routing`), status `Draft` | The parent's `<flowName>` resolves against a flow that must exist. |
| 3 | Activate the child (Setup > Flows > Resolve Case Routing > Activate) | `<flowName>` cannot name a version (L72638-72643), so the parent binds to whichever version is active. A `Draft`-only child is not callable. |
| 4 | Deploy the **parent** (`Case_AfterSave_Route`) | Now the reference resolves and the contract is already live. |
| 5 | Deploy the `FlowTest`, run it, then activate the parent | Test the contract before the trigger goes live. |

```bash
# 1. check-only validation of the whole manifest
sf project deploy validate --manifest manifest/package.xml --target-org uat

# 2. child first
sf project deploy start --metadata Flow:Resolve_Case_Routing --target-org uat

# 3. parent second (after activating the child in Setup)
sf project deploy start --metadata Flow:Case_AfterSave_Route --target-org uat

# 4. the contract test
sf project deploy start --metadata FlowTest:Resolve_Case_Routing_Premium --target-org uat

# retrieve the pair back to confirm what actually landed
sf project retrieve start --metadata Flow:Resolve_Case_Routing,Flow:Case_AfterSave_Route --target-org uat
```

Activation rules the guide states directly:

- "Any flow without a `status` value is deployed or retrieved with a `status` value of
  `Draft`" (L73188-73190). Both files above set `<status>Draft</status>` explicitly.
- "You can deploy changes to an active flow if in a non-production org, such as a scratch
  or sandbox org. To deploy changes in a production org, you must enable the **Deploy
  processes and flows as active** preference. After you deploy changes to an active flow,
  the flow's detail page shows a new flow version that's active" (L68038-68040).
- "You can delete a flow version if it isn't active and doesn't have any paused
  interviews" (L68041-68042) - which is why you cannot simply delete an old child version
  the moment a caller stops using it.
- "You can't use Metadata API to access a flow installed from a managed package unless
  the flow is a template" (L68035) - a packaged child is callable but not inspectable.

---

## 6. Verification

**Deploy-time.** `sf project deploy validate` in step 1 is the only place a broken
`<flowName>` reference surfaces before runtime, and only when the child is inside the same
manifest. Run the package checker first:

```bash
python3 skills/flow/subflows-and-reusability/scripts/check_subflows_and_reusability.py \
  --manifest-dir force-app/main/default
```

It cross-checks every `<subflows>` element against the child flow in the same tree:
`inputAssignments` names must exist as `isInput` variables, `outputAssignments` names as
`isOutput` variables, no self-reference, compatible `processType`, and no `faultConnector`
smuggled onto a subflow element.

**Setup.** Setup > Process Automation > Flows. Open **Resolve Case Routing** and confirm:
the version marked *Active* is the one you deployed, and its **Where Is This Used?**
related list names `Case_AfterSave_Route`. That list is the only place the org tells you
who the callers are - the checker sees only the files in your manifest.

**Runtime.** Create a Case on a Premium Account and query the routing result plus the
error channel:

```sql
SELECT Id, OwnerId, Owner.Name, Status
FROM Case
WHERE CreatedDate = TODAY AND Status = 'New'
ORDER BY CreatedDate DESC
LIMIT 20
```

```sql
SELECT Id, CreatedDate, Source__c, Severity__c, Message__c
FROM Application_Log__c
WHERE Source__c = 'Case_AfterSave_Route' AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

An empty log with correctly-owned Cases means the contract held. Rows in the log with
`Severity__c = 'ERROR'` are the child reporting failure through `outSucceeded` - the
parent caught it, which is exactly the behaviour a missing fault path would have hidden.
