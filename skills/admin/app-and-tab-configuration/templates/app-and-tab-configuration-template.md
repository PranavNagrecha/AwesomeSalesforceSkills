# Lightning App Configuration — [App Name]

## App Summary

| Field | Value |
|---|---|
| App Name (Label) | [e.g., Field Service Operations] |
| App API Name | [e.g., Field_Service_Operations] |
| App Type (`navType`) | [ ] Standard &nbsp;&nbsp;[ ] Console — permanent, not updateable after creation |
| Form Factors (`formFactors`) | [ ] Large (LEX desktop) &nbsp;&nbsp;[ ] Small (mobile app) |
| Default Landing Tab (`defaultLandingTab`) | [e.g. standard-home, or Field_Ops_Home] |
| Utility Bar FlexiPage (`utilityBar`) | [e.g. Field_Service_Utilities — one per app; shared bars change everywhere] |
| Primary Team/Role | [e.g., Field Technicians] |
| Salesforce Org | [Sandbox / Production] |
| Configured By | [Admin Name] |
| Date | [YYYY-MM-DD] |

---

## Navigation Items

List in display order (first item = default landing page):

| Order | Item Name | Item Type | Notes |
|---|---|---|---|
| 1 | [e.g., Field Visits] | Custom Object Tab | Primary object for this team |
| 2 | [e.g., Accounts] | Standard Object Tab | |
| 3 | [e.g., Contacts] | Standard Object Tab | |
| 4 | | | |

---

## Console Workspace Mappings

Console apps only. One row per navigation item — every tab needs an entry. A blank
Parent Lookup Field means the record opens as its own workspace tab; a filled one means
it opens as a subtab of the record that field points to.

| `<tabs>` value | Opens as | Parent Lookup Field (`fieldName`) |
|---|---|---|
| [e.g. standard-Account] | Workspace tab | *(none)* |
| [e.g. Field_Visit__c] | Subtab | [e.g. Account__c] |
| | | |

---

## Custom Tabs Created

| Tab Name | Tab Type | Object / Page / Component | Icon | Default Visibility |
|---|---|---|---|---|
| [e.g., Field Visits] | Custom Object Tab | Field_Visit__c | [Icon Name] | Default On |
| | | | | |

---

## Utility Bar

| # | Utility Item | Label | Width | Height | Load on Start |
|---|---|---|---|---|---|
| 1 | [e.g., Open CTI Softphone] | Phone | 300 | 500 | [ ] Yes [ ] No |
| 2 | [e.g., History] | History | 300 | 400 | [ ] Yes [ ] No |
| 3 | | | | | |

Note: Utility bar is desktop only. Mobile users will not see these items.
Width, height, and label are stored as component decorators on the utility bar's own
FlexiPage, not on the app. Record the FlexiPage name in the App Summary above and
confirm no other app names the same one.

---

## App Visibility

| Profile / Permission Set | Visible in App Launcher | Notes |
|---|---|---|
| [e.g., Field Technician] | Yes | Primary users |
| [e.g., System Administrator] | Yes | Admin access |
| [e.g., Sales User] | No | Not applicable |

---

## Profile Tab Settings Verified

Confirm each custom tab is NOT set to "Tab Hidden" on target profiles:

| Tab Name | Profile | Tab Setting | Status |
|---|---|---|---|
| [Field Visits] | [Field Technician] | Default On | [ ] Verified |
| | | | |

---

## Testing Checklist

- [ ] Logged in as target profile user in Lightning Experience
- [ ] App appears in App Launcher (waffle menu)
- [ ] All navigation items display in correct order
- [ ] Utility bar items are visible on desktop
- [ ] Tested on Salesforce mobile — utility bar items noted as desktop-only
- [ ] Users without the assigned profile cannot see this app in App Launcher
- [ ] `defaultLandingTab` loads correctly (it is a separate field, not "the first nav item")
- [ ] Console only: each record opens as the intended workspace tab or subtab
- [ ] `AppDefinition` and `AppTabMember` queries return the expected rows when run in a target user's session
- [ ] Checker run clean: `python3 skills/admin/app-and-tab-configuration/scripts/check_app_and_tab_configuration.py --manifest-dir force-app/main/default`

---

## Notes / Decisions

[Document any decisions made during configuration, e.g., why console vs standard, why certain tabs were excluded, etc.]
