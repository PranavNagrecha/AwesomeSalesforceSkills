# UAT Test Script — [Feature Name]

Fill every bracketed placeholder. The checker treats a surviving `[...]` as an unfilled template.
A worked, fully populated version of this file is `references/worked-examples.md`.

**Project:** [Project or Release Name]
**Sandbox:** [Sandbox Name] ([Full / Partial Copy / Developer Pro / Developer])
**Sandbox Refreshed:** [YYYY-MM-DD]
**Build Deployed To Sandbox:** [YYYY-MM-DD — must be AFTER the refresh date]
**Next Refresh Booked:** [YYYY-MM-DD or "none inside this window" — who can veto it: [Name]]
**UAT Start Date:** [YYYY-MM-DD]
**UAT End Date / Sign-Off Target:** [YYYY-MM-DD]
**Validation Deploy Id / Date:** [0Af… / YYYY-MM-DD — must be within 10 days of sign-off for a quick deploy]

**Why this sandbox type:** [cite `admin/sandbox-strategy` § Sandbox Type Decision Matrix]
**Cases this environment cannot prove:** [list, or "none" — a Partial Copy cannot prove volume-dependent behaviour]

---

## Pre-UAT Environment Checklist

- [ ] Sandbox email deliverability **read** and recorded (Setup → Deliverability): [No Access / System Email Only / All Email], set by [Name] on [YYYY-MM-DD]
- [ ] Contact / Lead / Person Account emails scrubbed to a `.invalid` test domain **before** deliverability was raised (only `User.Email` is obfuscated automatically)
- [ ] Scheduled jobs (CronTrigger) and Named Credential endpoints reviewed post-refresh
- [ ] Test users created per persona with the sandbox username suffix, correct profiles and permission sets — **no System Administrator**
- [ ] Test data created or confirmed in sandbox, including the control record for any bulk case
- [ ] Record types, page layouts, and profile assignments verified to match production for in-scope profiles
- [ ] Mobile pass scoped in or explicitly out (a Lightning page assigned only for the `Large` form factor is not what the phone renders)
- [ ] Tester briefing complete — testers understand the feature being tested

---

## Persona Roster

| Persona Id | Name | Test User (with sandbox suffix) | Profile | Permission Sets / PSG | What only this persona proves |
|---|---|---|---|---|---|
| P-[XXX] | [Role] | [user@example.com.[sandbox]] | [Profile — not System Administrator] | [PSG name] | [the check no other persona can make] |

---

## Test Cases

At least one row must be a negative case, and at least one must be a bulk case wherever any
criterion depends on data volume.

| TC ID | US ID | AC ID | Persona | Type | Preconditions | Steps | Expected Result | Actual Result | Pass/Fail | Defect ID | Tester | Date |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-001 | US-[XXX] | AC-[XX.X] | P-[XXX] | positive | Logged in as: [persona test user]. Record state: [describe]. Sandbox: [name]. | 1. [Step 1]. 2. [Step 2]. 3. [Step 3]. | [Verbatim from the AC's Then clause] | | | | | |
| TC-002 | US-[XXX] | AC-[XX.X] | P-[XXX] | **negative** | Logged in as: [persona test user]. Record state: [describe]. | 1. [Step 1]. 2. [Step 2]. | [Expected restriction or error message, verbatim] | | | | | |
| TC-003 | US-[XXX] | AC-[XX.X] | P-[XXX] | **bulk** | Load tool: [Data Loader SOAP / Bulk API 2.0 / REST]. Assignment rule setting: [rule id or "none"]. Row count: [N]. UI control record: [id]. | 1. [Step 1]. 2. [Step 2]. | [All N rows succeed; owner distribution matches the control record] | | | | | |

---

## Defect Log

| Defect ID | TC ID | Severity | Component Type | Description | Steps to Reproduce | Expected | Actual | Assignee | Status | Retest Date |
|-----------|-------|----------|----------------|-------------|-------------------|----------|--------|----------|--------|-------------|
| DEF-001 | TC-XXX | P1 / P2 / P3 / P4 | Configuration / Automation / Security / Sharing / Data / Integration / Training / Environment | [Brief description of the defect] | [Numbered steps] | [Expected result] | [Actual result] | [Admin/Dev/Data] | Open / Fixed / Closed | |

---

## Severity Reference

| Severity | Definition |
|----------|-----------|
| P1 — Critical | Feature completely broken; data loss or security exposure; testing cannot continue |
| P2 — Major | Core use case fails; workaround exists but feature does not meet acceptance criteria |
| P3 — Minor | Feature works but deviates from acceptance criteria in a non-blocking way |
| P4 — Cosmetic | No functional impact; label or formatting issue only |

---

## UAT Summary

| Metric | Count |
|--------|-------|
| Total Test Cases | |
| Passed | |
| Failed — P1 Open | |
| Failed — P2 Open | |
| Failed — P3/P4 (logged, deferred) | |
| Not Executed | |

**Go / No-Go Criteria:**
- [ ] Zero P1 open defects
- [ ] Zero P2 open defects (or documented go-live exception approved by business owner)
- [ ] All P3/P4 defects logged with owner and target date
- [ ] All deferred defects acknowledged by business owner in writing

---

## UAT Sign-Off

**Decision:** ☐ Go for Production  ☐ No-Go (defects must be resolved first)

| Name | Role | Signature / Date |
|------|------|-----------------|
| [Business Owner] | Business Owner | |
| [BA / QA Lead] | BA / QA | |
| [Admin / Release Manager] | Admin | |

**Known issues accepted for go-live:**
[List any deferred P3/P4 defects accepted by the business owner, with target fix date]

**Negative and bulk coverage actually executed:** [TC ids — a Go decision is not valid without them]
**Build tested:** [validation id] validated on [YYYY-MM-DD]
**Environment at sign-off:** [sandbox name], [type], refreshed [YYYY-MM-DD], deliverability [setting]

---

## Regression Coverage

| Changed Component | Component Type | Affected Features | Test Cases Included in Regression |
|-------------------|---------------|-------------------|----------------------------------|
| [Flow name] | Flow | [Feature 1], [Feature 2] | TC-001, TC-007 |
| [Validation Rule name] | Validation Rule | [Feature 3] | TC-012 |
| [Profile name] | Profile | [Feature 1], [Feature 4] | TC-003, TC-015 |


---

## Plan Record (lintable)

Save this alongside the script as `uat-plan.yaml` and run:

```bash
python3 scripts/check_uat_and_acceptance_criteria.py --file uat-plan.yaml
```

```yaml
plan_id: UAT-[RELEASE]-[FEATURE]
release: "[Release name]"
status: draft
environment:
  sandbox_name: [SandboxName]
  sandbox_type: Full
  refreshed_on: 2026-01-01
  build_deployed_on: 2026-01-02
  email_deliverability: All Email
  validation_id: 0Af0000000000000AAA
  validated_on: 2026-01-10
personas:
  - persona_id: P-ONE
    name: [Role]
    profile: Minimum Access - Salesforce
    permission_sets: [PSG_Name]
    test_user: user@example.com.sandbox
test_cases:
  - case_id: TC-001
    story_id: US-001
    ac_id: AC-001.1
    persona: P-ONE
    sandbox: [SandboxName]
    negative_path: false
    bulk_path: false
    expected_result: "[Verbatim from the AC Then clause]"
    pass_fail: Not Run
  - case_id: TC-002
    story_id: US-001
    ac_id: AC-001.2
    persona: P-ONE
    sandbox: [SandboxName]
    negative_path: true
    bulk_path: false
    expected_result: "[Expected restriction or error message]"
    pass_fail: Not Run
  - case_id: TC-003
    story_id: US-002
    ac_id: AC-002.1
    persona: P-ONE
    sandbox: [SandboxName]
    negative_path: false
    bulk_path: true
    expected_result: "[All N rows succeed and owners match the control record]"
    pass_fail: Not Run
defects: []
sign_off:
  decision: No-Go
  decided_on: 2026-01-15
  business_owner: [Name]
  qa_lead: [Name]
  build_version: 0Af0000000000000AAA
  sandbox: [SandboxName]
  known_issues: "[none, or the deferred defect ids with owners and target dates]"
source_skills:
  - admin/uat-test-case-design
  - admin/acceptance-criteria-given-when-then
  - admin/sandbox-strategy
  - devops/sandbox-data-isolation-gotchas
```

Allowed values the checker enforces:

| Field | Allowed |
|---|---|
| `environment.sandbox_type` | Developer, Developer Pro, Partial Copy, Full, Scratch |
| `environment.email_deliverability` | No Access, System Email Only, All Email |
| `test_cases[].pass_fail` | Pass, Fail, Blocked, Not Run |
| `defects[].severity` | P1, P2, P3, P4 |
| `defects[].category` | configuration, automation, security, sharing, data, integration, training, environment |
| `defects[].status` | Open, In Progress, Fixed, Retest, Closed, Deferred |
| `sign_off.decision` | Go, No-Go, Conditional Go |
