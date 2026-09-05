# Metadata Examples — Approval Processes

Deployable shapes for `ApprovalProcess` and the workflow actions it references. Element names, enum values, and the skeleton come from the Metadata API Developer Guide (v62 PDF, `ApprovalProcess` and `Workflow` sections); the worked example below extends the guide's own sample definition into a realistic two-step Opportunity discount approval. Verification SOQL comes from the Object Reference (`ProcessInstance`, `ProcessInstanceWorkitem`, `ProcessDefinition`).

Lint the tree before deploying:

```bash
python3 skills/admin/approval-processes/scripts/check_approval_design.py --manifest-dir force-app/main/default
```

## Where the files live

| Type | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| Approval process | `ApprovalProcess`, member `<Object>.<Name>` | `approvalProcesses/Opportunity.Discount_Approval.approvalProcess-meta.xml` | 28.0+ |
| The actions it fires | `Workflow`, member `<Object>` | `workflows/Opportunity.workflow-meta.xml` | 13.0+ |
| The approval-request template | `EmailTemplate`, member `Folder/Name` | `email/Sales_Approvals/Discount_Approval_Request.email-meta.xml` | — |

The guide states only that `ApprovalProcess` components "have the suffix `.approvalProcess` and are stored in the `approvalProcesses` folder". The object-qualified `<Object>.<Name>` form is inferred from the guide's own wildcard note — it rejects `Lead.*` as a way to retrieve a subset, which only makes sense if the member name is object-qualified. UNVERIFIED (2026-09-04): the guide does not spell out the DX filename mapping; if a retrieve in your org produces a different filename, trust the retrieve.

The process file holds no action definitions. `initialSubmissionActions`, `approvalActions`, `rejectionActions`, `finalApprovalActions`, `finalRejectionActions`, and `recallActions` are all `WorkflowActionReference` pointers — a `name` and a `type` — resolved against the object's workflow file at deploy time.

## Two-step Opportunity discount approval

Discounts above 20% need the owner's manager; above 40% they additionally need the deal desk. Rejection at step 2 goes back to the manager rather than killing the request. The record locks on submission and unlocks when approved.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApprovalProcess xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Deploy inactive; activate only after the workflow actions and the
         email template exist, and after process order is set in the org. -->
    <active>false</active>
    <allowRecall>true</allowRecall>

    <!-- Required. Reps file their own; deal desk files on their behalf. -->
    <allowedSubmitters>
        <type>owner</type>
    </allowedSubmitters>
    <allowedSubmitters>
        <submitter>Deal_Desk</submitter>
        <type>group</type>
    </allowedSubmitters>

    <!-- Shown to the approver, including in the mobile approval page. -->
    <approvalPageFields>
        <field>Name</field>
        <field>Owner</field>
        <field>Amount</field>
        <field>Discount_Percent__c</field>
        <field>Discount_Justification__c</field>
    </approvalPageFields>

    <!-- STEP 1: owner's manager, via the user hierarchy field declared in
         nextAutomatedApprover below. No entryCriteria: every record that
         entered the process reaches this step. No rejectBehavior is
         allowed on the first step. -->
    <approvalStep>
        <allowDelegate>true</allowDelegate>
        <assignedApprover>
            <approver>
                <type>userHierarchyField</type>
            </approver>
        </assignedApprover>
        <description>Owner's manager signs off on any discount over 20%.</description>
        <label>Manager Approval</label>
        <name>Manager_Approval</name>
        <rejectionActions>
            <action>
                <name>Notify_Submitter_Rejected</name>
                <type>Alert</type>
            </action>
        </rejectionActions>
    </approvalStep>

    <!-- STEP 2: deal desk queue plus a named backstop. FirstResponse means
         whichever responds first decides; Unanimous (the default) would
         require both. Records at 40% or under skip this step and are
         approved, because ifCriteriaNotMet is ApproveRecord. -->
    <approvalStep>
        <allowDelegate>false</allowDelegate>
        <approvalActions>
            <action>
                <name>Stamp_Deal_Desk_Reviewed</name>
                <type>FieldUpdate</type>
            </action>
        </approvalActions>
        <assignedApprover>
            <approver>
                <name>Deal_Desk_Queue</name>
                <type>queue</type>
            </approver>
            <approver>
                <name>vp.sales@acme.example</name>
                <type>user</type>
            </approver>
            <whenMultipleApprovers>FirstResponse</whenMultipleApprovers>
        </assignedApprover>
        <entryCriteria>
            <criteriaItems>
                <field>Opportunity.Discount_Percent__c</field>
                <operation>greaterThan</operation>
                <value>40</value>
            </criteriaItems>
        </entryCriteria>
        <ifCriteriaNotMet>ApproveRecord</ifCriteriaNotMet>
        <label>Deal Desk Approval</label>
        <name>Deal_Desk_Approval</name>
        <rejectBehavior>
            <type>BackToPrevious</type>
        </rejectBehavior>
        <rejectionActions>
            <action>
                <name>Notify_Submitter_Rejected</name>
                <type>Alert</type>
            </action>
        </rejectionActions>
    </approvalStep>

    <description>Discounts over 20% require manager approval; over 40% also require deal desk.</description>
    <emailTemplate>Sales_Approvals/Discount_Approval_Request</emailTemplate>
    <enableMobileDeviceAccess>false</enableMobileDeviceAccess>

    <!-- Process-level entry criteria: which records may enter at all.
         criteriaItems OR formula, never both. -->
    <entryCriteria>
        <booleanFilter>1 AND 2</booleanFilter>
        <criteriaItems>
            <field>Opportunity.Discount_Percent__c</field>
            <operation>greaterThan</operation>
            <value>20</value>
        </criteriaItems>
        <criteriaItems>
            <field>Opportunity.StageName</field>
            <operation>notEqual</operation>
            <value>Closed Won,Closed Lost</value>
        </criteriaItems>
    </entryCriteria>

    <finalApprovalActions>
        <action>
            <name>Set_Discount_Approved_True</name>
            <type>FieldUpdate</type>
        </action>
        <action>
            <name>Notify_Submitter_Approved</name>
            <type>Alert</type>
        </action>
    </finalApprovalActions>
    <!-- false: release the lock once approved so the rep can keep selling. -->
    <finalApprovalRecordLock>false</finalApprovalRecordLock>

    <finalRejectionActions>
        <action>
            <name>Set_Approval_Status_Rejected</name>
            <type>FieldUpdate</type>
        </action>
    </finalRejectionActions>
    <finalRejectionRecordLock>false</finalRejectionRecordLock>

    <initialSubmissionActions>
        <action>
            <name>Set_Approval_Status_Pending</name>
            <type>FieldUpdate</type>
        </action>
    </initialSubmissionActions>

    <label>Opportunity Discount Approval</label>

    <!-- Required for any step using approver type userHierarchyField.
         true = step 1 reads Manager on the record OWNER's user record;
         false = it reads Manager on the SUBMITTER's user record. -->
    <nextAutomatedApprover>
        <useApproverFieldOfRecordOwner>true</useApproverFieldOfRecordOwner>
        <userHierarchyField>Manager</userHierarchyField>
    </nextAutomatedApprover>

    <recallActions>
        <action>
            <name>Set_Approval_Status_Draft</name>
            <type>FieldUpdate</type>
        </action>
    </recallActions>

    <recordEditability>AdminOrCurrentApprover</recordEditability>
    <showApprovalHistory>true</showApprovalHistory>
</ApprovalProcess>
```

How to read it:

- **Step order is document order.** The array position of each `approvalStep` is the execution order, and after activation you can no longer add, delete, or reorder steps, or change reject or skip behaviour — even after deactivating the process. Get the order right before the first activation.
- **`rejectBehavior` is absent on step 1 on purpose.** It is "not allowed in the first step"; rejection there is governed by `finalRejectionActions`.
- **`ifCriteriaNotMet` on step 2 is what makes the ≤40% path work.** `ApproveRecord` approves and runs all final approval actions. `GotoNextStep` would skip to the next step, and if there is no later step the record is rejected. `RejectRecord` is only valid on the first step.
- **`whenMultipleApprovers`** defaults to `Unanimous`, so leaving it out with a queue *and* a named user would require both to approve. `FirstResponse` is the explicit choice here.
- **`userHierarchyField` needs `nextAutomatedApprover`.** Without that element on the process, no step may use that approver type at all. `Manager` is the standard hierarchy field; a custom one such as `Approver__c` works the same way.
- **`name` is omitted for `adhoc` and `userHierarchyField` approvers**, is a *username* for `user`, a *user-lookup field name* for `relatedUserField`, and a *queue name* for `queue`.
- **`criteriaItems` and `formula` are mutually exclusive** on `entryCriteria`; `booleanFilter` numbers the items in document order, and without it they are ANDed. `valueField` (comparing one field to another) is not supported in approval filter criteria.
- **`emailTemplate` is `Folder/Developer_Name`** and should be a *Classic* template — the guide notes Lightning email templates are not packageable. Omit the element to use the default approval-request template.
- **`recordEditability` is the only lock dial while pending.** `AdminOnly` restricts editing to Modify All Data / Modify All Records; `AdminOrCurrentApprover` adds the assigned approver, who must already have edit access through permissions and OWD.
- **`enableMobileDeviceAccess`** set to `true` forbids `adhoc` approvers anywhere in the process, so it is `false` here even though no step uses `adhoc` — flipping it later would be the constraint to check.

## The workflow actions the process references

Every `<action>` above must resolve to a definition in the object's workflow file. This is a separate metadata type in a separate directory, and it must be deployed first.

`workflows/Opportunity.workflow-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Workflow xmlns="http://soap.sforce.com/2006/04/metadata">
    <alerts>
        <fullName>Notify_Submitter_Approved</fullName>
        <description>Discount approved - notify the opportunity owner</description>
        <protected>false</protected>
        <recipients>
            <type>owner</type>
        </recipients>
        <senderType>CurrentUser</senderType>
        <template>Sales_Approvals/Discount_Approved</template>
    </alerts>
    <alerts>
        <fullName>Notify_Submitter_Rejected</fullName>
        <description>Discount rejected - notify the opportunity owner</description>
        <protected>false</protected>
        <recipients>
            <type>owner</type>
        </recipients>
        <senderType>OrgWideEmailAddress</senderType>
        <senderAddress>sales-ops@acme.example</senderAddress>
        <template>Sales_Approvals/Discount_Rejected</template>
    </alerts>

    <fieldUpdates>
        <fullName>Set_Approval_Status_Pending</fullName>
        <field>Approval_Status__c</field>
        <literalValue>Pending Approval</literalValue>
        <name>Set Approval Status Pending</name>
        <notifyAssignee>false</notifyAssignee>
        <operation>Literal</operation>
        <protected>false</protected>
        <reevaluateOnChange>false</reevaluateOnChange>
    </fieldUpdates>
    <fieldUpdates>
        <fullName>Set_Approval_Status_Draft</fullName>
        <field>Approval_Status__c</field>
        <literalValue>Draft</literalValue>
        <name>Set Approval Status Draft</name>
        <notifyAssignee>false</notifyAssignee>
        <operation>Literal</operation>
        <protected>false</protected>
        <reevaluateOnChange>false</reevaluateOnChange>
    </fieldUpdates>
    <fieldUpdates>
        <fullName>Set_Approval_Status_Rejected</fullName>
        <field>Approval_Status__c</field>
        <literalValue>Rejected</literalValue>
        <name>Set Approval Status Rejected</name>
        <notifyAssignee>false</notifyAssignee>
        <operation>Literal</operation>
        <protected>false</protected>
        <reevaluateOnChange>false</reevaluateOnChange>
    </fieldUpdates>
    <fieldUpdates>
        <fullName>Set_Discount_Approved_True</fullName>
        <field>Discount_Approved__c</field>
        <literalValue>true</literalValue>
        <name>Set Discount Approved</name>
        <notifyAssignee>false</notifyAssignee>
        <operation>Literal</operation>
        <protected>false</protected>
        <reevaluateOnChange>false</reevaluateOnChange>
    </fieldUpdates>
    <fieldUpdates>
        <fullName>Stamp_Deal_Desk_Reviewed</fullName>
        <field>Deal_Desk_Reviewed_On__c</field>
        <formula>NOW()</formula>
        <name>Stamp Deal Desk Reviewed</name>
        <notifyAssignee>false</notifyAssignee>
        <operation>Formula</operation>
        <protected>false</protected>
        <reevaluateOnChange>false</reevaluateOnChange>
    </fieldUpdates>
</Workflow>
```

How to read it:

- `fullName` on an alert or field update is the string the approval process's `<action><name>` must match, exactly.
- `description`, `protected`, and `template` are all required on a `WorkflowAlert`; `field`, `fullName`, `name`, `notifyAssignee`, `operation`, and `protected` are required on a `WorkflowFieldUpdate`.
- An alert needs `recipients` or `ccEmails` (or both) to send at all; `ccEmails` caps at five addresses.
- `senderType` `OrgWideEmailAddress` requires `senderAddress` to be a verified org-wide address in the *target* org — a common cause of a deploy that passes and an email that never arrives.
- `operation` decides which value element is read: `Literal` → `literalValue`, `Formula` → `formula`, `LookupValue` → `lookupValue` + `lookupValueType` (only `User` is supported), plus `Null`, `NextValue`, and `PreviousValue` (picklists only).
- `reevaluateOnChange` is left `false` deliberately. Set to `true` it re-evaluates every workflow rule on the object, and that cascade can chain up to five times.
- The approval action `type` enum also contains `FlowAction`, but that is the closed flow-trigger pilot. To run a Flow off an approval outcome, have the approval fire a `FieldUpdate` and put a record-triggered Flow on that field (`flow/orchestration-flows`, `admin/flow-for-admins`).

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity.Discount_Approval</members>
        <name>ApprovalProcess</name>
    </types>
    <types>
        <members>Opportunity</members>
        <name>Workflow</name>
    </types>
    <types>
        <members>Sales_Approvals/Discount_Approval_Request</members>
        <members>Sales_Approvals/Discount_Approved</members>
        <members>Sales_Approvals/Discount_Rejected</members>
        <name>EmailTemplate</name>
    </types>
    <version>62.0</version>
</Package>
```

The `*` wildcard on `ApprovalProcess` retrieves every approval process for every object. It cannot retrieve a subset — `Lead.*` is not supported — so to pull one object's processes you must name each one.

## Retrieve, lint, deploy

```bash
# 1. Pull what the org has today, before editing anything
sf project retrieve start \
  --metadata ApprovalProcess:Opportunity.Discount_Approval Workflow:Opportunity \
  --target-org my-sandbox

# 2. Lint the tree
python3 skills/admin/approval-processes/scripts/check_approval_design.py \
  --manifest-dir force-app/main/default

# 3. Deploy the actions and templates FIRST - the process references them by name
sf project deploy start \
  --source-dir force-app/main/default/email \
  --source-dir force-app/main/default/workflows \
  --target-org my-sandbox

# 4. Validate the process without committing it
sf project deploy validate --manifest manifest/package.xml --target-org my-sandbox

# 5. Deploy the process (still <active>false</active>)
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
```

Then, in the target org: **set the process order by hand** before activating. The metadata does not include the order of active approval processes, and the guide says outright that you sometimes have to reorder them in the destination org after deployment. Order decides which process a record enters when more than one matches.

## Submitting from Apex — the ten-line version

Full coverage of `Approval.ProcessSubmitRequest`, `ProcessWorkitemRequest`, bulk submission, `lock` / `unlock` / `isLocked`, and test patterns lives in `admin/approval-process-apex-patterns`. The minimum that proves a process is reachable:

```apex
Approval.ProcessSubmitRequest req = new Approval.ProcessSubmitRequest();
req.setObjectId(oppId);
req.setComments('Submitted by the discount desk.');
// Name it explicitly, or leave it null and let process order decide.
req.setProcessDefinitionNameOrId('Opportunity_Discount_Approval');
req.setSkipEntryCriteria(false);
Approval.ProcessResult result = Approval.process(req);
System.assert(result.isSuccess());
System.assertEquals('Pending', result.getInstanceStatus());
Id workItemId = result.getNewWorkitemIds()[0];
```

If `setProcessDefinitionNameOrId` is left null, submission "evaluates entry criteria for all processes applicable to the submitter", ordered by the org's process order, and submits to the first that matches. `setSkipEntryCriteria(true)` only has an effect when a process is named; otherwise it is ignored. Note that `Approval.process` counts against DML limits, and record locks and unlocks are treated as DML — blocked before a callout, counted toward the limits, and rolled back with the transaction.

## Verification

Confirm which process the record actually entered, and its state:

```sql
SELECT Id, Status, TargetObjectId, SubmittedById, LastActorId,
       CompletedDate, ElapsedTimeInHours,
       ProcessDefinition.DeveloperName, ProcessDefinition.LockType,
       ProcessDefinition.State
FROM ProcessInstance
WHERE TargetObjectId = '006XXXXXXXXXXXXXXX'
ORDER BY CreatedDate DESC
```

`ProcessInstance.Status` is a restricted picklist: `Approved`, `Fault`, `Held`, `NoResponse`, `Pending`, `Reassigned`, `Rejected`, `Removed`, `Started`. `ProcessDefinition.LockType` reports the lock actually applied (`Total`, `Admin`, `Owner`, `Workitem`, `Node`, `none`), and `ProcessDefinition.State` is `Active`, `Inactive`, or `Obsolete` — useful for spotting processes that were superseded rather than deleted.

Who is holding the pending request right now:

```sql
SELECT Id, ActorId, OriginalActorId, ProcessInstanceId,
       ProcessInstance.TargetObjectId,
       ProcessInstance.ProcessDefinition.DeveloperName
FROM ProcessInstanceWorkitem
WHERE ProcessInstance.Status = 'Pending'
```

`ActorId` and `OriginalActorId` are polymorphic across `Group` and `User`, so a queue-assigned step shows a Group id — that is the correct result for the queue step above, not a bug.

Step-by-step history, using the `Steps` child relationship the Object Reference names:

```sql
SELECT Id, Status, (SELECT Id, StepStatus, Comments, ActorId, ElapsedTimeInHours FROM Steps)
FROM ProcessInstance
WHERE TargetObjectId = '006XXXXXXXXXXXXXXX'
```

Find every pending approval past its SLA — the operational query behind the "stuck approvals" gotcha:

```sql
SELECT ProcessDefinition.DeveloperName, TargetObjectId, SubmittedById,
       ElapsedTimeInDays
FROM ProcessInstance
WHERE Status = 'Pending' AND ElapsedTimeInDays > 3
ORDER BY ElapsedTimeInDays DESC
```

Setup check, for what SOQL cannot see: Setup → Process Automation → Approval Processes, filtered to the object, shows the **process order** of the active processes. That order is not in the metadata and not in `ProcessDefinition`, so it has to be read (and set) in the UI after every deploy that adds a process.
