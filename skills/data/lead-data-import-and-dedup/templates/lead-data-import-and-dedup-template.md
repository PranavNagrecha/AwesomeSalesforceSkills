# Lead Data Import and Dedup — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `lead-data-import-and-dedup`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Data entry channel(s):** (CSV upload / Web-to-Lead / API / marketing automation sync / other)
- **Estimated import volume:** (number of records)
- **Estimated duplicate rate:** (% or unknown)
- **Fields available for matching:** (Email / Phone / Name / Company / External ID / other)
- **Cross-object check needed:** (Lead-to-Contact? Lead-to-Lead? Both?)
- **Existing Duplicate Rules active on Lead:** (list names and actions — Block or Alert)
- **Active rule slot count:** (out of 5 maximum)
- **Known constraints or automation on Lead object:** (triggers, flows, workflow rules that fire on insert/update/delete)

## Approach

Which pattern from SKILL.md applies?

- [ ] Pre-Import Normalization + Data Import Wizard
- [ ] Apex After-Insert Trigger for Web-to-Lead / API dedup
- [ ] Alert-Mode Duplicate Rule + Duplicate Record Set Review Queue
- [ ] Third-party tool (DemandTools / Cloudingo / Plauti)
- [ ] Other: _______________

**Why this approach:** (explain the decision based on channel, volume, and matching requirements)

## Pre-Import Checklist (for CSV imports)

- [ ] Import file deduplicated on Email column (within-file dedup)
- [ ] Email addresses lowercased and trimmed
- [ ] Phone numbers normalized (digits only or E.164)
- [ ] Company names normalized (common suffixes removed if using name-based matching)
- [ ] Records with no email identified and plan confirmed (insert + route to review queue)
- [ ] Data Import Wizard match field selected: _______________
- [ ] Wizard action selected: Add new / Update existing / Add new and update existing

## Configuration Checklist (for rule-based dedup)

- [ ] Standard Lead Matching Rule active and field coverage reviewed
- [ ] Lead Duplicate Rule action confirmed (Alert recommended for non-UI channels)
- [ ] Lead-to-Contact Matching Rule evaluated (active if cross-object detection needed)
- [ ] Active rule slot count confirmed (<= 5)
- [ ] Duplicate Record Set list view created for review queue

## Implementation Checklist (for Apex trigger)

- [ ] After-insert trigger calls `Datacloud.DuplicateRule.findDuplicates()` (not before-insert)
- [ ] Trigger does NOT call `Database.merge()` directly — merges queued asynchronously
- [ ] Duplicate status field updated for flagged records
- [ ] Flagged records routed to dedup queue owner
- [ ] Unit tests include mocked `findDuplicates()` result (do not rely on active rules in sandbox)

## Post-Import / Post-Activation Validation

Run these SOQL queries to confirm dedup behavior:

```soql
-- Count Duplicate Record Sets created for Lead
SELECT COUNT(Id) FROM DuplicateRecordSet WHERE SobjectType = 'Lead'

-- Review flagged leads (requires custom Duplicate_Status__c field)
SELECT Id, FirstName, LastName, Email, Company, Duplicate_Status__c, CreatedDate
FROM Lead
WHERE Duplicate_Status__c = 'Potential Duplicate'
ORDER BY CreatedDate DESC
LIMIT 200

-- Check DuplicateRecordItems for a specific lead
SELECT Id, RecordId, DuplicateRecordSetId
FROM DuplicateRecordItem
WHERE RecordId = '<lead_id>'
```

## Checklist Before Marking Complete

Copy and tick off items from the SKILL.md Review Checklist:

- [ ] Duplicate Rule action confirmed and Web-to-Lead bypass behavior understood
- [ ] Data Import Wizard dedup field chosen and pre-import normalization completed
- [ ] Standard Lead Matching Rule active and field coverage reviewed
- [ ] Lead-to-Contact Matching Rule evaluated
- [ ] Apex trigger or Flow in place for non-UI channels
- [ ] Duplicate Record Set list view configured for data steward review queue
- [ ] Post-import SOQL query run on DuplicateRecordItem to confirm flagging
- [ ] Ongoing Duplicate Jobs or scheduled scan configured

## Notes

Record any deviations from the standard pattern and why.

- Deviation:
- Reason:
- Approved by:
