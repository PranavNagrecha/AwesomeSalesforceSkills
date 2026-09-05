# DevOps Process Documentation — Work Template

Use this template when authoring or reviewing a Salesforce DevOps process document.
Choose the section that matches the document type requested.

---

## Document Type

Select one:

- [ ] Deployment Runbook — single deployment event execution checklist
- [ ] Environment Matrix — sandbox topology reference
- [ ] Deployment Guide — standing process reference
- [ ] Change-Request State Machine — who approves what, and the emergency path (Section D)
- [ ] Deploy Contract — the deployOptions this release used (Section E)

> The machine-checkable version of all five is a single `devops-process.yaml`. Its filled-in shape is
> `references/worked-examples.md` section 1; lint it with
> `python3 scripts/check_devops_process_documentation.py --file devops-process.yaml --manifest-dir manifest/`.
> Use this Markdown template when the audience will not read YAML.

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

## SECTION D: Change-Request State Machine

_Use to define who approves what. One row per state. A state with no approver role is an
accountability gap, not a shortcut._

**Record:** [`Change_Request__c` custom object / Jira / ServiceNow — name it]
**Record id used as the join key:** [e.g. `CR-{0000}` autonumber, quoted in the git branch, the deploy description, the RTM row and the UAT test case]

| State | Approver role | Exit criteria | SLA |
|---|---|---|---|
| Draft | [requesting admin] | [what must be filled in] | [none] |
| Triaged | [release manager] | [risk set, conflicts identified] | [N working days] |
| Built | [admin] | [exists in dev sandbox, committed to a branch named after the CR] | [ ] |
| Validated | [admin] | [validate-only run against the target succeeded; deploy id recorded] | [ ] |
| UAT-Signed-Off | [business owner] | [named owner executed the acceptance criteria] | [ ] |
| Approved | [release manager] | [rollback path owned, manual steps listed, window booked] | [ ] |
| Deployed | [release manager] | [post-deploy checks pass; deploy id and timestamp recorded] | [ ] |
| Rolled-Back | [release manager] | [rollback executed, smoke tests re-run, incident raised] | [ ] |
| Rejected | [release manager] | [reason recorded; branch deleted or parked with an expiry] | [ ] |

### Emergency path

| Field | Value |
|---|---|
| Approver role | [org owner — the role that authorises skipping the ladder] |
| Reachability | [phone / Slack handle, recorded here, not in a wiki] |
| Trigger | [e.g. P1 in production with no feature-flag or configuration workaround] |
| What it skips | [Triaged, Built, UAT-Signed-Off] |
| What it never skips | [the validate-only run — minutes on an Apex-free package, and the only cheap way to learn the package does not compile in the target] |
| Retro requirement | [normal-path CR within N days; change replayed forward into every lower environment so the ladder stops diverging] |

---

## SECTION E: Deploy Contract

_Record the deployOptions this release actually used. One column per run. Choosing the values is
`admin/change-management-and-deployment`; recording and verifying them is this document._

| Option | Validation run | Sandbox rehearsal | Production run |
|---|---|---|---|
| `checkOnly` | true | false | false |
| `testLevel` | [NoTestRun / RunSpecifiedTests / RunRelevantTests / RunLocalTests / RunAllTestsInOrg] | [same] | [same] |
| `runTests` | [only when testLevel is RunSpecifiedTests] | [ ] | [ ] |
| `rollbackOnError` | [true] | [true] | **true** (required for production) |
| `ignoreWarnings` | [false] | [false] | [false] |
| `purgeOnDelete` | [false] | [true — sandbox only] | **false** (inert in production) |
| `singlePackage` | [true] | [true] | [true] |
| Target org | [ ] | [ ] | [ ] |
| Deploy id | [record after the run] | [ ] | [ ] |
| Status read from the `status` field | [Succeeded / SucceededPartial / Failed] | [ ] | [ ] |

### Deploy order

_Only needed when the release is split across more than one submission. Submit each package only
after the previous one reports `Succeeded` — the queue is not first-in-first-out._

| # | Label | Metadata types | Manifest | Dependency reason |
|---|---|---|---|---|
| 1 | [schema and access] | [ ] | [manifest/package-01.xml] | [ ] |
| 2 | [presentation and routing] | [ ] | [ ] | [ ] |
| 3 | [automation and integration] | [ ] | [ ] | [ ] |
| 4 | [retirement] | [ ] | [destructiveChangesPost.xml] | [why post rather than pre] |

---

## SECTION F: RACI

_Roles, not names. Names live on the change-request record._

| Activity | Admin | Developer | Release manager | Data owner |
|---|---|---|---|---|
| Raise a change request | | | | |
| Set risk and identify conflicting CRs | | | | |
| Write the deploy order for the release | | | | |
| Run the validate-only pass | | | | |
| Approve the production window | | | | |
| Execute the deploy | | | | |
| Re-enter credentials post-deploy | | | | |
| Approve a production data export or masking exception | | | | |
| Approve a sandbox refresh (destroys in-flight UAT) | | | | |
| Call the rollback | | | | |
| Approve an emergency fix | | | | |

The last four rows are the ones usually missing. A refresh destroys other people's work and a data
export is a compliance decision; both need an accountable party before anyone needs one.

---

## Notes

Record any deviations from the standard pattern and the reason for the deviation.
