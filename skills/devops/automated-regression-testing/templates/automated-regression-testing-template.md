# Automated Regression Testing — Work Template

Use this template when building or evaluating a Salesforce UI regression testing strategy.

## Scope

**Skill:** `automated-regression-testing`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **UI technology stack:** [ ] LWC-dominant [ ] Aura-dominant [ ] Visualforce [ ] Hybrid (specify ratio: ___)
- **Shadow DOM mode:** [ ] Native Shadow DOM [ ] Synthetic Shadow (legacy) [ ] Unknown — check Setup > Session Settings
- **Existing automation tool:** [ ] None [ ] UTAM [ ] Provar [ ] Selenium (no UTAM) [ ] Playwright [ ] Copado Robotic Testing [ ] Other: ___
- **CI/CD platform:** [ ] GitHub Actions [ ] GitLab CI [ ] Jenkins [ ] Azure DevOps [ ] Bitbucket Pipelines [ ] Other: ___
- **Salesforce edition:** [ ] Enterprise [ ] Unlimited [ ] Developer [ ] Other: ___
- **Managed packages installed:** [ ] None [ ] List: ___
- **Next Salesforce release date:** ___ (check https://status.salesforce.com for release calendar)

## Critical Business Processes for Regression Coverage

List the 5-10 highest-priority business processes that must be regression-tested:

| # | Business Process | UI Pages Involved | Automation Priority | Owner |
|---|---|---|---|---|
| 1 | ___ | ___ | [ ] P0 [ ] P1 [ ] P2 | ___ |
| 2 | ___ | ___ | [ ] P0 [ ] P1 [ ] P2 | ___ |
| 3 | ___ | ___ | [ ] P0 [ ] P1 [ ] P2 | ___ |
| 4 | ___ | ___ | [ ] P0 [ ] P1 [ ] P2 | ___ |
| 5 | ___ | ___ | [ ] P0 [ ] P1 [ ] P2 | ___ |

## Framework Selection

**Selected framework:** ___
**Rationale:** (reference Decision Guidance table from SKILL.md)

## Page Object Inventory

| Page Object Name | Component / Page | Source | Status |
|---|---|---|---|
| ___ | ___ | [ ] UTAM pre-built [ ] Custom UTAM JSON [ ] Provar auto-generated | [ ] Draft [ ] Tested [ ] Stable |
| ___ | ___ | [ ] UTAM pre-built [ ] Custom UTAM JSON [ ] Provar auto-generated | [ ] Draft [ ] Tested [ ] Stable |

## Pre-Release Regression Schedule

| Release | Sandbox Signup Date | Preview Window Start | Nightly Run Start | Triage Deadline | GA Date |
|---|---|---|---|---|---|
| ___ '26 | ___ | ___ | ___ | ___ | ___ |

## CI Pipeline Configuration

**Pipeline file location:** ___
**Execution mode:** [ ] Headless Chrome [ ] Headed with screenshots [ ] Both
**Parallel slots:** ___ (ensure matching number of automation user accounts)
**JUnit output path:** ___
**Failure notification channel:** ___

## Checklist

- [ ] Page objects exist for every screen in the critical regression path
- [ ] Shadow DOM traversal is handled by framework, not inline JavaScript
- [ ] Tests produce JUnit XML output for CI consumption
- [ ] Headless browser execution confirmed working
- [ ] Pre-release sandbox regression schedule documented and calendar-blocked
- [ ] Test data setup is independent (API-based, not dependent on existing records)
- [ ] Flaky test quarantine process exists
- [ ] Automation user accounts provisioned (one per parallel execution slot)
- [ ] Sandbox refresh runbook includes re-provisioning automation credentials
- [ ] UTAM page object versions pinned to match target org Salesforce release

## Notes

Record any deviations from the standard patterns and why.
