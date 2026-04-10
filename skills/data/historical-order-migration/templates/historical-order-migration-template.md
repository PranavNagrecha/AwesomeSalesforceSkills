# Historical Order Migration — Work Template

Use this template when working on a CPQ historical order migration task.

## Scope

**Skill:** `historical-order-migration`

**Request summary:** (fill in what the user asked for)

---

## Org Configuration

| Setting | Value |
|---|---|
| CPQ Renewal Model | `Contract Based` / `Asset Based` (confirm before proceeding) |
| CPQ Package Version | (e.g., 240.x) |
| Background Pricing disabled before load | Yes / No |
| Price Rules disabled before load | Yes / No |
| Product Rules disabled before load | Yes / No |
| Amendments required (Assets needed) | Yes / No |

---

## Data Profile

| Object | Source Record Count | External ID Field |
|---|---|---|
| Account | (already in org / to be loaded) | Legacy_Account_Id__c |
| Opportunity | (already in org / to be loaded) | Legacy_Opportunity_Id__c |
| Product2 / SBQQ__Product__c | | Legacy_Product_Id__c |
| SBQQ__Quote__c | | Legacy_Quote_Id__c |
| SBQQ__QuoteLine__c | | Legacy_QuoteLine_Id__c |
| Contract | | Legacy_Contract_Id__c |
| SBQQ__Subscription__c | | Legacy_Subscription_Id__c |
| SBQQ__Asset__c | | Legacy_Asset_Id__c |

---

## Load Sequence

Follow this order exactly. Do not proceed to a step until the previous step's record count is confirmed.

- [ ] Step 1: Confirm CPQ Renewal Model = Contract Based
- [ ] Step 2: Disable CPQ background pricing, price rules, and product rules
- [ ] Step 3: Insert SBQQ__Quote__c (Status=Approved, Primary=true)
  - Confirmed record count: ___
- [ ] Step 4: Insert SBQQ__QuoteLine__c
  - Confirmed record count: ___
- [ ] Step 5: Insert Contract (SBQQ__Quote__c field populated)
  - Confirmed record count: ___
- [ ] Step 6: Insert SBQQ__Subscription__c at batch size 1
  - Confirmed record count: ___
- [ ] Step 7: Insert SBQQ__Asset__c at batch size 1 (if amendments required)
  - Confirmed record count: ___
- [ ] Step 8: Update Contract Status to Activated
- [ ] Step 9: Re-enable CPQ price rules, product rules, background pricing
- [ ] Step 10: Run post-load validation queries (see below)

---

## Batch Size Configuration

| Tool | Setting | Required Value |
|---|---|---|
| Data Loader | Batch size | 1 |
| Bulk API 2.0 | Not recommended for CPQ objects | Use REST API single-record inserts |
| Custom ETL | Records per API call | 1 |

---

## Required Field Mapping — SBQQ__Quote__c

| Source Field | Target Field | Required Value |
|---|---|---|
| (legacy quote ID) | Legacy_Quote_Id__c | (external ID) |
| (account ID) | SBQQ__Account__c | (Account external ID ref) |
| (opportunity ID) | SBQQ__Opportunity2__c | (Opportunity external ID ref) |
| (start date) | SBQQ__StartDate__c | YYYY-MM-DD |
| (end date) | SBQQ__EndDate__c | YYYY-MM-DD |
| (term months) | SBQQ__SubscriptionTerm__c | numeric |
| — hardcoded — | SBQQ__Status__c | Approved |
| — hardcoded — | SBQQ__Primary__c | true |

---

## Required Field Mapping — SBQQ__Subscription__c

| Source Field | Target Field | Notes |
|---|---|---|
| (legacy sub ID) | Legacy_Subscription_Id__c | external ID |
| (contract ID) | SBQQ__Contract__c | Contract external ID ref |
| (product ID) | SBQQ__Product__c | Product2 external ID ref |
| (start date) | SBQQ__StartDate__c | subscription start |
| (end date) | SBQQ__EndDate__c | subscription end |
| (quantity) | SBQQ__Quantity__c | numeric |
| (list price) | SBQQ__RegularPrice__c | pre-discount unit price |
| (net price) | SBQQ__NetPrice__c | post-discount unit price |
| (customer price) | SBQQ__CustomerPrice__c | price shown on renewal |
| (subscription type) | SBQQ__SubscriptionType__c | Renewable / One-time |

---

## Asset Field Rules

| Scenario | SBQQ__RootId__c | SBQQ__RevisedAsset__c |
|---|---|---|
| Original (root) asset | null | null |
| Revised (amended) asset | **null (must be null)** | <ID of replaced asset> |

---

## Post-Load Validation Queries

```soql
-- 1. Subscription count per contract (compare to source)
SELECT SBQQ__Contract__c, COUNT(Id) subCount
FROM SBQQ__Subscription__c
GROUP BY SBQQ__Contract__c
ORDER BY COUNT(Id) DESC
LIMIT 100

-- 2. Subscriptions missing required renewal fields
SELECT Id, SBQQ__Contract__c, SBQQ__Product__c, SBQQ__StartDate__c, SBQQ__EndDate__c
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__c = null
   OR SBQQ__Product__c = null
   OR SBQQ__StartDate__c = null
   OR SBQQ__EndDate__c = null
   OR SBQQ__Quantity__c = null

-- 3. Contracts not in Activated status
SELECT Id, AccountId, Status, SBQQ__Quote__c
FROM Contract
WHERE Status != 'Activated'
  AND SBQQ__Quote__c != null

-- 4. Quotes not Approved and Primary
SELECT Id, SBQQ__Status__c, SBQQ__Primary__c
FROM SBQQ__Quote__c
WHERE SBQQ__Status__c != 'Approved'
   OR SBQQ__Primary__c = false

-- 5. Asset records with both Root Id and Revised Asset populated (must be zero)
SELECT Id, SBQQ__RootId__c, SBQQ__RevisedAsset__c
FROM SBQQ__Asset__c
WHERE SBQQ__RootId__c != null
  AND SBQQ__RevisedAsset__c != null
```

---

## Notes and Deviations

(Record any deviations from the standard pattern and the business reason for each)

- Deviation 1:
- Deviation 2:
