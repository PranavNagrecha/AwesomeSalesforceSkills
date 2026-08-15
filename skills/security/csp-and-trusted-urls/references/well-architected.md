# Well-Architected Notes — CSP and Trusted URLs

## Relevant Pillars

- **Security** — Primary pillar. CSP is the browser-side control that limits the
  damage of a cross-site scripting flaw: even if an attacker injects markup, the
  policy decides which origins that markup may reach. Its value is entirely a
  function of how narrow the allow-list is. An entry with every directive ticked,
  or a wildcard covering a whole domain tree, is indistinguishable at review time
  from a correct one — which means the control silently degrades into
  documentation. The two mechanisms that matter here are *per-origin* entries and a
  `description` field that says which feature depends on each one.

- **Operational Excellence** — A Trusted URL list is an inventory of the org's
  browser-side external dependencies, and it is one of the few places that
  inventory exists at all. It only stays useful if entries are removed when
  features retire. Left to grow, it becomes both a security dilution and a real
  operational hazard: the generated CSP header has a practical size ceiling that
  large orgs reach.

- **Reliability** — Every allow-listed origin is a runtime dependency of a user
  interface. A vendor changing a CDN hostname breaks the page for every user at
  once, with a failure that appears only in the browser console and produces no
  Salesforce-side error, no debug log, and no alert. Vendoring third-party
  JavaScript into a static resource converts that class of outage into a deploy-time
  decision.

- **Performance** — Marginal, but real at scale. The CSP header is sent on every
  page load; a header approaching the documented 12–16 KB range is bytes on every
  request, and third parties add to it during processing.

## Architectural Trade-offs

**Static resource vs live CDN load.** Bundling third-party JavaScript as a static
resource is the platform-preferred answer: it satisfies `script-src 'self'` with no
Trusted URL, it pins the version, and it makes upgrades a reviewed deploy. The cost
is that security patches now arrive on your release cadence rather than the
vendor's, and the bundle is a build artifact somebody must maintain. Live CDN loads
give you the vendor's latest immediately and hand them the ability to change what
executes in your users' browsers without your knowledge. For payment and analytics
SDKs the vendor often mandates the live load; for charting and utility libraries
there is rarely a good reason not to vendor.

**Exact host vs wildcard.** `*.vendor.example.com` is one entry that never needs
maintenance and trusts every subdomain the vendor ever creates — including any they
later delegate to a fourth party. Listing twenty exact hosts is precise, auditable,
and a maintenance burden that pushes the org toward the CSP header size ceiling.
Default to exact; use a wildcard when hostnames genuinely rotate, and record that
reason in `description` so the choice survives its author.

**Per-context entries vs `All`.** Duplicating a record for `LEX` and `Communities`
documents exactly where the dependency exists and keeps each surface's policy
minimal. `All` is one record and grants the origin on every surface, including ones
the component does not run on today and surfaces added later. The duplication is
usually worth it — the second record is a copy-paste, and the narrower grant is the
whole point of the control.

**Browser-side call vs Apex proxy.** An LWC calling an external API directly is
fewer moving parts and lower latency, and it requires a Trusted URL plus whatever
CORS the vendor implements. Routing through Apex with a Named Credential moves the
call server-side: no Trusted URL, no CORS, credentials never reach the browser, and
the endpoint need not be exposed to the public internet. It costs an Apex class,
callout limits, and a round trip. Prefer the Apex path whenever the call carries a
credential or the endpoint is internal — and note that an internal service on plain
HTTP has *no* browser-side option at all, since CSP requires HTTPS for external
resources regardless of where they live.

**Relaxed CSP as an escape hatch.** It exists, it works, and it is site-wide.
Choosing it trades a specific, reviewable grant for a blanket one and destroys the
record of which origin was actually needed — which means the decision cannot be
walked back later even in principle. Treat it as a security-review decision with a
named risk owner, never as a build-time unblock.

## Anti-Patterns

1. **Ticking every directive.** The browser names the directive that blocked the
   request. An entry with six directives enabled where one was needed grants five
   capabilities nobody reviewed, and is indistinguishable from a correct entry.

2. **Omitting directive fields and relying on defaults.** The default for unset
   fields changed at API 50.0 and again at 59.0 — from "all true" to "img-src true"
   to "deployment rejected." Records created under API ≤ 49.0 with nothing ticked
   are *open* grants that a modern retrieve renders as all-false. Write every field
   explicitly.

3. **Ignoring context.** A URL trusted for Lightning Experience is not trusted for
   an Experience Builder site. The record looks configured, is marked Active, and
   does nothing for the surface that needs it.

4. **Reaching for Relaxed CSP.** Site-wide, effectively permanent, and it erases
   the information needed to tighten it again.

5. **Leaving the list to grow.** Trusted URLs for retired features are pure
   attack surface and consume header budget. The list must shrink as well as grow,
   on a cadence, using `description` to identify what is dead.

6. **Fixing one origin per incident.** A third-party widget typically needs its
   loader host, its API host, a frame host for challenge flows, an asset CDN, and a
   telemetry beacon. Enumerate from the vendor's CSP documentation in one pass, and
   test the failure and challenge paths — a 3-D Secure iframe fires only there.

7. **Trying to allow-list `script-src` on a Trusted URL.** There is no such field.
   The answer is a static resource loaded with `loadScript`.

8. **Setting `canAccessCamera` without the org-level `SecuritySettings` change.**
   The per-URL flag is inert unless `enablePermissionsPolicy` is `true` and
   `grantCameraAccess` is `TrustedUrls`.

9. **Confusing Trusted URLs with Remote Site Settings.** Browser-originated
   requests need the former; Apex callouts need the latter (or a Named Credential).
   Each error message names its own mechanism; read it.

## Official Sources Used

- Security for Lightning Components — Content Security Policy (the `'self'` defaults for `script-src`, `font-src`, `img-src`, `media-src`, `frame-src`, `style-src`, `connect-src`; the `unsafe-inline` prohibition and inline-handler example; the HTTPS requirement; the sample console violation message) — https://developer.salesforce.com/docs/platform/lightning-components-security/guide/content-security-policy-intro.html
- Metadata API Developer Guide — CspTrustedSite (`context` enum, the six `isApplicableTo*` fields, `canAccessCamera` / `canAccessMicrophone` and their `SecuritySettings` dependency, `endpointUrl` grammar and the malformed-URL note, the API-version default matrix, the 12 KB / 16 KB header size tip, directory and file suffix) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_csptrustedsite.htm
- Metadata API Developer Guide — SecuritySettings (`enablePermissionsPolicy`, `grantCameraAccess`, `grantMicrophoneAccess`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_securitysettings.htm
- Object Reference for the Salesforce Platform — CspTrustedSite — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_csptrustedsite.htm
- Salesforce Help — Manage Trusted URLs (Setup navigation path, CSP context and directive labels in the UI) — https://help.salesforce.com/s/articleView?id=platform.security_trusted_urls_manage.htm&type=5
- Salesforce Help — Manage Trusted URL and Browser Policy Violations — https://help.salesforce.com/s/articleView?id=xcloud.security_trusted_urls_csp_violations.htm&type=5
- Lightning Web Components Developer Guide — Use Third-Party JavaScript Libraries (`loadScript`, `lightning/platformResourceLoader`) — https://developer.salesforce.com/docs/platform/lwc/guide/js-third-party-library.html
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

<!-- UNVERIFIED: the console-phrase → directive mapping table in examples.md
     (e.g. "Refused to frame" → frame-src) is standard browser CSP behaviour
     defined by the W3C CSP specification and implemented by Chrome/Firefox,
     not by Salesforce. Only the "Refused to load the script ... because it
     violates the following Content Security Policy directive" example is
     quoted from Salesforce documentation. Exact wording varies by browser and
     browser version. -->
<!-- UNVERIFIED: the Experience Builder "Security Level: Relaxed CSP" setting
     name was not re-verified against current Salesforce Help in this pass; the
     option and its site-wide scope are long-standing Experience Cloud
     behaviour but the exact label may have changed. -->
<!-- UNVERIFIED: Stripe's specific host decomposition (js.stripe.com for the
     loader, api.stripe.com for the API, and a frame-src requirement for 3-D
     Secure) is a third-party vendor contract used illustratively. Confirm
     against Stripe's own CSP documentation before deploying. -->
