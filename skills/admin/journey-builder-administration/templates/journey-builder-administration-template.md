# Journey Builder Administration — Work Template

Use this template when working on Journey Builder setup, modification, or troubleshooting tasks.

## Scope

**Skill:** `journey-builder-administration`

**Request summary:** (fill in what the user asked for — new journey build, existing journey fix, analytics investigation, etc.)

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding:

- **Business Unit:** (which Marketing Cloud BU owns this journey?)
- **Entry source type:** (Data Extension / Salesforce Data / API Event / CloudPages / Audience Builder)
- **Entry timing requirement:** (real-time vs. scheduled — affects entry source choice)
- **Re-entry policy:** (single entry per version / re-entry enabled with interval — what is the interval?)
- **Activities required:** (Email, SMS, Push, Advertising, Update Contact, Salesforce Activity, custom)
- **Split logic:** (attribute fields and values, engagement criteria, random percentages, or Einstein STO)
- **Goal definition:** (conversion event and data condition — e.g., `PurchaseDate IS NOT NULL`)
- **Exit criteria:** (removal condition and stakeholder acknowledgment of 15-minute lag)
- **Journey status:** (new journey / new version of existing journey / troubleshooting active journey)

## Data Extension Validation

Before building or publishing:

- [ ] Entry source DE exists in the correct Business Unit
- [ ] Entry source DE is configured as Sendable (if used for email sends)
- [ ] All attribute split fields exist on the entry source DE and are populated for the entry population
- [ ] Run query to check for null values in split attribute fields:
  ```sql
  SELECT COUNT(*) AS NullCount
  FROM [EntryDE]
  WHERE CustomerTier IS NULL
  -- Replace CustomerTier with your actual split attribute field
  ```
- [ ] Goal condition field exists on the contact DE and is populated correctly for test contacts

## Journey Configuration Summary

Document the planned configuration before building:

**Entry source:**
- Type:
- DE or object name:
- Entry criteria:
- Evaluation schedule (if DE):
- Re-entry: Enabled / Disabled — Interval: [X days]

**Activity chain:**
```
Entry
  └─ [Activity 1: type, name]
  └─ [Wait: duration]
  └─ [Decision Split: type, field]
       ├─ Arm 1 (label: condition):
       │    └─ [Activity: type, name]
       │    └─ [Wait: duration]
       │    └─ [Activity: type, name]
       ├─ Arm 2 (label: condition):
       │    └─ [Activity: type, name]
       └─ Default Arm:
            └─ [Activity: type, name]
```

**Goal:**
- Condition:
- Field:
- Evaluate at: Each activity

**Exit criteria:**
- Condition:
- Field:
- Stakeholder acknowledgment of 15-minute lag: Yes / No

## Test Mode Plan

Before publishing, test contacts covering:

| Test Contact | Split Arm Expected | Goal Exit? | Expected Exit Path |
|---|---|---|---|
| Contact A | Arm 1 | No | Final activity → journey end |
| Contact B | Arm 2 | No | Final activity → journey end |
| Contact C | Any | Yes | Goal path after activity [X] |
| Contact D | Default | No | Default arm final activity → journey end |

Test Mode steps:
1. Activate Test Mode on the journey canvas
2. Inject each test contact (via UI or API Event as applicable)
3. Verify split routing matches expected arm
4. Advance contacts through wait activities manually or confirm wait duration acceptable
5. Confirm goal exit fires for Contact C before the expected email step
6. Confirm message suppression — no live sends to real subscribers

## Checklist

Copy from SKILL.md Review Checklist and tick as complete:

- [ ] Entry source type matches the required entry timing
- [ ] Re-entry policy is explicitly configured
- [ ] All DE fields required for attribute splits are present and populated
- [ ] Goal conversion event is defined and data condition field is confirmed
- [ ] Exit Criteria conditions are validated; stakeholders informed of 15-minute schedule
- [ ] All channel activities reference valid message definitions with correct from addresses
- [ ] Test Mode run with test contacts covering all split arms and goal exit path
- [ ] Journey Analytics dashboard reviewed post-launch for entry, goal, and exit counts
- [ ] Journey version strategy is documented

## Version Management Notes

If this is a new version of an existing journey:

- Previous version number:
- Reason for new version:
- In-flight contact count in previous version (check Journey Analytics):
- Plan for draining previous version (stop when count reaches 0 / leave open until [date]):

## Notes and Deviations

Record any deviations from the standard pattern and why:

(e.g., "Used Exit Criteria only for conversion removal — Goal not configured because stakeholder does not need conversion analytics. Accepted 15-minute lag.")
