# Examples — Quote-to-Cash Process (CPQ + Revenue Cloud)

## Example 1: Billing Schedules Not Created After Order Activation

**Scenario:** A CPQ org with Revenue Cloud Billing reports that Orders are being created and activated, but `blng__BillingSchedule__c` records are never generated for recurring subscription products.

**Problem:** The team created Orders directly from approved Quotes using a custom Flow, bypassing the Contract step. The Order activated successfully, but without a Contract, `SBQQ__Subscription__c` records were never created. Revenue Cloud Billing requires Subscriptions linked to a Contract to generate billing schedules for recurring products. The orders had `SBQQ__Contracted__c = false` because no Contract record existed to set it.

**Solution:**

Corrected flow sequence — contract the Quote before or alongside Order creation:

```text
1. SBQQ__Quote__c.SBQQ__Status__c = "Approved"
2. Set SBQQ__Quote__c.SBQQ__Contracted__c = true
   → CPQ trigger creates: Contract record + SBQQ__Subscription__c records (one per recurring line)
3. Create Order from Contract (not directly from Quote)
   → OrderItems created from Subscriptions
4. Set Order.Status = "Activated"
   → SBQQ__Contracted__c on Order set to true by CPQ
   → blng__BillingSchedule__c records created per billable OrderItem
5. Run billing job → blng__Invoice__c records generated
```

Diagnostic SOQL to confirm the missing Contract link:

```sql
SELECT Id, SBQQ__Contracted__c, SBQQ__Contract__c
FROM Order
WHERE SBQQ__Contracted__c = false
AND Status = 'Activated'
```

If `SBQQ__Contract__c` is null on activated Orders, the Contract pivot was skipped.

**Why it works:** The `blng__BillingSchedule__c` trigger in Revenue Cloud Billing is linked to the Order activation event only when the Order is associated with a valid Contract and the OrderItem's product has a `blng__BillingRule__c` assigned. Both conditions must be true.

---

## Example 2: Advanced Approvals Chain Returns No Approval Requests at Runtime

**Scenario:** An org has Advanced Approvals installed and configured with an `sbaa__ApprovalChain__c` linked to `SBQQ__Quote__c`. Reps submit quotes for approval but `sbaa__ApprovalRequest__c` records are not created. Quote status stays at "Needs Approval" but no approver receives a notification.

**Problem:** The `sbaa__ApprovalChain__c` was configured with `sbaa__ApprovalConditionsMet__c` set to "All" (all conditions must be met to activate the rule), but one condition referenced a Quote Line field (`SBQQ__QuoteLine__c.SBQQ__Discount__c`) using the wrong field path. The condition object API name was typed as `SBQQ__Quote__c` instead of `SBQQ__QuoteLine__c`, causing the rule to never match and no approver records to be created.

**Solution:**

Verify rule conditions reference the correct object:

```sql
SELECT Id, sbaa__Object__c, sbaa__Field__c, sbaa__Operator__c, sbaa__FilterValue__c
FROM sbaa__ApprovalCondition__c
WHERE sbaa__ApprovalRule__r.sbaa__ApprovalChain__r.Name = 'CPQ Quote Approval'
```

Expected for a line-level discount condition:
- `sbaa__Object__c` = `SBQQ__QuoteLine__c`
- `sbaa__Field__c` = `SBQQ__Discount__c`
- `sbaa__Operator__c` = `greater than`
- `sbaa__FilterValue__c` = `15`

After correcting the object reference, submit a test quote with a line discount above the threshold and confirm:

```sql
SELECT Id, sbaa__Status__c, sbaa__Approver__r.Name, sbaa__TargetId__c
FROM sbaa__ApprovalRequest__c
WHERE sbaa__TargetId__c = '<QuoteId>'
```

**Why it works:** Advanced Approvals evaluates conditions against the specific SObject API name configured on each `sbaa__ApprovalCondition__c`. A mismatch between the object name and the field path silently fails — no error is thrown, no request is created.

---

## Example 3: Amendment Quote Duplicates Billing Schedules

**Scenario:** A customer's subscription was amended mid-term. After the Amendment Quote was approved and contracted, the billing team reports duplicate invoices — both the original billing schedule and a new one are generating invoices for the same period.

**Problem:** The administrator used the standard "New Order" button on the Contract to create a second Order for the amended products, rather than using the Amendment flow which creates an Amendment Quote from the Contract. The CPQ Amendment flow correctly co-terminates the original Subscription and creates a new one at the amended price. Creating a raw new Order bypassed this logic, leaving the original `SBQQ__Subscription__c` active alongside the new one, resulting in two active billing schedules.

**Correct approach:**

```text
1. Navigate to the Contract record
2. Click "Amend" — this launches the CPQ Amendment flow
3. CPQ creates an Amendment SBQQ__Quote__c with SBQQ__Type__c = "Amendment"
4. Modify the line items on the Amendment Quote
5. Approve and contract the Amendment Quote
6. CPQ automatically sets SBQQ__SubscriptionEndDate__c on the original Subscription
   and creates a new Subscription at the amended terms
7. Billing schedules on the original Subscription terminate at the amendment date
8. New billing schedules are created from the new Subscription's Order
```

**Why it works:** The CPQ Amendment flow manages `SBQQ__Subscription__c` co-termination and start-date alignment automatically. Bypassing it by creating a raw Order leaves the original Subscription's end date unchanged.

---

## Anti-Pattern: Querying Standard Quote Object in a CPQ Org

**What practitioners do:** Write SOQL or reports against the standard `Quote` object to retrieve quote records, assuming CPQ quotes are stored there.

```sql
-- WRONG in a CPQ org:
SELECT Id, Name, Status FROM Quote WHERE OwnerId = :currentUserId
```

**What goes wrong:** CPQ quotes are stored on `SBQQ__Quote__c`, not the standard `Quote` object. The query above returns zero records (or only non-CPQ quotes if mixed). Apex, Flow, and report builders all make this mistake. The standard `Quote` object may have zero records in the org even though thousands of CPQ quotes exist.

**Correct approach:**

```sql
-- CORRECT in a CPQ org:
SELECT Id, Name, SBQQ__Status__c, SBQQ__Account__r.Name
FROM SBQQ__Quote__c
WHERE OwnerId = :currentUserId
```

**Detection hint:** Any reference to the object name `Quote` (without the `SBQQ__` prefix) in Apex, Flow, or SOQL in a CPQ org should be flagged for review.
