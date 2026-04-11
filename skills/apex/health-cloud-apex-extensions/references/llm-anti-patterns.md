# LLM Anti-Patterns — Health Cloud Apex Extensions

Common mistakes AI coding assistants make when generating or advising on Health Cloud Apex Extensions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Direct DML on CarePlan or CarePlanTemplate__c

**What the LLM generates:**
```apex
CarePlan cp = new CarePlan(
    Subject = 'Diabetes Management',
    Status = 'Active',
    AccountId = patientAccountId
);
insert cp;
```

**Why it happens:** LLMs trained on generic Salesforce Apex patterns treat all SObjects as interchangeable. They apply the standard `insert new SObject(...)` pattern without knowing that Health Cloud clinical objects have a managed-package service layer that must be invoked instead.

**Correct pattern:**
```apex
// Use the Health Cloud CreateCarePlan invocable action
Invocable.Action action = Invocable.Action.createCustomAction(
    'apex', 'HealthCloudGA.CreateCarePlan'
);
action.setInvocationParameter('patientId', patientAccountId);
action.setInvocationParameter('templateId', templateId);
List<Invocable.Action.Result> results = action.invoke();
if (!results[0].isSuccess()) {
    throw new CarePlanException('CreateCarePlan failed: ' + results[0].getErrors());
}
```

**Detection hint:** Look for `insert new CarePlan(`, `insert new CarePlanGoal(`, `insert new CarePlanProblem(`, or `update carePlan` without a preceding `Invocable.Action` call in the same code path.

---

## Anti-Pattern 2: Ignoring the HealthCloudGA Namespace for Interface Implementation

**What the LLM generates:**
```apex
// Wrong: implementing a non-existent interface
public class MyCallback implements CarePlanProcessorCallback {
    public void onCarePlanActivated(Id carePlanId) { ... }
}
```

**Why it happens:** LLMs drop the managed-package namespace prefix when they are uncertain about it or have seen patterns where namespace prefixes were omitted in internal (same-package) code. `CarePlanProcessorCallback` without the `HealthCloudGA.` prefix does not exist in customer namespaces and will not compile.

**Correct pattern:**
```apex
// Correct: always qualify with the HealthCloudGA namespace
global class MyCallback implements HealthCloudGA.CarePlanProcessorCallback {
    global void onCarePlanActivated(Id carePlanId) { ... }
    global void onCarePlanCreated(Id carePlanId) { ... }
    global void onCarePlanClosed(Id carePlanId) { ... }
}
```

**Detection hint:** Search for `implements CarePlanProcessorCallback` without the `HealthCloudGA.` prefix. Also flag any `public class` implementing Health Cloud interfaces — they must be `global`.

---

## Anti-Pattern 3: Missing HIPAA Logging Governance for Clinical Apex Classes

**What the LLM generates:**
```apex
List<EhrPatientMedication__c> meds = [
    SELECT Id, MedicationName__c, Dosage__c FROM EhrPatientMedication__c
    WHERE Patient__c = :patientId
];
System.debug('Patient meds: ' + meds);
```

**Why it happens:** LLMs apply standard debug logging patterns uniformly without knowledge of HIPAA constraints on debug log stores. Debugging clinical data queries with `System.debug()` is functionally identical to any other Apex debugging from the LLM's perspective.

**Correct pattern:**
```apex
List<EhrPatientMedication__c> meds = [
    SELECT Id, MedicationName__c, Dosage__c FROM EhrPatientMedication__c
    WHERE Patient__c = :patientId
];
// Gate debug output — never dump clinical field values in production
if (DebugSettings__mdt.getInstance('ApexDebug')?.IsEnabled__c == true) {
    System.debug('Retrieved ' + meds.size() + ' medication records for patient Id: ' + patientId);
    // Log count and Id only — never log clinical field values
}
```

**Detection hint:** Search for `System.debug(` followed by any reference to variables typed as or queried from `EhrPatientMedication`, `PatientHealthCondition`, `ClinicalEncounterCode`, `AuthorizationFormConsent`, or similar clinical objects. Any unconditional `System.debug()` in a method that queries clinical objects is suspect.

---

## Anti-Pattern 4: Treating Care Plan Invocable Actions as Optional Convenience

**What the LLM generates:** Code comments or explanations saying "you can also directly insert the CarePlan record if you don't need the full care plan template automation" — framing invocable actions as optional sugar rather than a compliance requirement.

**Why it happens:** LLMs often frame architectural choices as tradeoffs between simplicity and features. For generic Salesforce objects, that framing is accurate. For Health Cloud clinical objects, bypassing the service layer is a compliance failure, not a valid simplification.

**Correct pattern:** There is no optional path for care plan creation in a Health Cloud org. Always use `CreateCarePlan` invocable action. Document this as a requirement in code comments:
```apex
// REQUIRED: Use CreateCarePlan invocable action.
// Direct DML on CarePlan bypasses AuthorizationFormConsent evaluation
// and care plan lifecycle callbacks. This is a HIPAA compliance requirement,
// not a style preference.
```

**Detection hint:** Flag any explanation or code comment that describes direct DML on `CarePlan` or `CarePlanTemplate__c` as a valid alternative to the invocable action.

---

## Anti-Pattern 5: Using Raw DML on ReferralRequest__c for ICC Referrals

**What the LLM generates:**
```apex
ReferralRequest__c ref = new ReferralRequest__c(
    Patient__c = patientId,
    Specialty__c = 'Cardiology',
    Status__c = 'Submitted'
);
insert ref;
```

**Why it happens:** The `ReferralRequest__c` object is a standard Salesforce custom object to the LLM. Without knowledge of the Industries Common Components framework, the LLM treats it like any other custom object and generates standard DML.

**Correct pattern:**
```apex
// Use the ICC CreateReferral invocable action
Invocable.Action action = Invocable.Action.createCustomAction(
    'apex', 'industries_referral_mgmt.CreateReferral'
);
action.setInvocationParameter('patientId', patientId);
action.setInvocationParameter('specialty', 'Cardiology');
List<Invocable.Action.Result> results = action.invoke();
if (!results[0].isSuccess()) {
    throw new ReferralException('Referral failed: ' + results[0].getErrors());
}
```

**Detection hint:** Search for `insert new ReferralRequest__c(` or `insert referralRequest` in any Apex class handling clinical intake or referral workflows.

---

## Anti-Pattern 6: Omitting the Callback Registration Step from Deployment Instructions

**What the LLM generates:** Deployment steps that cover only `sfdx force:source:deploy` or change set deployment, without mentioning the required manual Setup step to register the callback class name in Health Cloud Care Plan Settings.

**Why it happens:** LLMs generate deployment instructions based on standard Salesforce metadata deployment patterns. The Health Cloud Setup registration is a runtime configuration step that exists outside the metadata layer and is not captured in any deployable artifact.

**Correct pattern:** Every deployment runbook for a `HealthCloudGA.CarePlanProcessorCallback` implementation must include:
```
Post-deploy manual step:
1. Navigate to Setup > Health Cloud Setup > Care Plan Settings
2. In the Custom Apex Callback field, enter the fully qualified class name:
   [namespace__]YourCallbackClassName
3. Click Save
4. Validate: activate a test care plan in a sandbox and confirm the callback fires
```

**Detection hint:** If deployment instructions for a callback class do not mention Health Cloud Setup > Care Plan Settings, the instructions are incomplete.
