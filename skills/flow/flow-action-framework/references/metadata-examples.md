# Metadata Examples — Flow Action Framework

One deployable record-triggered flow that exercises **four different action families in a
single path** — an Apex action bound to a generic-sObject invocable, a workflow email
alert, a Chatter post core action, and a subflow — plus the `InvocableActionExtension`
that controls how the Apex action's inputs are laid out in Flow Builder, a `FlowTest` that
pins the outcome, a `package.xml`, the deploy order, and the REST describe call that is
the only org-side proof the action catalogue actually holds what the flow expects.

Every element name, enum value, and default below is cited to the Metadata API Developer
Guide (`api_meta.txt`), Apex Developer Guide (`apexdev.txt`), or REST API Developer Guide
(`api_rest.txt`) by line. Shapes this file deliberately does not re-invent:
`templates/flow/RecordTriggered_Skeleton.flow-meta.xml` (Start element and entry
criteria), `templates/flow/FaultPath_Template.md` (what a fault path must do once you
route to it), `templates/flow/Subflow_Pattern.md` (the child contract table). The Apex
class behind the action belongs to `apex/invocable-methods`; only its flow-facing surface
appears here.

---

## 1. The flow — `Case_Escalation_Router.flow-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>After-save escalation router. Action inventory: apex(RankCaseCollection), emailAlert(Case.Escalation_Owner_Alert), chatterPost, subflow(Record_Escalation_Audit).</description>
    <environments>Default</environments>
    <interviewLabel>Case Escalation Router {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Case Escalation Router</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <status>Draft</status>

    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Get_Related_Cases</targetReference>
        </connector>
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

    <recordLookups>
        <name>Get_Related_Cases</name>
        <label>Get Related Cases</label>
        <locationX>50</locationX>
        <locationY>120</locationY>
        <connector>
            <targetReference>Rank_Cases</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Action_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>AccountId</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.AccountId</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <object>Case</object>
        <queriedFields>Id</queriedFields>
        <queriedFields>Priority</queriedFields>
        <queriedFields>CreatedDate</queriedFields>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>

    <!-- ACTION 1 of 4: actionType `apex`. Generic-sObject invocable, so it needs
         dataTypeMappings. Outputs are auto-stored, so no outputParameters block. -->
    <actionCalls>
        <name>Rank_Cases</name>
        <label>Rank Cases</label>
        <locationX>50</locationX>
        <locationY>240</locationY>
        <actionName>RankCaseCollection</actionName>
        <actionType>apex</actionType>
        <connector>
            <targetReference>Notify_Owner</targetReference>
        </connector>
        <dataTypeMappings>
            <typeName>T__inputCollection</typeName>
            <typeValue>Case</typeValue>
        </dataTypeMappings>
        <dataTypeMappings>
            <typeName>U__outputMember</typeName>
            <typeValue>Case</typeValue>
        </dataTypeMappings>
        <faultConnector>
            <targetReference>Log_Action_Fault</targetReference>
        </faultConnector>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>inputCollection</name>
            <value>
                <elementReference>Get_Related_Cases</elementReference>
            </value>
        </inputParameters>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </actionCalls>

    <!-- ACTION 2 of 4: actionType `emailAlert`. Sends by referencing a workflow email
         alert (api_meta L68729).
         UNVERIFIED (2026-09-05): the `Object.Alert_DeveloperName` shape of <actionName>
         and the input-parameter name `SObjectRowId` are not stated in api_meta.txt,
         api_rest.txt or apexdev.txt; they come from the Actions Developer Guide, which
         is not among the extracted PDFs. Retrieve one working emailAlert action from the
         target org and copy its exact <actionName>/<inputParameters> before deploying. -->
    <actionCalls>
        <name>Notify_Owner</name>
        <label>Notify Owner</label>
        <locationX>50</locationX>
        <locationY>360</locationY>
        <actionName>Case.Escalation_Owner_Alert</actionName>
        <actionType>emailAlert</actionType>
        <connector>
            <targetReference>Post_Escalation_Note</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Action_Fault</targetReference>
        </faultConnector>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>SObjectRowId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputParameters>
    </actionCalls>

    <!-- ACTION 3 of 4: actionType `chatterPost`. Input parameter names `text` and
         `subjectNameOrId` are the guide's own sample (api_meta L73249-73269). -->
    <actionCalls>
        <name>Post_Escalation_Note</name>
        <label>Post Escalation Note</label>
        <locationX>50</locationX>
        <locationY>480</locationY>
        <actionName>chatterPost</actionName>
        <actionType>chatterPost</actionType>
        <connector>
            <targetReference>Log_Escalation</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Action_Fault</targetReference>
        </faultConnector>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>text</name>
            <value>
                <elementReference>txtEscalationNote</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>subjectNameOrId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputParameters>
    </actionCalls>

    <!-- ACTION 4 of 4: a subflow. NOT an <actionCalls> element and NOT actionType `flow`
         — from a processType of AutoLaunchedFlow, FlowSubflow is the only legal way to
         call another flow (api_meta L68749-68754). It has no faultConnector field
         (api_meta L72625-72658), which is why the child returns outSucceeded instead. -->
    <subflows>
        <name>Log_Escalation</name>
        <label>Log Escalation</label>
        <locationX>50</locationX>
        <locationY>600</locationY>
        <connector>
            <targetReference>Check_Audit_Result</targetReference>
        </connector>
        <flowName>Record_Escalation_Audit</flowName>
        <inputAssignments>
            <name>inCaseId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>inRankedCount</name>
            <value>
                <elementReference>Rank_Cases.rankedCount</elementReference>
            </value>
        </inputAssignments>
        <outputAssignments>
            <assignToReference>varAuditLogId</assignToReference>
            <name>outLogId</name>
        </outputAssignments>
        <outputAssignments>
            <assignToReference>varAuditSucceeded</assignToReference>
            <name>outSucceeded</name>
        </outputAssignments>
    </subflows>

    <decisions>
        <name>Check_Audit_Result</name>
        <label>Check Audit Result</label>
        <locationX>50</locationX>
        <locationY>720</locationY>
        <defaultConnector>
            <targetReference>Log_Action_Fault</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Audit Failed</defaultConnectorLabel>
        <rules>
            <name>Audit_Succeeded</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>varAuditSucceeded</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <label>Audit Succeeded</label>
        </rules>
    </decisions>

    <recordCreates>
        <name>Log_Action_Fault</name>
        <label>Log Action Fault</label>
        <locationX>320</locationX>
        <locationY>240</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Case_Escalation_Router</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>ERROR</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordCreates>

    <textTemplates>
        <name>txtEscalationNote</name>
        <isViewedAsPlainText>true</isViewedAsPlainText>
        <text>Case escalated. Related open cases ranked: {!Rank_Cases.rankedCount}.</text>
    </textTemplates>

    <variables>
        <name>varAuditLogId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varAuditSucceeded</name>
        <dataType>Boolean</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

### How to read it

- **`actionName` + `actionType` are both `Required` and together identify the action.**
  `actionName` is "Required. Name for the action. Must be unique across actions with the
  same actionType" (api_meta L68462-68463) — uniqueness is *per action type*, not global,
  so `actionType apex` / `actionName Escalate` and `actionType flow` / `actionName
  Escalate` are two different actions. For `actionType apex` the name is the **Apex class
  name**, not the method name or the `label`: the guide's own sample pairs
  `<actionName>GetFirstFromCollection</actionName>` with the `GetFirstFromCollection`
  class in the Apex guide (api_meta L73215-73216, sample flow L73211-73248; apexdev L5240-5288), and "Only one
  method in a class can have the InvocableMethod annotation" (apexdev L5422) is what makes
  a class name sufficient to address a method.
- **`flowTransactionModel` is `Required` on every action call** (api_meta L68479-68480),
  not only on ones that call out. The three values are `Automatic` — "Creates a transaction
  if the invocable action supports it and there's pending DML"; `CurrentTransaction` —
  "Keeps the invocable action running in the same transaction"; `NewTransaction` —
  "Creates a transaction before the invocable action is executed" (api_meta L68481-68486).
  API 51.0 and later. The guide's own sample sets it even on a `chatterPost`
  (api_meta L73259, inside the sample's chatterPost element L73249-73269).
- **`dataTypeMappings` is the flow half of a generic-sObject contract.** `typeName` is
  "Required. API name of the input or output variable. The `T__` prefix is required for
  input variables. The `U__` prefix is required for output variables"; `typeValue` is the
  "API name of the specific sObject data type that this value maps to" (api_meta
  L70192-L70203). API 48.0 and later (api_meta L68470-68472). The Apex-side rules. Without it a generic action
  cannot be bound to a concrete object. The Apex-side rules for declaring
  `List<SObject>` belong to `apex/invocable-methods`.
- **`storeOutputAutomatically`** — "Indicates whether the action's output parameters are
  automatically available in the flow without creating any variables. When the value is
  `true`, you can reference an output parameter by specifying the API name of the Action
  element in the flow. The default value is `false`. When the value is `false`, create
  variables manually" (api_meta L68523-68529). That is why `{!Rank_Cases.rankedCount}`
  works above with no `outputParameters` block and no declared variable. API 48.0+.
- **`faultConnector`** — "Specifies which node to execute if the action call results in an
  error" (api_meta L68476-68477). It is optional in the schema, so an action ships without
  one unless you add it. All four action calls above route to the same
  `Log_Action_Fault` element. Fault-path *design* (retry, user messaging, log shape) is
  `flow/fault-handling`.
- **The subflow is not an action call.** `FlowSubflow` has exactly `connector`,
  `flowName`, `inputAssignments`, `outputAssignments`, `storeOutputAutomatically`
  (api_meta L72625-72658) — no `faultConnector`, no `flowTransactionModel`, no
  `dataTypeMappings`. `outputAssignments.assignToReference` is the parent variable;
  `name` is the child variable (api_meta L72674-72683). Contract design for the child is
  `flow/subflows-and-reusability`.
- **`$Record.AccountId` and `$Record.Id`** are `elementReference` values — the merge-field
  form of `FlowElementReferenceOrValue`, where the guide's rule is "Make sure that you
  specify only one of the fields" (api_meta L70411-L70413).

---

## 2. Laying out the Apex action's inputs — `RankCaseCollection.invocableactionextension-meta.xml`

By default Flow Builder shows an action's inputs alphabetically (apexdev L26901-26902).
`InvocableActionExtension` overrides that and groups them. Available in API version 65.0
and later (api_meta L81907).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<InvocableActionExtension xmlns="http://soap.sforce.com/2006/04/metadata">
    <targets>
        <targetType>ActionParameter</targetType>
        <targetName>RankCaseCollection.Requests.inputCollection</targetName>
        <attributes>
            <key>Order</key>
            <dataType>Integer</dataType>
            <value>1</value>
        </attributes>
        <attributes>
            <key>Group</key>
            <dataType>String</dataType>
            <value>Ranking Input</value>
        </attributes>
    </targets>
    <targets>
        <targetType>ActionParameter</targetType>
        <targetName>RankCaseCollection.Requests.rankingMode</targetName>
        <attributes>
            <key>Order</key>
            <dataType>Integer</dataType>
            <value>2</value>
        </attributes>
        <attributes>
            <key>Group</key>
            <dataType>String</dataType>
            <value>Ranking Input</value>
        </attributes>
        <attributes>
            <key>ProvidedValuesList</key>
            <dataType>String</dataType>
            <value>age|Oldest First, priority|Priority Then Age</value>
        </attributes>
    </targets>
</InvocableActionExtension>
```

### How to read it

| Element | Grounding |
|---|---|
| File name / location | "The file must have the suffix `.invocableactionextension-meta.xml` and the filename corresponds to the Apex class name… Add the metadata file to the `invocableactionextensions` directory" (apexdev L26979-26980). The Metadata API guide states the suffix without the `-meta.xml` tail: "components have the suffix `.invocableactionextension` and are stored in the `invocableactionextensions` folder" (api_meta L81902-81903) — the `-meta.xml` tail is the Salesforce-DX source form. |
| `targetType` | `ActionDefinition` (the action class), `ActionParameter` (a specific input/output parameter), `TypeDefinition` (custom Apex types), `TypeProperty` (properties within those types). Required (api_meta L81945-81956). |
| `targetName` | `<ApexClass>.<WrapperClass>.<field>` — the guide's example is `BookingAction.BookingRequest.startDate` (apexdev L26994). |
| `Order` | "Controls the vertical display sequence of input parameters in the action's property panel in Flow Builder" (api_meta L82002-82003). **All-or-nothing:** "If you define an `Order` for at least one parameter, you must define an `Order` for all parameters within the action to avoid unexpected behavior" (apexdev L26985-26986). |
| `Group` / `GroupName` | The Apex guide's worked example uses `<key>Group</key>` (apexdev L26996-27011) and the Metadata API sample uses `Group` too (api_meta L82043, L82057, L82071) — but the Metadata API *field table* names the standard key `GroupName` (api_meta L82000-82001). Both are printed in Summer '26 docs; deploy the Apex guide's `Group` form first and retrieve to confirm what the org normalises it to. |
| `ProvidedValuesList` / `ProvidedValueList` | Same split: apexdev uses `ProvidedValuesList` (L27033, L27048, L27096), while the api_meta field table (L82004-82005) *and* its samples (L82094, L82108) both say `ProvidedValueList`. Format is a comma-separated list, optional `value|Label` pairs (apexdev L27035). Cap: "Each input parameter supports up to 500 total picklist values" (apexdev L27034). `apex://MyDynamicPicklistClass` swaps the static list for a `VisualEditor.DynamicPicklist` subclass (apexdev L27092-27100). |
| `dataType` | Required. `Boolean`, `Date`, `Double`, `Integer`, `Long`, `String` (api_meta L81974-81981). |
| Root element name | The Metadata API guide prints one sample rooted at `<InvocableActionExt>` (api_meta L82033) and three at `<InvocableActionExtension>` (api_meta L82089, L82103; apexdev L26988). `InvocableActionExt` returns no other hit in the guide. `InvocableActionExtension` is the type name in the field tables — use it. |

The `CpeName` key assigns a Lightning web component as a **partial** custom property
editor for one input parameter, and `ConfiguredBy` links a second parameter to it
(api_meta L81992-81995). Building that LWC is `lwc/custom-property-editor-for-flow`;
deciding whether an editor is warranted is `flow/flow-custom-property-editors`.

---

## 3. Pinning the outcome — `Case_Escalation_Router_Escalates.flowtest-meta.xml`

`FlowTest` exists so that "Before you activate a record-triggered, autolaunched, or Data
Cloud-triggered flow, you can test it to verify its expected results and identify flow
run-time failures" (api_meta L73961-73962). API 55.0 and later (api_meta L73980).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Escalating a Case runs the four-action path and the audit subflow reports success.</description>
    <flowApiName>Case_Escalation_Router</flowApiName>
    <label>Escalation path succeeds end to end</label>
    <testType>WithAssertion</testType>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Status&quot;:&quot;New&quot;,&quot;Priority&quot;:&quot;Medium&quot;}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Status&quot;:&quot;Escalated&quot;,&quot;Priority&quot;:&quot;High&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <elementApiName>Finish</elementApiName>
        <assertions>
            <conditions>
                <leftValueReference>varAuditSucceeded</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>The audit subflow reported failure, so at least one action in the escalation path did not complete.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>varAuditLogId</leftValueReference>
                <operator>IsNull</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>No audit log Id came back from the subflow.</errorMessage>
        </assertions>
    </testPoints>
</FlowTest>
```

### How to read it — and what it cannot do

- **You get two test points, not one per element.** `FlowTestPoint.elementApiName` is
  "Required. The element API names for the start of the flow and the end of the flow.
  Possible values are: `Start`, `Finish`" (api_meta L74140-74146). There is no test point
  *at* `Rank_Cases`, so a FlowTest cannot assert on an action's output parameter directly.
  Route what you want to assert into a flow variable (as `varAuditSucceeded` above) and
  assert on that at `Finish`.
- **`testType` is `WithAssertion`** — "Specifies whether the test contains assertions.
  This field is available in API version 66.0 and later" (api_meta L74041-74048). At API
  65.0 and below, omit it.
- **Assertions fail the run individually.** "If one assertion evaluates to false, the test
  run fails" and "If one condition evaluates to false, the assertion fails" (api_meta
  L74158, L74182). `HasError` is a `FlowComparisonOperator` value from API
  64.0 (api_meta L74203) — useful for asserting a fault path was *taken*.
- **Screen flows are out of scope.** The type's own scope line names record-triggered,
  autolaunched and Data Cloud-triggered flows only (api_meta L73961-73962), so an action
  wired into a screen flow gets no FlowTest coverage. Deeper FlowTest technique lives in
  `flow/flow-testing`.
- **Mocking is not available.** `FlowTestPoint.isUseMockOuput` is "Reserved for future
  use" (api_meta L74148). A FlowTest over the flow above really invokes
  `RankCaseCollection`, really fires the email alert, and really posts to Chatter — which
  is a reason to keep side-effecting actions behind a subflow you can point at a sandbox
  configuration.

---

## 4. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>RankCaseCollection</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>RankCaseCollection</members>
        <name>InvocableActionExtension</name>
    </types>
    <types>
        <members>Case.Escalation_Owner_Alert</members>
        <name>WorkflowAlert</name>
    </types>
    <types>
        <members>Escalation_Owner_Email</members>
        <name>EmailTemplate</name>
    </types>
    <types>
        <members>Record_Escalation_Audit</members>
        <members>Case_Escalation_Router</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Case_Escalation_Router_Escalates</members>
        <name>FlowTest</name>
    </types>
    <version>66.0</version>
</Package>
```

**Why the alert and the template are listed explicitly.** The REST guide states it
outright: "If any of these elements are used in a flow, packageable components that
reference the elements aren't automatically included in the package" — the list is *Apex
action, Email alerts, Post to Chatter core action, Quick Action core action, Send Email
core action, Submit for Approval core action* — and "For example, if you use an email
alert, manually add the email template that's used by that email alert. To deploy the
package successfully, manually add those referenced components to the package"
(api_rest L13787-13800). Three of the four action families in this flow are on that list.
UNVERIFIED (2026-09-05): the `<name>WorkflowAlert</name>` type with an
`Object.Alert_DeveloperName` member is the conventional manifest shape, but `api_meta.txt`
documents alerts only as the `alerts` field inside a `Workflow` component, one file per
object with the `.workflow` suffix (L139908, L139896-L139897), and shows only
`<name>Workflow</name>` in its manifest example (L139886-L139890). If a `WorkflowAlert`
member is rejected, fall back to `<name>Workflow</name>` with the object name as the
member.

`FlowDefinition` is deliberately absent: since API 44.0 "The `flowDefinitions` directory
is empty" and its `activeVersionNumber` silently overrides your `status` fields if you
ship one (api_meta L73188, L73198-73200; L73929-73931).

---

## 5. Deploy order

| Step | What | Why this order |
|---|---|---|
| 1 | `ApexClass` + `InvocableActionExtension` | The flow's `<actionName>RankCaseCollection</actionName>` resolves against the action catalogue, which is built from compiled classes. |
| 2 | `EmailTemplate`, then `WorkflowAlert` | The alert references the template; neither is pulled in by the flow (api_rest L13787-13800). |
| 3 | The **child** flow `Record_Escalation_Audit`, then activate it | A parent binds to the active version — `flowName` "can't contain an appended hyphen and version number" (api_meta L72638-72643). |
| 4 | The **parent** flow `Case_Escalation_Router` | Every action it names now exists. |
| 5 | `FlowTest`, run it, then activate the parent | The test is what proves the four-action path before the trigger goes live. |

```bash
# check-only first; nothing is written
sf project deploy validate --manifest manifest/package.xml --target-org uat

# 1. the action's Apex + its Flow Builder layout
sf project deploy start \
  --metadata ApexClass:RankCaseCollection,InvocableActionExtension:RankCaseCollection \
  --target-org uat

# 2. email template before the alert that references it
sf project deploy start \
  --metadata EmailTemplate:Escalation_Owner_Email,WorkflowAlert:Case.Escalation_Owner_Alert \
  --target-org uat

# 3-4. child flow, then parent
sf project deploy start --metadata Flow:Record_Escalation_Audit --target-org uat
sf project deploy start --metadata Flow:Case_Escalation_Router --target-org uat

# 5. the contract test
sf project deploy start --metadata FlowTest:Case_Escalation_Router_Escalates --target-org uat

# retrieve the flow back to see what the org normalised
sf project retrieve start --metadata Flow:Case_Escalation_Router --target-org uat
```

---

## 6. Verification

**Before deploy — the package checker.** It is the only step that cross-checks the flow's
`actionCalls` against the Apex classes in the same tree:

```bash
python3 skills/flow/flow-action-framework/scripts/check_flow_action_framework.py \
  --manifest-dir force-app/main/default
```

**After deploy — the action catalogue describe.** This is the org-side proof that the
action the flow names actually exists with the parameters the flow binds. The invocable
actions resource is available in REST API version 32.0 and later
(api_rest L13762-13763 custom, L13918-13919 standard):

```bash
# the two catalogue roots
curl https://MyDomainName.my.salesforce.com/services/data/v66.0/actions \
  -H "Authorization: Bearer $SF_TOKEN"
# -> {"standard":"/services/data/v66.0/actions/standard",
#     "custom":"/services/data/v66.0/actions/custom"}

# every custom action family in this org
curl https://MyDomainName.my.salesforce.com/services/data/v66.0/actions/custom \
  -H "Authorization: Bearer $SF_TOKEN"
# -> {"quickAction":..., "apex":..., "emailAlert":..., "flow":..., "sendNotification":...}

# describe THIS action: does it exist, and what are its input names?
curl https://MyDomainName.my.salesforce.com/services/data/v66.0/actions/custom/apex/RankCaseCollection \
  -H "Authorization: Bearer $SF_TOKEN"

# the standard-action catalogue, for chatterPost / emailSimple / submit
curl https://MyDomainName.my.salesforce.com/services/data/v66.0/actions/standard \
  -H "Authorization: Bearer $SF_TOKEN"
```

Two behaviours make this describe worth running as a release gate rather than a curiosity:

- **It answers as the calling user.** "Describe and invoke for an Apex action respect the
  profile access for the Apex class. If you don't have access, an error is issued"
  (api_rest L13780). Run it as a *representative end user*, not as the admin who deployed
  — an action that describes for you and 403s for them is the classic "works in sandbox,
  fails in prod" shape.
- **It is the only pre-runtime signal that the binding still holds.** "If you add an Apex
  action to a flow, and then remove the Invocable Method annotation from the Apex class, a
  runtime error in the flow occurs" (api_rest L13781-13782) — the deploy succeeds either
  way. A describe that 404s on `custom/apex/RankCaseCollection` while the flow still names
  it is that failure, caught before an interview hits it.

**Runtime.** After a test escalation, the fault channel should be empty and the audit row
present:

```sql
SELECT Id, CreatedDate, Source__c, Severity__c, Message__c
FROM Application_Log__c
WHERE Source__c = 'Case_Escalation_Router' AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

Rows here carry `$Flow.FaultMessage` from whichever of the four actions failed — the
element name in the message is how you tell the Apex action apart from the email alert.
One more counter to watch on this flow specifically: "Sending email with the `emailAlert`
action counts against your daily email limit for workflows" (api_rest L13765-13766), so a
bulk escalation that fans out one alert per Case burns that allocation, not the Apex
`Messaging` allocation.
