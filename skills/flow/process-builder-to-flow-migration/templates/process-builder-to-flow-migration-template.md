# Process Builder to Flow Migration — Work Template

Use this template when migrating Process Builder processes to record-triggered Flows.

## Scope

**Object(s) affected:** (list each Salesforce object)

**Processes to migrate:** (list each Process Builder process by name and object)

**Migration approach:** Tool / Manual rebuild / Mixed

## Pre-Migration Inventory

| Process Name | Object | Action Types | ISCHANGED/ISNEW Criteria? | Scheduled Actions? | Tool-Eligible? |
|---|---|---|---|---|---|
| (process name) | (object) | field update, email alert | No | No | Yes |
| (process name) | (object) | invocable Apex, task | No | Yes | No — manual rebuild |

## Migration Checklist

### Before Migration
- [ ] All processes inventoried with action types identified
- [ ] ISCHANGED/ISNEW criteria noted; those processes marked for manual rebuild
- [ ] Pending scheduled actions in flight quantified and cutover timing decided
- [ ] All automation on affected objects cataloged (other flows, Apex triggers)
- [ ] Flow Trigger Explorer reviewed for existing priority assignments

### During Migration (per process)
- [ ] Ran Migrate to Flow tool (for tool-eligible) OR built manual replacement in Flow Builder
- [ ] Generated flow reviewed in Flow Builder against original process criteria
- [ ] ISCHANGED/ISNEW criteria rebuilt with `{!$Record__Prior.FieldName}` comparisons
- [ ] Fault paths added to all DML elements
- [ ] Flow Trigger Explorer priority assigned (no conflicts with existing flows)
- [ ] Tested in sandbox with 200+ records — bulk test passed
- [ ] No SOQL or DML inside loops confirmed

### At Activation
- [ ] Replacement flow activated
- [ ] Source Process Builder process deactivated in same window
- [ ] Verified only one automation system active per object
- [ ] Monitored debug logs for first 24 hours post-activation

## Flow Trigger Explorer Priority Map

| Object | Flow Name | Priority | Trigger Condition | Notes |
|---|---|---|---|---|
| (Opportunity) | (Opportunity_FieldUpdate_Flow) | 10 | Record is updated | Replaces PB process created 2020-01-15 |

## Manual Rebuild Notes

For each process requiring manual rebuild, record:

**Process:** (name)
**Unsupported element:** (ISCHANGED criteria / invocable Apex / task creation / scheduled action)
**Rebuild approach:** (describe how you rebuilt it in Flow Builder)
**Test assertion:** (what you checked to verify correctness)

## Rollback Plan

If issues are found post-activation:
1. Deactivate the replacement Flow
2. Re-activate the original Process Builder process
3. Investigate root cause before re-attempting migration
