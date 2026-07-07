# Examples — Lightning Out 2.0 Embedding

All code below is illustrative scaffolding authored from the official Lightning Out 2.0
developer guides. Replace `MY_DOMAIN`, the `app-id`, component names, and endpoints with
your own. Lightning Out 2.0 is GA as of Winter '26 and embeds **custom LWCs only** into
**external, non-Salesforce** apps.

## Example 1: Minimal host-page embed (plain JavaScript)

**Context:** an external marketing site (`https://acme.example.com`) needs to show a custom
`c-order-status` LWC to a signed-in Salesforce user.

**Problem:** the component must run in the Salesforce security context and authenticate, but
the host page is on a different origin and has no Salesforce session of its own.

**Solution:**

```html
<!-- index.html on the external host page -->
<!-- Script element is copied verbatim from the Lightning Out 2.0 App Manager -->
<script src="https://MY_DOMAIN.my.salesforce.com/lightning/lightning.out.latest/index.iife.prod.js"></script>

<lightning-out-application
    id="loApp"
    app-id="1Usfi200000006TCAQ"
    components="c-order-status">
</lightning-out-application>

<c-order-status record-id="500XXXXXXXXXXXXXXX"></c-order-status>

<script>
  // frontdoor-url is set at runtime — never hard-coded (see Example 2)
</script>
```

**Why it works:** the `<script>` loads the Lightning Out 2.0 library on the host page (not from
inside an LWC, which LWS would block). `<lightning-out-application>` is UI-less; it declares the
`app-id` and the `components` to embed, while the actual `<c-order-status>` tag marks where the
component renders inside its closed-shadow-DOM iframe.

---

## Example 2: Runtime frontdoor-URL exchange + lifecycle handling

**Context:** the same page must authenticate the current user and only reveal the component
once the session and component are ready.

**Problem:** a raw Session ID can't go in the markup, and a blank component area gives users no
signal when auth or cross-origin cookies fail.

**Solution:**

```javascript
// bootstrapLightningOut.js — runs on the external host page
async function bootstrapLightningOut() {
  const loApp = document.getElementById('loApp');

  // Subscribe to lifecycle events BEFORE setting frontdoor-url
  document.addEventListener('lo.application.ready', () => {
    document.getElementById('spinner').hidden = true;
  });
  document.addEventListener('lo.application.error', (e) => {
    showError('Session failed', e.detail?.message, e.detail?.originalError);
  });
  document.addEventListener('lo.component.ready', () => {
    document.getElementById('c-order-status-wrap').hidden = false;
  });
  document.addEventListener('lo.component.error', (e) => {
    showError('Component failed to render', e.detail?.message, e.detail?.originalError);
  });

  // 1. Get a Salesforce access token / Session ID for the current user
  //    (from your own authenticated backend — never expose it in static HTML)
  const { accessToken } = await fetch('/api/sf/token').then((r) => r.json());

  // 2. Exchange the token for a frontdoor URL via the UI Bridge API
  const frontdoorUrl = await fetch('/api/sf/frontdoor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ accessToken }),
  }).then((r) => r.json()).then((d) => d.frontdoorUrl);

  // 3. Set frontdoor-url so Lightning Out establishes the session
  loApp.setAttribute('frontdoor-url', frontdoorUrl);
}

bootstrapLightningOut();
```

**Why it works:** the token→frontdoor exchange happens server-side at runtime, so no secret
lands in static markup. Listening for all four `lo.*` events before assigning `frontdoor-url`
means no ready/error signal is missed. A stalled state (no ready, no error) is the classic
sign of blocked third-party cookies.

---

## Example 3: Styling across the iframe boundary

**Context:** the host page's brand color should reach the embedded component without the host
JavaScript reaching into the component.

**Problem:** the component lives in a closed shadow DOM inside an iframe, so host JS can't
mutate its internals.

**Solution:**

```html
<c-order-status
    record-id="500XXXXXXXXXXXXXXX"
    style="--brand-accent: #7a1fa2;">
</c-order-status>
```

```css
/* inside the LWC's CSS */
.badge {
  background: var(--brand-accent, #1b5297);
}
```

**Why it works:** CSS custom properties declared on the component tag cross into the embedded
component as styling hooks, which is the supported channel for theming — unlike direct DOM
access, which the closed shadow DOM deliberately prevents.

---

## Anti-Pattern: hard-coding a Session ID in the frontdoor URL

**What practitioners do:** paste a `frontdoor.jsp?sid=<session id>` URL, or a raw access token,
directly into the `frontdoor-url` attribute in the page's static HTML.

**What goes wrong:** the credential ships to every visitor's browser, is trivially exfiltrated,
and expires — turning the embed into an intermittent, insecure integration. Anyone viewing
source obtains a live session.

**Correct approach:** obtain the token from an authenticated backend at runtime, exchange it for
a frontdoor URL through the UI Bridge API, and assign `frontdoor-url` via JavaScript. Let the
OAuth flow handle users with no active session; never use the client credentials flow (it has
no user context and is unsupported).

---

## Anti-Pattern: loading the library from inside an LWC

**What practitioners do:** try to append the `lightning.out` `<script>` from a component's JS
(e.g. via `loadScript` or `document.createElement('script')`).

**What goes wrong:** Lightning Web Security blocks HTML `<script>` insertion, so the library
never loads and the embed silently does nothing.

**Correct approach:** put the App-Manager-provided `<script>` tag directly in the external host
page's HTML.
</content>
