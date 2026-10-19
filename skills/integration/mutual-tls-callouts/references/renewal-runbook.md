# Renewal Runbook — client certificate for an mTLS partner

Goal: replace the certificate a Named Credential presents without a window where the partner rejects every call. The design keeps the old certificate bound until the new one is enrolled and proven.

## Timeline

| When | Step | Done when |
|---|---|---|
| Expiry − (partner turnaround + 30 days) | Create a new CA-signed certificate (`BankACH_Prod_2027`), private-key export off, same key size the partner expects | Certificate record exists; CSR downloadable |
| Same day | Send the CSR to the partner's CA / enrolment desk | Ticket reference recorded |
| On return | Upload the full signed chain to the **same** new record | `expirationDate` shows the signed certificate's date |
| Partner confirms enrolment | In a sandbox Named Credential, point the `ClientCertificate` parameter at the new certificate and run the probe | Probe returns 200 |
| Change window | Switch the production Named Credential parameter to the new certificate; run the probe | Probe returns 200 |
| After a quiet period agreed with the partner | Ask the partner to remove the old certificate from their keystore; delete the old certificate from source and the org | Old certificate gone from both sides |

## The switch, as a metadata diff

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: only the ClientCertificate parameter changes between releases -->
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>BankACH</label>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
    <namedCredentialParameters>
        <parameterName>DefaultCert</parameterName>
        <parameterType>ClientCertificate</parameterType>
        <certificate>BankACH_Prod_2027</certificate>
    </namedCredentialParameters>
</NamedCredential>
```

Deploy it like any other metadata change, with the probe as the post-deploy check. Rolling back is the same one-line change pointing at the previous certificate, which is why the old one stays until the quiet period ends.

## Before you start

- Retrieve `certs/` so the checker can read both certificates' `expirationDate` and `privateKeyExportable`.
- Confirm the partner's turnaround in writing; the first column of the timeline depends on it.
- If the old certificate was self-signed, the partner must add the new one to its keystore; plan the same enrolment step.
