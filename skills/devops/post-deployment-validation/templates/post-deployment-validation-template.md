# Post Deployment Validation — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `post-deployment-validation`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Deployment type:** (validation deploy / quick deploy / full deploy)
- **Deployment ID:** (the ID returned by the deploy command)
- **Validation ID (if applicable):** (the checkOnly deploy ID, if using quick deploy)
- **Target org:** (alias or username)
- **Test level used:** (RunSpecifiedTests / RunLocalTests / RunAllTestsInOrg / NoTestRun)
- **Components deployed:** (list key metadata types and names)

## Pre-Deployment Baseline

- **Prior commit hash:** (git SHA of the last known-good state)
- **Pre-deployment test failures (if known):** (list any tests that were already failing)

## Post-Deployment Checks

- [ ] Deployment Status page reviewed — all components show success
- [ ] Apex test results reviewed — no new failures introduced
- [ ] Per-class code coverage meets 75% threshold for all package classes
- [ ] Key functional changes verified in the org
- [ ] New fields/objects accessible via permission sets/profiles
- [ ] Debug logs checked for unexpected errors after representative transactions

## Rollback Plan

- **Rollback method:** (re-deploy prior commit / retrieve-based snapshot / manual revert)
- **Rollback command:**

```bash
# Example: re-deploy prior version from source control
git checkout <prior-commit-hash> -- force-app/
sf project deploy start --source-dir force-app --target-org <alias> --test-level RunLocalTests
```

- **Dependencies to roll back in order:** (list any schema changes that must be reverted alongside code)

## Notes

Record any deviations from the standard pattern and why.
