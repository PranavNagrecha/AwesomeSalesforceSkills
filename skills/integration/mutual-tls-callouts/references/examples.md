# Examples — Mutual TLS Callouts

## Example 1: Bank ACH partner adds an mTLS mandate

**Context:** an existing nightly batch posts payment instructions to a bank. The bank
announces that from a fixed date it will require client-certificate authentication.

**Problem:** the current Apex sets an API key header. Apex can attach a certificate with
`HttpRequest.setClientCertificateName`, but binding it on the Named Credential keeps the
change in Setup and out of code — provided the certificate is created the right way round.

**Setup sequence (the order matters):**

1. Setup → **Certificate and Key Management** → **Create CA-Signed Certificate**. Name it
   for the partner and environment, e.g. `BankACH_Prod`. Salesforce generates the key pair
   internally. Turn private-key export off: `privateKeyExportable` defaults to true.
2. On the saved certificate record, **Download Certificate Signing Request**. Send the CSR
   to the bank's CA — not the certificate, and never a key file.
3. When the signed certificate returns, open the same certificate record and
   **Upload Signed Certificate**. Uploading to a *new* record instead of the original is
   the most common mistake: the new record has a different key pair and will not match.
4. Confirm with the bank that their server certificate chains to a CA the platform trusts;
   that is their side of the handshake, and the probe in Example 2 proves it.
5. Setup → **Named Credentials** → new credential `BankACH`, endpoint
   `https://ach.bank.example.com`, with `BankACH_Prod` as its client certificate (the
   `ClientCertificate` parameter in the metadata shown in SKILL.md).

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
            // Classify before escalating. The match strings below are placeholders: capture
            // the exact messages your org returns in a sandbox probe and match on those.
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

**Why it works:** with export turned off, the private key never exists outside the platform,
so there is no key file to leak, rotate by hand or lose. Classifying the `CalloutException`
message at the point of failure — "they rejected our certificate" versus "we don't trust
their chain" — is what stops the next incident becoming a week of network tickets.

---

## Example 2: Expiry and revocation monitor

**Context:** a previous certificate expired on a Friday evening. The batch failed silently
over the weekend and was discovered on Monday by the bank.

**Problem:** an mTLS callout works perfectly until the instant it does not. Diarising the
renewal fails because the slow part is the partner's signing round trip, not the upload —
by the time the expiry date arrives it is far too late to start.

**Solution — two independent signals, because expiry is not the only way a certificate
stops working.** Signal 1 runs in CI against source: retrieve the certificate metadata and let
the checker read `expirationDate` (Certificate isn't an sObject in the Object Reference, so plain Apex SOQL can't read its expiry).

```bash
sf project retrieve start --metadata Certificate --target-org prod --output-dir cert-check
python3 skills/integration/mutual-tls-callouts/scripts/check_mutual_tls_callouts.py \
  --manifest-dir cert-check --strict      # WARN (and with --strict, fail) inside 60 days
```

Signal 2 runs in the org: a scheduled probe that exercises the real handshake.

```apex
public with sharing class MtlsProbe implements Schedulable {
    public void execute(SchedulableContext ctx) {
        System.enqueueJob(new ProbeJob());   // callouts aren't allowed directly from execute()
    }

    public class ProbeJob implements Queueable, Database.AllowsCallouts {
        public void execute(QueueableContext qc) {
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
}
```

**Why it works:** the two signals fail for different reasons and neither subsumes the
other. The date check gives a renewal window long enough to absorb a partner CA's
turnaround. The probe is the only thing that catches a certificate revoked early, an
intermediate that changed on the partner side, or a Named Credential someone edited — all
of which leave `expirationDate` looking perfectly healthy. Run the probe against a
partner endpoint that is cheap and side-effect free; a `health` route exists for exactly
this, and posting a real payment to test the handshake is its own outage.
