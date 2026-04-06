# Trigger And Flow Coexistence — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `trigger-and-flow-coexistence`

**Object under analysis:** _______________

**Request summary:** (fill in what the user asked for)

## Automation Inventory

List every automation active on the target object.

### Before-Save Timing (Step 3)

| # | Automation Name | Type (Trigger/Flow) | Fields Read | Fields Written | Owner (Team/Person) |
|---|-----------------|---------------------|-------------|----------------|---------------------|
| 1 | _______________ | __________________ | ___________ | ______________ | ___________________ |
| 2 | _______________ | __________________ | ___________ | ______________ | ___________________ |
| 3 | _______________ | __________________ | ___________ | ______________ | ___________________ |

### After-Save Timing (Steps 4 / 15)

| # | Automation Name | Type (Trigger/Flow/WFR/PB) | DML Performed | Target Object | Fields Written on Target |
|---|-----------------|---------------------------|---------------|---------------|--------------------------|
| 1 | _______________ | _________________________ | _____________ | _____________ | ________________________ |
| 2 | _______________ | _________________________ | _____________ | _____________ | ________________________ |

### Legacy Automations (Workflow Rules / Process Builder)

| # | Automation Name | Type | Field Updates | Re-fires Triggers? |
|---|-----------------|------|---------------|---------------------|
| 1 | _______________ | ____ | _____________ | Yes / No            |
| 2 | _______________ | ____ | _____________ | Yes / No            |

## Field-Write Collision Analysis

| Field API Name | Writer 1 (Automation + Timing) | Writer 2 (Automation + Timing) | Conflict? | Resolution |
|----------------|-------------------------------|-------------------------------|-----------|------------|
| ______________ | _____________________________ | _____________________________ | Yes / No  | __________ |
| ______________ | _____________________________ | _____________________________ | Yes / No  | __________ |

## Recursion Path Analysis

| Path | Step 1 | Step 2 | Step 3 | Guarded? | Guard Mechanism |
|------|--------|--------|--------|----------|-----------------|
| 1    | ______ | ______ | ______ | Yes / No | _______________ |
| 2    | ______ | ______ | ______ | Yes / No | _______________ |

## Resolution Plan

### Field Ownership Changes

- [ ] Field `___________`: Transfer ownership from `___________` to `___________`
- [ ] Field `___________`: Consolidate into `___________`

### Recursion Guards to Implement

- [ ] Guard type: Static variable + InvocableMethod / Hidden checkbox / Field-value check
- [ ] Apex class: _______________
- [ ] Flow Decision element: _______________

### Legacy Migration

- [ ] Workflow rule `___________`: Migrate to _____________ by __________
- [ ] Process Builder `___________`: Migrate to _____________ by __________

## Consolidation Roadmap (if applicable)

**Target state:** Single entry point per timing slot using: [ ] Triggers [ ] Flows
**Timeline:** _______________
**Phase 1:** _______________
**Phase 2:** _______________

## Review Checklist

- [ ] Automation inventory is complete (no automations missing)
- [ ] No unresolved field-write collisions
- [ ] All recursion paths are guarded
- [ ] Flow Trigger Explorer confirms expected Flow order in sandbox
- [ ] Bulk DML test (200+ records) passes
- [ ] Automation inventory document is stored in shared location
- [ ] Legacy automation migration plan is documented

## Notes

Record any deviations from the standard pattern and why.
