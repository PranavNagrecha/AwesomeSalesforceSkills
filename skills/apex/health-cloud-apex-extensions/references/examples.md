# Examples — Health Cloud Apex Extensions

## Example 1: Implementing CarePlanProcessorCallback for Care Plan Lifecycle Automation

**Context:** A health system needs to automatically create a follow-up Task for the assigned Care Coordinator whenever a care plan transitions to Active status. The Task should reference the care plan, be due within 48 hours, and be assigned to the care coordinator on the patient's Care Team.

**Problem:** Adding an Apex trigger on the `CarePlan` object does not reliably intercept managed-package lifecycle transitions. Trigger events fire on raw DML, but Health Cloud's internal activation logic may not always surface as a simple update DML that a standard trigger would catch. Using `after update` on `CarePlan` also fires outside the Health Cloud transaction framework, which can cause governor limit conflicts with managed-package automation.

**Solution:**

```apex
global class CarePlanActivationCallback
    implements HealthCloudGA.CarePlanProcessorCallback {

    // Called by the HealthCloudGA managed package when a care plan is activated.
    // Method signature must exactly match the installed package version.
    global void onCarePlanActivated(Id carePlanId) {
        // Gate debug logging — never dump clinical object fields
        if (DebugSettings__mdt.getInstance('ApexDebug')?.IsEnabled__c == true) {
            System.debug('CarePlan activated: ' + carePlanId);
        }

        // Delegate to async context to avoid governor limit conflicts
        // with the managed-package transaction already in progress
        CarePlanActivationHandler.createFollowUpTaskAsync(carePlanId);
    }

    global void onCarePlanCreated(Id carePlanId) { }
    global void onCarePlanClosed(Id carePlanId) { }
}
```

```apex
public class CarePlanActivationHandler {
    @future
    public static void createFollowUpTaskAsync(Id carePlanId) {
        // Query only non-PHI fields needed for task creation
        CarePlan cp = [
            SELECT Id, OwnerId, Subject
            FROM CarePlan
            WHERE Id = :carePlanId
            LIMIT 1
        ];

        Task t = new Task(
            Subject = 'Care Plan Activation Follow-Up',
            WhatId = carePlanId,
            OwnerId = cp.OwnerId,
            ActivityDate = Date.today().addDays(2),
            Status = 'Not Started',
            Priority = 'Normal'
        );
        insert t;
    }
}
```

After deploying, register the callback class name (`CarePlanActivationCallback`) in Health Cloud Setup > Care Plan Settings > Custom Apex Callback. Without this registration step, the callback never fires.

**Why it works:** `HealthCloudGA.CarePlanProcessorCallback` is the contract the managed package calls within its own lifecycle. It fires reliably regardless of how the activation was triggered (UI, Flow, API). The `@future` delegation prevents the callback logic from competing for governor limits inside the managed-package transaction.

---

## Example 2: Referral Processing Using Invocable Actions vs. Raw DML

**Context:** A clinical intake Flow needs to submit a specialist referral when a care coordinator marks an assessment as requiring external consultation. The referral must go through the Industries Common Components routing engine to match available providers and apply consent checks.

**Problem:** A developer writes `insert new ReferralRequest__c(Patient__c = patientId, Specialty__c = 'Cardiology', Status__c = 'Submitted')` directly. The record is created in the database, but the ICC routing engine never evaluates it. The referral does not appear in the provider matching queue, consent is not evaluated against `AuthorizationFormConsent`, and no notification is sent to the referred-to provider. The record looks valid but is functionally dead.

**Solution:**

```apex
// Correct: invoke the ICC referral action via Invocable.Action
public class ReferralSubmissionService {

    public static void submitReferral(Id patientId, String specialty, Id referringProviderId) {
        // Build the input using the ICC framework's wrapper type
        Map<String, Object> inputMap = new Map<String, Object>{
            'patientId'           => patientId,
            'specialty'           => specialty,
            'referringProviderId' => referringProviderId
        };

        // Invoke the ICC-provided action — do NOT use insert ReferralRequest__c directly
        Invocable.Action action = Invocable.Action.createCustomAction(
            'apex',
            'industries_referral_mgmt.CreateReferral'
        );
        action.setInvocationParameter('referralInput', inputMap);

        List<Invocable.Action.Result> results = action.invoke();
        Invocable.Action.Result result = results[0];

        if (!result.isSuccess()) {
            // Surface errors — never silently swallow ICC framework errors
            throw new ReferralException(
                'Referral submission failed: ' + result.getErrors()
            );
        }
    }

    public class ReferralException extends Exception {}
}
```

**Why it works:** Calling the ICC invocable action routes the referral through the full Industries Common Components processing pipeline: provider matching, consent evaluation against `AuthorizationFormConsent`, status stamping, and outbound notifications. The action returns a structured result that can be evaluated for errors. Direct DML bypasses the entire pipeline and produces a record that is an orphan from the framework's perspective.

---

## Anti-Pattern: Using Direct DML on CarePlanTemplate for Care Plan Creation

**What practitioners do:** Write `insert new CarePlan(Subject = 'Diabetes Management', Status = 'Active', PatientId = patientId)` from Apex, sometimes seeded from a `CarePlanTemplate__c` record queried manually.

**What goes wrong:** The care plan is created without triggering the Health Cloud automation layer. Goals and problems from the template are not automatically associated. `AuthorizationFormConsent` is not evaluated. The `CarePlanProcessorCallback` `onCarePlanCreated` hook is not fired because the insert happened outside the managed-package service layer. The resulting care plan is visible in the database but behaves inconsistently in the Health Cloud UI — missing goals, wrong status transitions, and consent state unknown.

**Correct approach:** Use the `CreateCarePlan` invocable action via `Invocable.Action` from Apex, or trigger care plan creation through a Flow that calls the action. The action handles template instantiation, consent evaluation, and lifecycle event firing in a single transaction.
