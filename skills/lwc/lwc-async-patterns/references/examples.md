# Examples — LWC Async Patterns

Two worked scenarios and one anti-pattern showing how to write
async logic in LWC that handles loading state, surfaces errors,
and parallelizes independent server calls. The examples target
real component shapes: a record-detail panel and a dashboard tile
that fetches three independent server values concurrently.

---

## Example 1: Imperative Apex with async/await — loading state via `finally`

**Context:** A `<c-account-detail>` panel renders when the user
clicks an Account row in a custom list view. The parent passes the
selected record via `@api recordId`; the panel calls
`AccountService.getAccountSummary(recordId)` imperatively (not via
`@wire`) because the panel needs explicit loading and error UI tied
to the click action.

**Problem:** A first-cut implementation either (a) forgets
`try`/`catch` so a rejected Promise silently freezes the panel on
its spinner, or (b) resets `isLoading` only in the happy path,
leaving the spinner spinning on every server error. Both end up as
"the page is frozen" support tickets.

**Solution:** `async`/`await` with `try`/`catch`/`finally`, an
`@track`-decorated `isLoading` flag flipped *before* the await and
reset *in* `finally` so both success and rejection paths clear it.

```javascript
import { LightningElement, api, track } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import getAccountSummary
    from '@salesforce/apex/AccountService.getAccountSummary';

export default class AccountDetail extends LightningElement {
    @api recordId;

    @track isLoading = false;
    @track error;
    @track summary;

    async connectedCallback() {
        await this.loadSummary();
    }

    async loadSummary() {
        this.isLoading = true;
        this.error = undefined;
        try {
            this.summary = await getAccountSummary({
                accountId: this.recordId
            });
        } catch (err) {
            // Imperative Apex errors arrive as { body: { message } },
            // not as a plain Error with a .message property.
            this.error = err.body?.message ?? 'Unable to load summary.';
            this.dispatchEvent(new ShowToastEvent({
                title: 'Could not load account',
                message: this.error,
                variant: 'error',
                mode: 'sticky'
            }));
        } finally {
            // Runs on both success AND failure paths — the spinner
            // never gets stuck because of an uncaught rejection.
            this.isLoading = false;
        }
    }
}
```

```html
<template>
    <template lwc:if={isLoading}>
        <lightning-spinner alternative-text="Loading account"></lightning-spinner>
    </template>
    <template lwc:elseif={error}>
        <c-error-banner message={error}></c-error-banner>
    </template>
    <template lwc:elseif={summary}>
        <!-- summary content -->
    </template>
</template>
```

**Why it works:** The `finally` block is the load-bearing piece —
without it, only the success path clears `isLoading`, so any server
exception (validation rule violation, FLS denial, Apex
`AuraHandledException`) leaves the spinner running forever. The
`?? 'Unable to load summary.'` fallback covers the case where the
error has no `.body.message` (network failure, CSRF token expiry,
browser offline) so the banner never renders an empty string. The
sticky toast variant keeps the message visible until the user
dismisses it; default `dismissible` would auto-clear at 5 seconds,
often before the user finishes reading a multi-sentence error.

---

## Example 2: `Promise.all` to parallelize three independent imperative calls

**Context:** A `<c-account-dashboard-tile>` shown on the Account
record page needs three pieces of data: the Account record itself,
the count of related open Cases, and a boolean indicating whether
the running user has the "View Renewal Forecast" custom permission.
All three come from separate Apex methods on different services.
The tile renders nothing until all three resolve.

**Problem:** A sequential `await x; await y; await z;` chain pays
the round-trip latency of all three calls in series — roughly 600ms
on a healthy org for three lightweight Apex calls. Worse, if any
single call rejects, the implementation often forgets to clear the
loading state for the remaining calls that already returned.

**Solution:** `Promise.all` fires all three calls in parallel and
resolves with an array of results once every Promise resolves —
elapsed time is roughly the slowest call, not the sum. For
partial-failure tolerance (render whatever returns; don't fail the
whole tile because one of three errored), `Promise.allSettled`
returns per-call status objects instead of failing fast.

```javascript
import { LightningElement, api, track } from 'lwc';
import getAccount
    from '@salesforce/apex/AccountService.getAccount';
import getOpenCaseCount
    from '@salesforce/apex/CaseService.getOpenCaseCount';
import canViewRenewalForecast
    from '@salesforce/apex/PermissionService.canViewRenewalForecast';

export default class AccountDashboardTile extends LightningElement {
    @api recordId;

    @track isLoading = false;
    @track error;
    @track account;
    @track openCaseCount = 0;
    @track canSeeForecast = false;

    async connectedCallback() {
        this.isLoading = true;
        try {
            // Fast path: all three resolve, elapsed ~= slowest call.
            const [acc, count, perm] = await Promise.all([
                getAccount({ accountId: this.recordId }),
                getOpenCaseCount({ accountId: this.recordId }),
                canViewRenewalForecast()
            ]);
            this.account = acc;
            this.openCaseCount = count;
            this.canSeeForecast = perm;
        } catch (err) {
            // Promise.all is fail-fast: the FIRST rejection aborts.
            // For per-call partial render, use Promise.allSettled
            // (see variant below).
            this.error = err.body?.message ?? 'Unable to load dashboard.';
        } finally {
            this.isLoading = false;
        }
    }
}
```

**Partial-failure variant with `Promise.allSettled`:** When the
tile should render whatever returns (e.g., show the account header
even if the case-count call failed), `allSettled` returns an array
of `{ status: 'fulfilled', value }` or `{ status: 'rejected', reason }`
objects. The handler picks results per-call.

```javascript
async connectedCallback() {
    this.isLoading = true;
    try {
        const results = await Promise.allSettled([
            getAccount({ accountId: this.recordId }),
            getOpenCaseCount({ accountId: this.recordId }),
            canViewRenewalForecast()
        ]);
        const [accRes, countRes, permRes] = results;

        if (accRes.status === 'fulfilled') {
            this.account = accRes.value;
        } else {
            this.error = accRes.reason.body?.message
                ?? 'Account load failed.';
        }

        // Soft-fail the count: render 0 with a footnote rather than
        // hiding the whole tile because the count service is down.
        this.openCaseCount = countRes.status === 'fulfilled'
            ? countRes.value
            : 0;

        // Permission failure defaults to "denied" — fail closed.
        // Never trust an unresolved permission check to grant access.
        this.canSeeForecast = permRes.status === 'fulfilled'
            && permRes.value === true;
    } finally {
        this.isLoading = false;
    }
}
```

**Why it works:** `Promise.all` is the right primitive when calls
are *independent* (no call needs another's result) — the parallel
execution wins back the round-trip latency a sequential chain would
pay. The fail-fast semantics fit when the tile is a single atomic
unit; `allSettled` is the right escape hatch when partial render is
preferable to no render. The permission result defaults to `false`
on rejection — never let an unresolved permission check accidentally
grant access.

---

## Anti-Pattern: Chained `.then().then().then()` for sequential calls

**What practitioners do — cargo-culted from Aura:**

```javascript
// WRONG — readable in Aura, but obsolete in LWC.
import { LightningElement, track } from 'lwc';
import getUser from '@salesforce/apex/UserService.getCurrentUser';
import getOrders from '@salesforce/apex/OrderService.getOrdersForUser';
import getTickets from '@salesforce/apex/TicketService.getTicketsForUser';

export default class UserDashboard extends LightningElement {
    @track user;
    @track orders;
    @track tickets;
    @track error;
    @track isLoading = false;

    connectedCallback() {
        this.isLoading = true;
        getUser()
            .then(u => {
                this.user = u;
                return getOrders({ userId: u.Id });
            })
            .then(o => {
                this.orders = o;
                return getTickets({ userId: this.user.Id });
            })
            .then(t => {
                this.tickets = t;
                this.isLoading = false;       // reset 1
            })
            .catch(e => {
                this.error = e.body?.message ?? 'Failed.';
                this.isLoading = false;       // reset 2 (duplicated)
            });
    }
}
```

**What goes wrong:** The pyramid of `.then()` callbacks recreates
the "callback hell" pattern Promises were introduced to fix in the
first place. State has to be re-captured into instance fields
between handlers (`this.user = u; return getOrders({ userId: u.Id })`)
because each `.then()` callback can't see the previous callback's
local variables. The `isLoading = false` reset is duplicated in the
success branch and the catch branch — easy to forget one. There's
no `finally`, so a future refactor that adds a third reset path
(e.g., an early return when `this.user.IsActive === false`) will
leak the spinner.

**Correct approach:** `async`/`await` linearizes the same logic
into something that reads top-to-bottom and uses `finally` for the
single-source-of-truth loading reset:

```javascript
async connectedCallback() {
    this.isLoading = true;
    try {
        const user = await getUser();
        this.user = user;
        // After this line `user.Id` is a normal local — no need to
        // stash it on `this` purely to pass it to the next call.
        const [orders, tickets] = await Promise.all([
            getOrders({ userId: user.Id }),
            getTickets({ userId: user.Id })
        ]);
        this.orders = orders;
        this.tickets = tickets;
    } catch (err) {
        this.error = err.body?.message ?? 'Failed to load dashboard.';
    } finally {
        this.isLoading = false;       // single reset point
    }
}
```

The rewrite is shorter, has one `isLoading` reset (in `finally`),
and parallelizes the last two calls — which were never truly
sequential in the original; `getTickets` only depends on `user.Id`,
not on `getOrders`'s result. The `.then()` chain hid this
opportunity by making "do work in order" look like the only shape
available.

Chained `.then()` still has legitimate uses — composing helper
utilities that return Promises, interop with third-party libraries
that don't expose an async signature, or building a Promise chain
at module scope. Inside a component method, `async`/`await` is the
modern default; LWC has supported it since the framework launched.
