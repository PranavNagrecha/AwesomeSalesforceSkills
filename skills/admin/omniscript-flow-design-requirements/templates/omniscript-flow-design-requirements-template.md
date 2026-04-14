# OmniScript Flow Design Requirements — Work Template

Use this template to capture OmniScript requirements before development begins.

## Scope

**Skill:** `omniscript-flow-design-requirements`

**OmniScript Name:** (fill in)
**Business Process:** (fill in)
**User Persona:** (Internal agent / Experience Cloud authenticated user / Experience Cloud guest)
**Org Runtime:** Standard Runtime (Spring '25+) / Package Runtime (VBT managed package)
**OmniStudio License:** Confirmed on [Cloud Name]

---

## Step Inventory

| Step # | Step Label | Description | Pre-Step Data Source | Post-Step Data Source |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Screen Elements per Step

For each Step, list elements:

**Step 1 — [Step Label]**
| Element Name | Element Type | Required? | Notes |
|---|---|---|---|
| | | | |

**Step 2 — [Step Label]**
| Element Name | Element Type | Required? | Notes |
|---|---|---|---|
| | | | |

---

## Branching Logic (Conditional Views)

For each conditional path, complete:

| Block Name | Triggering Element | Condition Expression | Elements Inside Block |
|---|---|---|---|
| | [Radio Button name] | `%FieldName:value% == 'Value'` | |

---

## Data Requirements Matrix

| Step | Data Source Type | Object / API | Action Type | Timing | Fields Mapped |
|---|---|---|---|---|---|
| | DataRaptor Read / Transform / IP / Remote Action | | Read / Write | Pre-Step / Post-Step | |

---

## Action Requirements Register

| Action Type | Triggering Element | Target / Destination | Notes |
|---|---|---|---|
| Navigation | | URL / Record / OmniScript | |
| OmniScript Launch | | Child OmniScript name | |
| Apex / DataRaptor | | | |

---

## Navigate Action

**Type:** Navigate to Record / Navigate to URL / Navigate to OmniScript
**Target:** (record ID expression / URL / OmniScript Type+Sub Type)
**Condition (if conditional):** `%FieldName:value% == 'Value'`

---

## Review Checklist

- [ ] OmniStudio license confirmed and org runtime documented
- [ ] At least one Step element documented
- [ ] At least two data source bindings specified (read and write)
- [ ] All branching conditions documented in Block + Conditional View notation
- [ ] Navigate Action type and destination specified
- [ ] Data requirements matrix complete with field mappings
- [ ] External API calls specified as Integration Procedure (not DataRaptor)
- [ ] Experience Cloud guest user permissions noted if applicable
