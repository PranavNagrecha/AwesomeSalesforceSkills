---
name: lwc-wire-refresh-patterns
description: "refreshApex, getRecordNotifyChange, and RefreshView API for LWC data refresh: when wired data is stale, forcing re-fetch after imperative DML, cross-component refresh, 2024 RefreshView replacement of getRecordNotifyChange. NOT for wire basics (use lwc-wire-service). NOT for Lightning Data Service writes (use lwc-lds-writes)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
tags:
  - lwc
  - refreshapex
  - getrecordnotifychange
  - refreshview
  - wire
triggers:
  - "refreshapex wire service stale data after dml"
  - "getrecordnotifychange deprecation refreshview"
  - "lwc wire data not updating after update"
  - "how to refresh related list after child dml"
  - "refreshview api lwc spring 24 replacement"
  - "force rerun wire after imperative apex call"
inputs:
  - Wire adapter in use (getRecord, custom Apex wire)
  - Trigger for refresh (imperative call, platform event, parent change)
  - Cross-component refresh requirement
outputs:
  - Refresh pattern (refreshApex, RefreshView, wire re-provision)
  - Cross-component messaging approach
  - Test strategy for refresh flows
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# LWC Wire Refresh Patterns

Activate when an LWC's `@wire`-provisioned data becomes stale after an imperative DML, child record change, or cross-component event. Salesforce offers several refresh primitives — `refreshApex`, `getRecordNotifyChange` (deprecated), the newer `RefreshView` API, and wire re-provisioning via parameter change — each fits a specific scenario.

## Before Starting

- **Identify the wire adapter.** Custom Apex wire? Use `refreshApex`. Standard `getRecord`? Use `RefreshView` (or legacy `notifyRecordUpdateAvailable`).
- **Know about RefreshView.** Introduced Summer '24, replacing `getRecordNotifyChange` for standard UI API refreshes across the view.
- **Avoid forced re-render hacks** like nulling params then restoring — tends to break and confuses framework caching.

## Core Concepts

### refreshApex(wiredValue)

For custom Apex wires. Hold onto the raw wired value (not the destructured data) and call `refreshApex(this._wiredAccounts)`:

```
@wire(getAccounts, { filter: '$filter' })
wiredAccounts;

handleRefresh() { return refreshApex(this.wiredAccounts); }
```

### RefreshView API

Declarative refresh signal across the page/view:

```
import { RefreshEvent } from 'lightning/refresh';
this.dispatchEvent(new RefreshEvent());
```

Components in the view listen via `@wire(RefreshView)` or by implementing `refresh()`. Replaces `getRecordNotifyChange` for view-scoped refresh.

### notifyRecordUpdateAvailable (legacy)

`import { notifyRecordUpdateAvailable } from 'lightning/uiRecordApi';` — still works; informs LDS that specific records changed.

### Wire re-provision by param change

Changing a reactive `@wire` parameter re-runs the wire automatically. Useful when refresh is triggered by user action that changes context.

## Common Patterns

### Pattern: refreshApex after imperative DML

```
async save() {
    await updateAccount({ acc: this.acc });
    await refreshApex(this.wiredAccounts);
}
```

### Pattern: Dispatch RefreshEvent from a child after save

Child modal saves a record → dispatches `new RefreshEvent()` → parent (or the view) refreshes its wires.

### Pattern: Cross-component refresh via Lightning Message Service

Sibling components can't share wired data. Use LMS to publish a "data changed" event; siblings subscribe and call their own refresh.

## Decision Guidance

| Scenario | Refresh mechanism |
|---|---|
| Custom Apex wire, same component | refreshApex(wiredValue) |
| Standard getRecord, after save | RefreshView (RefreshEvent) or notifyRecordUpdateAvailable |
| Cross-view, global refresh | RefreshEvent at the app-level listener |
| Sibling components needing refresh | Lightning Message Service + per-component refresh |
| Param-driven context change | Reassign reactive @wire param |

## Recommended Workflow

1. Identify the wire adapter — custom Apex vs UI API.
2. For custom Apex: store the raw wired value; call `refreshApex` on it.
3. For UI API: dispatch `RefreshEvent` or call `notifyRecordUpdateAvailable`.
4. For sibling coordination: wire LMS; subscribe and refresh per-component.
5. Avoid param-nulling hacks.
6. Test refresh flows with Jest (mock `refreshApex` + wire adapters).
7. Document refresh ownership — which component is responsible for triggering refresh.

## Review Checklist

- [ ] Custom Apex wires use `refreshApex(rawWiredValue)`
- [ ] Standard wires use `RefreshEvent` or `notifyRecordUpdateAvailable`
- [ ] No param-null-then-restore hacks
- [ ] Cross-component refresh coordinated via LMS or parent
- [ ] Refresh triggers after imperative DML, not before
- [ ] Jest tests cover refresh flow
- [ ] Migration plan from deprecated `getRecordNotifyChange` documented

## Salesforce-Specific Gotchas

1. **`refreshApex` requires the RAW wired value, not the destructured `data`.** Store `wiredFoo` (full object) not `wiredFoo.data`.
2. **`getRecordNotifyChange` is deprecated.** Migrate to `RefreshView` + `notifyRecordUpdateAvailable`.
3. **Reassigning `@track` data to itself does NOT refresh wires.** Wires re-run only when reactive params change or explicit refresh is invoked.

## Output Artifacts

| Artifact | Description |
|---|---|
| Refresh pattern selection | Per wire / per trigger mapping |
| LMS channel for refresh signals | Cross-component plumbing |
| Migration plan | Legacy getRecordNotifyChange → RefreshView |

## Related Skills

- `lwc/lwc-wire-service` — wire fundamentals
- `lwc/lwc-lightning-message-service` — cross-component events
- `lwc/lwc-lds-writes` — updateRecord/createRecord semantics
