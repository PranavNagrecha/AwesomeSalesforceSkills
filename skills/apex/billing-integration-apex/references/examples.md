# Examples — Billing Integration Apex

## Example 1: Charging a Payment via blng.TransactionAPI in a Queueable

**Context:** A subscription renewal trigger on `blng__BillingSchedule__c` needs to charge the default payment method when a schedule becomes due. The trigger performs a DML update on the schedule record before initiating the charge, which means the charge callout cannot happen in the same transaction.

**Problem:** Calling `blng.TransactionAPI.charge()` synchronously in the same trigger execution that already updated the billing schedule record throws `System.CalloutException: You have uncommitted work pending`. The transaction has uncommitted DML and Salesforce does not allow callouts after DML in the same transaction.

**Solution:**

```apex
// Queueable class — handles the payment charge asynchronously
public class BillingChargeQueueable implements Queueable, Database.AllowsCallouts {

    private Id paymentId;
    private Decimal amount;

    public BillingChargeQueueable(Id paymentId, Decimal amount) {
        this.paymentId = paymentId;
        this.amount = amount;
    }

    public void execute(QueueableContext ctx) {
        // No DML before this point — safe to call out
        blng.TransactionAPI.ChargeRequest req = new blng.TransactionAPI.ChargeRequest();
        req.paymentId = this.paymentId;
        req.amount = this.amount;

        blng.TransactionAPI.ChargeResult result = blng.TransactionAPI.charge(req);

        // Persist the result — DML is now after the callout, which is allowed
        blng__Payment__c payment = new blng__Payment__c(
            Id = this.paymentId,
            blng__GatewayReferenceNumber__c = result.gatewayReferenceId,
            blng__Status__c = result.success ? 'Processed' : 'Failed',
            blng__GatewayErrorMessage__c = result.errorMessage
        );
        update payment;
    }
}

// Trigger handler — enqueues instead of calling TransactionAPI directly
public class BillingScheduleTriggerHandler {
    public static void onAfterUpdate(List<blng__BillingSchedule__c> newList,
                                     Map<Id, blng__BillingSchedule__c> oldMap) {
        List<BillingChargeQueueable> jobs = new List<BillingChargeQueueable>();
        for (blng__BillingSchedule__c schedule : newList) {
            if (schedule.blng__Status__c == 'Active' &&
                oldMap.get(schedule.Id).blng__Status__c != 'Active') {
                // Enqueue the charge — do NOT call TransactionAPI here
                System.enqueueJob(
                    new BillingChargeQueueable(schedule.blng__DefaultPaymentMethod__c,
                                               schedule.blng__TotalAmount__c)
                );
            }
        }
    }
}
```

**Why it works:** The Queueable runs in a separate transaction with no preceding DML, satisfying the platform's callout constraint. `Database.AllowsCallouts` on the class interface explicitly declares that this Queueable makes callouts, which is required for the platform to allow them. DML to persist the gateway result comes after the callout inside `execute()`, which is the correct ordering.

---

## Example 2: Programmatic Invoice Generation via Connect REST API

**Context:** A professional services org needs to generate invoices immediately for a specific set of billing schedules at project milestone completion, rather than waiting for the nightly Invoice Run batch.

**Problem:** The standard `blng.InvoiceRunAPI` processes all eligible schedules in the org and cannot be scoped to a specific subset without complex batch filtering. The Connect REST API provides targeted invoice generation but requires careful handling of the 200-schedule limit and async callout constraints.

**Solution:**

```apex
public class BillingInvoiceGenerationService implements Queueable, Database.AllowsCallouts {

    private List<Id> scheduleIds;
    private static final Integer MAX_BATCH_SIZE = 200;
    private static final String ENDPOINT =
        '/services/data/v63.0/commerce/invoices';

    public BillingInvoiceGenerationService(List<Id> scheduleIds) {
        // Enforce the 200-schedule limit per call
        if (scheduleIds.size() > MAX_BATCH_SIZE) {
            throw new IllegalArgumentException(
                'Cannot process more than ' + MAX_BATCH_SIZE +
                ' billing schedules per invocation. Chunk the input before calling.'
            );
        }
        this.scheduleIds = scheduleIds;
    }

    public void execute(QueueableContext ctx) {
        // Build the JSON request body
        Map<String, Object> body = new Map<String, Object>{
            'billingScheduleIds' => this.scheduleIds
        };
        String requestBody = JSON.serialize(body);

        // Issue the Connect REST API callout
        HttpRequest req = new HttpRequest();
        req.setEndpoint(URL.getOrgDomainUrl().toExternalForm() + ENDPOINT);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());
        req.setBody(requestBody);

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() != 200 && res.getStatusCode() != 201) {
            // Log the failure — do not rethrow to avoid job failure
            // swallowing all partial results
            System.debug(LoggingLevel.ERROR,
                'Invoice generation failed. Status: ' + res.getStatusCode() +
                ' Body: ' + res.getBody());
            insert new blng__InvoiceGenerationLog__c(
                blng__Status__c = 'Failed',
                blng__ErrorMessage__c = res.getBody().left(255)
            );
            return;
        }

        // Parse successful response — contains generated invoice IDs
        Map<String, Object> responseBody =
            (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        System.debug('Generated invoices: ' + responseBody.get('invoiceIds'));
    }

    // Static helper to chunk a large list and enqueue one job per chunk
    public static void enqueueInChunks(List<Id> allScheduleIds) {
        Integer batchSize = MAX_BATCH_SIZE;
        for (Integer i = 0; i < allScheduleIds.size(); i += batchSize) {
            Integer endIdx = Math.min(i + batchSize, allScheduleIds.size());
            List<Id> chunk = new List<Id>(allScheduleIds.subList(i, endIdx));
            System.enqueueJob(new BillingInvoiceGenerationService(chunk));
        }
    }
}
```

**Why it works:** The service enforces the 200-schedule limit at construction time, preventing silent truncation. Running in a Queueable with `Database.AllowsCallouts` ensures no DML constraint conflicts. The `enqueueInChunks` static method handles arbitrarily large sets by spawning one Queueable per 200-schedule chunk. The endpoint uses the org's domain URL combined with the versioned path, ensuring the correct API version (v63.0+) is always used.

---

## Example 3: Custom Payment Gateway Adapter

**Context:** An org uses a regional payment processor not supported natively by Salesforce Billing. The development team needs to integrate it so that the standard Billing payment lifecycle (authorize, capture, void, refund) flows through the custom processor.

**Problem:** Writing callouts directly on `blng__Payment__c` triggers bypasses the Billing package's transaction lifecycle management and breaks the reconciliation reports that rely on `blng__PaymentGatewayLog__c` records being created by the managed package.

**Solution:**

```apex
// Custom gateway adapter — registered on blng__PaymentGateway__c
global class AcmePaymentGatewayAdapter implements blng.PaymentGateway {

    // Authorize — reserve funds without capturing
    global blng.GatewayResponse authorize(blng.GatewayRequest request) {
        AcmeApiResponse apiResponse = callAcmeApi(
            '/authorize',
            new Map<String, Object>{
                'amount'   => request.amount,
                'currency' => request.currencyCode,
                'token'    => request.paymentMethodToken
            }
        );
        blng.GatewayResponse response = new blng.GatewayResponse();
        response.gatewayReferenceNumber = apiResponse.transactionId;
        response.success = apiResponse.status == 'authorized';
        response.errorMessage = apiResponse.errorMessage;
        return response;
    }

    // Capture — finalize a prior authorization
    global blng.GatewayResponse capture(blng.GatewayRequest request) {
        AcmeApiResponse apiResponse = callAcmeApi(
            '/capture',
            new Map<String, Object>{
                'transactionId' => request.gatewayReferenceNumber,
                'amount'        => request.amount
            }
        );
        blng.GatewayResponse response = new blng.GatewayResponse();
        response.gatewayReferenceNumber = apiResponse.transactionId;
        response.success = apiResponse.status == 'captured';
        response.errorMessage = apiResponse.errorMessage;
        return response;
    }

    // Void — cancel an authorization or captured transaction
    global blng.GatewayResponse voidTransaction(blng.GatewayRequest request) {
        AcmeApiResponse apiResponse = callAcmeApi(
            '/void',
            new Map<String, Object>{
                'transactionId' => request.gatewayReferenceNumber
            }
        );
        blng.GatewayResponse response = new blng.GatewayResponse();
        response.success = apiResponse.status == 'voided';
        response.errorMessage = apiResponse.errorMessage;
        return response;
    }

    // Refund — return funds for a completed transaction
    global blng.GatewayResponse refund(blng.GatewayRequest request) {
        AcmeApiResponse apiResponse = callAcmeApi(
            '/refund',
            new Map<String, Object>{
                'transactionId' => request.gatewayReferenceNumber,
                'amount'        => request.amount
            }
        );
        blng.GatewayResponse response = new blng.GatewayResponse();
        response.success = apiResponse.status == 'refunded';
        response.errorMessage = apiResponse.errorMessage;
        return response;
    }

    // Private helper — issues the actual HTTP callout to the Acme gateway
    private AcmeApiResponse callAcmeApi(String path,
                                         Map<String, Object> payload) {
        HttpRequest req = new HttpRequest();
        // Named credential handles endpoint and authentication
        req.setEndpoint('callout:Acme_Payment_Gateway' + path);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(payload));

        Http http = new Http();
        HttpResponse res = http.send(req);
        return (AcmeApiResponse) JSON.deserialize(
            res.getBody(), AcmeApiResponse.class
        );
    }

    // Inner class for deserialising Acme gateway responses
    private class AcmeApiResponse {
        public String transactionId;
        public String status;
        public String errorMessage;
    }
}
```

**Why it works:** The adapter class implements the `blng.PaymentGateway` interface, which the Billing managed package calls during standard `blng.TransactionAPI` lifecycle operations. By routing through the adapter, all `blng__PaymentGatewayLog__c` records are created correctly by the managed package, preserving reconciliation integrity. Named credentials handle the endpoint and auth, keeping secrets out of code.

---

## Anti-Pattern: Calling TransactionAPI Synchronously After DML

**What practitioners do:** Write a trigger on `blng__Invoice__c` that inserts a `blng__Payment__c` record and then immediately calls `blng.TransactionAPI.charge()` in the same `after insert` context.

**What goes wrong:** The insert of `blng__Payment__c` is uncommitted DML at the point `TransactionAPI.charge()` attempts its HTTP callout. Salesforce throws `System.CalloutException: You have uncommitted work pending. Please commit or rollback before calling out`. The transaction rolls back entirely, no payment is attempted, and the user sees an unhandled exception.

**Correct approach:** In the trigger, only collect the payment record IDs. After the trigger's DML commits (i.e., the trigger exits), enqueue a Queueable that calls `TransactionAPI.charge()` in a clean transaction with no prior DML.
