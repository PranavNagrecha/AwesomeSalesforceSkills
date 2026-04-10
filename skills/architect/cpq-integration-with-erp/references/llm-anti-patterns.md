# LLM Anti-Patterns — CPQ Integration with ERP

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ to ERP integration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Triggering ERP on Quote Close Instead of Order Activation

**What the LLM generates:** Code or Flow logic that fires the ERP callout when `SBQQ__Quote__c.SBQQ__Status__c` changes to `Approved`, or when `Opportunity.StageName` changes to `Closed Won`.

**Why it happens:** Standard Salesforce-to-ERP integration training data frequently uses Opportunity or Quote as the trigger — CPQ's asynchronous Order generation step is underrepresented in training corpora. The LLM generalizes from standard Quote patterns where Quote and QuoteLineItem are populated at quote creation time.

**Correct pattern:**

```
Trigger: Record-Triggered Flow on Order object
Entry condition: Order.Status EQUALS [configured activated value, e.g., "Activated"]
Action: Publish platform event Order_Activated__e with Order Id and amendment flag
```

**Detection hint:** Search generated output for `SBQQ__Status__c`, `Closed Won`, or `StageName` as a trigger condition for ERP callout. If found, flag for review — the trigger should be on `Order.Status`.

---

## Anti-Pattern 2: Querying QuoteLineItem for CPQ Quote Line Data

**What the LLM generates:** SOQL queries such as `SELECT Id, Quantity, UnitPrice FROM QuoteLineItem WHERE QuoteId = :quoteId` to retrieve line items from a CPQ quote.

**Why it happens:** `QuoteLineItem` is the standard Salesforce object for standard Quotes. LLMs trained on Salesforce documentation and StackExchange answers frequently cite `QuoteLineItem` as the object for quote line data without distinguishing standard Quotes from CPQ Quotes. CPQ's custom `SBQQ__QuoteLine__c` object is less commonly represented in training data.

**Correct pattern:**

```soql
-- For CPQ quote-time line data:
SELECT Id, SBQQ__Product__c, SBQQ__Quantity__c, SBQQ__NetPrice__c,
       SBQQ__SubscriptionType__c
FROM SBQQ__QuoteLine__c
WHERE SBQQ__Quote__c = :quoteId

-- For order-time line data (after Order is generated from CPQ quote):
SELECT Id, Product2Id, Product2.ProductCode, Quantity, UnitPrice, TotalPrice
FROM OrderItem
WHERE OrderId = :orderId
```

**Detection hint:** Any SOQL query against `QuoteLineItem` in a CPQ integration context should be flagged. CPQ does not populate this object.

---

## Anti-Pattern 3: Placing HTTP Callouts Inside QCP Methods

**What the LLM generates:** An implementation of the Quote Calculator Plugin's `calculate()` or `validate()` method that includes an `Http.send()` call to an ERP inventory or pricing API.

**Why it happens:** The QCP is the natural place to add pricing logic, so LLMs route inventory and pricing API calls there. The platform restriction on callouts from the QCP execution context is a non-obvious runtime constraint that does not appear in QCP interface signatures or most introductory CPQ API documentation.

**Correct pattern:**

```apex
// WRONG — do not put callouts in QCP methods
global void calculate(QuoteModel quote, QuoteLineModel line) {
    Http h = new Http(); // throws CalloutException at runtime
    HttpRequest req = new HttpRequest();
    // ...
}

// CORRECT — use an invocable Apex action called from LWC or Flow
@InvocableMethod(label='Check ERP Inventory')
public static List<InventoryResult> checkInventory(List<Id> quoteLineIds) {
    // HTTP callout is permitted here — outside QCP context
    Http h = new Http();
    HttpRequest req = new HttpRequest();
    // ...
}
```

**Detection hint:** Any `Http`, `HttpRequest`, or `WebServiceCallout` reference inside a class that implements `SBQQ.QuoteCalculatorPlugin` or extends `SBQQ.QuoteCalculatorPlugin2` should be flagged as a runtime error waiting to happen.

---

## Anti-Pattern 4: Treating CPQ Amendment Orders as Net-New ERP Sales Orders

**What the LLM generates:** Integration code that creates a new ERP Sales Order for every activated Salesforce Order, without checking whether the Order is an amendment or a new-business order.

**Why it happens:** The distinction between new-business and amendment Orders in CPQ is CPQ-specific domain knowledge. LLMs unfamiliar with CPQ's subscription amendment workflow assume every Order represents a new sale and generate a straightforward `POST /SalesOrder` call for all cases.

**Correct pattern:**

```apex
// Check for amendment before routing to ERP
String erpTransactionType = 'NEW_ORDER';

Order ord = [
    SELECT SBQQ__Quote__r.SBQQ__AmendedContract__c
    FROM Order WHERE Id = :orderId LIMIT 1
];

if (ord.SBQQ__Quote__r.SBQQ__AmendedContract__c != null) {
    erpTransactionType = 'AMENDMENT'; // route to delta-update API
}
```

**Detection hint:** If the generated integration code has no conditional branch for amendment detection before creating the ERP Sales Order, it is handling only the new-business case. Look for absence of `SBQQ__AmendedContract__c` or `SBQQ__Contracted__c` checks.

---

## Anti-Pattern 5: Storing ERP Credentials in Apex or Custom Metadata Unencrypted

**What the LLM generates:** Apex code that reads an ERP API key from a `Custom_Setting__c` field, a hardcoded string, or a Custom Metadata Type `Text` field, then passes it as a plain Authorization header in the HTTP request.

**Why it happens:** LLMs frequently generate the simplest possible credential access pattern — reading from a custom setting or hardcoded — without applying Salesforce security best practices for credential storage.

**Correct pattern:**

```apex
// WRONG — reading credentials from custom settings or hardcoded values
String apiKey = ERP_Settings__c.getInstance().API_Key__c;
req.setHeader('Authorization', 'Bearer ' + apiKey);

// CORRECT — use Named Credentials
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:ERP_SAP_Named_Credential/api/v1/orders');
req.setMethod('POST');
// Named Credential handles authentication automatically
// No credential in Apex code
```

**Detection hint:** Any `Authorization` header being set with a value read from a custom setting, custom metadata text field, or a string literal should be flagged. ERP credentials must use Named Credentials (`callout:NamedCredentialName`), which store credentials encrypted and apply them at callout time without exposing them in Apex code.

---

## Anti-Pattern 6: Missing ERP Writeback of Order Confirmation

**What the LLM generates:** Integration code that sends the CPQ Order to ERP and completes without writing the ERP order number or confirmation status back to the Salesforce Order record.

**Why it happens:** LLMs generate the happy path — data goes out to ERP — without modeling the return leg of the integration. Without writeback, there is no way to trace a Salesforce Order to its ERP counterpart, and reprocessing on failure creates duplicate ERP orders.

**Correct pattern:**

```apex
// After ERP confirms order creation, write back the ERP document number
Order orderToUpdate = new Order(
    Id = salesforceOrderId,
    ERP_Order_Number__c = erpResponse.documentNumber,
    ERP_Sync_Status__c = 'Confirmed',
    ERP_Last_Sync__c = Datetime.now()
);
update orderToUpdate;
```

**Detection hint:** If the generated integration has no update or upsert back to the Salesforce `Order` object after the ERP callout succeeds, the writeback is missing. This is required for deduplication, support tracing, and reconciliation.
