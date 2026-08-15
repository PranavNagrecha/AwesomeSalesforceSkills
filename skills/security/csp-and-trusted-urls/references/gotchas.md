# Gotchas — CSP and Trusted URLs

Non-obvious platform behaviours around Content Security Policy and Trusted URLs.
Grounded in the Metadata API Developer Guide (`CspTrustedSite`, `SecuritySettings`)
and Security for Lightning Components (Summer '26, API 67.0).

## Gotcha 1: Context Is Not a Label — a URL Trusted in LEX Is Not Trusted in Experience Cloud

**What happens:** A Trusted URL is created, verified working in Lightning
Experience, and the identical component fails in the Experience Cloud site with the
same CSP violation. The Trusted URLs list shows the URL as Active, so it looks
configured.

`context` is an enum that scopes the whole record:

| Value | Applies to | UI label |
|---|---|---|
| `All` | "all supported context types" | All |
| `LEX` | "Lightning Experience pages only" | Lightning Experience pages |
| `Communities` | "Experience Builder sites only" | Experience Builder Sites |
| `VisualForce` | "custom Visualforce pages only" (API 55.0+) | — |
| `FieldServiceMobileExtension` | Field Service Mobile Extensions only (API 47.0+) | — |
| `LightningOut` | "Reserved for future use" (API 64.0+) | — |

**When it occurs:** Whenever a component is reused across surfaces, which is the
normal reason for building it as an LWC in the first place.

**How to avoid:** Enumerate the surfaces the component runs on *before* creating
the record. Either create one entry per context or use `All` deliberately, with the
reason in `description`. `All` is a wider grant, not a shortcut — it trusts the
origin on every surface including ones the component does not run on today.

Note also the Visualforce caveat: "For custom Visualforce pages, content is
restricted to trusted URLs only if the page's `cspHeader` attribute is set to
`true`." A `VisualForce`-context Trusted URL does nothing for a page that does not
opt in.

---

## Gotcha 2: There Is No `script-src` Checkbox on a Trusted URL

**What happens:** The console says `Refused to load the script`, the developer opens
the Trusted URL screen looking for a script-src checkbox, and finds only
`connect-src`, `font-src`, `frame-src`, `img-src`, `media-src`, and `style-src`.

The `CspTrustedSite` field list confirms it: `isApplicableToConnectSrc`,
`isApplicableToFontSrc`, `isApplicableToFrameSrc`, `isApplicableToImgSrc`,
`isApplicableToMediaSrc`, `isApplicableToStyleSrc` — and nothing for scripts.

**When it occurs:** On any attempt to load third-party JavaScript by URL from a
Lightning component.

**How to avoid:** Vendor the library into a **static resource** and load it with
`loadScript` from `lightning/platformResourceLoader`. It is then served from the
org's own origin, which `script-src 'self'` already permits — no Trusted URL is
involved, and none would help. This also pins the version, removing the "the CDN
shipped a breaking change overnight" failure mode.

Where a vendor genuinely requires their loader to be fetched live (some payment and
analytics SDKs do), that is a platform-level conversation and a documented risk
acceptance, not a checkbox you have missed.

---

## Gotcha 3: Inline Handlers Are Blocked, and No Configuration Unblocks Them

**What happens:** Migrated Visualforce or Aura markup containing
`onclick="doSomething()"` produces a CSP violation that no Trusted URL resolves.

> "the framework prohibits `unsafe-inline` for the `script-src` directive ... this
> attempt to use an event handler to run an inline script is prevented:
> `<button onclick="doSomething()"></button>`"
> — Security for Lightning Components, *Content Security Policy*

**When it occurs:** During Aura-to-LWC and Visualforce-to-LWC migrations, and when
pasting vendor snippets from documentation written for a plain web page.

**How to avoid:** Use the LWC template binding form, `onclick={handleClick}`, which
the compiler turns into a real listener rather than an inline script string. There
is no org setting that permits `unsafe-inline` on Lightning pages; the only lever is
Relaxed CSP in Experience Builder, which is site-wide and is the wrong trade (see
Gotcha 9).

---

## Gotcha 4: A Malformed URL Saves, Is Marked Active, and Is Silently Excluded

**What happens:** A Trusted URL appears in the list view, `isActive` is `true`, the
host in the record is exactly the host in the console error — and the request is
still blocked.

> "Before February 2025, it was possible to save a malformed URL. Malformed URLs
> are excluded from generated CSP HTTP headers. To keep your Trusted URLs list
> accurate, remove any malformed entries."
> — Metadata API Developer Guide, `CspTrustedSite.endpointUrl`

Documented examples of malformed values that pass a casual eye:
`malformed^url.example.com` and `https://{subdomain}.example.com`.

**When it occurs:** In orgs older than early 2025, and in any org where entries were
templated from a variable that did not substitute — the second example above is
exactly what an unrendered template leaves behind.

**How to avoid:** When a URL is visibly allow-listed and still blocked, audit the
stored `endpointUrl` string character by character before looking anywhere else.
Salesforce publishes a knowledge article, *Identify Malformed Trusted URLs*, with an
Apex class for sweeping the org. Note also that `endpointUrl` is a literal: "To add
an `EndpointUrl` based on parameters, build the URL before you add it to this
Metadata Type."

---

## Gotcha 5: The API-Version Default for Unset Directives Has Changed Three Times

**What happens:** A `CspTrustedSite` deployed with an older `package.xml` version
grants something nobody selected — or, on a modern version, fails to deploy at all.

The behaviour when every `isApplicable*` field is `false`:

| API version of the deployment | Result |
|---|---|
| 49.0 and earlier | "if all `isApplicable` fields are `false`, these fields all default to `true`" — **everything** is granted |
| 50.0 to 58.0 | "if all `isApplicable` fields are `false`, the `isApplicableToImgSrc` field is set to `true`" |
| 59.0 and later | "for each trusted URL, at least one `CSPTrustedSite` starting with `isApplicable` or `canAccess` must be set to `true`" — deployment is rejected |

**When it occurs:** When retrieving records created years ago, or when a pipeline
pins an old `<version>` in `package.xml`. A record created under API ≤ 49.0 with
nothing ticked is an *open* grant that a modern retrieve will show as all-false.

**How to avoid:** Always write every directive field explicitly, `true` or `false`,
even the ones you are turning off. It is more XML and it removes the version
dependency entirely. Audit legacy entries by reading the generated CSP header rather
than the metadata, because for old records the two do not agree.

---

## Gotcha 6: Camera and Microphone Need an Org-Level Switch as Well as the Per-URL Flag

**What happens:** `canAccessCamera` is set to `true` on the Trusted URL, the iframe
loads, and the camera never activates. There is no error mentioning the camera.

Device access is governed by the `Permissions-Policy` header, not CSP, and the
per-URL flag is inert until the org opts into per-URL control:

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

**When it occurs:** On the first video, telehealth, or barcode-scanning integration
in an org. Both `canAccessCamera` and `canAccessMicrophone` are API 59.0 and later.

**How to avoid:** Treat this as a two-part change and deploy the `SecuritySettings`
change first — it is an org-wide setting with its own review, and flipping
`enablePermissionsPolicy` changes header behaviour for every page.

---

## Gotcha 7: A Third-Party Script Almost Never Talks to Only Its Own Origin

**What happens:** The vendor's loader is allow-listed and loads. Then a second CSP
violation appears for the vendor's API host, then a third for their CDN's image
host, then a fourth for a font. Each fix ships as its own change.

**When it occurs:** With payment SDKs, analytics, chat widgets, and mapping
libraries — anything with a runtime backend rather than a pure client-side library.

**How to avoid:** Read the vendor's own CSP documentation before configuring
anything and enumerate every host and directive in one pass. Most vendors publish
this exact list. Then create one Trusted URL per origin — not one wildcard covering
all of them — and give each a `description` that names the vendor and the feature.
Verify by exercising the *whole* flow, including the failure and challenge paths: a
3-D Secure iframe or an error-reporting beacon only fires on the unhappy path and
will otherwise be discovered by a customer.

---

## Gotcha 8: The Generated CSP Header Has a Practical Size Ceiling

**What happens:** In a large org with hundreds of Trusted URLs and several framing
relationships, requests start failing at the infrastructure layer — a proxy or load
balancer rejects the response — with no Salesforce-side error.

> "Some infrastructure limits the maximum size of HTTP headers. If you allow
> multiple domains to frame content served by your org, keep the size of the CSP
> header under 12 KB. Salesforce customers report issues when the header size
> approaches 16 KB, and third parties often add to the header during processing."
> — Metadata API Developer Guide, `CspTrustedSite`

**When it occurs:** Only in mature orgs, which is precisely where nobody is looking
for it, and where the allow-list has accumulated entries for features long retired.

**How to avoid:** Treat the Trusted URL list as something that shrinks as well as
grows. Review it on a fixed cadence, remove entries whose `description` names a
retired feature, and consolidate genuinely-rotating hostnames behind a single
wildcard rather than listing twenty siblings. Note the guide's other warning: "To
ensure smooth integration across Salesforce products, Salesforce includes URLs in
each of the CSP directives that correspond to the `isApplicable` fields, even though
those URLs aren't defined as `CspTrustedSite` components" — so the header is already
larger than your record count suggests, and it grows when Salesforce says so.

---

## Gotcha 9: Relaxed CSP in Experience Builder Is Site-Wide and Effectively Permanent

**What happens:** A widget will not load before a launch date. Someone sets the
Experience Cloud site's Security Level to Relaxed CSP, the widget works, and a
ticket is filed to tighten it later. The ticket is never actionable, because by then
nobody can enumerate which origins the site actually depends on.

**When it occurs:** Under deadline pressure, which is when the decision is worst
informed and hardest to reverse.

**How to avoid:** The escalation path from a CSP violation is: read the console
message → identify the directive → add one Trusted URL for that origin with that
one directive, in the `Communities` context. That path resolves the overwhelming
majority of cases in minutes. Relaxing site-wide CSP is a security-review decision
with a named risk owner, not a build-time workaround. If it is genuinely taken,
record the specific origins that motivated it so a future tightening is possible.

---

## Gotcha 10: HTTPS Is Mandatory, Including for Resources Inside Your Own Org

**What happens:** A legacy internal service on plain HTTP cannot be allow-listed.
The developer looks for a way to permit `http://` and finds none.

> "All references to external fonts, images, frames, and CSS must use an HTTPS URL"
> and "this requirement applies whether the resource is located in your org or
> accessed through a trusted URL." The guide is explicit that "You can't change the
> protocol from HTTPS to HTTP for these resources."

**When it occurs:** With on-premises internal services, older intranet endpoints,
and development environments people try to point at from a sandbox.

**How to avoid:** There is no configuration answer — the service must be fronted by
TLS. For an internal-only endpoint that cannot be exposed publicly, route the call
through Apex with a Named Credential instead of calling it from the browser: the
server-side path is governed by Remote Site Settings and Named Credentials, not by
CSP, and it keeps the endpoint off the public internet.

---

## Gotcha 11: Trusted URLs and Remote Site Settings Solve Different Problems

**What happens:** An Apex callout fails with
`Unauthorized endpoint, please check Setup->Security->Remote site settings`, and
someone adds a Trusted URL. Nothing changes. Or an LWC `fetch` is blocked and
someone adds a Remote Site Setting. Nothing changes.

| | Trusted URL (`CspTrustedSite`) | Remote Site Setting / Named Credential |
|---|---|---|
| Enforced by | The user's **browser**, via the CSP header | The Salesforce **application server** |
| Governs | `fetch`, `XMLHttpRequest`, `<img>`, `<iframe>`, fonts, CSS, WebSockets | Apex `Http.send()`, Visualforce server-side calls |
| Failure text | `Refused to connect to ... violates the following Content Security Policy directive` | `Unauthorized endpoint ...` |

**When it occurs:** Constantly, because both are "allow-list an external URL" screens
in Setup and the distinction is about *who makes the request*.

**How to avoid:** Ask where the request originates. Browser → Trusted URL. Apex →
Remote Site Setting, or better, a Named Credential. A feature that does both needs
both entries, and each must be configured independently.
