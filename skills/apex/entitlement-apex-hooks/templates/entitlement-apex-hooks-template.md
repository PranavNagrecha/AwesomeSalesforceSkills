# Entitlement Apex Hooks — Work Template

Use this template when implementing or reviewing Apex code that interacts with CaseMilestone records.

## Scope

**Skill:** `entitlement-apex-hooks`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Entitlement Management enabled:** Yes / No
- **Active entitlement process name(s):**
- **MilestoneType.Name values to target:** (exact strings, case-sensitive)
- **Trigger condition:** (e.g., Case.Status changes from 'New' to any other value)
- **Is violation detection required:** Yes / No
- **Existing triggers on Case:** (list any — check for bulk-safety interactions)

## Pattern Selected

Choose one:

- [ ] **Synchronous completion** — `after update` trigger on Case writes `CompletionDate`
- [ ] **Violation detection** — Scheduled Apex polls `IsViolated = true AND CompletionDate = null`
- [ ] **Both** — trigger for completion + scheduled job for violation escalation

## Implementation Checklist

### Trigger / Service Class

- [ ] Trigger context is `after update` (not `before update`)
- [ ] `CompletionDate = System.now()` used — NOT `IsCompleted = true`
- [ ] No write to `SlaExitDate`
- [ ] IDs collected into a `Set<Id>` before SOQL (no SOQL inside loop)
- [ ] SOQL filters: `CaseId IN :idSet AND CompletionDate = null AND MilestoneType.Name = '<exact name>'`
- [ ] DML issued on list, not inside loop

### Scheduled Apex (if applicable)

- [ ] Implements `Schedulable`
- [ ] Query: `IsViolated = true AND CompletionDate = null`
- [ ] Idempotency guard present (e.g., `Case.ViolationEscalated__c = false`)
- [ ] `LIMIT 200` on query to stay within synchronous governor limits
- [ ] Scheduled via `System.schedule()` at appropriate interval

### Test Class

- [ ] `@testSetup` creates: Account > Entitlement > EntitlementProcess > MilestoneType > EntitlementProcessMilestone > Case with EntitlementId
- [ ] Test asserts `CompletionDate` is non-null after trigger runs
- [ ] Test asserts `IsCompleted` reads back as `true`
- [ ] Bulk test: 200 cases processed in one trigger invocation
- [ ] Violation detection test: manually set `TargetDate` to past date in test setup to simulate violation

## Notes

(Record any deviations from the standard pattern and why.)
