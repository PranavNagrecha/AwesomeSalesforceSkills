# Gotchas — Workflow Rule to Flow Migration

Non-obvious Salesforce platform behaviors that cause real production problems during Workflow Rule migration.

## Gotcha 1: Pending Time-Based Actions Are Cancelled on Deactivation

**What happens:** When a Workflow Rule with time-based actions is deactivated, all pending entries in the time-based action queue are immediately and silently cancelled. No notification is sent, and the actions never fire.

**When it occurs:** Any time a Workflow Rule with time-based actions is deactivated — which must happen during migration. For example, if 500 Opportunities are queued to receive a follow-up email in 5 days, those emails will never be sent after the rule is deactivated.

**How to avoid:** Before deactivating, query the time-based workflow queue or audit the `FlowInterview` object. Plan cutover timing to minimize in-flight actions. Communicate to stakeholders that pending time-based actions will not fire after the cutover window. For critical time-based actions, consider running both the Workflow and Flow for one evaluation cycle (but deactivate WR quickly — see Gotcha 3).

---

## Gotcha 2: Outbound Message SOAP Payload Schema May Differ

**What happens:** The Migrate to Flow tool generates an Outbound Message Core Action that references the existing Outbound Message definition. However, the SOAP envelope sent by the Flow action may have structural or namespace differences from the original Workflow-triggered message — headers, field ordering, or envelope structure can vary.

**When it occurs:** Any migration involving Outbound Messages where the receiving integration validates the incoming SOAP schema.

**How to avoid:** Before cutover, capture a sample SOAP payload from the existing Workflow Rule trigger (via the receiving endpoint's logs), then test the Flow-generated payload against it. If the schemas differ, update the receiving endpoint to accept the new format before activating the Flow.

---

## Gotcha 3: ISCHANGED() Criteria Silently Mis-Mapped by Tool

**What happens:** The Migrate to Flow tool does not warn when it encounters `ISCHANGED()` or `ISNEW()` in a Workflow Rule's criteria. The generated flow may omit the condition entirely or generate a Decision that fires unconditionally on every record update.

**When it occurs:** Any Workflow Rule that uses `ISCHANGED(FieldName)` as entry or action criteria.

**How to avoid:** Audit every rule's criteria before running the tool. Any rule with ISCHANGED/ISNEW requires manual rebuild. After using the tool, always open the generated flow in Flow Builder and compare every Decision condition against the original rule.

---

## Gotcha 4: Task Creation Not Converted by Tool

**What happens:** The Migrate to Flow tool silently drops "Create Task" actions from Workflow Rules. The generated flow does not include any equivalent task-creation logic.

**When it occurs:** Any Workflow Rule with a Create Task action.

**How to avoid:** Before running the tool, identify all rules with Create Task actions. After tool conversion, manually add Create Records elements for each task. Alternatively, rebuild the flow entirely from scratch for task-heavy rules.

---

## Gotcha 5: Tool Requires Outbound Message Definition to Pre-Exist

**What happens:** If a Workflow Rule references an Outbound Message and the Outbound Message definition has been deleted or renamed, the Migrate to Flow tool either fails or generates an incomplete action reference that errors at runtime.

**When it occurs:** Migration attempts on stale or recently cleaned-up orgs where Outbound Message definitions were deleted but Workflow Rules still reference them.

**How to avoid:** Before running the tool for rules with Outbound Message actions, verify each referenced definition still exists in Setup > Outbound Messages. If a definition is missing, recreate it or remove the action from the migration scope.
