# LLM Anti-Patterns — LWC Async Patterns

Common mistakes AI coding assistants make with async/await in LWC.

## Anti-Pattern 1: Imperative Apex with no try/catch

**What the LLM generates:**

```
async handleClick() {
    this.data = await getData();
    this.isLoading = false;
}
```

**Why it happens:** Model treats `await` as a drop-in for `.then()` and forgets rejection handling.

**Correct pattern:**

```
A rejected promise throws. Without try/catch the loading state never
clears, the user sees a spinner forever, and the browser logs an
unhandled rejection — silent in production.

async handleClick() {
    this.isLoading = true;
    try {
        this.data = await getData();
    } catch (err) {
        this.error = err.body?.message ?? 'Unknown error';
    } finally {
        this.isLoading = false;
    }
}
```

**Detection hint:** `await` on a symbol imported from `@salesforce/apex/...` with no surrounding try/catch.

---

## Anti-Pattern 2: Swallowing errors in catch

**What the LLM generates:**

```
try {
    this.data = await getData();
} catch (e) {
    console.error(e);
}
```

**Why it happens:** Model adds a catch to satisfy lint, but no user feedback.

**Correct pattern:**

```
console.error is invisible to users. Surface errors via a sticky toast
or an inline banner bound to this.error:

catch (e) {
    this.error = e.body?.message ?? 'Unknown error';
    this.dispatchEvent(new ShowToastEvent({
        title: 'Something went wrong',
        message: this.error,
        variant: 'error',
        mode: 'sticky'
    }));
}

Silent failures are a top source of Salesforce LWC support tickets.
```

**Detection hint:** `catch` block containing only `console.*` calls with no user-visible side effect.

---

## Anti-Pattern 3: Missing finally — loading state stuck

**What the LLM generates:**

```
async load() {
    this.isLoading = true;
    try {
        this.data = await getData();
        this.isLoading = false;
    } catch (e) {
        this.error = e;
    }
}
```

**Why it happens:** Model resets the flag inside `try`, forgetting the catch path.

**Correct pattern:**

```
If getData rejects, isLoading stays true forever. Reset in finally so
both success AND failure paths clear the spinner:

try {
    this.data = await getData();
} catch (e) {
    this.error = e;
} finally {
    this.isLoading = false;
}
```

**Detection hint:** `this.isLoading = true` followed by an `await` without a `finally { this.isLoading = false }`.

---

## Anti-Pattern 4: No stale-response guard on search/filter

**What the LLM generates:**

```
async handleFilterChange(e) {
    this.results = await searchApex({ q: e.target.value });
}
```

**Why it happens:** Model doesn't consider overlapping calls.

**Correct pattern:**

```
User types "abc" then "abcd" — both calls are in flight. If "abc"
resolves after "abcd", stale results overwrite fresh ones. Guard with
a request-id counter or AbortController:

async handleFilterChange(e) {
    const reqId = ++this.latestReqId;
    const results = await searchApex({ q: e.target.value });
    if (reqId !== this.latestReqId) return;  // stale
    this.results = results;
}

Better: debounce (300ms) + AbortController to cancel prior fetch.
```

**Detection hint:** Handler bound to `onchange`/`oninput` making a server call with no debounce, no cancellation, no request-id check.

---

## Anti-Pattern 5: No cleanup on disconnect

**What the LLM generates:**

```
connectedCallback() {
    this.timer = setInterval(() => this.refresh(), 5000);
}
// no disconnectedCallback
```

**Why it happens:** Model knows `connectedCallback` but forgets the teardown partner.

**Correct pattern:**

```
When the component unmounts (navigation, tab close, record-page
rerender), pending timers, subscriptions, and in-flight fetches must
be cleaned up — otherwise setInterval fires against a dead component,
memory leaks, setState-on-unmounted warnings.

LWC has NO componentWillUnmount. Use disconnectedCallback:

disconnectedCallback() {
    clearInterval(this.timer);
    this.controller?.abort();         // cancel in-flight fetch
    unsubscribe(this.subscription);   // empApi / CDC
}
```

**Detection hint:** `connectedCallback` starts a timer / subscription / AbortController, but the component has no `disconnectedCallback`.
