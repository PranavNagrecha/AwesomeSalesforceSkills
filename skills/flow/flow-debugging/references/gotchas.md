# Gotchas — Flow Debugging

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Debug Mode Commits Real DML in After-Save Flows Unless "Rollback" Is Checked

**What happens:** A practitioner uses Flow Builder Debug mode to test an after-save record-triggered flow in a sandbox. The flow includes a Create Records element that creates a related Task. After a few debug runs, the sandbox has dozens of orphaned Task records — each debug run committed real DML to the org.

**When it occurs:** Any debug run on an after-save record-triggered flow where the **"Roll back changes after the debug run"** checkbox is left unchecked. Before-save flows do not commit DML at the before-save boundary, but after-save flows run in a real transaction.

**How to avoid:** Always check **"Roll back changes after the debug run"** in the Debug modal when working with after-save flows that contain DML, unless you specifically need to verify committed data. Treat this as the default safe setting for all debug runs.

---

## Gotcha 2: Flow Interview Log Has a 7-Day Retention Window

**What happens:** A support ticket arrives on Day 9 describing a record-triggered flow failure that occurred on Day 1. The practitioner navigates to Setup > Flows > Flow Interview Log expecting to find the failing interview record but finds nothing. The failure left no trace in the system.

**When it occurs:** Flow Interview Log entries are automatically purged after approximately 7 days. There is no configuration option to extend retention within standard Salesforce. If the org does not have Event Monitoring enabled and the flow does not have a custom error-logging fault path, the diagnostic data is permanently gone.

**How to avoid:** Two mitigations:
1. Build fault paths in every critical flow that write `$Flow.FaultMessage` to a custom object (e.g., `Flow_Error_Log__c`) with timestamp, flow name, and the failing record ID. This creates durable diagnostic data even when the Interview Log expires.
2. If Event Monitoring is available, flow execution events are retained in the event log files for 30 days (or 1 year on some licenses).

---

## Gotcha 3: "Run As" Debug Does Not Simulate All Sharing Behaviors

**What happens:** A practitioner uses Debug > Run as a specific user to test whether a flow works for a standard user. The debug session completes without error, but the same user reports a failure in production. The practitioner is confused because the debug run succeeded.

**When it occurs:** The **Debug > Run as user** option in Flow Builder changes the running user context for record access and field-level security checks, but it does not fully replicate the user's complete runtime environment. Specifically:
- If the flow uses a Scheduled Path or is invoked via an API call from an external system, the actual execution context differs from a direct debug run.
- Platform Event-triggered flows cannot be debugged interactively at all — they must be diagnosed via Interview Logs.
- Flows running in System Context (without sharing) ignore the running user for record access, even in a Run As debug.

**How to avoid:** After a successful Run As debug, verify the flow's **"Run As"** setting in the Start element: "System Context - Without Sharing" bypasses record access entirely for that user regardless of who you debug as. Also verify that any Apex actions called from the flow run with sharing rules consistent with the flow context.

---

## Gotcha 4: Activating a New Flow Version Immediately Retires In-Progress Interviews

**What happens:** A screen flow is used for a multi-step wizard that users sometimes leave and resume later (via a Save for Later step). A developer activates a new flow version mid-day. Users who had paused interviews on the old version find their in-progress wizard sessions are no longer accessible and they must start over.

**When it occurs:** When a new version of a flow is activated, all in-progress (paused) interviews on the previous version become invalid. Salesforce does not migrate paused interview state across versions.

**How to avoid:** Before activating a new flow version, check Setup > Paused Flow Interviews to confirm there are no active paused interviews on the current version. Schedule activations outside peak hours or during maintenance windows when multi-session screen flows are in use. Document that paused interviews must be completed or abandoned before the deployment window.

---

## Gotcha 5: Flow Test Suite Tests Do Not Execute in Deployed Orgs Automatically

**What happens:** A developer builds a thorough Flow Test Suite in a sandbox and all tests pass. After deployment to production, the same flow starts producing wrong results. The developer assumes the tests verified production behavior, but the tests were never re-run after deployment.

**When it occurs:** Flow Test Suite tests run in the org where they are created. They can be exported and re-imported, but they are not automatically executed as part of a standard metadata deployment (unlike Apex tests). Deploying the flow metadata does not trigger the test suite to run in the destination org.

**How to avoid:** Treat Flow Test Suite tests as a local verification tool, not a deployment gate. After deploying a flow to a new org, manually run the Test Suite in that org to confirm behavior. If automated deployment validation is required, combine Flow Tests with Change Set validation runs or CI/CD pipeline steps that explicitly trigger the test execution.
