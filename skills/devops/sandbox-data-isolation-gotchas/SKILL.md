---
name: sandbox-data-isolation-gotchas
description: "Use this skill when a sandbox has reached out to production systems, sent emails to real users, run live scheduled jobs, or leaked sensitive data after a refresh. Triggers: 'sandbox sent email to real customers', 'scheduled job fired against production API', 'integration hit live system from sandbox', 'Contact email not changed to .invalid', 'SandboxPostCopy did not run'. NOT for planning sandbox refresh cycles (use sandbox-refresh-and-templates), NOT for selecting sandbox types or counts (use environment-strategy), and NOT for scrubbing PII after copy (use sandbox-data-masking if that skill exists — otherwise document the masking logic in SandboxPostCopy)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "sandbox sent emails to real customers after the refresh and we need to stop it"
  - "scheduled job in sandbox fired against the production API endpoint after refresh"
  - "integration callout from sandbox hit the live payment gateway instead of the test gateway"
  - "Contact and Lead email addresses were not changed to .invalid after sandbox refresh"
  - "SandboxPostCopy class did not run and now sandbox is misconfigured after refresh"
  - "sandbox is making live API calls because Named Credentials still point to production"
  - "how do I prevent the sandbox from sending outbound email to real users"
tags:
  - sandbox
  - data-isolation
  - email-deliverability
  - sandboxpostcopy
  - scheduled-jobs
  - integration-endpoints
  - devops
  - security
inputs:
  - "Sandbox type (Developer, Developer Pro, Partial Copy, Full)"
  - "Whether a SandboxPostCopy class is registered on the sandbox in production"
  - "List of integrations and Named Credentials that connect to external systems"
  - "Whether email deliverability setting has been reviewed after the most recent refresh"
  - "Whether active scheduled jobs in the sandbox connect to production endpoints"
outputs:
  - "Pre-flight isolation checklist covering email, scheduled jobs, and integration endpoints"
  - "SandboxPostCopy implementation guidance for disabling dangerous jobs and resetting endpoints"
  - "Decision table for which isolation controls to apply per sandbox type"
  - "Audit queries for identifying live-endpoint callouts and active scheduled jobs in the sandbox"
dependencies:
  - devops/sandbox-refresh-and-templates
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Sandbox Data Isolation Gotchas

This skill activates when a sandbox has made unexpected contact with production systems — sending email to real users, firing scheduled jobs against live APIs, or leaking PII — after creation or refresh. It focuses on the isolation controls that are most commonly missed: email deliverability settings, scheduled job cleanup, integration endpoint resets, and the specific SandboxPostCopy behaviors that catch practitioners off-guard. It does not cover which sandbox type to choose, how to mask PII in copied records, or general refresh cycle management.

---

## Before Starting

Gather this context before working in this domain:

- Confirm which sandbox type is involved. Email deliverability defaults differ between sandbox types and Salesforce release windows. Full sandboxes copy all production records including any stored email addresses on Contact and Lead objects.
- Ask whether a SandboxPostCopy class exists in production and was registered on the sandbox record before the last refresh. If not, all isolation steps are manual and may have been missed.
- Identify every integration that connects the sandbox to an external system. Named Credentials are copied from production but their secrets are blanked — however, the endpoint URL is preserved and may still point to production.
- Check whether any scheduled Apex or scheduled Flow jobs are active in the sandbox. Salesforce copies CronTrigger records from production in a WAITING state. They will fire on schedule unless explicitly aborted.
- The most common wrong assumption: practitioners believe Salesforce automatically changes all email addresses to `.invalid` after a sandbox refresh. In fact, only **User** object email addresses are converted. Contact and Lead email addresses are **not** modified.

---

## Core Concepts

### Email Deliverability — What Is and Is Not Controlled Automatically

Salesforce sandbox email deliverability is a two-layer control:

**Layer 1 — Deliverability setting (Setup > Deliverability)**

Every sandbox has an email deliverability setting with three levels:
- `No Access` — No email is sent from the sandbox. System and workflow emails are suppressed.
- `System Email Only` — Only system-generated emails (password resets, sandbox activation notices) are sent. Workflow email alerts and Apex `Messaging.sendEmail()` calls are suppressed.
- `All Email` — All email is sent, including workflow alerts and Apex emails.

New sandboxes created via the Setup UI default to `System Email Only`. However, **sandboxes that were refreshed in older releases or promoted from an existing sandbox may inherit the previous deliverability setting** — including `All Email`. Always verify the deliverability setting after every refresh.

**Layer 2 — User email address obfuscation**

When a sandbox is refreshed, Salesforce appends `.invalid` to all **User** object `Email` field values (e.g., `jane.doe@example.com` becomes `jane.doe@example.com.invalid`). This prevents password reset emails and system notifications from reaching real users.

**What is NOT obfuscated:** Contact, Lead, Person Account, and any other object's email fields are copied verbatim from production. If a workflow email alert targets a Contact's email, and deliverability is `All Email`, that real email address will receive the message. This is one of the most common sandbox data leakage vectors.

### SandboxPostCopy Interface and Its Execution Constraints

The `SandboxPostCopy` Apex interface is the only platform-native hook for automating sandbox isolation immediately after refresh. However, it runs under constraints that practitioners frequently underestimate:

- **Runs as Automated Process user.** This is a system user with minimal permissions. DML against objects the Automated Process user cannot access will throw a `System.NoAccessException` or fail silently depending on the context. If the SandboxPostCopy class needs to abort scheduled jobs, update Custom Settings, or insert records on custom objects, the Automated Process user must have the required permissions (via a permission set).
- **No guarantee of sequential completion before sandbox is usable.** Salesforce marks the sandbox ready for login while the SandboxPostCopy class may still be running or queued. Users can log in and trigger automations before isolation steps complete.
- **Single registration per refresh.** Only one class can be registered per sandbox refresh. If isolation logic and test data setup are both needed, they must be combined in one class or chained via Queueable.
- **Exceptions do not block sandbox availability.** If the SandboxPostCopy class throws an unhandled exception, the sandbox becomes usable but the class is marked as failed. Salesforce does not retry the class. The only recovery is a new refresh or manual execution of the same logic.

### Scheduled Job Carry-Over

CronTrigger records (scheduled Apex jobs) are copied from production when a Full or Partial Copy sandbox is refreshed. Unlike User emails, scheduled jobs are **not** automatically deactivated. A scheduled Apex job that calls out to a production API, processes records, or sends email will execute on the same schedule as production from the moment the sandbox refresh completes.

The correct mitigation is to abort all CronTrigger records in the SandboxPostCopy class:

```apex
for (CronTrigger ct : [SELECT Id FROM CronTrigger WHERE State IN ('WAITING', 'ACQUIRED', 'EXECUTING')]) {
    System.abortJob(ct.Id);
}
```

Aborting CronTriggers requires the Automated Process user to have the "Manage Users" or relevant system permission. If the permission is missing, the abort will fail silently or throw — pre-grant via a permission set.

### Integration Endpoint Carry-Over

Named Credentials are copied from production to the sandbox. Their **endpoint URLs** are preserved (pointing at production endpoints), but their **secrets** (passwords, OAuth tokens) are blanked. This creates two risks:

1. If the Named Credential uses certificate-based or IP-allowlist-only auth, the sandbox may still successfully authenticate to the production endpoint using the same certificate that was copied.
2. If the endpoint URL is not environment-specific (e.g., uses a production hostname), any callout from the sandbox — even one that appears to fail due to a missing secret — may reach the production system with partial or unauthenticated requests.

The SandboxPostCopy class should update Named Credential endpoint URLs to point at sandbox-appropriate test endpoints. However, Named Credential secrets (passwords, tokens) cannot be set programmatically — they require manual re-entry in Setup after refresh.

---

## Common Patterns

### Pattern 1: Pre-Flight Isolation Checklist in SandboxPostCopy

**When to use:** Every Full or Partial Copy sandbox refresh where the sandbox will be used for development, testing, or demos. Developer sandboxes copy no data so most of these concerns do not apply, but email deliverability still must be verified.

**How it works:**

```apex
global class SandboxIsolation implements SandboxPostCopy {
    global void runApexClass(SandboxContext context) {
        // 1. Abort all scheduled jobs
        List<CronTrigger> jobs = [
            SELECT Id FROM CronTrigger
            WHERE State IN ('WAITING', 'ACQUIRED', 'EXECUTING')
        ];
        for (CronTrigger ct : jobs) {
            System.abortJob(ct.Id);
        }

        // 2. Reset integration endpoints in Custom Metadata (Named Cred URLs
        //    must be updated manually; update any Custom Settings that store URLs)
        Integration_Config__c cfg = Integration_Config__c.getOrgDefaults();
        if (cfg != null) {
            cfg.API_Endpoint__c = 'https://api.sandbox.example.com';
            upsert cfg;
        }

        // 3. Log isolation actions
        System.debug('SandboxIsolation: completed for sandbox '
            + context.sandboxName()
            + ' orgId=' + context.organizationId());
    }
}
```

**Why not the alternative:** Relying on manual post-refresh runbooks means any missed step goes undetected until an incident occurs. SandboxPostCopy runs automatically and is the only supported hook that fires before users can log in and trigger workflows.

### Pattern 2: Scrubbing Contact and Lead Emails Post-Refresh

**When to use:** Any Full or Partial Copy sandbox that will be used for QA, UAT, or demo scenarios where workflow email alerts, case auto-responses, or Apex emails might fire toward Contact/Lead email addresses.

**How it works:** Because Contact and Lead emails are not automatically obfuscated, the SandboxPostCopy class (or a Queueable chained from it) must update those fields. Do this in batches due to governor limits:

```apex
public class ObfuscateContactEmailsQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        List<Contact> contacts = [
            SELECT Id, Email FROM Contact
            WHERE Email != null
            AND Email NOT LIKE '%.invalid'
            LIMIT 10000
        ];
        for (Contact c : contacts) {
            c.Email = c.Email + '.invalid';
        }
        if (!contacts.isEmpty()) {
            update contacts;
        }
        // If more records remain, re-enqueue
        Integer remaining = [SELECT COUNT() FROM Contact
            WHERE Email != null AND Email NOT LIKE '%.invalid'];
        if (remaining > 0) {
            System.enqueueJob(new ObfuscateContactEmailsQueueable());
        }
    }
}
```

Chain this from SandboxPostCopy:

```apex
System.enqueueJob(new ObfuscateContactEmailsQueueable());
```

**Why not the alternative:** Setting deliverability to `No Access` would suppress the immediate risk, but it also suppresses legitimate system emails needed for QA testing. Explicit email scrubbing ensures the sandbox can run with `System Email Only` or `All Email` for testing purposes without risking leakage.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Sandbox emails reached real customers after refresh | Set deliverability to System Email Only; scrub Contact/Lead emails via Queueable; investigate which workflow or Apex triggered the sends | Email deliverability defaults to All Email in some refresh scenarios; Contact emails are not auto-obfuscated |
| Scheduled job fired against production API from sandbox | Abort all CronTrigger records in SandboxPostCopy; update endpoint references in Custom Settings | Scheduled jobs are copied in WAITING state and fire on schedule unless explicitly aborted |
| Named Credential still points at production endpoint | Update Named Credential URL manually in sandbox Setup; for non-secret URLs, set replacement value via Custom Settings in SandboxPostCopy | Named Credential secrets and URLs are copied; URLs cannot be changed programmatically pre-Spring '25 |
| SandboxPostCopy class failed with permissions error | Assign a permission set to the Automated Process user covering the objects the class touches; re-run logic manually | Automated Process user has minimal default permissions; DML on custom objects fails without explicit grants |
| SandboxPostCopy ran but Contact emails were not changed | Contact/Lead email obfuscation is not built in; implement a Queueable from SandboxPostCopy to scrub those fields | Platform only obfuscates User emails; all other email fields are verbatim copies from production |
| Developer sandbox — concerned about data leakage | Verify deliverability setting (System Email Only); no data is copied so Contact/Lead email risk does not apply | Developer sandboxes contain metadata only, not production records |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Triage the incident or risk** — determine whether this is a post-incident investigation (email was already sent, job already fired) or a pre-refresh checklist review. The output differs: incidents require root-cause analysis; pre-refresh requires a checklist walkthrough.
2. **Check email deliverability** — in sandbox Setup > Deliverability, confirm the setting is `System Email Only` (or `No Access` if email testing is not required). Change it if needed; this takes effect immediately.
3. **Audit Contact and Lead email fields** — run `SELECT COUNT() FROM Contact WHERE Email != null AND Email NOT LIKE '%.invalid'` in the sandbox. If the count is non-zero and deliverability is not `No Access`, scrub those records using the Queueable pattern above.
4. **Audit active scheduled jobs** — run `SELECT Id, CronJobDetail.Name, State FROM CronTrigger WHERE State != 'DELETED'` in the sandbox. For each WAITING job, evaluate whether it connects to an external system or sends email. Abort those that do.
5. **Audit Named Credentials and integration config** — list all Named Credentials in the sandbox (Tooling API or Setup UI). For each one, confirm the endpoint URL is a sandbox/test URL. Update Custom Settings or Custom Metadata records that store endpoint URLs.
6. **Verify or implement SandboxPostCopy** — confirm a SandboxPostCopy class is registered on the sandbox record in production. If not, implement one using the isolation pattern above before the next refresh.
7. **Document gaps as runbook items** — anything that cannot be automated (Named Credential secrets, OAuth token re-authorization) belongs in a written post-refresh runbook. Every manual step is a risk vector if skipped.

---

## Review Checklist

Run through these before marking sandbox isolation work complete:

- [ ] Email deliverability in sandbox Setup is `System Email Only` or `No Access`
- [ ] Contact and Lead email fields have been scrubbed to `.invalid` (or confirmed as metadata-only sandbox)
- [ ] No CronTrigger records in WAITING state that point at external production systems
- [ ] Named Credential endpoint URLs have been reviewed and updated to sandbox/test targets
- [ ] Custom Settings and Custom Metadata records storing endpoint URLs have been updated
- [ ] SandboxPostCopy class is registered in production for the next refresh
- [ ] SandboxPostCopy class runs as Automated Process user and that user has the required permissions
- [ ] Manual post-refresh runbook exists and covers Named Credential secrets and OAuth re-authorization

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Contact and Lead emails are NOT changed to `.invalid` on refresh** — Only User object `Email` fields are obfuscated during sandbox creation and refresh. Contact, Lead, Person Account, and any other object's email-type fields are copied verbatim from production. Any workflow email alert, Apex `Messaging.sendEmail()`, or case auto-response that targets those fields will send to real addresses if deliverability is not `No Access`.

2. **SandboxPostCopy runs as Automated Process user with minimal permissions** — The Automated Process user cannot access custom objects by default, cannot perform DML on many standard objects, and cannot call `System.abortJob()` without the appropriate system permission. If the SandboxPostCopy class silently fails, the first sign is often an isolation incident after users log in.

3. **Scheduled jobs fire immediately after refresh without warning** — CronTrigger records are copied from production with `State = 'WAITING'`. They begin evaluating against their next fire time the moment the sandbox is available. A job that fires at 2:00 AM daily in production will fire at 2:00 AM in the sandbox the same night the refresh completes.

4. **Named Credential endpoint URLs survive the refresh unchanged** — The secrets (passwords, OAuth tokens) are blanked, but the URL field is copied as-is. In orgs using certificate-based mutual TLS or IP-allowlisted OAuth, the sandbox can successfully call the production API even without an explicit secret. Always confirm Named Credential endpoint URLs in the sandbox point to test systems.

5. **Deliverability setting is not reset to a safe default on every refresh** — Sandboxes created from scratch default to `System Email Only`. However, sandboxes refreshed from an existing sandbox that had `All Email` enabled can carry forward that setting. Do not assume the deliverability setting is safe after a refresh — always verify it explicitly.

6. **SandboxPostCopy exceptions do not surface in the sandbox Setup UI by default** — If the class fails, the sandbox status page may show a generic completion message rather than an error. Enable debug logging for the Automated Process user before the refresh to capture the execution trace.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Sandbox isolation pre-flight checklist | Ordered checklist for email deliverability, Contact/Lead email scrubbing, scheduled job audit, and Named Credential review |
| SandboxPostCopy isolation class | Global Apex class implementing SandboxPostCopy that aborts scheduled jobs and resets integration config on every refresh |
| Contact/Lead email scrub Queueable | Apex Queueable that appends `.invalid` to Contact and Lead email fields, chained from SandboxPostCopy |
| Integration endpoint audit queries | SOQL/Tooling API queries to identify Named Credentials and Custom Settings pointing at production URLs |

---

## Related Skills

- `devops/sandbox-refresh-and-templates` — Covers the full refresh lifecycle: interval management, sandbox templates, and SandboxPostCopy registration. Use that skill for refresh planning; use this skill when isolation controls specifically have failed or need auditing.
- `devops/environment-specific-value-injection` — Covers the mechanism for keeping endpoint URLs, client IDs, and other env-specific values in Custom Metadata or Named Credentials so they do not hardcode to production values.
