# Gotchas — Security Incident Response

Non-obvious Salesforce platform behaviors that cause real production problems during security incident response.

## Gotcha 1: Freezing a User Leaves Active Sessions and OAuth Tokens Alive

**What happens:** When an admin freezes a user in Setup > Users, the frozen user cannot initiate new logins. However, any currently active browser sessions (AuthSession records) remain fully valid and functional. Similarly, OAuth refresh tokens issued to Connected Apps are completely unaffected. An attacker with an open session or a valid refresh token retains full API and UI access even after the freeze.

**When it occurs:** Every time an admin freezes an account without following up with session revocation and OAuth token deletion. It is the most common incomplete containment pattern in Salesforce IR.

**How to avoid:** Treat freeze as a two-step operation:
1. Freeze in Setup > Users (blocks new logins)
2. Immediately query `AuthSession` and DELETE each session record via REST: `DELETE /services/data/v60.0/sobjects/AuthSession/{Id}`
3. Revoke OAuth tokens: query `AuthToken` for the user and DELETE each, or use Setup > Connected Apps > OAuth Usage > Revoke All

---

## Gotcha 2: EventLogFile 1-Day Retention in Free Orgs Means Logs Can Vanish Before Investigation Starts

**What happens:** In Salesforce orgs without the Event Monitoring add-on, EventLogFile records for most event types are retained for only 1 calendar day (the log for a given day is available for ~24 hours after midnight UTC of that day). If an incident is discovered 26 hours after the attacker's last action, the EventLogFile containing the attacker's Report and API activity may already be permanently deleted with no recovery option.

**When it occurs:** Any org without Salesforce Shield or the Event Monitoring add-on. Common in professional, enterprise, and developer orgs.

**How to avoid:** Always query and download EventLogFile CSVs as the very first action in any IR engagement — before any containment steps. Even if the logs are only partially useful, getting them out is the priority. For ongoing protection, consider configuring an automated daily export of EventLogFile to an external SIEM or S3-compatible storage using the Salesforce REST API and a scheduled integration job.

---

## Gotcha 3: SetupAuditTrail Does Not Capture Metadata API Deploys in Full Detail

**What happens:** SetupAuditTrail records Setup-UI configuration changes reliably, but metadata changes deployed programmatically via the Metadata API (e.g., `sf deploy`, `ant migrate`, Workbench deploy) may not appear in SetupAuditTrail at the same level of granularity. An attacker with Metadata API credentials (e.g., via a stolen CI/CD service account) can modify Apex classes, Flows, or permission sets without generating easily readable SetupAuditTrail entries.

**When it occurs:** When the attacker had access to a service account with `Modify Metadata Through Metadata API Integrations` permission, or used a development tool like VS Code + Salesforce CLI to push changes.

**How to avoid:** In addition to querying SetupAuditTrail, use the `MetadataApiOperation` EventLogFile event type (Event Monitoring add-on required) to detect API-based deploys. Cross-reference timestamps with the known attack window. Also check for recent changes to Apex classes, Flows, and permission sets via the sObject metadata fields (`LastModifiedDate`, `LastModifiedBy`):
```soql
SELECT Id, Name, LastModifiedDate, LastModifiedBy.Username
FROM ApexClass
WHERE LastModifiedDate >= 2025-03-10T18:00:00Z
ORDER BY LastModifiedDate DESC
```

---

## Gotcha 4: Transaction Security Policies Only Apply to Events After Activation

**What happens:** When a security team creates a Transaction Security Policy with a Block or Notification action in response to an active attack, they sometimes expect the policy to retroactively flag past events or terminate sessions from earlier activity. Transaction Security Policies are purely prospective — they only evaluate new platform events fired after the policy is activated and saved.

**When it occurs:** In every incident where a policy is created reactively during an attack. The policy starts blocking new occurrences but has no effect on anything that already happened.

**How to avoid:** Understand that Transaction Security Policies are a containment and prevention tool, not a forensic tool. Use them during IR to block ongoing attacker activity (e.g., blocking new Report exports while the investigation is active), but use EventLogFile queries for historical forensics. Document that the policy was activated at a specific time so that future analysis correctly attributes which events occurred before vs. after the policy.

---

## Gotcha 5: LoginAnomaly Score Threshold and Suppression Are Org-Configurable

**What happens:** LoginAnomaly events are only generated when Salesforce's ML model exceeds a risk score threshold configured in the org's Transaction Security Policy for `LoginAnomaly`. If no policy referencing `LoginAnomaly` has been set up with Notifications or Blocks, the `LoginAnomaly` sObject records are still created but no admin alert fires. Many orgs with Shield have LoginAnomaly data sitting in the object that nobody is monitoring because the alerting policy was never configured.

**When it occurs:** Orgs that licensed Shield or Event Monitoring but never completed the Transaction Security Policy configuration for LoginAnomaly alerting.

**How to avoid:** After completing IR and before closing the incident, verify that a Transaction Security Policy exists for the `LoginAnomaly` event type with at minimum a Notification action and a score threshold (e.g., Score > 0.7). This ensures future high-risk logins generate admin email alerts. If the org has a SIEM, also configure the Real-Time Event Monitoring Streaming API to push LoginAnomaly events into the SIEM via Platform Events or a Pub/Sub subscriber.
