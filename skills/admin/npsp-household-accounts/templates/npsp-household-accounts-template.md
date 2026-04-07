# NPSP Household Accounts — Work Template

Use this template when working on NPSP Household Account configuration or management tasks.

## Scope

**Skill:** `npsp-household-accounts`

**Request summary:** (fill in what the user asked for — naming configuration, merge, greeting setup, etc.)

**Applies to:** NPSP orgs using the Household Account model. NOT for FSC Household Groups.

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md before proceeding.

- **NPSP model confirmed:** [ ] Household Account model active (not Individual/Bucket)
- **NPSP package version:** _______________
- **Org type:** Production / Sandbox / Scratch
- **Customized households present:** [ ] Yes — count: ___ / [ ] No / [ ] Unknown (run audit query)
- **Merge work in scope:** [ ] Yes / [ ] No
- **Naming format current value:** _______________
- **Formal Greeting format current value:** _______________
- **Informal Greeting format current value:** _______________

### Audit Query — Households with Customization Flag

Run this SOQL before making any naming changes to identify frozen household names:

```soql
SELECT Id, Name, npo02__SYSTEM_CUSTOM_NAMING__c
FROM Account
WHERE RecordType.Name = 'Household Account'
  AND npo02__SYSTEM_CUSTOM_NAMING__c != null
ORDER BY Name
```

Record the count here: _______________

---

## Approach

Which pattern from SKILL.md applies?

- [ ] **Pattern 1: Mixed-Last-Name Household Naming** — configure Name Format and greeting format strings
- [ ] **Pattern 2: Primary Contact Designation** — set `npo02__Household_Naming_Order__c` on Contacts
- [ ] **Merge Pattern** — use NPSP Merge Duplicate Contacts flow (NOT native Account merge)
- [ ] **Custom Override** — edit household name directly; document customization flag consequence

**Reasoning:** (explain why this pattern applies to the request)

---

## Configuration Values

Fill these in before applying any changes:

| Setting | Current Value | New Value |
|---|---|---|
| Household Name Format | | |
| Name Connector | | |
| Name Append Text | | |
| Formal Greeting Format | | |
| Formal Greeting Connector | | |
| Informal Greeting Format | | |
| Informal Greeting Connector | | |
| Custom Household Naming Class | | |

---

## Checklist

Copy from the SKILL.md review checklist and tick items as you complete them.

- [ ] NPSP Household Account model confirmed active (not Individual/Bucket model)
- [ ] Household Name Format, Formal Greeting, and Informal Greeting strings verified in NPSP Settings
- [ ] Batch name refresh completed and Apex Jobs show no failures
- [ ] Manually customized household names audited; intentional overrides documented
- [ ] Any duplicate merges performed using NPSP Merge Duplicate Contacts flow (not native Account merge)
- [ ] Rollup totals verified on surviving Household Account after any merge
- [ ] Primary Contact naming order (`npo02__Household_Naming_Order__c`) set correctly for multi-member households

---

## Verification Queries

### Verify naming regenerated correctly on a sample household

```soql
SELECT Id, Name, npo02__Formal_Greeting__c, npo02__Informal_Greeting__c,
       npo02__TotalOppAmount__c, npo02__NumberOfClosedOpps__c
FROM Account
WHERE RecordType.Name = 'Household Account'
  AND LastModifiedDate = TODAY
ORDER BY LastModifiedDate DESC
LIMIT 20
```

### Verify rollup totals after a merge

```soql
SELECT Id, Name, npo02__TotalOppAmount__c, npo02__NumberOfClosedOpps__c,
       npo02__LastCloseDate__c
FROM Account
WHERE Id = '<surviving_account_id>'
```

### Verify no orphaned Relationship records after a Contact merge

```soql
SELECT Id, npe4__Contact__c, npe4__RelatedContact__c, npe4__Type__c
FROM npe4__Relationship__c
WHERE npe4__Contact__c = null OR npe4__RelatedContact__c = null
```

---

## Notes

Record any deviations from the standard pattern and why:

-
