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

## Anti-Pattern 2: Recommending Direct Edits to a Published Action Plan Template

**What the LLM generates:** "Open the Action Plan template, find the task, and change its DaysFromStart value," applied to a template whose version is already published.

**Why it happens:** The model defaults to "open and edit" for configuration changes, and invents a `DaysFromStart` field because many task tools have one.

**Correct pattern:**

```
To change a published onboarding template:
1. Create a new version (or the org's documented clone path) in Draft.
2. Change items there; due dates are ActivityDate value formulas such as StartDate + 5.
3. Publish the new version (version Status = Final).
4. Plans already launched stay on their original version; apply the in-flight policy.
5. Name the version clearly, for example "Client Onboarding v3".
```

**Detection hint:** Any edit instruction for a published template, or any mention of `DaysFromStart` or `TaskDeadlineType`.

---

## Anti-Pattern 3: Using Required Flags as Sequencing

**What the LLM generates:** A flat task list where compliance steps are marked required, presented as if that stops later steps from starting.

**Why it happens:** "Required" sounds like "must happen first". In Action Plans it only records that the item must be done.

**Correct pattern:**

```
For each regulatory "A before B" rule:
- Mark A and B required (IsRequired = true).
- Add an actionPlanTemplateItemDependencies entry:
    previousTemplateItem = A, templateItem = B, creationType = OnPreviousItemCompleted
- Record the owner and the escalation path if A is not done within its SLA.
```

**Detection hint:** A regulated onboarding design with required items and no dependencies or approval steps between phases.

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

## Anti-Pattern 6: Asserting an Unconfirmed Item Limit, or Ignoring Template Size

**What the LLM generates:** Either a 90-item single template with no thought for size, or a confident "Action Plans have a hard 75-task limit" statement.

**Why it happens:** The 75-item figure circulates in older content, but it does not appear in the Object Reference or Metadata API entries for Action Plans read on 2026-10-03.

**Correct pattern:**

```
Before finalizing the item inventory:
1. Count items across all stages.
2. For very large templates, launch a test plan in a sandbox before sign-off.
3. Prefer phased templates (Pre-Onboarding and Document Collection; Compliance Review and Activation),
   launching phase 2 when phase 1's ActionPlanState reaches Complete.
4. Document the split in the process map.
```

**Detection hint:** A limit stated as fact with no source, or a very large single template with no size test.

---

## Anti-Pattern 7: Editing `IsRequired` on a Document Checklist Item to Waive a Document

**What the LLM generates:** "Uncheck Required on the document checklist item for this client."

**Why it happens:** The model assumes every checkbox is editable.

**Correct pattern:** `DocumentChecklistItem.IsRequired` is set at creation and has no Update property. Record exceptions as `Status = Waived` (values: `Accepted`, `New`, `Pending`, `Waived`) with a comment, so the waiver is auditable.

**Detection hint:** Any update to `IsRequired` on an existing document checklist item.

---

## Anti-Pattern 8: Assuming Every Record Can Anchor an Action Plan

**What the LLM generates:** "Create the onboarding template on FinancialAccount," with no check.

**Why it happens:** Financial Account is the natural FSC anchor, and the model does not know the parent lists differ between guides.

**Correct pattern:** The Metadata API template parent list does not include Financial Account; the plan object list includes it from API 48.0. Launch a test plan on the intended anchor in a sandbox, and fall back to Account or Opportunity if it fails.

**Detection hint:** A template `targetEntityType` chosen without a sandbox launch test.
