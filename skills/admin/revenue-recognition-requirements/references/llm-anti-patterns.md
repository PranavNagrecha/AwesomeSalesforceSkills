# LLM Anti-Patterns — Revenue Recognition Requirements

Common mistakes AI coding assistants make when generating or advising on Salesforce Billing revenue recognition configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing OpportunityLineItem Revenue Schedules with blng__RevenueSchedule__c

**What the LLM generates:** Instructions to "enable Revenue Schedules in Setup > Products > Schedule Settings" and populate the `Revenue Schedules` related list on OpportunityLineItems or Products. The LLM may also reference the `OpportunityLineItemSchedule` standard object as the mechanism for ASC 606 revenue recognition in Salesforce Billing orgs.

**Why it happens:** Standard Salesforce documentation and training content covers the native "Revenue Schedules" feature heavily. LLMs trained on Salesforce content conflate "revenue schedule" terminology between the standard CRM feature and the Salesforce Billing managed package object because both share the same plain-English name. The blng__ namespace distinction is not prominent in generalist training data.

**Correct pattern:**

```
In a Salesforce Billing org, revenue recognition is driven by:
1. blng__RevenueRecognitionRule__c — set on Product2 (lookup field)
2. blng__RevenueSchedule__c — auto-generated at Order activation (one per OrderProduct)
3. blng__RevenueTransaction__c — GL event records generated as Finance Periods close

Do NOT enable "Revenue Schedules" in standard Setup to influence Billing behavior.
Configure blng__RevenueRecognitionRule__c on Product2 and let Billing create
blng__RevenueSchedule__c records at Order activation.
```

**Detection hint:** Any response that references `OpportunityLineItemSchedule`, "Setup > Products > Schedule Settings", or the `Revenue Schedules` related list on OpportunityLineItem in the context of Salesforce Billing revenue recognition is incorrect.

---

## Anti-Pattern 2: Claiming Revenue Schedules Auto-Update on Contract Amendment

**What the LLM generates:** Guidance that says "when you create an amendment order in Salesforce CPQ Billing, the revenue schedule automatically updates to reflect the new contract value" or "the existing blng__RevenueSchedule__c is recalculated when the amendment order is activated."

**Why it happens:** LLMs often generalize from billing schedule behavior (where amendments create net-new schedule lines that adjust future invoices) to revenue schedules. The mental model of "amendment = auto-update" is consistent across many billing systems, so the LLM applies it here incorrectly.

**Correct pattern:**

```
Revenue schedules do NOT auto-update on amendment.

When an amendment order is activated:
- A NEW blng__RevenueSchedule__c is created for the delta OrderProduct only.
- The ORIGINAL blng__RevenueSchedule__c is unchanged.
- Manual reconciliation is required if Finance requires a single consolidated schedule.

Never tell a practitioner to "wait for the revenue schedule to update" —
they must query both schedules and confirm the ERP integration sums them correctly.
```

**Detection hint:** Any phrase like "automatically recalculates," "updates the revenue schedule," or "the amendment reflects in the existing schedule" signals this anti-pattern.

---

## Anti-Pattern 3: Forgetting Finance Period as a Prerequisite for Schedule Generation

**What the LLM generates:** A step-by-step Order activation guide that lists: (1) configure Revenue Recognition Rule, (2) assign to Product2, (3) activate Order, (4) verify blng__RevenueSchedule__c — with no mention of Finance Period prerequisites.

**Why it happens:** Finance Periods are a Salesforce Billing-specific administrative object not covered in most Salesforce certifications or general CRM training. LLMs trained on generalist Salesforce content do not have strong signal that Finance Periods are a hard prerequisite for revenue schedule generation. The silent failure mode (no error, no schedule) makes this particularly dangerous because the workflow appears to complete successfully.

**Correct pattern:**

```
BEFORE activating any Order in a revenue-recognition-enabled org:

Step 0: Verify Finance Periods
  SELECT Id, Name, blng__StartDate__c, blng__EndDate__c, blng__Status__c
  FROM blng__FinancePeriod__c
  WHERE blng__StartDate__c <= :orderEndDate
    AND blng__EndDate__c >= :orderStartDate
    AND blng__Status__c = 'Active'

If this query returns zero rows, create Finance Periods first.
Activating the Order without Finance Periods silently produces no revenue schedule.
```

**Detection hint:** Any revenue recognition workflow that jumps directly to "activate the Order" without a Finance Period verification step is missing a critical prerequisite check.

---

## Anti-Pattern 4: Recommending Direct Edits to blng__RevenueTransaction__c or blng__RevenueSchedule__c

**What the LLM generates:** When a practitioner reports a wrong GL amount or incorrect period on a Revenue Transaction, the LLM suggests: "You can update the blng__Amount__c field on the blng__RevenueTransaction__c record via Data Loader to correct the value" or "Edit the revenue schedule line amounts to fix the proration."

**Why it happens:** For most Salesforce objects, direct field edits are a valid correction mechanism. LLMs apply this pattern broadly without knowing that `blng__RevenueTransaction__c` is a system-managed GL record where direct edits bypass engine consistency checks and corrupt recognized-amount tracking on the parent schedule.

**Correct pattern:**

```
blng__RevenueTransaction__c records are system-managed. Do not edit them directly.

To correct a recognition error:
1. Identify the root cause (wrong rule? wrong Finance Period? wrong SSP?).
2. Close/cancel the affected blng__RevenueSchedule__c.
3. Fix the configuration on Product2 / blng__RevenueRecognitionRule__c.
4. Re-trigger schedule generation through the Salesforce Billing process.
5. For periods already closed in the ERP, record a manual journal entry.

Direct edits to blng__RevenueTransaction__c or blng__RevenueSchedule__c
will corrupt GL integrity and are not supported.
```

**Detection hint:** Any recommendation to use Data Loader, Developer Console, or Apex to directly update `blng__RevenueTransaction__c` fields is an anti-pattern. Flag it immediately.

---

## Anti-Pattern 5: Assuming Equal Distribution Is the Default for Subscription Products

**What the LLM generates:** Configuration instructions that set `blng__DistributionMethod__c = Equal Distribution` for a SaaS annual subscription, or guidance that assumes revenue is split evenly across 12 months without mentioning proration for partial months.

**Why it happens:** Equal distribution is conceptually simple and matches how practitioners often describe revenue spreading ("split the $12,000 equally across 12 months"). LLMs generate this as the natural configuration without modeling the partial-month edge case that occurs whenever a subscription starts or ends mid-month.

**Correct pattern:**

```
For SaaS subscriptions with variable start/end dates:
  blng__DistributionMethod__c = Daily Proration

Daily Proration: Allocates revenue proportionally to the days in each Finance Period
that overlap the service date range. Handles partial months at start and end correctly.

Equal Distribution: Divides the total evenly across all Finance Periods regardless of
period length. Produces incorrect revenue in the first and last period if the
subscription starts or ends mid-month — an ASC 606 compliance issue.

Use Equal Distribution ONLY when: service periods are exactly aligned to Finance Period
boundaries (rare in practice), or Finance explicitly approves it for simplicity.
```

**Detection hint:** Any configuration that recommends `Equal Distribution` for a subscription product without explicitly confirming that the service dates align to Finance Period boundaries should be questioned.

---

## Anti-Pattern 6: Treating blng__RevenueRecognitionRule__c as an Order-Level Setting

**What the LLM generates:** Instructions to set `blng__RevenueRecognitionRule__c` on the Order header record, the OrderProduct `blng__RevenueRecognitionRule__c` (if such a field existed), or the CPQ Quote Line — rather than on the Product2 record itself.

**Why it happens:** Billing Policy and Billing Rule configuration patterns involve multiple objects (Account, Order, OrderProduct, Product2). LLMs sometimes mis-apply the pattern and suggest setting the Revenue Recognition Rule at the Order or OrderProduct level, where it does not drive schedule generation.

**Correct pattern:**

```
blng__RevenueRecognitionRule__c must be set on Product2 — not on the Order, 
not on the OrderProduct, and not on the CPQ Quote Line.

The Billing engine reads the rule from Product2 at Order activation time.
Setting it anywhere else does not trigger revenue schedule creation.

SOQL to verify Product2 configuration:
  SELECT Id, Name, blng__RevenueRecognitionRule__c, blng__RevenueRecognitionRule__r.Name
  FROM Product2
  WHERE Id IN :inScopeProductIds
```

**Detection hint:** Any instruction that sets `blng__RevenueRecognitionRule__c` on a record other than Product2 is incorrect.
