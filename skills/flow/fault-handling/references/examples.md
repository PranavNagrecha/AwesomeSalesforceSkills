# Flow Fault Handling — Examples

## Example 1: Record-Triggered Flow Fault Branch

Use this pattern whenever an `Update Records` or `Create Records` element can fail:

```text
[Update Records: Update Case]
    ├── Success -> [Next business step]
    └── Fault -> [Assignment: set errorDetail = {!$Flow.FaultMessage}]
                 -> [Create Records: Flow_Error_Log__c]
                 -> [Send Email / Custom Notification]
                 -> [End]
```

Why it works:
- The user-safe path and support path are separate.
- `$Flow.FaultMessage` is preserved for diagnostics.
- The batch failure is observable instead of silent.

## Example 2: Screen Flow User Message Pattern

```text
[Action or DML step]
    └── Fault -> [Assignment: userMessage = "We could not complete your request right now."]
                 -> [Assignment: supportDetail = {!$Flow.FaultMessage}]
                 -> [Screen: Friendly error + next step]
```

Rules:
- Show the user what to do next.
- Do not dump raw system text to the screen.
- Log the detailed message elsewhere for admins.

## Example 3: Bulk Review Questions for Record-Triggered Flow

Use these review prompts before approving a data-load-facing Flow:

```text
- Does the Flow query related data once per interview?
- Does any after-save path create many related records per source record?
- Does the invocable Apex behind any Action accept lists?
- If one record fails, do we understand how the batch behaves?
```

## Example 4: The review that turned a "handled" flow into a handled flow

A record-triggered flow on `Case` was signed off because every DML element had a fault
connector. It still lost errors. Here is what the reviewer found and changed — this is the
diff, not a full flow; the complete deployable versions are in
`references/metadata-examples.md`.

**Before.** Two elements, two fault connectors, one shared tail. It passes a visual review.

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata"><!-- excerpt: the elements that changed -->
<recordUpdates>
    <name>Escalate_Case</name>
    <faultConnector>
        <targetReference>Log_Failure</targetReference>
    </faultConnector>
    <object>Case</object>
</recordUpdates>
<recordCreates>
    <name>Create_Escalation_Task</name>
    <faultConnector>
        <targetReference>Log_Failure</targetReference>
    </faultConnector>
    <object>Task</object>
</recordCreates>
<recordCreates>
    <name>Log_Failure</name>
    <inputAssignments>
        <field>Message__c</field>
        <value>
            <elementReference>$Flow.FaultMessage</elementReference>
        </value>
    </inputAssignments>
    <object>Application_Log__c</object>
</recordCreates>
</Flow>
```

Three defects, none visible on the canvas:

1. `Log_Failure` writes a record and has no `faultConnector` of its own. If the original
   failure was the 150-DML ceiling (`apexdev.txt` L19554), the log write fails too and the
   run leaves nothing behind.
2. Both fault paths land on the same element with no discriminator, so `Message__c` is the
   only evidence and `Source__c` / element name are absent. Every row reads the same.
3. `$Flow.FaultMessage` is referenced directly in the log element rather than captured in
   the first element of the fault branch. That works here only because `Log_Failure` is
   reachable *only* from fault connectors — add one non-fault path into it later and every
   row silently goes blank.

**After.** One assignment per branch, a discriminator, and a fault path on the fault path.

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata"><!-- excerpt: the elements that changed -->
<assignments>
    <name>Capture_Escalate_Fault</name>
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
            <stringValue>Escalate_Case</stringValue>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Log_Failure</targetReference>
    </connector>
</assignments>
<recordCreates>
    <name>Log_Failure</name>
    <faultConnector>
        <targetReference>Raise_Ops_Alert</targetReference>
    </faultConnector>
    <inputAssignments>
        <field>Element__c</field>
        <value>
            <elementReference>faultElement</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>Message__c</field>
        <value>
            <elementReference>faultDetail</elementReference>
        </value>
    </inputAssignments>
    <object>Application_Log__c</object>
</recordCreates>
</Flow>
```

**How the reviewer proved it.** Not by re-reading the canvas — by adding a validation rule
to `Task` in a sandbox that the escalation task would trip, running the flow once per
branch, and querying:

```sql
SELECT Element__c, Severity__c, COUNT(Id) rows
FROM Application_Log__c
WHERE Source__c = 'Case_AfterSave_Escalate' AND CreatedDate = TODAY
GROUP BY Element__c, Severity__c
```

Before the change: one row, `Element__c` null. After: one row per failing element, named.
A `GROUP BY` that returns a single null-keyed row is the signature of a merged fault tail
with no discriminator, and it is the fastest way to find one in an org you did not build.

