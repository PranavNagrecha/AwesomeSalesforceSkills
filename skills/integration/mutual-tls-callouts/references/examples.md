# Examples — Mutual TLS Callouts

## Example 1: Bank ACH partner adds an mTLS mandate

**Context:** an existing nightly batch posts payment instructions to a bank. The bank
announces that from a fixed date it will require client-certificate authentication.

**Problem:** the current Apex sets an API key header. There is no Apex API for attaching a
client certificate to an `HttpRequest`, so the change is entirely in Setup — but only if
the certificate is created the right way round.

**Setup sequence (the order matters):**

1. Setup → **Certificate and Key Management** → **Create CA-Signed Certificate**. Name it
   for the partner and environment, e.g. `BankACH_Prod`. Salesforce generates the key pair
   internally; the private key is not exportable.
2. On the saved certificate record, **Download Certificate Signing Request**. Send the CSR
   to the bank's CA — not the certificate, and never a key file.
3. When the signed certificate returns, open the same certificate record and
   **Upload Signed Certificate**. Uploading to a *new* record instead of the original is
   the most common mistake: the new record has a different key pair and will not match.
4. Import the bank's issuing and intermediate CA certificates so the platform can validate
   *their* server certificate.
5. Setup → **Named Credentials** → new credential `BankACH`, endpoint
   `https://ach.bank.example.com`, and select `BankACH_Prod` as the client certificate.

**Apex after the change — note that nothing about credentials appears in code:**

```apex
public with sharing class AchGateway {

    public class AchException extends Exception {}

    public static HttpResponse post(String payloadJson) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:BankACH/v1/payments');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setTimeout(120000);          // 120s is the documented maximum per callout
        req.setBody(payloadJson);

        try {
            HttpResponse res = new Http().send(req);
            if (res.getStatusCode() >= 500) {
                throw new AchException('Partner 5xx: ' + res.getStatusCode());
            }
            return res;
        } catch (System.CalloutException e) {
            // Classify before escalating. The alert text names the side that failed.
            String m = e.getMessage();
            if (m.contains('bad_certificate') || m.contains('handshake_failure')) {
                throw new AchException('mTLS: our client certificate was rejected — '
                    + 'check the Named Credential binding and partner enrolment. ' + m);
            }
            if (m.contains('PKIX path building failed')) {
                throw new AchException('mTLS: we do not trust the partner chain — '
                    + 'import their intermediate CA. ' + m);
            }
            throw new AchException('Callout failed: ' + m);
        }
    }
}
```

**Why it works:** the private key never exists outside the platform, so there is no key
file to leak, rotate by hand or lose. Classifying the `CalloutException` message at the
point of failure is what stops the next incident becoming a week of network tickets:
`bad_certificate` is our certificate, `PKIX path building failed` is theirs.

---

## Example 2: Expiry and revocation monitor

**Context:** a previous certificate expired on a Friday evening. The batch failed silently
over the weekend and was discovered on Monday by the bank.

**Problem:** an mTLS callout works perfectly until the instant it does not. Diarising the
renewal fails because the slow part is the partner's signing round trip, not the upload —
by the time the expiry date arrives it is far too late to start.

**Solution — two independent signals, because expiry is not the only way a certificate
stops working:**

```apex
public with sharing class CertificateHealthCheck implements Schedulable {

    private static final Integer WARN_DAYS = 60;
    private static final Integer CRITICAL_DAYS = 30;

    public void execute(SchedulableContext ctx) {
        // Signal 1 — scheduled expiry. Long lead time, because re-enrolment is slow.
        for (Certificate c : [
                SELECT DeveloperName, ExpirationDate
                FROM Certificate
                WHERE ExpirationDate != null]) {
            Integer daysLeft = Date.today().daysBetween(c.ExpirationDate.date());
            if (daysLeft <= CRITICAL_DAYS) {
                AlertService.page('CERT_EXPIRING', c.DeveloperName + ' in ' + daysLeft + 'd');
            } else if (daysLeft <= WARN_DAYS) {
                AlertService.ticket('CERT_RENEWAL_DUE', c.DeveloperName);
            }
        }

        // Signal 2 — unscheduled failure. Catches revocation, a partner-side
        // enrolment change, or a chain that stopped validating, none of which
        // move the expiry date.
        try {
            HttpRequest probe = new HttpRequest();
            probe.setEndpoint('callout:BankACH/health');
            probe.setMethod('GET');
            probe.setTimeout(30000);
            HttpResponse res = new Http().send(probe);
            if (res.getStatusCode() != 200) {
                AlertService.page('MTLS_PROBE_HTTP', String.valueOf(res.getStatusCode()));
            }
        } catch (System.CalloutException e) {
            AlertService.page('MTLS_PROBE_HANDSHAKE', e.getMessage());
        }
    }
}
```

**Why it works:** the two signals fail for different reasons and neither subsumes the
other. The date check gives a renewal window long enough to absorb a partner CA's
turnaround. The probe is the only thing that catches a certificate revoked early, an
intermediate that changed on the partner side, or a Named Credential someone edited — all
of which leave `ExpirationDate` looking perfectly healthy. Run the probe against a
partner endpoint that is cheap and side-effect free; a `health` route exists for exactly
this, and posting a real payment to test the handshake is its own outage.
