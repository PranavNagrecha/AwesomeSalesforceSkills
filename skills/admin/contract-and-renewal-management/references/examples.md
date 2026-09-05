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

**How to find it in an existing org.** Direct edits leave a fingerprint: subscription records whose last modifier is a human rather than the CPQ integration user, and contracts whose subscription end dates no longer agree with each other after co-termination should have converged them.

```sql
SELECT SBQQ__Contract__c, COUNT_DISTINCT(SBQQ__EndDate__c) distinctEndDates,
       MAX(LastModifiedDate) lastTouched
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__r.StatusCode = 'Activated'
GROUP BY SBQQ__Contract__c
HAVING COUNT_DISTINCT(SBQQ__EndDate__c) > 1
```

Any contract returned has subscription lines that co-termination should have aligned and something has since pulled apart. Cross-check each one against `ContractHistory` before assuming CPQ is at fault — history tracking is available on `Contract` (object_reference.txt L81536–L81537), and it will name the user and the field.

---

## Example 4: Standard Contract Activation Rejected Mid-Load

**Context:** A migration loads 4,200 historical contracts into a new org. Every row carries account, dates, term, signature dates and a status of `Activated`. The insert succeeds for none of them, or — worse, on a second attempt that splits the file — the contracts land as `Draft` and a follow-up update that sets `Status` plus `Renewal_Owner__c` fails on all 4,200 rows.

**Problem:** Two separate platform rules, both stated in the Object Reference `Contract` Usage section, are being violated at once:

1. "Client applications must initially create a Contract in a non-Activated state" (object_reference.txt L81520–L81521). A create with `Status = 'Activated'` is not a shortcut; it is rejected.
2. "the `Status` field is the only field you can update when activating the Contract" (object_reference.txt L81521–L81522). The follow-up update carrying `Status` *and* `Renewal_Owner__c` is rejected as a unit.

There is also a third rule waiting behind those: once a row does activate, "your client application can't change its status" and it can no longer be deleted (object_reference.txt L81523–L81525). A load that activates the wrong rows cannot be rolled back.

**Solution:** Three passes, in this order, with a gate between pass 2 and pass 3.

```bash
# Pass 1 — insert as Draft. Every field EXCEPT Status.
sf data import bulk --sobject Contract --file contracts_draft.csv --target-org prod --wait 30

# Pass 2 — enrich. Signature dates, renewal owner, custom fields. Still Draft.
sf data update bulk --sobject Contract --file contracts_enrich.csv --target-org prod --wait 30

# Pass 3 — activate. Id and Status ONLY. Run last, and only after the gate below.
sf data update bulk --sobject Contract --file contracts_activate.csv --target-org prod --wait 30
```

`contracts_activate.csv` has exactly two columns, and no third one however convenient it would be:

```csv
Id,Status
8001a000000AbCdAAK,Activated
8001a000000AbCeAAK,Activated
```

The gate between pass 2 and pass 3 — run it, read the count, and do not proceed on a non-zero result:

```sql
SELECT COUNT(Id) notReadyToActivate
FROM Contract
WHERE StatusCode = 'Draft'
  AND (AccountId = NULL
       OR StartDate = NULL
       OR ContractTerm = NULL
       OR CompanySignedDate = NULL
       OR CustomerSignedDate = NULL)
```

**Why it works:** Each pass carries only what its rule permits. Pass 1 respects the non-activated-create rule; pass 2 does all the enrichment while the record is still editable and still deletable; pass 3 carries the single field the activating update accepts. The gate exists because pass 3 is irreversible — a contract activated with a null `ContractTerm` has a null `EndDate` forever, and will never appear in a renewal query.

**Note on `EndDate`:** do not put an `EndDate` column in any of these files while `autoCalculateEndDate` is on. It is read-only and calculated from `StartDate` + `ContractTerm` (object_reference.txt L81153–L81160); the column is silently ignored and the load still reports success.
