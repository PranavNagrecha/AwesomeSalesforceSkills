# Contract and Renewal Management — Work Template

Use this template when working on CPQ contract creation, amendment, or renewal tasks.

## Scope

**Skill:** `contract-and-renewal-management`

**Request summary:** (fill in what the user asked for — e.g., "configure amendment quote for Account X" or "debug missing subscription records on Contract Y")

---

## Context Gathered

Answer these before starting. Refer to SKILL.md → Before Starting for guidance.

- **CPQ package version:** (e.g., 240.x — check Installed Packages)
- **Task type:** [ ] Contract Creation  [ ] Amendment  [ ] Renewal  [ ] Debugging
- **Number of subscription lines on the contract:** (if amendment — determines sync vs async)
- **CPQ Setting — Default Renewal Term:** (months — check CPQ Settings > Subscriptions & Renewals)
- **CPQ Setting — Co-Termination behavior:** [ ] Earliest End Date  [ ] End of Term
- **CPQ Setting — Auto Renew:** [ ] Enabled  [ ] Disabled
- **Contracted Price records exist for this account:** [ ] Yes  [ ] No  [ ] Unknown
- **Amendment scale:** [ ] <200 lines (sync OK)  [ ] 200–1000 lines (test in sandbox)  [ ] 1000+ lines (async required)

---

## Pre-Flight Checks

Run these SOQL queries to validate prerequisites before starting work.

### Check Quote Lines for Subscription Pricing

```sql
SELECT Id, Name, SBQQ__SubscriptionPricing__c, SBQQ__SubscriptionType__c, SBQQ__Product__r.Name
FROM SBQQ__QuoteLine__c
WHERE SBQQ__Quote__c = '<primary_quote_id>'
ORDER BY SBQQ__Product__r.Name
```

Expected: at least one line with `SBQQ__SubscriptionPricing__c` = `Fixed Price` or `Percent Of Total`.

### Check Subscription Records on Contract

```sql
SELECT Id, SBQQ__Product__r.Name, SBQQ__Quantity__c, SBQQ__NetPrice__c,
       SBQQ__StartDate__c, SBQQ__EndDate__c
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__c = '<contract_id>'
ORDER BY SBQQ__EndDate__c ASC
```

Note the earliest `SBQQ__EndDate__c` — this is the co-termination date for any amendment.

### Check Contract Renewal Fields

```sql
SELECT Id, SBQQ__DefaultRenewalTerm__c, SBQQ__RenewalQuoted__c, SBQQ__RenewedContract__c, EndDate
FROM Contract
WHERE Id = '<contract_id>'
```

---

## Approach

Which pattern from SKILL.md applies? (tick one and note why)

- [ ] **Standard Amendment** — <200 subscription lines, UI Amend button
- [ ] **Async Large-Scale Amendment** — 1000+ lines, `SBQQ.ContractManipulationAPI.amend()`
- [ ] **Renewal Quote Generation** — Contract approaching expiration, using Renew button
- [ ] **Debug: Missing Subscriptions** — No `SBQQ__Subscription__c` records after contract creation
- [ ] **Debug: Incorrect Pricing** — Pricing on amendment or renewal quote is unexpected

**Reason this pattern applies:** (fill in)

---

## Execution Steps

For Amendment (Standard):

1. [ ] Navigate to the active Contract record — confirm Status = `Activated`
2. [ ] Click **Amend** button
3. [ ] In the CPQ quote editor, existing lines are locked (expected) — do not attempt to edit their prices
4. [ ] Add new products or adjust quantities as required
5. [ ] Click **Calculate** — confirm co-termination date and prorated amounts are correct
6. [ ] Submit for approval if required
7. [ ] Activate the amendment quote
8. [ ] Confirm Contract and Subscription records are updated

For Renewal:

1. [ ] Confirm `SBQQ__DefaultRenewalTerm__c` on the Contract is correct
2. [ ] Click **Renew** button on the active Contract
3. [ ] Confirm Renewal Opportunity is created with `SBQQ__RenewedContract__c` set
4. [ ] Review Renewal Quote pricing — compare against expiring contract (prices will be at current list unless ContractedPrice records exist)
5. [ ] Negotiate adjustments, recalculate, approve, and activate

For Async Amendment (1000+ lines):

1. [ ] Trigger amendment via `SBQQ.ContractManipulationAPI.amend('<contract_id>')`
2. [ ] Monitor `AsyncApexJob` for completion:
   ```sql
   SELECT Id, Status, ExtendedStatus, NumberOfErrors
   FROM AsyncApexJob
   WHERE ApexClass.Name LIKE '%Amendment%'
   ORDER BY CreatedDate DESC LIMIT 5
   ```
3. [ ] On success, proceed with amendment review and approval
4. [ ] On failure, check `ExtendedStatus` for error details and remediate

---

## Pricing Verification

After amendment or renewal quote generation:

| Line | Expected Price Source | Actual Price on Quote | Match? |
|---|---|---|---|
| Existing subscription line (amendment) | Original contracted price (SBQQ__Subscription__c.SBQQ__NetPrice__c) | | |
| New line added in amendment | Current Price Book Entry | | |
| Renewal line | Current Price Book Entry (or ContractedPrice__c if exists) | | |

---

## Checklist

- [ ] `SBQQ__Contracted__c = true` on Opportunity AND at least one Quote Line has `SBQQ__SubscriptionPricing__c` populated
- [ ] CPQ Settings reviewed: Renewal Term, Co-Termination, Auto Renew
- [ ] For amendment: existing lines show original contracted price (not updated list price)
- [ ] Co-termination end dates verified — all amendment lines end on the earliest subscription end date
- [ ] For async amendment: `AsyncApexJob` monitored and confirmed `Status = Completed`
- [ ] Renewal Opportunity has `SBQQ__RenewedContract__c` set (not a cloned quote)
- [ ] `SBQQ__DefaultRenewalTerm__c` correct on Contract before renewal generation
- [ ] Amendment or Renewal Quote approved and activated — Contract Status = `Activated`
- [ ] Subscription records updated and reflect changes

---

## Notes

(Record any deviations from the standard pattern, edge cases encountered, and why a specific approach was chosen.)
