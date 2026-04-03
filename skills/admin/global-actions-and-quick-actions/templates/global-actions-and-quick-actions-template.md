# Quick Action Configuration — [Object or Global]

**Date:** [YYYY-MM-DD]
**Configured by:** [Admin Name]
**Environment:** [Sandbox / Production]

---

## Action Summary

| Field | Value |
|---|---|
| Action Name (API) | [e.g., New_Contact] |
| Action Label | [e.g., New Contact] |
| Action Type | [Create / Update / Log a Call / Custom / Flow / Send Email] |
| Target Object (if Create) | [e.g., Contact] |
| Scope | [Object-Specific: Account] or [Global] |

---

## Action Layout Fields

Fields included in the action form (in display order):

| # | Field API Name | Field Label | Required | Predefined Value |
|---|---|---|---|---|
| 1 | [e.g., FirstName] | First Name | No | — |
| 2 | [e.g., LastName] | Last Name | Yes | — |
| 3 | [e.g., AccountId] | Account Name | Yes | `{!Account.Name}` |
| 4 | | | | |
| 5 | | | | |

Fields set via predefined value but NOT shown in the form (hidden background values):

| Field API Name | Value / Formula |
|---|---|
| [e.g., RecordTypeId] | [e.g., Customer Contact record type ID] |

---

## Predefined Values

| Field | Value Type | Formula / Literal |
|---|---|---|
| [Account Name] | Field Reference | `{!Account.Name}` |
| [Status] | Literal | `Active` |

---

## Page Layout Placement

| Page Layout | Object | Action Position |
|---|---|---|
| [Account Layout] | Account | Position 2 (visible in action bar) |
| [Global Layout] | Global | Position 1 |

---

## Profiles / Permission Access

| Profile | Page Layout Assigned | Can See This Action |
|---|---|---|
| [Sales User] | [Account Layout] | Yes |
| [Read-Only] | [Account Read Layout] | No — action not on that layout |

---

## Test Results

- [ ] Action appears in Lightning Experience highlights panel (desktop)
- [ ] Action appears in Salesforce mobile app action bar
- [ ] Predefined values are populated correctly when action opens
- [ ] All required fields are present in the action layout
- [ ] Record saves successfully with valid data
- [ ] Profiles without the page layout assignment cannot see the action

---

## Notes / Decisions

[Document any non-obvious choices made, e.g., why a field was hidden via predefined value vs shown on the layout.]
