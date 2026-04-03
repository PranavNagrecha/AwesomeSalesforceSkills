# Examples — Callouts And HTTP Integrations

## Example 1: Named Credential Service Wrapper With Timeout And Status Handling

**Context:** Apex must create a ticket in an external support system using OAuth managed outside code.

**Problem:** Developers want to embed the full URL and bearer token directly in Apex, which becomes unsafe and environment-specific.

**Solution:**

```apex
public with sharing class SupportApiClient {

    public class SupportApiException extends Exception {}

    public static String createTicket(String subject, String description) {
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:Support_API/v1/tickets');
        request.setMethod('POST');
        request.setHeader('Content-Type', 'application/json');
        request.setTimeout(10000);
        request.setBody(JSON.serialize(new Map<String, Object>{
            'subject' => subject,
            'description' => description
        }));

        HttpResponse response = new Http().send(request);
        Integer statusCode = response.getStatusCode();
        if (statusCode < 200 || statusCode >= 300) {
            throw new SupportApiException(
                'Support API returned ' + statusCode + ': ' + response.getBody()
            );
        }

        Map<String, Object> payload =
            (Map<String, Object>) JSON.deserializeUntyped(response.getBody());
        return (String) payload.get('ticketId');
    }
}
```

**Why it works:** The endpoint and credentials live in configuration, the timeout is explicit, and non-success responses are handled deliberately rather than ignored.

---

## Example 2: Queueable For After-Save Callout

**Context:** A trigger on `Invoice__c` must notify an external billing service after records are committed.

**Problem:** Calling the external API directly in the trigger risks transaction failure and poor operational visibility.

**Solution:**

```apex
public class InvoiceSyncQueueable implements Queueable, Database.AllowsCallouts {
    private final Set<Id> invoiceIds;

    public InvoiceSyncQueueable(Set<Id> invoiceIds) {
        this.invoiceIds = invoiceIds;
    }

    public void execute(QueueableContext context) {
        List<Invoice__c> invoices = [
            SELECT Id, Name, Total__c, Sync_Status__c
            FROM Invoice__c
            WHERE Id IN :invoiceIds
        ];

        for (Invoice__c invoiceRecord : invoices) {
            HttpRequest request = new HttpRequest();
            request.setEndpoint('callout:Billing_API/invoices');
            request.setMethod('POST');
            request.setTimeout(15000);
            request.setHeader('Content-Type', 'application/json');
            request.setBody(JSON.serialize(invoiceRecord));

            HttpResponse response = new Http().send(request);
            invoiceRecord.Sync_Status__c =
                response.getStatusCode() == 200 ? 'Sent' : 'Failed';
        }

        update invoices;
    }
}
```

**Why it works:** The trigger transaction only queues the work. The Queueable owns the callout and can be monitored and retried independently.

---

## Anti-Pattern: Hardcoded Endpoint And Trigger Callout

**What practitioners do:** They call the remote system straight from the trigger and bake the URL into code.

```apex
HttpRequest request = new HttpRequest();
request.setEndpoint('https://sandbox-partner.example.com/api/send');
request.setMethod('POST');
HttpResponse response = new Http().send(request);
```

**What goes wrong:** Environment changes require code deployment, credentials drift, and the trigger becomes fragile under network failures or transaction rules.

**Correct approach:** Move the endpoint to a Named Credential and move outbound work to Queueable Apex when the callout should happen after DML.
