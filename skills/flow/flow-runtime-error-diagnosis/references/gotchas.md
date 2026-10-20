# Gotchas — Flow Runtime Error Diagnosis

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Fault Emails Go to the Flow's Last Modifier, Not the Admin

By default (`enableFlowUseApexExceptionEmail` false), Flow fault emails are sent to "The user who last modified the process or flow" (api_meta 264 L120062-120065), not to a dedicated admin inbox. The earlier text said "(saved/activated)"; the guide says last modified. If that user's email is unmoniored or they leave the organization, fault emails are silently lost.

**Fix:** In Setup > Process Automation Settings, set **Send Process or Flow Error Email to** (`enableFlowUseApexExceptionEmail`, api_meta 264 L120062-120067) so the emails go to the addresses on the Apex Exception Email page, and put an org-wide admin alias or distribution list there. The earlier text named the setting "Send Flow Error Emails To", which is not the documented label.

---

## Gotcha 2: Deleting a Field Does Not Deactivate or Warn the Flow

UNVERIFIED (2026-10-20): the whole behavior in this gotcha (no deactivation, no warning, runtime failure) and the `FlowVersionView` query are not in the corpus; `FlowVersionView` is a documented object (object_reference 264 L145676) but its `Metadata` column filtering is not shown. When you delete a custom field, Salesforce does not deactivate flows that reference it, and Flow Builder does not surface a warning at delete time. The flow continues to run and only fails at runtime when the deleted field is referenced. The flow version that references the deleted field can still be saved or activated without error — the INVALID_FIELD error only appears at runtime.

**Fix:** Before deleting any custom field, query for flow references using `FlowVersionView` in Salesforce Inspector or Dev Console:
```
SELECT DeveloperName, Status FROM FlowVersionView WHERE Metadata LIKE '%YourField__c%'
```
Update and re-activate any flows that reference the field before deleting it.

---

## Gotcha 3: Debug Mode Does Not Commit DML

UNVERIFIED (2026-10-20): Debug mode behavior is not in the corpus. Flow Builder's Debug mode executes flow logic but does not commit any DML operations to the database. This means validation rule failures, duplicate rule failures, and trigger-side-effect errors will not surface in a Debug run — they only appear in production or a real sandbox execution. Debugging a CANNOT_INSERT_UPDATE error requires testing against real data (in sandbox), not the Debug runner.

**Fix:** Use Debug mode for logic tracing and variable inspection. For DML-related errors, reproduce the scenario in a sandbox with the actual record data that triggered the failure.

---

## Gotcha 4: Multiple Flow Versions Can Exist; the Fault Email Version May Not Be the Active Version

UNVERIFIED (2026-10-20): that an older version keeps running is not in the corpus (`FlowDefinition` carries one `activeVersionNumber`, api_meta 264 L76681). Salesforce allows you to activate a new version of a flow while older versions remain in a deactivated state. If a scheduled flow or process builder invocation retains a reference to an older version, that older version may still run and generate fault emails — while you are looking at and debugging the newer active version.

**Fix:** Check the "Flow version" line in the fault email carefully. In Flow Builder, use the version dropdown to open the specific version referenced in the email. Verify which version is invoked by checking the schedule or the calling process's reference.

---

## Gotcha 5: Fault Path Handlers Do Not Prevent the Original DML From Rolling Back

UNVERIFIED (2026-10-20): the rollback statement is not in the corpus. Adding a Fault Path to a DML element (Create Records, Update Records) does not save the record — when the fault path fires, the DML that failed is rolled back. The fault path only controls what happens *after* the failure (show a message, log an error). You cannot use the fault path to "retry" the DML or to partially commit the record.

**Fix:** Use the fault path to present a friendly error message and log the failure details. If the record data needs to be saved despite the error, fix the underlying cause (validation rule, missing required field) rather than trying to work around it in the fault path.
