# LLM Anti-Patterns — Lightning Out 2.0 Embedding

Common mistakes AI coding assistants make when generating or advising on Lightning Out 2.0
embeds. These help the consuming agent self-check its own output. The dominant failure is
reproducing the **legacy Aura Lightning Out (beta)** pattern, which is far more common in
training data than the Winter '26 GA 2.0 API.

## Anti-Pattern 1: Emitting the legacy `$Lightning.use()` Aura bootstrap

**What the LLM generates:** a `$Lightning.use('c:myApp', callback, ...)` call plus an Aura
`lightning:out` dependency app, and calls it Lightning Out.

**Why it happens:** the Aura-based beta dominated documentation and blog posts for years, so the
model reaches for it by default.

**Correct pattern:**

```html
<script src="https://MY_DOMAIN.my.salesforce.com/lightning/lightning.out.latest/index.iife.prod.js"></script>
<lightning-out-application app-id="1Usfi..." components="c-my-lwc"></lightning-out-application>
<c-my-lwc></c-my-lwc>
```

**Detection hint:** any `$Lightning.use(`, `$Lightning.createComponent(`, or an Aura
`lightning:out` app is the beta, not 2.0.

---

## Anti-Pattern 2: Putting a Session ID or token in the markup

**What the LLM generates:** `frontdoor-url="https://MY_DOMAIN.my.salesforce.com/secur/frontdoor.jsp?sid=00D..."`
baked into static HTML, or an `access_token` attribute.

**Why it happens:** the model treats the frontdoor URL as a static string because the docs show
its shape, and it omits the runtime exchange.

**Correct pattern:** fetch a token from an authenticated backend, exchange it for a frontdoor URL
via the UI Bridge API, and assign `frontdoor-url` in JavaScript at runtime. Redact any real
credential as `[REDACTED]` in examples.

**Detection hint:** a literal `sid=`, `access_token`, or a non-placeholder token anywhere in
served markup.

---

## Anti-Pattern 3: Loading the library from inside an LWC

**What the LLM generates:** `loadScript(this, LIGHTNING_OUT_URL)` or a `document.createElement('script')`
inside a component to bootstrap the embed.

**Why it happens:** loading third-party scripts via `loadScript` is a well-known LWC idiom, so the
model applies it here.

**Correct pattern:** put the `<script>` tag in the external host page's HTML. Lightning Web
Security blocks `<script>` insertion from within a component.

**Detection hint:** any `loadScript`/`createElement('script')` referencing `lightning.out`.

---

## Anti-Pattern 4: Recommending it for Salesforce-hosted surfaces or guest users

**What the LLM generates:** advice to use Lightning Out 2.0 to place an LWC on a Lightning
record page, an Experience Cloud page, or for anonymous/guest visitors.

**Why it happens:** the model generalizes "embed an LWC" without the external-only and
authenticated-only constraints.

**Correct pattern:** state that Lightning Out 2.0 is for **external, non-Salesforce** hosts and
**authenticated Salesforce users only** (guest/unauthenticated access isn't supported yet). Use
standard LWC targets on Salesforce-hosted surfaces.

**Detection hint:** guidance that mixes Lightning Out with Lightning App Builder targets, or that
promises anonymous access.

---

## Anti-Pattern 5: Using the OAuth client credentials flow

**What the LLM generates:** a server-to-server client credentials flow to "get a token" for the
embed.

**Why it happens:** client credentials is the go-to headless-auth pattern in training data.

**Correct pattern:** Lightning Out 2.0 needs user context, so use a user access token / Session
ID through the UI Bridge exchange, or the automatic OAuth authorization flow. The client
credentials flow is explicitly unsupported.

**Detection hint:** `grant_type=client_credentials` anywhere in the proposed auth.

---

## Anti-Pattern 6: Keeping `lightning/navigation` in the embedded component

**What the LLM generates:** an embedded LWC that imports `NavigationMixin` / `lightning/navigation`
to route the user.

**Why it happens:** navigation is standard in in-org LWCs, so the model carries it over.

**Correct pattern:** remove `lightning/navigation`; it isn't supported in the embedded context.
Route on the host page or emit an event the host handles.

**Detection hint:** `import ... from 'lightning/navigation'` or `NavigationMixin` in a component
destined for a Lightning Out 2.0 embed.

---

## Anti-Pattern 7: Asserting the wrong maturity or misdescribing the beta relationship

**What the LLM generates:** "Lightning Out 2.0 has been GA since Spring '25," or "2.0 extends the
existing Lightning Out beta."

**Why it happens:** the model pattern-fills release labels and assumes a new version extends the
old one.

**Correct pattern:** 2.0 is **GA as of Winter '26** and **completely replaces** (does not extend)
Lightning Out (beta); the beta remains under Beta Service Terms. Don't state a maturity the
release notes don't give.

**Detection hint:** any GA date other than Winter '26, or language calling 2.0 an "extension" or
"enhancement" of the beta.
</content>
