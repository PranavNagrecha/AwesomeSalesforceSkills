# Examples: Approval Processes

---

## Example: Opportunity Discount Approval

**Requirement:** Any Opportunity with discount above 20% requires Sales Director approval before it can move to `Proposal/Quote`.

**Pattern:**
1. Entry criteria: `Discount_Percent__c > 20`
2. Approver source: `Opportunity.Owner.Manager.Manager`
3. Submission action: lock record, send email alert to approver
4. Final approval action: set `Discount_Approved__c = TRUE`
5. Final rejection action: set Stage back to `Negotiation/Review`

**Why Approval Process fits:** One object, clear approver, clear pending state, clear approve/reject outcomes.

---

## Example: Expense Approval With Amount Bands

**Requirement:** Expense requests under $1,000 go to Manager. $1,000-$10,000 go to Director. Above $10,000 goes to Finance VP after Director approval.

**Pattern:**
- Step 1: Manager approval for all submitted records
- Step 2: Director approval when `Amount__c >= 1000`
- Step 3: Finance VP approval when `Amount__c > 10000`

The banding is carried entirely by `ifCriteriaNotMet`, not by the step criteria. Each step's criteria say who *else* has to sign; `ApproveRecord` is what lets a small request stop early and be approved rather than stall. Steps are shown without the process-level wrapper — the complete file shape, `package.xml`, and the deploy commands are in `metadata-examples.md`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApprovalProcess xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Process-level elements (active, allowedSubmitters, entryCriteria,
         label, recordEditability, the action blocks) are elided here. -->

    <!-- Required because step 1 routes by user hierarchy field. -->
    <nextAutomatedApprover>
        <useApproverFieldOfRecordOwner>false</useApproverFieldOfRecordOwner>
        <userHierarchyField>Manager</userHierarchyField>
    </nextAutomatedApprover>

    <!-- Step 1: every submitted request. No entryCriteria, and no
         rejectBehavior - it is not allowed on the first step, where
         finalRejectionActions govern instead. -->
    <approvalStep>
        <allowDelegate>true</allowDelegate>
        <assignedApprover>
            <approver>
                <type>userHierarchyField</type>
            </approver>
        </assignedApprover>
        <label>Manager Approval</label>
        <name>Manager_Approval</name>
    </approvalStep>

    <!-- Step 2: under $1,000 does not meet the criteria, so ApproveRecord
         approves it here and runs all final approval actions. The approver
         is read from a user lookup on the record itself. -->
    <approvalStep>
        <allowDelegate>true</allowDelegate>
        <assignedApprover>
            <approver>
                <name>Director__c</name>
                <type>relatedUserField</type>
            </approver>
        </assignedApprover>
        <entryCriteria>
            <criteriaItems>
                <field>Expense__c.Amount__c</field>
                <operation>greaterOrEqual</operation>
                <value>1000</value>
            </criteriaItems>
        </entryCriteria>
        <ifCriteriaNotMet>ApproveRecord</ifCriteriaNotMet>
        <label>Director Approval</label>
        <name>Director_Approval</name>
        <rejectBehavior>
            <type>RejectRequest</type>
        </rejectBehavior>
    </approvalStep>

    <!-- Step 3: $1,000-$10,000 stops here via ApproveRecord; above
         $10,000 goes to the named Finance VP. -->
    <approvalStep>
        <allowDelegate>false</allowDelegate>
        <assignedApprover>
            <approver>
                <name>finance.vp@acme.example</name>
                <type>user</type>
            </approver>
        </assignedApprover>
        <entryCriteria>
            <criteriaItems>
                <field>Expense__c.Amount__c</field>
                <operation>greaterThan</operation>
                <value>10000</value>
            </criteriaItems>
        </entryCriteria>
        <ifCriteriaNotMet>ApproveRecord</ifCriteriaNotMet>
        <label>Finance VP Approval</label>
        <name>Finance_VP_Approval</name>
        <rejectBehavior>
            <type>RejectRequest</type>
        </rejectBehavior>
    </approvalStep>
</ApprovalProcess>
```

Three approver types in one process, each with a different `name` rule: `userHierarchyField` takes no `name` and forces the `nextAutomatedApprover` element onto the process; `relatedUserField` takes the *field* name; `user` takes a *username*.

**Critical design note:** The approver fields must exist and be populated before submission. If `Director__c` is blank, the approval breaks at runtime. There is no fallback approver setting to configure — block the submission upstream instead, with a validation rule on the object:

```text
AND(
  ISPICKVAL( Status__c , "Submitted"),
  Amount__c >= 1000,
  ISBLANK( Director__c )
)
```

---

## Example: When Standard Approval Process Is the Wrong Tool

**Requirement:** Contract review needs Legal, Security, and Finance responses in parallel, plus SLA timers, rework loops, and different rules by product line.

**Recommendation:** Use Flow plus a custom approval object instead of a standard Approval Process.

**Why:** Standard approval will become fragile because the process needs:
- parallel approvals,
- richer status tracking,
- exception handling,
- and cross-object coordination.
