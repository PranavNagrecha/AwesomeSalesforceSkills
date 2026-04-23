# LLM Anti-Patterns — LWC Debugging DevTools

Common mistakes AI coding assistants make when advising on runtime LWC debugging.

## Anti-Pattern 1: Recommending `alert()` for Debugging

**What the LLM generates:**

```js
renderedCallback() {
    alert('rendered: ' + this.recordId); // "so you can see what's happening"
}
```

**Why it happens:** Classic web-tutorial training data over-uses `alert()` as a debugging primitive. For LWC, it is actively harmful — it blocks the main thread, interrupts framework lifecycle hooks, and gives no structured output.

**Correct pattern:**

```js
renderedCallback() {
    // Prefer a breakpoint in Sources, or a conditional log-point.
    // If you must log, unwrap under LWS:
    console.log('rendered', JSON.parse(JSON.stringify({ id: this.recordId })));
}
```

**Detection hint:** grep for `alert(` in LWC `.js` files — there is almost no legitimate use in a Lightning component.

---

## Anti-Pattern 2: Suggesting "Disable LWS to Make Debugging Easier"

**What the LLM generates:** "If your logs show Proxy handles, you can disable Lightning Web Security in Session Settings to make objects log normally."

**Why it happens:** The LLM conflates Locker Service (where LWS is a replacement) with a debug flag. Disabling LWS is a security regression, is not a supported per-investigation toggle, and does not belong in a debugging recommendation.

**Correct pattern:** Leave LWS enabled. Unwrap the value at the log site:

```js
console.log('account', JSON.parse(JSON.stringify(this.account)));
// or
console.log('account', structuredClone(this.account));
```

**Detection hint:** grep for "disable LWS", "turn off Lightning Web Security", or "Session Settings" appearing next to debugging advice.

---

## Anti-Pattern 3: `console.log(this.record)` Expecting Fields to Print

**What the LLM generates:**

```js
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
wiredRecord({ data }) {
    this.record = data;
    console.log('record fields:', this.record); // expects {Name, Industry, ...}
}
```

**Why it happens:** The LLM reasons about `console.log` as if it were running in a vanilla browser without membrane Proxies. Under LWS, `this.record` prints as a Proxy handle.

**Correct pattern:**

```js
console.log('record fields:', JSON.parse(JSON.stringify(this.record)));
// or for specific fields
import NAME_FIELD from '@salesforce/schema/Account.Name';
import { getFieldValue } from 'lightning/uiRecordApi';
console.log('Name:', getFieldValue(this.record, NAME_FIELD));
```

**Detection hint:** Any `console.log(this.` or `console.log(record` on a platform-wrapped object without `JSON.parse(JSON.stringify(...))` or `structuredClone`.

---

## Anti-Pattern 4: "Enable Debug Mode in Production Settings"

**What the LLM generates:** "To debug, go to Setup → Production Settings → Enable Debug Mode." (Or a variant pointing to "Lightning Components → Debug Mode" as an org-wide switch.)

**Why it happens:** The LLM hallucinates a setup path. Debug Mode in the modern Salesforce UI is a per-user setting, reached via Setup → Debug Mode or each user's Debug Mode page. There is no "Production Settings" area that toggles it, and enabling it at the org scope is not the right mental model.

**Correct pattern:** Guide the user to Setup → Debug Mode, select the specific user, and enable. Emphasize that this is per user and should be disabled after the investigation.

**Detection hint:** Any instruction that places Debug Mode under "Production Settings," "Performance Settings," or any non-Debug-Mode path; any phrasing that implies it is org-wide.

---

## Anti-Pattern 5: Leaving `debugger;` Statements in Committed Code

**What the LLM generates:**

```js
connectedCallback() {
    debugger; // "so you can inspect state on load"
    this.loadData();
}
```

...and then fails to tell the developer to remove the statement before commit, or even commits it itself in a proposed patch.

**Why it happens:** The LLM treats `debugger;` as equivalent to a persistent breakpoint. In committed code it causes every developer (and every CI browser, and every end user with DevTools open) to pause on that line.

**Correct pattern:** Use `debugger;` only during active investigation. Remove before commit. For persistent breakpoints, use the Sources panel. Consider a lint rule (`no-debugger`) to prevent accidental commits.

**Detection hint:** grep for `debugger;` in LWC source; flag any instance in code paths that will be deployed.
