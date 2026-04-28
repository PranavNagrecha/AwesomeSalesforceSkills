# Validation Rule Patterns — canonical patterns

Used by `validation-rule-auditor`, `data-loader-pre-flight`, and consulted by `object-designer` and `automation-migration-router` (when source-type is `approval_process`).

Validation Rules are the most overloaded automation surface in Salesforce orgs. They accidentally become "trigger lite" ("fire an error message if the contact has no email during an integration sync") and are responsible for a large share of integration fault tickets. The patterns below are what a senior architect expects a VR to look like.

---

## The six valid uses of a Validation Rule

A VR is the right tool **only** when:

1. **Data integrity on user-driven edits** — user cannot create/update the record in a shape that violates the business rule.
2. **Cross-field dependency** — one field's value constrains another's on the same record.
3. **Stage-gate enforcement** — user cannot advance Stage/Status without prerequisite data.
4. **Write-time audit trail requirement** — a field cannot be cleared once set (compliance).
5. **Preventing bulk-unsafe changes** — block mass Owner reassignments on a particular record type, etc.
6. **Enforcing a formula-computable invariant** — e.g. `Discount__c < List_Price__c`.

A VR is **the wrong tool** for:

- Applying a default value (use a default formula on the field, or a Before-Save flow).
- Calculating a value (use a formula field or a flow).
- Transforming a value on save (use a Before-Save flow).
- Implementing approval logic (use Approval Process or Orchestrator).
- Checking data against external systems (use a flow with an invocable action).
- Blocking integrations that the integration's *design* already permits — use a Custom Permission / bypass instead.

The audit agent flags VRs that fall into the wrong-tool set and suggests the correct automation via `standards/decision-trees/automation-selection.md`.

---

## The canonical VR shape

Every well-formed VR has the following structure in its `ErrorConditionFormula`:

```text
AND(
  /* 1. Bypass condition — always first, OR'd inverse */
  NOT($Setup.Integration_Bypass__c.Is_Active__c),
  NOT($Permission.Bypass_Validation_<Domain>),

  /* 2. Relevance gate — when does this rule even apply? */
  ISPICKVAL(RecordType.DeveloperName, "..."),
  NOT(ISNEW()),  /* or ISNEW(), or AND(...), depending on intent */

  /* 3. The actual business rule — what is invalid? */
  OR(
    AND(ISCHANGED(Amount), Amount < 0),
    AND(ISPICKVAL(StageName, "Closed Won"), ISBLANK(CloseDate))
  )
)
```

- **Bypass FIRST.** Every VR MUST admit a bypass via either a Custom Setting (`Integration_Bypass__c`) OR a Custom Permission (`Bypass_Validation_<Domain>`). Both, in practice. See `skills/admin/validation-rules` for the canon.
- **Relevance gate SECOND.** Scope the VR to the record types / states it's intended for. An un-scoped VR on Account fires in every integration, every import, every test class.
- **Business rule LAST.** Keep it readable — a single OR of logical clauses. Complex nested logic is a sign the rule should be split.

---

## Bypass contract

**The `Integration_Bypass__c` Hierarchy Custom Setting and the `Bypass_Validation_<Domain>` Custom Permission are NOT optional.** Every VR the agent generates includes both. Every VR the agent audits is expected to have at least one (preferably both).

Why both:
- **Custom Setting** is how integrations disable VRs at the user level (the integration user is granted an org-level bypass for stable data loads).
- **Custom Permission** is how short-lived bypasses work for migration or data-fix operations — assign the permission via a time-limited PS (`Temp_Data_Fix_Feb26`), run the fix, unassign.

Missing bypass = P1 finding. The agent proposes a patch.

---

## IsChanged / IsNew patterns

- `ISNEW()` — fires only on insert. Use for "Required on create" gates.
- `NOT(ISNEW())` — fires only on update. Use for "Cannot change once set" rules.
- `ISCHANGED(Field)` — fires when the field value moves. Use for stage-transition gates. **Never** use `ISCHANGED` without `NOT(ISNEW())` wrapping it, or the rule fires on insert too (ISCHANGED is true for a new record).
- `PRIORVALUE(Field)` — the value at the start of the save context. Use for "cannot regress" rules (Stage can only move forward).

Common bugs the audit agent catches:
- `ISCHANGED(Field)` alone → fires on insert.
- `ISBLANK(Field)` on a formula/rollup field — `ISBLANK` is not reliable on formula fields; use `ISNULL` for numeric formulas, compare to `""` for text.
- `NOT(ISPICKVAL(Field, "X"))` when the intent is "not one of X or Y" — use `AND(NOT(ISPICKVAL...), NOT(ISPICKVAL...))`.

---

## VR + Flow coexistence

When a Before-Save flow and a VR both touch the same record:

1. Before-Save flow runs first (in the trigger chain order: before-save flow → apex before → VR → apex after → after-save flow).
2. If the flow *repairs* the data before save, the VR should NOT fire for that case. Scope the VR so the repaired case is outside its relevance gate.
3. If the flow *computes* a value the VR depends on, the VR can reference that computed value safely — it's already in context.

The `skills/apex/trigger-and-flow-coexistence` skill governs the mental model. When the agent sees both a VR and a Before-Save flow on the same object, it inspects for mutual consistency and reports conflicts.

---

## What the agent should do with this file

**When creating a VR (`object-designer`, human request):**

1. Confirm the rule belongs to one of the 6 valid-use categories. If not, recommend the correct tool and stop.
2. Compose the canonical shape above: Bypass → Relevance gate → Business rule.
3. Name per `templates/admin/naming-conventions.md` (`<Object>_<Field_or_Concept>_<Action>`).
4. Output a Setup-ready rule description + `ErrorConditionFormula` + suggested `ErrorMessage` (short, actionable, no "Error:", no uppercase shouting).
5. Generate the migration patch for missing Custom Settings / Custom Permissions if they don't exist yet.

**When auditing (`validation-rule-auditor`):**

1. List all active VRs on the target object via `list_validation_rules` (MCP tool added in Wave 0).
2. For each, classify: has bypass? has relevance gate? within the 6 valid uses? overlaps with another VR or Before-Save flow?
3. Report findings at P0 (missing bypass on integration-critical object, blocking known integrations), P1 (wrong-tool — should be a flow / formula default), P2 (naming drift, readability).
4. In Process Observations: note patterns — "12 of 14 VRs on Account have bypass; the 2 outliers were created in 2019 before the convention". Pattern signal > individual signal.

---

## Source skills

- `skills/admin/validation-rules`
- `skills/admin/formula-fields`
- `skills/admin/picklist-field-integrity-issues`
- `skills/apex/trigger-and-flow-coexistence`
- `skills/data/data-quality-and-governance`
