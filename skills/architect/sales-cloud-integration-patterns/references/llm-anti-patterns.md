# LLM Anti-Patterns — Sales Cloud Integration Patterns

Common mistakes AI coding assistants make when generating or advising on Sales Cloud integration designs. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Querying Before Upserting Instead of Using External ID

**What the LLM generates:** A SOQL query to find existing records by name or email, followed by conditional insert/update logic.

```apex
// WRONG: Query-then-decide pattern
List<Account> existing = [SELECT Id FROM Account WHERE Name = :erpAccount.name];
if (existing.isEmpty()) {
    insert new Account(Name = erpAccount.name);
} else {
    existing[0].BillingCity = erpAccount.city;
    update existing[0];
}
```

**Why it happens:** LLMs default to general-purpose CRUD patterns from non-Salesforce codebases. The External ID upsert is a Salesforce-specific operation not well represented in general training data.

**Correct pattern:**

```apex
Account a = new Account();
a.ERP_Account_ID__c = erpAccount.erpId;  // External ID field
a.Name = erpAccount.name;
a.BillingCity = erpAccount.city;
Database.upsert(a, Account.ERP_Account_ID__c, false);
```

**Detection hint:** Look for SOQL queries immediately before insert/update blocks on integration-synced objects. If an External ID field exists, the query is unnecessary.

---

## Anti-Pattern 2: Ignoring Lead Conversion in Marketing Sync Design

**What the LLM generates:** A marketing integration that syncs Leads bidirectionally but makes no mention of what happens when a Lead is converted to a Contact.

**Why it happens:** LLMs treat Lead and Contact as independent objects. Training data rarely covers the conversion lifecycle in integration context, so the model skips the transition entirely.

**Correct pattern:**

```
1. Sync Leads inbound using Marketing_Lead_ID__c as External ID
2. Subscribe to Lead.IsConverted change via trigger or CDC
3. On conversion, publish event with ConvertedContactId mapped to Marketing_Lead_ID__c
4. External system updates its reference from Lead to Contact
5. Post-conversion syncs target Contact and CampaignMember objects
```

**Detection hint:** If a marketing integration design mentions Lead sync but never mentions "conversion," "ConvertedContactId," or "IsConverted," the design is incomplete.

---

## Anti-Pattern 3: Sending Quotes Instead of Orders to ERP

**What the LLM generates:** An integration that transmits Quote and QuoteLineItem records directly to ERP for fulfillment, skipping the Order object entirely.

**Why it happens:** LLMs conflate "approved quote" with "order." In many non-Salesforce systems, a quote acceptance creates an order implicitly. In Salesforce, Quote and Order are separate objects with distinct lifecycle states.

**Correct pattern:**

```
1. Quote reaches Approved status
2. Create Order + OrderItems from Quote (standard action or CPQ contracted order)
3. Activate the Order
4. Transmit the Order (not the Quote) to ERP
5. Map Product2.ProductCode or ERP_Product_ID__c to ERP SKU
```

**Detection hint:** Look for `SBQQ__Quote__c` or `Quote` being sent to ERP. The handoff object should be `Order` or `SBQQ__Order__c`.

---

## Anti-Pattern 4: Full-Record Sync on Bidirectional Objects

**What the LLM generates:** Inbound and outbound syncs that transfer all fields on Account or Product, with no field-level mastery control.

```apex
// WRONG: Overwrites ALL fields from ERP
Account a = new Account();
a.ERP_Account_ID__c = payload.erpId;
a.Name = payload.name;
a.OwnerId = payload.ownerId;        // ERP should NOT set this
a.Territory__c = payload.territory;  // ERP should NOT set this
a.BillingCity = payload.city;
Database.upsert(a, Account.ERP_Account_ID__c, false);
```

**Why it happens:** LLMs default to mapping all available fields for "completeness." They do not understand that in bidirectional scenarios, each field has an owner and overwriting the other system's fields causes data loss.

**Correct pattern:**

```apex
// CORRECT: Only set ERP-mastered fields
Account a = new Account();
a.ERP_Account_ID__c = payload.erpId;
a.BillingCity = payload.city;
a.BillingState = payload.state;
a.Payment_Terms__c = payload.paymentTerms;
// OwnerId, Territory__c are SF-mastered — never set from ERP
Database.upsert(a, Account.ERP_Account_ID__c, false);
```

**Detection hint:** In inbound sync code, check if fields like `OwnerId`, `Territory__c`, or custom engagement fields are being set from external data. These are almost always Salesforce-mastered.

---

## Anti-Pattern 5: Synchronous Callout in Trigger Context for Order Integration

**What the LLM generates:** An `after insert` trigger on Order that makes an HTTP callout directly to the ERP system.

```apex
// WRONG: Callout in trigger context
trigger OrderToERP on Order (after insert) {
    for (Order o : Trigger.new) {
        Http h = new Http();
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ERP/orders');
        // This will fail — callouts not allowed in trigger context
    }
}
```

**Why it happens:** LLMs generate trigger-based integration code by combining "trigger fires on insert" with "HTTP callout to external system" without recognizing that Salesforce prohibits callouts in synchronous trigger execution.

**Correct pattern:**

```apex
// CORRECT: Enqueue async callout from trigger
trigger OrderToERP on Order (after insert) {
    List<Id> orderIds = new List<Id>();
    for (Order o : Trigger.new) {
        if (o.Status == 'Activated') {
            orderIds.add(o.Id);
        }
    }
    if (!orderIds.isEmpty()) {
        System.enqueueJob(new ERPOrderCalloutQueueable(orderIds));
    }
}
```

**Detection hint:** Look for `Http`, `HttpRequest`, or `callout:` inside trigger handler methods without a `@future` or `System.enqueueJob` wrapper.

---

## Anti-Pattern 6: Hardcoding Pricebook IDs in Product Sync

**What the LLM generates:** Product integration code that references a hardcoded Pricebook2 ID for the standard pricebook.

```apex
// WRONG: Hardcoded pricebook ID
PricebookEntry pbe = new PricebookEntry(
    Pricebook2Id = '01s000000000001',  // Hardcoded — breaks across orgs
    Product2Id = product.Id,
    UnitPrice = 100
);
```

**Why it happens:** LLMs copy ID patterns from examples without understanding that standard Pricebook IDs differ between orgs and sandboxes.

**Correct pattern:**

```apex
// CORRECT: Query for standard pricebook
Id stdPbId = [SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1].Id;
// Or use Test.getStandardPricebookId() in test context
```

**Detection hint:** Search for 15 or 18-character IDs starting with `01s` in integration code. These are likely hardcoded Pricebook IDs.
