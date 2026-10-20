# Field History Tracking — Work Template

Use this template when enabling, auditing, or troubleshooting field history tracking on a Salesforce object.

## Scope

**Skill:** `field-history-tracking`

**Request summary:** (fill in what the user asked for — e.g., "enable field history on Opportunity for StageName and Amount" or "diagnose why field changes are not showing in history")

---

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding:

- **Object(s) in scope:**
- **Fields to track (or currently tracked):**
- **Retention requirement (months):** (if > 24 months → escalate to `security/field-audit-trail`)
- **Field types confirmed eligible:** (formula / roll-up / auto-number fields flagged for exclusion)
- **Current tracked field count per object:** (check against 20-field limit)
- **Known constraints or failure modes:**

---

## Mode Selection

Check the mode that applies to this request:

- [ ] **Mode 1 — Enable field history tracking** on an object/field combination
- [ ] **Mode 2 — Audit existing configuration** (which fields are currently tracked, confirm metadata)
- [ ] **Mode 3 — Troubleshoot missing history records** (expected changes are not showing up)

---

## Enablement Decisions

*(Fill this out for Mode 1)*

| Object API Name | Field API Name | Field Type | Eligible? | Track? | Reason |
|---|---|---|---|---|---|
|  |  |  | Yes / No | Yes / No |  |
|  |  |  | Yes / No | Yes / No |  |
|  |  |  | Yes / No | Yes / No |  |

Current tracked field count after changes: _____ / 20

History related list added to page layouts: Yes / No / Not applicable

---

## Query Pattern

*(Fill in the appropriate History sObject and filter parameters)*

```soql
-- Adjust object, field, and filters as needed
SELECT Field, OldValue, NewValue, CreatedById, CreatedDate
FROM [ObjectApiName]History          -- e.g., AccountHistory, CaseHistory, MyObject__History
                                     -- exception: Opportunity field history is OpportunityFieldHistory (not OpportunityHistory)
WHERE [ParentField] = '[RecordId]'    -- <Object>Id on standard history (AccountId), ParentId on custom __History (unverified)
  AND Field = '[FieldApiName]'       -- omit to return all fields
  AND CreatedDate >= [StartDate]     -- e.g., 2025-01-01T00:00:00Z
ORDER BY CreatedDate DESC
LIMIT 200
```

---

## Troubleshooting Diagnosis

*(Fill in for Mode 3)*

| Check | Result | Action |
|---|---|---|
| History enabled on object? | Yes / No | If No: enable it (Setup > Field History Tracking) |
| Target field selected for tracking? | Yes / No | If No: enable field (check 20-field limit) |
| Field type eligible? | Yes / No | If No: formula/roll-up/auto-number — use custom log pattern; long text/multi-select record "edited" only |
| Change within the 18-month (UI) / 24-month (API) window? | Yes / No | If No: data purged — escalate to Field Audit Trail |
| Record still exists (not deleted)? | Yes / No | If No: history deleted with the record (secguide 262 L4895-4896) |
| SOQL probe returned any rows? | Yes / No | If No: confirm field API name spelling in query |

---

## Retention Advisory

- Without Field Audit Trail, field history is retained for **up to 18 months** in the UI and **up to 24 months** via the API (secguide 262 L4553-4554).
- If the stated retention requirement exceeds 24 months, document this gap and recommend:
  - Field Audit Trail (see `security/field-audit-trail` skill), which keeps archived history until you delete it (secguide 262 L4554-4555)
  - Custom logging into a `FieldChangeLog__c` object via Apex trigger for indefinite custom retention

Retention requirement stated by stakeholder: _________ months

Action required: [ ] Within standard limit — no action | [ ] Escalate to Shield FAT | [ ] Implement custom logging

---

## Review Checklist

Copy from SKILL.md review checklist and mark as work progresses:

- [ ] History tracking enabled on the object
- [ ] Required fields selected — count does not exceed 20 per object
- [ ] Ineligible field types excluded from selection
- [ ] History related list added to relevant page layouts
- [ ] SOQL query validated against correct History sObject name
- [ ] 18-month (UI) / 24-month (API) retention communicated to stakeholders
- [ ] Escalation path to Shield FAT documented if needed
- [ ] Test change made and history row confirmed in SOQL

---

## Notes

*(Record any deviations from standard pattern, stakeholder decisions, or unresolved items)*
