# FSC Relationship Groups — Work Template

Use this template when creating, configuring, or troubleshooting FSC Relationship Groups (Household, Professional Group, or Trust).

## Scope

**Skill:** `fsc-relationship-groups`

**Request summary:** (fill in what the user asked for — group creation, member role setup, rollup troubleshooting, etc.)

**Group type needed:** [ ] Household   [ ] Professional Group   [ ] Trust

---

## Context Gathered

Answer these before starting work:

- **FSC packaging model:** [ ] Managed-package (FinServ__ namespace)   [ ] Core FSC (no namespace, Winter '23+)
- **Person Accounts enabled:** [ ] Yes   [ ] No (required — cannot proceed without)
- **Required Account record types active:** [ ] Household   [ ] Professional Group   [ ] Trust
- **Group purpose:** (describe the financial unit — family, business partnership, estate trust, etc.)
- **Members:** (list each Person Account and their intended role in the group)
- **Multi-group members:** (list any Person Account that belongs to more than one group and confirm which group is their primary)
- **Rollup requirements:** (which object types need to aggregate to the group — FinancialAccount, Opportunity, InsurancePolicy, etc.)

---

## Primary Group Assignment Map

Record the deliberate primary group decision for each member before creating ACR records.

| Member (Person Account Name) | Primary Group | Rationale |
|---|---|---|
| (name) | (group name) | (why this group is primary for this member) |
| (name) | (group name) | |

---

## ACR Configuration Plan

For each group member, record the intended ACR field values before creation:

| Member | Group | FinServ__PrimaryGroup__c | FinServ__Primary__c | FinServ__IncludeInGroup__c | Notes |
|---|---|---|---|---|---|
| (name) | (group name) | true / false | true / false | true / false | |
| (name) | (group name) | true / false | true / false | true / false | |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] **Create a New Household Relationship Group** — new family group from scratch
- [ ] **Add a Client to a Trust Group Without Disrupting Primary Household** — secondary group for estate planning
- [ ] **Professional Group for Business Partners** — business entity grouping
- [ ] **Other / Hybrid:** (describe)

---

## Execution Steps

Track each step as it completes:

- [ ] Prerequisites verified (FSC model, Person Accounts enabled, record types active)
- [ ] Group type and purpose confirmed with stakeholder
- [ ] Primary Group Assignment Map completed for all members
- [ ] Relationship Group Account record created with correct record type
- [ ] ACR records created for all members — all three FSC fields explicitly set
- [ ] No Person Account has FinServ__PrimaryGroup__c = true on more than one ACR (verified via SOQL)
- [ ] Rollups__c picklist verified for required object types
- [ ] Rollup fields validated in sandbox (TotalAssets, TotalLiabilities, etc.)
- [ ] Batch rollup job run if bulk data load was performed
- [ ] Results reviewed with advisor or stakeholder

---

## Validation SOQL

Run these queries in Developer Console or Workbench to verify group configuration:

**Confirm ACR records for a group:**
```soql
SELECT Id, Contact.Name, FinServ__PrimaryGroup__c, FinServ__Primary__c, FinServ__IncludeInGroup__c
FROM AccountContactRelation
WHERE AccountId = '<GROUP_ACCOUNT_ID>'
```

**Detect members with multiple primary groups (should return zero rows):**
```soql
SELECT ContactId, COUNT(Id) acrCount
FROM AccountContactRelation
WHERE FinServ__PrimaryGroup__c = true
GROUP BY ContactId
HAVING COUNT(Id) > 1
```

**Check group rollup totals:**
```soql
SELECT Id, Name, FinServ__TotalAssets__c, FinServ__TotalLiabilities__c
FROM Account
WHERE Id = '<GROUP_ACCOUNT_ID>'
```

---

## Deviations from Standard Pattern

(Record any deviations and why — e.g., why a member was not set as primary, why IncludeInGroup was set to false, why a particular group type was chosen over another)

---

## Notes for Handoff

(Record org-specific configuration decisions, edge cases, and any post-go-live monitoring needed — e.g., batch rollup schedule, custom validation rule added, advisor notification of primary group change behavior)
