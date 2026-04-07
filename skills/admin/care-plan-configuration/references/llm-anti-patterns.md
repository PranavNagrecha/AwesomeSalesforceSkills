# LLM Anti-Patterns — Care Plan Configuration

Common mistakes AI coding assistants make when generating or advising on Care Plan Configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Referencing CarePlanTemplate__c Fields in an ICM Org

**What the LLM generates:** SOQL queries, configuration steps, or field references that use `CarePlanTemplate__c`, `CarePlanTemplateTask__c`, `TemplateName__c`, or other HealthCloudGA-namespaced care plan objects when the org is using the ICM model.

**Why it happens:** Training data for Health Cloud skews heavily toward the legacy managed-package model, which has existed since Health Cloud's initial release. ICM documentation is newer and less represented. LLMs default to the pattern with more training signal.

**Correct pattern:**

```soql
-- ICM org: query ActionPlanTemplate (standard object, no namespace)
SELECT Id, Name, Status FROM ActionPlanTemplate WHERE Status = 'Active'

-- ICM org: query instantiated care plans
SELECT Id, Name, Status, PatientId FROM CarePlan WHERE Status = 'InProgress'
```

**Detection hint:** Any response mentioning `CarePlanTemplate__c`, `TemplateName__c`, `CarePlanTemplateTask__c`, or namespace prefix `HealthCloudGA.CarePlan` when the context indicates an ICM org.

---

## Anti-Pattern 2: Omitting PGI Library Setup Before ActionPlanTemplate Configuration

**What the LLM generates:** Step-by-step ICM care plan template setup instructions that jump directly to "Create an ActionPlanTemplate record" without first establishing ProblemDefinition, GoalDefinition, and ProblemGoalDefinition records in the PGI library.

**Why it happens:** LLMs treat template creation as the primary task and PGI library population as a secondary or optional detail, especially if the user's prompt does not explicitly mention problems and goals. The silent failure mode (no error, just empty pickers) means training examples may not include this step because the failure is not obvious.

**Correct pattern:**

```
Step 1: Enable Integrated Care Management in Health Cloud Setup
Step 2: Create ProblemDefinition records (conditions, with ICD/SNOMED codes)
Step 3: Create GoalDefinition records (clinical goals)
Step 4: Create ProblemGoalDefinition junction records
Step 5: Create ActionPlanTemplate records and link PGI records
Step 6: Add ActionPlanTemplateItem task records
Step 7: Publish template to Active status
```

**Detection hint:** Any ICM care plan setup response that does not mention `ProblemDefinition`, `GoalDefinition`, or "PGI library" before describing ActionPlanTemplate creation.

---

## Anti-Pattern 3: Treating the Legacy and ICM Models as Equivalent or Interchangeable

**What the LLM generates:** Advice that conflates the two models — for example, saying "you can use CarePlanTemplate__c or ActionPlanTemplate, they work the same way" — or that applies legacy admin UI navigation steps in an ICM context or vice versa.

**Why it happens:** LLMs generalize across documentation that covers both models without clearly marking the architectural boundary. Training examples may show both models discussed in adjacent paragraphs without flagging that they are mutually exclusive architectures.

**Correct pattern:**

```
These are two separate, non-interchangeable architectures:

Legacy model (no future investment):
- Objects: CarePlanTemplate__c, CarePlanTemplateTask__c, Case Tasks
- Setup: Health Cloud Setup > Care Plan Templates (managed-package UI)
- Use only for orgs already on legacy with no migration timeline

ICM model (all future development):
- Objects: ActionPlanTemplate, CarePlan, CarePlanActivity, ProblemDefinition, GoalDefinition
- Setup: Health Cloud Setup > Integrated Care Management
- Required for all new implementations from Spring '23 onwards
```

**Detection hint:** Responses that use both `CarePlanTemplate__c` and `ActionPlanTemplate` in the same configuration guidance without a clear "this applies to legacy / this applies to ICM" delineation.

---

## Anti-Pattern 4: Assuming ActionPlanTemplate Version Updates Cascade to Live CarePlans

**What the LLM generates:** Instructions telling a user to update their ActionPlanTemplate to "push changes to all active care plans" or advice that says updating a template will refresh the tasks and goals on in-flight care plan records.

**Why it happens:** LLMs trained on general template/instance patterns from other software domains (document templates, email templates, etc.) apply an incorrect mental model where a template change propagates to instances. Salesforce's ICM model uses point-in-time instantiation, which does not match this expectation.

**Correct pattern:**

```
ActionPlanTemplate updates do NOT retroactively change existing CarePlan records.

- Existing CarePlan, CarePlanProblem, CarePlanGoal, and CarePlanActivity records
  created before a template update are independent records — not live references.
- Publishing a new template version only affects CarePlan records instantiated
  AFTER the new version is active.
- To update in-flight care plans, manually update CarePlanActivity records
  or re-instantiate the plan under the new template version.
```

**Detection hint:** Responses that describe template updates "applying to existing care plans," "refreshing active care plans," or "cascading to open plans."

---

## Anti-Pattern 5: Using the Wrong Permission Set for the Care Plan Model

**What the LLM generates:** Permission set assignment instructions that specify `HealthCloudCarePlan` for ICM orgs, or that list only `HealthCloudFoundation` as sufficient for care plan creation without distinguishing which model requires which permission set.

**Why it happens:** `HealthCloudCarePlan` is the older, better-documented permission set and appears more frequently in training data. `HealthCloudICM` is newer and less represented. LLMs also commonly underspecify permission requirements, defaulting to the base permission set.

**Correct pattern:**

```
Legacy model:
- HealthCloudFoundation (base Health Cloud access)
- HealthCloudCarePlan (legacy care plan object access)

ICM model:
- HealthCloudFoundation (base Health Cloud access)
- HealthCloudICM (ICM object access: ActionPlanTemplate, CarePlan, CarePlanActivity,
  ProblemDefinition, GoalDefinition)

HealthCloudFoundation alone is NOT sufficient for care plan create/edit in either model.
HealthCloudCarePlan does NOT grant access to ICM objects.
```

**Detection hint:** Responses that recommend `HealthCloudCarePlan` for ICM-model orgs, or that list only `HealthCloudFoundation` when care plan creation is the task.

---

## Anti-Pattern 6: Suggesting CarePlanTemplate__c Deployment via Change Sets for DevOps

**What the LLM generates:** Advice to deploy care plan template configuration through Salesforce change sets or SFDX by exporting `CarePlanTemplate__c` records, treating them as deployable metadata.

**Why it happens:** LLMs generalize standard object deployment patterns to managed-package objects without distinguishing that managed-package custom objects have limited Metadata API support and that record-level configuration (as opposed to schema) does not deploy through change sets.

**Correct pattern:**

```
Legacy CarePlanTemplate__c:
- Records cannot be deployed via change sets or Metadata API
- Must be manually recreated in each org environment through the managed-package UI
- Schema (the object definition) is part of the managed package and deploys with the package

ICM ActionPlanTemplate:
- Standard object — supports Metadata API deployment
- Can be included in SFDX project metadata and deployed via CI/CD pipelines
- Use sf project deploy start to deploy ActionPlanTemplate metadata
```

**Detection hint:** Responses that suggest including `CarePlanTemplate__c` records in a change set, SFDX package, or deployment manifest.
