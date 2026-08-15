---
name: csp-and-trusted-urls
description: "Configure Content Security Policy via Trusted URLs and CSP Trusted Sites so Lightning, LWR, and LWC can call third-party scripts, APIs, and frame sources. NOT for clickjack configuration — use lwc/static-resources-in-lwc."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "script refused to load salesforce csp"
  - "add trusted url for external api"
  - "lwc fetch third party blocked"
  - "csp trusted sites lightning"
tags:
  - csp
  - trusted-urls
  - lightning
inputs:
  - "External URLs the UI must reach"
  - "context (Lightning vs LWR vs Experience)"
outputs:
  - "Trusted URL records with correct context scopes"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# CSP and Trusted URLs

Salesforce sets a Content Security Policy header on Lightning pages. The framework
default is restrictive — `script-src 'self'`, and `font-src`, `img-src`,
`media-src`, `frame-src`, `style-src`, and `connect-src` likewise scoped to the
org's own origin. Any external resource a component needs is blocked until an
administrator adds a **Trusted URL** (called a CSP Trusted Site in API 58.0 and
earlier) that grants that specific origin, that specific directive, in that
specific context.

Setup path, verbatim from Salesforce Help: *From Setup, in the Quick Find box,
enter `Trusted URLs`, and then select **Trusted URLs**.*

The metadata type is `CspTrustedSite`, stored in `cspTrustedSites/` with the
`.cspTrustedSite` extension, available in API 39.0 and later.

---

## Before Starting

1. **Read the actual console message.** It names the directive that blocked the
   request, and that directive is the only checkbox you need. Configuring from a
   guess is how allow-lists rot.

2. **Establish which surfaces the component runs on.** Lightning Experience,
   Experience Builder site, and Visualforce are separate contexts, and a URL
   trusted in one is not trusted in another.

3. **Enumerate every origin the feature touches**, not just the one in the first
   error. A third-party SDK typically needs a loader host, an API host, a frame
   host for challenge flows, an asset CDN, and a telemetry beacon.

4. **Decide whether this is a browser problem at all.** If the request originates
   in Apex, you need a Remote Site Setting or a Named Credential, and no Trusted
   URL will help.

---

## Core Concepts

### The six directives you can grant

`CspTrustedSite` exposes exactly six directive fields. There is **no `script-src`
field** — Lightning fixes `script-src` at `'self'`.

| Field | Grants | Typical console phrase |
|---|---|---|
| `isApplicableToConnectSrc` | `fetch`, `XMLHttpRequest`, WebSockets | `Refused to connect to` |
| `isApplicableToFrameSrc` | `<iframe>` sources | `Refused to frame` |
| `isApplicableToImgSrc` | images | `Refused to load the image` |
| `isApplicableToFontSrc` | fonts | `Refused to load the font` |
| `isApplicableToStyleSrc` | stylesheets | `Refused to load the stylesheet` |
| `isApplicableToMediaSrc` | audio and video resources | `Refused to load media` |

### Context scopes the whole record

| `context` | Applies to |
|---|---|
| `All` | All supported context types |
| `LEX` | Lightning Experience pages only |
| `Communities` | Experience Builder sites only |
| `VisualForce` | Custom Visualforce pages only, **and only if the page's `cspHeader` attribute is `true`** (API 55.0+) |
| `FieldServiceMobileExtension` | Field Service Mobile Extensions only (API 47.0+) |
| `LightningOut` | "Reserved for future use" (API 64.0+) |

### The `endpointUrl` grammar

Must include a domain name; may include a port. Wildcards are supported
(`*.example.com`). Third-party APIs must begin with `https://`; WebSockets must
begin with `wss://`. The value is a literal — build any templated URL before you
write it into the metadata.

Malformed values (`malformed^url.example.com`, `https://{subdomain}.example.com`)
could be saved before February 2025 and are "excluded from generated CSP HTTP
headers" — an entry that looks Active and correct but has never been in the header.

### The default for unset directives is version-dependent

| API version of the deployment | If every `isApplicable*` is `false` |
|---|---|
| ≤ 49.0 | All of them default to `true` — an **open** grant |
| 50.0–58.0 | `isApplicableToImgSrc` is set to `true` |
| ≥ 59.0 | At least one `isApplicable*` or `canAccess*` must be `true`, or the deploy is rejected |

Write every field explicitly, `true` and `false` alike.

### Camera and microphone are `Permissions-Policy`, not CSP

`canAccessCamera` and `canAccessMicrophone` (API 59.0+) are inert unless the org has
`enablePermissionsPolicy = true` and `grantCameraAccess` / `grantMicrophoneAccess`
= `TrustedUrls` in `SecuritySettings`.

### Trusted URL is not Remote Site Setting

| | Trusted URL | Remote Site Setting / Named Credential |
|---|---|---|
| Enforced by | The user's **browser**, via the CSP header | The Salesforce **application server** |
| Governs | LWC/Aura `fetch`, `<img>`, `<iframe>`, fonts, CSS, WebSockets | Apex `Http.send()`, Visualforce |
| Error text | `Refused to ... violates the following Content Security Policy directive` | `Unauthorized endpoint, please check Setup->Security->Remote site settings` |

---

## Common Patterns

### Pattern A — one origin, one directive, one context

The default and the correct shape for most cases. Read the console error, create
one record with one directive ticked and every other field explicitly `false`, and
put the depending component's name in `description`. Example 1 in
[`references/examples.md`](references/examples.md).

### Pattern B — vendor the library into a static resource

For third-party JavaScript, this is the answer rather than a Trusted URL, because
there is no `script-src` field to grant. Upload the library as a static resource
and load it with `loadScript` from `lightning/platformResourceLoader`; it is then
served from the org's own origin. This also pins the version.

### Pattern C — one record per origin for a multi-host SDK

A payment or analytics SDK needs several entries — loader, API, challenge iframe,
asset CDN. Enumerate them from the vendor's own CSP documentation in one pass, then
test the *failure and challenge* paths, because a 3-D Secure iframe or an error
beacon fires only there.

### Pattern D — Apex proxy instead of a browser call

When the call carries a credential, or the endpoint is internal and not
HTTPS-reachable from a browser, route it through Apex with a Named Credential. No
Trusted URL, no CORS, credentials never reach the browser.

---

## Decision Guidance

| Situation | Approach |
|---|---|
| LWC needs to `fetch` an external JSON API | Trusted URL, `connect-src`, correct context |
| Component needs a third-party JS library | Static resource + `loadScript` — not a Trusted URL |
| Vendor mandates loading their script live | Vendor conversation and a documented risk acceptance; there is no per-URL `script-src` grant |
| Third-party widget in an iframe | Trusted URL, `frame-src`, plus `connect-src` for whatever the widget calls |
| Widget needs camera or microphone | `canAccess*` on the URL **and** `SecuritySettings` set to `TrustedUrls` |
| Apex callout is blocked | Remote Site Setting or Named Credential — not a Trusted URL |
| Internal service is HTTP-only | Apex proxy; CSP requires HTTPS and there is no exemption |
| Vendor hostnames genuinely rotate | Wildcard, with the reason recorded in `description` |
| Deadline pressure, widget still blocked | Escalate the enumeration, never Relaxed CSP |

---

## Recommended Workflow

1. **Reproduce and read the violation.** Capture the full console message: it names
   both the blocked URL and the directive. One message per blocked origin.
2. **Classify the caller.** Browser-originated → Trusted URL. Apex-originated →
   Remote Site Setting or Named Credential. A feature doing both needs both.
3. **Enumerate every origin the feature needs** from the vendor's CSP
   documentation, and note which directive each one requires. Do not configure
   incrementally, one incident at a time.
4. **Decide the context** from the surfaces the component runs on, and emit one
   record per context rather than defaulting to `All`.
5. **Author `CspTrustedSite` metadata** with every directive field written
   explicitly, an exact host unless rotation genuinely requires a wildcard, and a
   `description` naming the depending feature.
6. **Verify the whole flow**, including the failure and challenge paths, and
   confirm no residual console violations.
7. **Add the entry to the quarterly review list** so it is removed when the feature
   is retired — the allow-list must shrink as well as grow.

---

## Review Checklist

- [ ] The directive granted matches the directive named in the console error
- [ ] Every `isApplicableTo*` field is written explicitly, `true` or `false`
- [ ] `context` is set deliberately, not defaulted
- [ ] `endpointUrl` is an exact host unless a wildcard is justified in `description`
- [ ] `endpointUrl` has no template placeholders and no malformed characters
- [ ] `description` names the component or feature that depends on this entry
- [ ] Every origin the feature touches has an entry — loader, API, frame, CDN, beacon
- [ ] Third-party JavaScript is a static resource, not a live CDN load
- [ ] Camera/microphone grants are paired with the `SecuritySettings` change
- [ ] No Relaxed CSP anywhere in the solution
- [ ] Failure and challenge paths exercised, not just the happy path
- [ ] Entry recorded for quarterly review

---

## Salesforce-Specific Gotchas

Full detail with quotes in [`references/gotchas.md`](references/gotchas.md).

1. **Context is not a label** — a URL trusted in LEX is not trusted in Experience
   Cloud, and the record still shows as Active.
2. **There is no `script-src` checkbox.** Use a static resource.
3. **Inline handlers are blocked** and no configuration unblocks them.
4. **A malformed URL saves, shows Active, and is silently excluded** from the CSP
   header — the cause of "it's allow-listed and still blocked."
5. **The default for unset directives changed at API 50.0 and again at 59.0.**
6. **Camera and microphone need an org-level switch too.**
7. **A third-party script almost never talks to only its own origin.**
8. **The generated CSP header has a practical size ceiling** — keep it under 12 KB;
   problems are reported approaching 16 KB.
9. **Relaxed CSP is site-wide and effectively permanent.**
10. **HTTPS is mandatory**, including for resources inside your own org.
11. **Trusted URLs and Remote Site Settings solve different problems.**

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Origin inventory | Every host the feature touches, the directive each needs, and the vendor documentation it came from |
| `CspTrustedSite` metadata | One file per origin per context, every directive field explicit, `description` naming the dependent feature |
| `SecuritySettings` change | Only when camera or microphone access is required, deployed separately as an org-wide change |
| Verification note | Which flows were exercised, including failure and challenge paths, and confirmation of a clean console |
| Review entry | The record's name and owning feature added to the quarterly Trusted URL review |

---

## Related Skills

- `lwc/static-resources-in-lwc` — the `loadScript` / `loadStyle` path that replaces
  a `script-src` grant, and how to package a vendored library
- `security/network-security-and-trusted-ips` — the network-layer controls that
  Trusted URLs are frequently confused with
- `integration/named-credentials-setup` — the server-side alternative when the call
  carries a credential or the endpoint cannot be browser-reachable
