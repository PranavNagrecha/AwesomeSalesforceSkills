# Examples — CI/CD Pipeline Architecture

## Example 1: Enterprise 5-Stage Pipeline with Full Sandbox UAT

**Scenario:** A retail financial services company with 40 Salesforce developers releasing biweekly. The org contains FSC, Apex services, and Flow automations. They have a Full Sandbox for UAT, a Partial Copy for QA, and a shared Developer Sandbox for CI.

**Problem:** The team was deploying directly from a QA sandbox to production after a single manual test pass. Two consecutive releases broke production Flows because data-volume-dependent governor limits were not caught in QA (Partial Copy only). There was no rollback plan; each incident required a 4-hour manual recovery.

**Solution:**

```
Stage 1 — CI Validation Sandbox (shared Developer Sandbox)
  Trigger: Pull request opened or updated
  Gate:
    - sf project deploy validate --test-level RunLocalTests
    - Salesforce Code Analyzer scan (PMD ruleset: security, design, errorprone)
    - Fail build if any CRITICAL or HIGH violations present
  Artifact: Deployment validation ID (stored as CI artifact for Stage 5 quick deploy)

Stage 2 — Integration / QA Sandbox (Partial Copy)
  Trigger: PR merged to sprint branch
  Gate:
    - sf project deploy start (full deploy)
    - Run curated smoke test suite (sf apex run test --classnames ...)
    - Require org-wide coverage ≥ 75%; per-class ≥ 85% for new/modified classes
  Artifact: JUnit XML test results, coverage report

Stage 3 — UAT Sandbox (Full Sandbox)
  Trigger: QA lead approves after Stage 2 gates pass
  Gate:
    - Business sign-off checklist (manual approval in CI tool)
    - Automated regression suite covering high-value process flows
    - Load test for batch Apex jobs against production data volume
  Artifact: UAT sign-off record, regression test report

Stage 4 — Staging Sandbox (Full Sandbox production mirror)
  Trigger: Release manager schedules release
  Gate:
    - sf project deploy validate against Staging (validation-only; produces fresh deployment ID)
    - CAB approval ticket referenced and linked
    - Release notes reviewed
  Artifact: Validated deployment ID (< 96 hours old before Stage 5)

Stage 5 — Production
  Trigger: Scheduled change window (CAB-approved)
  Gate:
    - sf project deploy quick --job-id <validated-ID-from-Stage-4>
    - Post-deploy smoke test (manual or automated)
    - Rollback decision point: if smoke test fails, initiate git-revert-and-redeploy runbook
```

**Why it works:** Separating QA (Partial Copy) from UAT (Full Sandbox) ensures data-volume failures surface before production. The validation-only deploy at Stage 4 consumes the deployment ID used for a quick deploy at Stage 5, reducing the production change window from ~45 minutes to ~5 minutes. The rollback runbook exists before every deploy, not after the incident.

---

## Example 2: ISV Managed Package Release Pipeline

**Scenario:** An ISV building a managed package on the Salesforce AppExchange with separate development, QA, and packaging orgs. They release new package versions quarterly with a beta period.

**Problem:** The team was building package versions manually from a developer org without a standardized CI pipeline. Package version builds occasionally included uncommitted scratch org changes, and beta installs in customer trial orgs were failing due to unresolved namespace conflicts caught too late.

**Solution:**

```
Stage 1 — Scratch Org Unit Build
  Trigger: Push to any feature branch
  Gate:
    - sfdx force:org:create (ephemeral scratch org from project-scratch-def.json)
    - sf package version create --code-coverage --installation-key ...
    - Build must succeed with zero package creation errors
    - RunLocalTests ≥ 75% code coverage (enforced during package version create)
    - PMD scan on all Apex classes (errorprone, security rulesets)
  Artifact: Package version ID (04t) if gates pass; discard scratch org

Stage 2 — QA Sandbox Package Install
  Trigger: PR merged to main branch
  Gate:
    - sf package install --package <04t-ID> in QA sandbox
    - Integration test suite runs against installed package
    - No namespace conflicts or install errors
  Artifact: Install success record, test results

Stage 3 — Beta Package Version Promotion
  Trigger: QA lead approves
  Gate:
    - sf package version promote (marks version as Released = false, available for beta install)
    - Beta install test in a fresh Partner Developer Org
    - Confirm no breaking API changes (compare with previous version metadata)
  Artifact: Beta package version record in Dev Hub

Stage 4 — AppExchange Security Review Submission
  Trigger: Product manager approval after beta testing period
  Gate:
    - Salesforce Security Review submission (external gate; pipeline waits for approval)
    - All PMD Critical and High findings resolved
  Artifact: ISV Security Review approval record

Stage 5 — Production Release (Promoted Package)
  Trigger: Security review approval + release schedule
  Gate:
    - sf package version promote (marks Released = true in Dev Hub)
    - AppExchange listing updated
    - Customer upgrade instructions published
  Artifact: Released package version on AppExchange
```

**Why it works:** Building the package version in a scratch org at Stage 1 ensures only committed source is included — no uncommitted scratch org state leaks into the package. Namespace conflict detection at Stage 2 prevents install failures in customer orgs. The AppExchange Security Review is modeled as a mandatory external gate, not an afterthought, which aligns the pipeline with the actual release blocker.

---

## Anti-Pattern: Treating the CI YAML File as the Pipeline Architecture

**What practitioners do:** A developer asks for help with "CI/CD pipeline architecture" and receives a detailed GitHub Actions workflow YAML configuration with jobs, steps, and Apex test commands. The YAML is committed and the pipeline is considered "architected."

**What goes wrong:** The YAML specifies tool-level implementation but not the pipeline architecture: there is no documented stage sequence, no defined quality gate criteria, no rollback strategy, no environment topology. When the team needs to add a UAT sandbox, no one knows where it fits. When a deployment fails in production, there is no runbook. The CI tool configuration has to be reverse-engineered to understand what the pipeline is supposed to do.

**Correct approach:** Produce the stage sequence document and quality gate specification first (this skill). Then use `devops/github-actions-for-salesforce` or the relevant CI tool skill to implement the gates as YAML. The architecture document is the source of truth; the YAML is the implementation artifact.
