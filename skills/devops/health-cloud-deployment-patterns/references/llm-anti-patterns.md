# LLM Anti-Patterns — Health Cloud Deployment Patterns

Common mistakes AI coding assistants make when generating or advising on Health Cloud deployment patterns. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Omitting Managed Package Installation from the Deployment Plan

**What the LLM generates:** A deployment plan that starts directly with `sf project deploy start` or a change set upload, listing all metadata components including those in the HealthCloudGA namespace, without any mention of installing the HealthCloudGA managed package first.

**Why it happens:** LLMs default to the standard Salesforce metadata deployment workflow, which does not require managed package installation. Training data for standard Salesforce deployments vastly outnumbers Health Cloud-specific deployment walkthroughs. The model generalizes the simpler pattern.

**Correct pattern:**

```
Step 1: Install Salesforce Industries Common Components (if required)
  sf package install --package 04t... --target-org <alias> --wait 10

Step 2: Install HealthCloudGA managed package
  sf package install --package 04t... --target-org <alias> --wait 20

Step 3: [Additional feature packages if required]

Step 4: Deploy org-specific metadata
  sf project deploy validate --target-org <alias> --manifest manifest/package.xml
  sf project deploy start --target-org <alias> --manifest manifest/package.xml

Step 5: Execute post-deploy manual checklist
  - Assign Permission Set Licenses
  - Register CarePlanProcessorCallback in Health Cloud Setup
  - Create care plan templates via invocable actions
```

**Detection hint:** Scan for any Health Cloud deployment plan that begins with `sf project deploy` or a change set without a prior managed package install step. If `HealthCloudGA` appears in metadata references but no `sf package install` appears before the deploy command, the plan is incomplete.

---

## Anti-Pattern 2: Treating CarePlanProcessorCallback Registration as a Metadata Deploy Step

**What the LLM generates:** A deployment plan or Apex migration script that attempts to deploy or insert the CarePlanProcessorCallback registration as part of the metadata deployment — either by including a Custom Metadata record in the package, or by inserting a `HealthCloudGA__CarePlanProcessorSetting__mdt` record via DML or Metadata API.

**Why it happens:** LLMs recognize that Custom Metadata records can be deployed via the Metadata API and generalize this to all Custom Metadata, including those in managed namespaces. The model does not know that `HealthCloudGA__CarePlanProcessorSetting__mdt` is a managed-namespace CMT that cannot be written via customer-org deploy operations.

**Correct pattern:**

```
CarePlanProcessorCallback registration is a MANUAL post-deploy step.

1. Deploy the CarePlanProcessorCallback Apex class via sf project deploy
2. After deploy completes, navigate in the target org to:
   Setup > Health Cloud Setup > Care Plan Settings
3. In the "CarePlan Processor Callback" field, select the deployed class name
4. Click Save

This step must be in the deployment runbook. It cannot be automated via:
- sf project deploy
- Metadata API upsert
- Anonymous Apex DML on HealthCloudGA__CarePlanProcessorSetting__mdt
```

**Detection hint:** Look for any script or deployment plan that includes `HealthCloudGA__CarePlanProcessorSetting__mdt` in a `package.xml`, a `sf project deploy` command, or a DML insert. Any of these patterns indicates the anti-pattern.

---

## Anti-Pattern 3: Inserting Care Plan Templates via Direct DML

**What the LLM generates:** Apex code or a data migration script that creates `HealthCloudGA__CarePlanTemplate__c` records using `insert` or `Database.insert()`, often with child `CarePlanTemplateEntry__c` and `CarePlanTemplateGoal__c` records.

**Why it happens:** The objects are visible in SOQL and the org's schema, so LLMs assume they can be created like any other custom object. The LLM is unaware of the invocable action requirement enforced by the Health Cloud platform layer.

**Correct pattern:**

```apex
// WRONG: Direct DML
HealthCloudGA__CarePlanTemplate__c template = new HealthCloudGA__CarePlanTemplate__c(
    Name = 'Diabetes Management',
    HealthCloudGA__Description__c = 'Standard diabetes care plan'
);
insert template; // May succeed but produces non-functional template

// CORRECT: Use invocable action via Apex
// Build input for HealthCloud.CreateCarePlanTemplate
List<HealthCloud.CreateCarePlanTemplateInput> inputs = new List<HealthCloud.CreateCarePlanTemplateInput>();
HealthCloud.CreateCarePlanTemplateInput input = new HealthCloud.CreateCarePlanTemplateInput();
input.templateName = 'Diabetes Management';
input.templateDescription = 'Standard diabetes care plan';
// Add entries and goals per the invocable action's input structure
inputs.add(input);
HealthCloud.CreateCarePlanTemplate.createCarePlanTemplates(inputs);

// OR: Use the Health Cloud Care Plan Templates Setup UI
// Health Cloud Setup > Care Plan Templates > New
```

**Detection hint:** Search generated code for `insert` statements targeting `HealthCloudGA__CarePlanTemplate__c`, `HealthCloudGA__CarePlanTemplateEntry__c`, or `HealthCloudGA__CarePlanTemplateGoal__c`. Any direct DML on these objects is the anti-pattern.

---

## Anti-Pattern 4: Skipping HIPAA BAA Verification and Jumping Directly to Technical Configuration

**What the LLM generates:** A Health Cloud go-live checklist that begins with Shield Platform Encryption setup, care plan configuration, and user permission assignment — without any mention of confirming that a signed HIPAA BAA is in place with Salesforce.

**Why it happens:** LLMs are trained primarily on technical documentation. HIPAA BAA verification is a legal/contractual step, not a technical configuration step, so it is underrepresented in technical documentation and therefore underweighted by the model. The model jumps to the actionable technical steps it knows well.

**Correct pattern:**

```
HIPAA Pre-Go-Live Checklist (in order):

1. LEGAL: Confirm signed HIPAA BAA with Salesforce Account team
   - Request copy of executed BAA from Salesforce
   - Do NOT proceed with PHI import until BAA is confirmed
   
2. TECHNICAL: Enable Shield Platform Encryption
   - Generate and activate tenant secret
   - Define encryption policies for all PHI fields
   - Verify policies are active before importing any PHI

3. TECHNICAL: Restrict debug log access in production
   - Remove Modify All Data / View All Data from debug-enabled profiles
   - Document log purge procedure

4. OPERATIONAL: Configure audit logging
   - Enable Field Audit Trail or Event Monitoring for clinical record access

Only after steps 1-4 are confirmed complete:
5. Import PHI data
```

**Detection hint:** Any Health Cloud go-live checklist that omits "confirm signed HIPAA BAA" as an explicit first step before technical configuration is applying this anti-pattern. Look for checklists that start with "Enable Shield Platform Encryption" with no preceding BAA confirmation step.

---

## Anti-Pattern 5: Assuming Sandbox Refresh Preserves Health Cloud Configuration

**What the LLM generates:** A sandbox refresh runbook that refreshes the sandbox from production and then states "Health Cloud configuration is inherited from production — no additional steps required." Or a runbook that only lists org-specific metadata deployment as the post-refresh step, omitting package reinstall and manual configuration steps.

**Why it happens:** Sandbox refresh does preserve org-specific metadata (custom objects, flows, Apex). LLMs generalize this to assume all configuration is preserved, not recognizing that managed package installations, PSL assignments, and Health Cloud Setup registrations are outside the metadata snapshot used for sandbox refresh.

**Correct pattern:**

```
Post-Sandbox-Refresh Health Cloud Reconfiguration Checklist:

1. Reinstall managed packages (NOT preserved by sandbox refresh)
   - Salesforce Industries Common Components (if applicable)
   - HealthCloudGA at same version as production
   - Feature packages (Provider Search, etc.)

2. Reassign Permission Set Licenses (NOT preserved by sandbox refresh)
   - Assign Health Cloud PSLs to all test user personas

3. Re-register CarePlanProcessorCallback (NOT preserved by sandbox refresh)
   - Setup > Health Cloud Setup > Care Plan Settings > set callback class

4. Recreate care plan templates (NOT preserved by sandbox refresh)
   - Re-run care plan template setup via invocable actions or Setup UI

5. Verify Shield Encryption policies are active
   - Some encryption configurations may need to be reapplied in sandbox

6. Smoke test
   - Open a care plan, run through the Care Plan wizard, confirm templates appear
```

**Detection hint:** Any sandbox refresh runbook for a Health Cloud org that does not include "reinstall HealthCloudGA managed package" and "re-register CarePlanProcessorCallback" as explicit post-refresh steps is applying this anti-pattern.

---

## Anti-Pattern 6: Configuring Shield Encryption After PHI Data Import

**What the LLM generates:** A setup sequence that imports data (including PHI or PHI-shaped test data) and then configures Shield Platform Encryption policies to secure the imported data. The plan assumes the encryption policy will retroactively protect the already-imported records.

**Why it happens:** Shield Platform Encryption is often presented in documentation as an "org configuration step" without explicit callout that it only applies to future writes. LLMs trained on general encryption concepts assume that enabling encryption protects all data at rest, including data that existed before the policy was activated.

**Correct pattern:**

```
WRONG order:
1. Import test data
2. Configure Shield Platform Encryption
3. Assume all data is now encrypted  <-- INCORRECT

CORRECT order:
1. Enable Shield Platform Encryption
2. Generate and activate tenant secret
3. Define encryption policies for all PHI fields
4. VERIFY policies are active (check Encryption Statistics)
5. ONLY THEN import any PHI data

If PHI was already imported before encryption was configured:
- Delete existing PHI records
- Re-import after encryption policies are confirmed active
- Or contact Salesforce Support for bulk encryption assistance
  (not a self-service operation)
```

**Detection hint:** Any data migration or import plan for a Health Cloud org that does not confirm "Shield Platform Encryption policies are active" as a prerequisite step before the first data import is applying this anti-pattern.
