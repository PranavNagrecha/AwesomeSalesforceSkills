# Gotchas — Remote Site Settings and CSP Trusted Sites

UNVERIFIED (2026-10-21), applies to this file: the exception text `CalloutException: Unauthorized endpoint, please check Setup>Security>Remote Site Settings` is not in the corpus; the guides say only that the callout fails (apexdev 264 L34758-34759).

## Gotcha 1: CSP Trusted Sites (Trusted URLs) Have No Effect on Apex Http.send() Callouts

**What happens:** An admin adds an external endpoint to CSP Trusted Sites to fix a failing Apex callout. The callout continues to fail as unregistered. The admin tries multiple CSP directive types with no change in behavior.

**When it occurs:** Any time an Apex class calls a raw external URL via Http.send() without the URL registered in Remote Site Settings. "CSP Trusted Sites" (renamed Trusted URLs; "In API version 58.0 and earlier ... referred to as CSP Trusted Sites", api_meta 264 L41581-41582) sounds like the relevant control for any kind of "trust this site" configuration.

**How to avoid:** For Apex callout failures, check Remote Site Settings first (Setup Quick Find, apexdev 264 L34765), or use a named credential endpoint, which needs no Remote Site Setting (L34761). Trusted URLs set CSP directives for "Lightning components, third-party APIs, and WebSocket connections" (api_meta 264 L41579-41580) — not server-side Apex.

---

## Gotcha 2: Remote Site Settings Must Be Deployed With the Code That Calls Them

**What happens:** An Apex class is deployed to production via Change Set. After deployment, every callout fails because the site is not registered in production. The sandbox version works because the Remote Site Setting was added manually there.

**When it occurs:** Every deployment of Apex callout code where the Remote Site Setting is not in the same deployment. UNVERIFIED (2026-10-21): that Change Set dependency detection never adds Remote Site Settings for Apex — Change Set behaviour is Help-only. The nearest corpus line is about the browser-side sibling: "If a flow references a Lightning component that depends on a CSP Trusted Site, the trusted site isn't included in the package or change set automatically" (pkg2 264 L10539-10540).

**How to avoid:** Before uploading a Change Set or running a deploy that contains Apex callout code, explicitly add the dependent Remote Site Settings. Document the Remote Site Setting names in code comments near the callout so future developers know to include them.

---

## Gotcha 3: Protocol Mismatch Between Remote Site Setting and Apex Callout URL (UNVERIFIED)

**What happens:** A Remote Site Setting is added for `http://api.example.com`. The Apex code calls `https://api.example.com`. UNVERIFIED (2026-10-21): that the callout then fails as unregistered — the corpus does not describe how a registered URL is matched against the callout URL.

**When it occurs:** When an admin adds the Remote Site Setting from memory with the wrong scheme, or when an external service migrates from HTTP to HTTPS and the Remote Site Setting is not updated.

**How to avoid:** Copy the exact URL (including scheme) from the Apex callout code into the Remote Site Setting URL field, then test the callout in anonymous Apex. If the external service changes scheme, update the Remote Site Setting and include the update in the deployment package.

---

## Gotcha 4: `disableProtocolSecurity` Is Not a Certificate Switch

**What happens:** An admin sets `disableProtocolSecurity` to `true` to "fix SSL errors". The field does something else: when true, "code within Salesforce can pass data from an HTTPS session to an HTTP session, and vice versa. Only set to true if you understand the security implications" (api_meta 264 L106516-106521).

**When it occurs:** Troubleshooting a TLS or certificate failure by toggling the only security-sounding checkbox on the page.

**How to avoid:** Keep it `false`. Fix certificate problems at the certificate (the Apex guide's certificate section, apexdev 264 L36257, L36280), not on the Remote Site Setting.

---

## Gotcha 5: There Is No script-src Trusted URL

**What happens:** An LWC needs a third-party JavaScript library from a CDN; the admin adds a Trusted URL and looks for a script-src option. The `CspTrustedSite` field table has `isApplicableToConnectSrc`, `FontSrc`, `FrameSrc`, `ImgSrc`, `MediaSrc` and `StyleSrc`, then `mobileExtension` — no script-src flag (api_meta 264 L41687-41727).

**When it occurs:** Porting a web page that loads scripts from a CDN into a Lightning component.

**How to avoid:** Do not plan a Trusted URL for script loading; route the library through the component's own packaging (see `security/csp-and-trusted-urls`).
