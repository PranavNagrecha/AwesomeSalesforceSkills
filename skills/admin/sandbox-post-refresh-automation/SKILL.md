---
name: sandbox-post-refresh-automation
description: "Automating post-sandbox-refresh cleanup via the `SandboxPostCopy` interface — the Apex class that runs ONCE after a sandbox refresh or clone completes, before users can log in. Used to mask emails, deactivate users, scrub integration endpoints, disable scheduled jobs, and reapply per-environment configuration the metadata copy doesn't carry. Covers the interface contract (`runApexClass` setting, `SandboxContext` parameter, single-execution semantics), the email-masking pattern that stops sandbox tests emailing production addresses, and the refresh runbook checklist. NOT for choosing sandbox type or refresh cadence — use admin/sandbox-strategy. NOT for re-seeding reference data after a refresh — use data/sandbox-refresh-data-strategies. Trigger keywords: SandboxPostCopy, runApexClass, SandboxContext, Test.testSandboxPostCopyScript, RunAsAutoProcUser, Automated Process user, CronTrigger, System.abortJob, sandbox email masking, post-refresh runbook."
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
  - "sandbox post copy apex class did not run"
  - "scheduled jobs fired in sandbox after refresh"
  - "mask user emails after sandbox refresh so tests do not email customers"
  - "sandboxpostcopy script fails with insufficient access"
  - "test sandbox post copy script runasautoprocuser overload"
  - "abort all scheduled jobs crontrigger after sandbox refresh"
  - "why did my sandbox send email to real customers"
  - "sandbox username has suffix but user email is still real"
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
  - "Machine-checkable post-refresh checklist JSON"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
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
`admin/sandbox-strategy`. Generic Apex scheduling is
`apex/apex-scheduled-jobs`. This skill is specifically about the
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

## Questions to Ask Before Configuring

Ask these before writing a line of the post-copy class. Each one maps to a documented platform behaviour
that will otherwise surface as a silent half-run, and an LLM that skips them produces a class that passes
its tests and fails the refresh.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which objects does the post-copy actually need to touch, and does the Automated Process user reach them?" | The script runs as a restricted, org-invisible user with no access to all objects and features (`references/gotchas.md` § 10) | The list of steps that must move to the post-activation re-run instead of the refresh-time hook |
| "Which scheduled jobs mutate something outside this org?" | Abort-everything breaks sandbox testing; abort-nothing lets a prod-pointing batch fire (`references/gotchas.md` § 3, § 14) | The named allow-list, and the ordering: scrub endpoints *before* aborting jobs |
| "Is the class already in production, and which sandbox is it bound to?" | The sandbox copies Apex from the source org, and each sandbox names its own class (`references/gotchas.md` § 7) | A deploy-to-prod step that precedes the first refresh, plus the per-sandbox binding list |
| "How many active users does the source org have?" | Masking is a single synchronous DML inside the post-copy transaction; row counts decide sync vs Batch (`references/well-architected.md`) | A choice between the inline loop and a Queueable, made on a number rather than a hunch |
| "Who owns the deliverability Access Level, and when do they set it?" | It has no Metadata API surface, so it cannot ride along in the deploy (`references/gotchas.md` § 5) | A named human and a slot in the runbook, instead of a step everyone assumes is automated |
| "What is the re-run procedure when the script fails mid-way?" | The hook runs once; the sandbox unlocks regardless, and the guide names post-activation re-run as the recovery (`references/gotchas.md` § 2, § 9) | An idempotency requirement on every step, and a documented anonymous-Apex path |
| "Which fields carry customer-identifying data besides `Email`?" | The copy rewrites `Username` automatically and nothing else (`references/gotchas.md` § 11) | The real masking scope — phone, external ids — rather than email alone |

What a proper configuration adds over just writing the class: the refresh produces a sandbox where the
scheduled-job count is provably zero, no active user holds a routable address, and every step that could
not be automated has a named owner in a checklist a script can verify.

---

## Core Concepts

### The `SandboxPostCopy` interface

```apex
global class MySandboxPrep implements SandboxPostCopy {

    // Required. The copy process instantiates the class with this.
    global MySandboxPrep() {}

    global void runApexClass(SandboxContext context) {
        // Runs once, after sandbox refresh, before users log in.
        // Guard each step separately — see point 3.
        maskEmails();
        deactivateProdOnlyUsers();
        scrubIntegrationEndpoints();   // before the abort, not after
        disableScheduledJobs();
        repopulateSampleData();
        applyEnvironmentConfig();
    }
}
```

The full, deployable version — with per-step try/catch, the idempotent mask predicate and the six-state
abort query — is in `references/metadata-examples.md` § 1.

Four things to know:

1. **A no-arg constructor is mandatory.** The guide's own sample carries the comment: "Implementations
   of SandboxPostCopy must have a no-arg constructor. This constructor is used during the sandbox copy
   process" (Apex Reference Guide L228955–228956). Constructors with arguments are allowed but "won't be
   used by the sandbox copy process" (L228958–228960) — a class whose only constructor takes arguments
   cannot be instantiated by the copy.
2. **Write both the class and `runApexClass` `global`.** Every Salesforce sample does (L228952, L228975).
   UNVERIFIED (2026-09-05): the guide never states that a `public` implementation is rejected, and its
   member-signature line reads `public void runApexClass(System.SandboxContext context)` (L228926) — see
   `references/gotchas.md` § 1 for why this skill still recommends `global`.
3. **It runs as a restricted Automated Process user.** "This user doesn't have access to all object and
   features; therefore, the Apex script cannot access all objects and features. If the script fails, run
   the script after sandbox activation as a user with appropriate permissions" (L228889–228891). This is
   the single most common cause of a post-copy that works in test and fails in the refresh.
4. **`SandboxContext` exposes** `organizationId()`, `sandboxId()`, `sandboxName()` (L228933–228935). Use
   these for environment-aware logic, but keep the safety steps outside the branch.

### What runs vs what doesn't get copied

The metadata + data copy doesn't include:

- **Login Hours / Login IP Ranges** on profiles (security
  intentional).
- **Outbound message workflow targets** (always reset to a "do
  not deliver" placeholder by Salesforce — but verify in your
  org).
- **Scheduled jobs** — they DO copy, which is usually the wrong
  outcome. Sandbox post-copy disables them. UNVERIFIED (2026-09-05):
  the copy behaviour is Help-documented only; the abort mechanism
  below is fully grounded. See `references/gotchas.md` § 3.
- **Single-sign-on certificates** for some IdP integrations.

What the copy rewrites for you, and what it leaves alone:

- **`Username` is mutated automatically.** "In a sandbox named `test`, the username `user@acme.com`
  becomes `user@acme.com.test`" (Metadata API Developer Guide L2711–2713).
- **`Email` is not.** It arrives verbatim, routable, pointing at a real person. That asymmetry is the
  whole reason the masking step below exists — see `references/gotchas.md` § 11.

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

**Mitigation A: Org-wide deliverability restriction.** Setup → Email → Deliverability → Access Level.
Set at the org level, by hand. UNVERIFIED (2026-09-05): this control has **no** `EmailAdministrationSettings`
field — that type's complete list is 19 booleans, none an access-level enum (api_meta L114872–114994) —
so it cannot be deployed and cannot be set from the post-copy class. Track it as a `manual` step with a
named owner; see `references/metadata-examples.md` § 6 for what *is* deployable, and § 7 for the checklist
shape that stops a manual step masquerading as an automated one.

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

The `+sandbox@` tag preserves the original local-part for forensic debugging, and the
`NOT Email LIKE '%.invalid'` predicate (see `references/examples.md` Example 2) makes the step idempotent.
UNVERIFIED (2026-09-05): the claim that `.invalid` is IETF-reserved for non-routable use is general
internet knowledge, not sourced in any Salesforce guide checked for this skill. Nothing in the platform
enforces it — a mail server that chooses to route `.invalid` will. Masking is a strong control, not a
guarantee; pair it with mitigation A.

### Disabling scheduled jobs

```apex
private static void disableScheduledJobs() {
    for (CronTrigger ct : [
        SELECT Id FROM CronTrigger
        WHERE State IN ('WAITING', 'ACQUIRED', 'EXECUTING',
                        'PAUSED', 'BLOCKED', 'PAUSED_BLOCKED')
    ]) {
        try {
            System.abortJob(ct.Id);
        } catch (Exception ex) {
            System.debug(LoggingLevel.ERROR, 'abortJob failed: ' + ex.getMessage());
        }
    }
}
```

**Six states, not three.** `CronTrigger.State` has nine documented values; only `COMPLETE`, `ERROR` and
`DELETED` are terminal (Object Reference L86799–86811). A three-state filter leaves `BLOCKED` and
`PAUSED_BLOCKED` jobs alive, and `PAUSED` returns to `WAITING` by itself once a release window closes.
Full table in `references/metadata-examples.md` § 4.

**`abortJob` is not a kill.** "The specified job is stopped, but any code that is in progress will
continue to execute until it completes" (Apex Reference Guide L238662–238663). Scrub endpoints *before*
aborting so an in-flight run lands on mocks. And it needs the `CronTrigger` Id: "You can't abort a
scheduled Apex job using an AsyncApexJob ID" (L238678–238680). `CronTrigger` itself takes no DML —
supported calls are `describeSObjects()`, `query()`, `retrieve()` only (L86722).

A safer variant aborts only jobs whose name matches a documented list of "production-only" jobs;
over-aggressive abort can break sandbox tests.

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
| Step needs an object the copy user may not reach | Move it to the post-activation re-run, not the hook | Automated Process user has partial access (L228889–228891) |
| Writing the test class | 5-arg `Test.testSandboxPostCopyScript(..., true)` | 4-arg form runs as test initiator, hides the access failure (L241180–241184) |
| Deciding which jobs to abort | Query the six live `CronTrigger` states first, then allow-list | `BLOCKED` / `PAUSED_BLOCKED` are live and usually missed (L86799–86811) |
| Ordering scrub vs abort | Scrub endpoints, then abort jobs | `abortJob` lets in-flight code finish (L238662–238663) |
| More active users than one sync DML can carry | Post-copy enqueues a Queueable that masks in chunks | Post-copy shares one synchronous transaction |

---

## Recommended Workflow

1. **Inventory what is still live, from the source org.** Run the `CronTrigger` query in
   `references/metadata-examples.md` § 4 — all six live states, with `CronJobDetail.JobType` so you can
   see the Scheduled Flows an Apex-only sweep would miss. Answer the seven questions above against that
   list. Fill `templates/sandbox-post-refresh-automation-template.md`.
2. **Write `config/sandbox/post-refresh-checklist.json` first**, from `references/metadata-examples.md`
   § 7. Every step gets an `owner` (`apex` / `pipeline` / `manual`) and a `verify` query. The steps you
   mark `manual` — the deliverability Access Level among them — are the ones this skill cannot automate,
   and naming them now is the point of doing this before the Apex.
3. **Build the class and its test from `references/metadata-examples.md` § 1 and § 2.** No-arg
   constructor, per-step try/catch, idempotent mask predicate, six-state abort, scrub before abort. The
   test uses the 5-arg `Test.testSandboxPostCopyScript(..., true)` overload and asserts on state queried
   back, not on a return value.
4. **Run the checker** — it reads the checklist JSON, the Apex, and the settings file together:
   `python3 scripts/check_sandbox_post_refresh_automation.py --manifest-dir force-app/main/default`.
   Fix every finding before you deploy; each maps to a numbered gotcha.
5. **Validate then deploy to PRODUCTION** with `RunSpecifiedTests` on the post-copy test class
   (`references/metadata-examples.md` § 8). The sandbox copies Apex from the source org, so a class that
   only ever lived in a sandbox is gone after the next refresh.
6. **Bind the class to each sandbox** (`references/metadata-examples.md` § 3), then refresh the
   lowest-tier sandbox first and run the three verification queries from § 8 — zero live `CronTrigger`
   rows, zero unmasked active users, `IsSandbox = true`.
7. **Work the `manual` rows of the checklist**, deploy `EmailAdministration.settings` to the activated
   sandbox, and record which steps needed the post-activation re-run. Those are your Automated
   Process user access gaps; move them permanently into the pipeline half.

---

## Review Checklist

- [ ] Class implements `SandboxPostCopy` with `global` access **and a no-arg constructor**.
- [ ] `runApexClass` covers email masking, user deactivation, endpoint scrub, scheduled-job disable, sample data, env config — each in its own try/catch.
- [ ] Endpoint scrub runs **before** the job abort.
- [ ] The abort query covers all six live `CronTrigger` states, not three.
- [ ] Every step is idempotent (safe to re-run).
- [ ] The test class uses the 5-arg `testSandboxPostCopyScript` with `RunAsAutoProcUser = true`.
- [ ] `SandboxContext` is consulted when behavior should differ per environment, and the safety steps sit outside the branch.
- [ ] Class is deployed to production and bound to every sandbox.
- [ ] Checklist JSON exists, every step has an `owner` and a `verify`, and the checker passes.
- [ ] Deliverability Access Level is recorded as a `manual` step with a named owner.
- [ ] Failed-run procedure is documented (how to re-run after activation, as a permissioned user).

---

## Salesforce-Specific Gotchas

1. **`SandboxPostCopy` requires `global` access modifier.** `public` doesn't satisfy the interface contract. (See `references/gotchas.md` § 1.)
2. **`runApexClass` runs ONCE per refresh.** Mid-execution failure leaves the sandbox half-prepared; design for re-runnability. (See `references/gotchas.md` § 2.)
3. **Scheduled jobs DO copy** from prod to sandbox; they fire in the sandbox unless explicitly aborted in post-copy. (See `references/gotchas.md` § 3.)
4. **Named Credential URLs are not Apex-mutable.** Pre-deploy sandbox-pointing NC metadata or accept a stale URL. (See `references/gotchas.md` § 4.)
5. **Email deliverability resets to "System emails only"** on Salesforce's side after refresh — but verify; not all orgs / tiers behave identically. (See `references/gotchas.md` § 5.)
6. **`SandboxContext.sandboxName()` is the developer-given name**, not a hash; rely on it cautiously for branching. (See `references/gotchas.md` § 6.)
7. **The post-copy class must be already deployed in production** before refresh; the sandbox copies the class FROM production. (See `references/gotchas.md` § 7.)
8. **The script runs as a restricted Automated Process user** that isn't visible in the org and can't reach every object or feature. (See `references/gotchas.md` § 10.)
9. **The copy rewrites `Username` automatically; `Email` it leaves routable.** Derive masked addresses from `Email`, never from `Username`. (See `references/gotchas.md` § 11.)
10. **Implementations need a no-arg constructor** — an args-only constructor can't be used by the copy process. (See `references/metadata-examples.md` § 1.)
11. **The 4-arg `testSandboxPostCopyScript` runs as the test initiator**, so it can't reproduce the access failure that most often breaks a real refresh. (See `references/gotchas.md` § 13.)
12. **Three `CronTrigger` states aren't enough** — `PAUSED`, `BLOCKED` and `PAUSED_BLOCKED` are live too. (See `references/gotchas.md` § 12.)
13. **`abortJob` lets in-flight code finish** and needs the `CronTrigger` Id, not an `AsyncApexJob` Id. (See `references/gotchas.md` § 14.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `SandboxPostCopy` Apex class | The post-copy automation, one method per concern |
| Test class | Asserts each method's effects (mask, deactivate, scrub) |
| Sandbox configuration documentation | Which class is configured on which sandbox tier |
| Manual override runbook | How to re-run the class if it fails mid-execution, post-activation, as a permissioned user |
| `config/sandbox/post-refresh-checklist.json` | Machine-checkable step list — `owner` and `verify` per step; read by `scripts/check_sandbox_post_refresh_automation.py` |
| `EmailAdministration.settings-meta.xml` | The email-admin fields that are actually deployable to the refreshed sandbox |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing the actual artefacts: the `SandboxPostCopy` class with its no-arg constructor, the 5-arg test, the Tooling API `SandboxInfo` binding, the six-state `CronTrigger` inventory, the Data Loader masking fallback, the deployable `EmailAdministration.settings` elements, the checklist JSON, package.xml and the three verification queries |
| `references/gotchas.md` | A refresh half-ran, a job survived the abort, or a test passes and the refresh does not — 15 platform behaviours with guide line citations, and the UNVERIFIED markers on everything Help-only |
| `references/examples.md` | You want a worked scenario end to end: the email escape, the idempotent re-run, per-environment branching, the Custom Setting scrub, and the test-class shape |
| `references/well-architected.md` | You are justifying the design in a review — pillar mapping, the sync-vs-Queueable and Apex-vs-pipeline tradeoffs, and the sources this package rests on |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated post-copy advice or code and need the specific failure modes to check for |
| `templates/sandbox-post-refresh-automation-template.md` | Running workflow step 1 — the inventory and the questions, in one place |
| `scripts/check_sandbox_post_refresh_automation.py` | Workflow step 4, and in CI on every PR that touches the post-copy class or the checklist |

---

## Related Skills

- `admin/sandbox-strategy` — strategic decision (how many sandboxes, what tiers, refresh cadence). This skill is the implementation half.
- `apex/apex-scheduled-jobs` — generic scheduled / batch Apex; sandbox-post-copy is a specific runtime, and this is where the jobs you abort come from.
- `admin/email-deliverability-strategy` — the org-wide deliverability controls this skill can only mark as a manual step.
- `admin/email-templates-and-alerts` — email infrastructure; post-copy interacts with deliverability config.
- `apex/apex-mocking-and-stubs` — for the test class that exercises the post-copy methods.
- `data/sandbox-refresh-data-strategies` — re-seeding reference data after the copy, which this skill deliberately stubs out.
- `security/sandbox-data-masking` — masking beyond `User.Email`: the wider set of customer-identifying fields.
