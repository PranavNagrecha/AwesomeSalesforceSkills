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
  - Primary object (workspace tab): ___________
  - Related objects (subtabs): ___________
- **Omni-Channel already enabled?** Yes / No — if yes, are Service Channels and Presence Configs defined?
- **CTI adapter installed?** Yes / No — if yes, adapter name: ___________
- **Existing app to replace or new build?** Existing app name: ___________ / Net new
- **Known constraints:** ___________

---

## App Configuration

| Property | Value |
|---|---|
| App name | |
| Navigation type | Console Navigation (do NOT use Standard) |
| Navigation items (in order) | 1. Cases  2.   3.   4. |
| Default landing tab | Cases (first item) |
| Assigned profiles | |

---

## Utility Bar Items

| Utility | Include? | Load on Start? | Notes |
|---|---|---|---|
| History | Yes | No | Console apps only |
| Omni-Channel | Yes / No | Yes (if routing active) | Requires Omni-Channel prereqs |
| Macros | Yes | No | |
| Open CTI Softphone | Yes / No | No | Requires CTI adapter |
| Quick Text | Yes / No | No | |

---

## Navigation Rules

| Object | Rule | Reason |
|---|---|---|
| Case | Workspace Tab | Primary agent work object |
| Contact | Subtab of current workspace | Reference record; opened from Case |
| Account | Subtab of current workspace | Reference record; opened from Case |
| Knowledge Article | Subtab of current workspace | Reference record |
| (add others) | | |

---

## Macros to Create

| Macro Name | Trigger Scenario | Actions |
|---|---|---|
| | | |
| | | |

---

## Quick Text to Create

| Entry Name | Channel | Content Summary |
|---|---|---|
| | Email | |
| | Chat | |

---

## Checklist

- [ ] App created with Console Navigation (verified in App Manager)
- [ ] Navigation items in correct order (primary object first)
- [ ] App profile visibility assigned to correct agent profiles
- [ ] Navigation rules configured — Cases as workspace tabs, Contact/Account/Knowledge as subtabs
- [ ] Utility bar items added and tested
- [ ] Omni-Channel prerequisites completed before adding utility (if applicable)
- [ ] Macros created and Macros permission enabled on agent profile
- [ ] Quick Text entries created with correct channel assignments
- [ ] Keyboard shortcuts reviewed
- [ ] Validated end-to-end as an agent user in a sandbox or test environment

---

## Notes

Record any deviations from the standard pattern and the reason for each deviation.

(e.g., "Account set to Workspace Tab because agents independently initiate Account reviews outside of Cases")
