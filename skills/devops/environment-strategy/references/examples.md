# Examples — Environment Strategy

## Example 1: ISV / AppExchange Team Moving to Source-Driven Development

**Context:** A 12-person ISV team builds a managed package. They currently share two Developer sandboxes and promote via change sets. They are adopting Salesforce CLI and want to move to a source-driven CI/CD pipeline with GitHub Actions.

**Problem:** Their existing topology gives them one shared sandbox for development and one for QA. Both are bottlenecks — only one developer can deploy at a time without stepping on others, and the QA sandbox is frequently broken by incomplete feature work pushed from development. They have no automated test gate.

**Solution:**

```yaml
# Environment matrix for ISV team post-migration

stages:
  ci_per_pr:
    type: scratch-org
    purpose: Isolated unit test run per pull request
    data: empty (scripted seed via apex anonymous or SFDX plan)
    source_tracked: true
    lifetime: 7 days (deleted after CI run)
    branch: feature/* (created on PR open, deleted on PR close)

  developer_local:
    type: scratch-org
    purpose: Individual developer sandbox
    source_tracked: true
    lifetime: 30 days
    branch: feature/* (one per developer workstream)

  integration:
    type: developer-pro-sandbox
    purpose: Shared merge target after PR approval
    source_tracked: true (CLI flag)
    refresh: on demand after major integration milestones
    branch: main

  uat:
    type: partial-copy-sandbox
    purpose: QA and stakeholder review with sample data
    source_tracked: false
    refresh: every sprint (5-day minimum enforced by platform)
    branch: release/*

  pre_production:
    type: full-sandbox
    purpose: Final regression before managed package release
    source_tracked: false
    refresh: once per release cycle (29-day minimum)
    branch: release/*
```

**Why it works:** Scratch orgs eliminate the shared-sandbox bottleneck for development and CI. Every PR gets a clean, isolated test environment. The Developer Pro sandbox becomes the stable integration target that only receives merged, tested code. The Partial Copy sandbox provides the QA team a realistic data set without exposing full production data volume. The Full sandbox is reserved for pre-release regression — the only stage that actually needs production-level parity.

---

## Example 2: Enterprise Team on Gitflow Without SFDX Adoption

**Context:** A 30-person enterprise team manages a heavily customized Salesforce org. Multiple workstreams run in parallel (Sales Cloud enhancements, Service Cloud features, integration work). The org uses Experience Cloud and several AppExchange packages that do not reliably deploy into scratch orgs. Leadership wants faster releases without destabilizing the current topology.

**Problem:** All developers share a single Partial Copy sandbox for development and a Full sandbox for UAT. Every deployment to the Partial Copy sandbox overwrites other teams' in-progress work. The Full sandbox refresh window (29-day minimum) means UAT always runs against stale data. There is no environment for integration testing between team merges.

**Solution:**

```
Topology (sandbox-only, no scratch orgs):

  workstream-a-dev    Developer Pro Sandbox   Sales Cloud team isolated dev
  workstream-b-dev    Developer Pro Sandbox   Service Cloud team isolated dev
  workstream-c-dev    Developer Sandbox       Integration team isolated dev

  integration         Developer Pro Sandbox   Shared merge target after each workstream review
                                              Refreshed from production each sprint start
                                              Source tracking enabled via CLI

  uat                 Partial Copy Sandbox    Stakeholder UAT with sample data
                                              5-day minimum refresh, owned by Release Manager

  performance         Full Sandbox            Load testing only — not used for UAT
                                              29-day refresh, refreshed only for performance cycles

  pre-production      Full Sandbox            Final regression and cutover rehearsal
                                              Refreshed at start of each major release cycle
```

**Why it works:** Dedicating a Developer Pro sandbox per workstream eliminates the deployment collision problem. The integration sandbox serves as the gating environment where all workstreams merge before anything reaches UAT — replicating the role a Git integration branch plays in a source-driven model. Separating performance testing from UAT means the Full sandbox refresh window does not block UAT progress. The pre-production sandbox is reserved for genuine rehearsal, not routine testing.

---

## Anti-Pattern: Using a Full Sandbox for Developer Unit Testing

**What practitioners do:** Because a Full sandbox has the highest production parity, teams assume it is the "safest" place to test everything — including individual developer unit tests and CI runs.

**What goes wrong:** Full sandbox refresh is limited to every 29 days. Developer unit tests should run constantly — on every commit, on every PR, multiple times per day. A Full sandbox used for CI becomes a scarce, shared resource. Test runs step on each other. The sandbox cannot be refreshed to clean state between CI runs. Developers start treating the Full sandbox as their personal environment, which causes data and metadata drift that is impossible to trace. Worst case: an accidental `deleteAllData` in a test class wipes shared test data that other teams depend on.

**Correct approach:** Unit tests and CI runs belong in scratch orgs. Scratch orgs are created fresh per run, cost nothing extra (within Dev Hub limits), are destroyed after the run, and never accumulate drift. Reserve Full sandboxes exclusively for performance testing and pre-production regression — workloads that genuinely require full production data volume and cannot be satisfied by a Partial Copy or scratch org.
