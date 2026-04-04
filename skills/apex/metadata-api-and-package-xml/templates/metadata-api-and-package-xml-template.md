# Metadata API and Package.xml — Work Template

Use this template when working on retrieve, deploy, or deletion tasks using the Salesforce Metadata API.

## Scope

**Skill:** `metadata-api-and-package-xml`

**Request summary:** (fill in what the user asked for — retrieve, deploy, or delete)

**Operation type:** [ ] Retrieve  [ ] Deploy to sandbox  [ ] Deploy to production  [ ] Delete components

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Target org type:** (production / sandbox / Developer Edition)
- **API version to use:** (check current supported range — latest is v66.0, Spring '26)
- **User has required permissions:** [ ] Modify Metadata Through Metadata API Functions OR [ ] Modify All Data  + [ ] API Enabled
- **Components to include:** (list metadata types and specific member names)
- **Components to delete:** (list if applicable — note any Lightning page dependencies)

## Package.xml Draft

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members><!-- component name or * for all custom --></members>
    <name><!-- MetadataTypeName --></name>
  </types>
  <version>66.0</version>
</Package>
```

## destructiveChanges.xml Draft (if deleting components)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members><!-- exact component name — no wildcards --></members>
    <name><!-- MetadataTypeName --></name>
  </types>
</Package>
```

**Deletion order:** [ ] destructiveChanges.xml (delete before additions)  [ ] destructiveChangesPost.xml (delete after additions)

Reason for ordering choice: ___

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Pattern 1 — Retrieve targeted subset
- [ ] Pattern 2 — Deploy Apex with test level selection
- [ ] Pattern 3 — Delete with dependency cleanup (destructiveChangesPost.xml)

## Deployment Test Level (if deploying to production)

- [ ] RunLocalTests — safe default when Apex is included
- [ ] RunSpecifiedTests — faster; verify per-class 75% coverage first
- [ ] RunRelevantTests (Beta) — auto-selects relevant tests; available API v58+
- [ ] NoTestRun — only valid for sandbox deployments

Test classes to run (if RunSpecifiedTests): ___

## Pre-flight Checklist

- [ ] `<version>` tag is present and matches current API version
- [ ] All `<members>` values use correct full name format (e.g., `Object.Field__c` for custom fields)
- [ ] Standard objects are named individually — wildcard does not cover standard objects
- [ ] destructiveChanges.xml does not use wildcards
- [ ] If deleting a component referenced by Apex, destructiveChangesPost.xml is used and the referencing class is updated in the same deployment
- [ ] Components on active Lightning pages are not in destructiveChanges.xml
- [ ] Each Apex class/trigger in the deployment has individual 75%+ test coverage
- [ ] Deploying user has required permissions

## Notes

Record any deviations from the standard pattern and why.
