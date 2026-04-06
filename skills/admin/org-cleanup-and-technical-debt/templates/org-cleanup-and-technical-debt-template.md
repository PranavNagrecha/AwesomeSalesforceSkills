# Org Cleanup And Technical Debt — Work Template

Use this template when executing org cleanup tasks.

## Scope

**Skill:** `org-cleanup-and-technical-debt`

**Request summary:** (fill in what the user asked for)

**Cleanup type:** (field cleanup | automation deactivation | Flow version pruning | destructive deploy | mixed)

## Context Gathered

- **Org edition and sandbox availability:**
- **Prior assessment available?** (Optimizer report, technical-debt-assessment findings, or manual inventory)
- **Metadata types targeted:**
- **Managed package components in scope?** (If yes, these cannot be deleted — document separately)
- **Source control available?** (If no, take a metadata backup before any destructive action)

## Cleanup Inventory

| # | Component API Name | Type | Data Population | Metadata References Found | Action | Status |
|---|---|---|---|---|---|---|
| 1 | | | Yes / No / Unknown | Yes / No / Unknown | Delete / Deactivate / Skip | Pending |
| 2 | | | | | | |
| 3 | | | | | | |

## Approach

Which pattern from SKILL.md applies? (Field Cleanup Sprint / Legacy Automation Deactivation / Flow Version Pruning / Mixed)

**Deletion method:** (Manual Setup / Destructive deploy / Tooling API)

**Testing plan:** (Sandbox name, test level, critical Flows to verify)

## Destructive Manifest (if applicable)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members><!-- component API names --></members>
        <name><!-- metadata type --></name>
    </types>
    <version>62.0</version>
</Package>
```

## Checklist

- [ ] All targeted metadata confirmed as unreferenced before deletion
- [ ] Deletions tested in sandbox with full Apex test run passing
- [ ] Destructive deploy manifest reviewed by a second person before production execution
- [ ] Deleted fields queue purged if field limit recovery was the goal
- [ ] Legacy automation deactivated for observation period before permanent deletion
- [ ] Post-cleanup Optimizer report generated showing resolved findings
- [ ] Cleanup actions documented for audit trail

## Notes

Record any deviations from the standard pattern and why.
