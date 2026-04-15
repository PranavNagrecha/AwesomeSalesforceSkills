---
name: ci-cd-pipeline-architecture
description: "Use when designing or reviewing the end-to-end stage sequence, promotion strategy, and quality gates for a Salesforce CI/CD pipeline. Trigger keywords: pipeline stages, promotion strategy, quality gate, deployment gate, CI validation sandbox, staging environment, pipeline design, release strategy, rollback strategy, environment topology. NOT for configuring an individual CI tool (GitHub Actions, GitLab CI, Jenkins) — use devops/github-actions-for-salesforce or devops/gitlab-ci-for-salesforce. NOT for Apex test configuration in CI — use devops/continuous-integration-testing. NOT for DevOps Center setup or work item promotion — use devops/devops-center-pipeline."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "how many pipeline stages should we have between feature branch and production"
  - "what quality gates do we need before promoting metadata to a full sandbox"
  - "our release pipeline has no gate between QA and production and we keep breaking prod"
  - "what is the right environment topology for a Salesforce CI/CD pipeline"
  - "when should we use a validation-only deployment versus a full deployment in the pipeline"
  - "we need a rollback strategy for declarative metadata after a bad production deployment"
  - "how do we enforce PMD or Code Analyzer rules as a mandatory pipeline gate"
tags:
  - ci-cd
  - pipeline-architecture
  - deployment-strategy
  - quality-gates
  - devops
  - release-management
  - environment-topology
  - salesforce-dx
inputs:
  - "Team size and release cadence (weekly sprints, monthly releases, continuous delivery)"
  - "Org topology: number and types of sandboxes available (Developer, Partial Copy, Full)"
  - "Whether the project uses unlocked packages, managed packages, or org-based (metadata API) deployment"
  - "Existing CI tool in use or under evaluation (GitHub Actions, GitLab CI, Jenkins, Azure DevOps, Copado, DevOps Center)"
  - "Regulatory or change-management requirements (CAB approval, SOX, change freeze windows)"
outputs:
  - "Stage sequence diagram with environment-to-stage mapping and promotion triggers"
  - "Quality gate specification per stage (test thresholds, static analysis rules, validation mode)"
  - "Promotion strategy decision (manual gate vs. automated promotion conditions)"
  - "Rollback and forward-fix strategy for declarative and programmatic metadata"
  - "Monitoring and observability strategy for deployment health"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# CI/CD Pipeline Architecture

Use this skill when the work is to design, assess, or improve the pipeline itself — the stage sequence, environment topology, promotion rules, and mandatory quality gates — rather than configuring a specific CI tool or running individual deployments. A well-designed pipeline separates concerns: each stage has one job, each gate enforces one class of risk, and promotion is deterministic.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Deployment model:** Is the project org-based (Metadata API / SFDX deploy), unlocked packages, or managed packages? The promotion mechanism and rollback options differ fundamentally across these three.
- **Sandbox inventory:** Which sandbox types are available? Partial Copy and Full sandboxes support complete integration and regression testing; Developer sandboxes do not reliably reflect production data volumes or governor limits.
- **Regulatory constraints:** Does the org fall under SOX, HIPAA, or an internal CAB process? These impose mandatory human approval gates that cannot be automated away.
- **Most common wrong assumption:** That a CI tool configuration *is* a pipeline architecture. A CI YAML file is one implementation of a pipeline; the architecture decision is the stage sequence, gate logic, and promotion strategy — tool-agnostic.
- **Platform limits in play:** Apex test jobs time out at 10 minutes per test class. Validation-only deployments consume a deployment ID but do not alter org state; they are the correct mechanism for CI gate checks on sandboxes that cannot be modified mid-sprint.

---

## Core Concepts

### 1. Stage Sequence and Environment Topology

A Salesforce pipeline is a directed sequence of environments, each representing a higher level of change risk. The canonical stage sequence for an enterprise org-based deployment is:

```
Feature Branch
  → CI Validation Sandbox (read-only validation-only deploy + Apex tests)
    → Integration/QA Sandbox (full deploy, regression tests)
      → Staging / Full Sandbox (UAT, performance validation, final sign-off)
        → Production
```

DevOps Center supports a maximum of **15 pipeline stages per pipeline** (as documented in the DevOps Center Setup and Administration Guide). Pipelines with more than 15 stages must use a CLI-driven or third-party tool (Copado, Flosum, AutoRABIT) for the overflow stages.

Unlocked package pipelines replace environment promotion with version-controlled package versions; the stage sequence shifts to: `scratch org build → CI package version build → QA package install → staging package install → production package install`. The quality gate logic is identical; only the promotion artifact changes.

### 2. Quality Gates

A quality gate is a mandatory, automated check that must pass before metadata is promoted to the next stage. Gates are classified by type:

| Gate Type | Tool | Stage |
|---|---|---|
| Static analysis (PMD / Salesforce Code Analyzer) | External CI tool (not DevOps Center) | Feature Branch → CI |
| Validation-only deployment | `sf project deploy validate` | Feature Branch → CI |
| Apex test threshold (org-wide coverage ≥ 75%) | CI job parsing deployment results | CI → QA |
| Per-class coverage threshold (configurable ≥ 85% recommended) | Custom CI script | CI → QA |
| Regression test suite | CI job or Copado test automation | QA → Staging |
| Human approval / CAB | Pipeline tool gate or PR review | Staging → Production |

**DevOps Center does not provide custom quality gate configuration, code scanning, or test threshold enforcement.** These must be layered via GitHub Actions, GitLab CI, Jenkins, or a specialist DevOps tool. DevOps Center's built-in promotion check is limited to conflict detection and merge status.

### 3. Validation-Only Deployments as CI Gates

`sf project deploy validate` (or the legacy `sfdx force:source:deploy --checkonly`) deploys metadata and runs Apex tests against the target org without persisting any changes. It consumes a deployment ID that can later be used for a quick deploy (fast promotion). This makes it the correct mechanism for:

- CI gate checks on shared sandboxes that must not be modified mid-sprint
- Pre-production validation against a production-equivalent Full Sandbox
- SOX evidence of tested deployment packages before the change window

The validation job runs within the same Apex test timeout constraints as a real deployment. A single Apex test class that exceeds **10 minutes** will cause the validation to fail with a timeout error, not a test failure — the distinction matters for error handling in pipeline scripts.

### 4. Rollback Strategy

Salesforce does **not** provide a native rollback mechanism for declarative metadata (Flows, Page Layouts, Custom Objects, Profiles). Once a destructive change is deployed, it cannot be undone via the platform. The only rollback mechanisms are:

- **Git revert + re-deploy:** Revert the offending commit and deploy the reverted state. Valid for additive metadata changes.
- **Destructive changes package:** Manually construct a `destructiveChanges.xml` to remove the bad component. Required when the bad change added metadata that must now be removed.
- **Forward fix:** For Apex classes and LWC where a partial rollback would break dependent components, a forward fix commit is often faster and safer than a destructive rollback.
- **Sandbox restore (Full Sandbox only):** Salesforce allows a Full Sandbox to be refreshed from production, effectively rolling back to the production state. This is destructive to all sandbox-only changes and should be a last resort.

For unlocked packages, rollback is a package version install of the previous released version — cleaner but still requires a deployment window.

---

## Common Patterns

### Pattern 1: Linear 5-Stage Enterprise Pipeline

**When to use:** Mid-to-large enterprise teams with 5–50 developers, weekly or biweekly releases, and a Full Sandbox available for UAT.

**How it works:**

```
Stage 1: CI Validation (Developer Sandbox or scratch org)
  Gate: PMD scan (zero critical violations), validation-only deploy, RunLocalTests ≥ 75% org coverage
Stage 2: Integration / QA (Developer Pro or Partial Copy Sandbox)
  Gate: Full deploy, smoke test suite passes, no open P1 defects
Stage 3: UAT (Full Sandbox — production data copy)
  Gate: Business sign-off, regression suite passes, performance benchmark passes
Stage 4: Staging (Full Sandbox configured as production mirror)
  Gate: Validation-only deploy to production confirms no last-minute conflicts; CAB approval
Stage 5: Production
  Gate: Scheduled change window; quick deploy using previously validated deployment ID
```

Each stage has exactly one promotion owner: an automated CI job for stages 1–2, a QA lead for stage 3, a release manager for stages 4–5.

**Why not fewer stages:** Collapsing QA and UAT onto one sandbox means business stakeholders are testing on an environment that changes under them mid-sprint. Separate sandboxes isolate risk.

### Pattern 2: Lightweight 3-Stage Pipeline (Small Team or Admin-Led)

**When to use:** Small teams (1–5 contributors), admin-led delivery, no dedicated QA sandbox budget, Agile sprints with low change volume.

**How it works:**

```
Stage 1: CI Validation (shared Developer Sandbox or scratch org)
  Gate: Validation-only deploy, RunLocalTests pass, basic Code Analyzer scan
Stage 2: QA/UAT (Partial Copy or Developer Sandbox)
  Gate: Human tester sign-off, full deploy passes
Stage 3: Production
  Gate: CAB approval or PR approval; deploy in change window
```

This pattern sacrifices performance testing and staging but is appropriate when the risk profile is low and sandbox cost is a constraint.

**Why not go to 2 stages:** Deploying directly from CI to production without a human-tested environment is appropriate only for non-customer-facing configuration with complete automated test coverage. Most Salesforce orgs do not meet this bar.

### Pattern 3: Package-Based (Unlocked Package) Pipeline

**When to use:** ISV or enterprise teams adopting modular packaging, multiple independently releasable components, or teams that need atomic rollback.

**How it works:**

```
Stage 1: Scratch Org Build + Unit Tests
  Gate: Package version build succeeds, all unit tests pass, PMD scan clean
Stage 2: QA Package Install (Developer Sandbox)
  Gate: Package installs cleanly, integration tests pass
Stage 3: Staging Package Install (Full Sandbox)
  Gate: All managed dependencies resolve, regression suite passes
Stage 4: Production Install
  Gate: Scheduled window, installation script tested in staging
```

Promotion artifact is a package version (04t ID), not a metadata zip. This makes the promotion immutable and auditable. The tradeoff is that package dependency management adds complexity — circular dependencies and namespace conflicts must be caught at Stage 1.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Team has no Full Sandbox | 3-stage pipeline with Partial Copy for QA | Full Sandbox refresh cost is high; Partial Copy covers most regression risk |
| SOX or CAB requirement | 5-stage with mandatory human gate at Staging → Production | Automated pipelines cannot satisfy change control evidence requirements without a documented approval step |
| ISV / managed package release | Package-based pipeline with scratch org as Stage 1 | Managed packages require namespace isolation; scratch orgs provide clean slate for each build |
| Declarative-only changes (admin team) | 3-stage pipeline, DevOps Center for promotion | DevOps Center's GUI-driven promotion is appropriate for metadata-only change management; no code scanning needed |
| Multiple release trains (feature teams) | Separate pipelines per train converging at a shared staging sandbox | Prevents long-lived feature branches from blocking each other; converge at staging for integration |
| High-frequency releases (> 2/week) | Trunk-based development with automated CI gate; validation-only deploys on every PR | Long-lived branches with infrequent merges create integration debt; trunk-based development with quick deploys reduces the integration risk per release |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing a Salesforce CI/CD pipeline:

1. **Establish the deployment model.** Confirm whether the project uses org-based deployment (Metadata API / SFDX), unlocked packages, or managed packages. The stage sequence and rollback options differ fundamentally. If the model is undecided, use decision guidance above and the `devops/devops-center-pipeline` skill for DevOps Center-specific implementation.

2. **Map environments to stages.** List all available sandbox types. Assign each sandbox a stage and a single promotion owner. Confirm that the Full Sandbox (if any) is reserved for staging or UAT — not used as a developer integration point. Document which orgs are shared vs. dedicated.

3. **Define quality gates per stage transition.** For each stage boundary, specify: (a) the automated checks that must pass (test level, coverage threshold, static analysis rule set), (b) the artifact produced (validation deployment ID, test result JUnit XML, scan report), and (c) whether a human approval gate is required. Align with any regulatory requirements before finalizing.

4. **Design the rollback and forward-fix strategy.** For each stage, document: what happens if a deployment fails mid-promotion, what the recovery procedure is, and who is responsible. Confirm whether a quick deploy (reusing a validation ID) is in the runbook for the Production stage. Document that declarative metadata has no native rollback and that git revert + redeploy is the recovery mechanism.

5. **Identify CI tool responsibilities.** Separate what the pipeline architecture requires (gates, thresholds, promotion rules) from what a specific CI tool will implement. Use `devops/github-actions-for-salesforce`, `devops/gitlab-ci-for-salesforce`, or `devops/continuous-integration-testing` for tool-specific implementation. If DevOps Center is in use, document its limitations (no custom quality gates, no code scanning) and layer external tooling as needed.

6. **Validate the pipeline design against platform limits.** Check: DevOps Center pipeline stage count ≤ 15; Apex test classes do not individually exceed 10 minutes (or document the timeout handling); destructive changes are tested on a staging sandbox before production; metadata coverage includes all component types in the release.

7. **Document and socialize the pipeline contract.** Record the stage sequence, gate definitions, and promotion owners in a runbook or ADR. Ensure all team members understand what can and cannot be automated. Review the pipeline design against the Well-Architected Operational Excellence pillar before finalizing.

---

## Review Checklist

Run through these before marking pipeline design work complete:

- [ ] Each stage has exactly one promotion owner and one unambiguous gate definition
- [ ] Validation-only deploy is used for CI gate checks (not a full deploy to shared sandboxes)
- [ ] Apex test coverage threshold is specified explicitly (recommend ≥ 75% org-wide, ≥ 85% per class for new code)
- [ ] Static analysis (Code Analyzer / PMD) is configured as a gate at the feature branch → CI transition
- [ ] Rollback strategy for declarative metadata is documented (git revert + redeploy or destructive changes package)
- [ ] DevOps Center stage count confirmed ≤ 15 if DevOps Center is the promotion tool
- [ ] Human approval gate is present before Production for SOX/CAB environments
- [ ] Unlocked package pipeline uses a scratch org for Stage 1 (not a shared sandbox)
- [ ] Quick deploy runbook exists for the Production stage (reuses validated deployment ID)
- [ ] Pipeline design has been reviewed against Well-Architected Operational Excellence pillar

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **No native rollback for declarative metadata** — Once a Flow, Page Layout, or Custom Object change is deployed to production, Salesforce has no "undo deployment" function. A rollback requires a git revert followed by a fresh deployment, which itself consumes a deployment slot and test run time. Teams that discover this mid-incident waste hours looking for a rollback button that does not exist. Include explicit rollback runbooks in every pipeline design.

2. **Apex test 10-minute timeout causes misleading pipeline failures** — A single Apex test class that runs longer than 10 minutes causes the deployment (or validation-only deploy) to fail with a timeout error, not a test failure assertion. CI scripts that parse test results looking for `<testsuites>` failures will miss this and may incorrectly mark the gate as passed. Add explicit timeout monitoring in pipeline scripts and split large test classes before the pipeline matures.

3. **DevOps Center max 15 pipeline stages** — DevOps Center enforces a hard limit of 15 stages per pipeline (per the DevOps Center Setup and Administration Guide). Orgs that grow beyond this (e.g., regulated orgs with 4+ UAT sandboxes, regional staging environments, a shared services stage) must either consolidate stages or move overflow stages to a CLI-based pipeline. Plan the stage topology within this limit from the start; retrofitting is costly.

4. **Quick deploy window expires after 4 days** — A validation-only deployment produces a deployment ID that can be used for a quick deploy (skipping test re-execution), but this ID expires after **96 hours**. If a CAB approval or release window falls outside that window, the full validation must be re-run. Pipeline runbooks must account for this when scheduling change windows relative to the last validation job.

5. **Partial Copy sandbox data is not production-equivalent** — Integration and regression tests that pass on a Partial Copy sandbox may fail on a Full Sandbox or production because Partial Copy only contains a representative data sample, not full data volume. Governor limit failures (SOQL rows, heap size) caused by data volume will not surface until the Full Sandbox stage. Never use a Partial Copy sandbox as the sole pre-production gate for data-intensive changes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Stage sequence diagram | Visual or table showing environment-to-stage mapping, promotion triggers, and gate types per transition |
| Quality gate specification | Per-stage table of automated checks, thresholds, and artifacts required to pass |
| Rollback runbook | Stage-specific documented recovery procedures for deployment failures |
| Pipeline topology decision record | ADR documenting why this stage count and gate design was chosen over alternatives |

---

## Related Skills

- `devops/github-actions-for-salesforce` — Use when implementing CI quality gates in GitHub Actions (YAML workflow configuration, JWT auth, test threshold enforcement)
- `devops/gitlab-ci-for-salesforce` — Use when implementing the same gates in GitLab CI
- `devops/continuous-integration-testing` — Use when configuring Apex test levels, coverage thresholds, and JUnit result parsing within a CI job
- `devops/devops-center-pipeline` — Use when the promotion tool is DevOps Center (GUI-driven work item and bundle promotion)
- `devops/environment-specific-value-injection` — Use when pipeline stages require different configuration values per environment (Named Credentials, Custom Metadata, Custom Settings)
- `architect/well-architected-review` — Use to formally assess an existing pipeline against the Well-Architected Operational Excellence and Reliability pillars
- `architect/metadata-coverage-and-dependencies` — Use when determining which metadata types to include in each stage's deployment package
