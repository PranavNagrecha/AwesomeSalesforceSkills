# UAT Test Script — [Feature Name]

**Project:** [Project or Release Name]
**Sandbox:** [Sandbox Name and Type (Full/Partial/Developer)]
**Sandbox Refreshed:** [Date]
**UAT Start Date:** [Date]
**UAT End Date / Sign-Off Target:** [Date]
**Build Version / Deployment ID:** [Changeset or Deployment ID]

---

## Pre-UAT Environment Checklist

- [ ] Sandbox email deliverability set to "All Email" (Setup → Deliverability)
- [ ] Test users created with correct profiles and permission sets (no System Administrator)
- [ ] Test data created or confirmed in sandbox
- [ ] Record types, page layouts, and profile assignments verified to match production for in-scope profiles
- [ ] Tester briefing complete — testers understand the feature being tested

---

## Test Cases

| TC ID | US ID | Scenario | Preconditions | Steps | Expected Result | Actual Result | Pass/Fail | Defect ID | Tester | Date |
|-------|-------|----------|---------------|-------|-----------------|---------------|-----------|-----------|--------|------|
| TC-001 | US-XXX | [Describe the scenario being tested] | Logged in as: [Profile]. Record state: [describe]. Sandbox: [name]. | 1. [Step 1]. 2. [Step 2]. 3. [Step 3]. | [Verbatim from acceptance criterion] | | | | | |
| TC-002 | US-XXX | [Negative case — what should NOT happen] | Logged in as: [Profile]. Record state: [describe]. | 1. [Step 1]. 2. [Step 2]. | [Expected restriction or error message] | | | | | |

---

## Defect Log

| Defect ID | TC ID | Severity | Component Type | Description | Steps to Reproduce | Expected | Actual | Assignee | Status | Retest Date |
|-----------|-------|----------|----------------|-------------|-------------------|----------|--------|----------|--------|-------------|
| DEF-001 | TC-XXX | P1 / P2 / P3 / P4 | Configuration / Automation / Security / Data / Integration | [Brief description of the defect] | [Numbered steps] | [Expected result] | [Actual result] | [Admin/Dev/Data] | Open / Fixed / Closed | |

---

## Severity Reference

| Severity | Definition |
|----------|-----------|
| P1 — Critical | Feature completely broken; data loss or security exposure; testing cannot continue |
| P2 — Major | Core use case fails; workaround exists but feature does not meet acceptance criteria |
| P3 — Minor | Feature works but deviates from acceptance criteria in a non-blocking way |
| P4 — Cosmetic | No functional impact; label or formatting issue only |

---

## UAT Summary

| Metric | Count |
|--------|-------|
| Total Test Cases | |
| Passed | |
| Failed — P1 Open | |
| Failed — P2 Open | |
| Failed — P3/P4 (logged, deferred) | |
| Not Executed | |

**Go / No-Go Criteria:**
- [ ] Zero P1 open defects
- [ ] Zero P2 open defects (or documented go-live exception approved by business owner)
- [ ] All P3/P4 defects logged with owner and target date
- [ ] All deferred defects acknowledged by business owner in writing

---

## UAT Sign-Off

**Decision:** ☐ Go for Production  ☐ No-Go (defects must be resolved first)

| Name | Role | Signature / Date |
|------|------|-----------------|
| [Business Owner] | Business Owner | |
| [BA / QA Lead] | BA / QA | |
| [Admin / Release Manager] | Admin | |

**Known issues accepted for go-live:**
[List any deferred P3/P4 defects accepted by the business owner, with target fix date]

---

## Regression Coverage

| Changed Component | Component Type | Affected Features | Test Cases Included in Regression |
|-------------------|---------------|-------------------|----------------------------------|
| [Flow name] | Flow | [Feature 1], [Feature 2] | TC-001, TC-007 |
| [Validation Rule name] | Validation Rule | [Feature 3] | TC-012 |
| [Profile name] | Profile | [Feature 1], [Feature 4] | TC-003, TC-015 |
