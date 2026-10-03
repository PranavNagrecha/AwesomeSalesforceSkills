# Metadata Examples: Release Management

A complete, deployable release folder for an org-based release train. File paths are relative to the Salesforce DX project root.

## 1. Project configuration

`sfdx-project.json`

```json
{
  "packageDirectories": [
    { "path": "force-app", "default": true }
  ],
  "name": "northwind-release-train",
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "67.0"
}
```

`sourceApiVersion` 67.0 matches the Summer '26 (release 262) Metadata API. Keep it pinned per release so a CLI upgrade does not silently change the API version of a deploy.

## 2. Release manifest

The release manifest lists exactly what ships. The same file drives the pre-release backup, so the backup always covers the release scope.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AccountTriggerHandler</members>
        <members>AccountTriggerHandlerTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>AccountTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>Account.Customer_Tier__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Account_Tier_Assignment</members>
        <name>Flow</name>
    </types>
    <version>67.0</version>
</Package>
```

## 3. Flow activation setting (optional, production only)

Deploy this only if the release decision is to activate flows at deploy time. With it, deploying an active flow to production runs Apex tests and checks flow test coverage.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/settings/Flow.settings-meta.xml -->
<FlowSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableFlowDeployAsActiveEnabled>true</enableFlowDeployAsActiveEnabled>
</FlowSettings>
```

package.xml member form for this file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/settings-package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Flow</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

## 4. Release-night command sequence

```bash
#!/usr/bin/env bash
# release.sh: run from the project root. Every flag below appears in `sf <command> --help` for CLI 2.151.7.
set -euo pipefail
RELEASE_DATE="2026-10-03"
PROD="prod"   # org alias

# T-3 days: archive the production version of everything in scope (Metadata API format)
sf project retrieve start --manifest manifest/package.xml --target-org "$PROD" \
  --target-metadata-dir "backups/$RELEASE_DATE" --single-package

# T-3 days: validate against production and keep the 0Af job ID (valid 10 days)
sf project deploy validate --manifest manifest/package.xml --target-org "$PROD" \
  --test-level RunLocalTests --wait 120 --json > "backups/$RELEASE_DATE/validate.json"

# Release night: quick deploy the validated job ID (pass it explicitly; --use-most-recent looks back only 3 days)
VALIDATION_ID="$(python3 -c "import json;print(json.load(open('backups/$RELEASE_DATE/validate.json'))['result']['id'])")"
sf project deploy quick --job-id "$VALIDATION_ID" --target-org "$PROD" --wait 30 --json > "backups/$RELEASE_DATE/quick.json"

# Monitor the NEW deploy ID returned by the quick deploy
QUICK_ID="$(python3 -c "import json;print(json.load(open('backups/$RELEASE_DATE/quick.json'))['result']['id'])")"
sf project deploy report --job-id "$QUICK_ID" --target-org "$PROD"

# Rollback (only if a rollback trigger fires): redeploy the archive
# sf project deploy start --metadata-dir "backups/$RELEASE_DATE/unpackaged.zip" --single-package \
#   --test-level RunLocalTests --target-org "$PROD" --wait 120
```

The `result.id` path in the `--json` output is UNVERIFIED (2026-10-03): it matches CLI 2.151.7 behaviour seen in the plugin source, but confirm it on your CLI version before automating it.

## 5. Deploy order and verification

| Order | What | Verify |
|---|---|---|
| 1 | `Flow.settings` (only if activating at deploy time) | Setup > Process Automation Settings shows "Deploy processes and flows as active" |
| 2 | Release manifest via quick deploy | `sf project deploy report` shows Succeeded for the quick deploy ID |
| 3 | Manual flow activation (if the setting stayed off) | Flow detail page shows the new version Active |
| 4 | Smoke tests | Every row in the release plan's smoke test table passes |

## Sources

- Metadata API Developer Guide (Summer '26): `deployRecentValidation()`, DeployOptions `testLevel` and `rollbackOnError`, FlowSettings `enableFlowDeployAsActiveEnabled`, Settings package.xml form.
- Salesforce CLI `--help` output for `project retrieve start`, `project deploy validate`, `project deploy quick`, `project deploy report`, `project deploy start` (CLI 2.151.7).
