# OmniStudio Testing Patterns — Work Template

Use this template when planning or executing OmniStudio component testing.

## Scope

**Skill:** `omnistudio-testing-patterns`

**Component under test:** (fill in: OmniScript name / Integration Procedure name / DataRaptor name)

**Component type:** [ ] OmniScript  [ ] Integration Procedure  [ ] DataRaptor  [ ] All (full chain)

**Org runtime:** [ ] Package Runtime (managed package)  [ ] Standard/Core Runtime

**Target user profile:** (fill in: e.g., Sales User, Community Guest, FSC Advisor)

## Pre-Test Context

- **Named Credentials in use:** (list any Named Credentials referenced by IPs in this chain)
- **Navigation Actions present:** (list step names that are Save / Navigate / Cancel types)
- **FLS-restricted fields:** (list any fields that have FLS restrictions on the target profile)
- **Experience Cloud deployment:** [ ] Yes  [ ] No

## Stage 1 — DataRaptor Preview

| DataRaptor Name | Type (Extract/Transform/Load) | Test Input | Expected Output | Status |
|---|---|---|---|---|
| | | | | [ ] Pass / [ ] Fail |
| | | | | [ ] Pass / [ ] Fail |

Notes on failures:

## Stage 2 — Integration Procedure Step Testing

**IP Name:**

| Step Name | Input JSON | vlcStatus | errorMessage | Timing (ms) | Status |
|---|---|---|---|---|---|
| | | | | | [ ] Pass / [ ] Fail |
| | | | | | [ ] Pass / [ ] Fail |

Notes on failures:

## Stage 3 — OmniScript Preview

**OmniScript Name:**

- [ ] Conditional rendering logic validated
- [ ] Required field validation confirmed
- [ ] Step navigation (non-Navigation-Action) confirmed
- [ ] Formula expression outputs correct
- **Navigation Actions skipped in Preview:** (list them — must be tested in Stage 4)

## Stage 4 — Deployed User-Context Testing

**Sandbox:** (sandbox name)

**Test user:** (username or profile used)

| Navigation Action Step | Expected Behavior | Actual Behavior | Status |
|---|---|---|---|
| | | | [ ] Pass / [ ] Fail |

- [ ] Named Credentials authenticated successfully under target user
- [ ] FLS-restricted fields visible only to authorized users
- [ ] Experience Cloud guest access tested (if applicable)

## Stage 5 — UTAM Automation (if applicable)

- **UTAM page object library:** (Package Runtime / Standard Runtime — confirm before running)
- **Test suite command:** `npx jest --testPathPattern=<pattern>`
- [ ] UTAM tests pass against sandbox

## Sign-Off

- [ ] All DataRaptors validated via Preview
- [ ] All IP steps pass with vlcStatus success
- [ ] OmniScript Preview completed
- [ ] Deployed user-context testing completed for all Navigation Actions
- [ ] No FLS-related permission gaps found
- [ ] Ready for production deployment

## Notes

(Record any deviations from the standard testing pattern and the rationale.)
