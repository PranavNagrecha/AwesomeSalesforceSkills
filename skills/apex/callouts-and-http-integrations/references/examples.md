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

**Why it works:** The trigger transaction only queues the work. The Queueable owns the callout and can be monitored and retried independently. The `update` is after the callouts, which is the legal direction — "you can make callouts before performing these types of operations" (apexdev L35862–35863).

**What this minimal version still gets wrong** — deliberately, so the gap is visible:

| Gap | Why it matters | Fixed in |
|---|---|---|
| One callout per record with no budget guard | 101 invoices in one enqueue exceeds the 100-callouts-per-transaction limit (apexdev L35844) and the whole job dies | `references/code-examples.md` §2 (`CALLOUT_BUDGET`, `Limits.getCallouts()`) |
| `getStatusCode() == 200` only | 201/202 are marked `Failed`; a 200 with an HTML error body is marked `Sent` | `references/code-examples.md` §1 `classify()` |
| No `Idempotency-Key` | A retry after a 500 can double-post the invoice | `references/code-examples.md` §1 |
| No retryable/non-retryable split | A 401 is retried forever; a 503 is never retried | `references/code-examples.md` §1 |

---

## Example 3: Response Classification Table Before Any Code Is Written

**Context:** A reviewer asks "what does this integration do on a 429?" and nobody can answer from the code.

**Problem:** Retry policy is usually implicit — scattered across `if` branches — so nobody can state it, and the tests only prove the 200 path.

**Solution:** Agree the table first, then make the code and the tests mirror it row for row.

| Status | Meaning for this integration | Retryable | Record state | Test that proves it |
|---|---|---|---|---|
| `200`, `201`, `202` + parseable body | Accepted | no | `Synced`, external id stored | `postInvoices_success_returnsTypedAck` |
| `2xx` + unparseable / missing id | Contract break on their side | **no** | `Failed`, code `BAD_RESPONSE_SHAPE` | `postInvoices_badResponseShape_isNotRetryable` |
| `400`, `422` | Our payload is wrong | no | `Failed`, code `REJECTED` | validation-path test |
| `401`, `403` | Credential/principal misconfigured | **no** — retrying can lock the account | `Failed`, code `AUTH` | `postInvoices_authFailure_isNotRetryable` |
| `408`, `429` | Timed out / throttled | yes, with backoff | `Retrying`, code `THROTTLED` | sequence-mock test |
| `5xx` | Their outage, or a lost reply | yes — **only safe with an idempotency key** | `Retrying`, code `UPSTREAM` | `postInvoices_serverError_isRetryable` |
| status `0` from `HttpClient` | Transport failure; `CalloutException` was caught | yes | `Retrying`, code `TRANSPORT` | `postInvoices_transportFailure_reportsStatusZero` |

The status-0 row is the one AI-generated code omits most often: `templates/apex/HttpClient.cls`
catches the exception and reports `statusCode = 0`, so a `switch` over 2xx/4xx/5xx silently treats a
timeout as a hard failure.

---

## Example 4: Two-Way TLS Without Putting A Certificate In Code

**Context:** The remote system requires client-certificate (mutual TLS) authentication in addition to the bearer token.

**Problem:** Developers try to load a keystore or a PEM into Apex. There is no API for that on the request; the certificate must already exist in the org.

**Solution:** Generate or upload the certificate in Certificate and Key Management, then reference it by its Unique Name.

```apex
// "In your Apex, use the setClientCertificateName method of the HttpRequest class. The value
//  used for the argument for this method must match the Unique Name of the certificate that you
//  generated in the previous step." (apexdev L35832-35833)
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Partner_MTLS_API/v1/orders');
req.setMethod('POST');
req.setClientCertificateName('PartnerMtlsCert');   // Unique Name, not a file, not a blob
req.setTimeout(20000);
req.setHeader('Content-Type', 'application/json');
req.setBody(JSON.serialize(payload));
HttpResponse res = new Http().send(req);
```

**Why it works:** the private key never enters Apex or source control. The preferred form is one
level further out still — a Named Credential parameter of `parameterType` `ClientCertificate`
referencing the same certificate (api_meta L90321–90322), which removes the certificate name from
the code as well. See integration/mutual-tls-callouts for the full setup, and note that
`HttpRequest.setClientCertificate(clientCert, password)` is explicitly deprecated — "This method is
deprecated. Use setClientCertificateName instead." (apexrefguide L216559–216560).

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
