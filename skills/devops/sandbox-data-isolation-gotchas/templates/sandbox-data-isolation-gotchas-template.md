# Sandbox Data Isolation Gotchas — Work Template

Use this template when auditing a sandbox for isolation risks, investigating a sandbox isolation incident, or preparing a pre-refresh isolation checklist.

## Scope

**Skill:** `devops/sandbox-data-isolation-gotchas`

**Sandbox name:** (fill in, e.g., UAT, QA-Full, PerfTest)

**Sandbox type:** [ ] Developer  [ ] Developer Pro  [ ] Partial Copy  [ ] Full

**Request summary:** (fill in — e.g., post-incident investigation, pre-refresh audit, new SandboxPostCopy implementation)

**Trigger:** (paste the symptom or question that activated this skill)

---

## Context Gathered

Answer these before proceeding:

- **SandboxPostCopy class registered?** [ ] Yes — class name: ________________  [ ] No  [ ] Unknown
- **Last refresh date:** ________________
- **Deliverability setting (sandbox Setup > Deliverability):** [ ] No Access  [ ] System Email Only  [ ] All Email  [ ] Unknown
- **Contact/Lead email fields scrubbed?** Run `SELECT COUNT() FROM Contact WHERE Email != null AND Email NOT LIKE '%.invalid'` — count: ______
- **Active scheduled jobs (State = WAITING)?** Run `SELECT Id, CronJobDetail.Name, State FROM CronTrigger WHERE State != 'DELETED'` — count: ______
- **Named Credentials present?** [ ] Yes — list: ________________  [ ] No
- **Integrations connecting to external systems?** List: ________________
- **Known automation (workflows, Flows, Apex) that sends email?** Describe: ________________

---

## Isolation Status

| Control | Status | Notes |
|---|---|---|
| Email deliverability | [ ] Safe / [ ] At risk / [ ] Unknown | |
| Contact email obfuscation | [ ] Done / [ ] Needed / [ ] N/A (no data) | |
| Lead email obfuscation | [ ] Done / [ ] Needed / [ ] N/A (no data) | |
| Scheduled job abort | [ ] Done / [ ] Needed / [ ] N/A | |
| Named Credential endpoint URLs | [ ] Verified / [ ] At risk / [ ] Unknown | |
| Custom Settings / CMT endpoint URLs | [ ] Updated / [ ] At risk / [ ] N/A | |
| SandboxPostCopy registered for next refresh | [ ] Yes / [ ] No | |

---

## Approach

**Pattern applied:** (tick one)

- [ ] Pre-refresh checklist walkthrough — use before initiating a sandbox refresh
- [ ] Post-incident investigation — sandbox already sent email or called a live system
- [ ] New SandboxPostCopy implementation — building the class for the first time
- [ ] Audit of existing SandboxPostCopy class — reviewing for completeness

**Rationale:** (why this pattern applies to the current request)

---

## Actions Taken / Recommended

List each action:

1.
2.
3.

---

## Post-Refresh Manual Runbook Items

Items that cannot be automated in SandboxPostCopy:

| Step | Owner | Status |
|---|---|---|
| Set deliverability to System Email Only (Setup > Deliverability) | | [ ] Done |
| Update Named Credential [name] endpoint URL to sandbox target | | [ ] Done |
| Re-enter Named Credential [name] secret / OAuth token | | [ ] Done |
| Re-authorize connected app [name] | | [ ] Done |
| (add rows as needed) | | |

---

## Checklist

- [ ] Email deliverability verified and set to appropriate level
- [ ] Contact email field count = 0 with `.invalid` filter (or sandbox is metadata-only)
- [ ] Lead email field count = 0 with `.invalid` filter (or sandbox is metadata-only)
- [ ] No CronTrigger records in WAITING state connected to external systems
- [ ] Named Credential endpoint URLs reviewed — all point at non-production targets
- [ ] Custom Settings / Custom Metadata with endpoint URLs updated
- [ ] SandboxPostCopy class registered for next refresh (in production Setup)
- [ ] Manual runbook documented for remaining steps
- [ ] Debug log reviewed for SandboxPostCopy execution errors (Automated Process user)

---

## Notes

(Record any deviations from the standard isolation pattern and why — e.g., specific integrations that required a different approach, permissions issues with the Automated Process user, sandbox type constraints.)
