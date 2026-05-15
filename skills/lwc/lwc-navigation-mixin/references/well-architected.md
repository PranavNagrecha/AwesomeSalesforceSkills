# Well-Architected Notes — LWC NavigationMixin

## Relevant Pillars

Navigation is a cross-surface concern (LEX, Experience Cloud,
mobile) and `NavigationMixin` is the only correct abstraction over
those surfaces. Three pillars carry the architectural weight here.

- **Adaptable (Composability)** — `NavigationMixin` is the
  surface-agnostic API. Components that use it work identically
  in LEX and Experience Cloud (assuming the right PageReference
  variant); components that hand-roll URLs become surface-specific
  and resist reuse. The composability win compounds as the LWC
  suite grows: a navigation helper module written against
  `NavigationMixin` can be dropped into any context, where a URL-
  hardcoded version has to be re-engineered for each.
- **Operational Excellence** — `NavigationMixin`-based code
  participates in Salesforce's audit trails, click-tracking,
  CSP enforcement, and "Recently Viewed" tracking. Code that
  bypasses the mixin (via `window.location` or hand-built URLs)
  silently breaks all four. Ops teams chasing "why isn't this
  click being tracked" often trace the issue back to
  navigation code that skipped the mixin.
- **User Experience** — The mixin honors browser conventions
  (ctrl-click, right-click, middle-click, keyboard nav) when used
  with `<a href={...}>` patterns; it breaks them when used as a
  programmatic-only handler. Component authors who don't think
  about the difference produce UX that "works" but feels broken
  to power users.

Pillars that *don't* carry significant weight here: Reliability
(navigation rarely fails in a way that requires retry/circuit-
breaker patterns), Scalability (no backend load implications),
Security (Salesforce's link wrapping handles it, as long as you
use the mixin).

## Architectural Tradeoffs

The defining tradeoff is **`Navigate` vs `GenerateUrl` + anchor**:

| Dimension | `Navigate(pageRef)` | `GenerateUrl(pageRef)` + `<a href>` |
|---|---|---|
| Browser interactions | Click only | ctrl/cmd-click, middle-click, right-click → "open in new tab", keyboard Enter |
| Code complexity | One method call | Async URL generation + DOM anchor |
| Routing semantics | Triggers SPA route (no reload) | Default `<a>` does same on click; new tab on modifier |
| Best for | "Save and redirect" workflows | List rows, link cards, copy-link affordances |

The naive read says "Navigate is simpler, use it." The right read
is "use `Navigate` when the action is a programmatic redirect
triggered by something other than a click" — e.g., after a save,
during a workflow, on a timeout. Use `GenerateUrl` + anchor
whenever the user's gesture is naturally a "click on a link."
Mixing the two consistently is the mark of a polished LWC.

A second tradeoff is **surface awareness**: should a single LWC
detect its surface (LEX vs Experience Cloud vs mobile) and pick
the right PageReference type at runtime, or should there be one
component per surface?

| Approach | Pros | Cons |
|---|---|---|
| One LWC, surface detection | DRY; one place to maintain. | Bloat — code paths for all surfaces ship to every surface. Hard to test. |
| One LWC per surface | Lean per-surface bundles. Surface-specific UX easy. | Duplication; risk of drift between variants. |

The right call depends on how the surfaces diverge. For pure
navigation logic (where the divergence is just `standard__` vs
`comm__`), one LWC with a constant lookup table works well:

```javascript
const NAMED_PAGE = {
    lex: 'standard__namedPage',
    experience: 'comm__namedPage'
};
```

For deeper UX divergence (different layouts, different state
handling on each surface), splitting wins.

A third tradeoff is **state-passing breadth**. The `state` object
in a PageReference flows through the URL — which means it's
shareable, bookmarkable, *and* leaks into browser history, logs,
and analytics. Sensitive context (auth tokens, PII identifiers
beyond the standard recordId) should never live in `state`. Use
a server-side session store or a custom Lightning Message Service
channel for sensitive cross-component state.

## Anti-Patterns

1. **`window.location` for navigation.** Bypasses routing, breaks
   across surfaces, may be blocked by CSP. See the `examples.md`
   anti-pattern for the full failure profile.
2. **Hand-building Salesforce URLs.** Surface-fragile, version-
   fragile, and breaks the platform's link tracking. Always use
   `GenerateUrl`.
3. **Triggering navigation from `connectedCallback`.** The
   destination page's wires haven't warmed; users see a
   broken-looking blank state. See `gotchas.md` § 5.
4. **Un-prefixed `state` keys.** Silently stripped. Always `c__`
   for custom keys.
5. **Sensitive data in `state`.** Treat `state` as public, logged,
   indexable. Anything an attacker shouldn't see should not be in
   the URL.

## Official Sources Used

- LWC Reference — `lightning/navigation` and `NavigationMixin`:
  https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-navigation.html
- LWC Reference — PageReference types:
  https://developer.salesforce.com/docs/platform/lwc/guide/reference-page-reference-type.html
- LWC Reference — `CurrentPageReference`:
  https://developer.salesforce.com/docs/platform/lwc/guide/reference-current-page-reference.html
- Experience Cloud Developer Guide — `comm__` PageReference variants:
  https://developer.salesforce.com/docs/atlas.en-us.exp_cloud_lwr.meta/exp_cloud_lwr/components_config_for_communities_navigation.htm
- Salesforce Well-Architected — Adaptable (Composable):
  https://architect.salesforce.com/well-architected/adaptable/composable
