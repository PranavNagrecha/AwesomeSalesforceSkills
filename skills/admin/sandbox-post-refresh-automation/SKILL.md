---
name: sandbox-post-refresh-automation
description: "Automating the post-sandbox-refresh cleanup via the `SandboxPostCopy` interface — the Apex class that runs ONCE after a sandbox refresh / clone completes, before users can log in. Used to mask emails, deactivate users, scrub integration endpoints, disable scheduled jobs, repopulate sample data, and reapply any per-environment configuration that the metadata copy doesn't carry. Covers the interface contract (`runApexClass` setting, `SandboxContext` parameter, single-execution semantics), the email-masking pattern that prevents production emails firing from sandbox tests, and the runbook checklist of what every refresh should reset. NOT for the sandbox refresh-strategy decision (use devops/sandbox-strategy-designer), NOT for general bulk Apex (use apex/scheduled-apex)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "sandbox post copy apex class refresh automation"
  - "sandboxpostcopy interface implement runapexclass"
  - "sandbox refresh email mask deactivate user"
  - "post refresh disable scheduled job integration endpoint"
  - "sandbox clone apply config that metadata didn't copy"
  - "sandbox refresh runbook automation checklist"
tags:
  - sandbox
  - sandboxpostcopy
  - refresh-automation
  - email-masking
  - integration-endpoint-scrub
inputs:
  - "Refresh source: production → full sandbox / partial / dev / dev-pro"
  - "What user-data masking is required (emails, names, SSNs)"
  - "Which integrations point at production endpoints that must be scrubbed"
  - "Which scheduled jobs / queueables / batch jobs must be disabled"
  - "What sample data needs to be (re)inserted"
outputs:
  - "Apex class implementing SandboxPostCopy with runApexClass logic"
  - "Configuration on the sandbox: Setup → Sandboxes → Apex Class to run"
  - "Documentation of what the post-copy script does (audit trail)"
  - "Test plan that confirms refresh-time execution"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Sandbox Post-Refresh Automation

When a sandbox is refreshed (full, partial, dev, dev-pro), the
metadata + data are copied from the source. Users are then locked
out for a final preparation step before the sandbox becomes
available. The `SandboxPostCopy` interface is Salesforce's hook
into that step: an Apex class you specify in the sandbox refresh
configuration runs ONCE, before users can log in.

It's the right place to:

- **Mask emails** so test sends don't fire to real customers.
- **Deactivate users** who shouldn't have sandbox access.
- **Scrub integration endpoints** that point at production
  systems.
- **Disable scheduled jobs** that would race with prod
  (replicator, escalator, etc.).
- **Repopulate test data** that doesn't survive the copy (or
  shouldn't — auth tokens, caches, etc.).
- **Reapply environment-specific config** (named credentials,
  Custom Setting values keyed to environment, feature flags).

Without it, every refresh is a manual cleanup checklist that
inevitably gets forgotten on one of the steps. The most common
forgotten-step disaster: prod-pointing integration endpoints stay
configured; a developer in the sandbox triggers the integration;
production data changes.

What this skill is NOT. The strategic question of how many
sandboxes / which tier / refresh cadence lives in
`devops/sandbox-strategy-designer`. Generic Apex scheduling is
`apex/scheduled-apex`. This skill is specifically about the
post-refresh hook and what it should do.

---

## Before Starting

- **Confirm the sandbox tier matters.** All tiers support
  SandboxPostCopy. Some org features (e.g. partial-data sandbox
  data sampling) interact with the post-copy step.
- **Decide which actions are non-negotiable.** Email masking is
  always non-negotiable. Endpoint scrub is non-negotiable for orgs
  with prod-pointing integrations. Scheduled-job disable is
  non-negotiable if any scheduled job mutates external state.
- **Document the runbook explicitly.** The post-copy class IS the
  runbook; it's executable documentation. Future you reads it.
- **Plan idempotency.** The class runs once per refresh; failure
  during the run can leave the sandbox half-prepared. Build the
  class to be safe to re-run if needed.

---

## Core Concepts

### The `SandboxPostCopy` interface

```apex
global class MySandboxPrep implements SandboxPostCopy {
    global void runApexClass(SandboxContext context) {
        // Runs once, after sandbox refresh, before users log in.
        maskEmails();
        deactivateProdOnlyUsers();
        scrubIntegrationEndpoints();
        disableScheduledJobs();
        repopulateSampleData();
        applyEnvironmentConfig();
    }
}
```

Three things to know:

1. **`global` is required.** Internal `public` won't satisfy the
   interface contract.
2. **`SandboxContext` exposes** `sandboxName()`, `sandboxId()`,
   and `organizationId()`. Use these for environment-aware
   logic ("if dev sandbox, do X; if full sandbox, do Y").
3. **Configured at refresh time.** Setup → Sandboxes → click the
   sandbox → Apex Class field. Specify the class name. Saved with
   the sandbox; persists across refreshes.

### What runs vs what doesn't get copied

The metadata + data copy doesn't include:

- **Login Hours / Login IP Ranges** on profiles (security
  intentional).
- **Outbound message workflow targets** (always reset to a "do
  not deliver" placeholder by Salesforce — but verify in your
  org).
- **Scheduled jobs** — they DO copy, which is usually the wrong
  outcome. Sandbox post-copy disables them.
- **Single-sign-on certificates** for some IdP integrations.

What DOES copy and is dangerous in sandbox:

- **Named Credentials** — point at prod by default unless the
  named credential was already environment-aware.
- **Connected App configurations** — OAuth callback URLs are
  prod-shaped.
- **Custom Setting values** — usually carry prod values; rewrite
  in post-copy.
- **Workflow + Apex outbound emails** — if email deliverability
  is "All emails", the sandbox can fire emails to real customers
  unless masked.

### Email masking patterns

**Hardest constraint.** A refreshed sandbox with no email mask +
deliverability = "All emails" + a developer running a test = real
customers receive sandbox-generated emails.

**Mitigation A: Org-wide deliverability "System emails only".**
Setup → Email → Deliverability → Access Level → System emails
only. Done at the org level; survives across refreshes if set on
the sandbox post-copy. Belt-and-suspenders with email masking.

**Mitigation B: Mask user emails.**

```apex
private static void maskEmails() {
    List<User> toUpdate = new List<User>();
    for (User u : [SELECT Id, Email FROM User WHERE Email != NULL AND IsActive = TRUE]) {
        // Replace @ with .invalid + a tag — emails won't deliver, but
        // can be reverse-engineered for debugging.
        u.Email = u.Email.replace('@', '+sandbox@') + '.invalid';
        toUpdate.add(u);
    }
    update toUpdate;
}
```

The `.invalid` TLD is reserved by IETF for non-routable use —
mail servers reject delivery. The `+sandbox@` tag preserves the
original local-part for forensic debugging.

### Disabling scheduled jobs

```apex
private static void disableScheduledJobs() {
    for (CronTrigger ct : [
        SELECT Id FROM CronTrigger
        WHERE State IN ('WAITING', 'ACQUIRED', 'EXECUTING')
    ]) {
        try {
            System.abortJob(ct.Id);
        } catch (Exception ex) {
            // Some jobs can't be aborted (in-flight); log and continue.
        }
    }
}
```

Aborts every scheduled / queued job. A safer variant only aborts
jobs whose name matches a documented list of "production-only"
jobs; over-aggressive abort can break sandbox tests.

### Scrubbing integration endpoints

Named Credentials, Custom Settings, Custom Metadata Types — all
copy from production with prod values. Post-copy, rewrite to
sandbox / mock endpoints:

```apex
private static void scrubIntegrationEndpoints() {
    // Named Credentials are not directly Apex-mutable for endpoint URL;
    // typically scrubbed via metadata deploy in the sandbox setup script.
    // Custom Setting / Custom Metadata are mutable.
    Integration_Config__c cfg = Integration_Config__c.getOrgDefaults();
    cfg.Endpoint__c = 'https://mock.example-sandbox.com/api';
    cfg.API_Key__c = 'SANDBOX-MOCK-KEY';
    update cfg;
}
```

For Named Credentials, the sandbox-prep team usually pre-deploys
sandbox-pointing Named Credential metadata as part of the
post-copy + a metadata deploy step.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| New sandbox tier added | Implement `SandboxPostCopy` from scratch | Standard pattern |
| Existing sandbox with manual cleanup checklist | Codify the checklist in post-copy | Manual is forgotten one step at a time |
| Multi-environment Custom Setting values | Custom Setting + post-copy assignment | Centralized; deterministic |
| Prod-pointing Named Credentials | Pre-deploy sandbox NC metadata + post-copy callout (or just rely on deploy) | NC URL not Apex-mutable directly |
| Email deliverability concerns | **System emails only** + email masking (both) | Belt-and-suspenders |
| Scheduled jobs that mutate external state | `System.abortJob` in post-copy | Critical safety mechanism |
| Sandbox-specific feature flags | Custom Metadata + post-copy update | Survives across refreshes |
| Different post-copy for dev vs full sandbox | Use `SandboxContext.sandboxName()` to branch | Environment-aware behavior |
| Failed post-copy run mid-execution | Make every step idempotent; document re-run procedure | Failures happen; design for them |

---

## Recommended Workflow

1. **Inventory the manual post-refresh checklist.** Email masking, user deactivation, endpoint scrub, scheduled-job disable, sample data, env config.
2. **Build the `SandboxPostCopy` class** — one private method per checklist item.
3. **Make every method idempotent.** Re-running shouldn't break anything.
4. **Configure on every sandbox.** Setup → Sandboxes → Apex Class field.
5. **Test by refreshing a low-tier sandbox first.** Verify each method ran (audit log, masked emails, disabled jobs).
6. **Document the class in source control.** It's runbook-as-code.
7. **Keep `Sandbox` org-wide deliverability at "System emails only"** as a belt-and-suspenders default.

---

## Review Checklist

- [ ] Class implements `SandboxPostCopy` with `global` access.
- [ ] `runApexClass` covers email masking, user deactivation, endpoint scrub, scheduled-job disable, sample data, env config.
- [ ] Every step is idempotent (safe to re-run).
- [ ] `SandboxContext` is consulted when behavior should differ per environment.
- [ ] Class name is configured in Setup → Sandboxes for every sandbox.
- [ ] Org-wide deliverability is "System emails only" as a default.
- [ ] Failed-run procedure is documented (how to re-run).

---

## Salesforce-Specific Gotchas

1. **`SandboxPostCopy` requires `global` access modifier.** `public` doesn't satisfy the interface contract. (See `references/gotchas.md` § 1.)
2. **`runApexClass` runs ONCE per refresh.** Mid-execution failure leaves the sandbox half-prepared; design for re-runnability. (See `references/gotchas.md` § 2.)
3. **Scheduled jobs DO copy** from prod to sandbox; they fire in the sandbox unless explicitly aborted in post-copy. (See `references/gotchas.md` § 3.)
4. **Named Credential URLs are not Apex-mutable.** Pre-deploy sandbox-pointing NC metadata or accept a stale URL. (See `references/gotchas.md` § 4.)
5. **Email deliverability resets to "System emails only"** on Salesforce's side after refresh — but verify; not all orgs / tiers behave identically. (See `references/gotchas.md` § 5.)
6. **`SandboxContext.sandboxName()` is the developer-given name**, not a hash; rely on it cautiously for branching. (See `references/gotchas.md` § 6.)
7. **The post-copy class must be already deployed in production** before refresh; the sandbox copies the class FROM production. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `SandboxPostCopy` Apex class | The post-copy automation, one method per concern |
| Test class | Asserts each method's effects (mask, deactivate, scrub) |
| Sandbox configuration documentation | Which class is configured on which sandbox tier |
| Manual override runbook | How to re-run the class if it fails mid-execution |

---

## Related Skills

- `devops/sandbox-strategy-designer` — strategic decision (how many sandboxes, what tiers, refresh cadence). This skill is the implementation half.
- `apex/scheduled-apex` — generic scheduled / batch Apex; sandbox-post-copy is a specific runtime.
- `admin/email-templates-and-alerts` — email infrastructure; post-copy interacts with deliverability config.
- `apex/apex-mocking-and-stubs` — for the test class that exercises the post-copy methods.
