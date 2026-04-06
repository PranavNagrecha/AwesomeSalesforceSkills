# Examples — Sandbox Data Isolation Gotchas

## Example 1: Workflow Email Alert Sent to Real Customers After Full Sandbox Refresh

**Context:** A QA team refreshed a Full sandbox to prepare for UAT testing. The sandbox contained a copy of all production Contacts and their email addresses. A workflow rule on the Case object was configured to send an email alert to the case Contact when a case was opened. The QA team created test cases in the sandbox to validate a new case routing process.

**Problem:** Every test case created in the sandbox triggered the workflow email alert, which was delivered to the real customer email addresses stored on the Contact records (verbatim copies from production). The deliverability setting in the sandbox was `All Email` — the same setting as the production org from which the sandbox was originally created. The team was not aware that deliverability settings are not automatically reset on refresh.

**Solution:**

Step 1 — Immediately set deliverability to `No Access` in sandbox Setup > Deliverability to stop further sends.

Step 2 — Scrub Contact email addresses:

```apex
// Run anonymously in the sandbox via Developer Console Execute Anonymous
// or chain from SandboxPostCopy as a Queueable for future refreshes
List<Contact> contacts = [
    SELECT Id, Email FROM Contact
    WHERE Email != null
    AND Email NOT LIKE '%.invalid'
    LIMIT 10000
];
for (Contact c : contacts) {
    c.Email = c.Email + '.invalid';
}
update contacts;
```

Step 3 — For future refreshes, register a SandboxPostCopy class that:
- Enqueues an `ObfuscateContactEmailsQueueable` to scrub Contact and Lead email fields
- Sets deliverability to `System Email Only` (note: deliverability cannot be set programmatically via Apex; it must be a manual step or handled via the Setup UI immediately after refresh)

Step 4 — Add "verify deliverability setting" and "confirm Contact email obfuscation" to the post-refresh runbook as mandatory steps before any QA testing begins.

**Why it works:** The root cause is that Contact/Lead emails are verbatim copies of production, and deliverability is not automatically reset. Explicit scrubbing ensures test data cannot reach real customers even if deliverability drifts back to `All Email`.

---

## Example 2: Nightly Batch Job Fires Against Production API From Sandbox

**Context:** An org runs a nightly scheduled Apex job at 1:00 AM that queries Opportunity records and pushes pipeline data to an external CRM analytics platform via a Named Credential. The job fires every night in production without issue. After a Full sandbox refresh, the sandbox began firing the same job nightly against the same analytics API endpoint — duplicating data in the analytics platform and consuming rate-limited API calls against the production analytics account.

**Problem:** The CronTrigger record for the nightly job was copied from production with `State = 'WAITING'`. The Named Credential endpoint URL was also copied unchanged, pointing at the production analytics endpoint. Since the analytics platform uses an API key stored in the Named Credential secret, and secrets are blanked on refresh, the first execution failed with an auth error. However, the analytics platform's error handling still logged the incoming requests, consuming the org's daily API quota for that endpoint. On the second night, the team had re-entered the Named Credential secret (unaware it now pointed to the production endpoint), and the job began successfully duplicating data.

**Solution:**

Implement the following in the SandboxPostCopy class:

```apex
global class SandboxIsolation implements SandboxPostCopy {
    global void runApexClass(SandboxContext context) {
        // 1. Abort all scheduled jobs immediately
        for (CronTrigger ct : [
            SELECT Id, CronJobDetail.Name
            FROM CronTrigger
            WHERE State IN ('WAITING', 'ACQUIRED', 'EXECUTING')
        ]) {
            System.debug('Aborting job: ' + ct.CronJobDetail.Name);
            System.abortJob(ct.Id);
        }

        // 2. Reset integration endpoint in Custom Setting to sandbox value
        //    (Named Credential URL must be updated manually in Setup)
        Analytics_Config__c cfg = Analytics_Config__c.getOrgDefaults();
        if (cfg != null) {
            cfg.Endpoint__c = 'https://analytics-sandbox.example.com/api';
            upsert cfg;
        }
    }
}
```

Add to the manual post-refresh runbook: "Update Named Credential 'AnalyticsPlatform' endpoint URL to https://analytics-sandbox.example.com before re-entering the API key secret."

**Why it works:** Aborting CronTriggers in SandboxPostCopy ensures no scheduled job can fire before the team has a chance to review and reconfigure integration endpoints. Documenting Named Credential URL updates in the runbook closes the gap that Apex cannot cover programmatically.

---

## Anti-Pattern: Relying on "No Credentials = No Harm" for Named Credentials

**What practitioners do:** A team assumes that because Named Credential secrets are blanked on sandbox refresh, any integration callout from the sandbox will fail harmlessly before reaching the production system.

**What goes wrong:** Several real-world scenarios break this assumption:

1. **Certificate-based mutual TLS**: If the Named Credential uses a client certificate for authentication (not a username/password or OAuth token), the certificate is copied to the sandbox along with the endpoint URL. The sandbox can successfully authenticate to the production endpoint without any re-entry of secrets.

2. **IP-allowlisted APIs**: If the production API trusts all calls from the Salesforce IP ranges (e.g., outbound callout IPs listed on Salesforce trust), a sandbox callout may succeed even without credentials, depending on the API's authentication model.

3. **Partial auth**: Some APIs return a useful partial response or log the request for auditing purposes even when authentication fails. The request still reaches the production system.

**Correct approach:** Never assume that a missing secret prevents sandbox-to-production communication. Always:
1. Update Named Credential endpoint URLs to point at test/sandbox endpoints before any callout is possible.
2. Abort scheduled jobs in SandboxPostCopy to prevent any callout window.
3. Explicitly verify in the sandbox that Named Credentials point at non-production hostnames before re-entering any secrets.
