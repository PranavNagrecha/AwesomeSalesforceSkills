# LLM Anti-Patterns — Lightning Navigation Dead-Link Handling

Common mistakes AI coding assistants make when generating navigation code.

## Anti-Pattern 1: `.catch()` as the only failure path

**What the LLM generates:**

```javascript
this[NavigationMixin.Navigate](pageRef).catch(() => toast('error'));
```

**Why it happens:** Treats Navigate like an HTTP call.

**Correct pattern:** Pre-check the target. The Navigate promise resolves successfully even when the destination renders an error page; `.catch` doesn't fire for the failures users actually hit.

**Detection hint:** Any `Navigate(...)` followed by `.catch` with no preceding pre-check on the target.

---

## Anti-Pattern 2: Generic "could not navigate" error toast

**What the LLM generates:** A single toast for any pre-check failure.

**Why it happens:** Treats all errors as fungible.

**Correct pattern:** Distinguish deleted (offer search) from no-access (offer "request access" or contact-admin) from page-retired (redirect to home). Different recovery paths for different failures.

**Detection hint:** A pre-check that catches an error and emits a single toast text regardless of error code.

---

## Anti-Pattern 3: No console-context detection

**What the LLM generates:** `NavigationMixin.Navigate` everywhere, regardless of host.

**Why it happens:** Treats console as just another Lightning page.

**Correct pattern:** Use `IsConsoleNavigation` and `openSubtab` / `focusSubtab` from `lightning/platformWorkspaceApi` when in console. Otherwise subtab navigation opens a new primary tab.

**Detection hint:** Code that runs in service-console-likely contexts (case detail, lead detail) but never imports from `lightning/platformWorkspaceApi`.

---

## Anti-Pattern 4: `window.location.assign` as the fallback

**What the LLM generates:**

```javascript
try { Navigate(...) } catch { window.location.assign(`/r/${id}/view`); }
```

**Why it happens:** Treats Lightning navigation as exchangeable with browser navigation.

**Correct pattern:** Direct URL navigation bypasses Lightning's routing, breaks deep-link state, and produces a full page reload. The fallback should be another `Navigate` call to a known-good destination, not a window.location escape hatch.

**Detection hint:** Any `window.location.assign`, `window.location.href = `, or `window.open` adjacent to a NavigationMixin call.

---

## Anti-Pattern 5: Pre-check disabled in production "for performance"

**What the LLM generates:** A toggle that skips the `getRecord` wire when a feature flag is off.

**Why it happens:** Treats the wire as expensive overhead.

**Correct pattern:** `getRecord` is cached in the UI API; the marginal cost of the pre-check is negligible compared to the user-experience cost of a dead landing. Always pre-check.

**Detection hint:** Conditional logic around the pre-check wire whose disabled-branch goes straight to Navigate.
