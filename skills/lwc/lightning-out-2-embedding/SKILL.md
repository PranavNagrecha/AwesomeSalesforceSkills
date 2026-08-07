---
name: lightning-out-2-embedding
description: "Use when embedding a custom Lightning web component into an external, non-Salesforce web app (React, Angular, Vue, or plain JavaScript) with Lightning Out 2.0 — the Winter '26 GA feature built on Lightning Web Runtime that renders each LWC inside a closed-shadow-DOM iframe, authenticated by a UI Bridge frontdoor URL. Covers the <lightning-out-application> markup (frontdoor-url, app-id, components), the host-page script tag, the token→frontdoor auth exchange, lifecycle events, and the documented limitations. NOT for the legacy Aura-based Lightning Out (beta) or its $Lightning.use() API, NOT for embedding LWCs on Salesforce-hosted surfaces (Lightning pages, Experience Cloud, Flow — use lwc/* or flow/* skills), and NOT for guest/unauthenticated access (not supported yet)."
category: lwc
salesforce-version: "Winter '26+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "embed a Salesforce LWC in our React (or Angular/Vue) app on an external domain"
  - "show a custom Lightning web component on a non-Salesforce website with Lightning Out 2.0"
  - "migrating off the old Aura Lightning Out beta / $Lightning.use() to Lightning Out 2.0"
  - "wiring up the frontdoor-url / UI Bridge token exchange so my embedded LWC authenticates"
  - "my embedded component won't load and I'm getting lo.application.error on the host page"
tags:
  - lightning-out
  - lwc-embedding
  - external-app
  - frontdoor-url
  - ui-bridge-api
inputs:
  - "The custom LWC(s) to embed and the external host framework (React, Angular, Vue, or plain JavaScript)"
  - "The org My Domain and the host page's domain (which must be allowlisted for cross-origin use)"
  - "A runtime way to obtain a Salesforce access token or Session ID for the current user, to exchange for a frontdoor URL"
outputs:
  - "A Lightning Out 2.0 app (18-digit app-id) plus host-page markup: the lightning.out script tag and a <lightning-out-application> element"
  - "A runtime auth flow that exchanges an access token / Session ID for a frontdoor URL via the UI Bridge API (OAuth fallback when no session exists)"
  - "Lifecycle wiring for lo.application.ready/error and lo.component.ready/error to gate rendering and surface failures"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-07
---

# Lightning Out 2.0 Embedding

This skill activates when a practitioner wants to render a **custom** Lightning web component inside an external, non-Salesforce web app using **Lightning Out 2.0** — the feature that became generally available in **Winter '26** and *completely replaces* (it does not extend) the older Aura-based Lightning Out (beta). Lightning Out 2.0 is built on Lightning Web Runtime (LWR) and encapsulates each embedded component in an **iframe that is the root of a closed shadow DOM**, so the component runs in the Salesforce security context rather than the host page's.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm it's Lightning Out 2.0, not the beta.** The legacy Aura path used a `$Lightning.use('c:myApp', ...)` JavaScript call and an Aura `lightning:out` dependency app. Lightning Out 2.0 uses a declarative `<lightning-out-application>` custom element and a frontdoor URL. If you see `$Lightning.use(`, you are on the beta and should migrate — the beta remains subject to the Beta Service Terms, while 2.0 is GA.
- **Confirm the component is a custom LWC.** Lightning Out 2.0 embeds **only custom Lightning web components**. It does **not** support embedding Aura components (custom or standard), and standard base components can only appear composed inside your own LWC.
- **Confirm the users are authenticated Salesforce users.** In this initial GA, Lightning Out 2.0 apps are available **only to authenticated Salesforce users**; unauthenticated / guest access (e.g. anonymous Experience Cloud visitors) is **not supported yet**.
- **Confirm third-party cookies are viable.** Lightning Out 2.0 **requires third-party (cross-origin) cookies**, and each end user must have them enabled in their browser. A browser or policy that blocks third-party cookies breaks the session silently.
- **Do not assert a maturity beyond what the docs state.** 2.0 is GA as of Winter '26. Do not describe the auth model, guest access, or any roadmap item as GA/Beta/Pilot unless the release notes say so.

---

## Core Concepts

### The `<lightning-out-application>` element

The embed is declarative. A single, UI-less `<lightning-out-application>` element configures the session and names the components to load; you then place your component tags (e.g. `<c-my-lwc>`) on the page as siblings.

```html
<!-- 1. Load the Lightning Out 2.0 library ON THE HOST PAGE (not from inside an LWC) -->
<script src="https://MY_DOMAIN.my.salesforce.com/lightning/lightning.out.latest/index.iife.prod.js"></script>

<!-- 2. Configure the session + declare the components to embed -->
<lightning-out-application
    frontdoor-url="https://MY_DOMAIN.my.salesforce.com/secur/frontdoor.jsp?..."
    app-id="1Usfi200000006TCAQ"
    components="c-my-lwc">
</lightning-out-application>

<!-- 3. Render the component; CSS custom properties on the tag reach the embedded LWC -->
<c-my-lwc style="--custom-color: brown;"></c-my-lwc>
```

Three attributes matter:

- **`frontdoor-url`** — the runtime URL that establishes the Salesforce session. Set it *dynamically* after exchanging a token (see auth below); never hard-code it.
- **`app-id`** — the 18-digit id of the Lightning Out 2.0 app (e.g. `1Usfi200000006TCAQ`), obtained from the Lightning Out 2.0 App Manager. It is required for Spring '26 and later.
- **`components`** — a comma-separated list of custom LWCs to embed, in kebab case (`c-my-lwc`); namespaced components use underscores (`complex_ns-lwc-component`).

The App Manager generates the exact `<script>` element (with the right `src` for your My Domain) and the `app-id` — copy them rather than assembling them by hand.

### The library loads on the host page, never inside an LWC

You **cannot** load the Lightning Out 2.0 JavaScript library from within a Lightning web component: **Lightning Web Security (LWS) blocks the insertion of HTML `<script>` elements**. The `<script>` tag must be part of the external host page's own markup.

### Authentication: token → frontdoor URL via the UI Bridge API

Lightning Out 2.0 does not accept a raw session in the markup. At runtime you:

1. Obtain a valid Salesforce **access token or Session ID** for the current user.
2. Call the **UI Bridge API** to exchange that token/Session ID for a **frontdoor URL**.
3. Set that URL on `<lightning-out-application>`'s `frontdoor-url`, then load/trigger the script so it initializes the app and establishes the session.

If the user has **no active Salesforce session**, a full **OAuth authorization flow** kicks in automatically. The **OAuth 2.0 client credentials flow is explicitly not supported**, because it carries no user context.

### Isolation and lifecycle events

Because each component sits in a **closed-shadow-DOM iframe**, host-page JavaScript **can't directly see or manipulate** what's inside, and the LWC executes in the Salesforce context. The host communicates load/error state through four custom events on the host page:

| Event | Fires when | `detail` payload |
|---|---|---|
| `lo.application.ready` | the Salesforce session is established | — |
| `lo.application.error` | session establishment fails | `{ message, originalError }` |
| `lo.component.ready` | an embedded component renders successfully | — |
| `lo.component.error` | a component fails to render or throws at runtime | `{ message, originalError }` |

---

## Common Patterns

### Embed a component in an external SPA (React / Angular / Vue / plain JS)

**When to use:** you want a Salesforce-owned LWC (a case panel, a pricing widget) to appear natively inside an app you host on your own domain.

**How it works:** add the App-Manager-provided `<script>` to the host page's `index.html`; on mount, call your token endpoint, exchange the token for a frontdoor URL via the UI Bridge API, then set `frontdoor-url`, `app-id`, and `components` on a `<lightning-out-application>` element and drop your `<c-my-lwc>` tag where you want it rendered. Gate your "loaded" UI on `lo.application.ready` and `lo.component.ready`.

**Why not the alternative:** rebuilding the component's logic in your framework duplicates Salesforce business rules and loses server-side security; an `<iframe>` to a Salesforce page gives you no typed component API and a heavier surface.

### Robust load-and-error handling

**When to use:** always — network, cookie, and auth failures are common across origins.

**How it works:** register listeners for all four `lo.*` events *before* setting `frontdoor-url`. Show a spinner until `lo.application.ready` + `lo.component.ready`; on `lo.application.error` / `lo.component.error`, read `detail.message` / `detail.originalError`, log them, and show a retry path. Treat a stalled session (no ready, no error) as a likely blocked-third-party-cookie condition.

**Why not the alternative:** assuming the component "just renders" produces a blank area with no diagnostic when cookies are blocked or the token is stale.

### Migrating from Aura Lightning Out (beta)

**When to use:** you have an existing `$Lightning.use('c:...')` / `lightning:out` integration.

**How it works:** the embedded component must already be (or be rewritten as) an **LWC** — Aura components can't be embedded in 2.0. Replace the `$Lightning.use()` bootstrap and its Aura dependency app with the host-page `<script>` + `<lightning-out-application>` markup, and replace the session/`accessToken` handling with the UI Bridge frontdoor-URL exchange. Re-verify any `lightning/navigation` usage — it does **not** work in 2.0.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Embed an LWC on a Salesforce Lightning page / record page | Standard LWC targets, not Lightning Out | Lightning Out is for **external, non-Salesforce** hosts only |
| Embed on an Experience Cloud (LWR) site | Native Experience Builder / LWR components | Lightning Out 2.0 targets external apps; guest access isn't supported yet |
| Embed an Aura component externally | Rewrite it as an LWC first | 2.0 does not embed Aura (custom or standard) |
| You have a live user session in the host app | UI Bridge token → frontdoor URL exchange | The declared, supported 2.0 auth path |
| Server-to-server / no user context | Not supported — needs a user | Client credentials flow is explicitly unsupported |
| Component needs in-app page navigation | Redesign without `lightning/navigation` | The navigation service isn't supported in 2.0 |
| Existing `$Lightning.use()` beta integration | Migrate to `<lightning-out-application>` | 2.0 replaces, and isn't an extension of, the beta |

---

## Recommended Workflow

1. **Verify eligibility** — confirm the target is an external non-Salesforce app, the component is a custom LWC (rewrite Aura first), and users are authenticated Salesforce users. Rule out `lightning/navigation` and guest-access dependencies up front.
2. **Create the Lightning Out 2.0 app** — in the Lightning Out 2.0 App Manager, create the app and copy the generated `<script>` element and the 18-digit `app-id`. Allowlist the external host domain for cross-origin use and confirm third-party cookies are viable for your users.
3. **Wire host-page markup** — add the `<script>` to the host page (not inside an LWC), and place a `<lightning-out-application>` element with `app-id` and `components`, plus your `<c-my-lwc>` tag(s).
4. **Implement the auth exchange** — obtain the user's access token / Session ID, call the UI Bridge API for a frontdoor URL, and set `frontdoor-url` at runtime. Rely on the OAuth fallback for no-session users; never use the client credentials flow.
5. **Handle lifecycle events** — subscribe to `lo.application.ready/error` and `lo.component.ready/error` before setting the frontdoor URL; gate the UI on ready and surface `detail.message` on error.
6. **Test cross-origin and failure paths** — verify with third-party cookies enabled *and* blocked, with an expired token, and on each supported host framework. Run `scripts/check_lightning_out_2_embedding.py` against the host markup.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The host is an external, non-Salesforce app and the embedded component is a **custom LWC** (no Aura)
- [ ] The `lightning.out` `<script>` is on the host page, **not** injected from inside an LWC
- [ ] `<lightning-out-application>` has a runtime-set `frontdoor-url`, an 18-digit `app-id`, and a kebab-case `components` list
- [ ] No access token, Session ID, or frontdoor URL is hard-coded in static markup; it's fetched at runtime via the UI Bridge API
- [ ] The client credentials flow is **not** used; OAuth fallback covers no-session users
- [ ] All four `lo.*` lifecycle events are handled, with a visible error path reading `detail.message`
- [ ] Third-party-cookie-blocked behavior was tested and produces a clear message, not a blank area
- [ ] No `lightning/navigation` usage remains in the embedded component

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Blocked third-party cookies fail silently** — with cross-origin cookies disabled the session never establishes and the component area stays blank, often with no obvious error. Test the cookie-blocked path explicitly.
2. **You can't inject the library from an LWC** — Lightning Web Security blocks `<script>` insertion, so any attempt to load `lightning.out` from component JS fails. The tag must live in the host page's HTML.
3. **`lightning/navigation` doesn't work** — embedded components can't navigate pages; the navigation service is unsupported. Components that relied on it in-org will break when embedded.
4. **Client credentials flow is rejected** — it provides no user context, so server-to-server auth can't back a Lightning Out 2.0 session. You need a real user token or the OAuth fallback.
5. **Only custom LWCs embed** — standard components and all Aura components are excluded; a standard base component only works composed inside your own LWC.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Host-page markup | The `lightning.out` `<script>` plus a `<lightning-out-application>` element and component tags (see `templates/lightning-out-2-embedding-template.md`) |
| Lightning Out 2.0 app | The App-Manager-created app supplying the 18-digit `app-id` and the script `src` for your My Domain |
| Runtime auth glue | Host-app code that exchanges an access token / Session ID for a frontdoor URL via the UI Bridge API and sets `frontdoor-url` |
| Lifecycle handlers | Listeners for `lo.application.ready/error` and `lo.component.ready/error` gating render and surfacing errors |

---

## Related Skills

- `lwc/lwc-app-builder-config` — author and expose the custom LWC (`@api` properties, targets) that Lightning Out 2.0 embeds.
- `security/oauth-connected-apps` — the OAuth authorization / token model behind the frontdoor-URL exchange and the fallback flow.
- `flow/flow-for-experience-cloud` — the *different* pattern for surfacing Salesforce UI on a Salesforce-hosted Experience site; don't confuse it with external embedding.
