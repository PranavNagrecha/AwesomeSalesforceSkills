# LLM Anti-Patterns — Billing Integration Apex

Common mistakes AI coding assistants make when generating or advising on Billing Integration Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Calling blng.TransactionAPI Synchronously After DML

**What the LLM generates:** A trigger or controller method that inserts or updates a `blng__Payment__c` record and then immediately calls `blng.TransactionAPI.charge(req)` in the same execution context, without async offloading.

**Why it happens:** LLMs model "insert record, then call API" as a natural sequential pattern and do not always associate `blng.TransactionAPI` with the Salesforce callout-after-DML prohibition. Training data may include simplified examples that omit the async requirement.

**Correct pattern:**

```apex
// WRONG — DML before callout in same transaction
blng__Payment__c pmt = new blng__Payment__c(...);
insert pmt;  // uncommitted DML
blng.TransactionAPI.charge(req);  // THROWS CalloutException

// CORRECT — enqueue and let synchronous transaction commit
blng__Payment__c pmt = new blng__Payment__c(...);
insert pmt;
System.enqueueJob(new BillingChargeQueueable(pmt.Id, amount));
```

**Detection hint:** Look for `blng.TransactionAPI` method calls in the same method body as any DML statement (`insert`, `update`, `delete`, `upsert`) or Database DML methods without an intervening `@future` or `System.enqueueJob` boundary.

---

## Anti-Pattern 2: Missing blng__ Namespace on Managed Package sObject References

**What the LLM generates:** SOQL queries or DML targeting `Invoice__c`, `BillingSchedule__c`, `Payment__c`, or other Billing objects without the `blng__` prefix.

**Why it happens:** LLMs may strip namespace prefixes when generalizing from documentation examples, or may hallucinate sObject names based on the plain English concept (e.g., "Invoice object" becomes `Invoice__c`). The `blng__` double-underscore convention is less common in training data than standard custom object patterns.

**Correct pattern:**

```soql
-- WRONG
SELECT Id, Status__c FROM Invoice__c WHERE AccountId = :accountId

-- CORRECT
SELECT Id, blng__Status__c FROM blng__Invoice__c WHERE blng__Account__c = :accountId
```

**Detection hint:** Any reference to `Invoice__c`, `BillingSchedule__c`, `Payment__c`, `CreditNote__c`, or similar billing domain objects without the `blng__` prefix is incorrect. Also check field API names — `blng__InvoiceStatus__c`, not `InvoiceStatus__c`.

---

## Anti-Pattern 3: Using the Wrong API Version for the Connect REST commerce/invoices Endpoint

**What the LLM generates:** A Connect REST API callout to `/services/data/v55.0/commerce/invoices` or another sub-63.0 API version, or a generic `/services/data/latest/commerce/invoices` URL format.

**Why it happens:** LLMs may default to commonly seen API versions (v50–v58) in training data, or may not know that the `commerce/invoices` endpoint was introduced in v63.0 (Spring '25). The "latest" shortcut does not exist in Salesforce REST API URLs.

**Correct pattern:**

```apex
// WRONG — endpoint with outdated API version
req.setEndpoint(baseUrl + '/services/data/v55.0/commerce/invoices');

// CORRECT — minimum required version is 63.0
private static final String API_VERSION = 'v63.0';
req.setEndpoint(baseUrl + '/services/data/' + API_VERSION + '/commerce/invoices');
```

**Detection hint:** Look for `/services/data/v` followed by a version number less than `63.0` when the endpoint path contains `commerce/invoices`.

---

## Anti-Pattern 4: Conflating blng.InvoiceAPI with Admin Billing Setup Concepts

**What the LLM generates:** Advice to "configure InvoiceAPI settings in Setup" or to use `blng.InvoiceAPI` to set up billing rules, billing treatments, or invoice run schedules. Alternatively, generating code that uses `blng.InvoiceAPI` for payment processing or transaction authorization.

**Why it happens:** LLMs conflate the Apex API class (`blng.InvoiceAPI`, which is for credit operations like credit notes) with the broader concept of "invoice administration" or with the other Billing API surfaces. The name "InvoiceAPI" sounds general but it covers a narrow set of credit-side operations.

**Correct pattern:**

```
blng.InvoiceAPI  → credit note issuance and credit operations on existing invoices
                   (synchronous, no callout, can run alongside DML)

blng.TransactionAPI → payment gateway lifecycle (authorize, capture, charge, void, refund)
                       (requires async context, makes HTTP callouts)

Connect REST API POST /commerce/invoices → programmatic invoice generation
                       (requires async context, requires API v63.0+)

Admin Setup (billing rules, billing treatments, invoice run schedules) → NOT Apex API
```

**Detection hint:** Any suggestion to call `blng.InvoiceAPI` for payment processing, or to use `blng.TransactionAPI` for credit notes, indicates API surface confusion. Also flag any claim that InvoiceAPI configuration is done in Setup.

---

## Anti-Pattern 5: Passing More Than 200 Billing Schedule IDs to the Connect REST API Without Chunking

**What the LLM generates:** Code that queries all `blng__BillingSchedule__c` records for an account (or org-wide) and passes the full result list directly to the `billingScheduleIds` field of the Connect REST API request body, with no limit or chunking logic.

**Why it happens:** LLMs often generate the "happy path" without enforcing documented API limits. The 200-schedule limit is a runtime constraint, not a compile-time error, so there is no static signal for the LLM to surface it. General-purpose Apex list handling patterns do not include domain-specific API limits.

**Correct pattern:**

```apex
// WRONG — no limit check
Map<String, Object> body = new Map<String, Object>{
    'billingScheduleIds' => scheduleIds  // could be 500+ IDs
};

// CORRECT — enforce limit before constructing request
private static final Integer MAX_IDS = 200;
if (scheduleIds.size() > MAX_IDS) {
    throw new IllegalArgumentException(
        'billingScheduleIds cannot exceed ' + MAX_IDS + ' per request'
    );
}
Map<String, Object> body = new Map<String, Object>{
    'billingScheduleIds' => scheduleIds
};
```

**Detection hint:** Any code that constructs the Connect REST API invoice generation request body from a variable-length list of IDs without an explicit size assertion or chunking loop should be flagged.

---

## Anti-Pattern 6: Implementing Custom Gateway Logic in a Trigger Instead of the PaymentGateway Interface

**What the LLM generates:** A trigger on `blng__Payment__c` that fires on insert/update and directly calls a custom HTTP endpoint, bypassing the `blng.PaymentGateway` adapter interface entirely.

**Why it happens:** Trigger-based callout patterns are familiar from non-Billing integrations. LLMs may not associate the `blng.PaymentGateway` interface as the correct extension point for custom gateway integration with the Billing managed package.

**Correct pattern:**

```apex
// WRONG — direct callout from trigger, bypasses Billing lifecycle
trigger PaymentTrigger on blng__Payment__c (after insert) {
    for (blng__Payment__c pmt : Trigger.new) {
        // Direct HTTP callout — skips blng__PaymentGatewayLog__c creation,
        // status management, and reconciliation
        Http http = new Http();
        // ...
    }
}

// CORRECT — implement blng.PaymentGateway interface
global class MyGatewayAdapter implements blng.PaymentGateway {
    global blng.GatewayResponse authorize(blng.GatewayRequest req) { ... }
    global blng.GatewayResponse capture(blng.GatewayRequest req) { ... }
    // ... all required interface methods
}
// Register class name on blng__PaymentGateway__c.blng__GatewayType__c
```

**Detection hint:** Any `HttpRequest` or `Http.send()` call inside a trigger on `blng__Payment__c` or any Billing sObject, where the purpose is payment gateway communication, should be redirected to the adapter interface pattern.
