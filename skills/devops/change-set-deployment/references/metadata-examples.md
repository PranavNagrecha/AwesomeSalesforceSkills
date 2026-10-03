# Metadata Examples: Change Set Deployment

Change sets are built in the Setup UI, so there is no change set file to deploy. What you can keep in source control is a **package.xml mirror** of the change set. It lets you retrieve the target org's current version of every component before upload, diff it against the source, and run the skill checker on real XML.

## 1. package.xml mirror of the change set

`manifest/package.xml` lists the same components as the outbound change set "REL-2026-10 Service Tier".

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml : mirror of outbound change set REL-2026-10 Service Tier -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>ServiceTierService</members>
        <members>ServiceTierServiceTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Service_Tier__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Service_Tier__c.Tier_Level__c</members>
        <members>Service_Tier__c.Effective_Date__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Service_Tier_Assignment</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Service_Tier_Manager</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Service_Tier__c-Service Tier Layout</members>
        <name>Layout</name>
    </types>
    <version>67.0</version>
</Package>
```

## 2. Retrieve the target baseline and the source version, then check

```bash
# Target (production) baseline: what the change set will overwrite
sf project retrieve start --manifest manifest/package.xml --target-org prod --output-dir baseline/prod

# Source (UAT sandbox) version: what the change set will carry
sf project retrieve start --manifest manifest/package.xml --target-org uat --output-dir baseline/uat

# Diff the two trees, then run the skill checker on the source tree
diff -ru baseline/prod baseline/uat || true
python3 skills/devops/change-set-deployment/scripts/check_change_set_deployment.py \
  --manifest-dir baseline/uat
```

`--output-dir` must not match a package directory in `sfdx-project.json`, or the retrieve fails (Salesforce CLI `sf project retrieve start --help`).

## 3. Production flow activation setting

If the release decision is to activate flows at deploy time, the production org needs this setting first. It can ship in its own change set or deploy. With it on, deploying an active flow runs Apex tests and checks flow coverage.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/settings/Flow.settings-meta.xml -->
<FlowSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableFlowDeployAsActiveEnabled>true</enableFlowDeployAsActiveEnabled>
</FlowSettings>
```

package.xml member form: `<members>Flow</members>` under `<name>Settings</name>`.

## 4. Profile review scope

When a profile must ship, retrieve it together with the feature components. The retrieved `.profile-meta.xml` then holds exactly the sections the deploy will carry: settings for the listed components, plus `userPermissions`, `loginIpRanges`, and `loginHours`, which the Metadata API always includes.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/profile-review.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Service_Tier__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Sales Manager</members>
        <name>Profile</name>
    </types>
    <version>67.0</version>
</Package>
```

## 5. Deploy order and verification

| Order | Step | Verify |
|---|---|---|
| 1 | Flow settings (only if activating at deploy time) | Process Automation Settings shows "Deploy processes and flows as active" |
| 2 | Upload change set, validate with the chosen test level | Validation succeeded; coverage rule for the test level met |
| 3 | Quick deploy from Deployment Status within 10 days | Deployment Status shows the quick deploy Succeeded |
| 4 | Post-deploy: activate inactive flows, assign permission sets | Flow version Active; users have the permission set |

## Sources

- Metadata API Developer Guide (Summer '26): Profile usage (scoped retrieve and deploy), FlowSettings `enableFlowDeployAsActiveEnabled`, `deployRecentValidation()`, Layout member naming `Object-Layout Name`.
- Salesforce CLI 2.151.7 `sf project retrieve start --help` (`--manifest`, `--output-dir`, `--metadata`).
