# Lightning App Configuration — [App Name]

## App Summary

| Field | Value |
|---|---|
| App Name (Label) | [e.g., Field Service Operations] |
| App API Name | [e.g., Field_Service_Operations] |
| App Type | [ ] Standard Lightning App &nbsp;&nbsp;[ ] Console App |
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
- [ ] Default landing page (first nav item) loads correctly

---

## Notes / Decisions

[Document any decisions made during configuration, e.g., why console vs standard, why certain tabs were excluded, etc.]
