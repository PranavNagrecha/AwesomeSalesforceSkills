# Examples — Environment-Specific Value Injection

## Example 1: sfdx String Replacement for a Named Credential Endpoint URL

**Context:** A team deploys an integration that calls an external REST API. The sandbox and production endpoints are different (`https://sandbox.api.example.com` and `https://api.example.com`). The CI pipeline runs on GitHub Actions with per-environment secrets.

**Problem:** The team hard-coded `https://api.example.com` in the Named Credential XML. Every sandbox deployment connects to the production endpoint, causing integration tests to hit live data and occasionally corrupt production records.

**Solution:**

`force-app/main/default/namedCredentials/ExternalAPI.namedCredential` — source file with placeholder:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>External API</label>
    <name>ExternalAPI</name>
    <calloutUrl>${EXTERNAL_API_ENDPOINT}</calloutUrl>
    <allowMergeFieldsInBody>false</allowMergeFieldsInBody>
    <allowMergeFieldsInHeader>false</allowMergeFieldsInHeader>
    <generateAuthorizationHeader>true</generateAuthorizationHeader>
    <principalType>NamedUser</principalType>
    <protocol>Password</protocol>
</NamedCredential>
```

`sfdx-project.json` replacements block:

```json
{
  "packageDirectories": [{"path": "force-app", "default": true}],
  "name": "myproject",
  "sourceApiVersion": "63.0",
  "replacements": [
    {
      "filename": "force-app/main/default/namedCredentials/ExternalAPI.namedCredential",
      "stringToReplace": "${EXTERNAL_API_ENDPOINT}",
      "replaceWithEnv": "EXTERNAL_API_ENDPOINT"
    }
  ]
}
```

GitHub Actions workflow (deploy job step, inside the relevant environment):

```yaml
- name: Deploy metadata with environment-specific values
  run: |
    sf project deploy start \
      --target-org target-org \
      --source-dir force-app \
      --test-level RunLocalTests \
      --wait 30
  env:
    EXTERNAL_API_ENDPOINT: ${{ secrets.EXTERNAL_API_ENDPOINT }}
```

GitHub Actions environment secrets configuration:
- `staging` environment: `EXTERNAL_API_ENDPOINT = https://sandbox.api.example.com`
- `production` environment: `EXTERNAL_API_ENDPOINT = https://api.example.com`

**Why it works:** The source file is always neutral (contains only the placeholder). At deploy time, the CLI reads `EXTERNAL_API_ENDPOINT` from the runner's environment and substitutes it before sending the metadata to the org. The substituted value never enters the repository.

---

## Example 2: Custom Metadata Records for Feature Flags and Thresholds

**Context:** A processing engine in Apex uses a daily record-processing limit and a feature toggle that should be `true` in production and `false` in all sandboxes during testing. The team previously hardcoded `5000` and `true` in an Apex constant class. When a sandbox was refreshed from production, the flag was always `true`, causing test scripts to trigger production-grade processing.

**Problem:** Hardcoded constants in Apex cannot differ per environment. A sandbox refresh brings production values with no way to override them declaratively.

**Solution:**

Custom Metadata Type: `ProcessingConfig__mdt`
- `DailyRecordLimit__c` (Number)
- `EnableProductionProcessing__c` (Checkbox)

Source-controlled records:

`force-app/main/default/customMetadata/ProcessingConfig.Production.md-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Production</label>
    <protected>false</protected>
    <values>
        <field>DailyRecordLimit__c</field>
        <value xsi:type="xsd:double">5000</value>
    </values>
    <values>
        <field>EnableProductionProcessing__c</field>
        <value xsi:type="xsd:boolean">true</value>
    </values>
</CustomMetadata>
```

`force-app/main/default/customMetadata/ProcessingConfig.Sandbox.md-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Sandbox</label>
    <protected>false</protected>
    <values>
        <field>DailyRecordLimit__c</field>
        <value xsi:type="xsd:double">100</value>
    </values>
    <values>
        <field>EnableProductionProcessing__c</field>
        <value xsi:type="xsd:boolean">false</value>
    </values>
</CustomMetadata>
```

Apex reads the correct record by checking org type:

```apex
public class ProcessingConfigService {
    public static ProcessingConfig__mdt getConfig() {
        String env = [SELECT IsSandbox FROM Organization LIMIT 1].IsSandbox ? 'Sandbox' : 'Production';
        return ProcessingConfig__mdt.getInstance(env);
    }
}
```

**Why it works:** Both records are source-controlled and deploy together. Apex selects the correct record at runtime based on the org type. No hardcoded constants remain in code. A sandbox refreshed from production gets the `Sandbox` record (with safe limits) because it was deployed after refresh, not seeded from production data.

---

## Example 3: Post-Deploy Script to Populate Named Credential Password

**Context:** After deploying a Named Credential stub to a new full sandbox, the CI pipeline must set the API password for a service account. The password is stored in the pipeline's secret manager and must not appear in source control.

**Problem:** Without automation, a developer must manually navigate to Setup > Named Credentials, edit the record, and enter the password. This breaks fully automated provisioning and is error-prone.

**Solution:**

Post-deploy Python script (`scripts/populate_named_credentials.py`, stdlib only):

```python
#!/usr/bin/env python3
"""Populate Named Credential password after deployment using the Tooling API.

Usage:
    python3 populate_named_credentials.py \
        --instance-url https://example.sandbox.salesforce.com \
        --access-token $SF_ACCESS_TOKEN \
        --credential-name ExternalAPI \
        --username svc-integration@example.com.sandbox \
        --password-env EXTERNAL_API_PASSWORD
"""

import argparse
import json
import os
import urllib.request
import urllib.parse
import sys


def populate_named_credential(
    instance_url: str,
    access_token: str,
    credential_name: str,
    username: str,
    password: str,
) -> None:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    query = urllib.parse.quote(f"SELECT Id FROM NamedCredential WHERE DeveloperName = '{credential_name}'")
    query_url = f"{instance_url}/services/data/v63.0/tooling/query?q={query}"

    req = urllib.request.Request(query_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    if not result.get("records"):
        print(f"ERROR: Named Credential '{credential_name}' not found.", file=sys.stderr)
        sys.exit(1)

    nc_id = result["records"][0]["Id"]

    patch_url = f"{instance_url}/services/data/v63.0/tooling/sobjects/NamedCredential/{nc_id}"
    payload = json.dumps({"Password": password, "Username": username}).encode()
    patch_req = urllib.request.Request(patch_url, data=payload, headers=headers, method="PATCH")

    with urllib.request.urlopen(patch_req) as resp:
        if resp.status == 204:
            print(f"Named Credential '{credential_name}' populated successfully.")
        else:
            print(f"ERROR: Unexpected response {resp.status}", file=sys.stderr)
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance-url", required=True)
    parser.add_argument("--access-token", required=True)
    parser.add_argument("--credential-name", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password-env", required=True)
    args = parser.parse_args()

    password = os.environ.get(args.password_env)
    if not password:
        print(f"ERROR: Environment variable '{args.password_env}' is not set.", file=sys.stderr)
        sys.exit(1)

    populate_named_credential(
        args.instance_url, args.access_token, args.credential_name, args.username, password
    )


if __name__ == "__main__":
    main()
```

**Why it works:** The script reads the password from a CI environment variable (never hardcoded or logged). The Named Credential record already exists post-deploy; the script only populates the org-bound credential field that cannot travel through source control.

---

## Anti-Pattern: Embedding Org-Specific URLs in Apex Constants

**What practitioners do:** Create an Apex class `OrgConstants` with `public static final String API_ENDPOINT = 'https://api.example.com';` and comment `// change this for sandbox`.

**What goes wrong:** The comment is forgotten. Developers clone the class, inherit the hardcoded URL, and deploy to sandboxes pointing to production. Code reviews miss it because it looks intentional. Sandbox testing hits production data. There is no CI enforcement to catch the drift.

**Correct approach:** Replace the Apex constant with a Custom Metadata record lookup or a Named Credential callout. The value lives in deployable metadata, not code, and the CI pipeline controls which value each environment receives.
