# Service Console Configuration — Work Template

Use this template when configuring or reviewing a Lightning Service Console app for a support team.

## Scope

**Skill:** `service-console-configuration`

**Request summary:** (fill in what the user asked for — e.g., "Set up a Service Console app for the Tier-1 case team with Omni-Channel and macros")

---

## Context Gathered

Answer these before making any changes:

- **Service Cloud license confirmed?** Yes / No
- **Target objects and their role:**
  - Primary object (mapping with NO fieldName): ___________
  - Related objects, each with the lookup field on ITS OWN object that names the parent:
    ___________ via `___________`  (e.g. Contact via `AccountId`)
  - Any "subtab" requirement with no such lookup? List it here — it is not buildable as a
    mapping and needs a design decision: ___________
- **Omni-Channel already enabled?** Yes / No — if yes, are Service Channels and Presence Configs defined?
- **CTI adapter installed?** Yes / No — if yes, adapter name: ___________
- **Existing app to replace or new build?** Existing app name: ___________ / Net new
  - If existing: its `AppDefinition.NavType` is ___________ (`navType` is Not updateable — `Standard` means rebuild, not edit)
- **Utility bar shared with another app?** Run `SELECT DeveloperName, Label, UtilityBar FROM AppDefinition WHERE UtilityBar != null` — other apps on the same bar: ___________
- **Shared workstations?** Yes / No → `isNavTabPersistenceDisabled` = ___________
- **Known constraints:** ___________

---

## App Configuration

| Property | Value |
|---|---|
| App name | |
| Navigation type | `navType` = `Console` (leave `isServiceCloudConsole` absent — it is the Classic flag) |
| Navigation items (in order) | 1. Cases  2.   3.   4. |
| Default landing tab | Cases (first item) |
| Utility bar FlexiPage (owned by this app) | |
| Assigned profiles (via `PermissionSet.applicationVisibilities`) | |

---

## Utility Bar Items

Panel width / height / label are **component decorators** on the utility bar FlexiPage, not app fields.
Copy every `componentName` out of a retrieve — do not type them from memory.

| Utility | Include? | `componentName` (from retrieve) | Decorator width / height | Region |
|---|---|---|---|---|
| History | Yes / No | | | `Region` |
| Omni-Channel | Yes / No | | | `Region` |
| Macros | Yes / No | | | `Region` |
| Open CTI Softphone | Yes / No | | | `Region` |
| Notes | Yes / No | | | `Region` |
| (background listener, no button) | Yes / No | | n/a | `Background` |

---

## Workspace Mappings (`workspaceConfig` > `mappings`)

One row per `<tabs>` entry — including the primary tabs, where `fieldName` is deliberately blank.
`fieldName` is a lookup **on the tab's own object** pointing at the parent, and the parent's tab must
also be in this app.

| `<tab>` | `<fieldName>` | Result | Parent tab in app? | Reason |
|---|---|---|---|---|
| `standard-Case` | *(blank)* | Primary tab | n/a | Primary agent work object |
| `standard-Account` | *(blank)* | Primary tab | n/a | Agents also open Accounts directly |
| `standard-Contact` | `AccountId` | Subtab of `Contact.AccountId`'s Account | Yes / No | Reference record |
| | | | | |

---

## Macros to Create

`Operation` is only `Select` / `Set` / `Insert` / `Submit` / `Close` (+ `IF`/`ELSEIF`/`ELSE`/`ENDIF`
from API 46.0). `SortOrder` is 0-based; row 0 selects a `Tab.<Entity>` target.

| Macro Name | `StartingContext` | SortOrder | Operation | Target | Value / ValueRecord |
|---|---|---|---|---|---|
| | | 0 | Select | `Tab.` | |
| | | 1 | | | |
| | | 2 | | | |

---

## Quick Text to Create

`Channel` is a **multipicklist** — put every applicable channel on ONE record (`;`-separated in CSV),
not one record per channel. Set `IsInsertable` explicitly.

| Entry Name | Category | Channel(s) | IsInsertable | Content Summary |
|---|---|---|---|---|
| | | `Email;Chat` | true | |
| | | | | |

---

## Checklist

- [ ] `navType` = `Console`; `isServiceCloudConsole` absent
- [ ] `defaultLandingTab` set explicitly
- [ ] One `mappings` entry per `<tabs>` entry, primary ones included
- [ ] Every `fieldName` verified as a field on that tab's own object
- [ ] `utilityBar` FlexiPage is `type` `UtilityBar` and used by this app alone
- [ ] `isNavTabPersistenceDisabled` reflects the shared-workstation answer
- [ ] App/tab visibility assigned via `PermissionSet.applicationVisibilities` + `tabSettings`
- [ ] Omni-Channel prerequisites completed before adding the utility (if applicable)
- [ ] Macro instruction rows use only the five documented operations, `SortOrder` 0-based with no gaps
- [ ] Quick Text records carry all applicable channels on one record; `IsInsertable` set
- [ ] Keyboard shortcuts: developer handler confirmed for any `customShortcuts`
- [ ] `python3 scripts/check_service_console_configuration.py --manifest-dir <source root>` passes
- [ ] Post-deploy queries run: `AppDefinition.NavType`, shared `UtilityBar`, `MacroInstruction` order, `MacroUsage` failures
- [ ] Validated end-to-end as an agent user in a sandbox — Contact from a Case lands under the right Account

---

## Notes

Record any deviations from the standard pattern and the reason for each deviation.

(e.g., "Account set to Workspace Tab because agents independently initiate Account reviews outside of Cases")
