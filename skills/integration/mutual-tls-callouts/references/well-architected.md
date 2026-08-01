# Well-Architected Notes — Mutual TLS Callouts

**Security:** the key pair is generated inside the platform and the private key is not
exportable, so the strongest control is procedural — create the certificate in Setup and
send out only the CSR. Any workflow that produces a key file on someone's machine has
already lost the property that makes this design safe.

**Reliability:** an mTLS callout gives no gradual degradation signal; it works until it
does not. That requires two independent monitors — a long-lead expiry check sized to the
partner's signing turnaround, and a probe callout that catches revocation, chain changes
and configuration edits, none of which move the expiry date.

## Official Sources Used

- Named Credentials as Callout Endpoints — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm
- Apex Developer Guide — Invoking Callouts Using Apex, including the 120-second maximum callout timeout — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Certificate object reference — DeveloperName, ExpirationDate, for the monitoring query — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_certificate.htm
- Identity Provider and certificate management in Setup (Certificate and Key Management) — https://help.salesforce.com/s/articleView?id=sf.security_keys_about.htm
- Named Credentials setup — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
