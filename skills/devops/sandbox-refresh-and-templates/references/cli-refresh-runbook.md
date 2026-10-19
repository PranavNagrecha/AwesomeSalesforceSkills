# CLI Refresh Runbook

Refreshing from Salesforce CLI with a definition file in source control means the template and post-copy class are chosen by the file, not retyped in Setup each time.

## 1. Definition files, one per sandbox

`config/uat-sandbox-def.json` (Partial Copy — `templateId` is required):

```json
{
  "sandboxName": "uat",
  "licenseType": "Partial",
  "templateId": "1psXXXXXXXXXXXX",
  "apexClassName": "UAT_SandboxSetup",
  "description": "UAT for the release train; refreshed at the start of each release cycle"
}
```

`config/dev1-sandbox-def.json` (Developer — no template allowed):

```json
{
  "sandboxName": "dev1",
  "licenseType": "Developer",
  "apexClassName": "Dev_SandboxSetup"
}
```

Rules the checker enforces: one of `licenseType` / `sourceSandboxName` / `sourceId`; `apexClassId` or `apexClassName`, not both; `sandboxName` alphanumeric, 10 characters or fewer; `templateId` required for `Partial`, optional for `Full`, absent for `Developer` and `Developer_Pro`.

## 2. Refresh

```bash
python3 skills/devops/sandbox-refresh-and-templates/scripts/check_sandbox_refresh.py --manifest-dir .
sf org refresh sandbox --name uat --target-org prodOrg \
  --definition-file config/uat-sandbox-def.json --wait 60
```

`--name` is the sandbox name, not an alias; `--target-org` is the production (source) org.

## 3. Verify the post-copy work landed

Run as an admin in the refreshed sandbox:

```bash
# Scheduled jobs the post-copy class created (none come from production)
sf data query -o uat -q "SELECT CronJobDetail.Name, State, NextFireTime FROM CronTrigger"

# Environment marker the class wrote
sf data query -o uat -q "SELECT Environment__c, Endpoint_Base_URL__c FROM Integration_Config__c"

# Masking spot-check: no address outside the masked domain
sf data query -o uat -q "SELECT COUNT() FROM Contact WHERE Email != null AND (NOT Email LIKE '%@example-sandbox.invalid')"
```

If any check fails, the class probably hit something the Automated Process user can't access: run the same logic as an admin, as the Apex Reference Guide advises. Keeping the body of `runApexClass` in a separate public method that takes the sandbox name makes that a one-line Anonymous Apex call.

## 4. Manual runbook lines

- Verify each Named Credential / External Credential used in this sandbox authenticates against the sandbox endpoint.
- Point external systems' callbacks at the sandbox's My Domain URL.
- Set email deliverability for this sandbox.
- Record the refresh date and the next planned refresh in the release calendar.

## 5. Keep sandbox-expiry warnings on in production

Sandboxes that stay inactive for 180 days or longer are scheduled for deletion, and production users get email warnings first unless `SandboxSettings.disableSandboxExpirationEmails` is true. A rarely used Full sandbox is exactly the one that goes quiet; keep the warnings on in `settings/Sandbox.settings`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SandboxSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <disableSandboxExpirationEmails>false</disableSandboxExpirationEmails>
</SandboxSettings>
```
