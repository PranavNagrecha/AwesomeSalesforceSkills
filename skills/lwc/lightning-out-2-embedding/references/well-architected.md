# Well-Architected Notes — Lightning Out 2.0 Embedding

## Relevant Pillars

- **Security** — the embed authenticates a real Salesforce user across origins. The frontdoor
  URL is effectively a session key: obtain the underlying access token / Session ID from an
  authenticated backend and exchange it via the UI Bridge API at runtime, never in static markup.
  The closed-shadow-DOM iframe deliberately prevents host-page JavaScript from reaching into the
  component, so treat the boundary as a trust boundary — don't try to defeat it. The client
  credentials flow is unsupported precisely because it lacks user context; use only user-context
  auth. Third-party cookies are required, which is itself a security/privacy consideration to
  disclose to users.
- **Reliability** — cross-origin embeds fail in ways an in-org LWC never does: blocked cookies,
  expired tokens, network partitions. Subscribe to all four lifecycle events
  (`lo.application.ready/error`, `lo.component.ready/error`) *before* setting `frontdoor-url`, gate
  the visible UI on the ready events, and surface `detail.message` / `detail.originalError` on
  failure. A stalled state with neither ready nor error is the telltale sign of blocked
  third-party cookies.
- **Performance Efficiency** — each embedded component loads the LWR runtime inside an iframe;
  embed only the components a page needs and keep them lightweight, since they initialize a
  Salesforce session per host page.
- **Operational Excellence** — the `app-id` and the `<script>` src are tied to your My Domain and
  the Lightning Out 2.0 App Manager. Treat the App Manager as the source of truth for both, and
  keep the allowlisted host domains and connected-app/OAuth configuration under change control.

## Architectural Tradeoffs

- **Embed vs. rebuild.** Embedding a Salesforce-owned LWC keeps business logic and security in one
  place, but couples the external app to a cross-origin dependency, third-party cookies, and the
  authenticated-only constraint. Rebuilding in the host framework removes that coupling at the
  cost of duplicating logic and losing server-side enforcement. Prefer embedding when the
  component encapsulates real Salesforce behavior.
- **Lightning Out vs. an iframe to a Salesforce page.** A plain iframe is simpler but gives you no
  typed component API, no `@api` props, and a heavier full-page surface. Lightning Out 2.0 gives a
  component-level contract with CSS-custom-property theming across the boundary.
- **Now vs. wait for guest access.** Because unauthenticated access isn't supported yet, purely
  anonymous experiences can't use Lightning Out 2.0 today; if the audience is guests, this pattern
  is premature and Experience Cloud is the current fit.

## Anti-Patterns

1. **Session in the source.** Hard-coding a `frontdoor.jsp?sid=` URL or token in static HTML leaks
   a live session to every visitor and breaks on expiry. Exchange for a frontdoor URL at runtime.
2. **Legacy Aura pattern in a 2.0 context.** Using `$Lightning.use()` / a `lightning:out` Aura app
   is the beta, which 2.0 replaces — not an equivalent.
3. **Ignoring the failure paths.** Shipping without lifecycle-event handling leaves users staring
   at a blank area when cookies or auth fail, with no diagnostic.

## Official Sources Used

- Lightning Out 2.0 Is Now Generally Available in Winter '26 (Salesforce Developer Blog) — https://developer.salesforce.com/blogs/2025/10/lightning-out-2-0-is-now-generally-available-in-winter-26
- Embed Lightning Web Components in External Apps with Lightning Out 2.0 (intro) — https://developer.salesforce.com/docs/platform/lwc/guide/lightning-out-intro.html
- Lightning Out 2.0 Architecture — https://developer.salesforce.com/docs/platform/lwc/guide/lightning-out-architecture.html — confirms the `app-id` gate is the app's creation date ("If you created a Lightning Out 2.0 app before Spring '26, this attribute isn't required"), the mixed-case-namespace `components` format, and the four `lo.*` lifecycle events (verified 2026-08-14)
- Lightning Out 2.0 Limitations — https://developer.salesforce.com/docs/platform/lwc/guide/lightning-out-limitations.html — confirms the cookie requirement has an org half as well as a browser half ("Additionally, make sure that cross-domain Salesforce session cookies are enabled in your org") (verified 2026-08-14)
- Lightning Out **(Beta)** Requirements — https://developer.salesforce.com/docs/platform/lwc/guide/lightning-out-requirements.html — this page documents the *beta*, not 2.0; confirms "Lightning Out (beta) isn't supported when Lightning Web Security is enabled" and the beta's CORS-allowlist step (verified 2026-08-14)
- The Salesforce Developer's Guide to the Spring '26 Release — https://developer.salesforce.com/blogs/2026/01/developers-guide-to-the-spring-26-release — confirms the Spring '26 Lightning Out 2.0 changes: host domains configured in the App Manager plus the Trusted Domains allowlist in Session Settings, generated code blocks including `app-id`, and complex/mixed-case namespace support (verified 2026-08-14)
- Set Up Authentication for Lightning Out 2.0 (Salesforce Help) — https://help.salesforce.com/s/articleView?id=platform.lightning_out_auth.htm&language=en_US&type=5
- Build a Lightning Out 2.0 App (Salesforce Help) — https://help.salesforce.com/s/articleView?id=platform.lightning_out_build.htm&language=en_US&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
