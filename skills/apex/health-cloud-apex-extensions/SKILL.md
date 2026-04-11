---
name: health-cloud-apex-extensions
description: "Use this skill when extending Health Cloud via Apex: implementing HealthCloudGA managed-package interfaces, automating care plan lifecycle hooks, processing referrals using Industries Common Components invocable actions, or enforcing HIPAA-compliant logging governance for clinical Apex code. Trigger keywords: CarePlanProcessorCallback, HealthCloudGA namespace, ReferralRequest, ReferralResponse, care plan invocable actions, clinical Apex extension, Health Cloud Apex API. NOT for standard Apex triggers or generic Apex development unrelated to Health Cloud managed-package extension points."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
triggers:
  - "need to implement HealthCloudGA interface or care plan lifecycle hook in Apex"
  - "referral processing Apex using ReferralRequest or ReferralResponse objects"
  - "clinical Apex code logging PHI fields and need HIPAA log governance"
  - "care plan automation bypassing invocable actions with direct DML on CarePlanTemplate"
tags:
  - health-cloud
  - apex
  - care-plan
  - clinical-data
  - industries
inputs:
  - "Health Cloud managed package version (HealthCloudGA namespace installed)"
  - "Use case: care plan lifecycle hook, referral processing, or clinical data Apex automation"
  - "Whether the org uses Integrated Care Management (ICM) or legacy care plan model"
  - "Apex classes or flows currently managing care plan or referral logic"
outputs:
  - Compliant Apex extension class implementing HealthCloudGA interfaces
  - Referral processing Apex using invocable actions (not raw DML)
  - HIPAA Apex logging governance checklist and debug-log purge policy recommendation
  - Care plan automation strategy using Health Cloud built-in invocable actions
dependencies:
  - admin/care-plan-configuration
  - apex/apex-security-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Health Cloud Apex Extensions

This skill activates when a practitioner needs to extend Salesforce Health Cloud behavior through Apex, specifically using the `HealthCloudGA` managed-package namespace, Health Cloud invocable actions for care plan automation, Industries Common Components for referral processing, or when governance of PHI-containing Apex debug logs is required.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the `HealthCloudGA` managed package is installed and the version number. Interface signatures and available invocable actions vary across package releases.
- Determine whether the org uses the Integrated Care Management (ICM) data model or the legacy `CarePlanTemplate__c` model. Extension points differ between the two.
- Identify whether Apex debug logs are enabled in production. Logs containing `EhrPatientMedication`, `PatientHealthCondition`, or similar clinical objects constitute PHI and require governance.
- Confirm the org has `AuthorizationFormConsent` properly configured — bypassing consent enforcement through direct DML is a compliance and data integrity risk.

---

## Core Concepts

### HealthCloudGA Namespace and Managed-Package Interfaces

Health Cloud ships as a managed package under the `HealthCloudGA` namespace. Extension points are provided as Apex interfaces and abstract classes within this namespace. The most critical is `HealthCloudGA.CarePlanProcessorCallback`, which exposes lifecycle hooks for care plan creation, activation, and closure. Implementing this interface requires your class to be declared globally, and the implementation must be registered in Health Cloud Setup — simply deploying the class is insufficient. Interface method signatures are enforced by the managed package; mismatched signatures fail at deploy time.

### Care Plan Invocable Actions vs. Raw DML

Health Cloud provides built-in invocable actions — `CreateCarePlan`, `AddCarePlanGoal`, `AddCarePlanProblem` — that encapsulate the full automation logic for care plan records. These actions enforce consent checks via `AuthorizationFormConsent`, trigger care plan lifecycle events, and maintain data integrity within the Health Cloud data model. Using raw `insert` or `update` DML on `CarePlanTemplate__c`, `CarePlan`, or related objects bypasses all of this automation. The result is care plan records in an inconsistent state: goals created without the proper problem linkages, consent not evaluated, and lifecycle callbacks not fired. Always invoke care plan changes through the provided invocable actions or the `HealthCloudGA` Apex service layer.

### Industries Common Components — Referral Processing

The Industries Common Components (ICC) framework powers referral processing in Health Cloud. Referrals are represented as `ReferralRequest` and `ReferralResponse` records. The framework exposes Apex invocable actions for referral submission, status updates, and routing logic. Apex classes that need to trigger referral workflows must call these invocable actions rather than performing DML on `ReferralRequest` directly, for the same reasons as care plan invocable actions: the framework enforces business rules, consent, and notification logic at the action layer.

### HIPAA Apex Logging Governance

Salesforce Apex debug logs are not subject to field-level security or sharing rules — a log entry that captures a SOQL query result or a variable inspect for `EhrPatientMedication`, `PatientHealthCondition`, `ClinicalEncounterCode`, or similar clinical objects writes PHI as plain text to the debug log store. Under HIPAA, this constitutes a data exposure risk. Production debug logging must be disabled or tightly scoped (specific user, short duration), logs must be purged after use, and no automated process should retain clinical-field variable dumps in long-lived log stores. This applies equally to `System.debug()` calls in trigger handlers and to Flow-launched Apex actions.

---

## Common Patterns

### Implementing CarePlanProcessorCallback

**When to use:** You need to execute custom logic when a care plan transitions state — e.g., notifying a care coordinator when a care plan is activated, or creating a Task when a care plan closes.

**How it works:**
1. Declare a `global` Apex class implementing `HealthCloudGA.CarePlanProcessorCallback`.
2. Implement the required interface methods: `onCarePlanCreate`, `onCarePlanActivate`, `onCarePlanClose` (exact method signatures depend on the installed package version — always reference the installed namespace documentation).
3. Register the class name in Health Cloud Setup > Care Plan Settings > Custom Apex Callback.
4. Keep callback logic lightweight: avoid synchronous callouts, limit SOQL to selective queries, and delegate heavy work to `@future` or Queueable Apex to stay within governor limits.

**Why not the alternative:** Adding an Apex trigger on the `CarePlan` object fires outside the Health Cloud lifecycle framework. It cannot reliably intercept all state transitions and misses events triggered by managed-package automation.

### Referral Invocable Action Pattern

**When to use:** An Apex class or Flow needs to create or update a referral programmatically — e.g., when a clinical intake process determines that an external specialist referral is required.

**How it works:**
1. Use `Invocable.Action` to invoke the `industries_referral_mgmt__CreateReferral` or equivalent ICC invocable action from Apex rather than performing `insert new ReferralRequest__c(...)`.
2. Populate the input `ReferralRequest` wrapper object with patient context, referring provider, and target specialty.
3. Evaluate the `ReferralResponse` output for status and any error messages before proceeding.
4. If the referral fails validation, surface the error to the user via a platform event or record status field — do not silently swallow the response.

**Why not the alternative:** Direct DML on `ReferralRequest__c` skips the ICC business rules engine, consent checks, and provider matching logic. The resulting record may be technically valid in the database but functionally broken in the referral management UI and reporting.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Execute logic when a care plan is activated | Implement `HealthCloudGA.CarePlanProcessorCallback` and register it in Health Cloud Setup | Fires reliably within the managed-package lifecycle; Apex trigger on CarePlan does not catch all transitions |
| Create a care plan from Apex | Call the `CreateCarePlan` invocable action via `Invocable.Action` | Enforces consent evaluation and lifecycle hooks; raw DML bypasses both |
| Process an inbound referral | Use ICC `industries_referral_mgmt__CreateReferral` invocable action | Applies provider matching, consent, and routing rules from the ICC framework |
| Add a goal to an existing care plan | Call `AddCarePlanGoal` invocable action | Maintains data model integrity; direct DML on CarePlanGoal may produce orphaned records |
| Log debug info in a class touching clinical objects | Use conditional debug logging gated by a Custom Setting or Custom Metadata flag | Prevents PHI from entering debug logs in production; gate on environment type |
| Validate care plan Apex in a scratch org | Use a Health Cloud scratch org definition with Health Cloud features enabled | Ensures HealthCloudGA namespace and test data factories are available |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Confirm the installed `HealthCloudGA` package version and identify the specific extension point needed (callback interface, invocable action, or ICC action). Pull the interface signature from the namespace documentation or by inspecting the installed package in Setup > Installed Packages.
2. Determine whether the request involves care plan lifecycle, referral processing, or general clinical data automation. Route to the appropriate pattern: `CarePlanProcessorCallback` for lifecycle hooks, `CreateCarePlan`/`AddCarePlanGoal` invocable actions for care plan data, or ICC actions for referrals.
3. Implement the Apex class: declare it `global` if it implements a HealthCloudGA interface, use `Invocable.Action` for action-based calls, and ensure all DML on Health Cloud clinical objects is routed through the appropriate service layer rather than direct DML.
4. Audit all `System.debug()` calls and SOQL result references in the class — remove or gate any statements that would dump clinical object fields (`EhrPatientMedication`, `PatientHealthCondition`, `ClinicalEncounterCode`, `AuthorizationFormConsent`) into debug logs. Add a Custom Metadata-based debug gate.
5. Register the callback class in Health Cloud Setup if using `CarePlanProcessorCallback`, write unit tests using `@IsTest` with Health Cloud test data factories, and verify that no direct DML on `CarePlan`, `CarePlanTemplate__c`, or `ReferralRequest__c` remains in the code path.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Apex class implementing a HealthCloudGA interface is declared `global` and registered in Health Cloud Setup
- [ ] All care plan creation and modification routes through `CreateCarePlan` / `AddCarePlanGoal` invocable actions, not direct DML
- [ ] All referral creation routes through ICC invocable actions, not direct DML on `ReferralRequest__c`
- [ ] `System.debug()` calls referencing clinical object fields are removed or gated by a Custom Metadata debug flag
- [ ] Production debug log retention policy reviewed — no persistent logs containing PHI
- [ ] Unit tests cover callback interface methods and invocable action calls with mock responses
- [ ] Consent enforcement via `AuthorizationFormConsent` is not bypassed by any code path

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CarePlanProcessorCallback requires Setup registration** — Deploying a class that implements `HealthCloudGA.CarePlanProcessorCallback` is not sufficient. The class name must be explicitly registered in Health Cloud Setup > Care Plan Settings. An unregistered callback silently does nothing; there is no deploy-time or runtime error.
2. **Direct DML on clinical objects bypasses consent enforcement** — Inserting or updating `CarePlan`, `CarePlanGoal`, or `CarePlanProblem` directly bypasses `AuthorizationFormConsent` evaluation. The record is created, but the consent check never fires. This is both a compliance gap and a functional gap — Health Cloud UI features that depend on consent state will behave inconsistently.
3. **Apex debug logs containing clinical fields are PHI** — `EhrPatientMedication`, `PatientHealthCondition`, `ClinicalEncounterCode`, and similar objects contain protected health information. Debug logs are stored in plaintext and are accessible to any system administrator. Production debug logging on clinical Apex classes must be disabled by default, time-limited when enabled for troubleshooting, and purged immediately after use.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Compliant HealthCloudGA Apex extension class | A `global` Apex class implementing the target HealthCloudGA interface with correct method signatures and Setup registration instructions |
| Invocable action call pattern | Apex snippet using `Invocable.Action` to call `CreateCarePlan`, `AddCarePlanGoal`, or ICC referral actions with input/output handling |
| Debug logging governance checklist | List of `System.debug()` statements audited for PHI exposure with recommended Custom Metadata gate pattern |
| Unit test scaffold | `@IsTest` class covering callback methods and action calls, using Health Cloud test data factories where available |

---

## Related Skills

- `admin/care-plan-configuration` — Required prerequisite: care plan templates and ICM configuration must be in place before Apex extensions can be effectively implemented or tested
- `apex/apex-security-patterns` — Security patterns for FLS, CRUD, and sharing enforcement that also apply to clinical Apex classes
- `apex/clinical-decision-support` — Clinical decision logic patterns that frequently interact with care plan and referral Apex extension points
