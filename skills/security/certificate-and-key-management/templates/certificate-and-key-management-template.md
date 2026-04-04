# Certificate Rotation Runbook Template

Use this template to document a certificate rotation event. Fill in each section before executing the rotation. Keep a completed copy in your operations wiki or change management system.

---

## Rotation Summary

| Field | Value |
|---|---|
| Certificate Name in Salesforce | _(e.g., jwt_erp_sync_v2)_ |
| Certificate Type | _(self-signed / CA-signed)_ |
| Reason for Rotation | _(expiry / compromise / scheduled / CA change)_ |
| Old Certificate Expiry Date | _(YYYY-MM-DD)_ |
| New Certificate Expiry Date | _(YYYY-MM-DD)_ |
| Runbook Author | _(name)_ |
| Change Request / Ticket | _(link or ID)_ |
| Planned Execution Date | _(YYYY-MM-DD)_ |
| Execution Window | _(e.g., Sat 02:00–04:00 UTC)_ |

---

## Affected Integrations

List every integration, connected app, Named Credential, and Apex component that uses the certificate being rotated. This must be complete before execution begins.

| Integration / Component | Type | Environment | Owner / Team | Notes |
|---|---|---|---|---|
| _(e.g., ERP Sync Batch Job)_ | JWT OAuth | Production | _(team name)_ | _(notes)_ |
| _(e.g., Payment Gateway Named Credential)_ | mTLS Client Auth | Production | _(team name)_ | _(external contact)_ |

---

## Pre-Rotation Checklist

Complete all items before the rotation window begins.

- [ ] Old certificate expiry date confirmed: _(date)_
- [ ] All affected integrations identified and listed above
- [ ] External system team(s) notified of upcoming certificate change: _(date notified, contact name)_
- [ ] For CA-signed: new certificate obtained from CA and JKS assembled
- [ ] For CA-signed: original JKS archived in secure vault at: _(vault path or reference)_
- [ ] New certificate validated in lower environment (sandbox/UAT): _(environment name, tested by, date)_
- [ ] Rollback plan documented in the Rollback section below
- [ ] Change Request approved: _(CR number)_
- [ ] On-call engineer identified for monitoring period: _(name)_

---

## Certificate Creation / Import Steps

### Option A: Self-Signed Certificate (Salesforce-Generated)

1. Log in to the target Salesforce org (PRODUCTION — confirm before proceeding).
2. Navigate to: Setup > Security > Certificate and Key Management.
3. Click **Create Self-Signed Certificate**.
4. Fill in:
   - Label: `_(new cert label)_`
   - Unique Name: `_(new cert API name)_`
   - Key Size: 2048
   - Exportable Private Key: _(leave unchecked unless required)_
   - Expiration: `_(select date — recommend 2 years or per policy)_`
5. Click Save.
6. Click **Download Certificate** and save the `.crt` file.
7. Record the new certificate's expiry date: _(date)_

### Option B: CA-Signed Certificate Import

1. Confirm the JKS file is available at: _(vault path or local path)_
2. Log in to the target Salesforce org (PRODUCTION — confirm before proceeding).
3. Navigate to: Setup > Security > Certificate and Key Management.
4. Click **Import from Keystore**.
5. Upload: `_(filename.jks)_`
6. Keystore Password: _(retrieve from vault — do not record here)_
7. Click Save.
8. Confirm the certificate appears in the list with the correct alias and expiry date.
9. Record the new certificate's expiry date: _(date)_

Keystore assembly commands (run locally before import):
```bash
# Step 1: Convert PEM cert + key to PKCS#12
openssl pkcs12 -export \
  -in client_cert.crt \
  -inkey client_cert.key \
  -certfile ca_chain.crt \
  -out client_cert.p12 \
  -name "_(alias)_" \
  -passout pass:_(password)_

# Step 2: Convert PKCS#12 to JKS
keytool -importkeystore \
  -srckeystore client_cert.p12 \
  -srcstoretype PKCS12 \
  -srcstorepass _(password)_ \
  -destkeystore client_cert.jks \
  -deststoretype JKS \
  -deststorepass _(password)_ \
  -destkeypass _(password)_
```

---

## Reference Update Steps

Perform these steps **before** removing the old certificate.

### Connected App Update (JWT OAuth)

1. Navigate to: Setup > Apps > App Manager > _(connected app name)_ > Edit.
2. Under "Use Digital Signatures," upload the new certificate's `.crt` file.
3. Save the connected app.
4. Update any Apex code referencing the old certificate API name:
   ```apex
   // Update from old name to new name:
   jwt.setCertificateName('_(new_cert_api_name)_');
   ```
5. Deploy Apex change to production.

### Named Credential Update (mTLS)

1. Navigate to: Setup > Security > Named Credentials > _(named credential name)_ > Edit.
2. In the "Client Certificate" field, select the new certificate from the dropdown.
3. Save the Named Credential.

### External System Coordination

- [ ] Confirmed with _(external team / contact name)_ that the new certificate CN/SAN is: `_(value)_`
- [ ] External team has added the new certificate to their trust store / allowed-client list
- [ ] External team confirmation received: _(date/time, name of contact)_

---

## Validation Steps

Run these after updating all references. Do not deactivate the old certificate until all validation steps pass.

- [ ] JWT OAuth flow tested end-to-end: valid access token returned. _(tested by, date/time)_
- [ ] mTLS callout tested end-to-end: 200 response from external system. _(tested by, date/time)_
- [ ] Batch job / scheduled process executed manually and completed successfully. _(job name, date/time, result)_
- [ ] No errors in Salesforce Event Log or integration middleware. _(checked by, date/time)_
- [ ] All affected teams confirmed their integrations are operational. _(teams confirmed, date/time)_

---

## Old Certificate Deactivation

Do not proceed until all validation steps above are checked.

- [ ] Monitoring period complete (minimum 24 hours post-cutover)
- [ ] No integration errors reported during monitoring period
- [ ] Old certificate deleted in Setup > Certificate and Key Management
  - Certificate name deleted: `_(old cert API name)_`
  - Deleted by: _(name)_ on _(date)_

---

## Post-Rotation Record

| Field | Value |
|---|---|
| New Certificate Name | _(API name)_ |
| New Certificate Expiry | _(YYYY-MM-DD)_ |
| Next Rotation Due | _(set reminder: 60 days before expiry = YYYY-MM-DD)_ |
| Runbook Completed By | _(name)_ |
| Completion Date | _(YYYY-MM-DD)_ |
| Runbook Location (archived copy) | _(wiki URL or file path)_ |

---

## Rollback Plan

If the new certificate does not work after cutover:

1. Do not delete the old certificate — if it is still present, roll back all reference updates.
2. Revert the connected app's "Use Digital Signatures" to the old certificate.
3. Revert the Named Credential's "Client Certificate" field to the old certificate.
4. Revert any Apex code changes referencing the certificate name and redeploy.
5. Notify the external system team of the rollback.
6. Open an incident ticket and document what failed.
7. Schedule a post-mortem before the next rotation attempt.

---

## Notes and Exceptions

_(Record any deviations from this runbook, issues encountered, or decisions made during execution.)_
