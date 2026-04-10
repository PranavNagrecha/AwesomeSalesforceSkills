# LLM Anti-Patterns — Subscription Lifecycle Requirements

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ subscription lifecycle requirements. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Describing Amendments as Editing Existing Subscription Records

**What the LLM generates:** "To upgrade a customer from 10 seats to 15 seats, update the `SBQQ__Subscription__c` record's `SBQQ__Quantity__c` field from 10 to 15 using a DML update or a Flow record update action."

**Why it happens:** LLMs default to a CRUD mental model — a change to a data entity means updating the existing record. The CPQ additive ledger model is counterintuitive and is underrepresented in general Salesforce training data compared to standard SOQL/DML patterns.

**Correct pattern:**

```
To upgrade a customer from 10 seats to 15 seats, initiate an amendment from the 
active Contract record. CPQ creates a new delta SBQQ__Subscription__c record with 
SBQQ__Quantity__c = +5, prorated to the co-termination date. The original 10-seat 
subscription record (SBQQ__Quantity__c = 10) is never modified.

To read total entitlement:
SELECT SBQQ__Product__c, SUM(SBQQ__Quantity__c)
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__c = :contractId
GROUP BY SBQQ__Product__c
```

**Detection hint:** Flag any output containing "update the subscription record," "edit SBQQ__Subscription__c," "set SBQQ__Quantity__c on the existing subscription," or "DML update on SBQQ__Subscription__c." All of these indicate the in-place edit anti-pattern.

---

## Anti-Pattern 2: Claiming End Dates Can Be Changed on Existing Contract Subscriptions

**What the LLM generates:** "To extend the contract, update the `SBQQ__EndDate__c` field on the `SBQQ__Subscription__c` records to the new end date using a Flow or Apex trigger."

**Why it happens:** End dates are editable fields in the Salesforce object schema, and LLMs correctly recognize them as writeable. The CPQ package constraint — that these fields are immutable on activated contract subscriptions — is an application-level enforcement that is not visible in the field definition and is not widely documented in training data.

**Correct pattern:**

```
End dates on activated SBQQ__Subscription__c records are immutable.
To extend a contract, create a CPQ amendment from the active Contract.
On the amendment quote, add a new subscription line for the extension period.
CPQ creates a new delta subscription record with the new end date.

The original subscription record's end date remains unchanged.
The renewal quote will use the extended end date from the new delta record.
```

**Detection hint:** Flag any output instructing direct writes to `SBQQ__EndDate__c` on existing `SBQQ__Subscription__c` records. Acceptable only if the record has never been part of an activated contract (e.g., a draft subscription before contract activation).

---

## Anti-Pattern 3: Using the Wrong Proration Formula

**What the LLM generates:** "Prorated amount = (Remaining Days / 365) × Annual Price" or "Prorated amount = Monthly Price × Remaining Months."

**Why it happens:** Multiple proration formulas exist across billing systems, and LLMs blend them. The CPQ-specific formula (Effective Term / Product Term) × Unit Price is not universally applied and the distinction between monthly and daily proration methods is often glossed over.

**Correct pattern:**

```
CPQ proration formula:
Prorated Amount = (Effective Term / Product Term) × Unit Price

Where:
- Effective Term = duration from amendment effective date to co-termination date 
                   (in months if monthly proration, in days if daily proration)
- Product Term   = original subscription term in the same unit
- Unit Price     = contracted unit price (NOT current list price)

Example (monthly proration):
12-month subscription at $1,200/year, amended at month 6:
Effective Term = 6 months, Product Term = 12 months
Prorated Amount = (6 / 12) × $1,200 = $600
```

**Detection hint:** Flag proration formulas that use 365 days as a denominator when the proration method is set to monthly, or that reference "current list price" instead of "contracted unit price" in the numerator.

---

## Anti-Pattern 4: Assuming Amendment Pricing Reflects Updated List Prices

**What the LLM generates:** "After updating the price book entry for Product A to $1,500, the next amendment quote will show the new $1,500 price for existing subscription lines."

**Why it happens:** Standard Salesforce CPQ pricing logic (price rules, price books) is designed to calculate prices dynamically. LLMs generalize this to assume all pricing in CPQ is dynamic, missing the explicit exception for existing subscription lines on amendment quotes.

**Correct pattern:**

```
Existing subscription lines on an amendment quote are locked to the original 
contracted price. Updating the price book entry after contract activation has 
no effect on existing lines in an amendment quote.

Only net-new lines added during the amendment are priced from the current price book.

To apply a new price to an existing subscription line mid-contract, the only 
standard-CPQ approach is the zero-out swap:
1. Remove the existing line (quantity to 0) → generates $0 delta record
2. Add the product as a new line → priced at current price book, prorated to 
   co-termination date → generates new subscription record at new price

This workaround requires custom automation (Apex or Flow) to be repeatable at scale.
```

**Detection hint:** Flag any statement claiming that price book updates, price rule recalculation, or quote recalculation will change the price of an existing subscription line on an amendment quote.

---

## Anti-Pattern 5: Treating Renewal Pricing as Identical to Amendment Pricing

**What the LLM generates:** "Like amendments, renewal quotes will show the contracted price for all lines, so customers will not see price increases at renewal."

**Why it happens:** LLMs often summarize "CPQ locks prices for existing customers" without distinguishing the opposite behaviors of amendment (lock to contracted price) and renewal (reprice at list). The two behaviors are documented separately in Salesforce Help and the distinction is frequently lost in summarization.

**Correct pattern:**

```
Amendment quotes:  existing lines locked to CONTRACTED price (original price book value 
                   at contract signing)
Renewal quotes:    all lines repriced at CURRENT list price (current price book entry 
                   at time of renewal generation)

These are opposite behaviors.

To preserve contracted pricing at renewal, create SBQQ__ContractedPrice__c records 
for the account and product:
- SBQQ__Account__c:   the account being renewed
- SBQQ__Product__c:   the product to lock
- SBQQ__Price__c:     the contracted price to use at renewal

CPQ checks for a matching ContractedPrice record before applying list pricing 
during renewal quote generation.
```

**Detection hint:** Flag any statement that uses the same pricing rule to describe both amendment and renewal behavior, or that claims renewal will automatically use contracted prices without mentioning `SBQQ__ContractedPrice__c` records.

---

## Anti-Pattern 6: Describing Co-Termination as Optional Per Amendment

**What the LLM generates:** "You can choose whether to apply co-termination on a per-amendment basis by toggling the co-termination setting during the amendment process."

**Why it happens:** LLMs conflate the package-level co-termination setting (which is org-wide) with a per-quote or per-amendment toggle that does not exist in standard CPQ.

**Correct pattern:**

```
Co-termination in Salesforce CPQ is configured at the package level via:
Setup > Installed Packages > Salesforce CPQ > Configure > Subscriptions tab 
> Disable Co-Termination (checkbox)

This setting applies to all amendments in the org. There is no native per-amendment 
or per-contract override.

When co-termination is enabled (default):
- All subscription lines on an amendment share the earliest contract end date
- New lines added in an amendment are prorated to the co-termination date

When co-termination is disabled:
- Each line retains its own end date
- New lines receive a full term from the amendment effective date
```

**Detection hint:** Flag any output describing a per-quote, per-amendment, or per-contract co-termination toggle. There is no such native feature in standard CPQ.
