---
name: release-management
description: "Use when planning, coordinating, or governing Salesforce releases: version numbering, rollback strategy, release notes, go/no-go criteria, release calendar, and sandbox preview alignment. NOT for Salesforce's own seasonal platform release (Spring/Summer/Winter) readiness — release notes triage, Release Updates, Sandbox Preview opt-in (use admin/salesforce-release-preparation); this skill governs YOUR release train, not Salesforce's. NOT for deployment mechanics (use devops/post-deployment-validation or devops/change-set-deployment)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I plan a Salesforce release and define go/no-go criteria"
  - "what is the rollback strategy if a production deployment fails"
  - "how do I version Salesforce metadata in an org-based project"
  - "how do I use quick deploy to speed up deployment night"
  - "validate the production deployment this week and quick deploy it on release night"
  - "roll back a bad Salesforce production release"
tags:
  - release-management
  - release-planning
  - rollback
  - versioning
  - devops
inputs:
  - "Deployment target (production, partial sandbox, scratch org)"
  - "List of changes in the release (components, Apex, config)"
  - "Salesforce edition and Dev Hub availability"
  - "Release calendar constraints (freeze windows, go-live date)"
outputs:
  - "Release plan document with version number, go/no-go criteria, rollback trigger definition, and smoke test checklist"
  - "Release notes template populated with changes"
  - "Post-release validation checklist"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Release Management

This skill activates when a practitioner needs to plan, coordinate, or govern a Salesforce release cycle. It covers version numbering, rollback strategy, release notes, go/no-go criteria, and release calendar alignment with Salesforce's three major upgrades per year.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine whether the project is org-based (change sets, `sf project deploy`) or artifact-based (unlocked packages, managed 2GP). Version numbering and rollback differ fundamentally between the two.
- Confirm the Salesforce upgrade schedule for the production instance on Salesforce Trust. The Metadata API Developer Guide states that Salesforce performs major service upgrades three times per year.
- Identify which environments are in scope: production, Full, Partial, and Developer sandboxes, and scratch orgs. Each has different data and metadata state implications for rollback.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Is this release org-based metadata or a package version (unlocked or managed 2GP)? | Rollback is a redeploy for org-based metadata, a lower-version install for unlocked packages, and impossible for managed 2GP (downgrade isn't allowed). | Picks the rollback mechanism before go-live instead of during the incident. | The rollback runbook names a real command that the platform supports. |
| Does the release contain Apex classes or triggers, and which test level will production run? | With no test level, production runs local tests only when the package has Apex. RunSpecifiedTests needs 75% coverage on each deployed class and trigger. | Sizes the validation window and the test list. | A validation that passes is guaranteed to be quick-deployable within 10 days. |
| When exactly will the validation run, and when is the release window? | The validated job ID expires after 10 days, and `--use-most-recent` only looks back 3 days. | Puts validation and release dates on the calendar with the job ID recorded. | Release night is a quick deploy of a known job ID, not a fresh test run. |
| Does the release include active flows, and is "Deploy processes and flows as active" enabled in production? | When the setting is off (the production default), flows deploy inactive. When it is on, deploying an active flow runs Apex tests and checks flow test coverage. | Decides whether activation is a deploy-time or post-deploy step. | No silent "flow deployed but nothing happens" incident after go-live. |
| What data does the release change, and can that be reversed? | A metadata redeploy does not reverse records written by the released automation. | Lists compensating data scripts per component. | Rollback triggers include the data clean-up step, not just the metadata step. |
| Does the release window overlap a planned Salesforce service upgrade for the instance? | A deployment running during service downtime is retried from the beginning after the service is restored. | Moves the window or accepts the longer duration up front. | The window estimate is honest and the freeze calendar avoids upgrade weekends. |

---

## Core Concepts

### Seasonal Platform Releases and Sandbox Preview

Salesforce delivers three named releases per year (for example Spring '26, Summer '26, Winter '27). Production instances upgrade on scheduled maintenance windows that Salesforce Trust publishes per instance. UNVERIFIED (2026-10-03): the order of instance waves and the exact length of the sandbox preview window are published only in Salesforce Help and the Trust site, which do not fetch; treat any "4 to 6 weeks before" figure as a planning assumption to confirm on Trust.

Practical impact: any release you deploy to production close to the upgrade weekend for your instance is high risk. Test in a sandbox that is already on the upcoming release if your deployment overlaps a platform upgrade.

### Versioning Schemes by Deployment Model

**Org-based projects** (change sets, `sf project deploy start`): the platform has no native business version number for org metadata. The `apiVersion` in a component file is the platform API version, not a release number. Teams define their own convention:
- Git tag with `vYYYY.MM.DD-N` (date plus sequence)
- Work-tracking release milestone label
- Custom object to track deployed versions

**Unlocked packages**: version numbers are `MAJOR.MINOR.PATCH.BUILD`. The build number increments only when `versionNumber` ends in the `NEXT` keyword. Without `NEXT`, a forgotten `versionNumber` update produces a version with the same number as the previous one (Salesforce DX Developer Guide, Unlocked Packaging Keywords). Every version still gets a unique `04t` subscriber package version ID. After you promote a `MAJOR.MINOR.PATCH`, you can't create more versions with that number.

**Managed 2GP packages**: same `MAJOR.MINOR.PATCH.BUILD` scheme. Patch versions are created with Salesforce CLI from source by incrementing the patch number and specifying a managed-released ancestor with the same major and minor numbers. Managed 2GP has no patch orgs. Patch versioning must be enabled by Salesforce Partner Support and is available only to packages that passed AppExchange security review (Second-Generation Managed Packaging Developer Guide, Patch Versions).

### Rollback Strategy

Salesforce has no native undo for metadata deployments. Rollback means:
1. Before deploying: retrieve and archive the current production state of every component you are deploying.
2. After a failed release: redeploy the archived version.
3. For org-based: `sf project deploy start --metadata-dir backups/<date>/unpackaged.zip --single-package`, pointing at the archive retrieved before the release.
4. For unlocked packages: installing a lower version on top of a higher version is possible, but the Salesforce DX Developer Guide says this "is not the same as a rollback, which isn't possible." Removed custom objects and fields with user data are deprecated, not deleted, on upgrade.
5. For managed 2GP: downgrading an installed package isn't allowed. The only path forward is a new, higher version.

Data changes made by the released code are not reversed by redeploying metadata. Identify data mutations in your release notes and plan compensating data fixes.

### Go/No-Go Criteria

A go/no-go gate blocks deployment unless defined criteria pass. Typical criteria:
- All Apex tests pass with at least 75% overall coverage and some coverage on every trigger (RunLocalTests or RunAllTestsInOrg), or at least 75% on each deployed class and trigger (RunSpecifiedTests or RunRelevantTests beta).
- Smoke test checklist passes in a Full sandbox that mirrors production.
- Zero open Severity 1 defects from UAT.
- `sf project deploy validate` succeeded against production within the last 10 days, which makes it eligible for quick deploy.
- Release notes reviewed and signed off by the product owner.

---

## Common Patterns

### Validation Deploy + Quick Deploy

**When to use:** Large orgs where the full Apex test run takes a long time and the release window is short.

**How it works:**
1. Run `sf project deploy validate --manifest manifest/package.xml --test-level RunLocalTests --target-org prod --async` before the window (within 10 days).
2. Record the returned job ID (`0Af...`) in the release plan.
3. On release night, run `sf project deploy quick --job-id <validationJobId> --target-org prod`. It skips the test run.
4. Monitor the NEW deploy ID that the quick deploy returns with `sf project deploy report --job-id <quickDeployId>`.

The full command sequence lives in [references/metadata-examples.md](references/metadata-examples.md).

**Why not just deploy directly:** validation is a rehearsal. If it fails, you have days to fix. If a direct deploy fails at 2am, you are in an incident.

### Freeze Window Coordination

**When to use:** Shared production org with multiple teams and competing deployment schedules.

**How it works:**
1. Publish a release calendar with named code freeze dates. Code freeze means no new feature merges to the release branch.
2. Allow only P1 and P2 hotfixes after code freeze.
3. Define the freeze period, typically 3 to 5 business days before the release window.
4. Signal freeze status in the DevOps Center pipeline or the work-tracking board.

**Rollback trigger:** define trigger conditions in writing before deployment begins. For example: "If any Apex test fails in production post-deploy, or if more than 3 Sev-1 defects are raised within 2 hours, rollback starts."

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org-based project, versioning needed | Git tag plus internal version record | No native version support; the git tag is the retrieval anchor for rollback |
| Managed 2GP, need to patch a released version | Increment the patch number, set the managed-released ancestor, create the version with Salesforce CLI | Managed 2GP has no patch orgs; patch versioning needs Partner Support enablement |
| Release overlaps the Salesforce upgrade weekend | Test in a sandbox on the new release first, or move the window | Deployments during service downtime restart from the beginning |
| Need a fast release night with a large test suite | Validate 3 to 7 days early, quick deploy on the night | Quick deploy skips tests and uses the 10-day validated job ID |
| Multiple teams sharing one production org | Coordinated release train with a shared freeze calendar | Competing deploys cause cross-reference errors and test failures |

---

## Recommended Workflow

1. Confirm the deployment model (org-based or package-based) and record the versioning convention and the rollback mechanism it allows (redeploy, lower-version install, or roll forward only).
2. Check the instance maintenance calendar on Salesforce Trust and flag any overlap between the release window and a planned upgrade.
3. Build `manifest/package.xml` and the release notes from the component list, then retrieve the pre-release backup of every listed component from production into `backups/<date>/`.
4. Run `sf project deploy validate` against production at least 3 days before go-live, record the job ID and its expiry date, and resolve every failure.
5. Run `python3 skills/devops/release-management/scripts/check_release_management.py --project-dir .` to catch NoTestRun-in-production scripts, `--use-most-recent` reliance, and destructive manifests without a backup.
6. On release night, run `sf project deploy quick --job-id <id>`, monitor the new deploy ID, then run the smoke test checklist and the flow activation step if flows deployed inactive.
7. If a rollback trigger fires, redeploy the archived backup (org-based) or follow the package path from the Rollback Strategy section, then run the compensating data scripts.

---

## Review Checklist

- [ ] Version number is defined and recorded in the git tag, release notes, or version tracking record
- [ ] Instance maintenance calendar checked against the release window
- [ ] Validation passed against production within the last 10 days and its job ID is recorded
- [ ] UAT completed with full sign-off; zero open Sev-1 defects
- [ ] Rollback archive retrieved from production and stored before deployment begins
- [ ] Flow activation plan matches the production "Deploy processes and flows as active" setting
- [ ] Post-deploy smoke test checklist executed and all checks pass
- [ ] Release notes distributed to stakeholders before go-live

---

## Salesforce-Specific Gotchas

The full write-ups, with sources, are in [references/gotchas.md](references/gotchas.md).

| Gotcha | One-line summary |
|---|---|
| Quick deploy ID | Quick deploy returns a new deploy ID; monitor that one, not the validation ID. |
| `--use-most-recent` | The flag only finds validations from the last 3 days, although the job ID is valid for 10. |
| RunSpecifiedTests coverage | Each deployed class and trigger needs 75% from the listed tests. |
| Config-only releases | Without a test level, production runs no tests when the package has no Apex. |
| Upgrade downtime | A deployment interrupted by service downtime restarts from the beginning. |
| Package rollback | Unlocked lower-version install is not a rollback; managed 2GP can't downgrade. |
| Flow activation | Production deploys flows inactive unless "Deploy processes and flows as active" is on. |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Release plan document | Version number, scope, deployment date, rollback trigger definition, go/no-go criteria sign-off |
| Release notes | Component change log, data migration steps, known issues, stakeholder communication |
| Pre-release backup manifest | package.xml listing every component being changed; used as rollback input |
| Post-deploy smoke test checklist | Ordered list of manual verifications to execute immediately after deployment |

---

## Related Skills

- devops/post-deployment-validation: validation deploy mechanics and Quick Deploy commands
- devops/change-set-deployment: org-based deployment when SFDX is not in use
- devops/continuous-integration-testing: automated test execution in CI, coverage gates
- devops/environment-strategy: sandbox strategy and environment topology decisions
