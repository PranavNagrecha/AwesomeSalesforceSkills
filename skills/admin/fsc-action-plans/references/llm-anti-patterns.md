# LLM Anti-Patterns — FSC Action Plans

Common mistakes AI coding assistants make when generating or advising on FSC Action Plans.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting Direct Editing of a Published Template

**What the LLM generates:** "To update the task deadline in your published Action Plan template, open the ActionPlanTemplate record, click Edit, update the DaysFromStart field on the relevant ActionPlanTemplateItem, and save."

**Why it happens:** LLMs trained on generic Salesforce admin content know that most records can be edited via standard record edit. They do not consistently model the FSC Action Plans immutability constraint on Active templates, which is a domain-specific platform behavior not present in standard CRM objects.

**Correct pattern:**

```
To update a task in a published (Active) Action Plan template:
1. Open the Active ActionPlanTemplate record.
2. Use the Clone action to create a Draft copy.
3. Rename the clone to reflect the new version (e.g., "Client Onboarding v2").
4. Edit the ActionPlanTemplateItem records on the Draft clone.
5. Set the clone's Status to Active to publish.
6. Communicate to advisors to use the new template for all future plan launches.
7. Retain the original Active template until all plans bound to it are closed.
```

**Detection hint:** Any response that says "edit the published template", "update the active template", or "modify the ActionPlanTemplateItem on the live template" is incorrect.

---

## Anti-Pattern 2: Claiming New Template Versions Update In-Flight Plans

**What the LLM generates:** "Once you publish the updated template, all existing action plans using that template will automatically reflect the new task list."

**Why it happens:** LLMs reason by analogy to other versioning systems (e.g., Flow version activation, where old versions are deactivated and new ones take over). They incorrectly apply that mental model to Action Plans, which are bound permanently to the template version at launch time.

**Correct pattern:**

```
Publishing a new ActionPlanTemplate version (via clone-and-republish) 
does NOT affect in-flight ActionPlan instances. Existing plans continue 
running against the original template's task list. Only plans launched 
AFTER the new template is published will use the new task list.

If open plans must reflect the updated task list, they must be 
explicitly closed/cancelled and relaunched from the new template — 
a deliberate data migration, not an automatic platform capability.
```

**Detection hint:** Any response containing "automatically update existing plans", "retroactively apply", or "propagate to open plans" in the context of template versioning is incorrect.

---

## Anti-Pattern 3: Treating FSC Action Plans as Standard Task Automation or Flow

**What the LLM generates:** "You can achieve the same result using a Flow that creates Task records with the appropriate due dates" — then proceeds to design a full Flow automation as an equivalent alternative to Action Plan templates.

**Why it happens:** LLMs know Salesforce Flow can create Task records. They do not consistently distinguish between the Action Plans feature (versioned, grouped, reportable task sequences with built-in deadline offset math and Required-task enforcement) and ad-hoc Task creation via Flow, which lacks these properties.

**Correct pattern:**

```
FSC Action Plans and Flow-created Tasks are not equivalent:
- ActionPlan groups all tasks in a single plan record with completion tracking
- ActionPlanTemplate provides versioned, reusable task sequences
- Required-task enforcement on ActionPlanItem blocks plan completion
- DaysFromStart provides built-in deadline offset calculation from plan start date
- ActionPlan is a reportable object for book-of-business process completion monitoring

Flow is appropriate when task creation must be conditional, branching, 
or dynamic. For structured repeatable checklists, use Action Plan templates.
```

**Detection hint:** Any response that substitutes Flow task creation for an Action Plan template design request is likely missing the key Action Plans features listed above.

---

## Anti-Pattern 4: Suggesting FSC Objects Are Available Without FSC License

**What the LLM generates:** "Set TargetEntityType to FinancialAccount on your ActionPlanTemplate to target financial account records." (Without mentioning that FSC must be enabled.)

**Why it happens:** LLMs know the FSC object names (FinancialAccount, InsurancePolicy, etc.) from training data but do not consistently model the license/feature gate that makes these TargetEntityType values appear. They assume the objects are universally available in any org with Action Plans enabled.

**Correct pattern:**

```
FSC-specific TargetEntityType values are ONLY available when Financial 
Services Cloud is enabled in the org. Before configuring a template for 
FinancialAccount, InsurancePolicy, ResidentialLoanApplication, FinancialGoal, 
PersonLifeEvent, or BusinessMilestone, verify:

1. FSC is enabled: Setup > Financial Services > Settings
2. Org license includes FSC: Setup > Company Information > Licenses
3. The TargetEntityType picklist on ActionPlanTemplate displays FSC objects

If FSC is not active, only standard objects (Account, Contact, Opportunity, 
Lead, Contract, Case, Campaign) appear in the picklist.
```

**Detection hint:** Any response that instructs setting TargetEntityType to an FSC object without first confirming FSC is enabled is incomplete.

---

## Anti-Pattern 5: Ignoring the 75-Task Hard Limit

**What the LLM generates:** A design for a single ActionPlanTemplate with 80–100 task items for a complex onboarding or compliance workflow, with no mention of the platform limit.

**Why it happens:** LLMs generate task lists by requirement without tracking platform-specific object count limits. The 75-task-per-plan limit is a domain-specific FSC constraint that is not commonly documented in general Salesforce admin content.

**Correct pattern:**

```
ActionPlan instances support a maximum of 75 ActionPlanItem records.
Exceeding this limit causes plan launch to fail.

For complex workflows requiring more than 75 tasks:
1. Split into sequenced phase templates (e.g., "Onboarding Phase 1" 
   and "Onboarding Phase 2"), each under 75 tasks.
2. Use Flow to automatically launch the Phase 2 plan when Phase 1 
   is marked Complete.
3. Name templates to reflect their phase sequence so launchers 
   understand the workflow structure.
```

**Detection hint:** Any template design that lists more than 75 task items without acknowledging the platform limit and providing a multi-phase workaround is non-compliant.

---

## Anti-Pattern 6: Conflating BusinessDays Deadline Mode With Holiday-Aware Deadlines

**What the LLM generates:** "Set TaskDeadlineType to BusinessDays to ensure tasks are due only on working days, excluding weekends and holidays."

**Why it happens:** The term "business days" in natural language includes holiday exclusion in most business contexts. LLMs apply that natural language definition to the Salesforce field, incorrectly inferring holiday awareness from the name.

**Correct pattern:**

```
TaskDeadlineType = BusinessDays skips ONLY Saturday and Sunday.
It does NOT skip org-configured holidays (Setup > Business Hours > Holidays).

A plan with BusinessDays mode launched the day before a public holiday 
will compute a 1-business-day task as due on the holiday.

For holiday-aware deadlines:
- Use Calendar mode and adjust DaysFromStart manually
- Build post-launch Flow automation to shift due dates falling on holidays
- Communicate to launchers to adjust the plan start date near holidays
```

**Detection hint:** Any response that states or implies BusinessDays excludes holidays is incorrect. Look for phrases like "excluding weekends and holidays" applied to the BusinessDays setting.
