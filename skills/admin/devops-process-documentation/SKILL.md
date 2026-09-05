---
name: devops-process-documentation
description: "Use when authoring, reviewing, or maintaining Salesforce DevOps operational documents — runbooks, environment matrices, deployment guides, and post-deploy validation checklists. Triggers: 'runbook', 'environment matrix', 'deployment guide', 'pre-deploy checklist', 'post-deploy validation', 'how do I document a deployment', 'rollback procedure template'. NOT for what actually belongs on the pre-deploy gate — use devops/pre-deployment-checklist. NOT for release calendar, versioning, or go/no-go governance — use devops/release-management. Also covers: the devops-process YAML artefact (environment ladder, change-request state machine, deploy contract, deploy order, RACI), the deployOptions the runbook must record (checkOnly, testLevel, rollbackOnError, ignoreWarnings, purgeOnDelete, singlePackage, runTests), destructiveChangesPre/Post ordering, and the change-request emergency path."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - runbook
  - deployment-guide
  - environment-matrix
  - devops-documentation
  - operational-excellence
inputs:
  - "Org environment inventory: names, types (Developer, Partial, Full), purposes, and branch alignments"
  - "Deployment scope: metadata types, manual steps, Named Credential entries required"
  - "Rollback options: previous metadata version, feature toggle, or hotfix path"
  - "Data policy per environment: refresh cadence, anonymization rules, production data restrictions"
outputs:
  - "Environment matrix: structured table of all environments with type, purpose, branch, refresh cadence, and data policy"
  - "Deployment runbook: numbered execution checklist for a single deployment event covering pre-deploy, deploy, post-deploy, and rollback steps"
  - "Deployment guide: standing reference document covering promotion path, validation strategy, and Named Credential re-entry requirements"
triggers:
  - "how do I write a Salesforce deployment runbook"
  - "need an environment matrix for our sandbox topology"
  - "create a pre-deploy checklist for production deployment"
  - "what goes in a post-deploy validation checklist"
  - "how to document Named Credential re-entry steps after deploy"
  - "deployment guide template for Salesforce release process"
  - "rollback procedure template for Salesforce deployment"
  - "write the change request process for our Salesforce team"
  - "who approves what before a Salesforce deployment"
  - "document the environment ladder from dev sandbox to production"
  - "what order do we deploy the metadata types in this release"
  - "record the deploy options we actually used"
  - "define the emergency fix path so hotfixes stop skipping the ladder"
  - "build a RACI for our Salesforce release process"
  - "deploy succeeded but an old flow version is still active"
  - "our four packages deployed in the wrong order"
  - "quick deploy refused because the validation expired"
  - "the deployment stopped because a username does not exist in production"
  - "release calendar that avoids the Salesforce upgrade weekend"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# DevOps Process Documentation

Use this skill when you need to author or review Salesforce DevOps operational documents: runbooks that guide a single deployment event, environment matrices that map your sandbox topology, and deployment guides that describe standing process. Activate when a practitioner says they need a runbook, an environment matrix, documentation for a deployment, or a pre/post-deploy checklist.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Environment inventory**: collect org names, org types (Developer Edition, Developer Pro, Partial Copy, Full Copy, Production), their purpose in the promotion path, and which Git branches they align to in DevOps Center or a CLI-based workflow.
- **Most common wrong assumption**: practitioners conflate a runbook with a release plan. A runbook is a single-deployment-event execution checklist. A release plan is a project artifact covering scope, approvals, scheduling, and stakeholder communication. They are different documents with different owners and different lifecycles.
- **Platform constraints to track**: there is no Setup screen that holds a runbook, an environment matrix, or a change-request state machine — every artefact this skill produces lives outside the org, which is why it needs an owner and a review cadence written into it. UNVERIFIED (2026-09-05): the absence of a native documentation feature is an absence claim; no extracted guide asserts it and help.salesforce.com cannot be fetched from this environment. Secrets are the other constraint: on retrieve, "the consumer secret is always exported as a placeholder value, not as an encrypted secret" (api_meta.txt L24855–24856), so a retrieve → commit → deploy round trip carries a credential frame with nothing behind it. That is the single most common runbook omission — see `references/gotchas.md` Gotcha 1 for what the guide does and does not say here.

---

## Questions to Ask Before Configuring

Ask these before writing a line of the process document. Each one maps to a gotcha in
`references/gotchas.md`, and a document written without the answers reads fine and fails on its
first real release.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who can approve a refresh of this environment, and who loses work when it happens?" | The refresh is the destructive act nobody owns; a matrix row with a purpose and no owner cannot gate one, and a refresh after a rehearsal invalidates the rehearsal (Gotcha 2) | An `owner` on every environment row, and a refresh-approval row in the RACI |
| "Which states does a change pass through, and who approves each move?" | Approval that lives in an inbox cannot be reconstructed after an incident, and an undocumented emergency path is an undocumented approval bypass | The state machine with an `approver_role` per state, plus a named emergency path with a retro requirement |
| "Is this release one deployment or several, and in what order?" | Inside one deployment the Metadata API resolves dependencies itself; across several it does not — only one runs at a time and the queue is not FIFO (Gotcha 7) | A numbered `deploy_order`, each step gated on the previous deployment's `Succeeded` status |
| "What `testLevel` are we asking for, in the rehearsal and in production?" | The defaults differ by environment, so an unset level makes the rehearsal's duration meaningless as an estimate (Gotcha 10) | Two explicit test levels in the deploy contract and a real window estimate |
| "Is anything being deleted, and is it recoverable in production?" | `purgeOnDelete` is inert in production, and roll-up summary fields are purged regardless (Gotcha 12) | A rollback path stated per deleted component type, and a pre-deploy retrieve taken as the baseline |
| "Which components arrive needing a human to finish them?" | Credential secrets, Flow activation, and queue membership are post-deploy work that a Succeeded status does not cover (Gotchas 1 and 6) | A named manual-step list with owners, secret sources, and a verification with a pass criterion |
| "When is the production window, relative to the validation and to the Salesforce upgrade weekend?" | The quick-deploy licence is target-specific and expires in ten days (Gotcha 11), and an org-upgrade weekend gives any incident two candidate causes | A release calendar with the validation date inside the window and the upgrade weekend frozen |

What a proper process document adds over just doing the deployment: the release can be reconstructed
after the fact from written records rather than from memory, the person on the rollback call is
someone who agreed to be, and the next release does not rediscover the same manual steps.

---

## Core Concepts

### Runbook vs. Release Plan

A **runbook** is a single-event execution checklist tied to one deployment window. It answers "what exactly does the person doing the deployment click, enter, or verify, in what order, right now?" It is written at the task level: check sandbox refresh date, run validation, approve, deploy, enter Named Credential values, run smoke tests, confirm with stakeholders, close the window.

A **release plan** is a project artifact that answers scope, timeline, dependencies, and stakeholder communication across multiple environments and multiple deployment events. Conflating the two is the most frequent documentation failure in Salesforce DevOps.

### Environment Matrix

An environment matrix is a structured table that captures the complete state of your sandbox topology. For each environment the matrix records: org name, org type (Developer, Partial, Full), purpose (development, regression QA, UAT, staging, hotfix), branch alignment in source control, refresh cadence (monthly, quarterly, ad hoc, never), and data policy (anonymized production data, synthetic data, no production data permitted). Without this document, teams make incorrect assumptions about what is safe to do in a given sandbox.

UNVERIFIED (2026-09-05): earlier versions of this skill attributed the "maintain the matrix as a living document" requirement to Salesforce Well-Architected and to the DevOps Center Developer Guide. Neither is among the extracted guides and neither architect.salesforce.com nor developer.salesforce.com can be fetched from this environment, so the attribution is unconfirmed. What is grounded is the consequence: the environment name is the join key between the matrix, the runbook and the deploy contract, so a stale row makes every artefact that references it wrong at once.

### Deployment Guide vs. Runbook

A **deployment guide** is a standing reference document covering the team's promotion path, validation strategy, approval gates, and known manual steps that recur across every release. It is updated when the process changes. A **runbook** is a release-specific checklist derived from the deployment guide plus the specific scope of the upcoming deployment. The deployment guide is the template; the runbook is the instance.

### Named Credential and Auth Provider Manual Steps

`NamedCredential`, `ExternalCredential` and `AuthProvider` all deploy as frames. What does not survive a source-controlled round trip is the secret inside them: the guide states for `AuthProvider` that a defined consumer secret "is always exported as a placeholder value, not as an encrypted secret" (api_meta.txt L24855–24856). A secret *can* be deployed — since November 2022 `consumerSecret` goes in as plaintext (api_meta.txt L25120–25122) — but only by committing it to source control, which most teams refuse. Either way the target org ends up with a credential that authenticates against nothing until an administrator finishes it by hand, and the gap between "metadata deployed successfully" and "the integration works" is exactly that manual step. Runbooks must carry it as a numbered step with navigation path, field list, secret source and a verification callout — never as "configure credentials".


### The Deploy Contract

The single most reconstructible thing a runbook can record is the set of `deployOptions` the release
actually used. Every field below is a documented Metadata API deploy option (api_meta.txt L3088–3160);
this skill does not choose the values — `admin/change-management-and-deployment` does — it insists
they are written down before the window and verified after it.

| Option | Why the runbook records it |
|---|---|
| `checkOnly` | `true` is the validation: it verifies the results of the tests a deploy would run without committing anything (api_meta.txt L3095–3099). The runbook's validate-only step is this flag. |
| `testLevel` | One of `NoTestRun`, `RunSpecifiedTests`, `RunRelevantTests` (beta), `RunLocalTests`, `RunAllTestsInOrg` (api_meta.txt L3140–3168). Unset means two different defaults in sandbox and production. |
| `runTests` | Only applies when `testLevel` is `RunSpecifiedTests`, and that level changes coverage to 75% per class and trigger individually (api_meta.txt L3130–3160). |
| `rollbackOnError` | Defaults to `false`; must be `true` for production (api_meta.txt L3126–3130). This is the flag that decides whether a partial failure is a rollback or a `SucceededPartial`. |
| `ignoreWarnings` | When `true`, a warning is reported as success rather than treated as an error (api_meta.txt L3101–3109). Worth recording precisely because it changes what "Succeeded" means. |
| `purgeOnDelete` | Bypasses the Recycle Bin — but only in Developer Edition and sandbox orgs (api_meta.txt L3119–3123). It is why the rehearsal's rollback and production's rollback differ. |
| `singlePackage` | Whether the zip points at one package or a set (api_meta.txt L3136–3138). |

A `SucceededPartial` status is a documented outcome (api_meta.txt L3338–3352), not an anomaly. The
post-deploy gate reads the status field, not the shell exit code.

---

## Common Patterns

### Pattern 1: Runbook for a Standard Release

**When to use:** Any planned deployment to a production org or a pre-production environment where someone other than the author will execute the steps, or where a post-incident review might need to reconstruct what happened.

**How it works:**

Structure the runbook in four phases:

1. **Pre-deploy gate** — confirm sandbox refresh date is within policy, confirm the validation run passed, confirm the deployment window is approved, confirm backup or rollback path is documented, confirm Named Credential values are on hand for each target environment.
2. **Deploy execution** — record the exact deploy command or Change Set name, the user account executing the deploy, the start timestamp, and any environment-specific flags.
3. **Post-deploy validation** — run named smoke tests (links to test scripts or manual steps), verify Named Credentials are functional by testing the relevant integration endpoint, confirm Flows that were deployed are active in the expected status, confirm profile/permission set assignments are correct.
4. **Rollback decision gate** — define the go/no-go threshold, who owns the rollback call, the rollback procedure (previous metadata version, disable-and-restore, or hotfix), and the estimated rollback time.

**Why not the alternative:** A generic checklist without the four-phase structure fails because practitioners skip post-deploy credential re-entry (the most common gap) and skip the rollback decision gate until a problem has already escalated.

### Pattern 2: Environment Matrix with Data Policy Column

**When to use:** Any org where more than one sandbox exists, or where the team is onboarding new contributors who do not know what each environment is for.

**How it works:**

Build the matrix as a Markdown table with these exact columns: `Org Name | Org Type | Purpose | Branch Alignment | Refresh Cadence | Data Policy | Owner`. The data policy column must state explicitly whether production data is present, anonymized, synthetic, or prohibited — not just "no PII." Refresh cadence drives risk: a Full Copy sandbox refreshed quarterly accumulates configuration drift from production that can cause a pre-deploy validation to pass in the wrong environment context.

**Why not the alternative:** Omitting the data policy column creates a shared assumption among contributors that often turns out to be wrong, leading to test data or integration credentials from one environment being referenced in another.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single upcoming deployment to production | Author a runbook using the four-phase structure | Runbooks are event-scoped; the release plan already handled scope and approvals |
| Team has no documentation of sandbox topology | Build environment matrix first, then derive runbooks from it | Without the matrix, runbooks reference environments without context |
| Deployment includes Named Credentials or Auth Providers | Add explicit credential re-entry steps to the runbook | Metadata API does not carry secret values; omitting this step breaks integrations silently |
| Standing process is undocumented | Author a deployment guide before the next release | Deployment guide captures the reusable process; runbooks are derived from it |
| Post-incident review requested | Use the runbook as the primary reconstruction artifact | A well-kept runbook records who did what, when, and in what order |

---

## Recommended Workflow

1. **Name the artefact.** Runbook (one deployment event), environment ladder (topology), change-request
   state machine (approvals), or the whole `devops-process.yaml` that carries all three. Section 1 of
   `references/worked-examples.md` is the filled-in shape; copy it rather than inventing keys, because
   `scripts/check_devops_process_documentation.py` lints those keys.
2. **Fill the environment ladder first.** Name, type, purpose, branch, refresh cadence, data policy,
   owner — the owner is the field that makes the refresh-approval RACI row enforceable. Do not restate
   tier capacities or platform refresh intervals; cite `admin/sandbox-strategy`
   § "Type Capacities and Refresh Windows".
3. **Write the change-request state machine with an approver role per state**, plus an emergency path
   that names its approver and its retro requirement. The emergency path is the one that skips gates,
   so it is the one that most needs writing down.
4. **Derive the deploy order from the manifests, not from habit.** List the metadata types in each
   `package.xml`, decide which submission each belongs to, and state the dependency reason. Put
   deletions in `destructiveChangesPre.xml` or `destructiveChangesPost.xml` according to which side of
   the additions they must land on (api_meta.txt L4645–4660).
5. **Record the deploy contract** — see § The Deploy Contract — for the validation run, the sandbox
   rehearsal and the production run separately, because the defaults differ between them.
6. **Write the runbook as numbered steps with an owner and a pass criterion each**, in this order:
   pre-deploy retrieve (the rollback baseline), pre-deploy gates, validate-only, deploy, post-deploy
   checks, manual steps, smoke tests, rollback decision gate. The validate-only step must precede the
   deploy step — the checker enforces exactly that.
7. **Lint it before the window, not after.**
   `python3 scripts/check_devops_process_documentation.py --file devops-process.yaml --manifest-dir manifest/`
   fails on a missing environment owner, a state with no approver, a deploy before a validation, an
   invented `testLevel`, and any metadata type in a manifest that no deploy-order step claims.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Document type is clearly identified: runbook, environment matrix, or deployment guide (not a blend)
- [ ] All environments in scope are listed with type, purpose, branch alignment, refresh cadence, and data policy
- [ ] Every metadata type that requires manual post-deploy action is captured as an explicit numbered step
- [ ] Named Credential and Auth Provider re-entry steps include field-level detail, not a generic note
- [ ] Rollback path is named, owned, and time-estimated before the deployment window opens
- [ ] Pre-deploy gate includes: sandbox refresh date confirmation, validation run status, deployment window approval
- [ ] Post-deploy smoke tests are listed by name or link, not just as "run smoke tests"
- [ ] Document is stored and accessible to all participants before the deployment window
- [ ] Every environment row has an owner, not just a purpose — the refresh-approval RACI row depends on it
- [ ] Every change-request state names an approver role, and the emergency path names one too
- [ ] The validate-only step precedes the deploy step, and its target org is the one being deployed to
- [ ] `testLevel` and `rollbackOnError` are recorded explicitly for the rehearsal and the production run
- [ ] Every metadata type in every manifest is claimed by a numbered deploy-order step
- [ ] `scripts/check_devops_process_documentation.py --file devops-process.yaml --manifest-dir manifest/` exits 0

---

## Salesforce-Specific Gotchas

1. **A credential survives the deploy; its secret does not survive the retrieve** — The guide's rule is on the export side: a defined `AuthProvider` consumer secret "is always exported as a placeholder value" (api_meta.txt L24855–24856). A retrieve → commit → deploy pipeline therefore hands the target org a credential frame with a placeholder behind it, the deploy reports Succeeded, and the failure appears at the first callout. `references/gotchas.md` Gotcha 1 carries what the guide does and does not state here.

2. **Sandbox refresh invalidates prior runbook assumptions** — After a Full Copy sandbox refresh, the org configuration reverts to the production state at the time of the refresh snapshot. Runbooks authored before a refresh may reference settings, users, permission sets, or connected apps that no longer exist or have different IDs in the refreshed org. Always confirm sandbox refresh date as a pre-deploy gate item.

3. **Flow activation state is separate from Flow deployment** — Deploying a Flow through the Metadata API creates the Flow version in the target org, but whether it is active or inactive depends on the `status` field in the metadata. Teams frequently deploy Flows and then discover in production that the Flow is inactive (or worse, that an old active version is still running). Every runbook that includes Flow deployment must include a post-deploy step to verify active Flow version and version number.

4. **Environment matrices go stale silently** — Nothing in the platform pushes a notification to the matrix's readers when a sandbox is refreshed, an org type changes, or a new environment is provisioned. UNVERIFIED (2026-09-05): the notification behaviour on refresh is not described in any extracted guide, and help.salesforce.com cannot be fetched. Treat the review as the forcing function regardless: give the document a `review_cadence` and an owner, and the checker will WARN when either is missing.

5. **Conflating runbook with release plan creates accountability gaps** — If the runbook is written at release plan granularity (scope, timeline, stakeholder communication), it becomes too long to use during a deployment window and does not identify who is responsible for each action step. Runbooks must be written at execution granularity: numbered steps, single responsible person per step, expected duration, and a pass/fail outcome.
6. **A `FlowDefinition` in the package beats the `Flow`'s own `status`** — If both ship, the definition's `activeVersionNumber` wins: the guide's own example has the definition say 3, the latest flow say `Active` at 4, and version 3 active after the deploy (api_meta.txt L73925–73931). A runbook step that checks only "Active / Inactive" will pass while the wrong version runs.

7. **Four submissions do not give you four ordered deployments** — Only one deployment runs at a time, and queued ones "are not necessarily executed in the order in which they were submitted" (api_meta.txt L4117–4120). An order exists only if each submission waits for the previous one to report `Succeeded`.

8. **A username the target org does not have stops the whole deployment** — Not a per-component warning: "Salesforce displays an error, and the deployment stops" (api_meta.txt L2705–2718). A leaver deactivated between the refresh and the window is enough.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Environment matrix | Markdown table: org name, type, purpose, branch alignment, refresh cadence, data policy, owner |
| Deployment runbook | Numbered execution checklist covering pre-deploy gate, deploy execution, post-deploy validation, and rollback decision gate |
| Deployment guide | Standing reference: promotion path, validation strategy, approval gates, recurring manual steps |
| Named Credential re-entry checklist | Field-level steps for re-entering credentials in each target environment after deploy |
| `devops-process.yaml` | The machine-checkable document carrying the ladder, the change-request state machine, the deploy contract, the deploy order, the runbook and the RACI |
| Change-request record design | `Change_Request__c` field list plus the state machine and its approver roles, including the emergency path |
| Deploy contract | The recorded `deployOptions` for the validation, rehearsal and production runs |
| Release calendar | Acme-side windows aligned against the Salesforce seasonal upgrade weekends and freeze rules |
| RACI matrix | Roles, not names, for raise / approve / deploy / re-enter credentials / approve refresh / call rollback |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | Writing the document. Holds the whole Acme case-intake `devops-process.yaml` filled in — environment ladder, change-request states, deploy contract, deploy order, runbook — plus the manifests, the CLI commands, the release calendar, the RACI and the documentation-set map. |
| `references/gotchas.md` | Before booking a window, or when a deploy reported Succeeded and something is still wrong. Twelve platform behaviours with what happens / when it occurs / how to avoid, each grounded in the Metadata API guide. |
| `references/examples.md` | Two narrated cases — a credential re-entry step written properly, and a four-sandbox environment matrix — plus the runbook-as-release-plan anti-pattern and the split that fixes it. |
| `references/llm-anti-patterns.md` | Reviewing a runbook or matrix an AI assistant produced, before anyone executes it. |
| `references/well-architected.md` | Justifying the documentation effort, choosing granularity against maintenance cost, or chasing the source behind any claim in this package. |
| `templates/devops-process-documentation-template.md` | Authoring by hand, or handing a fill-in-the-blanks document to someone who will not read YAML. |
| `scripts/check_devops_process_documentation.py` | Linting `devops-process.yaml` (`--file`) and checking the deploy order against the real manifests (`--manifest-dir`). Run it in CI, not just before a window. |

---

## Related Skills

- **devops/environment-strategy** — Use when the environment topology itself needs to be designed or restructured, not just documented. This skill documents an existing topology; environment-strategy establishes it.
- **admin/change-management-and-deployment** — Use when the deployment method selection, release governance, or rollback strategy is the primary question. This skill documents the process; change-management-and-deployment governs it.
- **admin/deployment-risk-assessment** — Use when the primary need is risk scoring and pre-release risk identification before a deployment. This skill documents execution steps; deployment-risk-assessment evaluates risk.
- **devops/deployment-monitoring** — Use when the question is how to observe and alert on deployments in flight, not how to document the process.
- **admin/change-management-and-deployment** — Use when the question is which deploy option, which test level, or which deployment method to choose. That skill decides the deploy contract; this one records it and gates on it.
- **admin/sandbox-strategy** — Use for sandbox tiers, capacities, platform refresh intervals, masking and the `SandboxPostCopy` design. This skill records the ladder; sandbox-strategy sizes it.
- **admin/salesforce-release-preparation** — Use for the seasonal-release cycle: release-notes triage, Release Updates, preview opt-in and the preview refresh freeze that this skill's release calendar obeys.
- **admin/sandbox-post-refresh-automation** — Use when the environment row's post-refresh work needs to become Apex rather than a checklist item.
- **admin/configuration-workbook-authoring**, **admin/requirements-traceability-matrix**, **architect/architecture-decision-records**, **admin/uat-and-acceptance-criteria** — The other four artefacts in the documentation set; this document links to them by change-request number rather than absorbing them.
- **devops/destructive-changes-deployment** — Use for the mechanics of `destructiveChangesPre.xml` / `destructiveChangesPost.xml`; this skill decides where deletions sit in the deploy order.
- **devops/rollback-and-hotfix-strategy** — Use when the rollback technique itself is the question; this skill records which technique the runbook committed to, its owner and its time estimate.
- **devops/release-management** — Use for the release train, versioning and go/no-go governance across releases.
- **devops/pre-deployment-checklist** — Use for what belongs on the gate; this skill covers how the gate is written down and who signs it.
- **devops/post-deployment-validation** — Use for designing the post-deploy verification itself, beyond listing it as a runbook step.
- **devops/metadata-api-retrieve-deploy** — Use for the retrieve/deploy call mechanics behind the runbook's commands.

