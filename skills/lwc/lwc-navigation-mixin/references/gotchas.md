# Gotchas — LWC NavigationMixin

Platform behaviors and edge cases that surface only after a
NavigationMixin-based component is deployed across surfaces
(LEX, Experience Cloud, mobile) or used in less common patterns.

## Gotcha 1: `state` keys without the `c__` prefix are silently stripped

**What happens:** A component dispatches a navigation with
`state: { tab: 'history', filter: 'open' }`. The platform routes
the user to the destination page, but the URL contains no `tab`
or `filter` params — they were stripped. The receiving component
sees `pageRef.state` as an empty object (or with only the framework's
own keys). No console warning is logged; the navigation appears
successful.

**When it occurs:** Any custom state key not starting with `c__`.
The platform reserves the un-prefixed namespace for its own routing
keys (e.g., `recordIds`, `filterName`, framework internals) and
strips anything else to avoid conflict.

**How to avoid:** Always prefix custom state keys with `c__`:
`state: { c__tab: 'history', c__filter: 'open' }`. The receiver
must read them with the prefix too (`pageRef.state.c__tab`).
Document the prefix in a shared constants file so the producer
and consumer can't drift.

---

## Gotcha 2: `GenerateUrl` resolves with a *relative* path, not an absolute URL

**What happens:** Code awaits `GenerateUrl` and pipes the result
directly into `navigator.clipboard.writeText(url)` so a "Copy
Link" button can produce a shareable URL. The clipboard receives
`/lightning/r/Case/0011x...AAA/view` — a relative path that's
useless when pasted into an email, Slack, or another app.

**When it occurs:** Always — `GenerateUrl` returns a path, not an
absolute URL. The platform documents this but practitioners assume
"URL" means absolute. The result silently produces shared links
that work for one user (when typed into the URL bar of an already-
logged-in tab) but fail for everyone else.

**How to avoid:** Concatenate with `window.location.origin`:

```javascript
const path = await this[NavigationMixin.GenerateUrl](pageRef);
const absolute = window.location.origin + path;
navigator.clipboard.writeText(absolute);
```

For Experience Cloud, `window.location.origin` produces the
community domain; for Lightning Experience, it produces the org's
`my.salesforce.com` domain. Both work correctly with the relative
path that `GenerateUrl` returns.

---

## Gotcha 3: `standard__namedPage` works in LEX but throws in Experience Cloud

**What happens:** A component built for LEX uses
`type: 'standard__namedPage', attributes: { pageName: 'home' }`.
When the same component (or its package) is installed into an
Experience Cloud site, navigation fails with
`PageReference not supported in this context`. Practitioners
sometimes add a try/catch and fall back to `window.location` —
which has its own problems (see `examples.md` anti-pattern).

**When it occurs:** Any cross-surface deployment. Common scenarios:
- An ISV ships an LWC that customers install on both LEX record
  pages and Experience Cloud sites.
- An internal team builds a "shared utility component" for the
  org's LEX app and later embeds it in a partner community.

**How to avoid:** Read `pageRef.type` (via
`@wire(CurrentPageReference)`) at mount time and route to the
correct PageReference variant. Or, structure the component as
two thin wrappers (`utilityForLex.js`, `utilityForExperience.js`)
that share a `utilityCore` template — each picks the right
PageReference type for its surface. For a consolidated approach,
expose a `@api siteContext` property and let the parent app pass
the surface explicitly.

---

## Gotcha 4: Navigation to a Quick Action requires `standard__quickAction` AND the action's API name with namespace

**What happens:** A component tries to launch the "New Case"
quick action via NavigationMixin:

```javascript
this[NavigationMixin.Navigate]({
    type: 'standard__quickAction',
    attributes: { apiName: 'NewCase' }
});
```

Throws `Cannot read properties of undefined`. The fix isn't
obvious from the error — `apiName` must include the object
prefix (`Account.NewCase` for an Account-side global action, or
`Global.NewCase` for a true global action). The naked action name
is silently misinterpreted.

**When it occurs:** Whenever practitioners try to launch a
namespaced quick action. Most documentation examples skip the
prefix because they assume context, which leaves the reader to
discover the requirement through trial and error.

**How to avoid:** Always include the full `Object.Action` (or
`Global.Action`) form in `apiName`. For managed-package actions,
include the package namespace too: `mynamespace__Account.MyAction`.
The cleanest pattern is a per-page reference catalog in your codebase
(a `pageRefs.js` constants module) so the apiName format is
written once and reused.

---

## Gotcha 5: Navigation triggered inside `connectedCallback` fires *before* the destination wire pipeline is warm

**What happens:** A "redirect on load" pattern fires
`NavigationMixin.Navigate` inside `connectedCallback`. The user
arrives at the destination page and sees blank wires for several
hundred milliseconds — sometimes a full second — before any data
appears. The same destination page loads instantly when reached
via a sidebar click.

**When it occurs:** `connectedCallback`-driven navigation. The
destination page mounts immediately on arrival but its wires
fire only after the route transition completes; if you trigger
the transition before the source page has fully mounted, the
destination page's adapter caches haven't yet been pre-warmed by
the Lightning data flow. The visual result is "the redirected
landing feels broken" even though everything works correctly
once data arrives.

**How to avoid:** Defer the redirect until at least one
`renderedCallback` (or one `await Promise.resolve()` after
`connectedCallback`). Better: redirect from a user-action handler
(button click) rather than `connectedCallback`. If `connectedCallback`
redirect is genuinely required (e.g., feature-flag-driven page
gating), pre-warm the destination's wires by importing the relevant
`getRecord` (or custom Apex) adapter in the source component and
issuing a no-op fetch — the platform caches the result and the
destination page picks it up instantly.
