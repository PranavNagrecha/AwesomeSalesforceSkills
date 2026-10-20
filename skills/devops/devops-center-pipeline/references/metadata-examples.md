# Metadata Examples — DevOps Center Pipeline

## Which DevOps Center is on: `DevHub.settings`

The Metadata API stores Dev Hub settings in `settings/DevHub.settings` (in an SFDX source project the same file is `settings/DevHub.settings-meta.xml`). Enable one DevOps Center, not both. This excerpt shows Lifecycle Center (the Summer '26 "next-generation DevOps Center") switched on and the managed package switched off:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: settings/DevHub.settings — only the DevOps Center fields are shown -->
<DevHubSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableALMDevopsCorePref>true</enableALMDevopsCorePref>
    <enableDevOpsCenterGA>false</enableDevOpsCenterGA>
</DevHubSettings>
```

`enableDevopsCenterMigrationPref` (API 67.0) moves projects from the managed package to Lifecycle Center, but it is a developer preview; leave it out of production manifests.

## Source tracking for development sandboxes: `SourceTracking.settings`

Deploy to production, then create or refresh each Developer or Developer Pro sandbox that will be a development environment:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SourceTrackingSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableSourceTrackingSandboxes>true</enableSourceTrackingSandboxes>
</SourceTrackingSettings>
```

The setting is ignored outside production. Setting it back to false does not stop a sandbox that is already tracking until that sandbox is refreshed.

## Troubleshooting queries (Lifecycle Center)

Work items stuck on a conflict, newest first:

```soql
SELECT Name, Subject, Status, DevopsPipelineStageId, LastSyncDate
FROM WorkItem
WHERE Status = 'MERGE_CONFLICT'
ORDER BY LastModifiedDate DESC
```

Which test level each recent stage deployment actually ran:

```soql
SELECT Name, Status, TestLevel, RunTests, IsFullDeploy, TargetDeployOrgId
FROM DevopsEnvDeployment
ORDER BY CreatedDate DESC
LIMIT 20
```

A QA or UAT row with `TestLevel = 'Default'` ran no tests: `Default` means no tests in sandboxes and all local tests in production.
