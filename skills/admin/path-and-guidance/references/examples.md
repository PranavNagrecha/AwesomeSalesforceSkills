# Examples — Path and Guidance

## Example 1: Opportunity Path with MEDDIC-Aligned Key Fields

**Context:** A B2B sales org uses the MEDDIC qualification framework. Reps frequently forget to capture metrics and economic buyer details before moving to Proposal. The sales manager wants those fields surfaced contextually at the right stage.

**Problem:** The full opportunity layout has 40+ fields. Reps skip the MEDDIC fields because they are buried in the middle of the page. Deals reach Proposal with no economic buyer captured.

**Solution:**

```
Path Settings > New Path
  Object: Opportunity
  Record Type: Enterprise New Business
  Field: Stage

Stage: Qualification
  Key Fields:
    - Metrics__c          (What value does the customer measure?)
    - Economic_Buyer__c   (Lookup to Contact)
    - Decision_Criteria__c
    - Budget_Confirmed__c (Checkbox)
    - Next_Step__c
  Guidance Text:
    "Exit criteria for Qualification:
     - Economic buyer identified and contacted
     - Measurable business value confirmed
     - Next step scheduled
     Link: [MEDDIC Qualification Playbook](https://internal.example.com/meddic)"

Stage: Proposal/Price Quote
  Key Fields:
    - Decision_Process__c
    - Paper_Process__c
    - Proposed_Solution__c
    - Decision_Due_Date__c
    - Amount
  Guidance Text:
    "Before sending proposal:
     - Confirm decision process and timeline
     - Paper process (legal, procurement) documented
     - Champion confirmed proposal aligns to success criteria"

Stage: Closed Won
  Confetti: Enabled
  Key Fields:
    - Close_Date
    - Amount
    - Contract_Signed__c
  Guidance Text:
    "Deal closed! Next steps:
     - Submit order form within 24 hours
     - Schedule kickoff with CS team
     - Complete Win Report by end of week"
```

**Why it works:** Key fields surface exactly the right data at the right stage without requiring reps to scroll. The guidance text provides exit criteria linked to the internal playbook. Confetti on Closed Won gives reps a moment of recognition that costs the org nothing.

---

## Example 2: Case Path with Status-Based Agent Guidance

**Context:** A customer service team handles three case statuses: New, Working, Escalated. Agents frequently miss the SLA requirement to contact the customer within 4 hours of escalation. Management wants visible, in-context reminders at the Escalated status.

**Problem:** The SLA reminder lives in a training document that agents rarely read. Escalated cases regularly breach the 4-hour contact window.

**Solution:**

```
Path Settings > New Path
  Object: Case
  Record Type: All Record Types
  Field: Status

Stage: New
  Key Fields:
    - Priority
    - Case_Origin__c
    - Contact.Phone
  Guidance Text:
    "New case checklist:
     - Set Priority based on impact/urgency matrix
     - Confirm contact method matches customer preference
     - Assign to correct queue before taking ownership"

Stage: Working
  Key Fields:
    - Case_Reason
    - Related_Article__c  (Knowledge lookup)
    - Internal_Comments__c
  Guidance Text:
    "Working case tips:
     - Search Knowledge before custom troubleshooting
     - Update Internal Comments with your findings
     - Set follow-up task if awaiting customer response"

Stage: Escalated
  Key Fields:
    - Escalation_Reason__c
    - Escalated_By__c
    - Customer_Impact__c
    - Escalation_Timestamp__c
  Guidance Text:
    "ESCALATED — SLA: Contact customer within 4 hours of escalation.
     - Confirm escalation reason is documented
     - Notify team lead immediately
     - Do NOT change status back to Working without team lead approval"
```

**The same design as deployable metadata** — `pathAssistants/Case_Support_Path.pathAssistant-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PathAssistant xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <entityName>Case</entityName>
    <fieldName>Status</fieldName>
    <masterLabel>Support Case Path</masterLabel>
    <pathAssistantSteps>
        <fieldNames>Priority</fieldNames>
        <fieldNames>Origin</fieldNames>
        <info>Set Priority from the impact/urgency matrix, confirm the contact method matches the customer preference, and assign to the correct queue before taking ownership.</info>
        <picklistValueName>New</picklistValueName>
    </pathAssistantSteps>
    <pathAssistantSteps>
        <fieldNames>Reason</fieldNames>
        <fieldNames>Related_Article__c</fieldNames>
        <info>Search Knowledge before custom troubleshooting. Record findings in Internal Comments. Set a follow-up task if you are waiting on the customer.</info>
        <picklistValueName>Working</picklistValueName>
    </pathAssistantSteps>
    <pathAssistantSteps>
        <fieldNames>Escalation_Reason__c</fieldNames>
        <fieldNames>Customer_Impact__c</fieldNames>
        <fieldNames>Escalation_Timestamp__c</fieldNames>
        <info>SLA: contact the customer within 4 hours of escalation. Confirm the escalation reason is documented, notify the team lead, and do not return the case to Working without team-lead approval.</info>
        <picklistValueName>Escalated</picklistValueName>
    </pathAssistantSteps>
    <recordTypeName>Master</recordTypeName>
</PathAssistant>
```

Three things to notice, all of which the design conversation above glosses over:

- `recordTypeName` is `Master`, not "All Record Types". Even the master record type consumes the one-path-per-record-type slot (api_meta.txt L94496) — this org can never add a second Case path without introducing record types.
- The design listed `Contact.Phone` and `Internal_Comments__c` as key fields; both are dropped here. `fieldNames` names "the fields in entityName" (api_meta.txt L94545), so a cross-object dotted reference is not a field on Case, and a long text area is not a viable inline key field.
- `Closed` has no step. That is deliberate and it is not a deletion: "a missing step in the .xml file means it has not been configured, not that it doesn't exist" (api_meta.txt L94525–94526). The Closed chevron still renders, blank.

UNVERIFIED (2026-09-05): the Metadata API guide names only Opportunity, Lead, and Quote as objects with a hard-coded `entityName`, plus custom objects (api_meta.txt L94513–94515). Case Path is long-standing practice but is not confirmed by the extracted guides — check the object picker in Setup > Path Settings before building this.

**Why it works:** The 4-hour SLA reminder is unavoidable — it appears every time an agent views an Escalated case. No new automation or monitoring was required. The guidance replaces an ignored training doc with an in-context nudge.

---

## Anti-Pattern: Using Path as a Validation Enforcement Tool

**What practitioners do:** An admin adds a key field to a stage thinking it will become required before the rep can advance to the next stage.

**What goes wrong:** Path displays the field but does not enforce it. The rep can move to the next stage while the field is empty. The admin discovers this in UAT (or after go-live) and scrambles to add a validation rule.

**Correct approach:** Use Path for display and guidance, and pair every key field that genuinely must be filled with a validation rule. The two artifacts ship together and reference the same picklist value string:

```
# pathAssistants/Enterprise_New_Business_Path.pathAssistant-meta.xml  (displays)
<pathAssistantSteps>
    <fieldNames>Economic_Buyer__c</fieldNames>
    <picklistValueName>Proposal/Price Quote</picklistValueName>
</pathAssistantSteps>

# objects/Opportunity/validationRules/Opp_Proposal_RequireKeyFields.validationRule-meta.xml  (enforces)
errorConditionFormula:
    AND(
        ISPICKVAL(StageName, "Proposal/Price Quote"),
        ISBLANK(Economic_Buyer__c),
        NOT($Permission.Bypass_Validation_Rules)
    )
errorDisplayField: Economic_Buyer__c
errorMessage:      "Economic Buyer must be set before advancing to Proposal."
```

The literal `Proposal/Price Quote` appears in both files and in the record type's `picklistValues` block. If any one of the three drifts, the path shows a chevron the rule never fires on, or the rule blocks a save on a stage the path does not explain. `scripts/check_path_and_guidance.py` catches the path-to-record-type half of that drift; the rule half is `admin/validation-rules`.

---

## Anti-Pattern: Assuming Confetti Fires on Any Stage Change

**What practitioners do:** An admin enables confetti on Closed Won, then a Flow is built to auto-advance the stage when a contract is signed. The team expects confetti to fire automatically.

**What goes wrong:** Confetti does not fire. The stage change happened through a Flow (automation), not through the Path component's UI. The rep sees the stage is Closed Won but never saw the animation.

**Correct approach:** Design the process so reps manually click "Mark Stage as Complete" through the Path UI for the stages where celebration matters. If the stage must also be updated by automation, confetti will still fire if a rep subsequently loads the record and the Path reflects the current stage — but the animation only triggers on the manual user interaction, not retroactively.
