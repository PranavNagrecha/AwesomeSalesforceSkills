# NPSP Data Model — Work Template

Use this template when working on tasks that involve NPSP objects, namespaces, GAU allocations, recurring donations, relationships, or affiliations.

## Scope

**Skill:** `npsp-data-model`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding:

- **NPSP installed?** (confirm via Installed Packages or `SELECT Id FROM npe01__Households_Settings__c LIMIT 1`):
- **Specific object area** (Payments / Recurring Donations / GAU Allocations / Relationships / Affiliations):
- **Correct namespace prefix for this area** (see five-prefix table in SKILL.md):
- **Known constraints** (org limits, data volume, existing trigger customizations):
- **Failure modes to watch for** (orphaned allocations, missing RD parent, mirror relationship deletion):

## Namespace Quick Reference

| Namespace | Area | Key Objects |
|---|---|---|
| `npe01__` | Households and Payments | `npe01__OppPayment__c` |
| `npe03__` | Recurring Donations | `npe03__Recurring_Donation__c` |
| `npe4__` | Relationships (Contact-to-Contact) | `npe4__Relationship__c` |
| `npe5__` | Affiliations (Contact-to-Account) | `npe5__Affiliation__c` |
| `npsp__` | GAU Allocations and Core Settings | `npsp__Allocation__c`, `npsp__General_Accounting_Unit__c` |
| `npo02__` | Household Rollup Fields on Contact/Account | `npo02__TotalOppAmount__c` |

## Approach

Which pattern from SKILL.md applies?

- [ ] Querying GAU Allocations for Opportunities
- [ ] Querying Recurring Donations and installment Opportunities
- [ ] Safe Opportunity deletion with allocation cleanup
- [ ] Relationship or affiliation data model design
- [ ] Other (describe):

## SOQL / Apex Skeleton

Replace placeholders with the confirmed API names for the relevant namespace:

```soql
-- Template: adjust namespace and fields for your object area
SELECT Id, <namespace>__Field1__c, <namespace>__Field2__c
FROM <namespace>__ObjectName__c
WHERE <namespace>__ParentLookup__c IN :parentIds
```

## Checklist

Copy from SKILL.md Review Checklist and tick as complete:

- [ ] All NPSP object API names use the correct namespace prefix (not uniformly `npsp__`)
- [ ] Any code touching Opportunity deletion also handles `npsp__Allocation__c` records
- [ ] Installment Opportunities include a valid `npe03__Recurring_Donation__c` parent reference
- [ ] Relationship (`npe4__`) and affiliation (`npe5__`) objects are not confused
- [ ] SOQL queries validated against actual org metadata before embedding in Apex or flows
- [ ] GAU allocation amounts/percentages confirmed to sum correctly per Opportunity

## Notes

Record any deviations from the standard pattern and why:
