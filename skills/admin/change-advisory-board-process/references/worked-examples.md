# Worked Examples — Change Advisory Board Process

One scenario carried end to end: **Acme's CAB reviewing the case-intake release**.

Acme runs a Service Cloud org. Release `CI-2026.10` is the case-intake build — Case record
types and Support Processes, permission sets for Tier 1 / Tier 2 / Billing, Case OWD moved to
Private plus a criteria-based sharing rule, Case validation rules with an intake bypass,
Email-to-Case and Web-to-Case intake, assignment and escalation rules, entitlement milestones,
and two list views. Twenty build steps, one deploy window, one CAB meeting.

Everything below is an artefact you can copy and adapt. Section 3 is the record the checker
lints (`scripts/check_change_advisory_board_process.py`).

> **The environment ladder used throughout** — `ACMEDEV` → `ACMEQA` → `ACMEUAT` → `ACMEPROD`.
> The ladder itself and the change-request state machine are owned by
> `admin/devops-process-documentation`; this skill owns the *board* that sits on the
> `Approved` transition. The `Change_Request__c.Name` values below (`CR-0147`) are the join key
> between the two documents.

---

## 1. The CAB charter

Written once, reviewed quarterly. Without it, "the CAB approved it" is unfalsifiable — nobody
can say afterwards whether the right people were in the room.

```yaml
# artefacts/governance/cab-charter.yaml
cab_charter:
  name: "Acme Salesforce Change Advisory Board"
  version: "2.1"
  owner: release-manager
  reviewed: 2026-07-01
  next_review: 2026-10-01

  cadence:
    standing_meeting: "Tuesday 10:00 Europe/London, 45 minutes"
    submission_cutoff: "17:00 the preceding Thursday"
    async_window: >-
      Normal changes with risk: low may be approved async in the #cab channel between
      standing meetings, provided the quorum rule below is still met and the vote is
      recorded on the CR within 24 hours.

  # Quorum is a NUMBER plus a set of roles that must be among the voters.
  # A count without required roles lets three admins approve a sharing change.
  quorum:
    standard: 0            # pre-authorised; no board vote at all
    normal: 3
    emergency: 2

  required_roles:
    normal: [release-manager, business-owner, security-reviewer]
    emergency: [release-manager, org-owner]

  membership:
    - role: release-manager
      title: "Release Manager"
      standing: true
      decision_rights: "Chairs. Owns the calendar and the freeze register. Casting vote."
    - role: platform-admin
      title: "Salesforce Platform Admin"
      standing: true
      decision_rights: "Advises on metadata scope and deploy order. Votes."
    - role: security-reviewer
      title: "Security / IT"
      standing: true
      decision_rights: >-
        Veto on any change touching PermissionSet, Profile, SharingRules, OWD,
        NamedCredential, RemoteSiteSetting or ConnectedApp. A veto cannot be
        outvoted; it is escalated to org-owner.
    - role: business-owner
      title: "Head of Customer Support"
      standing: true
      decision_rights: "Veto on user-visible process change. Owns UAT sign-off."
    - role: data-owner
      title: "Data Owner (Case + Account)"
      standing: false
      decision_rights: "Attends when the change alters record visibility or retention. Votes."
    - role: org-owner
      title: "IT Director"
      standing: false
      decision_rights: "Escalation point. Sole approver of a freeze-window exception."

  decision_rights:
    approve: "Quorum met, required_roles present, no unresolved veto."
    approve_with_conditions: "Named conditions with owners; conditions block the deploy, not the vote."
    defer: "Insufficient evidence. The board names what is missing, not 'come back later'."
    reject: "Reason recorded on the CR. Requester may resubmit with new evidence."
    freeze_exception: "org-owner only, in writing, on the CR."
```

**What consumes it:** the checker reads `quorum` and `required_roles` and tests the decision
record's votes against them. Nothing in Salesforce reads this file — the charter is the input
to a human meeting and to the pipeline gate, not to the org.

---

## 2. The change classification matrix

Classification is a function of metadata type and risk signal, not of how the requester feels
about the change. Acme's matrix:

| Metadata type in the package | Default tier | Risk signal that raises the tier |
|---|---|---|
| `ListView`, `Report`, `Dashboard`, `EmailTemplate` (clone) | Standard | Filter references a field also used by a sharing rule → Normal |
| `CustomField` on a non-critical object, `CompactLayout`, `Layout` | Standard | Field is `Required` or feeds a validation rule → Normal |
| `ValidationRule` | **Normal** | Active on create and no bypass mechanism → Normal + rehearsal |
| `SharingRules`, `SharingCriteriaRule`, org-wide default change | **Normal** | Object over ~1M rows, or OWD tightening → Normal + off-hours window |
| `PermissionSet`, `PermissionSetGroup`, `Profile`, `CustomPermission` | **Normal** | Grants a `Modify All`/`View All`/`Author Apex` permission → Normal + security veto in play |
| `Flow` (record-triggered), `AssignmentRules`, `EscalationRules` | **Normal** | Ships active on first deploy → Normal + rehearsal |
| `NamedCredential`, `RemoteSiteSetting`, `ConnectedApp`, `ExternalCredential` | **Normal** | Always — external network surface |
| `ApexClass`, `ApexTrigger` | **Normal** | Any (production deploys of Apex run tests by default) |
| Anything in `destructiveChanges*.xml` | **Normal** | Deleting a component with dependents → Normal + rollback rehearsal |
| Restore-service fix for a live P1 | **Emergency** | — |

Two classification rules Acme writes down because arguments happen otherwise:

1. **Highest tier wins for the whole package.** A package containing one `ListView` and one
   `SharingRules` file is a Normal change. Tiers are not mixed inside one deploy; split the
   package if you want the list view to ship on the standard path.
2. **Why validation rules and sharing changes outrank list views.** A list view changes what
   one user sees in one list. A `ValidationRule` on `Case` that is active on create can reject
   every inbound Email-to-Case and Web-to-Case record silently — the intake channel has no user
   at a keyboard to read the error. A sharing or OWD change alters record visibility for every
   user at once and, at Acme's Case volume, triggers a sharing recalculation the platform
   documents as long-running enough that Salesforce ships a *defer sharing calculation*
   permission specifically so admins can "suspend and resume sharing calculations… when
   performing a large number of configuration changes, which might lead to very long sharing
   rule evaluations or timeouts" (`ldv.txt` L595–601, Large Data Volumes best-practice guide).
   That is the risk signal, and it is why the tier differs.

As an enum the checker and the ITSM form share:

```yaml
classification_enum: [standard, normal, emergency]
risk_level_enum: [low, medium, high]
decision_enum: [approved, approved-with-conditions, deferred, rejected]
vote_enum: [approve, approve-with-conditions, abstain, reject, veto]
```

---

## 3. The CAB decision record for `CI-2026.10`

This is the artefact. One YAML file per board decision, committed next to the release manifest
so the approval and the package it approved are versioned together.

```yaml
# artefacts/governance/cab-decisions/CAB-2026-014.yaml
cab_decision:
  id: CAB-2026-014
  change_request: CR-0147
  release: CI-2026.10
  title: "Case intake: record types, access model, intake channels, SLA"
  classification: normal
  raised_by: platform-admin
  meeting_date: 2026-10-06
  decision: approved-with-conditions
  charter_ref: artefacts/governance/cab-charter.yaml
  charter_version: "2.1"

  # ---- The vote ------------------------------------------------------------
  # Quorum for a normal change is 3, and release-manager, business-owner and
  # security-reviewer must all be among the voters (charter section 1).
  board:
    - role: release-manager
      name: "R. Okonkwo"
      vote: approve
    - role: security-reviewer
      name: "S. Bhatt"
      vote: approve-with-conditions
      condition: "Post-deploy permission audit within 24h; see conditions[1]."
    - role: business-owner
      name: "M. Traoré"
      vote: approve
    - role: data-owner
      name: "L. Fischer"
      vote: approve
    - role: platform-admin
      name: "J. Silva"
      vote: abstain
      note: "Author of the change; abstains by charter convention."

  conditions:
    - id: C1
      text: "Escalation rules and the Sev-1 entry deploy inactive; activation is a separate CR."
      owner: platform-admin
      blocks: deploy
    - id: C2
      text: >-
        Effective-permission audit of the three new permission sets against the approved
        matrix, run in ACMEPROD within 24 hours of deploy, output attached to CR-0147.
      owner: security-reviewer
      blocks: post-deploy-signoff

  # ---- Risk ----------------------------------------------------------------
  risk:
    level: high
    rationale: >-
      Case OWD moves from Public Read/Write to Private in the same package as a new
      criteria-based sharing rule and three permission sets. Access is recomputed for
      every Case in the org, and the intake channels are the only way support work
      enters the system.
    reversible: partial
    irreversible_elements:
      - "OWD tightening: reverting to Public Read/Write is itself a full recalculation, not an undo."
      - "Email-to-Case routing address verification is a manual, out-of-band step."

  blast_radius:
    source: "/analyze-field-impact run 2026-10-01, agents/field-impact-analyzer"
    report: artefacts/governance/evidence/field-impact-CI-2026.10.md
    objects: [Case, Account, Contact, Entitlement]
    records_affected: "~1.4M Case rows re-evaluated for sharing"
    users_affected: 212
    profiles_affected: [Support Tier 1, Support Tier 2, Billing Support]
    integrations_affected: ["Web-to-Case endpoint", "support@ and billing@ routing addresses"]
    metadata_types:
      - CustomObject
      - RecordType
      - PermissionSet
      - PermissionSetGroup
      - SharingRules
      - ValidationRule
      - AssignmentRules
      - EscalationRules
      - Flow
      - ListView

  # ---- Evidence ------------------------------------------------------------
  # Every path resolves under --manifest-dir. The checker fails the record when
  # one does not: an approval citing a missing file is an approval of nothing.
  test_evidence:
    - kind: uat
      artefact: artefacts/governance/evidence/uat-pack-CI-2026.10.md
      produced_by: admin/uat-and-acceptance-criteria
      summary: "12 Given/When/Then cases across the three intake channels; 12 pass in ACMEUAT."
      signed_off_by: business-owner
      date: 2026-10-02
    - kind: validation-deploy
      artefact: artefacts/governance/evidence/validate-ACMEPROD-0FC1x.json
      produced_by: devops/pre-deployment-checklist
      summary: >-
        checkOnly validation against ACMEPROD, testLevel RunLocalTests, 0 component
        errors, 0 test failures. Deploy id 0Af1x00000ABCDE recorded on CR-0147.
      date: 2026-10-05
    - kind: raci
      artefact: artefacts/governance/evidence/raci-CI-2026.10.md
      produced_by: admin/stakeholder-raci-for-sf-projects
      summary: "Named A for each deploy activity, including the manual post-deploy steps."
    - kind: release-run-sheet
      artefact: artefacts/governance/evidence/run-sheet-CI-2026.10.md
      produced_by: admin/salesforce-release-preparation
      summary: "Release Updates posture re-read this cycle; none enforced inside the window."

  # ---- Rollback ------------------------------------------------------------
  rollback:
    method: redeploy-previous-package
    package: artefacts/governance/rollback/CI-2026.09-package.xml
    owner: release-manager
    rehearsed: true
    rehearsed_in: ACMEUAT
    rehearsed_date: 2026-10-03
    rto_minutes: 45
    manual_steps:
      - "Re-set Case OWD to Public Read/Write in Setup — not carried by the rollback package."
      - "Re-verify the two Email-to-Case routing addresses."
    known_gap: >-
      Cancelling the forward deploy mid-flight is NOT the rollback plan. Metadata API
      cannot cancel a deployment whose status is Finalizing Deploy (api_meta.txt
      L4750-4753). The rollback is a second, forward deployment.

  # ---- Window --------------------------------------------------------------
  deploy_window:
    target_org: ACMEPROD
    start: 2026-10-10T20:00:00Z
    end: 2026-10-10T23:00:00Z
    approved_by: release-manager
    deploy_options:
      checkOnly: false
      testLevel: RunLocalTests
      rollbackOnError: true
      ignoreWarnings: false
      runTests: []
    quick_deploy:
      enabled: true
      validation_id: 0Af1x00000ABCDE
      validation_target_org: ACMEPROD
      validation_date: 2026-10-05

  freezes:
    - name: "Salesforce major service upgrade — ACMEPROD instance"
      start: 2026-10-16
      end: 2026-10-19
      source: "Salesforce Trust, instance upgrade schedule"
      exception_approver: org-owner
    - name: "Financial year-end close"
      start: 2026-12-28
      end: 2027-01-05
      source: "Finance"
      exception_approver: org-owner

  post_implementation_review:
    date: 2026-10-13
    owner: release-manager
    required: true
```

**How to read it**

- **`classification` drives everything else.** `normal` selects the quorum, the required roles
  and the evidence set. `emergency` relaxes the quorum and *adds* the retrospective requirement.
- **`board` is votes, not attendance.** A member who attended and did not vote is not part of
  quorum. That is why each row carries a `vote` from the enum.
- **`conditions[].blocks`** separates a condition that stops the deploy from one that stops the
  post-deploy sign-off. Collapsing the two is how conditions get quietly dropped.
- **`blast_radius` is imported, not asserted.** It cites the field-impact run that produced it.
  The board does not estimate blast radius in the meeting.
- **`test_evidence[].artefact` paths must resolve.** This is the single check that catches the
  most common CAB failure: an approval that references a UAT pack nobody wrote.
- **`rollback.rehearsed`** is a boolean the checker requires to be `true` for `risk.level: high`.
  "We would redeploy the old package" is a sentence, not a rehearsal.
- **`deploy_window` vs `freezes`** is a date-range overlap test, run by the checker rather than
  by whoever remembered the upgrade date.
- **`quick_deploy`** carries the validation id, its target org and its date because all three
  are conditions the platform imposes (section 5).

---

## 4. The manifests the record points at

The decision record approves a *package*, so the package has to be pinned. Manifest shape and
the `<version>`-only companion file are as the Metadata API Developer Guide documents them
(`api_meta.txt` L4619–4632).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- artefacts/M5-S04/package.xml — the package CAB-2026-014 approved (abridged) -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Case.Support</members>
        <members>Case.Billing</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Case_Support_Tier1</members>
        <members>Case_Support_Tier2</members>
        <members>Case_Billing_Support</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Case</members>
        <name>SharingRules</name>
    </types>
    <types>
        <members>Case.Require_Subject_On_Manual_Create</members>
        <name>ValidationRule</name>
    </types>
    <types>
        <members>Case</members>
        <name>AssignmentRules</name>
    </types>
    <types>
        <members>Case</members>
        <name>EscalationRules</name>
    </types>
    <version>62.0</version>
</Package>
```

A destructive step in the same release needs its own manifest plus a component-free
`package.xml` in the same directory:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- artefacts/M5-S04/destructiveChangesPost.xml — retire the interim intake list view -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case.Interim_Intake_Queue</members>
        <name>ListView</name>
    </types>
</Package>
```

Deletions are processed before additions by default; `destructiveChangesPre.xml` and
`destructiveChangesPost.xml` (API 33.0 and later) move them either side of the additions
(`api_meta.txt` L4641–4652). Wildcards are not supported in a destructive manifest
(`api_meta.txt` L4612–4613). A CAB reviewing a package with a destructive manifest is
reviewing an ordering decision, not just a component list — deploy-order documentation is
owned by `admin/devops-process-documentation`.

---

## 5. The deploy options the CAB decision actually controls

The board approves a *deployment*, and a deployment is a package plus a `DeployOptions`. These
are the five the decision record pins, with what the guide says about each:

| Option | Value at Acme | What the Metadata API Developer Guide states |
|---|---|---|
| `checkOnly` | `false` at deploy, `true` for the prior validation | "Set to `true` to perform a test deployment (validation) of components without saving the components in the target org." (L3095–3099) |
| `testLevel` | `RunLocalTests` | Enum: `NoTestRun`, `RunSpecifiedTests`, `RunRelevantTests` (beta), `RunLocalTests`, `RunAllTestsInOrg`. `NoTestRun` "applies only to deployments to development environments". `RunLocalTests` "is the default for production deployments that include Apex classes or triggers". (L4280–4329) |
| `rollbackOnError` | `true` | "This parameter must be set to `true` if you're deploying to a production org." (L4255–4260) |
| `ignoreWarnings` | `false` | "Defaults to `false`… Don't set this argument to `true` for deployments to production organizations." (L7390–7392) |
| `runTests` | `[]` | "A list of Apex tests to run during deployment… To use this option, set `testLevel` to `RunSpecifiedTests`." (L3132–3135) |

A CAB that approves "the change" without pinning these has approved a range of behaviours: the
same package deployed with `rollbackOnError: false` can land as `SucceededPartial` — a real
`DeployStatus` value (`api_meta.txt` L7451) — leaving the org in a state nobody reviewed.

**Quick deploy, and why the record carries three fields for it.** A validation can be promoted
to a deployment without re-running Apex tests only when "the components have been validated
successfully **for the target environment** within the last **10 days**", the Apex tests in the
target org passed, and coverage requirements are met (`api_meta.txt` L4863–4869, and identically
at L3452–3458 for the REST `deployRequest` resource). Hence `validation_id`,
`validation_target_org` and `validation_date` — a validation against `ACMEUAT` cannot be
quick-deployed to `ACMEPROD`, and a validation the board approved three weeks ago has expired.

The commands, for the record:

```bash
# 1. Validate against the target org and note the deploy id. This is the evidence
#    entry `validate-ACMEPROD-0FC1x.json` in the decision record.
sf project deploy validate \
  --manifest artefacts/M5-S04/package.xml \
  --target-org ACMEPROD \
  --test-level RunLocalTests \
  --json > artefacts/governance/evidence/validate-ACMEPROD-0FC1x.json

# 2. Lint the decision record before the meeting, not after.
python3 skills/admin/change-advisory-board-process/scripts/check_change_advisory_board_process.py \
  --manifest-dir artefacts

# 3. Inside the approved window, quick-deploy the validated id.
sf project deploy quick --job-id 0Af1x00000ABCDE --target-org ACMEPROD

# 4. Evidence that the deploy happened, who ran it, and whether tests ran.
sf project deploy report --job-id 0Af1x00000ABCDE --target-org ACMEPROD --json
```

**Verification after the window closes.** `DeployResult` carries `createdBy` /
`createdByName` and `canceledBy` / `canceledByName` (API 30.0 and later, `api_meta.txt`
L7346–7360), so the deploy report answers "who deployed this" from the platform rather than
from memory. For the Setup-side half, query the audit object:

```sql
SELECT CreatedDate, CreatedBy.Name, Action, Section, Display, DelegateUser
FROM SetupAuditTrail
WHERE CreatedDate >= 2026-10-10T20:00:00Z AND CreatedDate <= 2026-10-11T02:00:00Z
ORDER BY CreatedDate DESC
```

`SetupAuditTrail` "represents changes you or other admins made in your org's Setup area for at
least the last 180 days" and supports `query()` and `retrieve()` only
(`object_reference.txt` L261536–261560). `Action` is the category ("a value of `PermSetCreate`
indicates that an administrator created a permission set"), `Display` the full description,
`Section` the Setup menu area, and `DelegateUser` the Login-As user if one performed the action.
Its limits are in Gotcha 8.

---

## 6. The emergency path

Same board, different quorum, and one thing the normal path does not have: a mandatory
retrospective with a date on it.

```yaml
# artefacts/governance/cab-decisions/CAB-2026-015.yaml
cab_decision:
  id: CAB-2026-015
  change_request: CR-0151
  release: CI-2026.10-hotfix-1
  title: "Deactivate Case.Require_Subject_On_Manual_Create — rejecting all Web-to-Case"
  classification: emergency
  raised_by: platform-admin
  meeting_date: 2026-10-11
  decision: approved
  charter_ref: artefacts/governance/cab-charter.yaml
  charter_version: "2.1"

  trigger: >-
    P1 raised 2026-10-11 06:40Z. The validation rule shipped in CI-2026.10 is active on
    create and Web-to-Case supplies no Subject, so every web-channel case since the deploy
    window has been rejected. 340 cases lost. No configuration workaround.

  board:
    - role: release-manager
      name: "R. Okonkwo"
      vote: approve
    - role: org-owner
      name: "P. Vasquez"
      vote: approve

  risk:
    level: medium
    rationale: >-
      Single ValidationRule set inactive. Reverting to the pre-CI-2026.10 state for one
      component. No access or sharing change.
    reversible: yes

  blast_radius:
    source: "Incident INC-2211, scoped by the on-call admin"
    report: artefacts/governance/evidence/inc-2211-scope.md
    objects: [Case]
    records_affected: "340 rejected inbound cases require replay"
    users_affected: 0
    metadata_types: [ValidationRule]

  test_evidence:
    - kind: validation-deploy
      artefact: artefacts/governance/evidence/validate-hotfix-ACMEPROD.json
      produced_by: devops/pre-deployment-checklist
      summary: >-
        checkOnly against ACMEPROD, testLevel NoTestRun is NOT used for production —
        RunLocalTests, 0 errors. Two minutes. The emergency path skips UAT, not validation.
      date: 2026-10-11

  rollback:
    method: redeploy-previous-package
    package: artefacts/governance/rollback/CI-2026.10-package.xml
    owner: release-manager
    rehearsed: false
    rehearsed_note: "Emergency path; rehearsal waived by org-owner and recorded here."
    rto_minutes: 15
    manual_steps: []

  deploy_window:
    target_org: ACMEPROD
    start: 2026-10-11T08:00:00Z
    end: 2026-10-11T09:00:00Z
    approved_by: org-owner
    deploy_options:
      checkOnly: false
      testLevel: RunLocalTests
      rollbackOnError: true
      ignoreWarnings: false
      runTests: []
    quick_deploy:
      enabled: false

  freezes:
    - name: "Salesforce major service upgrade — ACMEPROD instance"
      start: 2026-10-16
      end: 2026-10-19
      source: "Salesforce Trust, instance upgrade schedule"
      exception_approver: org-owner

  # Emergency records without this are rejected by the checker. An emergency path
  # with no retrospective is a permanent bypass wearing a temporary label.
  post_implementation_review:
    date: 2026-10-14
    owner: release-manager
    required: true
    forward_fix_cr: CR-0152
```

Three rules Acme's charter attaches to the emergency path:

1. **It skips UAT and the standing meeting. It does not skip validation.** A `checkOnly` run
   against the target org costs minutes on an Apex-free package and is the cheapest way to learn
   the package does not deploy there. The same rule appears in
   `admin/devops-process-documentation`'s `change_request.emergency_path`.
2. **A forward-fix CR is raised within two working days** so the change is replayed down the
   ladder and `ACMEDEV`/`ACMEQA`/`ACMEUAT` stop diverging from production.
3. **The emergency:normal ratio is reported monthly.** Acme's threshold is 15%; above it, the
   normal cycle is treated as the defect, not the requesters.

---

## 7. The post-implementation review

```markdown
# PIR — CAB-2026-014 / CR-0147 (CI-2026.10)
Held 2026-10-13. Chair: release-manager. Attendees: platform-admin, security-reviewer,
business-owner, data-owner.

## 1. Did it deploy as approved?
Deploy id 0Af1x00000ABCDE, status Succeeded, 0 component errors, RunLocalTests passed.
`sf project deploy report` confirms createdByName = J. Silva, inside the approved window.
SetupAuditTrail for the window shows two entries NOT in the package — a Case layout tweak
made in Setup at 21:14Z by the on-call admin. Raised as CR-0153 to bring it into source.

## 2. Were the conditions met?
| Condition | Owner | Status |
|---|---|---|
| C1 escalation rules deployed inactive | platform-admin | Met — verified in Setup |
| C2 effective-permission audit within 24h | security-reviewer | Met — 2026-10-11 09:20Z, 1 discrepancy |

C2 discrepancy: `Case_Support_Tier2` carried a `View All` on Account that was present in
ACMEPROD before the deploy and is not in the source file. Permission-set deploys add and
update; they do not remove what was not in the file (Gotcha 2). Removal tracked as CR-0154.

## 3. What did the blast-radius estimate get wrong?
Estimated 212 users affected; actual 227 — the Billing queue members were not in the
field-impact run because queue membership is not a field. Feed back into the next
/analyze-field-impact scope.

## 4. Did the classification hold?
Yes. Normal was correct. The board notes that had the ListView shipped in its own package
on the standard path, the release would have needed two windows for no benefit.

## 5. Actions
| # | Action | Owner | Due |
|---|---|---|---|
| 1 | CR-0153: bring the out-of-band layout change into source | platform-admin | 2026-10-17 |
| 2 | CR-0154: remove the drifted View All from Tier 2 | security-reviewer | 2026-10-17 |
| 3 | Add queue membership to the field-impact scope checklist | release-manager | 2026-10-20 |
```

The PIR is where the charter earns its next revision. Acme's `2.1` charter exists because a
`2.0` PIR found that "three approvers" without named roles let three admins approve a sharing
change.

---

## 8. What consumes each artefact

| Artefact | Consumed by | Not consumed by |
|---|---|---|
| `cab-charter.yaml` | The checker (quorum, required roles); the CAB meeting | Nothing in the org |
| Classification matrix | The ITSM change form; the PR classification check in `references/examples.md` | Nothing in the org |
| `CAB-2026-0NN.yaml` | The checker; the pipeline gate; the compliance auditor | Nothing in the org — Salesforce has no CAB record type |
| `package.xml` / `destructiveChanges*.xml` | `sf project deploy validate` / `deploy start`; `admin/change-management-and-deployment` | — |
| PIR markdown | The next charter review; `devops/post-deployment-validation` | — |

Every one of these lives outside the Salesforce org. That is the constraint that shapes the
whole practice: the board's decision cannot be enforced by anything inside the system being
deployed to (see `references/llm-anti-patterns.md`, Anti-Pattern 1).
