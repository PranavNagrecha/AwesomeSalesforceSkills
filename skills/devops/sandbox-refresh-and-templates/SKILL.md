---
name: sandbox-refresh-and-templates
description: "Sandbox refresh cycles, sandbox templates, post-refresh automation via the SandboxPostCopy Apex interface, and data handling during refresh. NOT for sandbox type selection (use sandbox-strategy)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - sandbox-refresh
  - sandbox-templates
  - post-refresh-automation
  - sandboxpostcopy
  - devops
  - data-handling
inputs:
  - Sandbox type (Developer, Developer Pro, Partial Copy, Full)
  - Whether a SandboxPostCopy Apex class exists in the org
  - Whether sandbox templates have been defined for Partial Copy sandboxes
  - List of integrations, Named Credentials, and scheduled jobs that must be re-configured after refresh
outputs:
  - Refresh readiness assessment with pre-refresh checklist
  - SandboxPostCopy implementation guidance and code pattern
  - Post-refresh runbook for manual steps the Apex class cannot automate
  - Sandbox template configuration recommendations
triggers:
  - my sandbox data is stale and I need to bring it back in line with production
  - how do I automate user setup and org settings after a sandbox refresh
  - my SandboxPostCopy class is not running after the sandbox is refreshed
  - what data gets copied into a Partial Copy sandbox and how do I control it
  - integrations are broken in the sandbox after refresh and Named Credentials are missing
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Sandbox Refresh and Templates

This skill activates when a practitioner needs to run, plan, or troubleshoot a sandbox refresh — including how to configure sandbox templates for Partial Copy sandboxes, automate post-refresh setup using the SandboxPostCopy Apex interface, and handle data safely during the refresh process. It does not cover choosing which sandbox type to use (see `admin/sandbox-strategy` for that).

---

## Trigger Scenarios

- "my sandbox data is stale and I need to bring it back in line with production"
- "how do I automate user setup and org settings after a sandbox refresh"
- "my SandboxPostCopy class is not running after the sandbox is refreshed"
- "what data gets copied into a Partial Copy sandbox and how do I control it"
- "integrations are broken in the sandbox after refresh — Named Credentials are missing"
- "scheduled jobs are not running in the sandbox after we refreshed it"
- "I need to scrub PII data automatically when the sandbox copies from production"

---

## Before Starting

Gather this context before working in this domain:

- Know the sandbox type — refresh interval, data scope, and template availability differ by type.
- Confirm whether a SandboxPostCopy class already exists in the production org (search for classes implementing `SandboxPostCopy`).
- Identify all integrations and Named Credentials that point at external systems — these reset on refresh and require manual reconfiguration or SandboxPostCopy logic.
- Identify all active scheduled jobs that should not execute in the sandbox against production endpoints.
- Confirm whether any hardcoded org IDs exist in custom settings, metadata, or code.

---

## Core Concepts

### Refresh Intervals by Sandbox Type

Salesforce enforces mandatory minimum intervals between sandbox refreshes. A sandbox cannot be refreshed again until the interval has elapsed since the previous refresh completion.

| Sandbox Type | Refresh Interval | Data Copied |
|---|---|---|
| Developer | 1 day | Metadata only — no production data |
| Developer Pro | 1 day | Metadata only — no production data |
| Partial Copy | 5 days | Metadata + subset of data defined by sandbox template |
| Full | 29 days | Metadata + all production data (storage mirrors production) |

Developer and Developer Pro sandboxes are configuration-only copies. They receive no production records. Full sandboxes are exact replicas including all records. Partial Copy sandboxes receive a data subset controlled by a sandbox template.

### Sandbox Templates (Partial Copy Sandboxes Only)

Sandbox templates define which objects and how many records are copied into a Partial Copy sandbox. Templates are configured in Production under Setup > Sandbox Templates before the sandbox is created or refreshed.

Key behaviors:
- Templates are only available for Partial Copy sandboxes. Developer, Developer Pro, and Full sandboxes do not use templates.
- Each template specifies objects and an optional record count cap per object.
- If no template is specified, a Partial Copy sandbox copies a default subset of records.
- Templates do not filter by field value or relationship — they select records by count across the whole object.
- Related records (parent lookups) are followed automatically to maintain referential integrity, which can cause the actual record count to exceed template caps.
- Templates must be created and attached before the sandbox refresh is initiated; they cannot be applied retroactively.

### SandboxPostCopy Interface

The `SandboxPostCopy` interface is a System namespace Apex interface that runs automatically at the end of sandbox creation or refresh. It is the only supported mechanism for automating post-refresh configuration inside the sandbox itself.

**Interface definition:**
```apex
global interface SandboxPostCopy {
    void runApexClass(SandboxContext context);
}
```

**SandboxContext methods available inside `runApexClass`:**
- `context.organizationId()` — returns the sandbox org's 18-character org ID
- `context.sandboxId()` — returns the sandbox record ID from the production org
- `context.sandboxName()` — returns the sandbox name (e.g., `UAT`, `QA`)

**How to register the class:**
When creating or refreshing a sandbox via Setup UI, specify the Apex class name in the "Apex Class" field on the sandbox create/refresh form. The class must exist in the production org (not the sandbox), must be global, and must implement `SandboxPostCopy`.

**Execution context:**
The class runs under the Automated Process user in the new sandbox. This user does not have access to all objects and features. Any DML or callouts must be authorized under that user's permission set. Use `@future` or Queueable if the work needs to run asynchronously after the initial post-copy script completes.

**What SandboxPostCopy can automate:**
- Resetting user passwords or activating sandbox users
- Inserting or updating custom settings to point at sandbox endpoints
- Deactivating scheduled jobs or triggers that should not fire in a sandbox
- Scrubbing or masking sensitive field values on records
- Creating test data or reference records that the sandbox requires

### Org ID Changes on Refresh

Every time a sandbox is refreshed, the sandbox org receives a new organization ID. Any code, custom setting, or metadata that stores the org ID as a hardcoded value will be stale after the refresh. The SandboxContext object provides the new org ID via `context.organizationId()` and should be used to update any stored org ID values inside the post-copy script.

---

## Mode 1: Plan and Execute a Sandbox Refresh

Use this mode when preparing for an upcoming refresh or executing one for the first time with proper automation.

### Step 1 — Confirm refresh eligibility

Check when the sandbox was last refreshed. The refresh option in Setup is greyed out until the interval has elapsed. The interval resets from the moment the previous refresh completed (not when it was initiated).

### Step 2 — Check or create a sandbox template (Partial Copy only)

If the target is a Partial Copy sandbox, review the template attached to it under Setup > Sandbox Templates. Confirm it includes the objects your team needs for testing. Attach or update the template before initiating the refresh.

### Step 3 — Write or update the SandboxPostCopy class in production

The class must live in production and must be global. Minimum pattern:

```apex
global class SandboxSetup implements SandboxPostCopy {
    global void runApexClass(SandboxContext context) {
        String sandboxName = context.sandboxName();
        String orgId = context.organizationId();

        // Update custom settings with the sandbox org ID
        Sandbox_Config__c cfg = Sandbox_Config__c.getOrgDefaults();
        cfg.Org_ID__c = orgId;
        cfg.Environment_Name__c = sandboxName;
        upsert cfg;

        // Deactivate any scheduled jobs that should not run in sandbox
        for (CronTrigger ct : [SELECT Id FROM CronTrigger WHERE State = 'WAITING']) {
            System.abortJob(ct.Id);
        }

        // Reset integration endpoint to sandbox URL in custom metadata
        // (use a Queueable for callouts or DML that needs async context)
    }
}
```

### Step 4 — Register the class on the sandbox record

In Setup > Sandboxes, click Refresh next to the target sandbox. In the refresh form, enter the name of the `SandboxPostCopy` class in the "Apex Class" field.

### Step 5 — Initiate the refresh

Submit the refresh. Monitor status under Setup > Sandboxes. A Full sandbox refresh can take hours to days depending on data volume. Developer sandboxes typically complete in minutes.

### Step 6 — Run the post-refresh manual runbook

Document and execute any steps the SandboxPostCopy class cannot handle:
- Re-enter Named Credential passwords and OAuth tokens (these are blanked on refresh)
- Re-authorize connected apps that use user-agent OAuth flows
- Update any external system configuration that points at the old sandbox URL
- Verify email deliverability settings if the sandbox should not send outbound email

---

## Mode 2: Review or Audit Post-Refresh State

Use this mode on an existing sandbox to assess whether refresh automation is adequate or identify drift from production.

1. Check whether a SandboxPostCopy class is registered on the sandbox record in production Setup. If none, all post-refresh setup is manual and error-prone.
2. Search the production org for any Apex classes implementing `SandboxPostCopy`. Confirm only one active class is registered per sandbox.
3. Audit custom settings and custom metadata for hardcoded org IDs — query `Organization.Id` and compare against stored values.
4. List active scheduled jobs in the sandbox (`SELECT Id, CronJobDetail.Name, State FROM CronTrigger`). Flag any that point at production endpoints.
5. Review Named Credentials — any that require password/OAuth reconfiguration after refresh should be documented in the manual runbook.
6. For Partial Copy sandboxes, verify the sandbox template includes all objects needed for current test scenarios. Templates should be reviewed before each refresh cycle.
7. Check whether email deliverability is set to "System Email Only" or "All Email" in the sandbox — most sandboxes should be on "System Email Only" to prevent test emails reaching real users.

---

## Mode 3: Troubleshoot Refresh Issues

Use this mode when a refresh has failed, the SandboxPostCopy class did not run, or the sandbox is in an unexpected state after refresh.

### SandboxPostCopy class did not execute

- Confirm the class name was entered correctly in the Apex Class field on the refresh form (case-sensitive).
- Confirm the class is global and implements `System.SandboxPostCopy` (not a custom interface with the same name).
- Confirm the class exists in production, not only in a sandbox.
- Check debug logs in the sandbox for errors thrown by the Automated Process user during post-copy execution. Enable logging for the Automated Process user before the next refresh.
- If the class throws an unhandled exception, Salesforce marks the post-copy script as failed but the sandbox itself is still usable. The error will appear in the sandbox's status details.

### Refresh is stuck or taking unexpectedly long

- Full sandbox refreshes can take 24–72 hours for large orgs. This is expected.
- Check Salesforce Trust (https://status.salesforce.com) for active incidents affecting sandbox operations.
- If stuck beyond expected duration, contact Salesforce Support — do not attempt to cancel and restart unless support advises it.

### Data from the template is not what was expected (Partial Copy)

- Re-examine the template definition. Related parent records pulled in for referential integrity may inflate counts.
- The template record count is a cap, not a guarantee — if the object has fewer records than the cap, all records are copied.
- Records are selected pseudo-randomly unless the object's ID ordering produces a deterministic set. Do not rely on specific records being in a Partial Copy sandbox.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to automate user passwords and org settings after refresh | Implement SandboxPostCopy class in production | Only supported automated hook for post-copy setup inside the sandbox |
| Need to control which records land in a Partial Copy sandbox | Define a sandbox template in production before refresh | Templates are the only supported mechanism for Partial Copy data scoping |
| Need specific records in a sandbox, not just a random subset | Use Developer sandbox + data loading scripts post-refresh | Partial Copy templates cannot filter by specific record criteria |
| Named Credentials must be reconfigured after every refresh | Document in manual runbook; consider SandboxPostCopy to set placeholder values | Named Credential secrets cannot be set via Apex — manual entry required |
| Scheduled jobs must not fire in sandbox | Abort all CronTrigger records in SandboxPostCopy class | Jobs are copied from production in an active state and will fire unless explicitly aborted |
| Org ID is stored in custom settings or code | Read new org ID from SandboxContext in SandboxPostCopy and update stored values | Org ID changes on every refresh — stale IDs cause downstream failures |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking a refresh cycle complete:

- [ ] Refresh interval has elapsed for the sandbox type (1 day / 5 days / 29 days)
- [ ] SandboxPostCopy class is registered on the sandbox record in production
- [ ] SandboxPostCopy class ran successfully — check debug logs for the Automated Process user in the sandbox
- [ ] All scheduled jobs have been aborted or confirmed as sandbox-safe
- [ ] Named Credentials have been reconfigured with sandbox-appropriate credentials
- [ ] Custom settings and custom metadata no longer contain the previous org ID
- [ ] Email deliverability is set to the appropriate level for this sandbox
- [ ] Sandbox template (Partial Copy only) includes the objects needed for current test scenarios
- [ ] External systems that integrate with the sandbox have been pointed at the new sandbox URL

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Org ID changes on every refresh** — The sandbox receives a new organization ID each time it is refreshed. Hardcoded org IDs in custom settings, custom metadata, Apex constants, or remote site settings will be stale immediately after refresh. Use `context.organizationId()` in SandboxPostCopy to update any stored values.

2. **Scheduled jobs are active in the sandbox immediately after refresh** — All CronTrigger records are copied from production with their `WAITING` state preserved. If those jobs make callouts or DML against production data endpoints, they will fire in the sandbox. Always abort or reschedule CronTrigger records in SandboxPostCopy.

3. **Named Credentials lose their secrets on refresh** — Named Credentials are copied to the sandbox but their passwords and OAuth tokens are blanked. Any integration that uses Named Credentials will fail silently until secrets are re-entered manually. There is no Apex API to set Named Credential secrets, so this step is always manual.

4. **SandboxPostCopy runs as Automated Process user, not an admin** — The Automated Process user does not have access to all objects. DML against certain objects will throw a permissions error. Assign a permission set to the Automated Process user before the refresh if the class needs access to custom objects, or use `System.runAs()` in test coverage.

5. **Partial Copy template record counts are not exact** — Salesforce follows parent lookups to maintain referential integrity, which can pull in significantly more records than the template cap specifies. Template counts are a request, not a hard limit.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Refresh readiness checklist | Pre-refresh and post-refresh checklist covering interval, template, SandboxPostCopy registration, and manual runbook steps |
| SandboxPostCopy Apex class | Global Apex class implementing the SandboxPostCopy interface, registered in production for automated post-refresh configuration |
| Sandbox template recommendation | List of objects and record count caps for a Partial Copy sandbox template aligned to the team's testing needs |
| Manual post-refresh runbook | Ordered list of manual steps for credentials, Named Credentials, and external system configuration that cannot be automated |

---

## Related Skills

- `admin/sandbox-strategy` — Use for choosing sandbox types, defining environment topology, and setting refresh ownership. This skill picks up where strategy leaves off.
