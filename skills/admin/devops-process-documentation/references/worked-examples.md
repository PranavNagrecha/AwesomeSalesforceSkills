# Worked Example — The Acme Case-Intake DevOps Process Document, Filled In

One process document worked through completely: **Acme Freight moves case intake off a shared
Outlook mailbox (`support@acmefreight.example`) into Service Cloud**. Two admins, one contract
developer, one release manager, one data owner. Four environments and a production org. The build
lands over three releases; this file documents the process that carries it, and the runbook for the
first of those releases, `CI-2026.10`.

Nothing here is a placeholder. Copy the blocks, change the names, and lint the result with
`scripts/check_devops_process_documentation.py`.

**What this file does not own.** Choosing the deploy method and the deploy options is
`admin/change-management-and-deployment`. Choosing the sandbox *tiers* and what a refresh costs
is `admin/sandbox-strategy`. The seasonal-release preparation cycle is
`admin/salesforce-release-preparation`. Post-refresh Apex is `admin/sandbox-post-refresh-automation`.
The rollback *technique* is `devops/rollback-and-hotfix-strategy`. This file documents the process
those decisions get written into, and links out rather than restating them.

---

## 1. The process document — `devops-process.yaml`

This is the machine-checkable artefact. One file, six sections, checked into the repo next to
`sfdx-project.json` and linted in CI.

```yaml
devops_process:
  id: DPD-ACME-CASE-INTAKE
  title: "Acme Freight — case intake, shared mailbox to Service Cloud"
  owner: "rmartin@acmefreight.example"
  owner_role: release-manager
  status: active
  updated: "2026-09-05"
  review_cadence: "First working day of each release cycle, and after any sandbox refresh"
  scope: >-
    Email-to-Case intake, Case record types, the intake queue and assignment rules,
    the triage screen flow, and the ERP callout that stamps shipment references.

# --------------------------------------------------------------------------
# 1a. Environment ladder
#     Every row needs purpose, refresh_cadence and owner or the checker fails.
#     Tier capacities and the platform refresh intervals are NOT restated here —
#     see admin/sandbox-strategy, "Type Capacities and Refresh Windows".
# --------------------------------------------------------------------------
environments:
  - name: ACMEDEV
    type: Developer
    purpose: "Individual build work — Flow, fields, layouts. First place anything is built."
    branch: "feature/*"
    refresh_cadence: "On demand, and always immediately after a production release lands"
    data_policy: "Synthetic only — no production data permitted"
    owner: "jkang@acmefreight.example"
    owner_role: admin
    post_refresh_runbook: "skills/admin/sandbox-post-refresh-automation"

  - name: ACMEQA
    type: PartialCopy
    purpose: "Integration regression. The only environment where the ERP sandbox endpoint is wired up."
    branch: "develop"
    refresh_cadence: "Monthly, first Monday, from Production"
    data_policy: "Anonymized production subset — emails masked by PrepareSandbox post-copy class"
    owner: "jkang@acmefreight.example"
    owner_role: admin
    post_refresh_runbook: "skills/admin/sandbox-post-refresh-automation"

  - name: ACMEUAT
    type: Full
    purpose: "Business UAT and production rehearsal. Deploy order is proved here before production."
    branch: "release/*"
    refresh_cadence: "Once per release cycle, at least 10 working days before the production window"
    data_policy: "Full production copy, emails masked. Treated as production for access purposes."
    owner: "rmartin@acmefreight.example"
    owner_role: release-manager
    post_refresh_runbook: "skills/admin/sandbox-post-refresh-automation"

  - name: PRODUCTION
    type: Production
    purpose: "Live org. 340 internal users, 1 Email-to-Case address, 1 ERP integration user."
    branch: "main"
    refresh_cadence: "Not applicable — source of truth"
    data_policy: "Live customer data. Restricted; no export without data-owner approval."
    owner: "dsingh@acmefreight.example"
    owner_role: org-owner
    post_refresh_runbook: "not applicable"

# --------------------------------------------------------------------------
# 1b. Change request record
#     The Salesforce-native option is a Change_Request__c custom object so the
#     record itself is reportable. Field design belongs to admin/object-creation-and-design;
#     what this document owns is the STATE MACHINE and who approves each move.
# --------------------------------------------------------------------------
change_request:
  object: Change_Request__c
  record_ownership: "Requesting admin owns the record until Approved; release manager owns it after."
  fields:
    - api_name: Name
      type: AutoNumber
      format: "CR-{0000}"
      purpose: "Human-quotable id used in the git branch name and the deploy description"
    - api_name: Summary__c
      type: Text(255)
      purpose: "One line. Appears in the release note and the deploy comment."
    - api_name: Metadata_Scope__c
      type: LongTextArea
      purpose: "The package.xml types this change touches. Drives the deploy-order review."
    - api_name: Target_Release__c
      type: Text(40)
      purpose: "CI-2026.10 etc. Blank means unscheduled."
    - api_name: Risk__c
      type: Picklist
      values: [Low, Medium, High]
      purpose: "High forces a UAT rehearsal and a named rollback owner before Approved."
    - api_name: Requires_Manual_Step__c
      type: Checkbox
      purpose: "True when the change touches credentials, Flow activation, or queue membership."
    - api_name: Rollback_Path__c
      type: LongTextArea
      purpose: "Filled in before approval, not after failure."
    - api_name: Status__c
      type: Picklist
      purpose: "The state machine below. Values must match the states list exactly."

  states:
    - name: Draft
      approver_role: requesting-admin
      exit_criteria: "Summary, metadata scope and target release filled in."
      sla: "No SLA — the requester's own queue."
    - name: Triaged
      approver_role: release-manager
      exit_criteria: "Risk set; Requires_Manual_Step__c set; duplicate/conflicting CRs identified."
      sla: "2 working days from submission."
    - name: Built
      approver_role: admin
      exit_criteria: "Change exists in ACMEDEV, committed to a feature branch named after the CR."
      sla: "Within the sprint."
    - name: Validated
      approver_role: admin
      exit_criteria: >-
        Validate-only run against ACMEUAT succeeded with the documented test level.
        Deploy id recorded on the CR.
      sla: "Before the release branch cuts."
    - name: UAT-Signed-Off
      approver_role: business-owner
      exit_criteria: "Named business owner has executed the acceptance criteria in ACMEUAT."
      sla: "5 working days from UAT open."
    - name: Approved
      approver_role: release-manager
      exit_criteria: >-
        Rollback path named and owned; manual post-deploy steps listed with owners;
        deployment window booked.
      sla: "2 working days before the window."
    - name: Deployed
      approver_role: release-manager
      exit_criteria: "Post-deploy checks in the runbook all pass. Deploy id and timestamp recorded."
      sla: "Within the window."
    - name: Rolled-Back
      approver_role: release-manager
      exit_criteria: "Rollback executed, smoke tests re-run, incident record raised."
      sla: "Within the window."
    - name: Rejected
      approver_role: release-manager
      exit_criteria: "Reason recorded on the CR. Branch deleted or parked with an expiry date."
      sla: "None."

  emergency_path:
    name: Emergency-Fix
    approver_role: org-owner
    trigger: "P1 in production with no feature-flag or configuration workaround."
    rule: >-
      Skips Triaged, Built, UAT-Signed-Off. Does NOT skip the validate-only run —
      a validation against production is the only cheap way to learn that the package
      does not compile there, and it is minutes, not hours, on an Apex-free package.
    retro_requirement: >-
      A normal-path CR is raised within 2 working days recording what shipped, and the
      change is replayed forward into ACMEDEV, ACMEQA and ACMEUAT so the ladder stops diverging.
    approver_reachability: "Org owner's phone number is in the runbook header, not in a wiki."

# --------------------------------------------------------------------------
# 1c. Deploy contract
#     Every field below is a documented Metadata API deployOptions parameter
#     (api_meta.txt L3088-3160). Choosing the values is
#     admin/change-management-and-deployment; RECORDING them is this skill.
# --------------------------------------------------------------------------
deploy_contract:
  validation_run:
    checkOnly: true
    testLevel: RunLocalTests
    rollbackOnError: true
    ignoreWarnings: false
    singlePackage: true
    purgeOnDelete: false
    runTests: []
    note: >-
      A validation that passes with tests can be promoted without rerunning them,
      but only for 10 days against that same target org
      (api_meta.txt L4863 "validated successfully for the target environment within the last 10 days").
  production_run:
    checkOnly: false
    testLevel: RunLocalTests
    rollbackOnError: true
    ignoreWarnings: false
    singlePackage: true
    purgeOnDelete: false
    runTests: []
    note: >-
      rollbackOnError defaults to false and "must be set to true if you're deploying to a
      production org" (api_meta.txt L3126-3129). Do not rely on the default.
  sandbox_run:
    checkOnly: false
    testLevel: RunLocalTests
    rollbackOnError: true
    ignoreWarnings: false
    singlePackage: true
    purgeOnDelete: true
    runTests: []
    note: >-
      testLevel is set explicitly even in sandbox, because "by default, no tests are run in a
      deployment to a non-production organization" (api_meta.txt L2662). Leaving it unset means
      the sandbox rehearsal does not rehearse the production test run.
      purgeOnDelete is true here and false in production because the option
      "only works in Developer Edition or sandbox orgs. It doesn't work in production orgs"
      (api_meta.txt L3119-3123).

# --------------------------------------------------------------------------
# 1d. Deploy order
#     Within ONE deployment the Metadata API resolves component dependencies itself;
#     this order exists because the release is split into three submissions.
#     Only one deployment runs at a time and queued deployments "are not necessarily
#     executed in the order in which they were submitted" — to get an order you must
#     "submit them one at a time after the previous deployment has completed
#     successfully" (api_meta.txt L4117-4121). That sentence is why this section exists.
# --------------------------------------------------------------------------
deploy_order:
  - step: 1
    label: "Schema and access"
    metadata_types: [GlobalValueSet, CustomObject, CustomField, RecordType, BusinessProcess, PermissionSet]
    reason: >-
      Nothing downstream compiles or assigns without the fields and record types.
      PermissionSet ships with the fields it grants so the release never has a window
      where the field exists and nobody can see it.
    manifest: manifest/package-01-schema.xml
  - step: 2
    label: "Presentation and routing"
    metadata_types: [Layout, QuickAction, Queue, AssignmentRules, AutoResponseRules, EmailServicesFunction]
    reason: >-
      Layouts reference the fields from step 1. The Queue must exist before the assignment
      rule that targets it. Email-to-Case routing is last in this step because it is the
      component that starts putting live traffic on the new schema.
    manifest: manifest/package-02-routing.xml
  - step: 3
    label: "Automation and integration"
    metadata_types: [Flow, FlowDefinition, ExternalCredential, NamedCredential, ApexClass, ApexTrigger]
    reason: >-
      The triage Flow reads the fields, the record type and the queue, so it cannot go first.
      Credentials and the callout class ship together with the Flow that calls them.
    manifest: manifest/package-03-automation.xml
  - step: 4
    label: "Retirement"
    metadata_types: [CustomField]
    destructive: destructiveChangesPost.xml
    reason: >-
      The two legacy mailbox-tracking fields are deleted AFTER the additions, because the
      old triage Flow still references them until step 3 replaces it. Post-destructive
      changes are the documented mechanism for exactly this
      (api_meta.txt L4652-4660). Post destructive changes are processed before tests run.
    manifest: manifest/package-04-destructive.xml

# --------------------------------------------------------------------------
# 1e. Runbook — release CI-2026.10, ACMEUAT rehearsal then PRODUCTION
#     Checker rule: a validate-only step must appear before any deploy step,
#     and a rollback step must exist.
# --------------------------------------------------------------------------
runbook:
  release: CI-2026.10
  target_org: PRODUCTION
  rehearsal_org: ACMEUAT
  window: "2026-10-17 07:00–10:00 Europe/London"
  deploying_admin: "jkang@acmefreight.example"
  rollback_decision_owner: "rmartin@acmefreight.example"
  rollback_owner_reachable_on: "+44 7700 900123 / Slack @rmartin — confirmed 2026-10-16"
  steps:
    - id: RB-01
      phase: pre-deploy
      action: retrieve
      owner: admin
      duration_minutes: 10
      detail: >-
        sf project retrieve start --manifest manifest/package-01-schema.xml --target-org PRODUCTION
        --target-metadata-dir baseline/CI-2026.10 — this is the rollback baseline, taken before
        anything changes. Retrieve always uses SOAP API even when deploys are set to REST
        (api_meta.txt L3650 "Commands that retrieve source, such as project retrieve start, always use SOAP API").
      pass_criteria: "baseline/CI-2026.10 contains a non-empty unpackaged.zip"
    - id: RB-02
      phase: pre-deploy
      action: check
      owner: release-manager
      duration_minutes: 5
      detail: >-
        Confirm ACMEUAT Last Refresh Date is on or after 2026-10-03 and that the ACMEUAT
        rehearsal of steps 1–4 completed clean. A refresh after the rehearsal invalidates it.
      pass_criteria: "Refresh date recorded on CR; rehearsal deploy ids recorded on CR"
    - id: RB-03
      phase: pre-deploy
      action: check
      owner: release-manager
      duration_minutes: 5
      detail: >-
        Confirm every CR in CI-2026.10 is in state Approved, and that each CR with
        Requires_Manual_Step__c = true has a named owner in section RB-10/RB-11.
      pass_criteria: "CR report 'CI-2026.10 Release Gate' returns 0 rows not in Approved"
    - id: RB-04
      phase: pre-deploy
      action: check
      owner: admin
      duration_minutes: 5
      detail: >-
        Confirm the package is inside the platform ceiling: 10,000 files and approximately
        39 MB compressed (api_meta.txt L2038-2045). CI-2026.10 is 412 files / 1.8 MB.
      pass_criteria: "file count and zip size recorded on the CR"
    - id: RB-05
      phase: validate
      action: validate-only
      owner: admin
      duration_minutes: 25
      detail: >-
        Run the validation_run deploy contract against PRODUCTION for each of the four
        manifests, one at a time. checkOnly=true "performs a test deployment (validation)
        of components without saving the components in the target org" (api_meta.txt L3095-3099).
        Record each deploy id — the 10-day quick-deploy clock starts here.
      pass_criteria: "Four validations Succeeded; four deploy ids on the CR; zero SucceededPartial"
    - id: RB-06
      phase: validate
      action: check
      owner: release-manager
      duration_minutes: 5
      detail: >-
        Read the status field, not the exit code. SucceededPartial is a documented deploy
        status (api_meta.txt L3341-3344) and it is not success. Treat it as a failure.
      pass_criteria: "status == Succeeded on all four"
    - id: RB-07
      phase: deploy
      action: deploy
      owner: admin
      duration_minutes: 20
      detail: >-
        Deploy in the deploy_order sequence, submitting each package only after the previous
        one reports Succeeded. Do not queue all four — queued deployments are not necessarily
        executed in submission order (api_meta.txt L4117-4121).
      pass_criteria: "Four deploys Succeeded, in order, deploy ids recorded"
    - id: RB-08
      phase: post-deploy
      action: check
      owner: admin
      duration_minutes: 5
      detail: >-
        Verify the active Flow version. status on a Flow is one of Active, Draft, Obsolete,
        InvalidDraft, UnderReview, and Draft/Obsolete both display as "Inactive" in the UI
        (api_meta.txt L68416-68423). Confirm Case_Triage_v4 is Active and no FlowDefinition
        shipped alongside it — a FlowDefinition's activeVersionNumber overrides the Flow's
        status field (api_meta.txt L73925-73931).
      pass_criteria: "Setup > Flows shows Case_Triage version 4 Active; version 3 Obsolete"
    - id: RB-09
      phase: post-deploy
      action: check
      owner: admin
      duration_minutes: 5
      detail: "Confirm the two legacy fields are gone and are recoverable from the Recycle Bin
        (purgeOnDelete is false for the production run, so they are not purged)."
      pass_criteria: "Setup > Object Manager > Case > Fields shows neither Legacy_Mailbox_Ref__c nor Legacy_Thread_Id__c"
    - id: RB-10
      phase: post-deploy
      action: manual-step
      owner: admin
      duration_minutes: 15
      detail: >-
        Re-enter the ERP external credential principal secret. The credential frame deploys;
        the secret does not survive a retrieve → deploy round trip, because on export
        "the consumer secret is always exported as a placeholder value, not as an encrypted
        secret" (api_meta.txt L24855-24856 — stated for AuthProvider.consumerSecret).
        Setup > Security > Named Credentials > External Credentials > ACME_ERP > Principals >
        ERP_Integration > Authenticate. Secret source: 1Password item "Acme ERP — SFDC principal".
        Never paste the secret into this runbook.
      pass_criteria: >-
        Execute Anonymous:
        HttpRequest r = new HttpRequest(); r.setEndpoint('callout:ACME_ERP/healthcheck');
        r.setMethod('GET'); System.debug(new Http().send(r).getStatusCode());
        returns 200. 401 → stop, escalate to the integration owner.
    - id: RB-11
      phase: post-deploy
      action: manual-step
      owner: admin
      duration_minutes: 10
      detail: >-
        Add the four Tier-1 agents to the Case_Intake_Triage queue. Queue membership is
        environment-specific and is the classic thing a copied runbook gets wrong.
      pass_criteria: "Setup > Queues > Case_Intake_Triage lists exactly the four named users"
    - id: RB-12
      phase: post-deploy
      action: smoke-test
      owner: business-owner
      duration_minutes: 15
      detail: >-
        Send a live email to support@acmefreight.example from an external address. Expect:
        Case created with record type Email_Intake, owner = Case_Intake_Triage queue,
        auto-response received within 2 minutes, Shipment_Ref__c populated by the ERP callout.
      pass_criteria: "All four observations true; case number recorded on the CR"
    - id: RB-13
      phase: post-deploy
      action: check
      owner: release-manager
      duration_minutes: 5
      detail: "Confirm the shared mailbox auto-forward to the Email Service address is still in
        place and that no rule is double-delivering. This is the only step that touches a
        non-Salesforce system."
      pass_criteria: "One case per test email, not two"
    - id: RB-14
      phase: rollback
      action: rollback
      owner: release-manager
      duration_minutes: 25
      detail: >-
        Threshold: any smoke test in RB-12 fails, OR a P1 is raised within 2 hours of the
        window closing. Procedure, in order:
        (1) deactivate Case_Triage v4 and re-activate v3 from Setup > Flows — seconds, and it
        stops the bleeding without a deploy;
        (2) deploy baseline/CI-2026.10 from RB-01 with rollbackOnError=true;
        (3) re-create the two deleted fields from the Recycle Bin (RB-09 kept them there);
        (4) re-enter the ERP secret again — a rollback deploy has the same placeholder problem
        the forward deploy had;
        (5) revert the mailbox auto-forward;
        (6) notify #acme-support and raise an incident record within 24 hours.
      pass_criteria: "RB-12 smoke tests pass against the rolled-back org"
```

---

## 2. The manifests and the commands

`manifest/package-01-schema.xml` — the first of the four submissions in `deploy_order`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_Intake_Source</members>
        <name>GlobalValueSet</name>
    </types>
    <types>
        <members>Case</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Case.Intake_Source__c</members>
        <members>Case.Shipment_Ref__c</members>
        <members>Case.Triage_Tier__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Case.Email_Intake</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Case_Intake_Agent</members>
        <members>Case_Intake_Supervisor</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

`manifest/destructiveChangesPost.xml` — paired with a `package.xml` that lists no components,
which is the shape the guide requires for a delete-only submission
(api_meta.txt L4630-4637):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case.Legacy_Mailbox_Ref__c</members>
        <members>Case.Legacy_Thread_Id__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

Commands. `sf project retrieve start --manifest path/to/package.xml` and the
`--target-metadata-dir` variant are both shown in the guide (api_meta.txt L1348, L1368), as is
the dry-run deploy form (api_meta.txt L3985):

```bash
# RB-01 — rollback baseline, mdapi format, no source tracking
sf project retrieve start \
  --manifest manifest/package-01-schema.xml \
  --target-org PRODUCTION \
  --target-metadata-dir baseline/CI-2026.10

# RB-05 — validate only. checkOnly=true, tests run, nothing saved.
sf project deploy validate \
  --manifest manifest/package-01-schema.xml \
  --target-org PRODUCTION \
  --test-level RunLocalTests \
  --wait 60 --json

# RB-07 — promote the validation without rerunning tests, within 10 days
sf project deploy quick --job-id 0Af...ABC --target-org PRODUCTION --json

# any step — read the status field, not just the exit code
sf project deploy report --job-id 0Af...ABC --target-org PRODUCTION --json
```

UNVERIFIED (2026-09-05): the `sf project deploy validate` and `sf project deploy quick` subcommand
spellings come from the Salesforce CLI Command Reference, which is not one of the eight extracted
guides. The Metadata API guide shows only `sf project deploy start --dry-run … --test-level NoTestRun`
(api_meta.txt L3985) and describes the underlying semantics as `checkOnly` plus
`deployRecentValidation()` (api_meta.txt L4855-4875). Confirm with `sf project deploy validate --help`
before putting these lines in a real runbook.

---

## 3. Release calendar

Two calendars have to agree: Acme's own release train and Salesforce's seasonal upgrades.

| Cycle | CR freeze | ACMEUAT refresh | UAT window | Validate-only | Production window | Notes |
|---|---|---|---|---|---|---|
| CI-2026.10 | 2026-09-25 | 2026-10-03 | 2026-10-06 → 2026-10-14 | 2026-10-16 | 2026-10-17 07:00 | First intake release |
| CI-2026.11 | 2026-10-23 | 2026-10-31 | 2026-11-03 → 2026-11-11 | 2026-11-13 | 2026-11-14 07:00 | Entitlements + milestones |
| CI-2026.12 | — | — | — | — | **frozen** | Salesforce Winter '27 production upgrade weekend |
| CI-2027.01 | 2027-01-08 | 2027-01-16 | 2027-01-19 → 2027-01-27 | 2027-01-29 | 2027-01-30 07:00 | Resumes after the upgrade |

Rules the calendar encodes:

- **No Acme release lands in the same weekend as a Salesforce seasonal upgrade.** The org changes
  underneath you and any incident triage has two candidate causes.
- **`ACMEUAT` does not get refreshed between the preview cutover and the production upgrade.**
  Refreshing returns the sandbox to whatever release its source org is on, which throws away the
  preview. This rule is owned by `admin/salesforce-release-preparation` — read it there, do not
  re-derive it here.
- **The validate-only run is scheduled, not improvised**, and it sits inside the 10-day quick-deploy
  window before the production slot (api_meta.txt L4863).

UNVERIFIED (2026-09-05): Salesforce ships three seasonal releases a year (Spring / Summer / Winter),
and the per-instance upgrade date and the preview-sandbox instance list are published on
help.salesforce.com, trust.salesforce.com and the release calendar page — none of which are among
the eight extracted guides and none of which can be fetched from this environment. Read the actual
upgrade date for your instance off trust.salesforce.com Planned Maintenance rather than off a
headline date, and record it on the calendar with the date you read it.

---

## 4. RACI

Roles, not people, so the matrix survives a leaver. Names live on the CR record.

| Activity | Admin | Developer | Release manager | Data owner |
|---|---|---|---|---|
| Raise a change request | **R** | R | A | C |
| Set risk and identify conflicting CRs | C | C | **R/A** | I |
| Build in ACMEDEV | **R** | R | I | I |
| Write the deploy order for the release | R | C | **A** | I |
| Run the validate-only pass | **R** | C | A | I |
| Approve the UAT sign-off | I | I | A | C |
| Approve the production window | C | I | **R/A** | C |
| Execute the deploy | **R** | C | A | I |
| Re-enter credentials post-deploy | **R** | C | I | I |
| Approve any production data export or masking exception | I | I | C | **R/A** |
| Approve an ACMEUAT refresh (destroys in-flight UAT) | C | I | **R/A** | C |
| Call the rollback | C | C | **R/A** | I |
| Approve an emergency fix | C | C | R | I |

The two rows that are usually missing and always cause an argument: **who approves a refresh** (it
destroys other people's work) and **who approves a data export** (it is a compliance decision, not
an admin convenience). The emergency-fix row's accountable party is the org owner, per
`change_request.emergency_path.approver_role` above — the release manager is responsible for
executing it but does not authorise skipping the ladder.

---

## 5. The documentation set

The process document is one of five artefacts. Each is owned by a different skill; this one links
them rather than absorbing them.

| Artefact | What it answers | Owning skill |
|---|---|---|
| Configuration workbook | "What is configured in this org, and why" | `admin/configuration-workbook-authoring` |
| Requirements traceability matrix | "Which requirement does this metadata satisfy, and which test proves it" | `admin/requirements-traceability-matrix` |
| Architecture decision records | "Why Email-to-Case rather than a custom inbound handler" | `architect/architecture-decision-records` |
| UAT acceptance criteria | "What the business owner executes before signing off state UAT-Signed-Off" | `admin/uat-and-acceptance-criteria` |
| **DevOps process document (this file)** | "Which environment, which approval, which deploy, which rollback" | `admin/devops-process-documentation` |

The join between them is the CR number. `Change_Request__c.Name` appears in the git branch name,
in the deploy description, in the RTM row, and in the UAT test case. That single identifier is what
makes a post-incident reconstruction possible at all.

---

## 6. Linting it

```bash
python3 scripts/check_devops_process_documentation.py --file devops-process.yaml

# with the manifests, so deploy_order coverage is checked against the real package.xml files
python3 scripts/check_devops_process_documentation.py \
  --file devops-process.yaml --manifest-dir manifest/

# or point it at a directory and let it find both
python3 scripts/check_devops_process_documentation.py --manifest-dir .
```

What it will catch on a first draft, in order of how often it fires:

1. An environment row with a `purpose` but no `owner` — the commonest omission, and the one that
   makes the refresh-approval RACI row unenforceable.
2. A change-request state with no `approver_role`, usually `Draft` or `Rejected`.
3. A runbook whose first `deploy` step precedes any `validate-only` step.
4. `testLevel: RunTests` or `testLevel: AllTests` — plausible-looking values that are not in the
   documented enum (api_meta.txt L3140-3168).
5. `testLevel: RunSpecifiedTests` with an empty `runTests` list.
6. `rollbackOnError: false` on a run whose target is production.
7. A metadata type present in `manifest/*.xml` that no `deploy_order` step claims.

---

## 7. What consumes this artefact

| Consumer | What it reads out of the document |
|---|---|
| `agents/release-train-planner/AGENT.md` | The release calendar and the freeze rules |
| `agents/change-impact-planner/AGENT.md` | `deploy_order` and the CR `Metadata_Scope__c` |
| `agents/deployment-risk-scorer/AGENT.md` | `deploy_contract` and the manual-step list |
| `agents/release-readiness-reviewer/AGENT.md` | The CR states and the UAT sign-off gate |
| `agents/deployment-failure-triager/AGENT.md` | The runbook step ids and their pass criteria |
