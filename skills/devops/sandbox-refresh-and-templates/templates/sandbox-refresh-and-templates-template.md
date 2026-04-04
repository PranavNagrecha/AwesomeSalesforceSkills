# Sandbox Refresh Planning Template

Use this template to plan and document a sandbox refresh. Fill in every section before initiating the refresh. Keep the completed document in the team's release runbook.

---

## Refresh Target

| Field | Value |
|---|---|
| Sandbox name | _(e.g., UAT, QA, FULL-PERF)_ |
| Sandbox type | Developer / Developer Pro / Partial Copy / Full |
| Refresh initiated by | _(name and role)_ |
| Target refresh date | YYYY-MM-DD |
| Last refresh completed | YYYY-MM-DD |
| Refresh interval for this type | 1 day / 5 days / 29 days |
| Next eligible date (last refresh + interval) | YYYY-MM-DD |

**Eligibility check:** Is today on or after the next eligible date?
- [ ] Yes — proceed
- [ ] No — record the eligible date and reschedule

---

## Sandbox Template (Partial Copy Only)

Skip this section if the sandbox type is Developer, Developer Pro, or Full.

| Field | Value |
|---|---|
| Template name | _(name of the template in Setup > Sandbox Templates)_ |
| Template last reviewed | YYYY-MM-DD |
| Template attached to sandbox record | Yes / No |

**Objects in this template:**

| Object | Record Count Cap | Purpose |
|---|---|---|
| _(Object API name)_ | _(number or "All")_ | _(why this object is included)_ |
| | | |
| | | |

**Template gaps identified:**
_(List any objects or reference data not in the template that current test scenarios require.)_

---

## SandboxPostCopy Automation

| Field | Value |
|---|---|
| SandboxPostCopy class name | _(Apex class name, e.g., UAT_SandboxSetup)_ |
| Class exists in production | Yes / No |
| Class registered on sandbox record | Yes / No |
| Class version-controlled in repo | Yes / No |

**What the class automates:**
- [ ] Updates custom settings with new org ID from `context.organizationId()`
- [ ] Aborts all scheduled CronTrigger records
- [ ] Updates integration endpoint URLs to sandbox equivalents
- [ ] Masks or scrubs PII fields (list objects below)
- [ ] Other: _(describe)_

**PII objects scrubbed:**
_(List each object and field that is masked or overwritten by the class.)_

---

## Manual Post-Refresh Runbook

These steps cannot be automated via Apex and must be completed by a human after the refresh is active.

| Step | Owner | Completed |
|---|---|---|
| Re-enter Named Credential secrets for: _(list each)_ | _(name)_ | [ ] |
| Re-authorize OAuth connected apps: _(list each)_ | _(name)_ | [ ] |
| Set email deliverability to: _(System Email Only / All Email)_ | _(name)_ | [ ] |
| Update external system config pointing at sandbox URL: _(list each system)_ | _(name)_ | [ ] |
| Verify sandbox is not listed as production in any monitoring tool | _(name)_ | [ ] |
| Other: _(describe)_ | _(name)_ | [ ] |

---

## Pre-Refresh Sign-Off

Confirm all of the following before clicking Refresh:

- [ ] Refresh interval has elapsed
- [ ] All sandbox users have been notified that work will be lost
- [ ] No active uncommitted work exists in the sandbox (or it has been committed/backed up)
- [ ] Sandbox template is attached and current (Partial Copy only)
- [ ] SandboxPostCopy class is registered and up to date in production
- [ ] Manual runbook has been assigned to owners

**Approved by:** ______________________  **Date:** __________

---

## Post-Refresh Verification

Complete after the sandbox status shows "Active":

- [ ] SandboxPostCopy class execution confirmed — no errors in sandbox debug logs for Automated Process user
- [ ] Custom settings reflect new org ID
- [ ] All scheduled jobs aborted or confirmed sandbox-safe
- [ ] Named Credentials reconfigured
- [ ] At least one integration smoke test passed
- [ ] Email deliverability verified
- [ ] PII masking verified — spot-check at least 5 Contact or Account records
- [ ] Sandbox shared with QA / development team

**Verified by:** ______________________  **Date:** __________

---

## Notes

_(Record any deviations from the standard process, issues encountered during refresh, or decisions made.)_
