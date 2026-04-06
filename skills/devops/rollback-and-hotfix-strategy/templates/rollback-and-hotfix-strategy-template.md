# Rollback And Hotfix Strategy — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `rollback-and-hotfix-strategy`

**Request summary:** (fill in what the user asked for)

**Type:** [ ] Full rollback  [ ] Targeted hotfix  [ ] Rollback planning (pre-deploy)

## Context Gathered

- Pre-deploy archive location:
- Failed deployment manifest (`package.xml`):
- Components changed in failed deployment:
- Non-rollbackable components identified (Record Types, Picklist values, active Flows):
- Source control tag/commit for previous known-good state:

## Approach

Which pattern applies:
- [ ] Full rollback from pre-deploy archive (Pattern 1)
- [ ] Quick deploy hotfix (Pattern 2)
- [ ] Hybrid: rollback most components + hotfix for specific fix

Justification:

## Rollback Package Contents

| Component | Metadata Type | Action (revert / delete / manual) |
|---|---|---|
| | | |

## Manual Remediation Steps

List steps for non-rollbackable components:

1.
2.

## Checklist

- [ ] Pre-deploy archive exists or previous state reconstructed from source control
- [ ] All changed components accounted for in rollback package
- [ ] Non-rollbackable components have manual remediation steps documented
- [ ] Destructive changes manifest included for newly-added components
- [ ] Validation passed against production with RunLocalTests
- [ ] Quick deploy job ID captured (if applicable)
- [ ] Hotfix branch merged back into main/develop
- [ ] Production verified stable after rollback/hotfix

## Notes

Record any deviations from the standard pattern and why.
