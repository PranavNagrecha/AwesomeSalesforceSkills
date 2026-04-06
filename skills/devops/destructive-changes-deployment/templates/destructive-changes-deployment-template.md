# Destructive Changes Deployment — Work Template

Use this template when working on a destructive deployment task.

## Scope

**Skill:** `destructive-changes-deployment`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Components to delete (type + API name):
  - `<MetadataType>`: `<APIName>`
  - `<MetadataType>`: `<APIName>`
- Target org alias or auth:
- Known inbound references (components that reference each deleted component):
- Undeletable types confirmed absent (Record Types, Picklist values, active Flows): Yes / No

## Manifest Variant Selected

- [ ] `destructiveChangesPre.xml` — deletions fire before additions (standalone deletions or rename conflicts)
- [ ] `destructiveChanges.xml` — plain variant, equivalent to pre (legacy / simple cases)
- [ ] `destructiveChangesPost.xml` — deletions fire after additions (referencing component updated in same deploy)

**Reason for choice:**

## Manifest Draft

```xml
<!-- destructiveChanges[Pre|Post].xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members><!-- ParentObject.MemberName or just MemberName --></members>
        <name><!-- MetadataTypeName e.g. CustomField, ApexClass, LightningComponentBundle --></name>
    </types>
</Package>
```

## Companion `package.xml` Draft

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Add <types> blocks here if any components are being added/updated in this deploy -->
    <version>61.0</version>
</Package>
```

## Deployment Command

```bash
sf project deploy start \
  --manifest package.xml \
  --pre-destructive-changes destructiveChangesPre.xml \
  --target-org <alias>

# OR for post variant:
sf project deploy start \
  --manifest package.xml \
  --post-destructive-changes destructiveChangesPost.xml \
  --target-org <alias>
```

## Pre-Deploy Checklist

- [ ] All members listed by exact API name — no wildcards
- [ ] No `<version>` element in any destructive manifest file
- [ ] Manifest variant (pre/post/plain) matches dependency ordering requirement
- [ ] No undeletable component types in manifest (Record Types, Picklist values, active Flow versions)
- [ ] Valid companion `package.xml` present with API version
- [ ] Correct CLI flag matches the manifest filename (pre vs post)
- [ ] Checker script run: `python3 scripts/check_destructive.py --manifest-dir <path>`

## Post-Deploy Verification

- [ ] Deployment status shows Succeeded
- [ ] Deleted component is absent in Setup / metadata retrieval
- [ ] Local source files for deleted components removed from project
- [ ] Team notified to remove files from their local branches

## Notes

Record any deviations from the standard pattern and why.
