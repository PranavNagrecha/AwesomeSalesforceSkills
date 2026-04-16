# CPQ Deployment Patterns — Work Template

Use this template when planning or executing a CPQ configuration deployment between Salesforce environments.

## Scope

- Source org: ___________
- Target org: ___________
- Deployment type: [ ] Full CPQ config  [ ] Incremental (products/rules only)
- Data migration tool: [ ] SFDMU  [ ] Data Loader  [ ] Copado Data Deploy  [ ] Prodly

---

## Pre-Deployment Checklist

- [ ] External ID fields exist on all CPQ objects in source AND target org
- [ ] External IDs populated for all CPQ records in source org (no blanks)
- [ ] Metadata deployment (custom objects, fields, Apex) completed first
- [ ] Target org has CPQ managed package installed at correct version
- [ ] SFDMU or data tool configured with External ID upsert keys

---

## CPQ Data Load Order

| Step | Object | Depends On | External ID Field | Status |
|---|---|---|---|---|
| 1 | Pricebook2 | None | CPQ_External_Id__c | |
| 2 | SBQQ__DiscountCategory__c | None | CPQ_External_Id__c | |
| 3 | Product2 | None | CPQ_External_Id__c | |
| 4 | PricebookEntry | Product2 + Pricebook2 | (composite) | |
| 5 | SBQQ__PricingRule__c | Product2, Pricebook2 | CPQ_External_Id__c | |
| 6 | SBQQ__ProductRule__c | Product2, PricingRule | CPQ_External_Id__c | |
| 7 | SBQQ__QuoteTemplate__c | Products, Rules | CPQ_External_Id__c | |

---

## SFDMU export.json Key Configuration

```json
{
  "objects": [
    {
      "query": "SELECT Id, CPQ_External_Id__c, ... FROM SBQQ__PricingRule__c",
      "operation": "Upsert",
      "externalId": "CPQ_External_Id__c",
      "master": false
    }
  ]
}
```

---

## Post-Deployment Validation

```sql
-- CPQ configuration record counts
SELECT COUNT() FROM SBQQ__PricingRule__c
SELECT COUNT() FROM SBQQ__ProductRule__c
SELECT COUNT() FROM SBQQ__QuoteTemplate__c

-- Spot check relationship integrity
SELECT Id, SBQQ__Product__r.Name FROM SBQQ__PricingRule__c LIMIT 10
```

- [ ] Test CPQ quote generated for Scenario 1: ___________
- [ ] Test CPQ quote generated for Scenario 2: ___________
- [ ] Pricing results match source org expected pricing

---

## Notes

_Capture External ID strategy decisions, self-referential object handling, and open questions._
