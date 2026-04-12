# Nonprofit Data Architecture — Work Template

Use this template when working on tasks involving the NPSP data model, constituent 360 design, giving history rollups, or program participation tracking.

## Scope

**Skill:** `nonprofit-data-architecture`

**Request summary:** (fill in what the user asked for — e.g., "Design a constituent 360 query for the donor portal" or "Add a custom rollup for major gifts")

---

## Context Gathered

Answer these before proceeding with any design or code:

- **Platform confirmed as NPSP (not NPC/FSC)?**
  `SELECT Id FROM npo02__Household_Settings__c LIMIT 1` — result: ___________

- **Constituent model in use:**
  `SELECT DeveloperName FROM RecordType WHERE SObjectType = 'Account' AND DeveloperName = 'HH_Account'` — HH_Account present: Yes / No

- **CRLP enabled or legacy rollup mode?**
  Navigate to NPSP Settings > Rollup Settings — CRLP status: Enabled / Disabled / Unknown

- **PMM installed?**
  `SELECT SubscriberPackage.NamespacePrefix FROM InstalledSubscriberPackage` — pmdm__ present: Yes / No

- **NPSP version:**
  Installed Packages > Nonprofit Success Pack — version: ___________

- **Known constraints or customizations:**
  (triggers on Opportunity, custom rollup fields, custom HH Account record type name, etc.)

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Constituent 360 query (giving history + program participation)
- [ ] CRLP custom rollup configuration (new Rollup__mdt + Filter_Group__mdt)
- [ ] PMM program and service delivery data model
- [ ] Rollup validation / data quality check (rollup vs. raw Opportunity aggregate)
- [ ] Other: ___________

**Why this pattern:** ___________

---

## Data Model Reference

### Three-Layer Constituent 360

```
Contact (individual constituent)
  └─ AccountId → Account [RecordType.DeveloperName = 'HH_Account'] (household)
                    └─ Opportunities (gift transactions) [AccountId]
                         └─ npe01__OppPayment__c (payment schedules)

Contact
  └─ npo02__TotalOppAmount__c     (Contact-level: gifts where this contact is primary)
  └─ npo02__LastOppAmount__c
  └─ npo02__LastCloseDate__c
  └─ npo02__ConsecutiveYearsGiven__c

Account (HH_Account)
  └─ npo02__TotalOppAmount__c     (Account-level: all gifts to this household)
  └─ npo02__LastOppAmount__c
  └─ npo02__LastCloseDate__c
```

### PMM Program Participation (requires pmdm__ package)

```
Contact
  └─ pmdm__ProgramEngagement__c [pmdm__Contact__c]
        └─ pmdm__Program__c [pmdm__Program__c]
        └─ pmdm__ServiceDelivery__c [pmdm__ProgramEngagement__c]
              └─ pmdm__Service__c [pmdm__Service__c]
```

---

## SOQL Stubs

### Giving History (fill in variables)

```soql
-- Constituent rollup summary
SELECT Id, Name, AccountId,
    npo02__TotalOppAmount__c,
    npo02__LastOppAmount__c,
    npo02__LastCloseDate__c,
    npo02__OppAmountThisYear__c,
    npo02__ConsecutiveYearsGiven__c
FROM Contact
WHERE Id = '__CONTACT_ID__'

-- Raw gift transactions for household
SELECT Id, Name, Amount, CloseDate, StageName, npsp__Primary_Contact__r.Name
FROM Opportunity
WHERE AccountId = '__HH_ACCOUNT_ID__'
  AND IsWon = true
ORDER BY CloseDate DESC
```

### Program Participation (requires PMM)

```soql
SELECT Id, pmdm__Program__r.Name, pmdm__Stage__c, pmdm__StartDate__c
FROM pmdm__ProgramEngagement__c
WHERE pmdm__Contact__c = '__CONTACT_ID__'

SELECT Id, pmdm__DeliveryDate__c, pmdm__Quantity__c, pmdm__Service__r.Name
FROM pmdm__ServiceDelivery__c
WHERE pmdm__Contact__c = '__CONTACT_ID__'
ORDER BY pmdm__DeliveryDate__c DESC
```

---

## Checklist

- [ ] Confirmed org is NPSP (not Nonprofit Cloud NPC) before applying this skill
- [ ] Verified HH_Account record type present and in use
- [ ] CRLP enabled/disabled status documented — rollup approach matched to mode
- [ ] PMM package presence confirmed before referencing pmdm__ objects
- [ ] SOQL gift queries use AccountId (HH Account), not ContactId
- [ ] Rollup fields validated against aggregate SOQL on raw Opportunity records
- [ ] Namespace dependencies documented for any deployable solution
- [ ] NPSP Health Check run and passing

---

## Notes

(Record any deviations from the standard pattern, org-specific constraints, or decisions made during implementation.)
