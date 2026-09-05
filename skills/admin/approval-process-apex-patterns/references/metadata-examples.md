# Metadata Examples — Approval Process Apex Patterns

This file gives an Apex-driven approval implementation something
deterministic to run against: a **minimal, deployable test-fixture**
`ApprovalProcess`, the service class that drives it, the queries that
inspect it, and the test class that proves the failure modes.

It is deliberately not a declarative design guide. Element names,
enum values, and the skeleton come from the Metadata API Developer
Guide `ApprovalProcess` section (api_meta.txt L23057-23659); the full
multi-step design treatment — entry criteria, approver routing,
workflow actions, email templates — belongs to
`skills/admin/approval-processes/references/metadata-examples.md`.
Read that one when you are designing the process. Read this one when
you are writing the Apex.

Lint the tree before deploying:

```bash
python3 skills/admin/approval-process-apex-patterns/scripts/check_approval_process_apex_patterns.py \
    --manifest-dir force-app/main/default
```

---

## Where the files live

| Type | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| Approval process | `ApprovalProcess`, member `<Object>.<Name>` | `approvalProcesses/Expense__c.Expense_Approval.approvalProcess-meta.xml` | 28.0+ |
| Service class | `ApexClass` | `classes/ExpenseApprovalService.cls` | — |
| Test class | `ApexClass` | `classes/ExpenseApprovalServiceTest.cls` | — |

The guide states only that `ApprovalProcess` components "have the
suffix `.approvalProcess` and are stored in the `approvalProcesses`
folder" (api_meta.txt L23072-23073). UNVERIFIED (2026-09-05): the
object-qualified `<Object>.<Name>` filename is not spelled out in the
guide; it is inferred from the guide's wildcard note, which rejects
`Lead.*` as a way to retrieve a subset (api_meta.txt L23655-23659) —
a restriction that only makes sense if the member name is
object-qualified. If a retrieve in your org produces a different
filename, trust the retrieve.

---

## The test-fixture approval process

Everything in this fixture exists to make Apex behaviour observable,
and each choice maps to a question the Apex has to answer:

- **`<active>true</active>`** — required field. The `ProcessDefinition`
  preflight query below asserts `State = 'Active'`; an inactive
  process is invisible to a submission that names it.
- **`<allowRecall>true</allowRecall>`** — with `false`, "only
  administrators can recall approval requests" (api_meta.txt
  L23094-23097). True is what lets the recall test distinguish an
  Apex permission failure from a process-configuration one.
- **`<allowedSubmitters><type>allInternalUsers</type>`** — required
  field. `allInternalUsers` is "all Salesforce users in the
  organization" (api_meta.txt L23261), which is what makes
  `setSubmitterId(anyUser.Id)` succeed in a test. A production
  process should be narrower — and that narrowness is exactly what
  breaks the batch-submits-as-owner pattern (gotcha 11).
- **`<entryCriteria>`** — one filter, so `setSkipEntryCriteria(true)`
  and `false` produce visibly different outcomes.
- **Two steps, `Unanimous` on the second** — so the test can observe
  the other approver's `StepStatus` flipping to `NoResponse` on a
  rejection (object_reference.txt L226753-226766).
- **`<recordEditability>AdminOrCurrentApprover</recordEditability>`** —
  the wider of the two values, so a test approver can edit the locked
  record. `AdminOnly` restricts editing to Modify All Data / Modify
  All Records holders (api_meta.txt L23180-23196).
- **No workflow actions at all** — `initialSubmissionActions` and
  friends are `WorkflowActionReference` pointers resolved against the
  object's workflow file at deploy time. Omitting them keeps the
  fixture a single deployable file.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApprovalProcess xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <allowRecall>true</allowRecall>

    <!-- Required. Widest possible, so setSubmitterId never fails in a
         fixture. Production processes narrow this - see gotcha 11. -->
    <allowedSubmitters>
        <type>allInternalUsers</type>
    </allowedSubmitters>

    <approvalPageFields>
        <field>Name</field>
        <field>Owner</field>
        <field>Total_Amount__c</field>
    </approvalPageFields>

    <!-- STEP 1: adhoc approver. The submitter supplies the approver,
         which is what setNextApproverIds is for. No rejectBehavior is
         allowed on the first step. -->
    <approvalStep>
        <allowDelegate>false</allowDelegate>
        <assignedApprover>
            <approver>
                <type>adhoc</type>
            </approver>
        </assignedApprover>
        <description>Approver supplied by the submitting Apex.</description>
        <label>Nominated Approver</label>
        <name>Nominated_Approver</name>
    </approvalStep>

    <!-- STEP 2: two named approvers, unanimous. Entered only above
         5000, so a fixture record can be steered into one step or two. -->
    <approvalStep>
        <allowDelegate>false</allowDelegate>
        <assignedApprover>
            <approver>
                <name>finance.a@example.com</name>
                <type>user</type>
            </approver>
            <approver>
                <name>finance.b@example.com</name>
                <type>user</type>
            </approver>
            <whenMultipleApprovers>Unanimous</whenMultipleApprovers>
        </assignedApprover>
        <entryCriteria>
            <criteriaItems>
                <field>Expense__c.Total_Amount__c</field>
                <operation>greaterThan</operation>
                <value>5000</value>
            </criteriaItems>
        </entryCriteria>
        <ifCriteriaNotMet>ApproveRecord</ifCriteriaNotMet>
        <label>Finance Pair</label>
        <name>Finance_Pair</name>
        <rejectBehavior>
            <type>RejectRequest</type>
        </rejectBehavior>
    </approvalStep>

    <!-- Entry criteria for the process itself. setSkipEntryCriteria(true)
         is what bypasses this - and only when the process is named. -->
    <entryCriteria>
        <criteriaItems>
            <field>Expense__c.Total_Amount__c</field>
            <operation>greaterOrEqual</operation>
            <value>1000</value>
        </criteriaItems>
    </entryCriteria>

    <enableMobileDeviceAccess>false</enableMobileDeviceAccess>
    <finalApprovalRecordLock>false</finalApprovalRecordLock>
    <finalRejectionRecordLock>false</finalRejectionRecordLock>
    <label>Expense Approval</label>
    <recordEditability>AdminOrCurrentApprover</recordEditability>
    <showApprovalHistory>true</showApprovalHistory>
</ApprovalProcess>
```

`enableMobileDeviceAccess` must stay `false` here: "If set to true,
approval steps can't have approvers of type `adhoc`" (api_meta.txt
L23127-23129), and step 1 is `adhoc` on purpose.

---

## The Apex service class

Bulk submit with an error-row collector, workitem action without a
follow-up query, and a recall that expects to be refused.

```apex
/**
 * Drives the Expense_Approval process. Deployable against the
 * fixture ApprovalProcess in this file.
 */
public with sharing class ExpenseApprovalService {

    /** Chunk size. Not a documented governor - see gotchas.md § 7. */
    @TestVisible private static Integer CHUNK = 200;

    public class Failure {
        public Id recordId;
        public String message;
        public Failure(Id recordId, String message) {
            this.recordId = recordId;
            this.message = message;
        }
    }

    /**
     * Submits each record on behalf of its owner, allowing partial
     * success. Returns one Failure per row that did not submit.
     */
    public static List<Failure> submit(List<Expense__c> records, Id approverId) {
        List<Approval.ProcessSubmitRequest> requests =
            new List<Approval.ProcessSubmitRequest>();

        for (Expense__c e : records) {
            Approval.ProcessSubmitRequest req = new Approval.ProcessSubmitRequest();
            req.setObjectId(e.Id);
            // Developer name, never a 300-prefixed record Id.
            req.setProcessDefinitionNameOrId('Expense_Approval');
            // Must be an allowedSubmitter on the process definition.
            req.setSubmitterId(e.OwnerId);
            req.setComments('Auto-submitted by ExpenseApprovalService');
            // Step 1 is adhoc. Exactly one Id, never more.
            if (approverId != null) {
                req.setNextApproverIds(new List<Id>{ approverId });
            }
            requests.add(req);
        }

        List<Failure> failures = new List<Failure>();
        for (Integer i = 0; i < requests.size(); i += CHUNK) {
            Integer stop = Math.min(i + CHUNK, requests.size());
            List<Approval.ProcessSubmitRequest> chunk =
                new List<Approval.ProcessSubmitRequest>();
            for (Integer j = i; j < stop; j++) {
                chunk.add(requests[j]);
            }

            // Each call is ONE DML statement against the 150 limit.
            Approval.ProcessResult[] results = Approval.process(chunk, false);

            for (Integer j = 0; j < results.size(); j++) {
                if (!results[j].isSuccess()) {
                    failures.add(new Failure(
                        (Id) chunk[j].getObjectId(),
                        describe(results[j].getErrors())
                    ));
                }
            }
        }
        return failures;
    }

    /**
     * Submits and immediately approves in the same transaction.
     * getNewWorkitemIds() removes the need to re-query the workitem.
     */
    public static Approval.ProcessResult submitAndApprove(Id recordId, Id approverId) {
        Approval.ProcessSubmitRequest submitReq = new Approval.ProcessSubmitRequest();
        submitReq.setObjectId(recordId);
        submitReq.setProcessDefinitionNameOrId('Expense_Approval');
        submitReq.setNextApproverIds(new List<Id>{ approverId });
        Approval.ProcessResult submitted = Approval.process(submitReq, false);

        if (!submitted.isSuccess()) {
            return submitted;
        }
        List<Id> newWorkitems = submitted.getNewWorkitemIds();
        if (newWorkitems.isEmpty()) {
            return submitted;
        }

        Approval.ProcessWorkitemRequest actionReq =
            new Approval.ProcessWorkitemRequest();
        actionReq.setWorkitemId(newWorkitems[0]);
        actionReq.setAction('Approve');   // Approve | Reject | Removed
        actionReq.setComments('Auto-approved under policy 4.2');
        return Approval.process(actionReq, false);
    }

    /**
     * Reassigns a pending request. Plain DML on ProcessInstanceWorkitem
     * - no administrator permission required, unlike a recall.
     */
    public static void reassign(Id workitemId, Id newActorId) {
        update new ProcessInstanceWorkitem(Id = workitemId, ActorId = newActorId);
    }

    /**
     * Recalls. 'Removed' is system-administrator-only, so this is
     * written to be refused, not to be assumed.
     */
    public static Boolean recall(Id workitemId, String reason) {
        Approval.ProcessWorkitemRequest req = new Approval.ProcessWorkitemRequest();
        req.setWorkitemId(workitemId);
        req.setAction('Removed');
        req.setComments('Recalled: ' + reason);
        try {
            Approval.ProcessResult result = Approval.process(req, false);
            return result.isSuccess();
        } catch (Exception ex) {
            // Non-admin context. Park it rather than swallowing it.
            System.debug(LoggingLevel.WARN, 'Recall refused: ' + ex.getMessage());
            return false;
        }
    }

    private static String describe(Database.Error[] errors) {
        List<String> parts = new List<String>();
        for (Database.Error err : errors) {
            parts.add(err.getStatusCode() + ': ' + err.getMessage());
        }
        return String.join(parts, ' | ');
    }
}
```

---

## Pending approvals per user

The one query an operations dashboard actually needs: everything a
given approver is sitting on, aged, with the queue case separated
out. `ActorId` is polymorphic over `Group` and `User`
(object_reference.txt L226820-226835), so it needs `TYPEOF`.

```sql
SELECT Id,
       ActorId,
       ElapsedTimeInDays,
       ElapsedTimeInHours,
       ProcessInstance.TargetObjectId,
       ProcessInstance.Status,
       ProcessInstance.SubmittedById,
       ProcessInstance.ProcessDefinition.DeveloperName,
       TYPEOF Actor
           WHEN User  THEN Username, IsActive, Name
           WHEN Group THEN DeveloperName, Type
       END
FROM ProcessInstanceWorkitem
WHERE ProcessInstance.Status = 'Pending'
ORDER BY ElapsedTimeInDays DESC
```

Swap the filter for `ActorId = :someUserId` to scope it to one
approver, or add `AND ElapsedTimeInDays > 7` for the SLA-breach
sweep. Age on `ElapsedTimeInDays`, which the Object Reference
documents as Filter/Sort on this object (object_reference.txt
L226836-226846).

The completed-history counterpart, for the audit report:

```sql
SELECT Id, StepStatus, Comments, ActorId, OriginalActorId, ElapsedTimeInDays
FROM ProcessInstanceStep
WHERE ProcessInstanceId IN (
    SELECT Id FROM ProcessInstance WHERE TargetObjectId = :recordId
)
ORDER BY ElapsedTimeInDays DESC
```

`StepStatus` carries the same nine values as `ProcessInstance.Status`
— Approved, Fault, Held, NoResponse, Pending, Reassigned, Rejected,
Removed, Started (object_reference.txt L226748-226766). Filtering
that report on `StepStatus = 'Rejected'` undercounts: on a unanimous
step, one rejection sets every *other* approver's step to
`NoResponse`.

---

## Test class skeleton

The four cases that matter are the three failures plus the happy
path. Nothing here mocks `Approval.process` — it runs for real
against the deployed fixture.

```apex
@IsTest
private class ExpenseApprovalServiceTest {

    @TestSetup
    static void setup() {
        // TestDataFactory: see templates/apex/tests/TestDataFactory.
        List<Expense__c> expenses = new List<Expense__c>();
        for (Integer i = 0; i < 3; i++) {
            expenses.add(new Expense__c(
                Name = 'E-' + i,
                Total_Amount__c = 2000    // above the 1000 entry criterion
            ));
        }
        // One row deliberately BELOW entry criteria - the mixed batch.
        expenses.add(new Expense__c(Name = 'E-low', Total_Amount__c = 10));
        insert expenses;
    }

    @IsTest
    static void submitsBulkWithPartialSuccess() {
        List<Expense__c> all = [SELECT Id, OwnerId FROM Expense__c];
        Id approver = UserInfo.getUserId();

        Test.startTest();
        List<ExpenseApprovalService.Failure> failures =
            ExpenseApprovalService.submit(all, approver);
        Test.stopTest();

        // allOrNone=false: the three valid rows submitted anyway.
        Assert.areEqual(1, failures.size(),
            'Only the below-threshold row should fail');
        Assert.areEqual(3,
            [SELECT COUNT() FROM ProcessInstance WHERE Status = 'Pending'],
            'The three qualifying rows are pending');
    }

    @IsTest
    static void reportsInstanceStatusNotJustSuccess() {
        Expense__c e = [SELECT Id FROM Expense__c WHERE Total_Amount__c = 2000 LIMIT 1];

        Test.startTest();
        Approval.ProcessResult result =
            ExpenseApprovalService.submitAndApprove(e.Id, UserInfo.getUserId());
        Test.stopTest();

        Assert.isTrue(result.isSuccess(), 'Approve should succeed');
        // Assert on the status, not only the boolean.
        Assert.areEqual('Approved', result.getInstanceStatus(),
            'Single-step approval completes the instance');
    }

    @IsTest
    static void rejectsSubmitterOutsideAllowedSubmitters() {
        // Only meaningful against a process whose allowedSubmitters is
        // narrower than allInternalUsers. Point this at the production
        // process name, not the fixture, to exercise gotcha 11.
        User outsider = TestUserFactory.createUser('Standard User', new List<String>());
        Expense__c e = [SELECT Id FROM Expense__c WHERE Total_Amount__c = 2000 LIMIT 1];
        e.OwnerId = outsider.Id;

        Test.startTest();
        List<ExpenseApprovalService.Failure> failures =
            ExpenseApprovalService.submit(new List<Expense__c>{ e }, UserInfo.getUserId());
        Test.stopTest();

        Assert.areEqual(1, failures.size(),
            'A submitter outside allowedSubmitters fails its row');
    }

    @IsTest
    static void recallIsRefusedForNonAdmin() {
        Expense__c e = [SELECT Id, OwnerId FROM Expense__c WHERE Total_Amount__c = 2000 LIMIT 1];
        ExpenseApprovalService.submit(new List<Expense__c>{ e }, UserInfo.getUserId());
        ProcessInstanceWorkitem wi = [
            SELECT Id FROM ProcessInstanceWorkitem
            WHERE ProcessInstance.TargetObjectId = :e.Id
            LIMIT 1
        ];

        User standard = TestUserFactory.createUser('Standard User', new List<String>());
        Boolean recalled;
        Test.startTest();
        System.runAs(standard) {
            recalled = ExpenseApprovalService.recall(wi.Id, 'amount corrected');
        }
        Test.stopTest();

        Assert.isFalse(recalled,
            'Only system administrators can specify the Removed action');
    }
}
```

`TestUserFactory.createUser(profileName, permissionSetNames)` and
`TestDataFactory` are the repo's shared fixtures under
`templates/apex/tests/` — do not hand-roll new ones.

---

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Expense__c.Expense_Approval</members>
        <name>ApprovalProcess</name>
    </types>
    <types>
        <members>ExpenseApprovalService</members>
        <members>ExpenseApprovalServiceTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Expense__c</members>
        <name>CustomObject</name>
    </types>
    <version>62.0</version>
</Package>
```

The wildcard `*` under `ApprovalProcess` retrieves every approval
process for every object; "you can't use it to retrieve a subset.
Syntax such as `Lead.*` isn't supported" (api_meta.txt L23655-23659).

---

## Retrieve, lint, deploy

```bash
# 1. Read what the org actually has before writing any Apex against it.
sf project retrieve start \
    --metadata "ApprovalProcess:Expense__c.Expense_Approval" \
    --target-org myorg

# 2. Lint the tree - checks the fixture XML and every .cls that names a process.
python3 skills/admin/approval-process-apex-patterns/scripts/check_approval_process_apex_patterns.py \
    --manifest-dir force-app/main/default

# 3. Validate without committing, running only this skill's tests.
sf project deploy validate \
    --manifest manifest/package.xml \
    --test-level RunSpecifiedTests \
    --tests ExpenseApprovalServiceTest \
    --target-org myorg

# 4. Deploy.
sf project deploy start \
    --manifest manifest/package.xml \
    --test-level RunSpecifiedTests \
    --tests ExpenseApprovalServiceTest \
    --target-org myorg
```

The approval process is deployed `<active>true</active>` here because
it is a fixture. A production process should deploy inactive and be
activated after its workflow actions and templates exist — and, per
the Metadata API guide, "the metadata doesn't include the order of
active approval processes. Sometimes you have to reorder the approval
processes in the destination org after deployment" (api_meta.txt
L23066-23068). That reorder is a manual post-deploy step.

---

## Verification

Run these after the deploy, before trusting any Apex against the
process.

```sql
-- 1. The process the Apex names exists and is Active.
SELECT Id, DeveloperName, Name, State, TableEnumOrId, LockType, Type
FROM ProcessDefinition
WHERE DeveloperName = 'Expense_Approval'
```

Expect one row, `State = 'Active'`, `Type = 'Approval Process'`
(object_reference.txt L225398-225426). Zero rows means every
`setProcessDefinitionNameOrId('Expense_Approval')` in the codebase
fails.

```sql
-- 2. Nothing else on the object competes for a null process name.
SELECT DeveloperName, State, TableEnumOrId
FROM ProcessDefinition
WHERE TableEnumOrId = 'Expense__c' AND State = 'Active'
```

More than one row means a submission that leaves
`processDefinitionNameOrId` null is routed by org process order,
which the metadata does not carry.

```sql
-- 3. A test submission actually created an instance and a workitem.
SELECT Id, Status, SubmittedById, TargetObjectId,
       (SELECT Id, ActorId FROM Workitems)
FROM ProcessInstance
WHERE ProcessDefinition.DeveloperName = 'Expense_Approval'
ORDER BY Id DESC
```

`Workitems` is the child relationship name for
`ProcessInstanceWorkitem` on `ProcessInstance`, and `Steps` is the
child relationship for `ProcessInstanceStep` (object_reference.txt
L226220-226240).

Setup check, for anything SOQL cannot see: **Setup → Process
Automation → Approval Processes**, pick the object, and confirm the
process order — the one thing the deployed metadata does not carry.
