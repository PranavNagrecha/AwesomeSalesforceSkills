# FLS in Async Contexts — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `field-level-security-in-async-contexts`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record answers to the Before Starting questions from SKILL.md.

- Async entry point (Queueable / @future / Batch / Schedulable / PE-triggered):
- User identity at enqueue time (`UserInfo.getUserId()` value or class):
- User identity at execute time (likely the same? PE → Automated Process? Schedule → schedule creator?):
- Whose FLS the job MUST honor (originating user / service identity / system mode):
- Where data leaves the system (DML, callout, UI, log):

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1 — capture and assert originating user id (Queueable / @future / in-transaction Batch)
- [ ] Pattern 2 — cross-user FLS helper (Scheduled where user differs from data owner)
- [ ] Pattern 3 — filter at publish (PE-triggered subscribers)
- [ ] Run in declared system mode and document the contract

## Checklist

- [ ] Async class declares which user's FLS it honors (header comment)
- [ ] Originating user captured at enqueue and asserted in execute (where applicable)
- [ ] No `WITH USER_MODE` / `stripInaccessible` calls inside PE-triggered Apex
- [ ] No `System.runAs` outside test context
- [ ] `@future` parameters are primitives or collections of primitives
- [ ] Tests exercise the async path under multiple `runAs` users
- [ ] Tests cover at least one FLS-restricted user, not just sysadmin

## Notes

Record any deviations from the standard pattern and why.
