# Sales Engagement API — Work Template

Use this template when working on tasks that involve enrolling records in cadences, logging cadence step outcomes, or reacting to cadence lifecycle changes from Apex.

## Scope

**Skill:** `sales-engagement-api`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before writing any code.

- Sales Engagement license active in this org? (Yes / No / Unknown)
- Target object type (Lead / Contact / Person Account):
- Cadence name(s) already built in Cadence Builder UI:
- Assigned Sales Rep User ID(s) known:
- Active enrollment duplicate risk? (check ActionCadenceTracker via SOQL):
- Requirement type: enrollment only / step logging / CDC lifecycle reaction / all:
- Approximate enrollment volume per execution (for bulkification planning):

## Approach

Which pattern from SKILL.md applies? Mark one and explain why:

- [ ] Bulk Cadence Enrollment Service — invocable action with list inputs, result inspection
- [ ] CDC Async Apex Trigger — reaction to ActionCadenceTrackerChangeEvent
- [ ] Step Completion and Call Logging — completeActionCadenceStep invocable action or Task update
- [ ] Combination of the above — describe below

Reason for chosen pattern:

## Checklist

- [ ] Enrollment uses `assignTargetToSalesCadence` invocable action, not DML on ActionCadenceTracker
- [ ] All `Invocable.Action.Result` items checked with `isSuccess()` and errors logged or surfaced
- [ ] Pre-flight SOQL guard on `ActionCadenceTracker WHERE State = 'Active'` prevents duplicate submissions
- [ ] CDC used for lifecycle reactions (not standard Apex trigger on ActionCadenceTracker)
- [ ] Step completion uses `completeActionCadenceStep` or Task field updates — no direct DML on step tracker
- [ ] Invocable action called with a list of inputs, not one-at-a-time in a loop
- [ ] Service class uses `with sharing` to respect record-level security
- [ ] Tests use mocked/stubbed enrollment service; environment limitations documented
- [ ] Checker script run: `python3 scripts/check_sales_engagement_api.py --manifest-dir <path>`

## Notes

Record any deviations from the standard pattern and why.
