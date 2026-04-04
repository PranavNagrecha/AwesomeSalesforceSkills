---
name: uat-and-acceptance-criteria
description: "Use this skill when writing acceptance criteria for Salesforce features, structuring UAT test scripts from user stories, classifying defects found during UAT, or planning regression testing before a Salesforce release. Trigger keywords: UAT, user acceptance testing, test script, acceptance criteria, defect classification, regression testing, test plan, test case. NOT for automated testing (use flow-testing or apex-test-class-standards). NOT for writing user stories or eliciting requirements (use requirements-gathering-for-sf). NOT for setting up sandboxes or environment strategy (use sandbox-strategy)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I write UAT test scripts for a Salesforce release"
  - "what format should acceptance criteria use for a Salesforce feature"
  - "how to classify defects found during Salesforce UAT testing"
  - "how to plan regression testing for a Salesforce release"
  - "UAT test script template for Salesforce features"
  - "how to structure a test case for a Salesforce validation rule or flow"
  - "how do I know if a Salesforce feature passed UAT"
tags:
  - uat
  - acceptance-criteria
  - testing
  - business-analysis
  - defect-management
inputs:
  - "User stories with acceptance criteria for the feature being tested"
  - "Salesforce sandbox or org environment where the build is deployed"
  - "List of personas (profiles/permission sets) that interact with the feature"
  - "Description of the feature: objects, fields, automation, pages involved"
outputs:
  - "Structured UAT test script with test steps, expected results, and pass/fail columns"
  - "Defect log with Salesforce-specific severity classification"
  - "Regression test plan identifying which existing features must be re-tested"
  - "UAT sign-off checklist for the feature"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---

# UAT and Acceptance Criteria

This skill activates when a Business Analyst, admin, or QA lead needs to translate Salesforce user stories into executable test scripts, run structured UAT, classify defects using a Salesforce-appropriate severity model, and plan regression testing before a release goes to production.

---

## Before Starting

Gather this context before beginning UAT work:

- **What sandbox type is being used?** Full sandboxes have production data copies and reflect real user volume. Partial sandboxes have a data subset. Developer sandboxes have no production data — test data must be created manually. UAT should ideally run in a Full or Partial sandbox so that data volume, sharing rules, and record types match production behavior.
- **Which user personas are in scope?** Testing one profile may not reveal a field-level security (FLS) gap visible to a different profile. Identify every profile or permission set that will use the feature and ensure test execution covers each.
- **Is time-based automation in scope?** Time-based workflow rules and scheduled flows cannot be advanced manually in sandbox. If a feature includes time-triggered automation, plan for either manual triggering via Developer Console or a separate automation testing environment.
- **Have all acceptance criteria been confirmed as testable?** Acceptance criteria must be boolean (observable pass/fail) before test scripts are written. Criteria like "the page should be fast" or "the form should be intuitive" cannot be tested — they must be rewritten before UAT begins.

---

## Core Concepts

### Acceptance Criteria Format for Salesforce

Acceptance criteria are the conditions a feature must satisfy to be considered complete. In Salesforce projects, the Trailhead BA curriculum specifies the **if/then format**: each criterion takes the form "If [precondition or user action], then [observable Salesforce outcome]."

This format is preferable to vague statements because it forces specificity about:
- The user state (which profile, which record state, which field value)
- The Salesforce response (which field becomes required/visible, which automation fires, which error message appears)

**Salesforce-specific acceptance criteria checklist per story:**
- Field-level behavior: "If the user has the Sales Rep profile and opens an Account record, then the Credit Limit field is read-only."
- Automation behavior: "If the Opportunity Stage is set to Closed Won, then a Task is automatically created for the Account owner with subject 'Post-Sale Follow-Up' and due date 7 days from today."
- Validation rule: "If the user saves a Case without a Subject, then the save fails with error message 'Subject is required.'"
- Sharing/visibility: "If a user with the Service Agent role opens a Contact not linked to their account, then the record is not visible."
- Report/dashboard: "If the Sales Manager runs the Q1 Pipeline report, then only Opportunities with Close Date in Q1 of the current year and Stage not equal to Closed Lost appear."

Every acceptance criterion must map to exactly one test case in the UAT script.

### UAT Test Script Structure

A Salesforce UAT test script is a table where each row is one acceptance criterion. The standard columns for a Salesforce UAT test script are:

| Column | Content |
|--------|---------|
| Test Case ID | Unique ID, e.g., TC-001 |
| User Story ID | Cross-reference to the source story |
| Test Scenario | Human-readable description of what is being tested |
| Preconditions | Required setup: logged in as [profile], record in [state], sandbox [name] |
| Test Steps | Numbered steps the tester executes, written at click-level detail |
| Expected Result | The exact observable Salesforce outcome per the acceptance criterion |
| Actual Result | Recorded by the tester during execution |
| Pass / Fail | Boolean result |
| Defect ID | Link to defect if Fail |
| Tester | Who executed the test |
| Date Executed | When the test ran |

Test steps must be written at a level of detail that allows someone unfamiliar with the feature to execute them without interpretation. "Go to Opportunities" is insufficient. "Navigate to the App Launcher, select Sales, then click Opportunities in the navigation bar" is correct.

### Defect Classification for Salesforce

Not every defect found in UAT has the same impact. A Salesforce-specific severity model:

| Severity | Definition | Salesforce Examples |
|----------|-----------|---------------------|
| P1 — Critical | Feature is completely broken. Testing cannot continue. Data loss risk or security exposure. | Automation fires on wrong records; sharing rule exposes records to wrong profile; flow deletes wrong records |
| P2 — Major | Feature is partially broken. A core use case does not work, but a workaround exists. | Required field not enforced; validation rule fires on wrong condition; page layout missing critical field |
| P3 — Minor | Feature works but behavior deviates from acceptance criteria in a non-blocking way. | Wrong field label; help text missing; list view default sort incorrect; email template formatting issue |
| P4 — Cosmetic | No functional impact. | Capitalization inconsistency; extra space in field label; non-breaking UI misalignment |

In addition to severity, classify defects by Salesforce component type for faster routing:
- **Configuration defect** — field, page layout, record type, picklist value (admin fixes)
- **Automation defect** — Flow, Workflow Rule, Approval Process logic error (admin or dev fixes)
- **Security defect** — FLS, sharing rule, OWD, profile permission error (admin fixes — prioritize P1/P2 immediately)
- **Data defect** — existing records in bad state due to migration or earlier defect (data team fixes)
- **Integration defect** — callout, external ID, sync error (dev team fixes)

A defect log is maintained per release. Each entry includes: Defect ID, Test Case ID, Component type, Severity, Description of actual vs expected behavior, Steps to reproduce, Assignee, Status (Open/In Progress/Fixed/Closed), and Retest result.

### Regression Testing Planning

Every Salesforce release carries regression risk. Changes to shared components — page layouts, record types, validation rules, profiles, flows — can break features that were previously working.

Before each release, compile a regression test list using this process:

1. **Identify changed components.** List every field, object, flow, validation rule, profile, page layout, or sharing rule modified in the release.
2. **Map each component to existing features.** For each changed component, ask: "Which existing business processes use this component?" The fit-gap table and existing test scripts from prior releases are the input.
3. **Select regression test cases.** For each affected existing feature, select the minimum set of test cases that validates the core user journey. Do not re-run every test from every prior release — focus on the path that exercises the changed component.
4. **Prioritize P1/P2 scenarios.** Regression test cases that cover data integrity, security, and core automation should always be included.
5. **Automate repetitive regression checks.** Flows that run in Every Release should be documented as prime candidates for Apex test automation (not manual UAT).

---

## Common Patterns

### Pattern: Test Script from Acceptance Criteria

**When to use:** A completed Salesforce feature is ready for UAT. User stories with acceptance criteria exist. The BA or QA lead needs to convert those criteria into executable test cases.

**How it works:**
1. Review each acceptance criterion in each user story.
2. For each criterion, create one test case row in the test script table.
3. Write preconditions: log in as [profile], navigate to [record or app], ensure [field/record state].
4. Decompose the criterion into numbered click-level test steps.
5. Capture the expected result verbatim from the acceptance criterion.
6. Identify which other profiles or permission sets must run the same test with potentially different expected results (FLS testing).
7. Identify any data setup required (e.g., "an Account with Type = Customer must exist") and document in the Preconditions column.
8. Schedule a tester from the business (end user, not the builder) to execute the test.

**Why not to have the builder test their own work:** The builder knows how to avoid the edge cases they did not build for. Business users find defects that builders never anticipate because they use the feature in ways the builder did not expect.

### Pattern: Regression Test Planning for a Release

**When to use:** A Salesforce release is ready for deployment to production. The release includes changes to shared components and the team needs to verify no regressions were introduced.

**How it works:**
1. Produce a change inventory: all metadata changed in this release.
2. For each metadata component, identify which business processes it participates in.
3. For each affected process, retrieve the UAT test script from the prior release.
4. Select the subset of test cases that exercise the changed component directly.
5. Add any new test cases for new features in this release.
6. Execute the combined set in the UAT sandbox that mirrors production configuration.
7. Defects from regression tests are classified and triaged identically to UAT defects.

### Pattern: UAT Sign-Off

**When to use:** UAT is complete and the team needs a formal go/no-go decision for production deployment.

**How it works:**
1. Count all test cases by status: Passed, Failed (open defects), Failed (deferred).
2. Apply the go-criteria: zero P1 open, zero P2 open (or approved exception), all P3/P4 logged and acknowledged.
3. Obtain business owner sign-off on any deferred defects — these become known issues with owners and target fix dates.
4. Document the sign-off: who approved, date, sandbox used, version of the build tested.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Acceptance criteria is vague ("should be easy to use") | Rewrite as if/then before writing test cases | Vague criteria cannot produce pass/fail results — they produce opinion |
| Two profiles see the same feature differently | Write separate test cases per profile | FLS and page layout assignments vary by profile — a P1 security defect may be invisible from the wrong profile |
| Feature includes time-based automation | Use Developer Console to execute scheduled jobs in advance, or mock with a future date trigger | Time-triggered flows cannot be advanced by simply waiting in a sandbox |
| Defect found in regression is P1 | Stop UAT, block the release, route immediately to build team | P1 defects in regression mean a prior working feature is now broken |
| Business owner wants to skip regression testing | Document the risk formally; require explicit sign-off | Skipping regression and finding a P1 in production is more expensive than a 2-hour regression pass |
| Test environment differs from production (missing data, different OWD) | Document sandbox limitations in test preconditions; flag as a test risk | Tests run against an unrepresentative environment produce misleading results |
| Build team fixes a defect between UAT cycles | Require a targeted retest of the specific test case that failed | Do not assume the fix is correct without executing the original failing test case |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before declaring UAT complete and signing off for production deployment:

- [ ] Every acceptance criterion has a corresponding test case in the test script
- [ ] Test cases cover every profile/permission set that uses the feature
- [ ] Test preconditions specify the exact sandbox, user, and record state required
- [ ] Test steps are written at click-level detail — executable without interpretation
- [ ] Every defect is classified by severity (P1–P4) and component type
- [ ] All P1 and P2 defects are resolved or have a documented go-live exception approved by the business owner
- [ ] Regression test cases are identified and executed for any shared components that changed
- [ ] Business owner has formally signed off (name, date, sandbox, build version documented)
- [ ] Deferred defects have owners and target resolution dates
- [ ] Test results and defect log are stored in a project artifact location (not in the tester's inbox)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Email alerts are suppressed in sandbox by default** — Salesforce sandboxes have email deliverability set to "System email only" by default. Email alerts triggered by flows or approval processes will not be delivered to end users during UAT. Testers who expect to receive an email as part of an acceptance criterion will see a false failure. Before UAT, confirm the sandbox email deliverability setting (Setup → Deliverability) is set to "All Email" for the UAT environment.

2. **Sharing recalculation is asynchronous** — When a sharing rule is added or a record is reparented, the sharing recalculation job runs asynchronously. If a tester immediately checks record visibility after triggering a sharing change, they may see the old sharing state and report a false failure. Allow a few minutes after sharing-related actions before testing record visibility.

3. **Record type and profile assignments may differ from production** — If the UAT sandbox was refreshed months ago, profile assignments, record type defaults, and page layout assignments may not match production. Changes made to the sandbox for other projects can silently corrupt the test environment. Before UAT, verify that the sandbox configuration matches production for the personas being tested.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| UAT Test Script | Table of test cases derived from acceptance criteria, with steps, expected results, actual results, and pass/fail tracking |
| Defect Log | Structured log of all defects with severity, component type, status, and owner |
| Regression Test Plan | List of test cases selected for regression based on changed components |
| UAT Sign-Off Document | Formal record of business owner approval: approver name, date, sandbox, build version, known issues list |

---

## Related Skills

- requirements-gathering-for-sf — use before UAT to elicit and write the user stories and acceptance criteria that UAT test scripts are derived from
- sandbox-strategy — use to select and configure the appropriate sandbox environment for UAT
- flow-testing — use when acceptance criteria cover Flow automation that should be covered by automated tests, not manual UAT
- apex-test-class-standards — use for automated Apex test coverage, not manual UAT
