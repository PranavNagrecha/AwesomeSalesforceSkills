# Gotchas — Health Cloud Apex Extensions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Apex Debug Logs Containing Clinical Fields Are PHI Under HIPAA

**What happens:** Any `System.debug()` call that directly or indirectly outputs the value of clinical object fields — `EhrPatientMedication.MedicationName__c`, `PatientHealthCondition.ConditionCode__c`, `ClinicalEncounterCode.Code__c`, `AuthorizationFormConsent` audit fields, etc. — writes protected health information (PHI) as plaintext to the Salesforce debug log store. Debug logs are accessible to any System Administrator in Setup > Debug Logs and are not subject to field-level security or org-wide sharing rules. In a HIPAA-covered org, this constitutes a data exposure event.

**When it occurs:** Any time a developer enables debug logging on a user or class that executes clinical data queries, or any time automated monitoring scripts enable trace flags in production. It also occurs in scratch orgs and sandboxes that contain cloned production clinical data.

**How to avoid:** Gate all `System.debug()` calls in clinical Apex classes behind a Custom Metadata Type flag (e.g., `DebugSettings__mdt`) that is set to `false` in production and only enabled temporarily by a named administrator. Establish a debug log purge policy: logs must be deleted within a defined window (e.g., 1 hour) after troubleshooting is complete. Never include clinical field values in log output — log record IDs only.

---

## Gotcha 2: Direct DML on CarePlan Objects Bypasses Consent Enforcement

**What happens:** Inserting or updating `CarePlan`, `CarePlanGoal`, `CarePlanProblem`, or `CarePlanTemplate__c` records via direct Apex DML creates the records without evaluating the patient's `AuthorizationFormConsent` record. Health Cloud's consent enforcement is implemented in the managed-package service layer, not as a trigger on these objects. Direct DML completely skips it.

**When it occurs:** Any Apex class, trigger, or Queueable that performs `insert new CarePlan(...)` or `update carePlanGoal` without going through the Health Cloud invocable actions (`CreateCarePlan`, `AddCarePlanGoal`) or the `HealthCloudGA` Apex service layer. This pattern is common when developers copy care plan creation logic from generic Apex tutorials without considering the Health Cloud context.

**How to avoid:** Route all care plan create and modify operations through the Health Cloud invocable actions. In Apex, call these via `Invocable.Action.createCustomAction(...)`. In Flow, use the standard Health Cloud action elements. Add the `check_health_cloud_apex_extensions.py` checker to CI to detect direct DML on care plan objects.

---

## Gotcha 3: HealthCloudGA Interface Implementation Requires Setup Registration

**What happens:** A developer deploys a `global` Apex class that correctly implements `HealthCloudGA.CarePlanProcessorCallback`. The class compiles without errors. But in production, no callback events fire — the `onCarePlanActivated`, `onCarePlanCreated`, and `onCarePlanClosed` methods are never called. There is no runtime exception or warning.

**When it occurs:** Any time the callback class is deployed without being registered in Health Cloud Setup > Care Plan Settings > Custom Apex Callback. The managed package does not auto-discover callback implementations by convention — it only calls the class whose name is explicitly registered in the Setup configuration field.

**How to avoid:** Include a deployment runbook step: after deploying the callback class, navigate to Health Cloud Setup > Care Plan Settings and enter the fully qualified class name in the Custom Apex Callback field. Validate registration by activating a test care plan in a sandbox and confirming the callback fires. Add this step to your CI/CD post-deploy verification checklist.

---

## Gotcha 4: Interface Method Signatures Must Match the Installed Package Version

**What happens:** `HealthCloudGA.CarePlanProcessorCallback` method signatures — parameter types, return types, and method names — can change between Health Cloud managed package versions. An Apex class written against an older package version fails to compile when the package is upgraded, breaking the deployment pipeline.

**When it occurs:** During Health Cloud package upgrades, particularly when upgrading across multiple major versions. Also occurs when a developer copies a callback example from documentation that was written for a different package version than what is installed.

**How to avoid:** Always verify the installed `HealthCloudGA` package version in Setup > Installed Packages before writing or updating a callback implementation. The authoritative interface signature is in the installed package, not in external documentation. Use `System.debug(HealthCloudGA.CarePlanProcessorCallback.class)` in an Anonymous Apex execute to confirm the available methods before implementation.

---

## Gotcha 5: @future Apex Cannot Accept sObject Parameters — Serialize Manually for Callbacks

**What happens:** When a `CarePlanProcessorCallback` implementation tries to delegate work to a `@future` method by passing a `CarePlan` sObject, the compiler rejects the call because `@future` methods only accept primitive types, collections of primitives, and `Id` types. Developers trying to pass context from a callback into an async method are blocked.

**When it occurs:** When a callback implementation needs to pass care plan field values (not just the Id) to an async handler, and a developer attempts to pass the sObject directly.

**How to avoid:** Pass only the `carePlanId` (`Id` type) to the `@future` method. Re-query any additional context fields inside the async method. For more complex data passing, use a Queueable Apex class (which accepts any serializable type in its constructor) and enqueue it from the callback.
