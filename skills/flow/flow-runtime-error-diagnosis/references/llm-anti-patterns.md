# LLM Anti-Patterns — Flow Runtime Error Diagnosis

## Anti-Pattern 1: Suggesting Debug Mode to Reproduce DML Errors

**What the LLM generates:** Instructions to use Flow Builder's Debug mode to reproduce a `CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY` or `FIELD_INTEGRITY_EXCEPTION` error.

**Why it happens:** LLMs recommend Debug mode as a general-purpose diagnostic tool without knowing that debug mode does not commit DML.

**Correct pattern:** Debug mode is for logic tracing and variable inspection only. DML-related errors (validation rule failures, trigger failures, required field violations) require testing against real data in a sandbox using an actual record scenario, not the Debug runner. Reproduce DML errors by running the flow from the record UI or via test data setup in sandbox.

**Detection hint:** Any instruction to "run Debug mode to reproduce the DML error" or "debug the validation rule failure in Flow Builder."

---

## Anti-Pattern 2: Adding a Retry Loop in a Fault Path

**What the LLM generates:** A fault path that loops back to retry the failed DML element a second time.

**Why it happens:** Retry patterns are common in integration and async code. LLMs apply them without knowing that a fault path cannot re-execute the failed element and that loops in fault paths create infinite execution risk.

**Correct pattern:** Fault paths are for graceful failure handling only — display a user-friendly message, log the error, or send a notification. The failed DML is already rolled back when the fault path fires. To handle retryable scenarios, fix the data condition before the DML element (null checks, validation pre-checks) rather than retrying after failure.

**Detection hint:** Any fault path connector that leads back to a Loop element or back to the DML element that failed.

---

## Anti-Pattern 3: Recommending Flow Deactivation to Fix a Runtime Error

**What the LLM generates:** Advice to deactivate the flow as the first response to a runtime error report.

**Why it happens:** Deactivation is a quick way to stop error emails, and LLMs suggest it without understanding the operational impact of stopping an active business process.

**Correct pattern:** Deactivating a flow stops the business process entirely — which may be worse than the error. The correct first response is to read the fault email, identify the failing element and error type, and apply a targeted fix. If the flow must be stopped urgently, deactivate only after confirming the business impact and communicate to stakeholders. In most cases, the fix can be deployed as a new version without deactivating the current version until the fix is ready.

**Detection hint:** Any first-step recommendation to deactivate the flow before diagnosing the error.

---

## Anti-Pattern 4: Confusing Flow Version in Fault Email With Active Version

**What the LLM generates:** Instructions to open the flow in Flow Builder and check the "active" version, without verifying whether the active version is the same version referenced in the fault email.

**Why it happens:** LLMs assume there is a single active version and that it is the version that ran.

**Correct pattern:** The fault email specifies the flow version number that ran. If the flow has been updated since the error occurred, the active version may be different. In Flow Builder, use the version dropdown to open the specific version number from the fault email. This is the version that contains the failing element — not necessarily the current active version.

**Detection hint:** Any diagnostic instruction that says "open the flow" without specifying to check the version number from the fault email.

---

## Anti-Pattern 5: Adding Fault Paths as a Substitute for Null Checks

**What the LLM generates:** Adding a fault path to the Get Records element to "handle" the case where Get Records returns no records.

**Why it happens:** Fault paths seem like error handling, and LLMs apply them broadly without knowing that a Get Records element returning no results is not an error — it completes successfully with a null variable. Fault paths on Get Records only fire for infrastructure or SOQL errors, not for empty result sets.

**Correct pattern:** A Get Records element that returns no records does not trigger its fault path — it returns null and continues on the normal path. To handle the empty-result case, add a Decision element after Get Records that checks whether the variable `is null`. Route the null outcome to a graceful path. Fault paths on Get Records are for INVALID_FIELD errors, SOQL limit errors, and similar platform-level failures.

**Detection hint:** Any solution that adds a fault path to a Get Records element to handle "no record found" scenarios instead of a Decision null check.
