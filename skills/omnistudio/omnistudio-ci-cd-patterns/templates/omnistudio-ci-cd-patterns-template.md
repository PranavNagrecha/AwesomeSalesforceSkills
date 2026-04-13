# OmniStudio CI/CD Patterns — Work Template

Use this template when designing or implementing an OmniStudio deployment pipeline.

## Scope

**Skill:** `omnistudio-ci-cd-patterns`

**Project:** (fill in the project or org name)

**Org runtime:** [ ] Package Runtime (vlocity_cmt / vlocity_ins namespace)  [ ] Standard/Core Runtime

**CI/CD platform:** [ ] GitHub Actions  [ ] Bitbucket Pipelines  [ ] Jenkins  [ ] Other: ___

## Environment Map

| Environment | Org Alias | Promotion Trigger | Approval Required |
|---|---|---|---|
| Development | | Feature branch push | No |
| UAT | | PR merge to main | No |
| Production | | Manual approval | Yes |

## Components to Deploy

| Component Type | Component Name | Package Runtime Key | Notes |
|---|---|---|---|
| OmniScript | | | |
| Integration Procedure | | | |
| DataRaptor | | | |
| FlexCard | | | |

## Pipeline Stages (Package Runtime — DataPack Path)

### Stage 1: Export
```bash
sf omnistudio datapack export \
  --manifest manifest.json \
  --output-dir datapacks/ \
  --target-org $SOURCE_ORG
```

- [ ] DataPack JSON committed to feature branch
- [ ] Diff reviewed — only expected components changed

### Stage 2: Deploy to UAT
```bash
sf omnistudio datapack deploy \
  --source-dir datapacks/ \
  --activate \
  --target-org $UAT_ORG
```

- [ ] Deploy exit code 0
- [ ] Active version verified post-deploy
- [ ] UAT validation completed by business user

### Stage 3: Deploy to Production
```bash
sf omnistudio datapack deploy \
  --source-dir datapacks/ \
  --activate \
  --target-org $PROD_ORG
```

- [ ] Manual approval received
- [ ] Deploy exit code 0
- [ ] Active version verified post-deploy

## Post-Deploy Verification Checklist

- [ ] Component active version matches deployed version (query target org)
- [ ] OmniScript renders correctly for target user profile
- [ ] Integration Procedure callouts succeed in production context
- [ ] DataRaptor field mappings return expected values
- [ ] No runtime errors in org debug logs after first production user session

## Rollback Plan

If post-deploy verification fails:

1. Re-deploy prior DataPack version: `sf omnistudio datapack deploy --source-dir datapacks-backup/ --activate --target-org $TARGET_ORG`
2. Verify prior version is active
3. Investigate failure in UAT before re-attempting production deployment

## Security Notes

- [ ] No credentials stored in DataPack job files
- [ ] CI/CD service account uses JWT bearer flow (no username/password)
- [ ] Connected app credentials stored as encrypted CI/CD secrets

## Notes

(Record any deviations from the standard pattern and the rationale.)
