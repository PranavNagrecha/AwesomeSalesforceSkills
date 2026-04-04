# OmniStudio DataPack Deployment — Work Template

Use this template when planning or executing a DataPack export, import, or CI/CD configuration task.

## Scope

**Skill:** `omnistudio-deployment-datapacks`

**Request summary:** (describe what is being deployed, from where, and to where)

---

## Context Gathered

Answer these before starting:

- **Source org alias:** _______________
- **Target org alias:** _______________
- **OmniStudio package mode** (managed / standard): _______________
- **OmniStudio package version in source org:** _______________
- **OmniStudio package version in target org:** _______________
- **vlocity CLI / sf omnistudio plugin version in use:** _______________
- **Components to deploy** (list type and name):
  - OmniScript: _______________
  - Integration Procedure: _______________
  - DataRaptor: _______________
  - FlexCard: _______________
  - Other: _______________
- **Environment-specific values that differ between source and target:**
  - Named Credential names: source = _______________, target = _______________
  - Endpoint URLs: source = _______________, target = _______________
  - Custom Setting / Metadata values: _______________

---

## Export Configuration

Copy and fill this `propertySetConfig.json` before running export:

```json
{
  "queries": [
    {
      "query": "Select Id from OmniProcess where Type = 'OmniScript' and Name = '<OmniScript Name>' and Language = 'English'",
      "VlocityDataPackType": "OmniScript"
    },
    {
      "query": "Select Id from OmniIntegrationProcedure where Name = '<IP Name>'",
      "VlocityDataPackType": "IntegrationProcedure"
    },
    {
      "query": "Select Id from OmniDataTransform where Name = '<DataRaptor Name>'",
      "VlocityDataPackType": "DataRaptor"
    }
  ],
  "defaultMaxParallel": 1,
  "exportPacksMaxSize": 50
}
```

**Note:** Replace `<OmniScript Name>`, `<IP Name>`, `<DataRaptor Name>` with actual component names. Adjust object API names for managed package namespace if applicable (e.g., `vlocity_cmt__OmniScript__c`).

---

## Export Command

```bash
# With Salesforce CLI plugin
sf omnistudio datapack export \
  --target-org <source-org-alias> \
  --job propertySetConfig.json \
  --output datapacks/

# With standalone vlocity CLI
vlocity -sfdx.username <source-org-alias> \
  -job propertySetConfig.json \
  packExport
```

---

## Pre-Import Checklist

- [ ] DataPack JSON files committed to Git and PR reviewed
- [ ] Environment-specific values identified and override substitution prepared
- [ ] Target org has the same OmniStudio package version (or a compatible version)
- [ ] Named Credentials and Remote Site Settings confirmed to exist in target org
- [ ] Dependencies confirmed: either included in this DataPack set or already active in target org

---

## Import Command

```bash
# With Salesforce CLI plugin (recommended for CI/CD)
sf omnistudio datapack import \
  --target-org <target-org-alias> \
  --source-dir datapacks/ \
  --activate \
  --verbose

# With standalone vlocity CLI
vlocity -sfdx.username <target-org-alias> \
  -job propertySetConfig.json \
  packDeploy
```

---

## Post-Import Checklist

- [ ] Import log reviewed — all components show `Success`, zero `Error` entries
- [ ] Active version verified in OmniStudio app for each imported component
- [ ] Smoke test run: at least one end-to-end user journey tested in the target org
- [ ] Integration Procedure callouts tested against the correct environment endpoint
- [ ] Deployment result documented in the ticket or release log

---

## Rollback Plan

If the import introduces a regression:

1. Identify the prior active version number from Git history or org version history.
2. Export the prior version DataPack from the source-of-truth org (or retrieve the prior JSON from Git).
3. Re-import with `--activate` to restore the prior version as active in the target org.
4. Verify activation and re-run smoke test.

---

## Notes

(Record any deviations from the standard pattern, environment-specific decisions, or issues encountered during this deployment.)
