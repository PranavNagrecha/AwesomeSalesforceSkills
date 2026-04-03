# Gotchas: Approval Processes

---

## Record Locking Breaks Legitimate Work

**What happens:** A submitter sends a record for approval, then another team needs to correct a field before the approver responds. The record is locked, the correction cannot be made, and business users blame Salesforce.

**When it bites you:** Revenue approvals, case escalations, and any process where business users still work the record while waiting.

**How to avoid it:** Decide up front whether the record should lock, who needs edit access while pending, and whether the approval should happen later in the lifecycle.

**Example:**
```text
Bad pattern: Submit for approval at draft stage, then expect sales ops to keep editing the record.
Better pattern: Submit only after required fields are final.
```

---

## Blank Approver Fields Fail at Runtime

**What happens:** Approval routing depends on a lookup such as `Director__c`. One record has that field blank. Submission fails even though the process design itself looks valid.

**When it bites you:** User-lookup routing, manager-based routing after org changes, and record-specific approver fields.

**How to avoid it:** Validate approver fields before submission and create a fallback owner or escalation path.

**Example:**
```text
If `Legal_Approver__c` is blank, block submission with a validation message before the user reaches the approval engine.
```

---

## Recall Does Not Undo Every Side Effect

**What happens:** A record is submitted, field updates and email alerts fire, then the submitter recalls it. The business assumes everything returned to pre-submission state. It did not.

**When it bites you:** Processes with submission actions that notify customers, create tasks, or stamp approval status fields.

**How to avoid it:** Document which actions happen on submit, approve, reject, and recall. If recall must reverse state, build that explicitly.

**Example:**
```text
Submission action: set Status = Pending Approval
Recall expectation: Status returns to Draft
Reality: only true if you build recall handling for it
```

---

## Approval Processes Hide Organizational Drift

**What happens:** A process routed cleanly when managers and directors were stable. Six months later, a reorg leaves stale manager relationships and inactive approvers, and approvals start stalling.

**When it bites you:** Manager-based approvals and orgs with frequent user moves.

**How to avoid it:** Audit approver routing after reorgs and monitor pending approvals older than the expected SLA.

**Example:**
```text
Quarterly control: report all pending approvals older than 3 business days and inspect approver assignments.
```
