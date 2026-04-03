# Custom Metadata Design Worksheet

## Requirement Summary

- Business capability:
- Owner of the values:
- Change frequency:
- Must deploy through source control: Yes / No
- Needs per-user or per-profile override: Yes / No
- Contains secrets: Yes / No
- Needs reporting or end-user CRUD: Yes / No

## Storage Decision

| Option | Choose? | Why |
|---|---|---|
| Custom Metadata Type |  | Deployable, packageable, source-controlled config |
| Hierarchy Custom Setting |  | User or profile override requirement |
| Custom Object |  | Business-managed, reportable, frequently edited data |
| Named Credential |  | Secret, auth, or endpoint host concern |

## Metadata Type Shape

- Type API name:
- Record key strategy (`DeveloperName`, external-style field, or both):
- Visibility model:
- Required fields:
- Optional fields:
- Subscriber-editable fields:

## Runtime Access Plan

### Apex Access

```apex
// Query or static accessor plan:
SELECT DeveloperName
FROM Example_Config__mdt
WHERE DeveloperName = 'Default'
```

### Flow Access

- `Get Records` criteria:
- Decision logic that consumes the values:
- Fault path if no matching record exists:

### Formula Access

- Formula entry point:
- Example placeholder: `$CustomMetadata.Example_Config__mdt.Default.Flag__c`

## Deployment And Governance

- Source path for records:
- Promotion owner:
- Backfill or migration plan from old settings:
- Rollback plan:
- Tests that prove configuration is wired correctly:
