# Examples — Contract and Renewal Management

## Example 1: Contract Creation Fails to Generate Subscription Records

**Context:** A sales rep closes an Opportunity as Won and sets `SBQQ__Contracted__c = true`. The system creates a Contract record, but no `SBQQ__Subscription__c` child records appear. The Amend and Renew buttons are missing from the Contract.

**Problem:** Without subscription records, the entire CPQ contract lifecycle breaks. There is nothing to amend or renew. This silently produces incomplete contracts that appear valid but cannot be managed via CPQ.

**Solution:**

Diagnose by checking the Quote Lines on the primary Quote:

```sql
SELECT Id, SBQQ__Product__c, SBQQ__SubscriptionPricing__c, SBQQ__SubscriptionType__c
FROM SBQQ__QuoteLine__c
WHERE SBQQ__Quote__c = '<primary_quote_id>'
```

Expected: at least one line with `SBQQ__SubscriptionPricing__c` set to `Fixed Price` or `Percent Of Total`, and `SBQQ__SubscriptionType__c` set to `Renewable` or `Evergreen`.

If `SBQQ__SubscriptionPricing__c` is blank on all lines, open the product record and set the **Subscription Pricing** field on the product. Reconfigure the quote, re-close the Opportunity, or if the Contract was already created, delete and re-create it after fixing the product configuration.

**Why it works:** CPQ's contract creation logic only materializes `SBQQ__Subscription__c` records for Quote Lines that have both a subscription type and a subscription pricing model. This data comes from the Product record and must be set before the quote is created.

---

## Example 2: Amendment Quote Shows Wrong Prices on New Lines

**Context:** A customer's contract is being amended to add a new product. The admin creates the amendment quote, but the new line is showing last year's list price rather than the current price book price.

**Problem:** The amendment was created correctly, but the Price Book on the Amendment Quote was not updated to the current Price Book entry version, or a price rule is applying a stale price override.

**Solution:**

1. On the Amendment Quote record, confirm the **Price Book** lookup points to the correct active Price Book.
2. Check for `SBQQ__PriceRule__c` records with conditions that match the new product — a rule may be injecting a hardcoded price.
3. Re-calculate the quote from the CPQ quote editor to force a fresh price calculation cycle.

```sql
-- Confirm the price book entry for the new product
SELECT Id, UnitPrice, IsActive
FROM PricebookEntry
WHERE Product2Id = '<product_id>'
AND Pricebook2Id = '<pricebook_id>'
AND IsActive = true
```

If the `PricebookEntry` shows the correct current price but the quote line shows a different value, a price rule is overriding it. Review rules in CPQ Settings > Price Rules filtered to the product.

**Why it works:** New lines added during an amendment are priced from the Price Book at calculation time, not from the original contracted price. If the price is wrong, either the Price Book entry is stale or a price rule is interfering.

---

## Example 3: Renewal Quote Term Is Incorrect

**Context:** A 12-month contract expires and the admin generates a renewal quote, but the renewal quote defaults to a 24-month term instead of 12 months.

**Problem:** `SBQQ__DefaultRenewalTerm__c` on the Contract is set to 24, overriding the CPQ Settings default. This is likely left over from a manual edit or a workflow that set it incorrectly.

**Solution:**

```sql
-- Check the DefaultRenewalTerm on the Contract
SELECT Id, SBQQ__DefaultRenewalTerm__c, SBQQ__RenewalTerm__c, EndDate
FROM Contract
WHERE Id = '<contract_id>'
```

If `SBQQ__DefaultRenewalTerm__c = 24` and the correct term is 12, update the Contract record before generating the renewal:

```apex
Contract c = [SELECT Id, SBQQ__DefaultRenewalTerm__c FROM Contract WHERE Id = :contractId];
c.SBQQ__DefaultRenewalTerm__c = 12;
update c;
```

Then re-generate the renewal quote by clicking Renew on the Contract.

**Why it works:** CPQ reads `SBQQ__DefaultRenewalTerm__c` at renewal quote creation time. Fixing the Contract field before initiating renewal ensures the correct term flows into the Renewal Quote.

---

## Anti-Pattern: Directly Editing SBQQ__Subscription__c Records

**What practitioners do:** To "quickly" fix a subscription price or end date without going through the amendment process, admins or developers directly update `SBQQ__Subscription__c` field values in Setup or via anonymous Apex.

**What goes wrong:** CPQ's amendment and renewal logic reads subscription data as the source of truth for future contracts. Directly modifying subscriptions bypasses validation logic, skips proration recalculation, and produces subscription records whose data no longer matches the quote line history. When a renewal quote is later generated, the renewal lines may have incorrect prices, incorrect terms, or may fail to generate at all if referencing subscription records in an inconsistent state.

**Correct approach:** Always make changes through an Amendment Quote. Even for a single field change (like a quantity correction), go through the CPQ Amend flow. This ensures proration is calculated, approval workflows are triggered, and the contract and subscription records stay in sync with quote history.
