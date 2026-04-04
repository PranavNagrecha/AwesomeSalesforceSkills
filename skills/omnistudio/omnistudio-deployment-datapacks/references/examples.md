# Examples — OmniStudio Deployment DataPacks

## Example 1: Export OmniStudio Assets to Git for the First Time

**Context:** A financial services team has built three OmniScripts, four Integration Procedures, and six DataRaptors in a developer sandbox. The team is moving to a code-review-based delivery workflow and needs the OmniStudio components in Git so changes can be reviewed before promotion to UAT.

**Problem:** Without DataPack export, components exist only as records in the sandbox org. There is no audit trail, no way to review changes in a pull request, and no repeatable mechanism to promote to UAT without manual re-creation or change sets that do not handle record-based components cleanly.

**Solution:**

1. Create a `propertySetConfig.json` in the project root:

```json
{
  "queries": [
    {
      "query": "Select Id from OmniProcess where Type = 'OmniScript' and Language = 'English'",
      "VlocityDataPackType": "OmniScript"
    },
    {
      "query": "Select Id from OmniIntegrationProcedure",
      "VlocityDataPackType": "IntegrationProcedure"
    },
    {
      "query": "Select Id from OmniDataTransform",
      "VlocityDataPackType": "DataRaptor"
    }
  ],
  "defaultMaxParallel": 1,
  "exportPacksMaxSize": 50
}
```

2. Authenticate and export:

```bash
sf org login web --alias fs-sandbox
sf omnistudio datapack export \
  --target-org fs-sandbox \
  --job propertySetConfig.json \
  --output datapacks/
```

3. Review the output directory structure:

```
datapacks/
  OmniScript/
    LoanApplication_English_1/
      LoanApplication_English_1.json
  IntegrationProcedure/
    GetApplicantDetails/
      GetApplicantDetails.json
  DataRaptor/
    ExtractApplicantData/
      ExtractApplicantData.json
```

4. Scan for embedded org-specific record IDs before committing. A quick check:

```bash
# Find any 15- or 18-char Salesforce record ID patterns in the DataPack JSON
grep -rE '"[a-zA-Z0-9]{15,18}"' datapacks/ | grep -v '"VlocityDataPackType"'
```

5. Commit to Git:

```bash
git add datapacks/
git commit -m "feat: initial OmniStudio DataPack export — LoanApplication OmniScript, GetApplicantDetails IP, ExtractApplicantData DataRaptor"
```

**Why it works:** The vlocity CLI writes each component as a separate JSON file, so Git diffs are per-component and reviewable. The JSON format is deterministic — re-exporting the same component produces the same file, making it safe to re-run exports in CI without spurious diffs (provided no org-side changes occurred).

---

## Example 2: CI/CD Pipeline Import with Activation and Environment Override

**Context:** The same financial services team has established a main branch policy: merging to `main` triggers automated deployment to UAT. The UAT org uses a different Named Credential name (`UAT_LoanService`) than the sandbox (`DEV_LoanService`). Without override, the Integration Procedure would be imported with the sandbox credential name embedded, causing all outbound calls to fail at runtime in UAT.

**Problem:** The DataPack JSON for `GetApplicantDetails` contains `"namedCredential": "DEV_LoanService"` embedded in the HTTP action element. Importing this verbatim into UAT causes a `Named Credential not found` error at runtime because the UAT org only has `UAT_LoanService`.

**Solution:**

Add an override step in the GitHub Actions workflow that uses `sed` (or a Python script) to replace the environment-specific value at pipeline runtime before import:

```yaml
# .github/workflows/deploy-to-uat.yml
name: Deploy OmniStudio to UAT

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Salesforce CLI
        run: npm install -g @salesforce/cli

      - name: Install OmniStudio plugin
        run: sf plugins install @salesforce/plugin-omnistudio

      - name: Authenticate to UAT
        run: |
          echo "${{ secrets.UAT_SFDX_URL }}" > /tmp/uat_sfdx_url.txt
          sf org login sfdx-url --sfdx-url-file /tmp/uat_sfdx_url.txt --alias uat-org

      - name: Apply environment overrides
        run: |
          # Replace sandbox Named Credential name with UAT equivalent
          find datapacks/ -name "*.json" -exec \
            python3 scripts/apply_env_overrides.py \
              --input {} \
              --replace DEV_LoanService=${{ vars.UAT_NAMED_CREDENTIAL }} \
            \;

      - name: Import DataPacks with activation
        run: |
          sf omnistudio datapack import \
            --target-org uat-org \
            --source-dir datapacks/ \
            --activate \
            --verbose

      - name: Verify activation
        run: |
          sf omnistudio datapack list \
            --target-org uat-org \
            --type OmniScript \
            --filter "Name = 'LoanApplication'"
```

`apply_env_overrides.py` is a stdlib-only Python script in the project that does a targeted string replacement inside the DataPack JSON for known environment-specific keys.

**Why it works:** Environment-specific values are replaced at pipeline runtime from CI secrets/variables, so the canonical DataPack JSON in Git stays environment-neutral. The `--activate` flag ensures the imported version becomes live in UAT immediately, rather than requiring a manual activation step that is easy to forget.

---

## Anti-Pattern: Importing Without Checking Dependency Closure

**What practitioners do:** Export only the top-level OmniScript (the component being worked on) and import it into a target org, assuming the Integration Procedures and DataRaptors it calls are already there from a prior deployment.

**What goes wrong:** The prior deployment may have brought older versions of the dependencies. The OmniScript's references are resolved at runtime by name and active version, so if the target org has an older active version of the Integration Procedure (from the previous release), the OmniScript will call the old IP behavior even though the OmniScript itself is newly imported. The team observes that the new OmniScript appears to work incorrectly because it is calling stale downstream components.

**Correct approach:** Always export the complete dependency closure together. Use `--maxDepth -1` (or the equivalent in the propertySetConfig) on the export to include all transitive dependencies. Import the full set together so the vlocity CLI can resolve and deploy in correct dependency order: DataRaptors first, Integration Procedures second, OmniScripts last. This guarantees runtime consistency across all layers.
