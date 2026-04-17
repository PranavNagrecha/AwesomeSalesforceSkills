# Workflow Rule to Flow Migration — Work Template

Use this template when migrating Workflow Rules to record-triggered Flows.

## Scope

**Object(s) affected:** (list each Salesforce object)

**Rules to migrate:** (list each Workflow Rule by name and object)

**Migration approach:** Tool / Manual rebuild / Mixed

## Pre-Migration Inventory

| Rule Name | Object | Entry Criteria | Action Types | ISCHANGED/ISNEW? | Time-Based? | Outbound Msg? | Tool-Eligible? |
|---|---|---|---|---|---|---|---|
| (rule name) | (object) | Status = "Active" | field update, email | No | No | No | Yes |
| (rule name) | (object) | ISCHANGED(Status) | task, time-based | Yes | Yes | No | No — manual |

## Outbound Message Pre-Check

For any rule with Outbound Message actions:

| Outbound Message Name | Endpoint URL | Definition Exists? | WSDL Reviewed? |
|---|---|---|---|
| (name) | (url) | Yes/No | Yes/No |

## Migration Checklist

### Before Migration
- [ ] All Workflow Rules inventoried with criteria and action types noted
- [ ] ISCHANGED/ISNEW criteria identified; those rules marked for manual rebuild
- [ ] Outbound Message definitions confirmed existing in Setup
- [ ] Time-based actions inventoried; cutover timing decided to minimize in-flight cancellations
- [ ] All automation on affected objects cataloged (other flows, Apex triggers, Process Builder)

### During Migration (per rule)
- [ ] Ran Migrate to Flow tool (tool-eligible) OR built manual replacement in Flow Builder
- [ ] Generated flow reviewed against original criteria in Flow Builder
- [ ] ISCHANGED/ISNEW criteria rebuilt with `{!$Record__Prior.FieldName}` comparisons
- [ ] Task creation rebuilt as Create Records elements
- [ ] Time-based actions rebuilt as Scheduled Paths
- [ ] Fault Paths added to all DML elements
- [ ] Flow Trigger Explorer priority assigned

### At Activation
- [ ] Replacement flow tested in sandbox with 200+ records
- [ ] Flow activated; Workflow Rule deactivated in same session
- [ ] Verified no double-execution (only Flow active on object)
- [ ] Monitored for first 24 hours post-activation

## Scheduled Path Map

| Rule Name | Original Time Trigger | Flow Scheduled Path Offset | Source Date Field |
|---|---|---|---|
| (rule) | 5 days after CloseDate | 5 Days After | Opportunity.CloseDate |

## Rollback Plan

If issues found post-activation:
1. Re-activate the Workflow Rule
2. Deactivate the replacement Flow
3. Investigate root cause before re-attempting
