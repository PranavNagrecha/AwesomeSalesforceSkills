# Gotchas — Sandbox Post-Refresh Automation

Non-obvious behaviors of the SandboxPostCopy lifecycle.

---

## Gotcha 1: `SandboxPostCopy` requires `global` access modifier

**What happens.** Class declared `public class MyPrep implements
SandboxPostCopy`. Compiles in Apex but the post-copy framework
can't invoke it because the interface implementation must be
`global`.

**When it occurs.** Standard Apex pattern habit.

**How to avoid.** `global class MyPrep implements SandboxPostCopy`.
Both the class and `runApexClass` method are `global`.

---

## Gotcha 2: `runApexClass` runs ONCE; mid-execution failure leaves sandbox half-prepared

**What happens.** Post-copy class's first method (mask emails)
succeeds. Second method (deactivate users) hits a governor limit.
Class throws. Sandbox is unlocked anyway, but only emails are
masked; users still active.

**When it occurs.** Long post-copy classes that exceed sync CPU.

**How to avoid.**
- Make every step idempotent so re-running cleans up.
- For very long work, queue follow-up work via Queueable / Batch.
  The post-copy class enqueues; the queueable does the long work.
- Document the manual "re-run" command (`Test.testSandboxPostCopyScript`
  in anonymous Apex, with the deployed class).

---

## Gotcha 3: Scheduled jobs DO copy from prod to sandbox

**What happens.** Production has a scheduled batch that
synchronizes data with an external system every hour. Sandbox is
refreshed; the batch copies. After sandbox unlock, the batch
fires — sending sandbox-side data to the production-pointing
integration.

**When it occurs.** Every refresh that doesn't include explicit
job-disable in post-copy.

**How to avoid.** `System.abortJob` for every CronTrigger in
post-copy. Or selectively for jobs that mutate external state.
Test by querying `CronTrigger` after the sandbox is up to confirm
the disable.

---

## Gotcha 4: Named Credential URLs are not Apex-mutable directly

**What happens.** Post-copy class tries to update Named
Credential's URL via DML; Apex doesn't expose it for write.

**When it occurs.** Implementing endpoint scrubbing in pure Apex.

**How to avoid.** Pre-deploy sandbox-pointing Named Credential
metadata as a SEPARATE metadata-deploy step that runs after the
sandbox is unlocked (CI pipeline orchestrates: refresh → wait →
deploy NC metadata → run post-copy). Or accept that NCs need
manual re-pointing post-refresh.

---

## Gotcha 5: Email deliverability behavior post-refresh varies by org

**What happens.** Some orgs find deliverability is reset to
"System emails only" after refresh; others find it remains at
"All emails". Behavior isn't 100% deterministic across editions /
tiers.

**When it occurs.** Refreshes where the deliverability mitigation
relies on Salesforce's auto-reset behavior.

**How to avoid.** Don't depend on auto-reset. Set deliverability
explicitly in post-copy via `Setup → Email → Deliverability`
Custom Setting (if exposed) or via metadata deploy. Or pin the
sandbox at "System emails only" once and trust it across
refreshes (verify in your org).

---

## Gotcha 6: `SandboxContext.sandboxName()` returns the human-given name

**What happens.** Post-copy logic branches on
`context.sandboxName() == 'Dev'`. Admin renames the sandbox to
"Development". Branching breaks silently.

**When it occurs.** Sandbox renames; or org acquisitions where
naming conventions differ.

**How to avoid.** Document the names your post-copy class
branches on. Add an explicit fallback for unknown names. Don't
trust the name as a stable identifier.

---

## Gotcha 7: The post-copy class must already be deployed in production

**What happens.** Admin writes the post-copy class in a sandbox.
Refresh runs; the class doesn't exist in the refreshed sandbox
because it was never in prod.

**When it occurs.** First-time deployment of the post-copy
infrastructure.

**How to avoid.** Deploy the post-copy class to PRODUCTION first.
The sandbox copies it from prod on refresh. Configure it on each
sandbox in Setup → Sandboxes → Apex Class.

---

## Gotcha 8: Test coverage for post-copy classes

**What happens.** SandboxPostCopy class deploys to production but
has zero test coverage; deploy fails on the org-wide 75% threshold.

**When it occurs.** First-time deployment without a test class.

**How to avoid.** Use `Test.testSandboxPostCopyScript` in a test
class that invokes the post-copy logic. Asserts each method's
side effects.

---

## Gotcha 9: Single-execution semantics — no retry on failure

**What happens.** Post-copy class throws an unhandled exception.
The sandbox is unlocked anyway; the post-copy doesn't re-run
automatically. Admin must manually invoke
`Test.testSandboxPostCopyScript` from anonymous Apex.

**When it occurs.** Any unhandled exception during post-copy.

**How to avoid.** Wrap each method in try-catch; log + continue
rather than throwing. Manual re-run procedure documented in the
runbook.
