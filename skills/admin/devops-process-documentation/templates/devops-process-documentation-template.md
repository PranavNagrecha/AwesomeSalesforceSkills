# DevOps Process Documentation — Work Template

Use this template when authoring or reviewing a Salesforce DevOps process document.
Choose the section that matches the document type requested.

---

## Document Type

Select one:

- [ ] Deployment Runbook — single deployment event execution checklist
- [ ] Environment Matrix — sandbox topology reference
- [ ] Deployment Guide — standing process reference

**Request summary:** (fill in what the user asked for)

---

## SECTION A: Deployment Runbook

_Use for a specific upcoming or in-progress deployment event._

### Release Identifier

| Field               | Value                          |
|---------------------|-------------------------------|
| Release name        | [e.g., Release 2026-Q2-001]   |
| Target org          | [org name and type]            |
| Target environment  | [Staging / UAT / Production]   |
| Deployment window   | [Date, start time, end time, timezone] |
| Deploying admin     | [Name and email]               |
| Release manager     | [Name and email — rollback decision owner] |
| Rollback decision owner | [Same or different person]  |

---

### Pre-Deploy Gate

Complete every item before opening the deployment window.

- [ ] Sandbox refresh date confirmed: Last Refresh Date = [date] (must be after [runbook authored date])
- [ ] Validation run status: PASS (run ID: [ID or link])
- [ ] Deployment window approved by: [approver name], approved on [date]
- [ ] Rollback path confirmed: [ ] Previous metadata version  [ ] Feature toggle  [ ] Hotfix
- [ ] Estimated rollback time: [N] minutes
- [ ] Named Credential values on hand for: [list credential names]
- [ ] Downstream system contacts reachable: [list integration team contacts]
- [ ] Communication sent to affected users: [Yes / Not required — reason]

---

### Deploy Execution

| Field                  | Value                          |
|------------------------|-------------------------------|
| Deploy method          | [ ] Change Set  [ ] DevOps Center  [ ] CLI  [ ] Package install |
| Change Set name / CLI command | [exact value]         |
| Executing user account | [username@org.com]             |
| Start timestamp        | [record when execution begins] |
| End timestamp          | [record when deploy completes] |
| Deploy status          | [ ] Succeeded  [ ] Failed      |

**If deploy failed:** stop, do not proceed to post-deploy validation. Initiate rollback decision gate.

---

### Post-Deploy Validation

Complete every item in order.

#### Named Credential Re-entry

Repeat for each credential in scope:

```
Credential name: [NamedCredential API Name]
Navigation: Setup > Security > Named Credentials > [Name]

Field                   | Value
------------------------|------------------------------------------
URL                     | [endpoint URL]
Identity Type           | [Named Principal / Per User / Anonymous]
Authentication Protocol | [Password / JWT / OAuth / Custom]
Username                | [username]
Password                | [retrieve from: vault entry name / secure handoff]

Verification:
- Test callout to: [endpoint/healthcheck path]
- Expected: HTTP 200
- Actual: ______
- Pass / Fail: ______
```

#### Flow Version Verification

For each Flow deployed:

- [ ] Flow API name: [Name] — Active version: [version number], Last modified: [timestamp]
- [ ] Confirmed correct version is active (not a prior version left active from before deploy)

#### Smoke Tests

| Test name | Steps | Expected result | Actual result | Pass/Fail |
|-----------|-------|-----------------|---------------|-----------|
| [Test 1]  | [link or description] | [expected] | | |
| [Test 2]  | [link or description] | [expected] | | |

#### Permission and Sharing Verification

- [ ] Permission set assignments confirmed for: [list affected user groups]
- [ ] Sharing rules active as expected: [confirm specific rules if changed]

---

### Rollback Decision Gate

**Go/No-Go threshold:** [define the condition that triggers rollback — e.g., "any P1 incident within 2 hours of go-live" or "smoke test failure on [test name]"]

**Decision owner:** [Name] — must be reachable at [phone/Slack handle]

**Rollback procedure:**

1. [Step 1 — e.g., deploy previous manifest or disable feature toggle]
2. [Step 2 — e.g., re-enter prior Named Credential values if applicable]
3. [Step 3 — notify stakeholders]
4. [Step 4 — file incident report within 24 hours]

**Rollback time estimate:** [N] minutes

---

### Deployment Close

- [ ] Smoke tests passed
- [ ] Named Credentials verified functional
- [ ] Stakeholder communication sent: [Yes / Not required]
- [ ] Runbook archived in: [shared location / wiki link]
- [ ] Deployment complete timestamp: [timestamp]

---

## SECTION B: Environment Matrix

_Use to document the sandbox topology._

**Last reviewed:** [YYYY-MM-DD]
**Reviewed by:** [Name]
**Next review due:** [YYYY-MM-DD — add to release pre-flight checklist]

| Org Name | Org Type | Purpose | Branch Alignment | Refresh Cadence | Data Policy | Owner |
|----------|----------|---------|-----------------|-----------------|-------------|-------|
| [name]   | [Developer Pro / Partial Copy / Full Copy / Production] | [purpose] | [branch pattern] | [Monthly / Quarterly / On demand / Never] | [Synthetic only / Anonymized prod / Full prod copy / No prod data permitted] | [name] |
| [name]   | | | | | | |
| [name]   | | | | | | |

**Environment rules:**
- [Add any environment-specific rules here, e.g., "sf-uat must not be used for feature development"]
- [Add data handling rules, e.g., "Full Copy sandboxes may not be accessed from personal devices"]

---

## SECTION C: Deployment Guide

_Use for the standing process reference that persists across all releases._

**Version:** [1.0 / date of last update]
**Owner:** [Name and role]

### Promotion Path

[Environment 1] → [Environment 2] → [Environment 3] → Production

### Deployment Method

[ ] Change Sets — used when: [describe scope]
[ ] DevOps Center — standard method for: [describe scope]
[ ] CLI / CI pipeline — used when: [describe scope]

### Approval Gates

| Stage | Approver | Criteria |
|-------|----------|----------|
| [e.g., Deploy to UAT] | [approver role] | [criteria, e.g., QA sign-off] |
| [e.g., Deploy to Production] | [approver role] | [criteria] |

### Recurring Manual Steps

List metadata types that always require manual post-deploy action:

1. **Named Credentials** — re-enter [list credential names] in each target environment after every deploy that includes integration metadata.
2. **Auth Providers** — re-enter client ID and client secret in Setup > Auth. Providers after deploy.
3. **[Other recurring manual step]** — [description]

### Rollback Strategy

Default rollback method: [Previous metadata version / Feature toggle / Hotfix]
Rollback decision owner role: [role title]
Maximum acceptable rollback time: [N minutes]

### Contact List

| Role | Name | Contact |
|------|------|---------|
| Release manager | | |
| DevOps lead | | |
| Integration owner | | |
| Org owner | | |

---

## Notes

Record any deviations from the standard pattern and the reason for the deviation.
