---
name: sandbox-refresh-and-templates
description: "Sandbox refresh cycles, sandbox templates, post-refresh automation via the SandboxPostCopy Apex interface, and data handling during refresh. NOT for sandbox type selection — use admin/sandbox-strategy."
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
  - "my sandbox data is stale and I need to bring it back in line with production"
  - "how do I automate user setup and org settings after a sandbox refresh"
  - "my SandboxPostCopy class is not running after the sandbox is refreshed"
  - "what data gets copied into a Partial Copy sandbox and how do I control it"
  - "integrations are broken in the sandbox after refresh and Named Credentials are missing"
  - "sandbox refresh SandboxPostCopy automation"
  - "sandbox refresh isn't working"
  - "refresh a sandbox from the CLI with a definition file and a post-copy class"
  - "reschedule Apex jobs after a sandbox refresh"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Sandbox Refresh and Templates

This skill activates when a practitioner needs to run, plan, or troubleshoot a sandbox refresh — configuring sandbox templates, automating post-refresh setup with the `SandboxPostCopy` Apex interface, and handling data and integrations safely afterwards. It does not cover choosing which sandbox type to use (see `admin/sandbox-strategy`).

---

## Before Starting

- Know the sandbox type: Developer and Developer Pro sandboxes get metadata only; Partial Copy and Full also get data.
- Find the `SandboxPostCopy` class, if any (search for `implements SandboxPostCopy`), and which sandboxes name it.
- List the scheduled Apex jobs the sandbox needs — they are not copied on refresh.
- List integrations, Named Credentials, and External Credentials that point at external systems.
- Search code, custom settings, and custom metadata for stored org IDs and production URLs.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which scheduled jobs must run in this sandbox after refresh? | Scheduled jobs from the source org aren't copied on refresh; they must be rescheduled (gotcha 2). | A reschedule list the post-copy class or runbook executes. |
| What must the post-copy class do, and does the Automated Process user have access to those objects? | The class runs as an Automated Process user that can't access all objects and features (gotcha 4). | A scoped task list, a test that runs as that user, and a manual fallback. |
| Is this a Partial Copy sandbox, and which template does it use? | `templateId` is required for Partial sandboxes, optional for Full, and not available for Developer or Developer Pro (gotcha 5). | A named template with the objects the tests need. |
| Does any data copied into the sandbox contain personal data? | Partial Copy and Full sandboxes receive production data (gotcha 6). | A masking step in the post-copy class (or a dedicated masking product) before users get access. |
| Which external endpoints and credentials does the sandbox call? | Copied configuration points at production systems until it is changed (gotcha 3). | Endpoint and credential changes owned by the post-copy class or a runbook line. |
| Where are org IDs or production URLs stored as values? | A sandbox is its own org; values copied from production are wrong there (gotcha 1). | Code that reads the org ID at runtime instead of storing it. |
| Who refreshes, how, and when is the next window? | Options such as the template are chosen per refresh, and a CLI refresh can change them through a definition file; refresh intervals limit how often you can retry (gotcha 7). | A refresh owner, a definition file in source control, and a calendar. |

A proper refresh setup adds a tested post-copy class, a template that matches the tests, and a short manual runbook, where "just clicking Refresh" produces a sandbox with no scheduled jobs, production endpoints, and unmasked customer data.

---

## Core Concepts

### What a refresh copies

| Sandbox type | Copied from source | Template |
|---|---|---|
| Developer | Metadata | Not available |
| Developer Pro | Metadata | Not available |
| Partial Copy | Metadata + data for the objects the template selects | Required (`templateId`) |
| Full | Metadata + data | Optional (`templateId`) |

Refreshing updates a sandbox's metadata from the source org; if the sandbox is a clone or uses a template, the refresh also updates its data. A sandbox template lets you select which objects to copy. Scheduled jobs are not copied.

Refresh intervals: Developer and Developer Pro 1 day, Partial Copy 5 days, Full 29 days. UNVERIFIED (2026-10-19): these intervals are published in Salesforce Help ("Sandbox Licenses and Storage Limits by Type"), which does not fetch; confirm in Setup > Sandboxes before planning a calendar around them.

### The SandboxPostCopy interface

`System.SandboxPostCopy` has one method, `runApexClass(System.SandboxContext context)`; the context gives `context.organizationId()`, `context.sandboxId()`, and `context.sandboxName()`. You specify the class when creating or refreshing the sandbox (Setup's Apex Class field, or `apexClassName` / `apexClassId` in a CLI sandbox definition file). The class needs a no-arg constructor, because that is the constructor the copy process uses. It runs at the end of the copy as a special Automated Process user that isn't visible in the org and doesn't have access to all objects and features; if the script fails, run it after activation as a user with the right permissions.

```apex
global class SandboxSetup implements SandboxPostCopy {
    global SandboxSetup() {}   // the copy process uses the no-arg constructor

    global void runApexClass(SandboxContext context) {
        Sandbox_Config__c cfg = Sandbox_Config__c.getOrgDefaults();
        cfg.Environment_Name__c = context.sandboxName();
        cfg.Endpoint_Base_URL__c = 'https://sandbox-api.example.com';
        upsert cfg;

        // Scheduled jobs are not copied on refresh: schedule the ones this sandbox needs.
        System.schedule('Nightly sync (sandbox)', '0 0 2 * * ?', new NightlySyncSchedulable());
    }
}
```

Test it with `Test.testSandboxPostCopyScript(script, orgId, sandboxId, sandboxName, true)` — the overload whose last argument runs the test with the Automated Process user's permissions, which Salesforce recommends over the four-argument version.

### Refreshing from the CLI

```json
{
  "sandboxName": "uat",
  "licenseType": "Partial",
  "templateId": "1psXXXXXXXXXXXX",
  "apexClassName": "SandboxSetup",
  "autoActivate": true
}
```

`sf org refresh sandbox --name uat --target-org prodOrg --definition-file config/uat-sandbox-def.json` refreshes with that configuration; `--name` is the sandbox name, not its alias, and the name itself can't change on refresh. `sandboxName` is alphanumeric, 10 characters or fewer.

---

## Recommended Workflow

1. Answer the Questions table; record the refresh owner, sandbox type, template, and post-copy class in `templates/sandbox-refresh-and-templates-template.md`.
2. Write or update the `SandboxPostCopy` class in production with a no-arg constructor, job scheduling, endpoint changes, and masking; cover it with a `Test.testSandboxPostCopyScript(..., true)` test.
3. Keep the sandbox definition file in `config/` and run `python3 skills/devops/sandbox-refresh-and-templates/scripts/check_sandbox_refresh.py --manifest-dir .` — it ERRORs on a Partial definition without `templateId`, a template on Developer types, a post-copy class with no no-arg constructor, and conflicting definition options.
4. Refresh (Setup or `sf org refresh sandbox --definition-file ...`), then confirm the post-copy work landed: config values, scheduled jobs in `CronTrigger`, masked fields.
5. Run the manual runbook for what the class could not do (credentials, external system callbacks, email deliverability), and re-run the class as an admin if it failed.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Repeatable setup after every refresh | `SandboxPostCopy` class named on the sandbox | Runs automatically at the end of the copy |
| Control which objects land in Partial Copy | Sandbox template (`templateId`) | Required for Partial sandboxes; selects objects |
| Need specific records, not a sample | Developer sandbox + scripted data load | A template selects objects, not individual records |
| Jobs needed in the sandbox | `System.schedule` in the post-copy class or a runbook step | Scheduled jobs aren't copied on refresh |
| Credentials for sandbox endpoints | Sandbox-specific Named/External Credentials; `ConnectApi.NamedCredentials.createCredential` where the running user has access | Production credentials should not be reused |
| Org ID needed by code | `UserInfo.getOrganizationId()` at runtime | Stored IDs copied from production are wrong in the sandbox |

---

## Review Checklist

- [ ] The post-copy class has a no-arg constructor, implements `SandboxPostCopy`, and is named on the sandbox
- [ ] A test calls `Test.testSandboxPostCopyScript(..., true)` and asserts the post-copy results
- [ ] Every scheduled job the sandbox needs is rescheduled after refresh
- [ ] Partial Copy sandboxes have a `templateId`; Developer types have none
- [ ] Personal data is masked before users are given access
- [ ] Endpoints and credentials point at sandbox systems
- [ ] No org ID or production URL is stored as a literal
- [ ] The checker exits 0 on the project

---

## Salesforce-Specific Gotchas

Full list in `references/gotchas.md`. The two that surprise teams most:

1. **Scheduled jobs are not copied** — the sandbox starts with none of production's scheduled Apex.
2. **The post-copy user is limited** — the Automated Process user can't reach every object; plan a manual re-run.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Refresh readiness checklist | Interval, template, post-copy class, owner |
| `SandboxPostCopy` class + test | Scheduling, endpoints, masking; tested as the Automated Process user |
| Sandbox definition file | `config/<name>-sandbox-def.json` with `templateId` and `apexClassName` |
| Manual post-refresh runbook | Credentials, external callbacks, email deliverability |

---

## Reference Files

| File | Use it for |
|---|---|
| `references/examples.md` | Post-copy class, Partial Copy template design, PII masking |
| `references/gotchas.md` | Seven refresh behaviours with avoidance steps |
| `references/llm-anti-patterns.md` | Refresh advice AI assistants get wrong |
| `references/well-architected.md` | Pillar framing and the guide lines behind each claim |
| `references/cli-refresh-runbook.md` | CLI create/refresh with definition files and a post-refresh verification query set |

---

## Related Skills

- `admin/sandbox-strategy` — choosing sandbox types, environment topology, and refresh ownership. This skill picks up where strategy leaves off.
