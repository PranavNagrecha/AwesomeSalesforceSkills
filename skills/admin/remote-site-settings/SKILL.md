---
name: remote-site-settings
description: "Use when configuring Remote Site Settings to allow Apex callouts to external URLs, or distinguishing them from CSP Trusted Sites for Lightning component resource loading. NOT for storing an endpoint and its auth as a Named Credential — use integration/named-credentials-setup. NOT for allow-listing a URL the browser itself loads (script, iframe, fetch) — use security/csp-and-trusted-urls."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "Apex callout is failing with CalloutException even though I added the URL to CSP Trusted Sites"
  - "How do I allow Salesforce to call an external REST API from Apex?"
  - "Remote Site Settings not included in Change Set — callouts failing after deployment"
  - "What is the difference between Remote Site Settings and CSP Trusted Sites?"
  - "Apex Http.send() is throwing an error in production but works in sandbox"
tags:
  - remote-site-settings
  - apex-callout
  - csp-trusted-sites
  - integration-admin
  - callout-security
inputs:
  - "External endpoint URL that Apex code needs to call (including protocol: https://)"
  - "Whether the issue is a failing Apex callout or a Lightning component resource loading issue"
  - "Whether the endpoint is being added via Change Set or Metadata API"
outputs:
  - "Remote Site Setting configuration for the external endpoint"
  - "Distinction guidance: Remote Site Settings vs. CSP Trusted Sites"
  - "Change Set inclusion steps for Remote Site Settings"
  - "Metadata API RemoteSiteSetting deployment configuration"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-21
---

# Remote Site Settings and CSP Trusted Sites

This skill activates when a practitioner needs to configure external endpoint access for Apex callouts (Remote Site Settings) or when troubleshooting the common confusion between Remote Site Settings (server-side Apex callout gate) and CSP Trusted Sites (browser-side Lightning component resource gate). It covers the most critical anti-pattern in this domain: adding a URL to CSP Trusted Sites to fix a failing Apex callout.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Server-side vs. browser-side**: Remote Site Settings and CSP Trusted Sites are completely separate security controls for completely different scenarios. Remote Site Settings gate server-side Apex callouts. CSP Trusted Sites gate browser-side resource loading in Lightning components. Adding a URL to the wrong control does nothing.
- **Most critical misconception**: Adding an endpoint to CSP Trusted Sites does NOT fix a failing Apex Http.send() callout. Apex callouts are server-side — a raw-URL callout needs the site registered in Remote Site Settings, and a callout whose endpoint is a named credential needs no Remote Site Setting (apexdev 264 L34758-34762); CSP plays no part.
- **Change Set gotcha**: Remote Site Settings are deployable Metadata API components (type `RemoteSiteSetting`, api_meta 264 L106496) and must travel with the Apex that calls them. UNVERIFIED (2026-10-21): that Change Sets do not add them automatically as dependencies of Apex — Change Set behaviour is Help-only.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Does the failing call run in Apex on the server or in the browser (LWC/Aura `fetch`)? | Apex callouts need a Remote Site Setting (apexdev 264 L34758); browser loads need a Trusted URL (api_meta 264 L41578-41580) — Gotcha 1 | The one control that fixes the failure |
| Does the Apex use a named credential (`callout:Name/...`) as the endpoint? | Then no Remote Site Setting is needed (apexdev 264 L34761) — Anti-pattern 5 | No redundant allow-list entry |
| What exact URL, including scheme, does the code call? | Matching rules (prefix, scheme) are not in the corpus — Gotcha 3 | A URL copied from the code, not typed from memory |
| Does the code send data between an HTTPS session and an HTTP site? | That is what `disableProtocolSecurity` allows (api_meta 264 L106516-106521) — Anti-pattern 4 | `false` unless the security implication is accepted in writing |
| How is it deployed: Change Set, `sf project deploy`, or a managed package? | Change Set auto-inclusion is UNVERIFIED (Gotcha 2); in a managed package the Remote Site Name is not editable after install (pkg2 264 L14572) | The setting listed explicitly in the deploy |
| Which browser resource type does the LWC load (fetch, font, image, frame, style)? | Trusted URLs have one `isApplicableTo…` flag per type, and no script-src flag (api_meta 264 L41687-41727) | The exact flag to set |
| Is the setting meant to be active in every org it is deployed to? | `disableProtocolSecurity`, `isActive` and `url` are Required fields (api_meta 264 L106516, L106542-106545) | Metadata that deploys and is switched on |

A proper configuration names the one gate the call path needs and deploys it with the code, where "just doing it" adds URLs to whichever allow-list someone remembers until the error stops.

## Core Concepts

### Remote Site Settings — Server-Side Apex Callout Gate

Remote Site Settings (from Setup, enter Remote Site Settings in the Quick Find box, apexdev 264 L34765) are the allow-list for external sites: "Before any Visualforce page, Apex callout, or JavaScript code using XmlHttpRequest in an s-control or custom button can call an external site, that site must be registered in the Remote Site Settings page, or the call fails" (api_meta 264 L106497-106498). UNVERIFIED (2026-10-21): the exact error text (commonly quoted as `CalloutException: Unauthorized endpoint, please check Setup>Security>Remote Site Settings`) — the guides say only that the callout fails.

Key characteristics:
- Applied per org — the type has no user or profile field (fields `description`, `disableProtocolSecurity`, `fullName`, `isActive`, `url`, api_meta 264 L106513-106545).
- UNVERIFIED (2026-10-21): that URL matching is prefix-based (one entry for `https://api.example.com` covers every path) and that `http://` and `https://` need separate entries; the guide's own sample registers a URL with a path, `https://www.maptestsite.net/mapping1` (api_meta 264 L106556).
- Remote Site Settings are metadata (type `RemoteSiteSetting`, available in API 19.0 and later, api_meta 264 L106508) and deploy through the Metadata API or `sf project deploy`; Change Set inclusion is UNVERIFIED (see Before Starting).

### Trusted URLs (formerly CSP Trusted Sites) — Browser-Side Lightning Component Gate

`CspTrustedSite` "Represents a trusted URL"; each component's CSP directives let "Lightning components, third-party APIs, and WebSocket connections" access a resource type from the URL; "In API version 58.0 and earlier ... [they] were referred to as CSP Trusted Sites" (api_meta 264 L41578-41582).

Key characteristics:
- Scoped by `context` (All, Communities, LEX, VisualForce, ...; api_meta 264 L41618-41644).
- One flag per resource type: `isApplicableToConnectSrc` (fetch/XHR, "load URLs using script interfaces"), `isApplicableToFontSrc`, `isApplicableToFrameSrc`, `isApplicableToImgSrc`, `isApplicableToMediaSrc`, `isApplicableToStyleSrc` (api_meta 264 L41687-41722). There is **no script-src flag** — the field table ends at `mobileExtension` (L41727).
- Trusted URLs do not register a site for Apex callouts — only the Remote Site Settings page or a named credential does (apexdev 264 L34758-34762).
- A Lightning component making an XHR/fetch call to an external API from the browser needs a Trusted URL with `isApplicableToConnectSrc`. An Apex class making the same call from the server needs a Remote Site Setting.

### Metadata API Deployment

Remote Site Settings are deployed as `RemoteSiteSetting` metadata type, stored in `remoteSiteSettings/` with the extension `.remoteSite`, file name = the setting's unique name (api_meta 264 L106503-106504):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- remoteSiteSettings/ExternalPaymentGateway.remoteSite -->
<RemoteSiteSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Payment gateway endpoint for Apex callouts</description>
    <disableProtocolSecurity>false</disableProtocolSecurity>
    <isActive>true</isActive>
    <url>https://api.paymentgateway.com</url>
</RemoteSiteSetting>
```


Deploy via `sf project deploy start`. UNVERIFIED (2026-10-21): the Change Set UI path (Add → Component Type "Remote Site Setting") is Help-only.

---

## Common Patterns

### Fixing a Failing Apex Callout

**When to use:** An Apex class using `Http.send()` to a raw URL fails because the site is not registered (apexdev 264 L34758-34759; the exact exception text is UNVERIFIED, see Core Concepts).

**How it works:**
1. Identify the exact URL being called in the Apex code (including scheme and domain).
2. From Setup, enter Remote Site Settings in the Quick Find box, then select Remote Site Settings (apexdev 264 L34765).
3. Click New Remote Site (L34766).
4. Enter a name (letters and underscores, starting with a letter, api_meta 264 L106523-106526), the URL, and optionally a description (apexdev 264 L34767-34769).
5. Leave "Disable Protocol Security" unchecked. When true, "code within Salesforce can pass data from an HTTPS session to an HTTP session, and vice versa. Only set to true if you understand the security implications" (api_meta 264 L106516-106521). It is not a certificate-validation switch.
6. Save and test the Apex callout.

### Including Remote Site Settings in a Change Set

**When to use:** Deploying Apex code that makes callouts from sandbox to production via Change Set.

**How it works (UNVERIFIED (2026-10-21): Change Set UI steps and dependency behaviour are Help-only):**
1. In the Change Set, click Add.
2. Under Component Type, select "Remote Site Setting."
3. Add each required Remote Site Setting.
4. Deploy the Change Set — the Remote Site Setting will be created in the target org.

If the setting is not deployed with the code, the Apex deploys but the callout fails in the target org, because the site is not registered there (apexdev 264 L34758-34759).

---

## Decision Guidance

| Situation | Correct Control | Why |
|---|---|---|
| Apex `Http.send()` to a raw URL fails as unregistered | Remote Site Setting | "Before any Apex callout can call an external site, that site must be registered in the Remote Site Settings page" (apexdev 264 L34758) |
| Lightning component fetch/XHR failing (browser error) | Trusted URL (`CspTrustedSite`) with `isApplicableToConnectSrc` | Browser-side loading is gated by CSP directives (api_meta 264 L41578-41580, L41687) |
| Both Apex and Lightning need to call the same endpoint | BOTH Remote Site Setting AND Trusted URL | Server-side and browser-side are separate gates |
| Apex callout working in sandbox, failing in production | Deploy the Remote Site Setting with the code | The target org has no registration for the site; Change Set auto-inclusion is UNVERIFIED |
| Code must exchange data between an HTTPS session and an HTTP site | `disableProtocolSecurity: true`, only with a written security sign-off | That is what the field allows (api_meta 264 L106516-106521); it does not disable certificate validation |
| Using Named Credentials for callouts | No Remote Site Setting for that endpoint | "If the callout specifies a named credential as the endpoint, you don't need to configure remote site settings" (apexdev 264 L34761) |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the error type** — Determine whether the failing call is from Apex server-side code (`Http.send()`) or from a Lightning component in the user's browser (fetch, XHR, img.src). The error source determines which control to configure.
2. **For Apex callout failures** — If the endpoint is `callout:<NamedCredential>`, no Remote Site Setting is needed (apexdev 264 L34761). Otherwise open Remote Site Settings from Quick Find, verify the URL is registered, and add it copied from the code.
3. **For Lightning component resource failures** — Add a Trusted URL (`CspTrustedSite`) for the external URL with the flag for the resource type (`isApplicableToConnectSrc` for XHR/fetch; there is no script-src flag, api_meta 264 L41687-41727).
4. **For Change Set deployments** — Add each Remote Site Setting explicitly before uploading; do not rely on dependency detection (UNVERIFIED either way).
5. **For Metadata API / SFDX deployments** — Include `remoteSiteSettings/<Name>.remoteSite` files; the file name matches the setting's unique name (api_meta 264 L106503-106504). Run `python3 skills/admin/remote-site-settings/scripts/check_remote_site_settings.py --manifest-dir force-app` before deploying.
6. **Test the callout** — After adding the Remote Site Setting, test the Apex callout (via anonymous Apex or the relevant trigger/class) and confirm it no longer fails as unregistered.
7. **Document the dependency** — Add a comment near the Apex callout code indicating which Remote Site Setting is required. This prevents future Change Set deployments from omitting it.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Remote Site Setting added for every external URL called via Apex Http.send() without a named credential
- [ ] Trusted URL added, with the right `isApplicableTo…` flag, for every external URL accessed by Lightning components in the browser
- [ ] Remote Site Settings explicitly included in any Change Set that includes Apex code using them
- [ ] Remote Site Setting metadata files included in Metadata API / SFDX deployment packages
- [ ] `disableProtocolSecurity` is `false`, or its HTTPS-to-HTTP data flow has a security sign-off
- [ ] Apex callout tested successfully after configuration
- [ ] Named Credentials evaluated as an alternative (preferred over Remote Site Settings for credential management)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Adding a URL to Trusted URLs (CSP Trusted Sites) does not fix a failing Apex callout** — Apex `Http.send()` is a server-side call; only the Remote Site Settings page or a named credential registers a site for it (apexdev 264 L34758-34762). Trusted URLs set CSP directives for Lightning components, third-party APIs and WebSocket connections (api_meta 264 L41579-41580).
2. **Change Sets and Remote Site Settings** — the Remote Site Settings that callout classes depend on must reach the target org, or the callout fails there. UNVERIFIED (2026-10-21): that the Change Set tool never adds them as dependencies automatically.
3. **`disableProtocolSecurity` is about HTTP/HTTPS session crossing, not certificates** — api_meta 264 L106516-106521. UNVERIFIED (2026-10-21): that `http://` and `https://` URLs need separate entries (references/gotchas.md Gotcha 3).
4. **Packaged settings are not updated on upgrade** — for a managed package, "Component Is Updated During Package Upgrade: No" and the Remote Site Name is not editable by developer or subscriber (pkg2 264 L14550, L14572).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Remote Site Setting configuration | Remote Site Settings entry (Setup Quick Find) for the external endpoint |
| Trusted URL configuration | `CspTrustedSite` entry for browser-side access |
| RemoteSiteSetting metadata XML | Deployable `.remoteSite` file for SFDX / Metadata API deployment |
| Change Set inclusion guide | Steps to add Remote Site Settings to a Change Set explicitly |

---

## Related Skills

- `admin/integration-admin-connected-apps` — Configure connected apps for OAuth-based integration authentication
- `admin/integration-user-management` — Set up the integration user whose callouts will use these settings
- `integration/named-credentials-setup` — endpoint plus auth in one definition, no Remote Site Setting needed
- `security/csp-and-trusted-urls` — browser-side Trusted URL design
