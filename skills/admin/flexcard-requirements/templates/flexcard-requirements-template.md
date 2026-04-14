# FlexCard Requirements — Work Template

Use this template to capture FlexCard requirements before development begins.

## Scope

**Skill:** `flexcard-requirements`

**FlexCard Name:** (fill in)
**Business Purpose:** (fill in)
**Deployment Context:** Lightning Record Page / Service Console / Experience Cloud / Standalone
**User Persona:** Internal agent / Experience Cloud authenticated / Experience Cloud guest
**OmniStudio License:** Confirmed on [Cloud Name]

---

## Data Source Mapping Matrix

| Field Displayed | Source Object/API | Data Source Type | Notes |
|---|---|---|---|
| | | SOQL / DataRaptor / Integration Procedure / Apex / Streaming | |

**Integration Procedure name (if IP used):** ______

---

## Card State Templates

| State Name | Condition Expression | Description |
|---|---|---|
| | `{FieldName} == 'Value'` | |

---

## Action Requirements Register

| Button / Trigger Label | Action Type | Target / Destination | Data Passed from Card | Notes |
|---|---|---|---|---|
| | Navigation / OmniScript Launch / Apex / DataRaptor / Custom LWC | | | |

---

## Embedded Component Requirements

| Component Name | Type | Build Status | Activation Dependency |
|---|---|---|---|
| | Child FlexCard / OmniScript / Custom LWC | Already built / In development | Must activate before this card |

---

## Build and Activation Dependency Order

List dependencies in activation order:
1. (IP Name) — must be Active before card activation
2. (Child FlexCard Name) — must be Active before parent card activation
3. (Custom LWC Name) — must be deployed before card activation
4. This FlexCard

---

## Review Checklist

- [ ] OmniStudio license confirmed and deployment context documented
- [ ] All displayed data fields mapped to a data source type
- [ ] All user actions documented with type and outcome
- [ ] Card state templates specified with condition expressions
- [ ] Embedded components identified with activation/deployment dependencies noted
- [ ] Experience Cloud / guest user permissions documented if applicable
- [ ] Build and activation dependency order documented
