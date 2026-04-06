# Deployment Error Troubleshooting — Work Template

Use this template when diagnosing and resolving a failed Salesforce metadata deployment.

## Scope

**Skill:** `deployment-error-troubleshooting`

**Request summary:** (fill in what the user asked for)

## Error Capture

Record the deployment error details from `componentFailures`:

| # | Component Type | Full Name | Problem | Problem Type |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

**Deployment method:** (sf CLI / change set / Metadata API / DevOps Center)
**Target org type:** (production / sandbox / scratch org)
**Test level used:** (NoTestRun / RunSpecifiedTests / RunLocalTests / RunAllTestsInOrg)

## Error Classification

**Category:** (dependency compilation / missing reference / coverage failure / API version mismatch / partial deploy / other)

**Root cause:** (describe the specific root cause based on componentFailures analysis)

## Resolution Plan

1. (step to fix the root cause)
2. (step to validate the fix with a dry run)
3. (step to re-deploy the full package)
4. (step to verify in the target org)

## Checklist

- [ ] Full `componentFailures` array was read
- [ ] Error category was correctly identified
- [ ] Root cause was fixed in the correct location (source project vs. target org)
- [ ] A checkOnly/dry-run deploy confirmed the fix
- [ ] The full package was re-deployed (not just failed components)
- [ ] Target org was spot-checked post-deploy
- [ ] Preventive step was documented in the deployment runbook

## Prevention

What should be added to the deployment runbook or CI pipeline to prevent this error from recurring?

- (preventive check or pipeline step)

## Notes

Record any deviations from the standard troubleshooting workflow and why.
