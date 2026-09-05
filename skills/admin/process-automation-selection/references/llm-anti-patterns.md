# LLM Anti-Patterns — Process Automation Selection

Common mistakes AI coding assistants make when advising on which Salesforce automation tool to use.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Process Builder or Workflow Rules for new automation

**What the LLM generates:** "Use Process Builder to update the Account Rating when an Opportunity closes."

**Why it happens:** LLMs trained on pre-2025 content reference Process Builder and Workflow Rules as viable options. Both reached end of support on 31 December 2025. The correction an assistant usually over-shoots: they did not stop *executing*. Existing rules and processes still run and can still be activated, deactivated and edited — they simply receive no fixes and no enhancements, which is exactly why they rot quietly. Build nothing new in them; migrate existing logic. UNVERIFIED (2026-09-04): the end-of-support date is not stated in the extracted Metadata API, Apex Developer or Object Reference guides; `standards/decision-trees/automation-selection.md` sources it to Salesforce Help article 001096524, which cannot be fetched here.

**Correct pattern:**

```
Automation tool status:
- Workflow Rules: END OF SUPPORT 31 Dec 2025 — still executes, no fixes. Migrate to Flow.
- Process Builder: END OF SUPPORT 31 Dec 2025 — still executes, no fixes. Migrate to Flow.
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

**Why it happens:** LLMs describe automations as isolated, and when they do quote the order of execution they routinely get the positions wrong — most often putting validation rules and before triggers on the wrong side of each other, or after-save flows before after triggers. The real sequence is numbered in the Apex Developer Guide and is worth pasting rather than recalling.

**Correct pattern** — the step numbers below are the guide's own, from *Triggers and Order of Execution* (apexdev.txt L15414–L15489):

```
Salesforce order of execution (server side, the automation-relevant steps):
 1. Load the original record (or initialize it for an upsert).
 2. Load new field values from the request; run system validation.
 3. Record-triggered flows configured to run BEFORE the record is saved.
 4. All BEFORE triggers.
 5. Most system validation again, plus custom validation rules.
 6. Duplicate rules (a blocking duplicate stops here — no after triggers, no workflow).
 7. Save the record to the database, not yet committed.
 8. All AFTER triggers.
 9. Assignment rules.
10. Auto-response rules.
11. Workflow rules. A workflow FIELD UPDATE then re-saves the record and re-runs
    before update AND after update triggers one more time, and only one more time.
    Validation rules, flows, duplicate rules, Process Builder and escalation rules
    do NOT run again in that pass.
12. Escalation rules.
13. Process Builder processes and workflow-launched flows, in no guaranteed order.
14. Record-triggered flows configured to run AFTER the record is saved.
15. Entitlement rules.
16-17. Roll-up summary recalculation on parent, then grandparent.
18. Criteria Based Sharing evaluation.
19. Commit all DML.
20. Post-commit logic: email, enqueued async Apex, async paths in record-triggered flows.

Note: during a RECURSIVE save, Salesforce skips steps 9 through 17 — which
means after-save record-triggered flows (14) and assignment rules (9) do not
fire on records another automation put back through the save procedure.

Design considerations:
- Before-save flow (3) runs BEFORE before triggers (4), so it cannot see anything
  the trigger computes; after-save flow (14) runs AFTER after triggers (8).
- If two automations on the same object conflict, the execution order determines
  which "wins."
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
