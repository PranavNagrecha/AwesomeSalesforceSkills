# Examples — Flow Debugging

## Example 1: Record-Triggered Flow Not Firing on Update

**Context:** A record-triggered flow on the Opportunity object is supposed to send an internal Chatter notification when an Opportunity stage changes to "Closed Won." After deployment, the notification never appears, even when the stage is updated manually.

**Problem:** The flow appears inactive from the user's perspective — no errors, no fault emails, nothing happens. Checking entry conditions is skipped because the flow is confirmed active and the trigger event is "A record is created or updated."

**Solution:**

The bug is in the entry conditions. The flow was configured with **"Only when a record is updated to meet the conditions"** and the condition checks `StageName Equals Closed Won`.

With that setting, the flow fires only when the record transitions from a non-"Closed Won" value to "Closed Won" during the same DML operation. Any Opportunity already in "Closed Won" that gets updated for another field (e.g., CloseDate) will never fire this path — the stage field did not change to match, it was already matching.

Steps to diagnose:
1. Open the flow in Flow Builder.
2. Click the Start element.
3. Read the **Entry Conditions** section.
4. Check the condition evaluation option — "Only when a record is updated to meet the conditions" vs "Every time a record is saved and meets the conditions."
5. Use **Debug mode** in a sandbox: set `StageName` = "Prospecting" on the test record, save, then update `StageName` to "Closed Won" — the flow fires. Then update `StageName` to "Closed Won" again on an already-"Closed Won" record — the flow does not fire.

Fix: Change entry condition evaluation to **"Every time a record is saved and meets the conditions"** if the flow should fire on any save where the stage is "Closed Won," or add a condition that checks `ISCHANGED(StageName)` in a formula resource if the intention is strictly on-change-only.

**Why it works:** The "Only when updated to meet" behavior is a common source of confusion because the flow is not broken — it is working exactly as configured. The debug trace makes this immediately visible: the entry condition check shows "Not Met" when the record was already in the target state.

---

## Example 2: Fault Email Received for After-Save Flow on Case

**Context:** The admin receives a fault email with the subject "Unhandled Fault in Flow: Case_Escalation_Flow." The email identifies the failing element as "Update_Related_Account" and the error message as `FIELD_INTEGRITY_EXCEPTION: Required fields are missing: [Billing Street]`.

**Problem:** The practitioner assumes the flow logic is wrong and begins restructuring the decision branches. Time is lost investigating the wrong layer.

**Solution:**

The fault email contains everything needed to identify the cause directly:

1. **Element name**: `Update_Related_Account` — this is a Flow Update Records element that writes to the Account associated with the Case.
2. **Error category**: `FIELD_INTEGRITY_EXCEPTION` — this is a required-field validation on the Account object, not a flow logic error.
3. **Error detail**: `Required fields are missing: [Billing Street]` — a required field on the Account is not being populated.

Investigation path:
1. Open the flow to the `Update_Related_Account` element.
2. Check which Account fields are being written. The element is updating the Account but not providing a value for `Billing Street`, which has been made required by a recent validation rule.
3. Confirm by checking the Account object's validation rules — a new validation rule was added last week requiring `Billing Street` for all Account updates.

Fix options:
- Add `Billing Street` to the Update element's field assignments using the existing Account record value (Get the Account first, then pass `{!Account.BillingStreet}` back into the update).
- Or add a fault connector from the Update element to an error-logging path so that partial failures do not roll back the entire Case save.

**Why it works:** The fault email element name directly pins the failing operation. Mapping the SFDC error code (`FIELD_INTEGRITY_EXCEPTION`) to its cause (validation rule or required field enforcement) narrows the diagnosis to minutes instead of hours.

---

## Anti-Pattern: Running Debug Without Setting Matching Field Values

**What practitioners do:** Open Flow Builder, click Debug, accept all default variable values, and step through the debug session. The flow completes with no visible issue. The practitioner concludes the flow is working correctly and closes the session.

**What goes wrong:** The default variable values in a debug session are empty or zero. If the flow has entry conditions that require a specific field value (e.g., `Priority = High`), the debug run enters the flow with `Priority = null`, which evaluates to a different decision branch than the real failing scenario. The bug is never surfaced because the debug run did not replicate the actual triggering conditions.

**Correct approach:** Before clicking Run in the Debug modal, explicitly set all relevant input variables and record field values to match the failing scenario. For a record-triggered flow: set the field values that represent the record state at the time of the failure. For an autolaunched flow: set the input variable values that the calling process would pass. Always confirm the debug session is running the same data path as the production failure before interpreting results.
