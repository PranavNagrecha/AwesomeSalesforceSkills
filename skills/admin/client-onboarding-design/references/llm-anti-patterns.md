# LLM Anti-Patterns — Client Onboarding Design

Common mistakes AI assistants make when generating or advising on FSC client onboarding process design. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating OmniStudio as Included With FSC

**What the LLM generates:** A process design that specifies OmniScript as the intake tool for guided client data collection without any mention of licensing requirements — implying OmniStudio is a standard FSC feature.

**Why it happens:** FSC documentation prominently features OmniStudio examples and OmniScript workflows because the products are frequently licensed together. Training data conflates "commonly used with FSC" with "included in FSC." The LLM reproduces this conflation.

**Correct pattern:**

```
Before recommending OmniStudio OmniScripts or FlexCards:
1. Confirm org has OmniStudio installed: Setup > Installed Packages > search "OmniStudio"
2. If OmniStudio is NOT installed → design guided intake as Screen Flow
3. If OmniStudio IS installed → OmniScript is the preferred intake design
4. Document the license basis in the technology selection rationale artifact
```

**Detection hint:** Any process design that specifies OmniScript or FlexCard without a preceding license confirmation step should be flagged for review.

---

## Anti-Pattern 2: Recommending Direct Edits to an Active Action Plan Template

**What the LLM generates:** Instructions such as "open the Action Plan template, find the task you want to update, and edit the DaysFromStart field" — applied to an already-published (Active) template.

**Why it happens:** LLMs default to the intuitive "open and edit" pattern for configuration updates. The immutability constraint on published Action Plan templates is a platform-specific behavior that is not obvious from general Salesforce patterns.

**Correct pattern:**

```
To update a published Action Plan template:
1. Navigate to the active template
2. Click "Clone" to create a Draft copy
3. Edit the Draft copy (name, tasks, deadlines, owners)
4. Activate the Draft clone (Status = Active) — this becomes the new version
5. Leave the original template active until all in-flight plans on it are closed
6. Follow the naming convention (e.g., "Client Onboarding v3") for the new version
```

**Detection hint:** Any instruction to "edit," "update," or "modify" an Action Plan template without first cloning it should be flagged if the template is already published.

---

## Anti-Pattern 3: Skipping Compliance Gate Design in Favor of a Flat Task List

**What the LLM generates:** A flat Action Plan task list with all tasks at equivalent priority, no required flags, and no sequencing constraints — presented as a complete onboarding design.

**Why it happens:** LLMs optimize for simplicity in task lists and tend to produce flat checklists. The regulatory requirement that certain steps must be completed before subsequent steps are permitted is a domain-specific constraint that requires explicit design, not just a list.

**Correct pattern:**

```
For each compliance-mandatory checkpoint:
- Set the task as required (Required = true on ActionPlanTemplateItem)
- Document the gate condition: "Stage N cannot begin until [task X] is closed"
- Identify the owner and escalation path if the gate is not cleared within SLA
- In the process map, draw an explicit gate between phases where required tasks
  must be completed before the next phase's tasks are launched
```

**Detection hint:** A process design with no required tasks and no phase gates in a financial services onboarding context should be reviewed for missing compliance checkpoint enforcement.

---

## Anti-Pattern 4: Omitting Template Versioning Governance From the Process Design

**What the LLM generates:** A detailed onboarding process map and Action Plan task inventory with no mention of how the process will be updated post-launch — treating template versioning as an implementation detail to be figured out later.

**Why it happens:** Versioning governance is a process management concern rather than a technical one. LLMs focus on the immediate deliverable (the onboarding design) and do not proactively raise operational governance questions unless prompted.

**Correct pattern:**

```
Template versioning governance must be included in every client onboarding process design:
- Named template owner (role, not person)
- Change request protocol (who initiates, who approves, minimum lead time)
- Naming convention for versions (e.g., "[Use Case] v[N]")
- In-flight plan policy (complete on current version vs. manual remediation)
- Review trigger (when does the template get reviewed — annually, on regulatory change, on audit finding)
```

**Detection hint:** A process design deliverable that has no governance section and no mention of how template updates will be managed after go-live is incomplete.

---

## Anti-Pattern 5: Designing the Welcome Journey Handoff Without Specifying the Trigger

**What the LLM generates:** "When onboarding is complete, send the client a welcome email and start the welcome journey." — with no specification of what platform event or field change constitutes "onboarding complete" or what data the downstream system needs.

**Why it happens:** Welcome journey descriptions are often stated in business terms ("when done, send welcome"). LLMs reproduce the business-level description without translating it into the specific trigger event, field name, value, and data payload that an implementation team needs to configure the automation.

**Correct pattern:**

```
Welcome journey handoff specification must include:
- Trigger: the specific field and value that fires the handoff
  (e.g., FinancialAccount.Status changes to "Active")
- Channel: email / SMS / portal notification / Marketing Cloud journey
- Timing: immediate, N days after trigger, or scheduled
- Data payload: the exact fields the downstream system needs
  (e.g., Contact.FirstName, FinancialAccount.Name, User.Name [advisor],
   User.Email [advisor], FinancialAccount.AccountNumber)
- Fallback: what happens if the downstream system is unavailable
```

**Detection hint:** Any welcome journey description that does not name a specific trigger field/value and does not list the data payload fields is underspecified and should be completed before implementation begins.

---

## Anti-Pattern 6: Exceeding the 75-Task Limit Without a Split Design

**What the LLM generates:** A comprehensive onboarding Action Plan template with 90+ individual task items covering every document, signature, and checklist step — presented as a single template without noting the 75-task hard limit.

**Why it happens:** LLMs generating detailed task inventories for complex regulated onboarding processes will naturally produce large lists. The 75-task platform limit is a non-obvious constraint that the LLM does not automatically apply unless it has been trained on this specific FSC behavior.

**Correct pattern:**

```
Before finalizing the Action Plan task inventory:
1. Count total tasks across all stages
2. If total > 75: split into sequential phased templates
   - Phase 1 template: Pre-Onboarding + Document Collection
   - Phase 2 template: Compliance Review + Activation
3. Design the Phase 1 → Phase 2 handoff trigger
   (e.g., Flow triggered on ActionPlan Status = Completed)
4. Document the split in the process map so the handoff is explicit
```

**Detection hint:** Any onboarding task inventory with more than 60 items that does not mention splitting into phases should be reviewed against the 75-task limit.
