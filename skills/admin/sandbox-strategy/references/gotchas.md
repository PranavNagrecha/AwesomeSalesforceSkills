# Gotchas: Sandbox Strategy

---

## Refreshing Over Active Work

**What happens:** A sandbox is refreshed while admins or developers still have uncommitted work. Metadata and test data disappear, and everyone blames Salesforce.

**When it occurs:** Shared admin sandboxes, rushed UAT windows, and teams without source discipline.

**How to avoid:** Require changes to be committed or backed up before refresh approval, and publish refresh windows in advance.

---

## Treating Partial Copy Like a Production Clone

**What happens:** Teams assume a Partial Copy gives reliable production realism for every test scenario. It does not.

**When it occurs:** Performance tests, complex edge-case UAT, and data-volume validation.

**How to avoid:** Use Partial Copy for sampled realism and reserve Full Sandbox for true production rehearsal.

---

## Forgetting Post-Refresh Configuration

**What happens:** Refresh completes, but logins, integrations, email behavior, or schedules remain broken because no one owns the post-refresh tasks.

**When it occurs:** Named Credentials, connected apps, email deliverability, and integration users.

**How to avoid:** Maintain a runbook with environment-specific reset steps and owners.

---

## Leaving Production Data Unmasked

**What happens:** Sensitive production data is copied to non-production and remains readable by a broader audience than policy allows.

**When it occurs:** Public sector, healthcare, education, and any org under audit pressure.

**How to avoid:** Make masking a standard refresh step, validate it, and document exceptions if any exist.

---

## Post-Copy Apex Runs as a User You Cannot Grant Anything To

**What happens:** The `SandboxPostCopy` class is executed at the end of the sandbox copy by a special Automated Process user that is not visible within the org, and that user does not have access to all objects and features (Apex Reference Guide, `SandboxPostCopy Interface`, apexrefguide.txt L228889–228893). Meanwhile, Apex database operations run in user mode by default — they apply the sharing rules, FLS, and object permissions of the running user (Apex Developer Guide, apexdev.txt L11938–11941) — and Automated Process users cannot perform object and FLS checks in custom code unless permission sets are explicitly applied to them (apexdev.txt L11921–11922). The masking or seeding job you wrote runs against a permission profile you cannot open in Setup and edit. It fails, and the sandbox is reported as ready.

**When it occurs:** Every post-copy class whose DML and queries are left at the default access level, and disproportionately on custom objects and protected standard fields — the exact fields a scrub is aimed at. It is worse in orgs on API version 67.0 and later, where Apex runs in user context by default rather than system mode (apexdev.txt L11925–11927).

**How to avoid:** Pin the class's writes to system mode — `insert as system` / `update as system` (apexdev.txt L11976–11979), or `AccessLevel.SYSTEM_MODE` on `Database` methods (apexdev.txt L11991–11994). Then verify by data, not by status: query for the condition the scrub was supposed to eliminate. Salesforce's own remedy when the script fails is to re-run it after sandbox activation as a user with appropriate permissions (apexrefguide.txt L228892–228893), so the runbook needs that manual fallback documented, with the class callable outside the copy.

---

## The Four-Argument Post-Copy Test Overload Passes on Code That Will Fail in Production

**What happens:** `Test.testSandboxPostCopyScript(script, organizationId, sandboxId, sandboxName)` runs the script as the **test initiator** — usually an admin with full access. The five-argument overload with `RunAsAutoProcUser = true` runs it with the same user access permissions used by post-copy tasks during sandbox creation (apexrefguide.txt L241191–241196, L241225–241232). Salesforce explicitly recommends the five-argument form over the four (apexrefguide.txt L241180–241186). A green test written with the shorter overload proves the script's logic and nothing about whether the user that actually runs it can reach the objects.

**When it occurs:** Any team that copied the four-argument signature out of an older sample, and any generated test — the shorter overload is the one an LLM reaches for first.

**How to avoid:** Use the five-argument overload with `RunAsAutoProcUser = true` in every post-copy test. The failure it surfaces at desk time is the failure that would otherwise surface at the end of a 29-day-floor Full sandbox copy.

---

## A Sandbox Deploy Runs No Tests at All Unless You Ask

**What happens:** By default, no tests are run in a deployment to a non-production organization such as a sandbox or a Developer Edition org (Metadata API Developer Guide, api_meta.txt L2659–2661). The team validates in UAT, sees a clean deploy, promotes the same package to production — and production runs the tests for the first time, on the day of the release.

**When it occurs:** Every sandbox deploy where `testLevel` is left unset, which is the default in most CLI invocations and every change set.

**How to avoid:** Set the test level explicitly on sandbox deploys: `RunLocalTests` is enforced regardless of the contents of the deployment package and is valid for both sandbox and production deployments (api_meta.txt L2677–2679). Contrast this with production, where tests execute by default only when the package contains Apex classes or triggers — meaning the two environments disagree about when tests run unless you make them agree.

---

## A Deploy Out of a Sandbox Stops Dead on a Username the Target Has Never Heard Of

**What happens:** When metadata refers to a specific user — a workflow email notification recipient, a dashboard running user — Salesforce matches by username against the destination org and adapts the org domain name. Sandbox usernames carry the sandbox name appended (`user@acme.com` in a sandbox named `test` becomes `user@acme.com.test`), and that suffix is ignored on deploy. But if a username in the source environment does not exist in the destination environment at all, Salesforce displays an error and **the deployment stops** until the usernames are removed or resolved (api_meta.txt L2705–2718). A user created only in the sandbox, or a leaver deactivated in production between the refresh and the deploy, blocks the whole package.

**When it occurs:** Long-lived sandboxes where test users accumulate, and any release that crosses a joiners-and-leavers boundary — so, most quarterly releases.

**How to avoid:** Treat dashboards and workflow-alert recipients as deployment dependencies, not configuration details. Before promoting, list the user references in the package and confirm each username resolves in the target. Prefer queues and permission-set-driven ownership over named individuals in metadata that has to travel.

---

## A Full Sandbox Created From a Template Does Not Get the Flat API Allocation

**What happens:** The 5,000,000 API calls per 24-hour period figure for a Full Sandbox applies **only to Full Sandboxes that aren't created from a template**. For any sandbox created from a template, values in the template determine the limits (Salesforce Developer Limits and Allocations Quick Reference, salesforce_app_limits_cheatsheet.txt L593–600). Teams plan a load test or a bulk migration rehearsal against the headline number, use a template to keep the copy small, and discover the ceiling is somewhere else entirely.

**When it occurs:** Full sandboxes provisioned with a template to shorten copy time or trim data — an increasingly common cost-control move — and any rehearsal sized against the published Full-sandbox number.

**How to avoid:** Record in the topology table whether each production-data sandbox was created from a template, and check the template's values before sizing any API-heavy rehearsal against it. If the rehearsal's whole point is to prove production API volume, the environment cannot be a templated one.

---

## Sandboxes Get No Grace When They Hit the Daily API Ceiling

**What happens:** When an org reaches or exceeds its daily API request limit, Salesforce lets operations proceed by a certain amount where possible, to avoid blocking workflows during unexpected spikes. That allowance applies only to paid orgs in active status — it explicitly **does not apply to trial orgs, Developer Edition, or sandboxes** (salesforce_app_limits_cheatsheet.txt L653–660). Production absorbs a spike; the sandbox rehearsing that same spike hard-stops.

**When it occurs:** Integration rehearsals, bulk-load dress runs, and load tests in Partial Copy or Full sandboxes — precisely the work those environments exist for.

**How to avoid:** Size an integration rehearsal against the sandbox's own allocation with no headroom assumed, and monitor it during the run rather than after. Concurrent long-running request limits are the same 25 for production orgs and sandboxes (salesforce_app_limits_cheatsheet.txt L481–488), so concurrency behaves alike — it is the daily total that has no give.

---

## The Test-Queue Ceiling Is Higher in Sandbox Than in Production

**What happens:** The maximum number of test classes that can be queued per 24-hour period is the greater of 500 or **20** multiplied by the number of test classes in the org for sandbox and Developer Edition orgs, but the greater of 500 or **10** multiplied by the number of test classes for production orgs (salesforce_app_limits_cheatsheet.txt L325–333). A CI pipeline tuned until it stops erroring in a sandbox is tuned against twice the allowance production will give it.

**When it occurs:** Release day, on a large org with many test classes and a re-run-on-failure CI strategy — the retries that fit in the sandbox exhaust the production allocation.

**How to avoid:** Budget the pipeline's test-class enqueues against the production multiplier, not the sandbox one, and cap automatic re-runs. If the environment strategy calls for the sandbox to be a faithful rehearsal of the production deploy, this is one of the places it is structurally not.

---

## An Inactive Sandbox Is Deleted, and the Only Warning Is a Notification Someone Can Turn Off

**What happens:** Salesforce sends the source org's users email notifications about impending deletions of sandboxes that have been inactive for 180 days or longer. `SandboxSettings.disableSandboxExpirationEmails` turns those notifications off for the source (production) org — it does not stop the deletion, only the warning (Metadata API Developer Guide, `SandboxSettings`, api_meta.txt L125452–125458). A training or disaster-recovery sandbox that nobody logs into is exactly the kind that is both eligible for deletion and unmissed until it is needed.

**When it occurs:** Environments kept "just in case" — annual training orgs, a parked pre-migration snapshot, a partner sandbox between engagements — combined with an org that suppressed the notifications to reduce Setup noise.

**How to avoid:** Check the value of `disableSandboxExpirationEmails` in production as part of the environment review, and keep it `false` unless a named owner tracks inactivity by another means. Give every low-traffic environment in the topology table a deliberate keep-alive step or an explicit decision to let it lapse — a sandbox with no owner is a sandbox with no one to receive the warning.
