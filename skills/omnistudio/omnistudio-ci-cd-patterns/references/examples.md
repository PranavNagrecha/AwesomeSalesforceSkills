# Examples — OmniStudio CI/CD Patterns

## Example 1: DataPack Pipeline Failing Silently Due to Missing --activate

**Context:** A financial services company has a Package Runtime org with an OmniScript for loan origination. The DevOps team sets up a GitHub Actions pipeline to promote DataPack components from UAT sandbox to production. The pipeline runs successfully (exit 0) but the business team reports no changes are visible in production.

**Problem:** The pipeline's deploy step uses `sf omnistudio datapack deploy --source-dir datapacks/` without the `--activate` flag. The component records are imported into the production org, creating a new version, but the previously active version remains live. The pipeline exit code is 0, giving no indication of the problem.

**Solution:**

Update the pipeline deploy step to include `--activate`:

```yaml
# GitHub Actions workflow snippet
- name: Deploy OmniStudio DataPacks
  run: |
    sf omnistudio datapack deploy \
      --source-dir datapacks/ \
      --activate \
      --target-org ${{ secrets.PROD_ORG_ALIAS }}
  env:
    SF_ACCESS_TOKEN: ${{ secrets.PROD_ACCESS_TOKEN }}

- name: Verify Active Version
  run: |
    sf data query \
      --query "SELECT Id, Name, IsActive, Version__c FROM OmniScript__c WHERE Name = 'LoanOrigination' ORDER BY Version__c DESC LIMIT 1" \
      --target-org ${{ secrets.PROD_ORG_ALIAS }} \
      --json | jq '.result.records[0].IsActive'
```

Add a post-deploy verification step that queries the component's `IsActive` field. If false, fail the pipeline with a non-zero exit code.

**Why it works:** The `--activate` flag triggers OmniStudio's activation mechanism after import, setting the new version as the active runtime version. The verification query provides an explicit confirmation signal that the pipeline can act on.

---

## Example 2: Standard Runtime Migration Breaking an Existing DataPack Pipeline

**Context:** A telecommunications company migrates from Package Runtime to Standard/Core Runtime as part of a Salesforce-encouraged upgrade path. Their existing CI/CD pipeline uses the OmniStudio Build Tool with DataPack export/import. After migration, the pipeline continues to run without errors but OmniStudio components stop being updated in target orgs.

**Problem:** After Standard Runtime migration, OmniStudio components are stored as native Salesforce metadata (OmniScript, IntegrationProcedure metadata types), not as data records. The DataPack tool queries the vlocity namespace objects to find components to export — after migration, those records are gone. The tool finds nothing to export, exports an empty DataPack, and the deploy step imports nothing. Exit code is 0 because no errors occurred.

**Solution:**

```yaml
# Old pipeline (Package Runtime - DataPack)
- name: Export OmniStudio Components
  run: sf omnistudio datapack export --manifest manifest.json --output-dir datapacks/

# New pipeline (Standard Runtime - SFDX Metadata)
- name: Retrieve OmniStudio Components
  run: |
    sf project retrieve start \
      --metadata "OmniScript:LoanOrigination,IntegrationProcedure:GetCreditScore,FlexCard:ApplicantSummary" \
      --target-org ${{ secrets.SOURCE_ORG_ALIAS }}
      
- name: Deploy OmniStudio Components
  run: |
    sf project deploy start \
      --manifest package.xml \
      --target-org ${{ secrets.TARGET_ORG_ALIAS }}
```

Add a pipeline pre-check step that queries the org's runtime type before selecting the deploy path:

```bash
# Detect runtime by checking for Package Runtime namespace
sf data query \
  --query "SELECT Id FROM InstalledSubscriberPackage WHERE SubscriberPackage.NamespacePrefix = 'vlocity_cmt' LIMIT 1" \
  --target-org $ORG_ALIAS 2>/dev/null && echo "PACKAGE_RUNTIME" || echo "STANDARD_RUNTIME"
```

**Why it works:** Standard Runtime components are native metadata and must use standard Salesforce metadata deployment tooling. The pre-check query detects the runtime type at pipeline execution time, enabling the pipeline to branch to the correct deploy path automatically.

---

## Anti-Pattern: Storing Org Credentials in the DataPack Job File

**What practitioners do:** Use the OmniStudio Build Tool job file's inline credential fields for convenience, committing the job file (including username, password, and security token) to the Git repository.

**What goes wrong:** Any team member with repo access — or any attacker who gains access to the repository — can use those credentials to authenticate to the Salesforce org and perform any action the integration user is authorized for. Even in private repos, committing credentials violates security policy and Salesforce's acceptable use terms.

**Correct approach:** Store all org credentials as encrypted CI/CD secrets (GitHub Secrets, Bitbucket Secured Variables, etc.). Reference them as environment variables in the pipeline. Use the JWT bearer flow with a connected app for non-interactive CI/CD authentication — this eliminates plaintext passwords entirely and uses a private key stored in the CI/CD secret store.
