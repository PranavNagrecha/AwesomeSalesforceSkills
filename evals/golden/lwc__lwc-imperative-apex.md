# Eval: lwc/lwc-imperative-apex

- **Skill under test:** `skills/lwc/lwc-imperative-apex/SKILL.md`
- **Priority:** P0
- **Cases:** 3
- **Last verified:** 2026-04-16
- **Related templates:** `templates/lwc/patterns/imperativeApexPattern.js`, `templates/apex/SecurityUtils.cls`
- **Related decision trees:** None directly.

## Pass criteria

Imperative Apex in LWC must: use `@AuraEnabled(cacheable=false)` for writes,
explicit loading + error state, `ShowToastEvent` on failure, CRUD/FLS on
the Apex side (never relying on the client), and unit tests that mock
`@salesforce/apex/…` imports.

## Case 1 — Button-click write flow

**Priority:** P0

**User prompt:**

> "I need a button on the Opportunity record page that re-runs a
> quote-to-cash calculation on the server. The Apex method is
> `QuoteService.runRecalc(opportunityId)` and it does DML."

**Expected output MUST include:**

- `@AuraEnabled(cacheable=false)` on Apex (writes can never be cacheable).
- Imperative call with `async/await` — not `.then()`-chain only.
- `loading` property disables the button while in-flight.
- Success and error both surfaced via `ShowToastEvent`; error also stored
  locally for inline display.
- Use `notifyRecordUpdateAvailable` after success so other wires refresh.
- Jest test mocks `@salesforce/apex/QuoteService.runRecalc` and asserts
  loading → success path.

**Expected output MUST NOT include:**

- Fire-and-forget (`runRecalc({...})` with no `await`).
- Swallowing exceptions (`catch {}`).
- Using `console.log` for errors as the only handling.
- Missing the loading state.

**Rubric (0–5):**

- **Correctness:** `async/await` + loading + error handling.
- **Completeness:** Toast + inline error + wire-refresh.
- **Bulk safety:** Apex side handles the operation atomically.
- **Security:** Apex enforces FLS/CRUD via `SecurityUtils` or `WITH USER_MODE`.
- **Citation of official docs:** Links to `@AuraEnabled` + `ShowToastEvent` docs.

**Reference answer (gold):**

```javascript
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { notifyRecordUpdateAvailable } from 'lightning/uiRecordApi';
import runRecalc from '@salesforce/apex/QuoteService.runRecalc';

export default class OpportunityRecalc extends LightningElement {
    @api recordId;
    loading = false;
    errorMessage;

    get disabled() { return this.loading; }

    async handleClick() {
        this.loading = true;
        this.errorMessage = undefined;
        try {
            await runRecalc({ opportunityId: this.recordId });
            await notifyRecordUpdateAvailable([{ recordId: this.recordId }]);
            this.dispatchEvent(new ShowToastEvent({
                title: 'Totals recalculated',
                variant: 'success'
            }));
        } catch (e) {
            this.errorMessage = this.toMessage(e);
            this.dispatchEvent(new ShowToastEvent({
                title: 'Recalc failed',
                message: this.errorMessage,
                variant: 'error'
            }));
        } finally {
            this.loading = false;
        }
    }

    toMessage(error) {
        if (!error) return 'Unknown error';
        if (Array.isArray(error.body)) return error.body.map((e) => e.message).join(', ');
        return (error.body && error.body.message) || error.message || String(error);
    }
}
```

Jest (sketch):

```javascript
jest.mock('@salesforce/apex/QuoteService.runRecalc', () => ({
    default: jest.fn()
}), { virtual: true });
import runRecalc from '@salesforce/apex/QuoteService.runRecalc';

it('calls apex and fires success toast', async () => {
    runRecalc.mockResolvedValue(undefined);
    const el = createElement('c-opportunity-recalc', { is: OpportunityRecalc });
    el.recordId = '006000000000001';
    document.body.appendChild(el);
    el.shadowRoot.querySelector('lightning-button').click();
    await Promise.resolve(); // microtask
    expect(runRecalc).toHaveBeenCalledWith({ opportunityId: '006000000000001' });
});
```

## Case 2 — Cacheable read where wire adapters won't work

**Priority:** P0

**User prompt:**

> "I need to show a rolled-up aggregate from 5 different objects on one
> component. LDS wire adapters don't cover it — can I use imperative Apex
> with caching?"

**Expected output MUST include:**

- Yes: `@AuraEnabled(cacheable=true)` on a read-only Apex method that
  returns a DTO.
- Prefer `@wire` syntax over imperative when cacheable — it gives you
  reactive updates + consistent cache semantics.
- If parameters come from user input, use imperative; if reactive to
  recordId, use `@wire`.
- Cache invalidation: call `refreshApex(this.wiredResult)` after any DML
  that affects the aggregate.
- Apex MUST still enforce sharing + FLS.

**Expected output MUST NOT include:**

- `cacheable=true` combined with DML inside the method (illegal).
- Using imperative + no caching when `@wire` would work.
- Manual localStorage caching in the JS layer (breaks LDS semantics).

**Rubric (0–5):**

- **Correctness:** Explains when wire vs imperative for cacheable reads.
- **Completeness:** Cache invalidation addressed.
- **Bulk safety:** Apex aggregates via one SOQL per object.
- **Security:** `WITH USER_MODE` on Apex.
- **Citation of official docs:** Links to Lightning Data Service cache + `refreshApex`.

**Reference answer (gold):**

"Yes — `@AuraEnabled(cacheable=true)` with a DTO. Structure it as a wire unless the inputs are user-typed:

```apex
public with sharing class DashboardAggregate {
    public class Result {
        @AuraEnabled public Integer openCases;
        @AuraEnabled public Integer openOpps;
        @AuraEnabled public Decimal pipeline;
    }
    @AuraEnabled(cacheable=true)
    public static Result forAccount(Id accountId) {
        Result r = new Result();
        r.openCases = [SELECT COUNT() FROM Case WHERE AccountId = :accountId AND IsClosed = false WITH USER_MODE];
        r.openOpps  = [SELECT COUNT() FROM Opportunity WHERE AccountId = :accountId AND IsClosed = false WITH USER_MODE];
        r.pipeline  = [SELECT SUM(Amount) total FROM Opportunity WHERE AccountId = :accountId AND IsClosed = false WITH USER_MODE][0].get('total') == null
                      ? 0
                      : (Decimal) [SELECT SUM(Amount) total FROM Opportunity WHERE AccountId = :accountId AND IsClosed = false WITH USER_MODE][0].get('total');
        return r;
    }
}
```

LWC side:

```javascript
@wire(forAccount, { accountId: '$recordId' })
aggregate;
```

When some other component in the app does DML on Case/Opportunity,
call `refreshApex(this.aggregate)` (by keeping the wired result) or
rely on `notifyRecordUpdateAvailable` for LDS-backed wires.

Rule: `cacheable=true` means pure read. Any DML inside = runtime error. Never combine."

## Case 3 — Error UX for a long-running imperative call

**Priority:** P0

**User prompt:**

> "My imperative Apex call takes 8-15 seconds. Users click the button and
> either wait with no feedback or double-click and double-submit. What
> should the UX look like?"

**Expected output MUST include:**

- Disable the button + show `lightning-spinner` while `loading = true`.
- `debounce` the button handler OR guard with `if (this.loading) return;`.
- Consider moving the work to async (Queueable) and returning immediately
  if it's NOT blocking on the user's input — poll a status record from the
  LWC.
- Timeout the UX: after 15s show a different message ("This is taking
  longer than usual — keep waiting or check back later").
- Error toast with retry affordance.
- Log the failed call via `ApplicationLogger` on Apex side for debugging.

**Expected output MUST NOT include:**

- A hidden `setTimeout` cancellation that never cleans up.
- Leaving the button enabled.
- Throwing away the error.

**Rubric (0–5):**

- **Correctness:** Prevents double-submit.
- **Completeness:** Loading + guard + UX degrade at 15s + retry.
- **Bulk safety:** N/A — score 5.
- **Security:** Apex-side logging sanitizes PII.
- **Citation of official docs:** Links to `lightning-spinner` + LWC performance best practices.

**Reference answer (gold):**

"Three things:

1. **Prevent double-submit** with a guard + disabled attribute:

```javascript
async handleClick() {
    if (this.loading) return;
    this.loading = true;
    const slowWarning = setTimeout(() => { this.slow = true; }, 15000);
    try { await runSomething(...); }
    catch (e) { this.showError(e); }
    finally {
        clearTimeout(slowWarning);
        this.slow = false;
        this.loading = false;
    }
}
```

Template:

```html
<lightning-button label="Run" disabled={loading} onclick={handleClick}></lightning-button>
<template if:true={loading}>
    <lightning-spinner size="small"></lightning-spinner>
    <template if:true={slow}>
        <p>This is taking longer than usual — you can wait or come back later.</p>
    </template>
</template>
```

2. **Reconsider synchronous**. If the work doesn't need the user's immediate
   response, enqueue a Queueable and have `runSomething` return a job Id.
   The LWC polls a `Job_Status__c` record via `@wire(getRecord, ...)` —
   reactive, no spinning, and the page survives refresh.

3. **Error UX with retry**. Show the toast + an inline retry button that
   re-invokes `handleClick`. Log the error context on the Apex side via
   `ApplicationLogger.error(...)` with the request Id so Support can
   correlate the user report."
