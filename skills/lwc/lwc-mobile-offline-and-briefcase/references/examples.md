# Examples — LWC Mobile Offline and Briefcase

Concrete patterns for the five most common offline-LWC scenarios. Each example shows the LWC code, the Briefcase rule (where applicable), and the failure mode if you skip a step.

---

## Example 1 — Offline-aware imperative Apex with explicit fallback

**Scenario:** A "Quote Summary" LWC needs an aggregated total across child line items. The current implementation calls an `@AuraEnabled` Apex method and breaks offline.

**Before — silently breaks offline:**

```javascript
import { LightningElement, api, wire } from 'lwc';
import getQuoteTotal from '@salesforce/apex/QuoteController.getQuoteTotal';

export default class QuoteSummary extends LightningElement {
    @api recordId;
    total;
    error;

    connectedCallback() {
        getQuoteTotal({ quoteId: this.recordId })
            .then((result) => { this.total = result; })
            .catch((err) => { this.error = err; });   // also fires on offline
    }
}
```

When the device is offline, the `getQuoteTotal` promise rejects with a network error and the component shows a generic error state. The user has no idea this is an offline-only failure.

**After — pre-compute server-side, read with LDS:**

Add a roll-up summary field `Total_Amount__c` on the `Quote` object (or a calculated formula if the math is simple). Then read it through LDS, which is offline-aware:

```javascript
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
import TOTAL_AMOUNT_FIELD from '@salesforce/schema/Quote.Total_Amount__c';

export default class QuoteSummary extends LightningElement {
    @api recordId;

    @wire(getRecord, { recordId: '$recordId', fields: [TOTAL_AMOUNT_FIELD] })
    record;

    get total() {
        return this.record?.data?.fields?.Total_Amount__c?.value;
    }

    get isOfflineMissing() {
        // getRecord returns an error envelope when the record is not in
        // any offline cache layer. Branch on the error and avoid a
        // generic "something failed" message.
        return !!this.record?.error && !this.record?.data;
    }
}
```

```html
<template>
    <template lwc:if={total}>
        <p>Quote total: {total}</p>
    </template>
    <template lwc:elseif={isOfflineMissing}>
        <p class="empty">This quote isn't available offline. Reconnect to view.</p>
    </template>
</template>
```

**Why this works:** the field-on-record is part of the record payload that LDS caches. When the device is offline and the parent Quote was either Briefcase-primed or LDS-cached from a recent view, the total is available with no network call. When the record is genuinely unavailable, the component shows an explicit empty state instead of a generic error.

---

## Example 2 — Briefcase priming rule for a Service team

**Scenario:** Field-based service reps need offline access to their assigned open Cases, the parent Account, the Account's primary Contact, and the most recent 5 CaseComments. They are offline for full work shifts, often without cellular signal.

**Briefcase definition (Setup → Briefcase Builder → New):**

```yaml
Briefcase Name: Service_Field_Reps
Description: Open cases + parent context for road-warrior service reps
Audience:
  Permission Set: Service_Field_Rep_Briefcase_Audience
Priming Rules:
  - Root Object: Case
    Filter: |
      OwnerId = $User.Id
      AND Status NOT IN ('Closed', 'Resolved')
      AND CreatedDate = LAST_N_DAYS:90
    Related Objects:
      - Object: Account
        From relationship: Case.AccountId
      - Object: Contact
        From relationship: Case.ContactId
      - Object: CaseComment
        From relationship: Case.Id (parent → child)
        Filter: ORDER BY CreatedDate DESC
        Limit: 5
```

**Records-per-user estimate:**

| Object | Average per user | Notes |
|---|---|---|
| Case | 35 open per rep | Within 400-record soft limit |
| Account | ~20 (deduplicated by parent) | Many cases share an Account |
| Contact | ~25 | One per case + a few shared |
| CaseComment | 35 x 5 = 175 | Below per-object soft limit |

Total per user: ~255 records primed. Comfortably within published Briefcase-per-user guidance.

**Audience setup:** assign `Service_Field_Rep_Briefcase_Audience` permission set to the relevant users. The same user could belong to multiple Briefcases — the device receives the union.

**Failure modes if this is skipped:** without the rule, reps see only Cases they happened to open in the last few hours (LDS recently-viewed). A rep starting a shift after lunch, with no recent Salesforce visits, sees an empty case list when offline.

**What this rule does NOT prime:**

- Knowledge articles (`KnowledgeArticleVersion`) — not on the supported object list. Use the Knowledge Mobile feature separately.
- File attachments on Cases (`ContentDocument`) — only the *pointer* is cached, not the binary content.
- Custom picklist values on Case — these come through LDS metadata cache and are not Briefcase-primed.
- Record types — see Gotcha 2 in `references/gotchas.md`.

---

## Example 3 — Sync conflict UI for offline edits

**Scenario:** A "Visit Log" LWC lets reps record visit outcomes offline. Multiple reps can edit the same Account record (rare, but it happens with team accounts). Default last-write-wins risks silent overwrite of dispatcher updates.

**Pattern: snapshot-based conflict detection.**

When the form opens, capture `LastModifiedDate` of the record. On save, send it as part of the payload. A custom Apex method compares the snapshot to the current `LastModifiedDate`; if newer, it routes to a conflict screen instead of overwriting.

```javascript
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
import saveVisitLog from '@salesforce/apex/VisitLogController.saveWithConflictCheck';
import LAST_MODIFIED_DATE from '@salesforce/schema/Account.LastModifiedDate';
import VISIT_NOTES from '@salesforce/schema/Account.Last_Visit_Notes__c';

export default class VisitLog extends LightningElement {
    @api recordId;
    snapshotTimestamp;
    notes = '';
    pendingSync = false;
    conflict;

    @wire(getRecord, { recordId: '$recordId',
                       fields: [LAST_MODIFIED_DATE, VISIT_NOTES] })
    wiredRecord({ data }) {
        if (data) {
            this.snapshotTimestamp = data.fields.LastModifiedDate.value;
            this.notes = data.fields.Last_Visit_Notes__c.value || '';
        }
    }

    handleNotesChange(e) { this.notes = e.target.value; }

    async handleSave() {
        try {
            const result = await saveVisitLog({
                recordId: this.recordId,
                snapshot: this.snapshotTimestamp,
                notes: this.notes
            });
            if (result.conflict) {
                this.conflict = result;     // route to conflict UI
            }
        } catch (err) {
            // Network error while online = real problem.
            // Network error while offline = action queued automatically by LDS
            // for the LDS path, but imperative Apex does NOT auto-queue.
            // Surface it as "saved locally — will retry when online."
            if (this.isOfflineError(err)) {
                this.pendingSync = true;
                // Persist a local draft so the user can re-submit on reconnect.
                this.persistDraft();
            } else {
                throw err;
            }
        }
    }

    isOfflineError(err) {
        return navigator.onLine === false;
    }

    persistDraft() {
        try {
            localStorage.setItem(
                'visitLogDraft_' + this.recordId,
                JSON.stringify({ notes: this.notes, snapshot: this.snapshotTimestamp })
            );
        } catch { /* storage full; degrade silently */ }
    }
}
```

```html
<template>
    <textarea value={notes} onchange={handleNotesChange}></textarea>

    <template lwc:if={pendingSync}>
        <p class="queued">Saved locally. We'll retry when you're back online.</p>
    </template>

    <template lwc:if={conflict}>
        <c-visit-log-conflict-resolver
            current-server-value={conflict.serverNotes}
            your-value={notes}
            onpickserver={handlePickServer}
            onpickyours={handlePickYours}>
        </c-visit-log-conflict-resolver>
    </template>
</template>
```

**Server side (sketch):**

```apex
@AuraEnabled
public static SaveResult saveWithConflictCheck(
    Id recordId, Datetime snapshot, String notes) {

    Account a = [SELECT Id, LastModifiedDate, Last_Visit_Notes__c
                 FROM Account WHERE Id = :recordId];
    if (a.LastModifiedDate > snapshot) {
        return new SaveResult(true, a.Last_Visit_Notes__c);   // conflict
    }
    a.Last_Visit_Notes__c = notes;
    update a;
    return new SaveResult(false, null);
}
```

**Important caveat:** because this uses imperative Apex, only the *online* path is conflict-aware. The *offline* path persists a draft locally and re-submits on reconnect. To get conflict detection on offline writes too, the conflict check has to run server-side at sync time — which means using `lightning-record-edit-form` and adding a server-side `before update` trigger that compares `LastModifiedDate` against a custom field. This is non-trivial; reserve it for high-stakes records.

---

## Example 4 — Persisting a draft form across app backgrounding

**Scenario:** A long-form intake LWC takes 5+ minutes of typing. The user backgrounds the Salesforce Mobile App to look something up, comes back, and the form is empty.

**Why it happens:** by default LWC component instances are torn down when the user navigates away or the app is backgrounded long enough. LDS caches *records*, not unsubmitted form drafts. The draft lives only in component memory unless persisted.

**Pattern: persist to local storage (browser/WebView level), restore in `connectedCallback`.**

```javascript
import { LightningElement, api } from 'lwc';

const DRAFT_KEY_PREFIX = 'visitDraft_';

export default class VisitIntake extends LightningElement {
    @api recordId;
    visitNotes = '';
    visitOutcome = '';

    connectedCallback() {
        const raw = this.readDraft();
        if (raw) {
            try {
                const draft = JSON.parse(raw);
                this.visitNotes = draft.visitNotes ?? '';
                this.visitOutcome = draft.visitOutcome ?? '';
            } catch { /* malformed; ignore */ }
        }
    }

    get draftKey() { return DRAFT_KEY_PREFIX + this.recordId; }

    readDraft() {
        try { return localStorage.getItem(this.draftKey); }
        catch { return null; }
    }

    handleChange(e) {
        const field = e.target.dataset.field;
        this[field] = e.target.value;
        this.persistDraft();
    }

    persistDraft() {
        const draft = {
            visitNotes: this.visitNotes,
            visitOutcome: this.visitOutcome,
            savedAt: new Date().toISOString()
        };
        try {
            localStorage.setItem(this.draftKey, JSON.stringify(draft));
        } catch { /* storage full; degrade silently */ }
    }

    async handleSubmit() {
        // Submit through LDS so offline submission auto-queues.
        // ... call updateRecord or use lightning-record-edit-form ...
        try { localStorage.removeItem(this.draftKey); } catch { /* ignore */ }
    }
}
```

**Caveats:**

- `localStorage` is per-WebView origin. The Salesforce Mobile App's WebView preserves it across backgrounding but can clear it on app reinstall, on iOS storage pressure, or when the user signs out.
- Quotas vary by platform but are bounded (commonly 5–10 MB). Store only the form fields, not large attachments.
- Treat persisted drafts as *user data*. If the user signs out, the LWC may not run on sign-out — clear stale keys defensively in `connectedCallback` if the stored draft's owner differs from the current user.
- Persisted drafts are not encrypted. For PII or regulated data, this pattern is unsuitable — design a server-side draft endpoint with proper field-level security instead.

---

## Example 5 — Form-factor + offline detection for graceful degradation

**Scenario:** A "complex chart" LWC works on desktop and tablet but is unusable on phones, AND the chart depends on imperative Apex that fails offline.

```javascript
import { LightningElement, api } from 'lwc';
import FORM_FACTOR from '@salesforce/client/formFactor';
import getChartData from '@salesforce/apex/ChartController.getChartData';

export default class ChartTile extends LightningElement {
    @api recordId;
    chartData;
    networkError = false;

    formFactor = FORM_FACTOR;   // 'Large' | 'Medium' | 'Small'

    connectedCallback() {
        if (this.formFactor === 'Small') return;  // skip the work entirely
        this.loadChart();
    }

    async loadChart() {
        try {
            this.chartData = await getChartData({ recordId: this.recordId });
        } catch (err) {
            // navigator.onLine is a hint, not a guarantee.
            // Use it only to choose the message, never to make correctness decisions.
            this.networkError = !navigator.onLine;
            if (!this.networkError) throw err;
        }
    }

    get showSmallScreenMessage() { return this.formFactor === 'Small'; }
    get showOfflineMessage() { return this.networkError; }
    get showChart() { return !!this.chartData; }
}
```

```html
<template>
    <template lwc:if={showChart}>
        <c-chart-renderer data={chartData}></c-chart-renderer>
    </template>
    <template lwc:elseif={showSmallScreenMessage}>
        <p>Chart available on desktop and tablet. Open this record in a browser to view.</p>
    </template>
    <template lwc:elseif={showOfflineMessage}>
        <p>Chart requires a connection. Reconnect to load.</p>
    </template>
</template>
```

**Important — `@salesforce/client/formFactor` is not an offline indicator.** It returns one of `'Large'`, `'Medium'`, `'Small'` based on the rendering surface. A phone with full LTE returns `'Small'`; a desktop with no network returns `'Large'`. To detect connectivity, use `navigator.onLine` for UX purposes only, and treat the actual network failure as the source of truth for correctness. `navigator.onLine` lies about captive-portal scenarios and can be `true` even when no Salesforce host is reachable.
