# LLM Anti-Patterns — Contract and Renewal Management

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ contract and renewal management. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming List Price Updates Propagate to Amendment Subscription Lines

**What the LLM generates:** Advice such as "update the Price Book Entry for the product and the amendment quote will reflect the new price" or code that updates `PricebookEntry.UnitPrice` expecting the change to appear on existing amendment lines.

**Why it happens:** LLMs generalize from standard Salesforce quoting behavior, where Price Book Entry changes affect quote lines upon recalculation. CPQ amendment quotes are a special case: existing subscription lines are locked to their original contracted price regardless of Price Book Entry updates.

**Correct pattern:**

```
Existing subscription lines on an amendment quote are priced from SBQQ__Subscription__c.SBQQ__NetPrice__c
(the original contracted price), not from the current Price Book Entry.
To change the price of an existing line mid-contract, create a SBQQ__ContractedPrice__c record
for the account/product combination with the corrected price before generating the amendment quote.
New lines added during the amendment do use the current Price Book Entry.
```

**Detection hint:** Look for any advice that says "recalculate the quote" to update prices on existing subscription lines in an amendment context. If the suggestion is about existing lines (not new additions), flag it as incorrect.

---

## Anti-Pattern 2: Recommending Direct SBQQ__Subscription__c Record Edits

**What the LLM generates:** Apex snippets or instructions that directly update fields on `SBQQ__Subscription__c` records (e.g., `sub.SBQQ__Quantity__c = newQty; update sub;`) as a way to fix subscription data without going through an amendment.

**Why it happens:** Direct record updates are the idiomatic Apex pattern for field corrections. LLMs apply this pattern broadly without recognizing that CPQ subscription records are maintained by the CPQ managed package and must be modified through the amendment workflow to stay consistent with quote history.

**Correct pattern:**

```
Never directly update SBQQ__Subscription__c records.
Always generate an Amendment Quote via the Amend button (or SBQQ.ContractManipulationAPI.amend())
and make changes through the CPQ quote editor.
This ensures proration, co-termination, approval routing, and audit history are maintained.
```

**Detection hint:** Any `update` DML on `SBQQ__Subscription__c` outside of a unit test or data migration context is a red flag. Flag code that modifies `SBQQ__Quantity__c`, `SBQQ__EndDate__c`, or `SBQQ__NetPrice__c` directly on subscription records.

---

## Anti-Pattern 3: Cloning a Quote as a Renewal

**What the LLM generates:** Instructions to clone the original Opportunity and its Quote as a "renewal," or Apex code that creates a new Opportunity and Quote by copying fields from the expiring contract without setting `SBQQ__RenewedContract__c`.

**Why it happens:** LLMs are familiar with the generic Salesforce "clone record" pattern and may apply it to renewals without knowing that CPQ requires a specific contract chain linkage via `SBQQ__RenewedContract__c` on the Renewal Opportunity.

**Correct pattern:**

```
Generate renewals using the Renew button on the active Contract record, which automatically:
1. Creates a Renewal Opportunity with SBQQ__RenewedContract__c = the expiring Contract Id
2. Creates a Renewal Quote linked to that Opportunity
3. Reprices lines at current Price Book (or Contracted Price if applicable)

If creating renewals programmatically, the Renewal Opportunity record MUST have:
  SBQQ__RenewedContract__c = <expiring_contract_id>
Without this, contract history chaining and contracted price inheritance are broken.
```

**Detection hint:** Any renewal creation flow that does not set `SBQQ__RenewedContract__c` on the Opportunity is incorrect. Search generated code for "renewal" plus "Opportunity" — if `SBQQ__RenewedContract__c` is absent, flag it.

---

## Anti-Pattern 4: Ignoring Async Requirements for Large-Scale Amendments

**What the LLM generates:** Instructions to click the Amend button or call synchronous amendment methods for contracts with large numbers of subscription lines, without checking line count or recommending the async API path.

**Why it happens:** LLMs default to the simplest path (UI button or synchronous API call) and do not model the governor limit constraints that make synchronous amendment fail at scale. The 1,000-line threshold is CPQ-specific knowledge that is not broadly represented in training data.

**Correct pattern:**

```
Before amending, check subscription line count:
  SELECT COUNT() FROM SBQQ__Subscription__c WHERE SBQQ__Contract__c = :contractId

If count > 1000: use SBQQ.ContractManipulationAPI.amend(contractId) (async batch)
If count < ~200: synchronous Amend button is safe
Between 200–1000: test in sandbox first

Monitor async job:
  SELECT Id, Status, ExtendedStatus FROM AsyncApexJob
  WHERE ApexClass.Name LIKE '%Amendment%'
  ORDER BY CreatedDate DESC LIMIT 5
```

**Detection hint:** Any amendment advice for enterprise or large accounts that does not mention line count or async processing is potentially incomplete. Flag answers that only recommend the Amend button without qualifying the scale threshold.

---

## Anti-Pattern 5: Treating Renewal Pricing as Equivalent to Amendment Pricing

**What the LLM generates:** Explanations that renewals "preserve the contracted price like amendments do" or advice that renewal quotes will automatically show the same price the customer was paying.

**Why it happens:** LLMs conflate amendment behavior (existing lines locked to contracted price) with renewal behavior (lines repriced at current list). The two workflows have opposite pricing semantics, and this distinction is easy to miss without specific CPQ knowledge.

**Correct pattern:**

```
Amendment quotes: existing lines are locked to the original contracted price.
Renewal quotes: ALL lines are repriced at the current Price Book Entry price.

If a customer has negotiated rates that should carry into renewal:
  Create SBQQ__ContractedPrice__c records for the Account/Product combinations.
  CPQ will use these over the Price Book Entry when generating the renewal quote.

Without ContractedPrice records, assume the renewal quote will show list pricing,
which may be higher than what the customer was paying.
```

**Detection hint:** Any statement that renewal quotes "inherit" or "preserve" contract pricing without qualifying that `SBQQ__ContractedPrice__c` records are required for this to work is misleading. Flag it.

---

## Anti-Pattern 6: Activating a Contract or Order in the Same DML as the Field Edits

**What the LLM generates:** A single `update` that sets `Status = 'Activated'` alongside signature dates, an owner, or custom fields — in Apex, in a Flow's Update Records element, or as one Data Loader file:

```apex
// WRONG — the platform rejects this whole update.
c.CompanySignedDate = Date.today();
c.CustomerSignedDate = Date.today();
c.Status = 'Activated';
update c;
```

**Why it happens:** Batching field changes into one DML is the correct instinct everywhere else on the platform, and nothing in the field metadata hints otherwise — `Status`, `CompanySignedDate` and `CustomerSignedDate` all carry the `Update` property.

**Correct pattern:**

```apex
// Pass 1 — everything except Status, while the record is still Draft.
c.CompanySignedDate = signedByUs;
c.CustomerSignedDate = signedByThem;
c.Renewal_Owner__c = renewalDeskUserId;
update c;

// Pass 2 — Status alone. Irreversible: after this the status cannot change
// and the record cannot be deleted.
Contract activation = new Contract(Id = c.Id, Status = 'Activated');
update activation;
```

The Object Reference is explicit for both objects: "the `Status` field is the only field you can update when activating the Contract", and the same sentence appears for Order.

**Detection hint:** Any DML, Flow Update Records element, or CSV column set that includes `Status` *and* any other field on `Contract` or `Order`. Flag it regardless of how the status value is spelled.

---

## Anti-Pattern 7: Filtering Contracts on the `Status` Label Instead of the `StatusCode` Category

**What the LLM generates:** Renewal queries, report filters, Flow entry criteria and validation rules keyed on `Status = 'Activated'` — and, related, advice to "check the `IsActivated` field", which does not exist on `Contract`.

**Why it happens:** `Status` is the visible field and `Activated` is its out-of-the-box label, so the label reads like the state. `StatusCode` looks like an internal duplicate rather than the category the label belongs to. The invented `IsActivated` comes from generalising the platform's `IsClosed` / `IsWon` convention.

**Correct pattern:**

```sql
-- Correct: StatusCode is the category, so any Activated-category label matches.
SELECT Id, ContractNumber, EndDate, Status, StatusCode
FROM Contract
WHERE StatusCode = 'Activated'
  AND EndDate >= TODAY
  AND EndDate <= :cutoffDate

-- Wrong: matches only the literal label. A contract whose Status is
-- 'Activated - Renewal Pending' is in the Activated category and is missed.
-- WHERE Status = 'Activated'
```

There is no `IsActivated` boolean. Activation is evidenced by `StatusCode = 'Activated'`, with `ActivatedById` and `ActivatedDate` recording who and when.

**Detection hint:** Grep generated SOQL, formulas and Flow conditions for `Status = 'Activated'` on `Contract` or `Order` without a nearby `StatusCode`, and for any reference to `Contract.IsActivated`. Formulas are the exception that still needs care: they cannot reach the category, so an `ISPICKVAL(Status, ...)` gate must enumerate every Activated-category label rather than assume one.
