# Well-Architected Notes — OmniStudio Testing Patterns

## Relevant Pillars

- **Reliability** — Structured testing (DataRaptor Preview, IP step isolation, deployed user-context testing) prevents silent data corruption and navigation failures from reaching production users.
- **Operational Excellence** — Documented test plans for OmniScript/IP/DataRaptor components reduce mean time to diagnose failures. Per-step IP test execution enables targeted debugging without full redeployment cycles.
- **Security** — Testing as the target user profile (not admin) is the only way to validate FLS enforcement, sharing rule visibility, and Experience Cloud guest-user access restrictions. Skipping this step is an architectural security gap.

## Architectural Tradeoffs

**In-designer testing vs. deployed user-context testing:** In-designer tools (Preview, IP Test Execution, DataRaptor Preview) are fast and require no deployment, but all run as admin and skip Navigation Actions. Deployed user-context testing is slower and requires a sandbox environment, but it is the only method that catches permission gaps and end-to-end flow failures. A robust testing strategy uses both in sequence, not one instead of the other.

**UTAM automation vs. manual testing:** UTAM provides repeatable regression coverage and can be integrated into a CI/CD pipeline, but it has a high setup cost (page objects must be maintained, runtime-specific), and tests are brittle across managed-package HTML changes. Manual deployed testing is faster to stand up but does not scale to regression. For complex enterprise OmniScripts used at scale, UTAM investment is justified. For simpler implementations, documented manual test scripts per target user profile are a proportionate alternative.

## Anti-Patterns

1. **Admin-Only Testing** — Running all tests exclusively in OmniScript Preview or as the System Administrator user, then marking the component ready for production. This guarantees that permission-related failures are discovered in production rather than testing.

2. **Ignoring vlcStatus warnings in IP testing** — Treating `vlcStatus: "warning"` as acceptable during IP step testing without investigating the downstream data impact. Warning-status steps continue execution but can silently corrupt downstream data by passing null or default values to consuming steps.

3. **Using wrong UTAM library for runtime** — Copying UTAM page objects from documentation or community examples without confirming they match the org's runtime (Package vs. Standard). Tests that reference Package Runtime DOM selectors fail silently or with misleading errors on Standard Runtime orgs.

## Official Sources Used

- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Preview and Test an OmniScript — https://help.salesforce.com/s/articleView?id=sf.os_preview_and_test_omniscript.htm&type=5
- Debug and Activate an Integration Procedure — https://help.salesforce.com/s/articleView?id=sf.os_debug_and_activate_integration_procedure.htm&type=5
- UI Test Automation Model (UTAM) — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.test_utam
- OmniStudio Integration Procedures — https://help.salesforce.com/s/articleView?id=sf.os_integration_procedures.htm&type=5
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
