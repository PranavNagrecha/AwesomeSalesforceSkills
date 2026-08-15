# Examples — CSP and Trusted URLs

Salesforce sets a Content Security Policy header on Lightning pages. The framework
default is restrictive:

> "`script-src 'self'` — JavaScript libraries can only be referenced from your org"
> and `font-src`, `img-src`, `media-src`, `frame-src`, `style-src`, and
> `connect-src` are likewise set to `'self'`, so those resources "must be located
> in the org by default."
> — Security for Lightning Components, *Content Security Policy*

A **Trusted URL** (called a CSP Trusted Site in API 58.0 and earlier) adds one
external origin to one or more of those directives, in one or more contexts.

Setup path, verbatim from Salesforce Help: *From Setup, in the Quick Find box,
enter `Trusted URLs`, and then select **Trusted URLs**.*

---

## Reading the browser error before you configure anything

The console message names the directive that blocked the request. That directive
is the checkbox you need — nothing else.

```text
Refused to load the script 'https://js.stripe.com/v3/' because it violates the
following Content Security Policy directive: "script-src 'self' ..."
```

| Console phrase | Directive | Trusted URL field |
|---|---|---|
| `Refused to load the script` | `script-src` | *(no per-URL checkbox — see Example 4)* |
| `Refused to connect to` | `connect-src` | `isApplicableToConnectSrc` |
| `Refused to frame` / `Refused to display ... in a frame` | `frame-src` | `isApplicableToFrameSrc` |
| `Refused to load the image` | `img-src` | `isApplicableToImgSrc` |
| `Refused to load the font` | `font-src` | `isApplicableToFontSrc` |
| `Refused to load the stylesheet` | `style-src` | `isApplicableToStyleSrc` |
| `Refused to load media` | `media-src` | `isApplicableToMediaSrc` |

Guessing which boxes to tick, or ticking all of them, is how allow-lists rot.

---

## Example 1: Let an LWC call a partner REST API from Lightning Experience

**Context:** An LWC on a Lightning record page calls
`https://analytics.corp.example.com/v1/summary` with `fetch()`. It works in a Jest
test and fails in the org.

**Problem:**

```text
Refused to connect to 'https://analytics.corp.example.com/v1/summary' because it
violates the following Content Security Policy directive: "connect-src 'self' ..."
```

`connect-src` — and only `connect-src`. The API returns JSON; it serves no
scripts, images, fonts, or frames.

**Solution — UI:**

```text
Setup → Quick Find: "Trusted URLs" → Trusted URLs → New Trusted URL

  API Name:  Corp_Analytics
  URL:       https://analytics.corp.example.com
  Active:    checked

  CSP Settings
    CSP Context:     Lightning Experience pages
    CSP Directives:  [x] connect-src (scripts)
                     [ ] everything else
```

**Solution — metadata (what you actually commit):**

`force-app/main/default/cspTrustedSites/Corp_Analytics.cspTrustedSite-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Corporate analytics API. Read-only JSON consumed by
        analyticsSummary LWC on the Account record page.</description>
    <context>LEX</context>
    <endpointUrl>https://analytics.corp.example.com</endpointUrl>
    <isActive>true</isActive>
    <isApplicableToConnectSrc>true</isApplicableToConnectSrc>
    <isApplicableToFontSrc>false</isApplicableToFontSrc>
    <isApplicableToFrameSrc>false</isApplicableToFrameSrc>
    <isApplicableToImgSrc>false</isApplicableToImgSrc>
    <isApplicableToMediaSrc>false</isApplicableToMediaSrc>
    <isApplicableToStyleSrc>false</isApplicableToStyleSrc>
</CspTrustedSite>
```

Components are "stored in the `cspTrustedSites` directory ... the file name matches
the unique name of the trusted site, and the extension is `.cspTrustedSite`."

**Why it works:** exactly one origin gains exactly one capability in exactly one
context. The `description` is the part reviewers actually need in a year — the URL
alone does not say which component depends on it.

**Note on Trusted URL vs Remote Site Setting.** These are different controls for
different callers:

| | Trusted URL (`CspTrustedSite`) | Remote Site Setting (`RemoteSiteSetting`) |
|---|---|---|
| Governs | The **browser** — `fetch`, `XMLHttpRequest`, `<img>`, `<iframe>` | The **server** — Apex `Http.send()`, Visualforce |
| Enforced by | The CSP header, in the user's browser | The Salesforce application server |
| Needed for | LWC/Aura calling an external origin | Apex callouts (unless a Named Credential is used) |

An LWC calling out needs a Trusted URL. An Apex callout needs a Remote Site Setting
or a Named Credential. A feature that does both needs both, and adding one does not
satisfy the other.

---

## Example 2: A payment widget in an Experience Cloud site — three directives, and the context trap

**Context:** A B2C Experience Cloud (LWR) checkout loads Stripe.js, which then
opens a 3-D Secure challenge in an iframe and calls Stripe's API.

**Problem:** The team adds a Trusted URL for `https://js.stripe.com` and the script
still fails. Then it loads, and the 3-D Secure step shows a blank frame.

Two independent mistakes:

1. **Wrong context.** The Trusted URL was created with the default context (or
   `LEX`), and the page is an Experience Builder site. The context enum is explicit:
   `LEX` applies "to Lightning Experience pages only," `Communities` applies "to
   Experience Builder sites only." A URL trusted in one is not trusted in the other.
2. **Missing directives.** Stripe serves the script from `js.stripe.com`, but the
   3-D Secure iframe and the API call are different origins and different
   directives.

**Solution:** one entry per origin, each with only what that origin needs.

```xml
<!-- cspTrustedSites/Stripe_JS.cspTrustedSite-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Stripe.js loader for the LWR checkout. Frame-src carries the
        3-D Secure challenge.</description>
    <context>Communities</context>
    <endpointUrl>https://js.stripe.com</endpointUrl>
    <isActive>true</isActive>
    <isApplicableToConnectSrc>true</isApplicableToConnectSrc>
    <isApplicableToFrameSrc>true</isApplicableToFrameSrc>
    <isApplicableToFontSrc>false</isApplicableToFontSrc>
    <isApplicableToImgSrc>false</isApplicableToImgSrc>
    <isApplicableToMediaSrc>false</isApplicableToMediaSrc>
    <isApplicableToStyleSrc>false</isApplicableToStyleSrc>
</CspTrustedSite>
```

```xml
<!-- cspTrustedSites/Stripe_API.cspTrustedSite-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Stripe API endpoint called by Stripe.js from the LWR
        checkout.</description>
    <context>Communities</context>
    <endpointUrl>https://api.stripe.com</endpointUrl>
    <isActive>true</isActive>
    <isApplicableToConnectSrc>true</isApplicableToConnectSrc>
    <isApplicableToFontSrc>false</isApplicableToFontSrc>
    <isApplicableToFrameSrc>false</isApplicableToFrameSrc>
    <isApplicableToImgSrc>false</isApplicableToImgSrc>
    <isApplicableToMediaSrc>false</isApplicableToMediaSrc>
    <isApplicableToStyleSrc>false</isApplicableToStyleSrc>
</CspTrustedSite>
```

If the same checkout also runs inside Lightning Experience for internal agents,
duplicate both entries with `<context>LEX</context>`, or use `<context>All</context>`
on each and accept the wider blast radius deliberately.

**Why it works:** the allow-list mirrors the actual network graph. A third-party
script almost never talks to only its own origin — read the vendor's CSP
documentation and enumerate every host before you configure anything.

---

## Example 3: Wildcards, ports, and malformed URLs

`endpointUrl` has a documented grammar, and the failure modes are not obvious.

```xml
<!-- Valid -->
<endpointUrl>https://example.com</endpointUrl>
<endpointUrl>https://example.com:8080</endpointUrl>   <!-- ports allowed -->
<endpointUrl>*.example.com</endpointUrl>              <!-- wildcard subdomain -->
<endpointUrl>wss://example.com</endpointUrl>          <!-- WebSocket MUST be wss:// -->

<!-- Invalid: excluded from the generated CSP header, silently -->
<endpointUrl>malformed^url.example.com</endpointUrl>
<endpointUrl>https://{subdomain}.example.com</endpointUrl>
```

From the Metadata API guide:

> "This field must include a domain name and can include a port. ... To reduce
> repetition, you can use the wildcard character `*` (asterisk). For example,
> `*.example.com`. For a third-party API, the URL must begin with `https://`. ...
> For a WebSocket connection, the URL must begin with `wss://`."

and the part that produces a genuine mystery:

> "Before February 2025, it was possible to save a malformed URL. Malformed URLs are
> excluded from generated CSP HTTP headers. To keep your Trusted URLs list accurate,
> remove any malformed entries."

So an org that has been running for a few years can hold Trusted URL records that
look correct in the list view, are marked Active, and have never been part of the
CSP header. The symptom is a CSP violation for a URL that is visibly allow-listed.

**On wildcards.** `*.example.com` is supported and is the right call when a CDN
genuinely rotates hostnames. It is the wrong call as a shortcut: it trusts every
current and future subdomain, including any a partner might later delegate. Prefer
the exact host, and when you use a wildcard, put the reason in `description`.

**Templating.** "To add an `EndpointUrl` based on parameters, build the URL before
you add it to this Metadata Type." The field is a literal; there is no merge-field
support.

---

## Example 4: What a Trusted URL cannot do — inline handlers and remote `<script>`

**Context:** A developer migrating an old Visualforce page into an LWC adds a
Trusted URL for a CDN and expects `<script src="...">` to work.

**Problem:** It does not, and no directive checkbox fixes it. The Lightning CSP
disallows `unsafe-inline` for `script-src`:

> "this attempt to use an event handler to run an inline script is prevented:
> `<button onclick="doSomething()"></button>`"
> — Security for Lightning Components, *Content Security Policy*

### WRONG

```html
<!-- inline handler: blocked by CSP, and invalid in LWC templates anyway -->
<button onclick="doSomething()">Go</button>

<!-- remote script tag inside a component: blocked -->
<script src="https://cdn.example.com/chart.min.js"></script>
```

### RIGHT — declarative event binding plus a static resource

```html
<!-- chartPanel.html -->
<template>
    <button onclick={handleClick}>Go</button>
    <div class="chart" lwc:dom="manual"></div>
</template>
```

```js
// chartPanel.js
import { LightningElement } from 'lwc';
import { loadScript } from 'lightning/platformResourceLoader';
import CHART_JS from '@salesforce/resourceUrl/chartJs';

export default class ChartPanel extends LightningElement {
    chartInitialised = false;

    renderedCallback() {
        if (this.chartInitialised) {
            return;
        }
        this.chartInitialised = true;

        // The library is uploaded as a static resource, so it is served from
        // the org's own origin and satisfies script-src 'self'. No Trusted URL
        // is involved, and none would help.
        loadScript(this, CHART_JS)
            .then(() => this.renderChart())
            .catch((error) => {
                // eslint-disable-next-line no-console
                console.error('Chart library failed to load', error);
            });
    }

    handleClick() {
        this.renderChart();
    }

    renderChart() {
        // ... uses the global the library installed
    }
}
```

**Why it works:** the library now comes from the org's own origin, which
`script-src 'self'` already permits. `onclick={handleClick}` is a template binding
compiled by LWC, not an inline script string, so it is not `unsafe-inline`.

**The general rule:** vendor third-party JavaScript into a static resource. It also
pins the version, which removes an entire class of "the CDN changed and production
broke" incidents. Reach for `script-src` on a Trusted URL only when the vendor
requires their loader to be fetched live — payment providers and some analytics
SDKs genuinely do — and record why in the `description`.

---

## Example 5: Camera and microphone are a separate, two-part switch

**Context:** An LWC embeds a third-party video-consultation widget in an iframe.
The frame loads; the camera never turns on.

**Problem:** Camera and microphone are governed by the `Permissions-Policy` header,
not by CSP. Granting `frame-src` does nothing for device access.

**Solution:** two settings that must both be right.

```xml
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Telehealth consultation widget. Needs camera and mic.</description>
    <context>LEX</context>
    <endpointUrl>https://consult.vendor.example.com</endpointUrl>
    <isActive>true</isActive>
    <isApplicableToFrameSrc>true</isApplicableToFrameSrc>
    <isApplicableToConnectSrc>true</isApplicableToConnectSrc>
    <canAccessCamera>true</canAccessCamera>
    <canAccessMicrophone>true</canAccessMicrophone>
    <isApplicableToFontSrc>false</isApplicableToFontSrc>
    <isApplicableToImgSrc>false</isApplicableToImgSrc>
    <isApplicableToMediaSrc>false</isApplicableToMediaSrc>
    <isApplicableToStyleSrc>false</isApplicableToStyleSrc>
</CspTrustedSite>
```

The per-URL flags are inert on their own. From the field description:

> "This field takes effect only when the `enablePermissionsPolicy` field equals
> `true` and the `grantCameraAccess` field equals `TrustedUrls` in the
> `SecuritySettings` metadata API type."

```xml
<!-- settings/Security.settings-meta.xml -->
<SecuritySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enablePermissionsPolicy>true</enablePermissionsPolicy>
    <grantCameraAccess>TrustedUrls</grantCameraAccess>
    <grantMicrophoneAccess>TrustedUrls</grantMicrophoneAccess>
</SecuritySettings>
```

Both fields are API 59.0 and later.

**Why it works:** the org-level setting says "device access is decided per trusted
URL"; the per-URL flag then decides. Setting only the per-URL flag leaves the
org-level policy in whatever mode it was already in, and the flag is ignored.

---

## Anti-Pattern: Turning on Relaxed CSP to ship

**What practitioners do:** in Experience Builder, set the site's Security Level to
Relaxed CSP so the third-party widget works today, and open a ticket to tighten it
later.

**What goes wrong:** the setting is site-wide and permanent in practice. It relaxes
`script-src` for *every* component on *every* page of the site, including any
component a future admin drags on. The specific origin you needed is now
indistinguishable from every other origin, and there is no record of which one the
site actually depended on — so nobody can safely tighten it again.

**Correct approach:** read the console message, identify the directive, and add one
Trusted URL per origin with only that directive ticked. If the vendor's widget
genuinely needs `unsafe-inline` script execution, that is a vendor problem to raise
with the vendor and a risk to accept explicitly in a security review — not a
default to reach for under deadline pressure.
