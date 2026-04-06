# LLM Anti-Patterns — Solution Design Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce automation layer selection and solution design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Apex for Every Non-Trivial Requirement

**What the LLM generates:** "This requirement is complex enough that you should write an Apex trigger" for requirements that are well within Flow's capabilities, such as multi-condition field updates, related record creation, or sending notifications based on field changes.

**Why it happens:** Apex is disproportionately represented in training data because developers write about it extensively. LLMs equate "non-trivial" with "needs code" even when Salesforce's declarative tools (Flow, validation rules, formula fields) handle the pattern natively and with lower maintenance cost.

**Correct pattern:**

```text
Use Flow (not Apex) when the requirement involves:
- Before-save field updates (record-triggered flow, before context)
- After-save actions: create related records, send emails, post to Chatter
- Approval processes or multi-step user interactions (screen flows)
- Scheduled operations on record sets (scheduled-triggered flows)
- Simple conditional branching with fewer than 15 decision paths

Escalate to Apex when:
- HTTP callouts are needed in a synchronous record-save context
- Complex error handling with try-catch and partial rollback is required
- The logic needs Apex-specific APIs (Crypto, Queueable chaining, EventBus)
- Unit test coverage is required for ISV package certification
- Performance profiling shows measurable Flow overhead at scale
```

**Detection hint:** Flag Apex trigger recommendations where the stated requirement is field updates, record creation, or email notifications — all natively supported by record-triggered Flows.

---

## Anti-Pattern 2: Mixing Automation Tools on the Same Object Without Acknowledging Order of Execution

**What the LLM generates:** "Add a Flow to update the field and also add an Apex trigger to handle the validation" without addressing Salesforce's order of execution, which determines when triggers, flows, validation rules, and assignment rules fire relative to each other.

**Why it happens:** LLMs treat each automation recommendation independently without modeling how they interact within Salesforce's fixed execution order. Training data rarely shows the full order of execution, only individual patterns.

**Correct pattern:**

```text
Before adding automation to an object, map the existing execution order:

1. Record-triggered before-save Flows (before triggers)
2. System validation (required fields, field types)
3. Before triggers (Apex)
4. Custom validation rules
5. After triggers (Apex)
6. Assignment rules, auto-response rules
7. Record-triggered after-save Flows
8. Workflow rules (legacy)
9. Escalation rules
10. Roll-up summary field recalculation

Adding a new Flow or trigger without mapping existing automation risks:
- Infinite loops (Flow triggers trigger, trigger triggers Flow)
- Validation rule blocking intended updates from automation
- Governor limit consumption from cascading DML
```

**Detection hint:** Flag recommendations that add Flow AND Apex trigger on the same object without referencing order of execution or potential recursion control.

---

## Anti-Pattern 3: Suggesting Process Builder or Workflow Rules for New Automation

**What the LLM generates:** "Create a Process Builder to update the parent record when the child is modified" or "Set up a Workflow Rule to send an email notification" — recommending deprecated automation tools for new development.

**Why it happens:** Process Builder and Workflow Rules were the primary declarative automation tools for years and dominate training data. LLMs do not consistently apply Salesforce's retirement timeline: Workflow Rules are in maintenance mode, and Process Builder was retired for new creation in Spring '23.

**Correct pattern:**

```text
For ALL new automation, use Flow:
- Record-Triggered Flow replaces Process Builder and Workflow Rules
- Screen Flow replaces Visualforce pages for guided user interactions
- Scheduled-Triggered Flow replaces time-based Workflow actions
- Platform Event-Triggered Flow replaces Process Builder event subscriptions

Process Builder: no new creation since Spring '23. Migrate existing ones.
Workflow Rules: maintenance mode. No new features. Migrate existing ones.

Use the Salesforce Migrate to Flow tool to convert existing Process Builders.
```

**Detection hint:** Flag any recommendation containing "Process Builder" or "Workflow Rule" for new automation. Look for `ProcessDefinition`, `WorkflowRule`, or `WorkflowFieldUpdate` in metadata recommendations.

---

## Anti-Pattern 4: Over-Engineering with Custom LWC When Standard Components Suffice

**What the LLM generates:** Custom LWC code to build a record detail page, related list, or data table when Salesforce provides standard Lightning components (Dynamic Forms, Related Lists, Enhanced Related Lists, Lightning App Builder standard components) that accomplish the same result without code.

**Why it happens:** LLMs are code-generation tools that default to building custom solutions. They are not trained to first evaluate whether a standard drag-and-drop component in Lightning App Builder already meets the requirement.

**Correct pattern:**

```text
Before building custom LWC, check standard options:
1. Dynamic Forms: conditional field visibility, field sections on record pages
2. Dynamic Actions: conditional action button visibility
3. Enhanced Related List: inline editing, custom columns, no code
4. Highlights Panel: key fields at top of record page
5. Rich Text, Report Charts, Recent Items: standard App Builder components
6. lightning-datatable: standard LWC base component (if custom table is needed)

Build custom LWC only when:
- The interaction pattern is not available in any standard component
- Real-time external data rendering is required
- Complex client-side computation or visualization is needed
- The component will be reused across many pages or apps
```

**Detection hint:** Flag custom LWC proposals where the described functionality matches a standard Lightning App Builder component. Look for custom implementations of record detail, related list, or data table patterns.

---

## Anti-Pattern 5: Hard-Coding Record Type IDs, Profile IDs, or User IDs in Automation

**What the LLM generates:** Apex code or Flow formulas that reference hard-coded 15- or 18-character Salesforce IDs for record types, profiles, or users — values that differ between sandbox and production.

**Why it happens:** LLMs generate code from training examples that often include specific IDs as placeholders. The habit of using Custom Metadata Types, Custom Labels, or Schema describe methods to resolve IDs dynamically is underrepresented in training data.

**Correct pattern:**

```text
Never hard-code Salesforce IDs in automation. Use dynamic resolution:

Record Types:
  Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName()
    .get('Business_Account').getRecordTypeId()

Profiles (avoid querying by name if possible — use Permission Sets instead):
  [SELECT Id FROM Profile WHERE Name = :profileName LIMIT 1]

Custom Metadata for environment-specific values:
  Config_Setting__mdt setting = Config_Setting__mdt.getInstance('Key_Name');

Custom Labels for strings that vary by environment:
  System.Label.Integration_Endpoint
```

**Detection hint:** Regex for 15- or 18-character Salesforce IDs in Apex or Flow metadata: `['\"]0[0-9A-Za-z]{14,17}['\"]`. Flag any match that is not a test-context ID factory.

---

## Anti-Pattern 6: Ignoring Bulkification in Flow Design

**What the LLM generates:** Record-triggered Flow designs that use "Get Records" and "Update Records" elements inside a loop, which causes separate SOQL queries and DML operations per record — hitting governor limits when processing bulk record changes.

**Why it happens:** Flow's visual designer encourages per-record thinking. LLMs replicate this pattern because most Flow training examples show single-record scenarios. Bulk-safe Flow patterns (collection variables, loop-then-DML-outside-loop) are less represented.

**Correct pattern:**

```text
Bulk-safe Flow patterns:
1. Use $Record and $Record__Prior in record-triggered Flows to avoid
   Get Records for the triggering record itself.
2. Collect records to update in a Collection Variable inside the loop.
3. Place the Update Records element OUTSIDE the loop, operating on the
   entire collection.
4. Use the "Get Records" element BEFORE the loop when you need related data,
   not inside the loop.
5. For before-save Flows, use direct field assignment on $Record — no DML
   element needed.

Test Flows with bulk data (200+ records via Data Loader) to verify
governor limit compliance.
```

**Detection hint:** In Flow metadata XML, look for `<actionCalls>` or `<recordUpdates>` elements nested inside `<loops>`. Flag Get Records or DML elements inside loop iterations.
