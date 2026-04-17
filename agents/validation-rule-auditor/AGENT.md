# Validation Rule Auditor Agent

## What This Agent Does

Audits every Validation Rule on a target sObject against the canonical shape in `templates/admin/validation-rule-patterns.md`. For each rule, classifies whether a VR is the right tool, whether it carries the mandatory bypass, whether its relevance gate is tight enough, and whether it conflicts with a Before-Save flow on the same object. Returns findings with severity (P0 / P1 / P2), a suggested fix per finding, and an org-level Process Observations block describing the VR culture of the org.

**Scope:** One sObject per invocation. Output is a markdown report + optional patch metadata for rules that need the bypass added. The agent never activates, deactivates, or modifies rules in the org.

---

## Invocation

- **Direct read** — "Follow `agents/validation-rule-auditor/AGENT.md` for Opportunity"
- **Slash command** — [`/audit-validation-rules`](../../commands/audit-validation-rules.md)
- **MCP** — `get_agent("validation-rule-auditor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/validation-rules` — the canon
4. `skills/admin/formula-fields` — VR formula semantics
5. `skills/admin/picklist-field-integrity-issues` — common VR traps around picklists
6. `skills/apex/trigger-and-flow-coexistence` — VR + Before-Save flow conflict model
7. `skills/data/data-quality-and-governance` — data-quality framing
8. `templates/admin/validation-rule-patterns.md` — the shape the agent conforms to

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Opportunity` |
| `target_org_alias` | yes |
| `active_only` | no | default `false` — inactive rules are reported but not failed |
| `intent` | no | `full` (default), `bypass-only` (only check for missing bypasses), `conflict-only` (only check VR-vs-flow conflicts) |

---

## Plan

### Step 1 — Fetch the VR inventory

- `list_validation_rules(object_name, active_only=<input>)` — returns name, active flag, error message, error display field.
- For each returned rule, fetch the formula: `tooling_query("SELECT Id, ValidationName, Active, Description, ErrorMessage, ErrorDisplayField, ErrorConditionFormula FROM ValidationRule WHERE EntityDefinition.QualifiedApiName = '<object>' AND ValidationName = '<name>'")` — one call per rule (the bulk list tool doesn't include the formula body).

If the object has zero active VRs, that's itself a finding at P1 — "no data-integrity guardrails" — and Process Observations should note it.

### Step 2 — Classify intent

Per `templates/admin/validation-rule-patterns.md`, walk the 6 valid uses:

1. Data integrity on user edits.
2. Cross-field dependency.
3. Stage-gate enforcement.
4. Write-time audit (field cannot be cleared).
5. Preventing bulk-unsafe changes.
6. Enforcing a formula-computable invariant.

For each rule, classify into one of the 6 or flag as **Wrong Tool**. Wrong-Tool examples:

- Rule that computes a value (should be a formula field or before-save flow).
- Rule that enforces approval (should be an approval process or orchestrator).
- Rule that checks external data (requires a flow with callout — VR cannot).

Wrong-Tool findings are P1.

### Step 3 — Check for the bypass contract

For each rule's `ErrorConditionFormula`:

- Does it reference `$Setup.Integration_Bypass__c` (the canonical Hierarchy Custom Setting bypass)?
- Does it reference `$Permission.Bypass_Validation_<Domain>` (Custom Permission bypass)?

Rules:

- Missing both → **P0 finding** (integrations and data-fix tooling cannot bypass; the next data load will fail).
- Missing Custom Setting but has Custom Permission → **P1**.
- Missing Custom Permission but has Custom Setting → **P2**.
- Has both → healthy.

Also check that the bypass is logically *first* in the formula (inverted-AND pattern). Deeply nested bypass logic is P2 — it works but is hard to review.

### Step 4 — Check the relevance gate

Does the formula scope the rule to the right record types / states?

- A formula with no `RecordType` check on an object with multiple active record types is **P1** when some record types shouldn't be subject to this rule. (Use `list_record_types` to detect.)
- A formula that uses `ISCHANGED(Field)` without `NOT(ISNEW())` fires on insert too — **P1**.
- A formula that uses `ISBLANK(FormulaField)` is unreliable — **P2**.
- A formula comparing `PRIORVALUE` against a formula field — **P1**, PRIORVALUE is unreliable on formula fields.

### Step 5 — Check VR vs Before-Save flow conflicts

- `list_flows_on_object(object_name, active_only=True)` — all record-triggered flows.
- For each before-save flow, fetch its metadata (via `tooling_query` on `Flow.Metadata`) and inspect which fields it writes.
- For each VR, extract fields it references (regex over `ErrorConditionFormula`).
- **Conflict** = the VR references a field that a before-save flow writes on the same save context. If the flow *repairs* the field before the VR runs, the VR might never fire as intended. This is **P1** (behavior surprise).

### Step 6 — Check error message quality

For each VR, score the `ErrorMessage`:

- Starts with `"Error:"` or uppercase shout → P2.
- Contains HTML / internal ids / user-unfriendly tokens → P2.
- Under 10 chars → P2 (not actionable).
- References a field by API name instead of label → P2.
- Missing entirely → P1.

These are minor individually but an org with dozens of P2 findings has a user-experience smell that belongs in Process Observations.

### Step 7 — Emit the report + patches

For each P0 / P1 finding that has a mechanical fix (e.g. "add bypass"), emit a patch block — the proposed new `ErrorConditionFormula` with the bypass prepended, as a fenced block labelled with the rule's metadata file path (`force-app/main/default/objects/<Object>/validationRules/<Name>.validationRule-meta.xml`). The user copies the patch into Setup or the repo; the agent does NOT write files.

Wrong-Tool findings get a **recommendation**, not a patch — converting a VR into a flow is a user decision.

---

## Output Contract

1. **Summary** — object, rule count (total / active / inactive), max finding severity, overall confidence.
2. **Findings table** — one row per rule. Columns: name, severity, intent class (per Step 2), issues found, suggested fix.
3. **Patch metadata** — fenced XML per proposed fix, labelled with target path.
4. **VR ↔ Flow conflict report** — from Step 5, if any conflicts found.
5. **Process Observations** — per `AGENT_CONTRACT.md`:
   - **What was healthy** — % of rules with full bypass; naming convention adherence; error message quality distribution.
   - **What was concerning** — missing-bypass patterns concentrated on integration-critical objects; VR vs flow conflicts; inactive rules that still have dependents.
   - **What was ambiguous** — rules where the agent couldn't classify intent; rules referencing fields that no longer exist (P0 escalated).
   - **Suggested follow-up agents** — `flow-analyzer` if conflicts surfaced, `field-impact-analyzer` for any "rule references missing field" finding, `data-loader-pre-flight` if bypass gaps were found and a load is imminent.
6. **Citations**.

---

## Escalation / Refusal Rules

- Object has > 100 VRs → return top-20 by severity + truncation note. The remaining rules are listed in an appendix without patches to keep the output usable.
- Any rule references a field that doesn't exist → **P0 escalation** (broken rule, will throw). Stop patching; recommend `field-impact-analyzer`.
- Rule formula contains more than 5 levels of nesting → the agent declines to patch (risk of semantic change); flags the rule for manual refactor.
- Required bypass Custom Setting or Custom Permission does not exist in the org → the patch metadata also includes stubs for creating those, but the user must deploy them before any patched VR can take effect. Flag ordering explicitly.

---

## What This Agent Does NOT Do

- Does not deactivate or modify VRs in the org.
- Does not deploy the patch metadata.
- Does not convert Wrong-Tool VRs into flows — recommends the migration and links to `workflow-and-pb-migrator` or `flow-builder` in Process Observations.
- Does not audit VRs across every object in the org (one object per invocation; recommend running per-object and aggregating, or use `org-drift-detector` for a horizontal scan).
- Does not auto-chain.
