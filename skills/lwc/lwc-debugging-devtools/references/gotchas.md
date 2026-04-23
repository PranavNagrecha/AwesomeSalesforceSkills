# Gotchas — LWC Debugging DevTools

Non-obvious Salesforce platform behaviors that cause real production debugging misfires.

## Gotcha 1: Debug Mode Is Per User, Not Per Org

**What happens:** A developer enables Debug Mode for themselves, verifies the component works, and closes the ticket — but end users keep hitting the original bug because they are still served the minified bundle and, for them, nothing has changed.

**When it occurs:** Any time debugging spans multiple users, or the bug is "only reproducing for certain users" and the developer assumes the toggle is org-wide.

**How to avoid:** Treat Debug Mode as a per-user flag. Enable it for yourself to investigate. If the bug affects a specific end user, reproduce under your own account first; only enable it for the end user if you must, and disable it again afterward.

---

## Gotcha 2: `console.log(this)` Under LWS Logs a Proxy Handle

**What happens:** Logging `this`, `this.record`, `this.account`, or any LDS-wrapped object prints something that looks empty — `Proxy {}`, `{}`, or the object name with no fields. It feels like the data never arrived.

**When it occurs:** Any org with Lightning Web Security enabled (the default for new orgs since Winter '23) logging a platform-wrapped object.

**How to avoid:** Force a plain JSON copy: `console.log(JSON.parse(JSON.stringify(obj)))`. For cloneable shapes, `structuredClone(obj)` also works. If the object contains functions, `Map`, `Set`, or circular refs, log individual fields rather than the whole object.

---

## Gotcha 3: Source Maps Only Load in Debug Mode — Breakpoints in Minified Code Are Useless

**What happens:** A developer sets a breakpoint in the Sources panel and it either never hits or hits at the wrong line. Stepping lands in framework wrapper code that looks nothing like the original component.

**When it occurs:** Any time the developer forgot to enable Debug Mode (or hit it from an incognito window where the toggle does not apply to that session's user).

**How to avoid:** Confirm Debug Mode is on for the acting user before setting breakpoints. Verify by opening Sources and searching for the bundle name — readable code means Debug Mode is active.

---

## Gotcha 4: The Lightning Component Inspector Is Chromium-Only

**What happens:** A developer on Firefox opens DevTools, finds no "Lightning" panel, and cannot inspect the component tree.

**When it occurs:** Any Firefox-based debugging session.

**How to avoid:** Switch to Chrome, Edge, Brave, or another Chromium-based browser. Firefox has no parity extension.

---

## Gotcha 5: Breakpoints Inside `renderedCallback` Fire Many Times

**What happens:** A breakpoint inside `renderedCallback` pauses on every render cycle — sometimes dozens of times during a single interaction — making it impossible to step through cleanly.

**When it occurs:** Any `renderedCallback`, especially in components that receive reactive prop updates or host child components whose state changes frequently.

**How to avoid:** Right-click the breakpoint → "Edit breakpoint" → add a condition like `this.recordId === '001...'` or use a log-point that writes to the console without pausing. For first-render-only debugging, guard with `if (!this._renderedOnce)` plus a flag.

---

## Gotcha 6: LWS Sandboxes `window` — Not Every Browser Debugging Trick Works

**What happens:** Snippets like `Object.defineProperty(window, 'myVar', ...)`, attaching a debug helper to `window`, or grabbing a global reference the way you would in a vanilla web app either silently do nothing or throw `Access check failed`.

**When it occurs:** Under LWS, module-scoped globals are distorted per-module. `window` is not a single shared surface the way it is in non-LWS contexts.

**How to avoid:** Use `debugger;` statements and DevTools Scope inspection rather than reaching for `window`. When you need a value across reloads, store it in `sessionStorage` from inside the component and read it in the next session.

---

## Gotcha 7: Experience Cloud CSP Is Stricter Than LEX

**What happens:** A component works in Lightning Experience but breaks silently in an Experience Cloud site — a third-party script fails to load, an inline style is dropped, a `connect-src` request is blocked.

**When it occurs:** Experience Cloud sites enforce a Content Security Policy that can be stricter than the LEX defaults, and the defaults vary by site template and by whether Strict CSP is enabled.

**How to avoid:** Check the Network panel for `CSP` violations and the Console for `Refused to load` messages. Review the Experience Cloud site's CSP settings under Workspaces → Administration → Security & Privacy before blaming the component. When debugging, reproduce on the actual Experience Cloud URL, not just in LEX preview.
