---
name: omnistudio-testing-patterns
description: "Use when testing or validating OmniStudio components — OmniScript preview, Integration Procedure step debugging, DataRaptor field-mapping validation, and end-to-end UTAM-based automation. NOT for Apex unit testing or standard Flow debugging."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "How do I test my OmniScript before deploying it to users?"
  - "Integration Procedure is returning an error — how do I debug which step is failing?"
  - "DataRaptor is not mapping fields correctly, how do I test it without deploying?"
  - "OmniScript Preview passes but users get errors in production"
  - "How do I set up automated testing for OmniStudio components in a CI/CD pipeline?"
tags:
  - omnistudio
  - testing
  - omnistudio-testing-patterns
  - integration-procedure
  - datarapter
  - utam
  - debugging
inputs:
  - "OmniScript or Integration Procedure component name and version"
  - "Runtime type: Package Runtime (managed package) or Standard/Core Runtime"
  - "Test user context: admin, community guest, named permission set user"
  - "Named Credentials or external callout details if testing Integration Procedures"
outputs:
  - "Test execution plan for OmniScript Preview, IP Test Execution, and DataRaptor Preview"
  - "Debug analysis of vlcStatus, errorMessage, and step timing from IP test runs"
  - "UTAM test scaffold for end-to-end automation (if required)"
  - "Checklist of Preview-mode gaps that require environment-level verification"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# OmniStudio Testing Patterns

This skill activates when a practitioner needs to test, validate, or debug OmniStudio components — OmniScripts, Integration Procedures, or DataRaptors — before or after deployment. It covers the three built-in manual test surfaces Salesforce provides, their known gaps, and what end-to-end automated testing actually requires.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Runtime type matters**: Determine whether the org uses Package Runtime (managed package, OmniStudio namespace) or Standard/Core Runtime (native metadata). UTAM automation targets differ between the two because HTML rendering differs across runtimes.
- **Most common wrong assumption**: Practitioners treat OmniScript Preview mode as a full simulation. It is not — Preview always runs in the admin user security context, silently skips Navigation Actions, and does not exercise Named Credentials or Experience Cloud guest-user permissions. A passing Preview does not mean the component works for end users.
- **No first-party automated test framework exists**: Salesforce does not ship a built-in automated testing library for OmniStudio. End-to-end automation requires UTAM (UI Test Automation Model), Selenium, or equivalent browser automation tools applied against a deployed runtime.

---

## Core Concepts

### OmniScript Preview Mode

OmniScript Preview is an in-designer tool accessible from the OmniScript designer canvas. It renders the script using the designer's admin security context — not the target user's context — and skips Navigation Actions (Save/Navigate steps). It validates JSON structure, conditional rendering logic, and basic step sequencing, but it cannot test permission-controlled data access, FLS-gated fields, or Experience Cloud guest-user behavior. Preview is mandatory as a first-pass gate but must never be treated as final sign-off.

### Integration Procedure Test Execution

Integration Procedure (IP) designers include a per-step test execution panel that accepts a JSON input payload and returns the full step response including `vlcStatus` (success/error/warning), `errorMessage`, `responseSize`, and step timing. Each step can be tested in isolation by providing mock input — this allows identification of which step in a multi-step IP is failing without deploying and running the full chain. Named Credentials are evaluated at test execution time, making this the correct tool for testing IP callouts — but it still runs as the admin user.

### DataRaptor Preview

DataRaptor Extract, Transform, and Load components all have a Preview/Test tab in their designer. Extract Preview accepts a record ID and returns field-mapped output; Transform Preview accepts a JSON input and shows the transformed output; Load Preview simulates a write operation. These are essential for validating field mapping formulas before wiring a DataRaptor into an Integration Procedure or OmniScript. DataRaptor Preview uses the admin context like the other tools.

### UTAM and Browser Automation

UTAM (UI Test Automation Model) is Salesforce's open-source framework for describing UI component interactions in a JSON page-object format that compiles into Selenium WebDriver commands. For OmniStudio, UTAM page objects exist for the runtime components (OmniScript elements, step navigation, submit actions). End-to-end testing with UTAM runs against a fully deployed org in the target user's security context, making it the only approach that catches permission gaps and Navigation Action behavior. UTAM page objects for managed-package HTML differ from Standard Runtime HTML — use the correct page object library for the org's runtime.

---

## Common Patterns

### Layered Three-Stage Testing

**When to use:** Any OmniScript with Integration Procedure callouts, multiple steps, and role-based conditional fields targeting non-admin users (e.g., Experience Cloud guests, community users with restricted profiles).

**How it works:**
1. Run DataRaptor Preview for each DataRaptor in the chain to confirm field mappings produce expected output.
2. Run Integration Procedure Test Execution step-by-step with a representative JSON payload. Confirm each step's `vlcStatus` is `success` and review timing for any step exceeding 5 seconds.
3. Run OmniScript Preview to validate conditional rendering, step-to-step navigation logic, and formula expressions.
4. Deploy to a scratch org or sandbox and run a UTAM-based or manual walkthrough as the actual target user (e.g., create a community guest test session or login-as the relevant profile).

**Why not Preview alone:** Preview always runs as admin, skips Navigation Actions, and does not test Named Credentials in the real user context. Skipping step 4 is the most common production defect path.

### Integration Procedure Step-Isolation Debugging

**When to use:** An IP is failing in production or staging and the error message from the OmniScript output is vague (e.g., "Integration Procedure Error" without step detail).

**How it works:**
1. Open the IP designer and navigate to the failing step's Test tab.
2. Construct a JSON input object representing the values that would flow into that step from prior steps. Use prior step outputs from a known-good run if available.
3. Execute the step and inspect the response JSON: `vlcStatus` of `error` with a populated `errorMessage` pinpoints the failure; `warning` status may continue execution but silently produce partial data.
4. If the step calls a Named Credential, confirm the credential is active and the integration user has access.
5. Fix at the step level and re-run the IP end-to-end before re-deploying.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| First-pass validation of OmniScript logic and rendering | OmniScript Preview | Fast, no deployment needed, validates JSON and conditional logic |
| Debug a failing IP step in isolation | IP Test Execution (per-step) | Pinpoints the exact step with vlcStatus + errorMessage, no redeployment needed |
| Validate DataRaptor field mappings | DataRaptor Preview/Test tab | Tests Extract/Transform/Load in isolation with real record IDs or mock JSON |
| Test with real user permissions and Navigation Actions | Deploy to sandbox + UTAM or manual test as target user | Preview and IP test always run as admin; only real user context catches permission gaps |
| CI/CD pipeline automated regression | UTAM with deployed sandbox | Only option for automated browser-level validation; requires maintained page objects |
| Validate Named Credential connectivity | IP Test Execution | Named Credentials are evaluated at IP test execution time; Preview does not call them |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the component type and runtime** — Determine whether the failing or to-be-tested component is an OmniScript, Integration Procedure, or DataRaptor, and whether the org uses Package Runtime or Standard/Core Runtime. This determines which test tool applies and which UTAM page objects to use.
2. **Run DataRaptor Preview for all DataRaptors in the chain** — Open each DataRaptor in the designer, navigate to the Preview/Test tab, supply a representative record ID or JSON payload, and confirm field mappings produce expected output. Fix any mapping errors before proceeding.
3. **Run IP Test Execution step-by-step** — For each Integration Procedure step, open the Test tab, supply the JSON input that would reach that step from prior steps, execute, and inspect `vlcStatus`, `errorMessage`, and timing. Resolve any step with a non-success status before testing the full IP end-to-end.
4. **Run OmniScript Preview** — Execute OmniScript Preview in the designer. Validate conditional rendering, required field logic, step navigation expressions, and formula outputs. Document any step that relies on Navigation Actions or user-context data — these cannot be validated in Preview.
5. **Deploy to sandbox and test as target user** — Deploy the component to a sandbox. Log in as (or use login-as for) a user with the target profile and permission set. Navigate the OmniScript or trigger the IP through the full runtime path, including any Experience Cloud or page-level embedding. Verify Navigation Actions execute, permissions are correct, and Named Credentials authenticate successfully.
6. **Run UTAM automation if a regression suite exists** — If the project maintains UTAM page objects, execute the relevant test suite against the sandbox. Review any failures against the specific page object library for the org's runtime.
7. **Document gaps before sign-off** — Record any scenarios that could not be covered by in-designer testing (guest-user edge cases, high-concurrency, Named Credential failures) and communicate them to the team before marking the component ready for production.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] DataRaptor Extract/Transform/Load components validated via Preview with representative test data
- [ ] All Integration Procedure steps tested in isolation with vlcStatus = success and no errorMessage
- [ ] OmniScript Preview completed; conditional rendering and step navigation confirmed correct
- [ ] Component deployed to sandbox and tested as the actual target user profile (not admin)
- [ ] Navigation Actions confirmed to execute correctly in deployed runtime
- [ ] Named Credentials confirmed active and accessible to the integration user
- [ ] UTAM or manual regression test completed if component is part of a regression suite

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Preview mode silently skips Navigation Actions** — OmniScript Preview does not execute steps of type Navigation Action (Save, Navigate, Cancel). A script that works perfectly in Preview can fail completely in production if a Navigation Action contains required logic or triggers downstream processes. Always verify Navigation Actions in a deployed runtime.
2. **Preview always runs as admin, masking FLS and permission issues** — All three in-designer test tools (OmniScript Preview, IP Test Execution, DataRaptor Preview) authenticate as the admin user. Field-Level Security, object permissions, sharing rules, and Experience Cloud guest-user restrictions are invisible in Preview. The most common defect pattern: Preview passes, admin-in-sandbox passes, community guest fails silently with a blank step or missing data.
3. **IP Test Execution vlcStatus `warning` continues execution but drops data** — A step that returns `vlcStatus: "warning"` does not abort the IP — execution continues to the next step. However, the step's output may be partial or empty, silently producing corrupted downstream data. Treat all non-`success` statuses as failures during testing.
4. **UTAM page objects differ between Package Runtime and Standard Runtime** — Managed-package (Package Runtime) OmniStudio components render with the `vlocity_ins` or `vlocity_cmt` namespace HTML structure; Standard Runtime uses the native structure. Using the wrong UTAM page object library against the wrong runtime produces false test failures. Always confirm the org's runtime before selecting UTAM page objects.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Test execution plan | Step-by-step test sequence for DataRaptor, IP, and OmniScript in-designer tools |
| IP debug analysis | JSON breakdown of each step's vlcStatus, errorMessage, and timing from IP test runs |
| Preview gap checklist | List of scenarios Preview cannot validate that require deployed-runtime testing |
| UTAM scaffold (if applicable) | Starter page object and test runner configuration for automated browser testing |

---

## Related Skills

- omnistudio-ci-cd-patterns — Use alongside this skill for deploying tested components through DataPack-based pipelines
- omnistudio-datapack-migration — Understand how DataPacks export/import affects component versions before testing
