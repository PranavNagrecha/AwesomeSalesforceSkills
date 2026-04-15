# CI/CD Pipeline Architecture — Work Template

Use this template when designing, reviewing, or documenting a Salesforce CI/CD pipeline.

---

## Scope

**Skill:** `architect/ci-cd-pipeline-architecture`

**Request summary:** (fill in what the user asked for — pipeline design, pipeline review, rollback strategy, gate specification, etc.)

---

## Context Gathered

Answer the Before Starting questions from SKILL.md:

- **Deployment model:** [ ] Org-based (Metadata API / SFDX deploy)  [ ] Unlocked packages  [ ] Managed packages
- **Team size:** ___  **Release cadence:** ___
- **Available sandbox types:** (list: Developer / Developer Pro / Partial Copy / Full / Scratch Orgs)
- **CI tool in use or under evaluation:** ___
- **Regulatory constraints:** [ ] SOX  [ ] HIPAA  [ ] Internal CAB  [ ] None
- **DevOps Center in use:** [ ] Yes  [ ] No — if yes, confirm stage count will not exceed 15

---

## Pipeline Stage Sequence

| Stage # | Stage Name | Environment Type | Sandbox Name | Trigger | Promotion Owner |
|---------|------------|-----------------|--------------|---------|-----------------|
| 1 | CI Validation | Developer Sandbox / Scratch Org | | PR opened or updated | Automated (CI job) |
| 2 | Integration / QA | | | PR merged to sprint branch | QA lead |
| 3 | UAT | Full Sandbox | | QA gate passes | Business sign-off |
| 4 | Staging | Full Sandbox (production mirror) | | UAT sign-off | Release manager |
| 5 | Production | Production | | CAB approval + change window | Release manager |

*Add or remove rows to match the project topology. Remove UAT and Staging rows for the lightweight 3-stage pattern.*

---

## Quality Gate Specification

For each stage transition, complete the following:

### Stage 1 → Stage 2 Gate

| Check | Tool | Threshold / Criteria | Artifact Produced |
|-------|------|---------------------|-------------------|
| Static analysis scan | Salesforce Code Analyzer (PMD) | Zero CRITICAL or HIGH violations | Scan report (JSON or HTML) |
| Validation-only deploy | `sf project deploy validate` | Deploy succeeds, no component errors | Deployment validation ID |
| Apex test execution | `--test-level RunLocalTests` | Org-wide coverage ≥ 75%; modified classes ≥ 85% | JUnit XML test results |

### Stage 2 → Stage 3 Gate

| Check | Tool | Threshold / Criteria | Artifact Produced |
|-------|------|---------------------|-------------------|
| Full deployment | `sf project deploy start` | Zero deploy errors | Deployment result |
| Smoke test suite | (define suite name) | All tests pass | Test result report |
| Coverage check | CI script parsing deploy results | Org-wide ≥ 75% | Coverage report |

### Stage 3 → Stage 4 Gate (UAT → Staging)

| Check | Tool | Threshold / Criteria | Artifact Produced |
|-------|------|---------------------|-------------------|
| Business sign-off | Manual approval (CI tool gate or PR review) | Sign-off checklist complete | Approval record |
| Regression test suite | (define suite name) | All regression tests pass | Regression test report |
| Performance / load test | (if applicable) | Governor limits not exceeded at production data volume | Load test results |

### Stage 4 → Stage 5 Gate (Staging → Production)

| Check | Tool | Threshold / Criteria | Artifact Produced |
|-------|------|---------------------|-------------------|
| Validation-only deploy to Production (or Staging mirror) | `sf project deploy validate` | Deploy succeeds (produces quick deploy ID) | Validated deployment ID (note: expires in 96 hours) |
| CAB / change control approval | Manual (linked ticket) | Approval ticket number: ___ | Change control record |
| Release notes review | Manual | Release notes published | Release notes document |

---

## Rollback Strategy

Document the recovery procedure for each stage:

| Stage | Failure Scenario | Recovery Procedure | Estimated Recovery Time |
|-------|-----------------|-------------------|------------------------|
| CI Validation | Validation deploy fails | Fix in feature branch; re-push PR | Minutes |
| QA | Full deploy fails | Fix in sprint branch; re-deploy | 15–30 min |
| UAT | Regression test failure | Revert to last passing commit; re-deploy to UAT | 30–60 min |
| Staging | Validation conflict detected | Resolve merge conflict in Git; re-run Stage 4 gate | 30–60 min |
| Production | Post-deploy smoke test fails | Initiate git-revert-and-redeploy runbook; deploy previous state | 45–90 min |

**Declarative metadata rollback reminder:** There is no native rollback for Flows, Page Layouts, or Custom Objects. Recovery always requires a git revert followed by a fresh deployment. Document the specific git commands in the runbook before each production deploy.

**Quick deploy note:** The Production quick deploy ID expires 96 hours after the Stage 4 validation. If the change window is more than 4 days after the Stage 4 gate, re-run validation before the production deploy.

---

## Environment Topology Diagram

```
[Feature Branch]
      |
      | PR opened
      v
[CI Validation Sandbox / Scratch Org]  ← Stage 1 gate (PMD scan + validation-only deploy + RunLocalTests)
      |
      | PR merged
      v
[QA / Integration Sandbox]  ← Stage 2 gate (full deploy + smoke tests + coverage check)
      |
      | QA lead approves
      v
[UAT Sandbox (Full)]  ← Stage 3 gate (business sign-off + regression suite)
      |
      | Release manager schedules
      v
[Staging Sandbox (Full, production mirror)]  ← Stage 4 gate (validation-only deploy + CAB approval)
      |
      | Change window + quick deploy
      v
[Production]
```

*Adjust to match actual environment topology. For unlocked packages, replace environments with package version stages.*

---

## CI Tool Responsibilities

| Concern | CI Tool | DevOps Center | Manual |
|---------|---------|---------------|--------|
| PMD / Code Analyzer scan | X | | |
| Validation-only deploy (Stage 1) | X | | |
| Full deploy (Stage 2+) | X | X (if DC) | |
| Test execution and result parsing | X | | |
| Coverage threshold enforcement | X | | |
| Work item and bundle promotion | | X (if DC) | |
| CAB approval gate | | | X |
| Business sign-off gate | | | X |

---

## Pipeline Contract (for team documentation)

- **Single promotion tool per org:** All production changes flow through this pipeline. Change Set deployments are prohibited for components managed by this pipeline.
- **Gate bypass policy:** Gates may NOT be bypassed except by the Release Manager with written justification recorded in the incident/change ticket.
- **Branch protection:** The `main` branch requires a passing CI gate (Stage 1) and at least 1 reviewer approval before merge.
- **Ownership:** Stage gates 1–2 are owned by the DevOps engineer. Stages 3–5 require business and release manager sign-off.

---

## Notes and Deviations

Record any deviations from the standard pattern and why:

- (e.g., "Stage 4 Staging sandbox is not available; CAB approval replaces staging validation-only deploy")
- (e.g., "DevOps Center used for Stages 2–5; external GitHub Actions job handles Stage 1 quality gates")
