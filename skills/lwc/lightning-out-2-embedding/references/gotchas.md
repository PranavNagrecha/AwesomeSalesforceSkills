# Gotchas — Lightning Out 2.0 Embedding

Non-obvious Salesforce platform behaviors that cause real production problems when embedding
custom LWCs in external apps with Lightning Out 2.0.

## Gotcha 1: Blocked third-party cookies fail silently

**What happens:** the component area stays blank and no obvious error appears; the session
never establishes.

**When it occurs:** the browser (or a corporate policy, or the user's privacy settings) blocks
third-party / cross-origin cookies. Lightning Out 2.0 *requires* them, and each end user must
have them enabled.

**How to avoid:** test with third-party cookies both enabled and blocked; treat a stalled state
(no `lo.application.ready`, no `lo.application.error`) as the signature of blocked cookies and
render an actionable message telling the user to enable them.

---

## Gotcha 2: The library can't be loaded from inside an LWC

**What happens:** an attempt to inject the `lightning.out` script from component JavaScript does
nothing and the embed never initializes.

**When it occurs:** you try to append the `<script>` via `loadScript`, `document.createElement`,
or any DOM insertion inside a Lightning web component. Lightning Web Security **blocks HTML
`<script>` element insertion**.

**How to avoid:** place the App-Manager-provided `<script>` tag directly in the external host
page's HTML. The library is a host-page concern, not a component concern.

---

## Gotcha 3: Aura components and standard components won't embed

**What happens:** the embed shows nothing, or you can't add the component to the app at all.

**When it occurs:** the component you're trying to embed is an Aura component (custom or
standard) or a standard base component referenced directly. Lightning Out 2.0 embeds **only
custom LWCs**.

**How to avoid:** rewrite Aura components as LWCs, and compose any standard base components
*inside* your own custom LWC rather than embedding them directly.

---

## Gotcha 4: `lightning/navigation` doesn't work in the embedded context

**What happens:** clicks that should navigate do nothing, or throw, inside the embedded
component.

**When it occurs:** the embedded LWC imports and calls the `lightning/navigation` service.
Page navigation for embedded components is **not supported** in Lightning Out 2.0.

**How to avoid:** remove `lightning/navigation` usage from components you intend to embed;
handle any navigation on the host page instead (e.g. the host app routes, or the component
emits an event the host listens for).

---

## Gotcha 5: The client credentials flow can't back the session

**What happens:** a server-to-server integration authenticates fine to the API but the
Lightning Out 2.0 session never establishes.

**When it occurs:** you try to authorize with the OAuth 2.0 **client credentials flow**. It's
explicitly unsupported because it carries **no user context**, and Lightning Out 2.0 needs a
real user.

**How to avoid:** obtain a user access token / Session ID and exchange it via the UI Bridge API
for a frontdoor URL; rely on the automatic OAuth authorization flow when there's no active
session.

---

## Gotcha 6: Hard-coded frontdoor URLs leak sessions and expire

**What happens:** the embed works briefly, then breaks; meanwhile any visitor can read a live
session out of the page source.

**When it occurs:** a `frontdoor.jsp?sid=...` URL or a raw token is pasted into the
`frontdoor-url` attribute in static HTML.

**How to avoid:** always set `frontdoor-url` at runtime from a value fetched through your own
authenticated backend and the UI Bridge API — never in checked-in or served static markup.

---

## Gotcha 7: The cookie requirement has an org half as well as a browser half

**What happens:** every developer's browser is configured correctly, third-party cookies are
allowed, and the session still never establishes — so the team keeps re-testing the browser
setting that isn't the problem.

**When it occurs:** the org-side setting is off. The limitations page states both halves:
"Lightning Out 2.0 requires third-party, or cross-origin, cookies. End users must enable
third-party cookies in their browser. Additionally, make sure that cross-domain Salesforce
session cookies are enabled in your org."

**How to avoid:** treat this as two separate preconditions with two separate owners — the end
user (browser third-party cookies) and the admin (cross-domain Salesforce session cookies in
the org). Verify the org half once, up front, before debugging any individual browser. Pair it
with the domain registration: since Spring '26 the host domain goes in the Lightning Out 2.0
App Manager **and** in the Trusted Domains allowlist under Session Settings.

---

## Gotcha 8: The beta and Lightning Web Security can't coexist

**What happens:** an org enables Lightning Web Security as part of a routine hardening or
Locker-migration project, and every remaining Lightning Out (beta) embed stops working.

**When it occurs:** any org still on `$Lightning.use()` when LWS is switched on. The beta
requirements page is explicit: "Lightning Out (beta) isn't supported when Lightning Web
Security is enabled. We recommend Lightning Web Security as the preferred security architecture
for most orgs, but you must use Lightning Locker instead if you use Lightning Out (beta)."

**How to avoid:** treat the LWS enablement date — not a beta retirement date — as the deadline
for migrating to Lightning Out 2.0. Inventory `$Lightning.use(` across host apps before the LWS
change, and note the inversion when you migrate: the beta *requires* Locker, while under 2.0 it
is LWS that blocks loading the library from inside a component (Gotcha 2).
