# LLM Anti-Patterns — Subscription Management Architecture

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ subscription lifecycle architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Updating Existing SBQQ__Subscription__c Records Directly

**What the LLM generates:** Code or instructions that directly update fields (quantity, price, end date) on existing `SBQQ__Subscription__c` records to reflect an amendment:

```apex
// Wrong — LLM-generated "amendment" via DML
SBQQ__Subscription__c sub = [SELECT Id, SBQQ__Quantity__c FROM SBQQ__Subscription__c WHERE ...];
sub.SBQQ__Quantity__c = 750;
update sub;
```

**Why it happens:** LLMs trained on general CRM patterns expect subscription state to be stored in mutable records. The CPQ ledger model (append-only delta records) is counter-intuitive and not common in other platforms, so LLMs default to the mutable record assumption.

**Correct pattern:**

```text
Amendments must be executed through a CPQ Amendment Quote, not via DML:
1. Call SBQQ.ContractManipulationAPI.amend() or use the Amend button.
2. Modify quantities on the amendment quote in the CPQ UI or via SBQQ__QuoteAPI.
3. Activate the amendment quote. CPQ creates NEW delta SBQQ__Subscription__c records.
Never write directly to SBQQ__Quantity__c or SBQQ__NetPrice__c on existing subscription records.
```

**Detection hint:** Look for `update` DML targeting `SBQQ__Subscription__c` with field assignments. Any such pattern is wrong unless it is a system-generated update from CPQ's own managed package code.

---

## Anti-Pattern 2: Reading Latest Subscription Record as Current State

**What the LLM generates:** SOQL queries that ORDER BY CreatedDate DESC and LIMIT 1 to get the "current" subscription for a product:

```soql
-- Wrong: LLM assumes latest record = current state
SELECT SBQQ__Quantity__c, SBQQ__NetPrice__c
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__c = :contractId
  AND SBQQ__Product__c = :productId
ORDER BY CreatedDate DESC
LIMIT 1
```

**Why it happens:** LLMs pattern-match to "get current version" queries in audit-log style data models and assume the most recent record is authoritative. CPQ's ledger model requires aggregation, which LLMs do not infer from schema alone.

**Correct pattern:**

```soql
-- Correct: aggregate all delta records
SELECT SBQQ__Product__c, SUM(SBQQ__Quantity__c) effectiveQty
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__c = :contractId
  AND SBQQ__Product__c = :productId
  AND SBQQ__SubscriptionEndDate__c >= TODAY
GROUP BY SBQQ__Product__c
```

**Detection hint:** Look for `ORDER BY CreatedDate DESC LIMIT 1` on `SBQQ__Subscription__c` queries. Also flag any integration mapping that uses a lookup on `SBQQ__Subscription__c` and does not include aggregation logic.

---

## Anti-Pattern 3: Enabling Both Preserve Bundle Structure and Combine Subscription Quantities

**What the LLM generates:** CPQ Settings configuration advice that enables both settings to "get the best of both worlds":

```text
-- Wrong: LLM recommends enabling both
SBQQ__PreserveBundleStructure__c = true   (to maintain bundle hierarchy)
SBQQ__CombineSubscriptionQuantities__c = true  (to simplify reporting)
"This will preserve your bundle relationships AND keep your subscription data clean."
```

**Why it happens:** LLMs read each setting's description independently and conclude they are compatible because they address different concerns. The silent mutual exclusion is not documented in a way that LLMs reliably extract from training data.

**Correct pattern:**

```text
Choose ONE:
Option A — Preserve Bundle Structure only:
  SBQQ__PreserveBundleStructure__c = true
  SBQQ__CombineSubscriptionQuantities__c = false
  Use when: bundle products exist on contracts. Bundle child subscriptions 
            must remain linked to bundle parents.

Option B — Combine Subscription Quantities only:
  SBQQ__PreserveBundleStructure__c = false (or not set)
  SBQQ__CombineSubscriptionQuantities__c = true
  Use when: no bundle products; simplified subscription ledger is required.
  
Never enable both simultaneously.
```

**Detection hint:** Check CPQ Settings metadata for both `SBQQ__PreserveBundleStructure__c = true` and `SBQQ__CombineSubscriptionQuantities__c = true` appearing together.

---

## Anti-Pattern 4: Ignoring Async Job Completion Before Triggering Billing

**What the LLM generates:** Code that calls the async amendment API and immediately activates the Contract or triggers billing:

```apex
// Wrong: activate immediately after async call
SBQQ.ContractManipulationAPI.amend(ctx);
contract.Status = 'Activated';
update contract;  // Billing fires before amendment job completes
```

**Why it happens:** LLMs default to sequential synchronous reasoning. The concept of "fire async and wait before proceeding" requires LLMs to reason about eventual consistency, which they often fail to apply unless explicitly prompted. The async CPQ amendment API is also less commonly documented in LLM training data than the synchronous path.

**Correct pattern:**

```apex
// Correct: async amendment with completion gate
SBQQ.ContractManipulationAPI.amend(ctx);
// Do NOT update contract status here.
// Schedule a job to poll AsyncApexJob for SBQQ.AmendmentBatchJob completion.
// Only after Status = 'Completed':
//   → Review amendment quote
//   → Approve amendment quote  
//   → Set contract Status = 'Activated'
//   → Billing schedules generate against complete subscription data
```

**Detection hint:** Look for `Status = 'Activated'` DML on Contract within the same transaction or immediately after a call to `SBQQ.ContractManipulationAPI.amend()`. Also flag any Flow that sets Contract Status without checking for pending `AsyncApexJob` records.

---

## Anti-Pattern 5: Treating Price Change as a Direct Amendment Line Edit

**What the LLM generates:** Instructions to edit the unit price field directly on an existing subscription line in the amendment quote:

```text
-- Wrong: LLM instructs direct price override on existing line
1. Open the amendment quote.
2. Find the existing "Professional Services Hours" line.
3. Click the price field and enter the new negotiated price ($170).
4. Save and calculate.
```

**Why it happens:** LLMs generalize from other quoting systems where amendment quotes allow price overrides on all lines. CPQ's distinction between locked existing lines and editable new lines is a platform-specific constraint that LLMs do not reliably retain.

**Correct pattern:**

```text
Swap pattern for mid-contract price changes:
1. In the amendment quote, set Quantity = 0 on the existing product line.
   → This generates a zero-out delta subscription record.
2. Add a new line for the same product with the new negotiated price.
   → This generates a new-price delta subscription record.
3. Calculate the quote. CPQ co-terms and prorates the new line.
4. Approve and activate.
Result: effective subscription state reflects new price from amendment date.
```

**Detection hint:** Flag any instruction that says "edit the price on the existing line" or "override the unit price on the amendment quote" for a product that was on the original contract. The correct answer always involves the swap pattern (zero out + add new).

---

## Anti-Pattern 6: Assuming Renewal Quotes Use Contracted Prices by Default

**What the LLM generates:** Advice stating that renewal quotes will automatically carry forward the customer's negotiated prices from the original contract:

```text
-- Wrong: LLM assumes contracted prices flow to renewals automatically
"When the renewal quote is generated, it will use the same contracted 
prices the customer has been paying. No price adjustments are needed."
```

**Why it happens:** LLMs observe that amendment quotes lock existing lines at contracted price and incorrectly generalize this behavior to renewal quotes. The distinction (amendments = locked contracted price; renewals = current list price) is a subtle platform-specific asymmetry.

**Correct pattern:**

```text
Renewal quotes reprice at CURRENT LIST PRICE by default — not contracted price.

To carry forward negotiated pricing to renewals:
1. Create SBQQ__ContractedPrice__c records linking:
   - Account (SBQQ__Account__c)
   - Product (SBQQ__Product__c) 
   - Price (SBQQ__Price__c)
   before the renewal quote is generated.
2. The CPQ pricing engine reads ContractedPrice records during renewal 
   quote calculation and applies them instead of the price book price.

Without ContractedPrice records, every renewal quote shows list price 
regardless of the customer's historical negotiated pricing.
```

**Detection hint:** Flag any claim that renewal quotes "inherit" or "carry forward" contracted prices without explicitly mentioning `SBQQ__ContractedPrice__c` records. Also flag advice that omits the need to create ContractedPrice records before renewal quote generation.
