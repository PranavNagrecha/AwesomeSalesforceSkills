# Metadata Examples: OmniStudio Debugging

Artifacts for the "works in sandbox, fails in production" investigation. Element names for RemoteSiteSetting come from the Metadata API Developer Guide (Summer '26). OmniStudio type names and source folders (`omniScripts/*.os-meta.xml`, `omniIntegrationProcedures/*.oip-meta.xml`, `omniDataTransforms/*.rpt-meta.xml`) come from the Salesforce CLI metadata registry (source-deploy-retrieve 12.22.6).

## 1. Pull the same assets from both orgs and compare

```bash
#!/usr/bin/env bash
# compare-omni.sh: retrieve OmniStudio assets from sandbox and production, then diff and check them
set -euo pipefail
for ORG in uat prod; do
  sf project retrieve start \
    --metadata OmniIntegrationProcedure OmniScript OmniDataTransform NamedCredential RemoteSiteSetting \
    --target-org "$ORG" --output-dir "compare/$ORG"
done
diff -ru compare/uat compare/prod || true
python3 skills/omnistudio/omnistudio-debugging/scripts/check_omnistudio_debugging.py --manifest-dir compare/prod
```

What to look for in the diff:

| Difference | Meaning |
|---|---|
| `isActive` (`active` for Data Mappers) differs | A different version runs in each org |
| HTTP step path is a raw URL in one org | The call needs a Remote Site Setting there, or should move to a named credential |
| A NamedCredential exists only in the sandbox | The production HTTP step has no credential to use |
| `fieldLevelSecurityEnabled` differs on a Data Mapper | Restricted users see different fields per org |

`--output-dir` must not match a package directory in `sfdx-project.json`, or the retrieve fails (CLI help).

## 2. Remote Site Setting for an endpoint that is not a named credential

Only needed when the HTTP step calls a raw URL. Callouts to a named credential endpoint need no Remote Site Setting (Apex Developer Guide).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/remoteSiteSettings/Weather_API.remoteSite-meta.xml -->
<RemoteSiteSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Weather API called by the acct_getDetails Integration Procedure. Owner: Service IT.</description>
    <disableProtocolSecurity>false</disableProtocolSecurity>
    <isActive>true</isActive>
    <url>https://api.weather.example.com</url>
</RemoteSiteSetting>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/debug-fix.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Weather_API</members>
        <name>RemoteSiteSetting</name>
    </types>
    <version>67.0</version>
</Package>
```

## 3. Repeatable Preview input

Store the input you debug with next to the asset so every re-run, in every org, uses the same data.

```json
{
  "asset": "acct_getDetails_Procedure",
  "org": "prod",
  "input": { "AccountId": "001XXXXXXXXXXXXXXX", "includeContacts": true },
  "expected": { "Account": { "Name": "<non-empty>" }, "Contacts": "<array>" },
  "observed": { "Account": {}, "Contacts": null },
  "firstWrongStep": "CallCrm",
  "cause": "named credential ExternalCRM missing in prod"
}
```

## 4. Verification order

| Order | Step | Verify |
|---|---|---|
| 1 | Fix the dependency (credential, Remote Site Setting, custom setting value) | Present in the target org |
| 2 | Re-run the IP Preview with the stored input | The first wrong step now returns data |
| 3 | Run the OmniScript in the deployed page as a representative user | The screen shows the data or a specific error |
| 4 | Record the active versions | Same versions active in both orgs, or the difference is intended |
