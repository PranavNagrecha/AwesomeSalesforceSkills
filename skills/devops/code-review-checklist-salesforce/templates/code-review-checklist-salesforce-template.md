# Code Review Checklist Salesforce — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `code-review-checklist-salesforce`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Setting / configuration: (entry points, package vs org code, API context)
- Known constraints: (batch size, async type, profile under test)
- Failure modes to watch for: (limits, FLS exceptions, partial DML)

## Approach

Which pattern from SKILL.md applies (bulkified handler, USER_MODE reads, etc.) and why.

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] No SOQL, DML, or callouts inside loops over query or trigger row collections; totals stay within per-transaction limits for the expected path.
- [ ] Triggers and synchronous services tolerate 200 records without redundant queries or per-row DML.
- [ ] Sharing model is explicit and justified; user-facing queries enforce FLS/CRUD (`WITH USER_MODE`, `WITH SECURITY_ENFORCED`, or `stripInaccessible` on results as appropriate).
- [ ] Dynamic SOQL/SOSL uses binding or escaping; no string concatenation of raw end-user input into queries.
- [ ] Tests assert outcomes (not only coverage); include bulk and negative cases where behavior branches; avoid `SeeAllData=true` unless documented and unavoidable.
- [ ] Async entry points (`execute`, `start`, schedulable `execute`) respect queueable/batch limits and do not chain blindly into unbounded recursion.
- [ ] Naming matches team conventions and Apex naming guidance; no `System.debug` left for production paths unless behind diagnostic flags.

## Notes

Record any deviations from the standard pattern and why.
