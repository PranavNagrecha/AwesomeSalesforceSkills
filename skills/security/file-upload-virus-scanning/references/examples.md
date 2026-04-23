# File Upload Virus Scanning — Examples

## Example 1: Post-Save Queueable With State Field

**Context:** Internal org accepts case attachments from employees.

**Design:**
- `ContentVersion` after-insert trigger enqueues `FileScanQueueable`.
- Queueable calls the scanning API with the file blob.
- On verdict, updates `ContentVersion.ScanStatus__c`.
- Case detail LWC hides attachments where `ScanStatus__c != 'Clean'`.

**Why it works:** Near-invisible UX for internal users; policy is centralized.

---

## Example 2: Experience Cloud Pre-Save With Middleware

**Context:** Customer portal accepts claim document uploads.

**Design:**
- Upload LWC uploads to MuleSoft endpoint (not directly to Salesforce).
- MuleSoft scans; on Clean, creates ContentVersion via Salesforce API.
- On Infected, rejects with a user-facing message.

**Why it works:** Untrusted bytes never reach Salesforce storage.

---

## Anti-Pattern: Deleting Infected Files

A trigger deletes ContentVersion when scan returns infected. Audit trail is lost; regulators cannot verify what the file was. Prefer quarantine with blob redaction and state flag.
