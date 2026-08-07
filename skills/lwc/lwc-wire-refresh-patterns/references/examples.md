# Examples — LWC Wire Refresh Patterns

Two worked scenarios and one anti-pattern showing the three refresh
primitives in their canonical use cases. Each example assumes the
LWC has already established the relevant `@wire` adapter and the
goal is to force a re-fetch after an external change.

---

## Example 1: `refreshApex` after imperative DML in the same component

**Context:** An LWC shows a list of an account's open Cases using a
custom Apex `@AuraEnabled(cacheable=true)` method, with a "Mark all
high-priority" button that imperatively updates the displayed Cases
through a different Apex method. After the imperative update returns,
the displayed list still shows the old `Priority` values until the
user refreshes the browser.

**Problem:** Lightning Data Service does not cache custom Apex wire
results in a way that recognizes "the Cases I just updated."
Wire adapters re-run on reactive-parameter changes and on a
60-second interval by default (depending on the `cacheable` flag and
the adapter's caching policy) — neither happens fast enough to
update the UI before the user notices. The fix requires explicit
`refreshApex` against the *raw wired result*, not the destructured
data.

**Solution:**

```javascript
// caseList.js
import { LightningElement, wire, api } from 'lwc';
import { refreshApex } from '@salesforce/apex';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import getOpenCases from '@salesforce/apex/CaseService.getOpenCases';
import promoteToHighPriority
    from '@salesforce/apex/CaseService.promoteToHighPriority';

export default class CaseList extends LightningElement {
    @api recordId;
    _wiredCases;
    cases;
    error;

    @wire(getOpenCases, { accountId: '$recordId' })
    wiredCases(result) {
        this._wiredCases = result;
        if (result.data) {
            this.cases = result.data;
            this.error = undefined;
        } else if (result.error) {
            this.error = result.error;
        }
    }

    async handlePromote() {
        const ids = this.cases
            .filter(c => c.Priority !== 'High')
            .map(c => c.Id);
        try {
            await promoteToHighPriority({ caseIds: ids });
            await refreshApex(this._wiredCases);
            this.dispatchEvent(new ShowToastEvent({
                title: 'Updated', variant: 'success',
                message: `${ids.length} case(s) promoted.`
            }));
        } catch (e) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Update failed', variant: 'error',
                message: e.body?.message ?? e.message
            }));
        }
    }
}
```

**Why it works:** The wire function-form (rather than the
property-form `@wire(...) wiredCases;`) is critical here — it gives
us a chance to capture the *entire* result object (with `data`,
`error`, and internal cache keys) into `_wiredCases`. `refreshApex`
needs that full object to invalidate the right cache entry. If you
pass just `this.cases` (the unwrapped data), `refreshApex` throws
`TypeError: refreshApex called on a non-wired value` because the
data array has no cache identity.

---

## Example 2: `RefreshEvent` from a modal that updates a record via UI API

**Context:** A standard Account record page has a custom LWC tab
("Health Score Details") that uses `getRecord` to render fields
including a calculated `HealthScore__c`. A separate LWC quick action
opens a modal where the user inputs three slider values; on save,
the modal calls `updateRecord` on the parent Account. After the
modal closes, the Account record page should reflect the new
`HealthScore__c` without a manual refresh.

**Problem:** `updateRecord` from `lightning/uiRecordApi`
automatically notifies LDS to refresh standard-API-cached views.
What it does *not* refresh is the standard Account record page's
header fields, the highlights panel, or related components that
were rendered before the modal opened — those have already
committed to their `@wire`'d snapshot. Calling
`notifyRecordUpdateAvailable` is the documented mitigation but
it's the targeted path; the view-scoped alternative is the
`RefreshEvent` half of the RefreshView API, shipped in Spring '23.

**Solution:**

```javascript
// healthScoreModal.js
import { LightningElement, api } from 'lwc';
import { RefreshEvent } from 'lightning/refresh';
import { updateRecord } from 'lightning/uiRecordApi';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import HEALTH_FIELD
    from '@salesforce/schema/Account.HealthScore__c';

export default class HealthScoreModal extends LightningElement {
    @api recordId;
    inputs = { financial: 0, engagement: 0, risk: 0 };

    async handleSave() {
        const score = computeScore(this.inputs);
        try {
            await updateRecord({
                fields: { Id: this.recordId, [HEALTH_FIELD.fieldApiName]: score }
            });
            this.dispatchEvent(new RefreshEvent());
            this.dispatchEvent(new CustomEvent('close'));
        } catch (e) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Save failed', variant: 'error',
                message: e.body?.output?.errors?.[0]?.message ?? e.message
            }));
        }
    }
}

function computeScore({ financial, engagement, risk }) {
    return Math.max(0, Math.min(100, financial + engagement - risk));
}
```

**Why it works:** `RefreshEvent` propagates up the DOM and into the
`lightning/refresh` infrastructure, which signals every component in
the active view (record page tabs, related lists, custom components
registered via `registerRefreshHandler()`) to invalidate and re-fetch.
This is the modern replacement for the targeted-record approach;
unlike `notifyRecordUpdateAvailable`, it doesn't require the caller
to know which records changed — useful when the modal's logic might
have triggered Flow/Apex side effects that updated *other* records
too. The downside is breadth — see `gotchas.md` for the
performance implication.

---

## Anti-Pattern: Forcing wire re-run by nulling a reactive parameter

**What practitioners do:**

```javascript
async refreshHack() {
    const saved = this.filter;
    this.filter = null;
    await Promise.resolve();
    this.filter = saved;
}
```

**What goes wrong:** This pattern relies on the framework noticing
that `$filter` changed (to null and back) and re-running the wire.
In practice the LDS caching layer often **collapses** the no-op
update — Lightning's reactivity engine sees `null → 'oldValue'`
inside a single microtask and decides not to re-provision the
wire because the "effective" value didn't change. When the engine
does re-fire, it may not invalidate the cached result for the
original `filter` value, so the wire returns the same stale data.
The behavior varies by adapter and by version, which makes
debugging maddening.

Even when it does work, the component momentarily renders with
`null` data, which usually means a loading spinner flickers, a
chart rebuilds, and downstream wires that depend on the same
filter cascade through the same null state. Users see a UI
"glitch" that doesn't appear in tests but does in production.

**Correct approach:** Use the right primitive for the wire type:
- Custom Apex wire: `refreshApex(this._wiredFoo)` — exact, cheap,
  no UI glitch.
- Standard UI API wire (`getRecord`, `getRecords`,
  `getRelatedListRecords`): `RefreshEvent` (broad refresh) or
  `notifyRecordUpdateAvailable([{ recordId }])` (targeted).
- Param-driven context legitimately changed: assign the new value,
  let reactivity do its job.

If none of these fit, the architecture is wrong — typically the
LWC is trying to use a wire as a synchronous data fetch. Switch
to an imperative Apex call (`import getFoo from
'@salesforce/apex/...'; const data = await getFoo({...});`) and
manage the data shape explicitly.
