# LLM Anti-Patterns — Process Automation Selection

Common mistakes AI coding assistants make when advising on which Salesforce automation tool to use.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Process Builder or Workflow Rules for new automation

**What the LLM generates:** "Use Process Builder to update the Account Rating when an Opportunity closes."

**Why it happens:** LLMs trained on pre-2025 content reference Process Builder and Workflow Rules as viable options. Both tools ceased functioning after December 2025. All new automation should be built with Flow. Existing Process Builder and Workflow Rule logic should be migrated.

**Correct pattern:**

```
Automation tool status:
- Workflow Rules: RETIRED (Dec 2025). Migrate to Flow.
- Process Builder: RETIRED (Dec 2025). Migrate to Flow.
- Flow: CURRENT. All new automation uses Flow.
- Apex triggers: CURRENT. Use for complex scenarios beyond Flow's capabilities.

Migration path:
1. Use Setup → "Migrate to Flow" tool for simple processes.
2. For complex Process Builder logic, rebuild in Flow manually.
3. Test thoroughly — Flow execution order differs from Process Builder.
```

**Detection hint:** If the output recommends `Process Builder` or `Workflow Rule` as a new automation tool, it is recommending retired tools. Search for `Process Builder` or `Workflow Rule` as recommendations (not as migration sources).

---

## Anti-Pattern 2: Defaulting to Apex triggers when a Before-Save Flow is sufficient

**What the LLM generates:** "Write an Apex trigger to normalize the Phone field format on save."

**Why it happens:** LLMs default to code solutions because training data is code-heavy. A same-record field normalization (formatting a phone number, setting a default value, copying a field) is a Before-Save Flow task. Before-Save flows use no DML, execute faster, and can be maintained by admins without code deployment.

**Correct pattern:**

```
Automation boundary decision:
- Same-record field update, no external data → Before-Save Flow.
  Examples: format phone, set default status, concatenate fields.
- Related-record update, child creation → After-Save Flow.
  Examples: update Account when Opportunity closes, create Task on Case creation.
- Complex cross-object transaction, callout orchestration,
  governor-limit-sensitive logic → Apex trigger.
  Examples: multi-object rollback, platform event publishing,
  complex conditional logic exceeding Flow complexity limits.
- Scheduled batch operations → Scheduled Flow or Apex Batch.
- User-interactive multi-step process → Screen Flow.

Use the simplest tool that handles the requirement.
```

**Detection hint:** If the output uses Apex for a same-record field update that involves no external queries or complex logic, a Before-Save Flow would be simpler. Search for `trigger` combined with simple field updates on `$Record`.

---

## Anti-Pattern 3: Ignoring the execution order of multiple automations on the same object

**What the LLM generates:** "Create a Before-Save Flow for field validation and an After-Save Flow for the related record update. They will run independently."

**Why it happens:** LLMs describe automations as isolated. Salesforce has a defined order of execution: validation rules fire before triggers, Before-Save flows fire before After-Save flows, and multiple flows on the same object fire in a defined (but not always predictable) order. Conflicting automations cause unexpected behavior.

**Correct pattern:**

```
Salesforce order of execution (simplified):
1. System validation (required fields, field format).
2. Before-Save Flows (record-triggered, before save).
3. Validation Rules.
4. Duplicate Rules.
5. Apex Before Triggers.
6. Record saved to database (not committed).
7. After-Save Flows (record-triggered, after save).
8. Apex After Triggers.
9. Assignment Rules, Escalation Rules.
10. Transaction committed.

Design considerations:
- If two automations on the same object conflict, the execution
  order determines which "wins."
- Use ONE Flow per object per trigger timing where possible
  (consolidate logic into one Before-Save Flow per object).
- Document all automations per object in a single inventory.
```

**Detection hint:** If the output creates multiple automations on the same object without discussing execution order or consolidation, conflicts may arise. Search for `execution order` or `order of execution` in the design.

---

## Anti-Pattern 4: Using Flow for everything when Apex is the right boundary

**What the LLM generates:** "Build a Flow that loops through 5,000 records, makes a callout per record, and creates child records based on the response."

**Why it happens:** LLMs try to stay in the declarative (no-code) world. Some operations exceed Flow's practical capabilities: complex loops with callouts, heavy computation, retry logic, or operations requiring fine-grained governor limit management. Forcing these into Flow creates fragile, unmaintainable automations.

**Correct pattern:**

```
When Apex is the right choice over Flow:
1. Callout orchestration with retry/error handling per callout.
2. Complex data transformations exceeding Flow formula capabilities.
3. Operations requiring bulkified processing beyond Flow's
   auto-bulkification (e.g., platform event publishing at scale).
4. Logic that needs unit test coverage for compliance.
5. Integration patterns requiring custom serialization/deserialization.

Hybrid pattern (recommended):
- Use a Flow as the entry point (record trigger or screen).
- Call an Invocable Apex action for the complex logic.
- Return results to the Flow for downstream steps.
This keeps the orchestration declarative and the complex logic testable.
```

**Detection hint:** If the output builds a Flow with per-record callouts inside a loop or complex computation that would be simpler in Apex, the tool boundary is wrong. Search for `Loop` combined with `HTTP Callout` or `Action` inside the loop.

---

## Anti-Pattern 5: Not documenting the automation inventory for the object

**What the LLM generates:** "Create the new Flow on the Opportunity object. It will handle the status update."

**Why it happens:** LLMs create individual automations without considering the existing automation landscape on the object. An Opportunity object may already have 3 record-triggered flows, 2 validation rules, and an Apex trigger. Adding another flow without inventorying existing automations risks duplication, conflicts, and recursion.

**Correct pattern:**

```
Before adding automation to any object:
1. Inventory existing automations:
   - Record-Triggered Flows (before and after save).
   - Apex Triggers.
   - Validation Rules.
   - Legacy: any remaining Workflow Rules or Process Builders.
2. Check for overlap: does existing automation already handle
   part of the new requirement?
3. Consider consolidation: can the new logic be added to an
   existing Flow instead of creating a new one?
4. Document the automation in a per-object automation registry:
   | Object      | Type          | Name              | Timing     | Purpose           |
   |-------------|---------------|-------------------|------------|-------------------|
   | Opportunity | Flow          | Opp_Before_Save   | Before     | Default values    |
   | Opportunity | Flow          | Opp_After_Save    | After      | Update Account    |
   | Opportunity | Apex Trigger  | OpportunityTrigger| Before/After| Integration sync |
```

**Detection hint:** If the output creates a new automation without inventorying existing automations on the object, conflicts may arise. Search for `existing automation`, `inventory`, or `consolidate` in the design.
