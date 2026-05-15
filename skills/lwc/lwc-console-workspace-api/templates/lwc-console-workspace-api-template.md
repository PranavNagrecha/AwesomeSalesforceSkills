# LWC Console Workspace API — Work Template

Use this template when designing or reviewing an LWC that manipulates Service Console tabs.

## Scope

**Skill:** `lwc-console-workspace-api`

**Request summary:** (one-line description of the bundle and what it does)

## Host Posture

| Question | Answer |
|---|---|
| Will the component run only in Service Console? Y/N | |
| Will it also render in App Builder preview, Experience Cloud, mobile? | |
| Where is it mounted? (record page / utility bar / app page / overlay) | |

## Tab Actions Required

Tick each action the component will perform:

- [ ] `openTab` — open a new primary workspace tab
- [ ] `openSubtab` — open a subtab under a specified primary
- [ ] `focusTab` — bring a tab to the foreground
- [ ] `refreshTab` — re-fetch the tab's underlying record / page
- [ ] `closeTab` — close a tab
- [ ] `setTabLabel` — change the displayed tab label
- [ ] `setTabIcon` — change the tab icon
- [ ] `setTabHighlighted` — visually emphasize the tab
- [ ] `getFocusedTabInfo` — query the currently focused tab
- [ ] `getAllTabInfo` — enumerate all open tabs
- [ ] `getEnclosingTabId` — get the tab id for "this" component's tab

## Utility Bar Actions (if applicable)

- [ ] `openUtility` / `minimizeUtility`
- [ ] `setUtilityLabel` / `setUtilityIcon` / `setUtilityHighlighted`
- [ ] `getEnclosingUtilityId` / `getUtilityInfo`

## Console-Detection Wiring

- [ ] `@wire(IsConsoleNavigation) isConsole;` declared
- [ ] Every workspace-API call is gated by `if (this.isConsole) { ... } else { ...fallback... }`
- [ ] No `this.isConsole` read in `connectedCallback` (wire not yet emitted)
- [ ] Non-console fallback identified for each action: ____________

## Refresh Pairing

For each refresh trigger, identify the matching action:

| Trigger | Refresh call | Notes |
|---|---|---|
| imperative Apex DML | `refreshTab(await getEnclosingTabId())` (inside console) + `refreshApex` (outside) | |
| `lightning-record-edit-form onsuccess` | (LDS notifies automatically; refreshTab usually unnecessary) | |
| LMS message from sibling tab | `refreshTab(tabId)` for matching `recordId` from `getAllTabInfo` | |

## Promise Rejection Handling

- [ ] Each workspace-API call wrapped in `try { ... } catch (e) { ... }` or `.catch(...)`
- [ ] Rejection produces a degraded-but-usable UX (toast, console.error, retry button)

## Jest Test Coverage

- [ ] Test 1: `isConsole === true` branch (mock the wire adapter to emit `true`)
- [ ] Test 2: `isConsole === false` branch
- [ ] Test 3 (if refresh involved): assert DOM state AFTER `await Promise.resolve()` twice post-refresh

## Tab ID Hygiene

- [ ] Tab id never persisted to sessionStorage / localStorage / record field
- [ ] Domain identifier (recordId) used as the cross-reload anchor instead

## Notes

(Record deviations from the standard pattern and why.)
