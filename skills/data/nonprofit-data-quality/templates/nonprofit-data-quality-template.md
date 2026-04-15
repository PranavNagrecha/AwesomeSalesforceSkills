# Nonprofit Data Quality — Work Template

Use this template when working on constituent address standardization, duplicate household Contact detection, NCOA processing, or general NPSP data hygiene tasks.

## Scope

**Skill:** `nonprofit-data-quality`

**Request summary:** (fill in what the user or org asked for)

**Task type:** (check one)
- [ ] Address verification — retroactive processing of historical `npsp__Address__c` records
- [ ] Duplicate Contact detection and NPSP Contact Merge
- [ ] NCOA processing (requires Insights Platform Data Integrity license)
- [ ] Ongoing data hygiene — matching rules, field validation, hygiene scoring
- [ ] Other: ___________

## Context Gathered

- NPSP version installed:
- Household Account model active: Yes / No
- Address verification service configured: Cicero / Google Geocoding / SmartyStreets / None
- Insights Platform Data Integrity license present (NCOA only): Yes / No / Not applicable
- Agentforce Nonprofit installed (if Yes, NCOA add-on is incompatible): Yes / No
- Approximate number of `npsp__Address__c` records with `npsp__Verified__c = false`:
- Approximate number of suspected duplicate Contacts:

## Pre-Work SOQL Checks

Run these queries in Developer Console before beginning:

**Unverified address count:**
```soql
SELECT npsp__Verified__c, COUNT(Id) total
FROM npsp__Address__c
GROUP BY npsp__Verified__c
```

**Duplicate Contact candidates (basic name + email match):**
```soql
SELECT FirstName, LastName, Email, COUNT(Id) cnt
FROM Contact
GROUP BY FirstName, LastName, Email
HAVING COUNT(Id) > 1
ORDER BY COUNT(Id) DESC
LIMIT 50
```

**Seasonal addresses never verified:**
```soql
SELECT Id, npsp__Household_Account__c, npsp__Seasonal_Start_Month__c, npsp__Verified__c
FROM npsp__Address__c
WHERE npsp__Seasonal_Start_Month__c != null
AND npsp__Verified__c = false
LIMIT 200
```

## Approach

Which pattern from SKILL.md applies? (check one)
- [ ] Pattern 1: Mass Address Verification for Historical Records
- [ ] Pattern 2: NPSP Contact Merge for Duplicate Households
- [ ] Pattern 3: NPSP Contact Matching Rules for Ongoing Duplicate Prevention
- [ ] NCOA processing via Insights Platform Data Integrity

Justification: (explain why this pattern was selected based on context gathered above)

## Execution Notes

- Address verification batch size used: _____ (recommended: 25)
- AsyncApexJob ID for batch tracking:
- Number of Contacts merged:
- Household Account IDs requiring rollup recalculation:

## Checklist

- [ ] All `npsp__Address__c` updates targeted the `npsp__Address__c` object — NOT Contact or Account mailing address fields
- [ ] All Contact merges used NPSP Contact Merge (`/apex/NPSP__merge`) — NOT standard Salesforce merge
- [ ] Address verification batch completed and `npsp__Verified__c` coverage confirmed post-run
- [ ] NCOA step only performed if Insights Platform Data Integrity license confirmed active
- [ ] No standard Salesforce Duplicate Rules used as primary matching gate for NPSP imports
- [ ] Rollup fields verified on all Household Accounts touched by Contact merges
- [ ] Seasonal address verification coverage reviewed if seasonal addresses exist in org

## Results

**Before:**
- Unverified `npsp__Address__c` count:
- Duplicate Contact pairs identified:

**After:**
- Unverified `npsp__Address__c` count:
- Duplicate Contact pairs merged:
- NCOA corrections applied (if applicable):

## Notes

(Record any deviations from the standard pattern, unexpected API errors, licensing gaps discovered, or follow-up tasks.)
