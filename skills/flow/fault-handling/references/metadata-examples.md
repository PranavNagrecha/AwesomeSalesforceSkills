# Metadata Examples — Flow Fault Handling

Three complete, deployable flows that fail on purpose — a **screen flow** that routes a
fault to a rollback plus a user-safe screen, an **autolaunched flow** whose fault path
logs to a custom object and posts to Chatter (and whose *log write* has its own fault
path), and a **record-triggered before-save flow** whose fault path lands on a **Custom
Error** element that blocks the save. Plus a `FlowTest` that asserts the guard fired,
a `package.xml`, a deploy order, and the two places you verify what actually landed.

Every element name, enum value and version floor below comes from the Metadata API
Developer Guide, Flow section (`api_meta.txt`, `Flow` L68065+), cited by `grep -n` line.
Save-order and transaction claims cite the Apex Developer Guide (`apexdev.txt`
L15402–15481).

## Which elements can carry a fault path

This is the first thing to get right, because Flow Builder simply does not draw the
connector on the elements that lack the field, and an agent generating XML will happily
emit one that the deploy rejects.

| Metadata type | Flow Builder element | `faultConnector`? | Guide line |
|---|---|---|---|
| `FlowRecordCreate` | Create Records | yes | `api_meta.txt` L70965 |
| `FlowRecordUpdate` | Update Records | yes | L71283 |
| `FlowRecordDelete` | Delete Records | yes | L71046 |
| `FlowRecordLookup` | Get Records | yes | L71120 |
| `FlowActionCall` | Action (Apex, email, Chatter, External Service, local action) | yes | L68476 |
| `FlowApexPluginCall` | legacy Apex plug-in | yes | L69688 |
| `FlowWait` | Pause | yes — "If any of the wait events fail, the flow takes the fault connector" | L72993 |
| `FlowSubflow` | Subflow | **no** — the field list is `connector`, `flowName`, `inputAssignments`, `outputAssignments`, `storeOutputAutomatically` | L72625–72660 |
| `FlowAssignment` | Assignment | no | L69729 |
| `FlowDecision` | Decision | no — `connector` / `defaultConnector` only | L70225–70240 |
| `FlowLoop` | Loop | no — `nextValueConnector` / `noMoreValuesConnector` only | L70698–70715 |
| `FlowScreen` | Screen | no | L71427 |
| `FlowCustomError` | Custom Error | no — it *is* the error | L70006 |
| `FlowRecordRollback` | Roll Back Records | no; **screen flows only** | L71253–71256 |
| `FlowOrchestratedStage` | Orchestration stage | field exists but the guide says **"Not used."** | L70803 |

The two rows that catch people: **Subflow has no fault connector at all**, and
**Orchestration stages have the field but it is inert**.

---

## Assumed org model

| Component | Type | Used by |
|---|---|---|
| `Invoice__c` | Custom object — `Status__c` (picklist), `Balance_Due__c` (currency), `Write_Off_Reason__c` (text), `Account__c` (lookup) | Flows 1 and 2 |
| `Payment__c` | Custom object — `Invoice__c` (lookup), `Amount__c` (currency), `Posted__c` (checkbox) | Flow 3 |
| `Application_Log__c` | Custom object — `Source__c`, `Severity__c`, `Message__c`, `Element__c`, `Related_Record_Id__c` | every fault path; the object `templates/flow/FaultPath_Template.md` and `templates/apex/ApplicationLogger.cls` both write to |
| `Collections_Alert__e` | Platform event — `Message__c`, `Source__c`, with `publishBehavior` = `PublishImmediately` | Flow 2's last-resort notification |

`templates/flow/FaultPath_Template.md` is the shape all three fault paths fill in — capture
`{!$Flow.FaultMessage}`, write one `Application_Log__c` row, show the user something they
can act on. What that template states as a checklist, the XML below states as deployable
metadata: its four numbered steps map to `Capture_*` (assignment) → `Log_*`
(`recordCreates`) → `Notify_*` / `Show_*` → End, in that order, in every flow here.
The template's `Request_Id__c = {!$Flow.InterviewGuid}` line is *not* reproduced below —
**UNVERIFIED (2026-09-05): `$Flow.InterviewGuid` does not appear in `api_meta.txt`,
`object_reference.txt` or `apexdev.txt`.** The correlation key used here is
`Related_Record_Id__c`, set from a record id the flow already holds.

---

## 1. Screen flow — `Invoice_Write_Off_Request.flow-meta.xml`

A user writes off an invoice. The Update can fail on a validation rule, a record lock, or
field-level security. The fault path does four things in order: capture the diagnostic,
log it, **roll back** the partial work, then show a message the user can act on.

`recordRollbacks` is the reason this pattern belongs in a screen flow and nowhere else:
"Rolls back the current transaction and cancels its pending record changes… **Available
only in screen flows**" (`api_meta.txt` L71253–71256).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Capture_Write_Off_Fault</name>
        <label>Capture Write Off Fault</label>
        <locationX>380</locationX>
        <locationY>470</locationY>
        <assignmentItems>
            <assignToReference>faultDetail</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>userMessage</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>We could not write off this invoice. Nothing was changed. Check that the invoice is still open, then try again or contact Collections.</stringValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Log_Write_Off_Failure</targetReference>
        </connector>
    </assignments>
    <description>Screen flow. Writes off an invoice; every fault lands on a logged, rolled-back, user-safe path.</description>
    <environments>Default</environments>
    <interviewLabel>Invoice Write Off {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Invoice Write Off Request</label>
    <processType>Flow</processType>
    <recordCreates>
        <name>Log_Write_Off_Failure</name>
        <label>Log Write Off Failure</label>
        <locationX>380</locationX>
        <locationY>590</locationY>
        <connector>
            <targetReference>Roll_Back_Write_Off</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Roll_Back_Write_Off</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Invoice_Write_Off_Request</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Element__c</field>
            <value>
                <stringValue>Write_Off_Invoice</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>ERROR</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>faultDetail</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Related_Record_Id__c</field>
            <value>
                <elementReference>recordId</elementReference>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordRollbacks>
        <name>Roll_Back_Write_Off</name>
        <label>Roll Back Write Off</label>
        <locationX>380</locationX>
        <locationY>710</locationY>
        <connector>
            <targetReference>Show_Failure</targetReference>
        </connector>
    </recordRollbacks>
    <recordUpdates>
        <name>Write_Off_Invoice</name>
        <label>Write Off Invoice</label>
        <locationX>176</locationX>
        <locationY>350</locationY>
        <connector>
            <targetReference>Show_Success</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Capture_Write_Off_Fault</targetReference>
        </faultConnector>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>recordId</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Status__c</field>
            <value>
                <stringValue>Written Off</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Write_Off_Reason__c</field>
            <value>
                <elementReference>Collect_Reason.writeOffReason</elementReference>
            </value>
        </inputAssignments>
        <object>Invoice__c</object>
    </recordUpdates>
    <screens>
        <name>Collect_Reason</name>
        <label>Collect Reason</label>
        <locationX>176</locationX>
        <locationY>230</locationY>
        <allowBack>false</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <connector>
            <targetReference>Write_Off_Invoice</targetReference>
        </connector>
        <fields>
            <name>writeOffReason</name>
            <dataType>String</dataType>
            <fieldText>Why are you writing off this invoice?</fieldText>
            <fieldType>InputField</fieldType>
            <isRequired>true</isRequired>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>
    <screens>
        <name>Show_Failure</name>
        <label>Show Failure</label>
        <locationX>380</locationX>
        <locationY>830</locationY>
        <allowBack>false</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <fields>
            <name>failureText</name>
            <fieldText>{!userMessage}</fieldText>
            <fieldType>DisplayText</fieldType>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>
    <screens>
        <name>Show_Success</name>
        <label>Show Success</label>
        <locationX>176</locationX>
        <locationY>470</locationY>
        <allowBack>false</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <fields>
            <name>successText</name>
            <fieldText>Invoice written off.</fieldText>
            <fieldType>DisplayText</fieldType>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Collect_Reason</targetReference>
        </connector>
    </start>
    <status>Draft</status>
    <variables>
        <name>faultDetail</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>recordId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>userMessage</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

### How to read it

- **`<processType>Flow</processType>`** is the screen flow — "A flow that requires user
  interaction because it contains one or more screens… In the UI and Salesforce Help,
  it's a screen flow" (`api_meta.txt` L68198+, the `FlowProcessType` enumeration). It is
  what makes `recordRollbacks` legal here.
- **`<faultConnector>` on `Write_Off_Invoice`** is a `FlowConnector`, so its only
  meaningful child is `<targetReference>` (`api_meta.txt` L70147–70158). It is not a
  different shape from `<connector>`; it is the same type on a different field.
- **`$Flow.FaultMessage` is captured first, before anything else runs.** The Lightning Web
  Components Developer Guide is the one place in these sources that states the mechanism
  outright: when an element fails "the flow takes the… fault connector and sets the error
  message to `$Flow.FaultMessage`" (`lwc_guide.txt` L8839). It is set *by taking the fault
  connector* — so it is meaningful only on the fault branch, and the first thing on that
  branch should be the assignment that preserves it.
- **`Log_Write_Off_Failure` has its own `faultConnector`, pointing at the same rollback.**
  A fault path that writes a record is itself a DML element and can fail for exactly the
  reasons the original element did — a governor limit that is already exhausted does not
  refill for the error handler. Without this line, a failing log write is an unhandled
  fault and you lose both the change and the diagnostic.
- **`Roll_Back_Write_Off` runs before the screen, not after.** `FlowRecordRollback`
  "rolls back the current transaction and cancels its pending record changes"
  (`api_meta.txt` L71253). Roll back first so the user is not looking at an error message
  while a half-applied change is still pending.
- **`{!userMessage}` on the screen, `faultDetail` in the log.** The raw text never reaches
  `Show_Failure`. For a local action the default is *"An error occurred when the
  elementName element tried to execute the c-myComponent component"* (`lwc_guide.txt`
  L8840) — accurate, and useless to a collections clerk.
- **`storeOutputAutomatically` on the create** is available in API 48.0 and later
  (`api_meta.txt` L71015+); it is what lets you reference the new log's id downstream
  without declaring a variable.

---

## 2. Autolaunched flow — `Post_Collections_Batch.flow-meta.xml`

Called from Apex or the Invocable Actions REST resource. No user is present, so the fault
path's whole job is to leave evidence: an `Application_Log__c` row, a Chatter post to the
collections group, and — if even the log write fails — a platform event that survives the
rollback.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionCalls>
        <name>Notify_Collections_Group</name>
        <label>Notify Collections Group</label>
        <locationX>500</locationX>
        <locationY>710</locationY>
        <actionName>chatterPost</actionName>
        <actionType>chatterPost</actionType>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>text</name>
            <value>
                <elementReference>alertMessage</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>subjectNameOrId</name>
            <value>
                <elementReference>collectionsGroupId</elementReference>
            </value>
        </inputParameters>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </actionCalls>
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Capture_Read_Fault</name>
        <label>Capture Read Fault</label>
        <locationX>700</locationX>
        <locationY>350</locationY>
        <assignmentItems>
            <assignToReference>faultDetail</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>faultElement</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Get_Overdue_Invoices</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>alertMessage</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Collections batch could not read overdue invoices. No invoices were moved. See Application Log.</stringValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Log_Batch_Failure</targetReference>
        </connector>
    </assignments>
    <assignments>
        <name>Capture_Write_Fault</name>
        <label>Capture Write Fault</label>
        <locationX>500</locationX>
        <locationY>470</locationY>
        <assignmentItems>
            <assignToReference>faultDetail</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>faultElement</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Mark_Invoices_In_Collections</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>alertMessage</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Collections batch could not update invoices. The batch was rolled back. See Application Log.</stringValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Log_Batch_Failure</targetReference>
        </connector>
    </assignments>
    <description>Autolaunched. Moves overdue invoices to Collections; both fallible elements route to one discriminated fault tail.</description>
    <environments>Default</environments>
    <interviewLabel>Post Collections Batch {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Post Collections Batch</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Batch_Failure</name>
        <label>Log Batch Failure</label>
        <locationX>500</locationX>
        <locationY>590</locationY>
        <connector>
            <targetReference>Notify_Collections_Group</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Raise_Collections_Alert</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Post_Collections_Batch</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Element__c</field>
            <value>
                <elementReference>faultElement</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>ERROR</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>faultDetail</elementReference>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordCreates>
        <name>Raise_Collections_Alert</name>
        <label>Raise Collections Alert</label>
        <locationX>700</locationX>
        <locationY>710</locationY>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Post_Collections_Batch</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>faultDetail</elementReference>
            </value>
        </inputAssignments>
        <object>Collections_Alert__e</object>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordCreates>
    <recordLookups>
        <name>Get_Overdue_Invoices</name>
        <label>Get Overdue Invoices</label>
        <locationX>176</locationX>
        <locationY>230</locationY>
        <connector>
            <targetReference>Mark_Invoices_In_Collections</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Capture_Read_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Overdue</stringValue>
            </value>
        </filters>
        <filters>
            <field>Balance_Due__c</field>
            <operator>GreaterThan</operator>
            <value>
                <numberValue>0.0</numberValue>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <object>Invoice__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Mark_Invoices_In_Collections</name>
        <label>Mark Invoices In Collections</label>
        <locationX>176</locationX>
        <locationY>350</locationY>
        <faultConnector>
            <targetReference>Capture_Write_Fault</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Status__c</field>
            <value>
                <stringValue>In Collections</stringValue>
            </value>
        </inputAssignments>
        <inputReference>Get_Overdue_Invoices</inputReference>
        <object>Invoice__c</object>
    </recordUpdates>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Overdue_Invoices</targetReference>
        </connector>
    </start>
    <status>Draft</status>
    <variables>
        <name>alertMessage</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>collectionsGroupId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>faultDetail</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>faultElement</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

### How to read it

- **Two fault connectors, one tail, and `faultElement` is what makes that safe.** Both
  `Capture_*` assignments set `faultElement` to the name of the element that failed before
  they hand off to `Log_Batch_Failure`. Merging fault paths saves elements; merging them
  *without* a discriminator produces a log table where every row says "the batch failed"
  and none says where.
- **`Mark_Invoices_In_Collections` has no `<connector>` — only a `<faultConnector>`.** On
  the success path it is the end of the flow. A fault connector is not a substitute for a
  success connector and does not imply one; they are independent fields on the node.
- **The update takes `inputReference`, not `filters`.** `Get_Overdue_Invoices` stores its
  collection automatically, so the update operates on that collection in one DML statement
  (`FlowRecordUpdate.inputReference`, `api_meta.txt` L71283+). One Get and one Update for
  the whole batch is the difference between two statements and 2N.
- **`Raise_Collections_Alert` is the fault path's fault path, and it is a platform event
  rather than a record for one specific reason.** `publishBehavior` on the event
  definition decides whether the message survives: `PublishImmediately` means "published
  when the publish call executes, **regardless of whether the transaction succeeds**",
  `PublishAfterCommit` means "if the transaction fails, the event message isn't published"
  (`api_meta.txt` L42206–42229, API 46.0+). The default when the field is omitted is
  `PublishImmediately`. An alert event declared `PublishAfterCommit` is silent in exactly
  the case you built it for.
- **`Notify_Collections_Group` uses `chatterPost`, not an email action, deliberately.**
  Email is post-commit work: sending email is step 20 of the save order, after "Commits
  all DML operations to the database" at step 19 (`apexdev.txt` L15478–15487). A fault
  path that ends in a rolled-back transaction never reaches step 19, so the email is never
  sent. The Chatter post shares that exposure; `Raise_Collections_Alert` is the layer that
  does not.
- **`flowTransactionModel` is `Required` on `FlowActionCall`** (`api_meta.txt` L68479,
  API 51.0+). `CurrentTransaction` keeps the action in the same transaction;
  `NewTransaction` creates one before the action executes. If you want a notification to
  outlive the caller's rollback, `NewTransaction` is the field that says so — not a
  comment in the description.
- **No `triggerType` on `<start>`.** "If you exclude this field, the flow has no trigger
  and starts only when a user or app launches the flow" (`api_meta.txt` L72496).

---

## 3. Record-triggered before-save — `Payment_BeforeSave_Guard.flow-meta.xml`

A before-save flow on `Payment__c`. It has no DML of its own — only a Get Records, a
Decision, and assignments to `$Record` — so its *only* fallible element is the Get. Both
failure shapes land on a **Custom Error** element, which "roll[s] back a change that
triggered a flow and inform[s] the user exactly what caused the error" (`api_meta.txt`
L70007).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Capture_Lookup_Fault</name>
        <label>Capture Lookup Fault</label>
        <locationX>560</locationX>
        <locationY>470</locationY>
        <assignmentItems>
            <assignToReference>faultDetail</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </assignmentItems>
    </assignments>
    <assignments>
        <name>Flag_Overpayment</name>
        <label>Flag Overpayment</label>
        <locationX>320</locationX>
        <locationY>590</locationY>
        <assignmentItems>
            <assignToReference>guardReason</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Overpayment</stringValue>
            </value>
        </assignmentItems>
    </assignments>
    <assignments>
        <name>Mark_Payment_Postable</name>
        <label>Mark Payment Postable</label>
        <locationX>120</locationX>
        <locationY>470</locationY>
        <assignmentItems>
            <assignToReference>$Record.Posted__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </assignmentItems>
    </assignments>
    <customErrors>
        <name>Invoice_Unreadable</name>
        <label>Invoice Unreadable</label>
        <locationX>560</locationX>
        <locationY>350</locationY>
        <connector>
            <targetReference>Capture_Lookup_Fault</targetReference>
        </connector>
        <customErrorMessages>
            <errorMessage>We could not read the invoice this payment points to, so the payment was not saved. Check that the invoice still exists and that you have access to it.</errorMessage>
            <isFieldError>false</isFieldError>
        </customErrorMessages>
        <description>Fault target for Get_Parent_Invoice. Blocks the save rather than posting a payment against an unknown balance.</description>
    </customErrors>
    <customErrors>
        <name>Overpayment_Blocked</name>
        <label>Overpayment Blocked</label>
        <locationX>320</locationX>
        <locationY>470</locationY>
        <connector>
            <targetReference>Flag_Overpayment</targetReference>
        </connector>
        <customErrorMessages>
            <errorMessage>This payment is larger than the invoice balance. Reduce the amount or split it across invoices.</errorMessage>
            <fieldSelection>Amount__c</fieldSelection>
            <isFieldError>true</isFieldError>
        </customErrorMessages>
    </customErrors>
    <decisions>
        <name>Check_Balance</name>
        <label>Check Balance</label>
        <locationX>176</locationX>
        <locationY>350</locationY>
        <defaultConnector>
            <targetReference>Mark_Payment_Postable</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Within Balance</defaultConnectorLabel>
        <rules>
            <name>Exceeds_Balance</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Amount__c</leftValueReference>
                <operator>GreaterThan</operator>
                <rightValue>
                    <elementReference>Get_Parent_Invoice.Balance_Due__c</elementReference>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Overpayment_Blocked</targetReference>
            </connector>
            <label>Exceeds Balance</label>
        </rules>
    </decisions>
    <description>Before-save guard on Payment__c. The Get Records fault path and the business-rule branch both end in a Custom Error that blocks the save.</description>
    <environments>Default</environments>
    <interviewLabel>Payment BeforeSave Guard {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Payment BeforeSave Guard</label>
    <processType>AutoLaunchedFlow</processType>
    <recordLookups>
        <name>Get_Parent_Invoice</name>
        <label>Get Parent Invoice</label>
        <locationX>176</locationX>
        <locationY>230</locationY>
        <connector>
            <targetReference>Check_Balance</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Invoice_Unreadable</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Invoice__c</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <object>Invoice__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Parent_Invoice</targetReference>
        </connector>
        <object>Payment__c</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordBeforeSave</triggerType>
    </start>
    <status>Draft</status>
    <triggerOrder>10</triggerOrder>
    <variables>
        <name>faultDetail</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>guardReason</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

### How to read it

- **`<processType>AutoLaunchedFlow</processType>` with
  `<triggerType>RecordBeforeSave</triggerType>`.** `triggerType` is "Available only when
  `processType` is `AutoLaunchedFlow` or `PromptFlow`" (`api_meta.txt` L72551+) —
  record-triggered flows are autolaunched flows with a trigger, not a distinct process
  type. `recordTriggerType` takes `Create`, `Update`, `CreateAndUpdate`, `Delete`, `None`
  (L72448+).
- **Both `customErrors` elements carry a `<connector>` because the guide marks that field
  `Required`** (`api_meta.txt` L70013). Flow Builder draws Custom Error as a terminal
  element with nothing after it, which is why hand-written and generated XML tends to omit
  it. *UNVERIFIED (2026-09-05): the guide states the field is Required but does not say
  whether a deploy without it is rejected — supplying a harmless assignment costs nothing
  and removes the question.* The two targets here are deliberately DML-free: the
  transaction is being rolled back, so a log write on this branch would be discarded.
- **`isFieldError` chooses the two very different UIs.** `true` "indicates that the custom
  error message displays inline on a field"; `false` means "it displays in a window on a
  record page", and the default is `false` (`api_meta.txt` L70037–70040). `fieldSelection`
  names the field for the inline case (L70034). `Overpayment_Blocked` puts the message on
  `Amount__c` where the user's cursor already is; `Invoice_Unreadable` is a page-level
  window because no single field is at fault.
- **Why a Custom Error and not a fault path that "handles" the failure.** The guide's own
  sentence for `FlowCustomError` is "roll back a change that triggered a flow" — the
  element's purpose is to *stop* the save. A fault path that swallows an unreadable parent
  invoice and lets the payment save posts money against an unknown balance.
- **This flow has no `recordCreates` / `recordUpdates` / `recordDeletes` / `actionCalls`.**
  Before-save flows run at save-order step 3, before before-triggers (step 4) and before
  the record is written at step 7 (`apexdev.txt` L15440, L15447). Assignments to `$Record`
  persist as part of that same save with no second DML. Note the consequence for fault
  design: custom validation rules run at step 5 (`apexdev.txt` L15442), *after* this flow — so it can hand
  a value to a validation rule that then rejects it, and that rejection is not a fault
  this flow can catch.
- **`triggerOrder`** takes 1–2,000 and is available in API 54.0 and later
  (`api_meta.txt` L68438+). Set it before a second flow lands on `Payment__c`, not after.

---

## 4. Asserting the guard — `Payment_BeforeSave_Guard_Overpayment.flowtest-meta.xml`

`FlowTest` covers "record-triggered, autolaunched, or Data Cloud-triggered flow[s]"
(`api_meta.txt` L73961–73962), so flow 3 is testable and flow 1 is not. Components have
the suffix `.flowtest` and live in the `flowtests` folder (L73976); in a Salesforce DX
source tree that is `flowtests/<Name>.flowtest-meta.xml`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>A payment larger than the invoice balance must raise the Overpayment_Blocked custom error and block the save.</description>
    <flowApiName>Payment_BeforeSave_Guard</flowApiName>
    <label>Payment BeforeSave Guard - Overpayment Blocks Save</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Amount__c&quot;:5000,&quot;Posted__c&quot;:false}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>$Record</leftValueReference>
                <operator>HasError</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>The overpayment guard did not fire; the payment was allowed to save.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>guardReason</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Overpayment</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>The flow ended somewhere other than the Overpayment_Blocked branch.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

### How to read it

- **`HasError` is the operator that makes a fault branch assertable.** It is a
  `FlowComparisonOperator` value "available in API version 64.0 and later"
  (`api_meta.txt` L74203 in the `FlowTestCondition` table, and L70087 in the general
  operator list). Below API 64.0 there is no way to assert "this run raised an error", and
  the only assertable evidence is a side effect the branch left behind.
  *UNVERIFIED (2026-09-05): the guide lists `HasError` and its version floor but does not
  define its semantics or which references it accepts on the left side.* The second
  assertion exists for that reason — `guardReason` is a plain string check that pins the
  same branch without depending on `HasError` behaving as read.
- **Two assertions, one test point.** "If one assertion evaluates to `false`, the test run
  fails" (`api_meta.txt` L74158), and "if one condition evaluates to `false`, the assertion
  fails" (L74182). Splitting them means the failure message tells you which half broke.
- **`errorMessage` is what appears in Flow Builder** when the condition is false
  (`api_meta.txt` L74176). Write it as the diagnosis, not as a restatement of the
  assertion.
- **`<testType>WithAssertion</testType>` is `Required` and available in API 66.0 and
  later** (`api_meta.txt` L74041–74048). Deploying this file against an older
  `package.xml` version drops the element.
- **Only `InputTriggeringRecordInitial` is supplied**, because this is the create case.
  For an update scenario the guide's sample supplies `InputTriggeringRecordInitial` *and*
  `InputTriggeringRecordUpdated` (L74341–74393) — the pair is what lets `IsChanged` and
  entry criteria evaluate.

---

## 5. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Application_Log__c</members>
        <members>Collections_Alert__e</members>
        <members>Invoice__c</members>
        <members>Payment__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Invoice_Write_Off_Request</members>
        <members>Payment_BeforeSave_Guard</members>
        <members>Post_Collections_Batch</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Payment_BeforeSave_Guard_Overpayment</members>
        <name>FlowTest</name>
    </types>
    <version>66.0</version>
</Package>
```

`66.0` is not decoration: `FlowTest.testType` and `flowTestDataSources` are API 66.0 and
later (`api_meta.txt` L74041+, L74000+), and the guide's own `FlowTest` sample manifest
uses `<version>66.0</version>` (L74450–74457).

---

## 6. Deploy order

```bash
# 0. lint before anything reaches an org — this is the check the deploy will not do for you
python3 skills/flow/fault-handling/scripts/check_flow_faults.py \
  --manifest-dir force-app/main/default

# 1. check-only validation of the whole manifest; nothing is committed
sf project deploy start --manifest manifest/package.xml --dry-run --test-level NoTestRun

# 2. the objects and the platform event first. A flow that references Application_Log__c
#    before that object exists fails at deploy time, and a flow whose fault path cannot
#    be deployed is a flow with no fault path.
sf project deploy start \
  --metadata CustomObject:Application_Log__c \
  --metadata CustomObject:Collections_Alert__e \
  --metadata CustomObject:Invoice__c \
  --metadata CustomObject:Payment__c

# 3. the three flows, as Draft
sf project deploy start \
  --metadata Flow:Invoice_Write_Off_Request \
  --metadata Flow:Post_Collections_Batch \
  --metadata Flow:Payment_BeforeSave_Guard

# 4. the flow test, then run it from Setup > Flows > Payment BeforeSave Guard > View Tests
sf project deploy start --metadata FlowTest:Payment_BeforeSave_Guard_Overpayment

# 5. activate deliberately: flip <status> to Active and redeploy, one flow at a time
sf project deploy start --metadata Flow:Payment_BeforeSave_Guard

# retrieve the set back to see what actually landed, including version numbers
sf project retrieve start --manifest manifest/package.xml
```

Deploy the flows as `Draft` first. "Any flow without a `status` value is deployed or
retrieved with a `status` value of `Draft`" (`api_meta.txt` L73187), and `FlowVersionStatus`
takes `Active`, `Draft`, `Obsolete`, `InvalidDraft`, `UnderReview` (L68416+). A fault path
you have not exercised should not be the active version.

---

## 7. Verification

**Setup.** Setup > Process Automation > **Process Automation Settings**. Read the *Send
Process or Flow Error Email to* field. This is the setting the metadata calls
`enableFlowUseApexExceptionEmail`: `false` (the default) sends process and flow error
emails to "the user who last modified the process or flow"; `true` sends them to "the
addresses set on the Apex Exception Email page in Setup" (`api_meta.txt` L116961–116972).
Setup > **Apex Exception Email** is where those addresses live, and the Apex Developer
Guide confirms those recipients "can also receive process or flow error emails"
(`apexdev.txt` L39598–39601).

Check it, because the default is the trap: the recipient is whoever touched the flow last,
which after a release is often a consultant who no longer has a licence.

**SOQL — did the fault path actually write?** Force a failure in a sandbox (deactivate a
required lookup, or add a validation rule the flow's update will trip), run each flow
once, then read the log:

```sql
SELECT Id, CreatedDate, Source__c, Element__c, Severity__c,
       Message__c, Related_Record_Id__c
FROM Application_Log__c
WHERE Source__c IN ('Invoice_Write_Off_Request', 'Post_Collections_Batch')
  AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

Three shapes to read for:

- **No rows at all** after a forced failure means the fault connector is missing, or the
  fault path itself failed and the whole transaction — log row included — rolled back.
  That is the case `Raise_Collections_Alert` exists for; check the event next.
- **Rows with a populated `Message__c` but a null `Element__c`** mean fault paths merged
  without a discriminator. You know something broke and not where.
- **A row for `Invoice_Write_Off_Request`** is expected to survive: it is written *before*
  `Roll_Back_Write_Off` runs. *UNVERIFIED (2026-09-05): whether a `recordRollbacks`
  element discards a log row created earlier in the same interview is not stated in
  `api_meta.txt` L71253–71256, which says only that it "rolls back the current transaction
  and cancels its pending record changes". Confirm in a sandbox before relying on the log
  row surviving a screen-flow rollback; if it does not, move that log write to a platform
  event as in flow 2.*

**Runtime — is `$Flow.FaultMessage` leaking to users?** Open `Invoice_Write_Off_Request`
in Flow Builder and confirm the only screen a user can reach on the fault branch renders
`{!userMessage}`. The checker enforces the machine-readable half of this:

```bash
python3 skills/flow/fault-handling/scripts/check_flow_faults.py \
  --manifest-dir force-app/main/default
```

It exits non-zero on a fault-capable element with no `faultConnector`, a `faultConnector`
pointing at an element that does not exist, DML on a fault path with no fault path of its
own, `$Flow.FaultMessage` referenced outside a fault branch, `recordRollbacks` in a
non-screen flow, and `customErrors` in a flow that is not record-triggered.
