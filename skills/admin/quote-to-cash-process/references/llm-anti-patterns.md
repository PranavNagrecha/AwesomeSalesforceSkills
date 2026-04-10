# LLM Anti-Patterns — Quote-to-Cash Process (CPQ + Revenue Cloud)

Common mistakes AI coding assistants make when generating or advising on CPQ and Revenue Cloud quote-to-cash processes. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Standard Quote and QuoteLineItem Objects in a CPQ Org

**What the LLM generates:**

```apex
List<Quote> quotes = [SELECT Id, Name, Status FROM Quote WHERE OwnerId = :UserInfo.getUserId()];
List<QuoteLineItem> lines = [SELECT Id, Quantity, UnitPrice FROM QuoteLineItem WHERE QuoteId IN :quoteIds];
```

**Why it happens:** LLMs are trained heavily on standard Salesforce documentation and examples that reference the standard `Quote` and `QuoteLineItem` objects. CPQ's custom objects (`SBQQ__Quote__c`, `SBQQ__QuoteLine__c`) are less represented in training data. The LLM defaults to the standard object names because they appear natural and correct in a Salesforce context.

**Correct pattern:**

```apex
List<SBQQ__Quote__c> quotes = [
    SELECT Id, Name, SBQQ__Status__c, SBQQ__Account__r.Name
    FROM SBQQ__Quote__c
    WHERE OwnerId = :UserInfo.getUserId()
];
List<SBQQ__QuoteLine__c> lines = [
    SELECT Id, SBQQ__Quantity__c, SBQQ__NetPrice__c
    FROM SBQQ__QuoteLine__c
    WHERE SBQQ__Quote__c IN :quoteIds
];
```

**Detection hint:** Any Apex, SOQL, or Flow referencing `FROM Quote` or `FROM QuoteLineItem` in a CPQ org should be flagged for review.

---

## Anti-Pattern 2: Skipping the Contract Pivot and Routing Quote Directly to Order

**What the LLM generates:**

```text
Recommended workflow:
1. Quote is approved
2. Create an Order from the approved Quote
3. Activate the Order
4. Billing schedules are generated
```

**Why it happens:** The LLM pattern-matches to the simpler standard Sales Cloud Q2C flow (Quote → Order) and misses the CPQ-specific Contract requirement. The Contract pivot is unique to CPQ's subscription management and is not present in standard Sales Cloud flows. The LLM conflates the two.

**Correct pattern:**

```text
Correct CPQ workflow:
1. SBQQ__Quote__c approved (SBQQ__Status__c = "Approved")
2. Contract the Quote (set SBQQ__Contracted__c = true on the Quote)
   → CPQ creates Contract + SBQQ__Subscription__c records
3. Create Order from Contract
4. Activate Order (Status = "Activated")
   → blng__BillingSchedule__c records created per billable OrderItem
5. Billing run generates blng__Invoice__c records
```

**Detection hint:** Any Q2C workflow that goes directly from Quote to Order without a Contract step should be flagged in a CPQ context.

---

## Anti-Pattern 3: Conflating Standard Salesforce Approval Processes With Advanced Approvals

**What the LLM generates:**

```text
To set up multi-tier CPQ quote approvals:
1. Go to Setup > Approval Processes
2. Create a new Approval Process on SBQQ__Quote__c
3. Add Step 1 for manager approval (discount > 15%)
4. Add Step 2 for director approval (discount > 30%)
```

```apex
// To check if a CPQ quote is pending approval:
List<ProcessInstance> pending = [
    SELECT Id FROM ProcessInstance
    WHERE TargetObjectId = :quoteId AND Status = 'Pending'
];
```

**Why it happens:** Standard Salesforce Approval Processes are the dominant approval concept in LLM training data. Advanced Approvals (sbaa__) is a separate managed package with its own object model, and is far less represented. The LLM defaults to what it knows — standard approvals — and misses the architectural distinction.

**Correct pattern:**

```text
Advanced Approvals uses sbaa__ objects, not Setup > Approval Processes:
- sbaa__ApprovalChain__c — defines the chain linked to SBQQ__Quote__c
- sbaa__ApprovalRule__c — adds approvers when conditions are met
- sbaa__ApprovalCondition__c — field-level conditions (can reference QuoteLine fields)
- sbaa__ApprovalRequest__c — runtime record (check sbaa__Status__c, not ProcessInstance)
```

```apex
// Correct: query sbaa__ApprovalRequest__c for Advanced Approvals status
List<sbaa__ApprovalRequest__c> requests = [
    SELECT Id, sbaa__Status__c, sbaa__Approver__r.Name
    FROM sbaa__ApprovalRequest__c
    WHERE sbaa__TargetId__c = :quoteId
];
```

**Detection hint:** Any reference to `ProcessInstance`, `ProcessInstanceWorkitem`, or `Setup > Approval Processes` in the context of CPQ quote approvals should be verified — it may be conflating standard and Advanced Approvals.

---

## Anti-Pattern 4: Assuming Order Creation Triggers Billing Schedule Generation

**What the LLM generates:**

```text
When an Order is created in Revenue Cloud, the system automatically generates
billing schedules for recurring products based on the product's billing rule.
```

**Why it happens:** The LLM infers a causal relationship between Order creation and billing from general descriptions of Revenue Cloud Billing's capabilities. It misses the specific platform behavior that billing schedules are triggered by Order **activation**, not creation, and that `SBQQ__Contracted__c = true` on the Order is also required.

**Correct pattern:**

```text
Billing schedule generation requires ALL of the following to be true simultaneously:
1. Order.Status = 'Activated'
2. Order.SBQQ__Contracted__c = true
3. OrderItem's product has a blng__BillingRule__c assigned
4. A billing run has executed (scheduled or on-demand)

Creating an Order in Draft status generates no billing schedules.
```

**Detection hint:** Any claim that Order creation generates billing schedules should be corrected to Order activation. Look for statements like "when an Order is created, billing..." as a signal of this anti-pattern.

---

## Anti-Pattern 5: Generating sbaa__ Object Records Using Hardcoded User IDs

**What the LLM generates:**

```apex
sbaa__Approver__c approver = new sbaa__Approver__c(
    Name = 'Sales Manager',
    sbaa__User__c = '0050Y000003Abcd'  // hardcoded User ID
);
insert approver;
```

**Why it happens:** The LLM generates concrete, runnable code and defaults to a hardcoded User ID as the simplest example of an approver reference. It does not consider the operational fragility of hardcoding user IDs in a production approval configuration.

**Correct pattern:**

```apex
// Use a dynamic approver source — field-based user reference or queue
sbaa__Approver__c approver = new sbaa__Approver__c(
    Name = 'Sales Manager (Dynamic)',
    sbaa__UserField__c = 'Owner.Manager',  // resolves at runtime from Quote owner's manager
    sbaa__ObjectType__c = 'SBQQ__Quote__c'
);
insert approver;

// OR use a Queue for team-based approval routing:
Group approvalQueue = [SELECT Id FROM Group WHERE Type = 'Queue' AND Name = 'Sales Approval Queue' LIMIT 1];
sbaa__Approver__c queueApprover = new sbaa__Approver__c(
    Name = 'Sales Approval Queue',
    sbaa__Group__c = approvalQueue.Id
);
insert queueApprover;
```

**Detection hint:** Any `sbaa__Approver__c` with a literal 15- or 18-character Salesforce ID in `sbaa__User__c` is a hardcoded reference that will break when the user is deactivated or changes role.

---

## Anti-Pattern 6: Recommending Process Builder for CPQ Automation

**What the LLM generates:**

```text
To automate contract creation when a CPQ quote is approved:
1. Go to Setup > Process Builder
2. Create a new Process on SBQQ__Quote__c
3. Add criteria: SBQQ__Status__c = "Approved"
4. Add action: Update Record — set SBQQ__Contracted__c = true
```

**Why it happens:** Process Builder appears frequently in older Salesforce training material and LLM training data. It is a legacy tool that Salesforce has deprecated in favor of Flow. More importantly, Process Builder interactions with CPQ package triggers are known to cause race conditions because Process Builder fires asynchronously in some contexts, which can conflict with CPQ's synchronous trigger logic.

**Correct pattern:**

```text
Use Record-Triggered Flow on SBQQ__Quote__c:
- Trigger: After Update
- Entry criteria: SBQQ__Status__c changed to "Approved" AND SBQQ__Contracted__c = false
- Re-entry: Once per record version (prevents recursion)
- Action: Update SBQQ__Quote__c.SBQQ__Contracted__c = true
  (CPQ trigger fires synchronously and creates Contract + Subscriptions)
```

**Detection hint:** Any recommendation to use Process Builder on `SBQQ__Quote__c` or other CPQ managed objects should be replaced with Record-Triggered Flow.
