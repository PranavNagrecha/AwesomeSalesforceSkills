# Lightning Out 2.0 Embed — Host-Page Template

A copy-paste starting point for embedding a **custom LWC** in an external, non-Salesforce app
with Lightning Out 2.0 (GA Winter '26). Replace every `<<PLACEHOLDER>>`. Do not commit real
tokens or frontdoor URLs — they are fetched at runtime.

Validate the result with:

```bash
python3 ../scripts/check_lightning_out_2_embedding.py --host-dir .
```

---

## 1. Prerequisites (do these first)

- [ ] Component to embed is a **custom LWC** (not Aura, not a standard component used directly).
- [ ] A Lightning Out 2.0 app exists in the **Lightning Out 2.0 App Manager**; copy its
      generated `<script>` element and 18-digit `app-id`.
- [ ] The host domain `<<HOST_ORIGIN>>` is allowlisted for cross-origin use.
- [ ] Target users are **authenticated Salesforce users**, and their browsers allow
      **third-party cookies** (required).
- [ ] A backend endpoint can return a Salesforce access token / Session ID for the current
      user, and exchange it for a frontdoor URL via the **UI Bridge API**. Never expose the
      token in static content.

---

## 2. Host-page HTML

```html
<!-- <script> element copied verbatim from the Lightning Out 2.0 App Manager -->
<script src="https://<<MY_DOMAIN>>.my.salesforce.com/lightning/lightning.out.latest/index.iife.prod.js"></script>

<div id="lo-spinner">Loading…</div>
<div id="lo-error" hidden></div>

<lightning-out-application
    id="loApp"
    app-id="<<18_DIGIT_APP_ID>>"
    components="<<c-my-lwc>>">
</lightning-out-application>

<div id="lo-wrap" hidden>
  <!-- CSS custom properties on the tag cross into the embedded component -->
  <<c-my-lwc>> style="--brand-accent: #1b5297;"></<<c-my-lwc>>>
</div>
```

---

## 3. Runtime bootstrap (host-page JavaScript)

```javascript
async function bootstrapLightningOut() {
  const loApp = document.getElementById('loApp');
  const spinner = document.getElementById('lo-spinner');
  const wrap = document.getElementById('lo-wrap');
  const errorBox = document.getElementById('lo-error');

  const fail = (title, detail) => {
    spinner.hidden = true;
    errorBox.hidden = false;
    errorBox.textContent = `${title}: ${detail?.message ?? 'unknown error'}`;
    console.error(title, detail?.originalError ?? detail);
  };

  // Register ALL lifecycle listeners before setting frontdoor-url.
  document.addEventListener('lo.application.ready', () => { spinner.hidden = true; });
  document.addEventListener('lo.application.error', (e) => fail('Session failed', e.detail));
  document.addEventListener('lo.component.ready', () => { wrap.hidden = false; });
  document.addEventListener('lo.component.error', (e) => fail('Component failed', e.detail));

  try {
    // 1. Get a user token from YOUR authenticated backend (never in static markup).
    const { accessToken } = await fetch('<<TOKEN_ENDPOINT>>').then((r) => r.json());

    // 2. Exchange it for a frontdoor URL via the UI Bridge API (server-side proxy).
    const { frontdoorUrl } = await fetch('<<FRONTDOOR_ENDPOINT>>', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accessToken }),
    }).then((r) => r.json());

    // 3. Assign frontdoor-url at runtime to establish the session.
    loApp.setAttribute('frontdoor-url', frontdoorUrl);
  } catch (err) {
    fail('Bootstrap failed', { message: String(err), originalError: err });
  }

  // If neither ready nor error fires within a few seconds, third-party cookies
  // are likely blocked — surface an actionable message.
  setTimeout(() => {
    if (!spinner.hidden) {
      fail('Timed out establishing session',
           { message: 'Enable third-party cookies in your browser and retry.' });
    }
  }, 8000);
}

bootstrapLightningOut();
```

---

## 4. Do-not-do list

- [ ] No `frontdoor.jsp?sid=` / `access_token=` hard-coded in served HTML or JS.
- [ ] No `$Lightning.use()` / Aura `lightning:out` (that is the beta 2.0 replaces).
- [ ] No loading the library via `loadScript` / `createElement('script')` from inside an LWC.
- [ ] No `lightning/navigation` / `NavigationMixin` in the embedded component.
- [ ] No OAuth `client_credentials` flow (no user context; unsupported).

---

## 5. Sign-off notes

- Channels/browsers tested (with third-party cookies enabled **and** blocked):
- Token/frontdoor exchange endpoint owner:
- App-Manager app-id and My Domain of record:
