# CPQ Deployment Administration — Work Template

Use this template when planning or executing a Salesforce CPQ configuration migration between orgs.

## Scope

**Skill:** `cpq-deployment-administration`

**Request summary:** (describe what CPQ configuration needs to move and between which orgs)

**Source org:** (org alias or URL)

**Target org:** (org alias or URL)

---

## Pre-Migration Context

| Check | Source Org | Target Org |
|---|---|---|
| CPQ managed package version | | |
| CPQ Custom Settings populated | Yes / No | Yes / No |
| External ID fields on SBQQ objects | Yes / No / Not yet set up | Yes / No |
| Product catalog parity confirmed | Yes / No | |
| Admin access available | Yes / No | Yes / No |

---

## CPQ Objects in Migration Scope

List all SBQQ objects that need to be migrated. Use the parent-before-child ordering.

| Order | Object API Name | Record Count (Source) | Notes |
|---|---|---|---|
| 1 | Product2 / Pricebook2 / PricebookEntry | | (confirm parity first) |
| 2 | SBQQ__ProductRule__c | | |
| 3 | SBQQ__PriceRule__c | | |
| 4 | SBQQ__PriceCondition__c | | |
| 5 | SBQQ__PriceAction__c | | |
| 6 | SBQQ__OptionConstraint__c | | |
| 7 | SBQQ__QuoteTemplate__c | | |
| 8 | SBQQ__TemplateSection__c | | |
| 9 | SBQQ__TemplateContent__c | | |
| 10 | SBQQ__CustomClass__c (Custom Settings) | | |
| — | ContentDocument / ContentVersion (if templates have embedded content) | | |

---

## Tooling Choice

- [ ] **Prodly AppOps** — recommended for frequent migrations; auto-handles dependency graph
- [ ] **SFDMU** — free; requires manual ordering plan and external ID setup
- [ ] **Copado Data Deploy** — use if Copado is already the DevOps platform
- [ ] **Salto** — use for version-controlled, PR-reviewed CPQ configuration management
- [ ] **Custom data loader** — last resort; requires full manual ordering and ID mapping

**Tooling rationale:** (explain why this tool was chosen)

---

## External ID Scheme

(Complete only if using SFDMU or Data Loader)

| SBQQ Object | External ID Field API Name | Value Construction Logic |
|---|---|---|
| SBQQ__PriceRule__c | CPQ_External_Id__c | e.g. 'PRICERULE_' + Name |
| SBQQ__PriceAction__c | CPQ_External_Id__c | e.g. 'PRICEACTION_' + PriceRule Name + '_' + Name |
| SBQQ__ProductRule__c | CPQ_External_Id__c | e.g. 'PRODUCTRULE_' + Name |
| SBQQ__QuoteTemplate__c | CPQ_External_Id__c | e.g. 'TEMPLATE_' + Name |
| (add rows for each object) | | |

---

## Pre-Migration Validation Queries

Run these SOQL queries in the source org before exporting:

```soql
-- 1. Count Price Rules and confirm active status
SELECT SBQQ__Active__c, COUNT(Id) cnt FROM SBQQ__PriceRule__c GROUP BY SBQQ__Active__c

-- 2. Check for potential broken API-name string references (custom fields)
SELECT SBQQ__TestedField__c, COUNT(Id) cnt FROM SBQQ__PriceCondition__c
GROUP BY SBQQ__TestedField__c
ORDER BY cnt DESC

SELECT SBQQ__TargetField__c, COUNT(Id) cnt FROM SBQQ__PriceAction__c
GROUP BY SBQQ__TargetField__c
ORDER BY cnt DESC

-- 3. Check for Quote Templates with associated files
SELECT LinkedEntityId, ContentDocument.Title
FROM ContentDocumentLink
WHERE LinkedEntityId IN (SELECT Id FROM SBQQ__QuoteTemplate__c)
```

---

## Post-Migration Validation Checklist

- [ ] CPQ Custom Settings values match source org
- [ ] Price Rules count in target matches source
- [ ] Price Actions count per Price Rule matches source
- [ ] Create a test Quote with a product covered by migrated Price Rules; confirm discount applies
- [ ] Confirm at least one Product Rule enforces correctly (error message appears or option hidden)
- [ ] Generate a Quote Document from a migrated Quote Template; confirm no missing sections
- [ ] Run SOQL on `SBQQ__PriceCondition__c.SBQQ__TestedField__c` and cross-reference field names against target org field list
- [ ] Run SOQL on `SBQQ__PriceAction__c.SBQQ__TargetField__c` and confirm all API names are valid in target

---

## Migration Runbook

1. (Step 1 — what to do first)
2. (Step 2)
3. (Step 3)
4. (Step 4 — dry run against staging)
5. (Step 5 — production migration)
6. (Step 6 — post-migration validation)

---

## Notes and Deviations

(Record any deviations from the standard pattern, unexpected issues found, and how they were resolved.)
