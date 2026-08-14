# Gotchas — LWC Locker → LWS Migration

Subtle traps when flipping the Locker → LWS switch in a real org. Each gotcha lists what happens, when it occurs, and how to reproduce or avoid it.

---

## 1. `typeof SecureElement` and `instanceof SecureWindow` silently steer code into a fallback path

**What happens:** under LWS, `SecureElement` and `SecureWindow` are not defined globals. Locker-era guards like `typeof SecureElement !== 'undefined'` simply evaluate to `false` and the code runs the `else` branch — which may not be the path the original author intended for "real DOM" callers. There is **no error** to surface this.

**When it occurs:** any code that probed the runtime to adapt behaviour. Common in: signature pads, custom canvas widgets, in-house drag-and-drop, anything that did coordinate math.

**Reproduction:**
1. Add `console.log('using locker path')` inside the `if (typeof SecureElement !== 'undefined')` branch.
2. Run under Locker — log fires.
3. Flip LWS — log never fires; the `else` path runs unconditionally.

**How to avoid:** **delete the probe entirely** before flipping. Locker-only branches are dead under LWS; leaving them in place is a refactoring landmine. Static-grep for `SecureElement`, `SecureWindow`, `SecureDocument`, `SecureObject` and remove every reference.

---

## 2. Functions passed across namespaces silently become `undefined` (or throw `TypeError`)

**What happens:** when `acme__ParentComponent` passes `@api callback={someFunction}` to `widgets__ChildComponent` (different namespace), LWS realm semantics mean the function does not transfer. The child sees `undefined`, or — if the function reference partially survives via property descriptor lookup — gets `TypeError: callback is not a function`.

**When it occurs:** cross-namespace component composition where the parent passes a method as an `@api` property. Single-namespace orgs do not see this because both components share a realm.

**Reproduction:**
1. In a managed package or 2GP namespace `widgets__`, expose an `@api formatter` property of type function.
2. Consume from a custom namespace `acme__` that passes `formatter={this.fmt}`.
3. Under Locker — works.
4. Flip LWS — child receives `undefined` for `this.formatter`.

**How to avoid:** never pass functions across namespaces. Use one of:
- Pass already-formatted strings/primitives and let the child be a dumb renderer.
- Emit `CustomEvent`s with structured-cloneable `detail` payloads; let the parent transform on the way back.
- Use Lightning Message Service for cross-namespace coordination — its payload semantics are explicitly cloneable.

---

## 3. Deep-clone-on-input shims (`JSON.parse(JSON.stringify(x))`) become harmful, not redundant

**What happens:** Locker-era code often deep-cloned data on the way into a third-party library to "escape the proxy." Under LWS the proxy is gone, so the clone is no longer needed — but if removed thoughtlessly, it can also strip:

- `Date` objects → become strings,
- `Map`/`Set` → become `{}`,
- functions inside config objects (`tooltip.callbacks.label`) → silently dropped,
- class instances → become plain objects without their prototype.

The library now misbehaves in subtle ways (missing tooltips, broken date formatting, tooltip callbacks never fire) **after** the LWS flip even though the change was supposed to be neutral.

**When it occurs:** charting libraries, PDF generators, table libraries, anywhere config objects contain functions or non-JSON types.

**Reproduction:** see Example 1 — Chart.js `tooltip.callbacks.label` becomes a no-op after the flip if the deep-clone hack is left in.

**How to avoid:** when removing a Locker-era shim, **also remove** any deep-clone of its inputs. Pass through references directly. Re-test the library's full API surface (tooltips, callbacks, custom serializers) in a sandbox.

---

## 4. The org switch is not "live-reload safe" — in-flight user sessions see a mixed state

**What happens:** the **Use Lightning Web Security for Lightning web components** toggle takes effect on the **next page load** for each user. Users in mid-session continue to run Locker until they navigate or refresh. If your release plan assumes "everyone is on LWS at 9:00am" and triggers a downstream comms event tied to that time, some users will still be on Locker when they receive the comms.

**When it occurs:** any production cutover during business hours. Most pronounced in 24/7 contact-centre tenants where users rarely refresh.

**Reproduction:**
1. In a sandbox, log in as User A and open a Lightning page.
2. As System Administrator (User B), toggle LWS on.
3. User A's tab continues to run Locker until refresh.

**How to avoid:** schedule the flip in a low-traffic window. Force-refresh dashboards by deploying any LWC change in the same release (which invalidates the LWC cache for all users on next page render). Communicate that users should hard-refresh after the change.

---

## 5. `lwc-recipes` and Salesforce sample code may show LWS-only or Locker-only patterns without labelling

**What happens:** the public `trailheadapps/lwc-recipes` repository targets the current default runtime (LWS for Spring '23+ orgs). Some examples now use APIs that **fail under Locker** (e.g., `OffscreenCanvas`, advanced `IntersectionObserver` options, certain `Element.attachInternals()` patterns). If you copy a recipe into an org that is still on Locker, it will fail.

**When it occurs:** during the migration window itself, when developers grab sample code "to validate the new approach" in a Locker-still-on environment.

**Reproduction:** clone `lwc-recipes` master, deploy any recipe that uses `Element.attachInternals()` to a Locker-on sandbox, observe failure.

**How to avoid:** keep migration sandbox(es) explicitly tagged "LWS-on" and "Locker-on" and run tests in the right one. Do not assume sample code is runtime-portable. When validating a recipe pattern, validate it on **both** runtimes during the migration window.

---

## 6. Aura LWS toggle lags LWC LWS — Aura components stay on Aura Locker

**What happens:** flipping **Lightning Web Security for Lightning web components** does not flip Lightning Web Security for Aura. Aura code continues to run under Aura Locker (a distinct sandbox with its own quirks). Teams that flip LWC LWS and then debug a regression in an Aura component looking for "LWS issues" waste time — the Aura component is still on Locker.

**When it occurs:** orgs with mixed Aura + LWC custom code, especially where an Aura wrapper hosts an LWC.

**Reproduction:** check `Setup → Session Settings`. The LWC toggle and the Aura toggle are separate checkboxes. Toggling one does not toggle the other.

**How to avoid:** when triaging post-flip regressions, identify whether the failing component is Aura or LWC before assuming runtime-related cause. The distinction matters for which Locker / LWS doc applies.

---

## 7. `force:hasRecordId` / `force:hasSObjectName` Aura wrappers are unaffected by the LWC LWS flip

**What happens:** these are **Aura interfaces**. They are implemented by Aura components, not LWCs. The LWC LWS flip does not change their behaviour, does not retire them, and does not alter how an Aura wrapper forwards `recordId` to a child LWC.

**When it occurs:** when teams hear "LWS migration" and assume it is a sweeping modernization that retires legacy Aura adapters. It is not — it is a runtime-sandbox change for LWC code.

**How to avoid:** retire `force:hasRecordId`-only Aura wrappers as a **separate** clean-up after the LWS flip stabilises. Place the LWC directly on the record page; it receives `recordId` via `@api`. Keep this change separable for rollback clarity.

---

## 8. `eval` / `new Function` are still a problem — LWS is not "looser CSP"

**What happens:** developers (and LLMs) read "Locker blocked `eval`, LWS does not have the SecureWindow proxy" and conclude that `eval` is now permitted. It is not — Lightning Experience's content security policy disallows `unsafe-eval` for hosted code regardless of which sandbox runs the LWC.

**When it occurs:** when an LLM is asked to "remove Locker workarounds" and reaches for `eval` because the original library shipped a "non-Locker" build that used `eval`.

**Reproduction:** ship a component that calls `eval('1+1')` — fails under both Locker and LWS due to CSP.

**How to avoid:** treat `eval` and `new Function` as off-limits unconditionally. The LWS migration is not a license to relax this. See `references/llm-anti-patterns.md` for the full anti-pattern.

---

## 9. Summer '26: LWS blocks `data:` URIs on `HTMLAnchorElement.prototype.href`

**What happens:** Summer '26 added a batch of new LWS distortions. Per the Summer '26 developer release guide: "`HTMLAnchorElement.prototype.href` now **blocks the `data:` URI scheme**. If you trigger client-side downloads by setting an anchor's `href` to a `data:` URL, that stops working." The classic LWC export recipe — build `'data:text/csv;charset=utf-8,' + encodeURIComponent(csv)`, assign it to an anchor, set `download`, `click()` — stops downloading. It usually fails **quietly**: no exception, just no file.

This is a distortion, not a Locker-vs-LWS difference: the idiom worked under Locker *and* under LWS until Summer '26. Do not diagnose it as an incomplete migration.

**When it occurs:** any org on Summer '26 with a client-side CSV / JSON / PDF / vCard export built on the anchor + `data:` URL pattern. Very common — it was the widely-published LWC recipe for years. Whether a bundle pinned to an older `apiVersion` in its `.js-meta.xml` is exempt is **not** documented on the release-guide page — do not assume either way, and confirm against the Distortion Viewer in a sandbox on the target release. (Note the LWS distortion set is not the same mechanism as the Locker API-version selector, which is a Locker-only org setting.)

**Reproduction:**
1. In a Summer '26 org, render an anchor and set `a.href = 'data:text/csv,' + encodeURIComponent('a,b')`, `a.download = 'x.csv'`, then `a.click()`.
2. No download starts; the console is clean.
3. Inspect `a.href` in DevTools to confirm the `data:` value was rejected. (The release guide documents that the download stops working, not the exact read-back value — check the Distortion Viewer for the API's precise distorted behaviour rather than assuming it.)

**How to avoid:** use the blob pattern, which the release guide calls "the supported pattern anyway — build a blob in JavaScript and use a `blob:` object URL (origin-bound, and revoked after use)." Code is in `references/llm-anti-patterns.md` Anti-Pattern 9.

The same release distorted more APIs the migration test plan should cover: "Other new distortions include `Element.getAttribute`, `innerHTML/outerHTML` getters, `MutationObserver.observe`, the `IndexedDB` factory, `Promise.then/catch/finally`, and more — with matching ESLint rules." Run `@locker/eslint-config-locker` (`npm update` it — the rules ship per release) and check the [LWS Distortion Viewer](https://developer.salesforce.com/tools/lws-distortion-viewer) for the current behaviour of a specific API. The Viewer is the live source of truth; a distortion list pinned in any document, including this one, decays every release.
