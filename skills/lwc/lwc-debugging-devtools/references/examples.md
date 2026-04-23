# Examples — LWC Debugging DevTools

## Example 1: A `@wire` Adapter That Isn't Emitting

**Context:** A developer wires `getRecord` to show an Account's fields on a custom tab. The component shows no data. No errors are visible in the console.

**Problem:** Without a tooling-first diagnosis, the team guesses: is it permissions? A bad FieldReference? A wrong recordId? Each guess burns an hour.

**Solution — step by step:**

1. Enable Debug Mode for the acting user: Setup → Debug Mode → Enable. Confirm the persistent "Debug Mode" badge is visible.
2. Hard-refresh the affected page (Cmd/Ctrl+Shift+R). Open DevTools → Sources. Search for the bundle filename (e.g. `accountSummary.js`). Confirm the source is un-minified and readable.
3. Place a breakpoint on the first executable line of the wire handler:

   ```js
   @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
   handleRecord({ data, error }) {
       // <-- breakpoint here
       if (data) { this.account = data; }
       else if (error) { this.error = error; }
   }
   ```

4. Reproduce by reloading the page. If the breakpoint never fires, the adapter was never activated — the reactive `$recordId` is `undefined`. Inspect the component in the Lightning Component Inspector and read the `@api` `recordId` value. If it is indeed undefined, the parent or page binding is the root cause, not the wire.
5. If the breakpoint does fire but only with `{ data: undefined, error: undefined }`, that is the normal first emission. Keep the breakpoint and watch for a second emission with real data or an error.
6. In parallel, open the Network panel and filter requests by `/ui-api/`. Reload. You should see a `GET /services/data/vXX.X/ui-api/records/<id>?fields=...` request. A missing request confirms the adapter was never activated. A 4xx response (commonly 400 with "Invalid field") surfaces the true cause — often an invalid FieldReference import.

**Why it works:** This path distinguishes "wire never activated" from "wire activated and returned nothing useful" from "wire errored silently." Those three root causes have three different fixes, and pure `console.log` cannot distinguish them.

---

## Example 2: Blank in Prod, Works in Dev — Silent Render Failure

**Context:** A component renders correctly in a developer sandbox, but in production it shows a blank region on the record page.

**Problem:** The console has no visible error. The component's own `errorCallback` in the parent swallowed the throw, and LWS wrapped the logged error into a Proxy that the console printed as `{}`.

**Solution:**

1. Confirm Debug Mode is enabled **for the production user** — not assumed from the sandbox session. This is the single biggest miss: developers forget that Debug Mode is per user, per org, and that it was never toggled in production.
2. Hard-refresh. Open DevTools → Sources. Click the "Pause on caught exceptions" checkbox (the pause icon with the hex, then the "caught" checkbox).
3. Reproduce. The debugger pauses at the original throw site, typically in the child component.
4. In the Scope panel, inspect `this`. It appears empty because LWS wraps `this.template` and some data as Proxies. Use the DevTools console while paused:

   ```js
   // Does NOT work — prints Proxy handle
   console.log(this.record);

   // Works — materializes into a plain JSON tree
   console.log(JSON.parse(JSON.stringify(this.record)));

   // For structured data without functions or circular refs
   console.log(structuredClone(this.record));
   ```

5. With the real error now visible (e.g., "Cannot read properties of undefined reading 'Name'"), open the Lightning Component Inspector and navigate the component tree to the failing child. Read its `@api` props — you will typically see a prop that is populated in sandbox (because the test record has the field) but missing in production (because the prod record is older or a different record type).

**Why it works:** The combination of Debug Mode (readable stacks) + Pause on caught exceptions (catches framework-swallowed throws) + JSON-unwrapped logging (defeats LWS Proxy opacity) + Inspector (finds which component in the tree is actually failing) turns a silent blank render into a concrete, fixable bug.

---

## Anti-Pattern: Leaving Debug Mode On Org-Wide "Because It Was Useful Once"

**What practitioners do:** After a productive debugging session, a developer leaves Debug Mode enabled for many users — or enables it for a generic user that service agents share — reasoning "we might need it again soon."

**What goes wrong:**

- End users see noticeably slower page loads because the org serves un-minified bundles.
- Page-load analytics, Real User Monitoring dashboards, and Performance Assistant metrics are all skewed downward for those users.
- Support tickets claiming "the app is slow this week" multiply, and the team chases a non-existent performance regression.
- In Experience Cloud sites, the effect is worse because those pages target unauthenticated or lightly authenticated traffic.

**Correct approach:** Enable Debug Mode only for the user who is actively debugging, keep a note in the investigation log, and disable it as the final step of the debugging workflow. Treat it like turning off a feature flag — not like a permanent setting.
