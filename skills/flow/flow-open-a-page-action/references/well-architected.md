# Well-Architected Notes — Flow Open A Page Action

## Relevant Pillars

- **Security** — the action routes the browser; it does **not** grant access. Navigating a user
  to a Salesforce record still runs through that record page's sharing/CRUD/FLS enforcement, so a
  user without access lands on an insufficient-access page rather than seeing data. Treat "open a
  record" as a UX convenience, never as a data-exposure path, and be especially careful with
  external-URL targets (avoid putting session-sensitive tokens in URLs the flow builds) and with
  guest/external users in Experience Cloud.
- **Operational Excellence** — replacing a custom `NavigationMixin` LWC, a `navigateToUrl` local
  action, or a `retURL` URL hack with the declarative action removes code and fragile URL strings
  from the maintenance surface. One supported, metadata-only navigation mechanism is easier to
  read, deploy, and reason about than a bespoke component per flow — provided you delete the
  legacy redirect (and its dead variables) instead of running both.
- **Reliability** — the native action rides Salesforce upgrades, whereas hand-built URL hacks and
  finish-URL customizations are the classic "worked until the release changed the runtime URL"
  failure. Because the maturity/edition specifics of this Summer '26 action were not pinned by a
  citable official quote here, reliability also means verifying the behavior and availability in a
  real Summer '26 org before you depend on it.
- **Performance** — declarative navigation avoids shipping and rendering a custom LWC purely to
  redirect; there's nothing to load or execute beyond the action itself.

## Architectural Tradeoffs

- **Declarative action vs. custom component.** The action covers the common cases (open a record,
  open a URL) with zero code, but it can't target a specific related tab or reuse the current page
  (both open IdeaExchange requests). When navigation must be richer or reactive, a custom
  `NavigationMixin` screen component is the right tool — at the cost of code you own and test.
- **Mid-flow action vs. finish behavior.** Because Open a Page is a canvas action, you can branch
  to it or run it conditionally, unlike finish-URL/retURL customization that only fires at
  completion. The tradeoff is placement discipline: put it where the target value (e.g. a new
  record Id) is guaranteed to exist.
- **One open-location value vs. many surfaces.** A single Where to Open Page setting must behave
  acceptably across every surface the Screen Flow runs (desktop, console, mobile, Experience
  Cloud). Choosing it once and testing it everywhere is the tradeoff against per-surface tuning
  the action doesn't offer.

## Anti-Patterns

1. **Running two redirect mechanisms at once** — adding the native action but leaving the old
   custom LWC / local action / retURL in place, so they compete and the outcome is
   surface-dependent. Migrate fully and delete the legacy path.
2. **Navigation as an access grant** — assuming "open the record" means the user will see it.
   The record page enforces its own security; confirm access first.
3. **Committing on an assumed maturity/edition** — treating the action as GA and universally
   available without confirming in a Summer '26 org, when the release notes don't state a
   maturity level.

## Official Sources Used

- Salesforce Summer '26 Release Notes (release note: "Simplify the User Workflow with the Open a Page Action") — https://help.salesforce.com/s/articleView?id=release-notes.salesforce_release_notes.htm&language=en_US&release=262&type=5
- IdeaExchange — "Open a Page Flow Action - Add 'Current Page' as Where to Open Page Option" — https://ideas.salesforce.com/s/idea/a0BHp000017JjCiMAK/open-a-page-flow-action-add-current-page-as-where-to-open-page-option
- IdeaExchange — "Provision to navigate to a related tab from Open a Page action in Flow" — https://ideas.salesforce.com/s/idea/a0BHp000019OrKBMA0/provision-to-navigate-to-a-related-tab-from-open-a-page-action-in-flow
- Trailhead — Summer '26 Release Highlights module — https://trailhead.salesforce.com/content/learn/modules/summer-26-release-highlights
- Salesforce Help — Redirect Flow Users with a Local Action — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_finish_override.htm&language=en_US&type=5
- Salesforce Help — Customize a Flow URL to Control Finish Behavior (retURL) — https://help.salesforce.com/s/articleView?id=platform.flow_distribute_internal_url_retURL.htm&language=en_US&type=5
- Salesforce Help — Understanding When a Screen Flow Finishes — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_finish.htm&language=en_US&type=5
- Salesforce Help — Flow Reference — https://help.salesforce.com/s/articleView?id=platform.flow_ref.htm&language=en_US&type=5
- Lightning Web Components Developer Guide — Navigate to Pages, Records, and Lists — https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate.html
- Lightning Web Components Developer Guide — PageReference Types — https://developer.salesforce.com/docs/platform/lwc/guide/reference-page-reference-type.html
- Component Library — force:navigateToURL — https://developer.salesforce.com/docs/component-library/bundle/force:navigateToURL
