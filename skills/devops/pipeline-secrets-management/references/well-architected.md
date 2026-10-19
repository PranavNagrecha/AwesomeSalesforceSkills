# Well-Architected Notes — Pipeline Secrets Management

**Security:** the choice of credential type decides what a leak costs. An SFDX auth URL
contains all the information needed to authorize the org, so the value alone is the
credential. The JWT bearer flow moves the long-lived artefact to a private key you hold
and pairs it with a certificate on the external client app (or connected app), so revocation
is replacing one certificate rather than an incident. That difference is the reason the JWT flow is the
documented approach for CI, where there is no human to complete a browser login.

**Security, blast radius:** one app and one integration user shared across
environments makes the credential that validates a pull request the credential that deploys
to production. Per-environment apps, per-environment integration users, and a permission set
sized to what the pipeline actually does keep a compromised runner from being an org
compromise. "System Administrator because it was quicker" is the single decision that turns
a leaked key into a takeover.

**Security, the log is a secret store you did not choose:** CI logs are broadly readable,
long-retained and routinely forwarded. Provider masking only covers values declared as
secrets, so anything the CLI prints on request — `sf org auth show-sfdx-auth-url`,
`show-access-token`, or `sf org display` with `SF_TEMP_SHOW_SECRETS=true` — appears in the
clear. Keeping those commands and `set -x` out of any step that touches a credential is worth
more than most of the controls above it.

**Operational Excellence:** a certificate gives no gradual failure signal; it works until
the morning it does not. Rotating on a schedule rather than on the expiry date converts an
inevitable outage into a routine job, and ordering the rotation — prove the new key on an idle app, publish, then
retire the old certificate — means every intermediate state still has a working credential. The temporary key
file needs the same discipline: `umask 077` so co-tenants on a shared runner cannot read it,
and a `trap ... EXIT` so a failed deploy does not leave it behind.

**Operational Excellence, detection:** prevention fails, so the unbounded quantity is the
time between a leak and its discovery. Push protection plus a local hook matching
`force://`, PEM headers and `.ecaGlblOauth` files closes that window cheaply. A leaked
credential is compromise rather than a mistake to tidy away — rewriting history revokes
nothing, so the response is rotation first and cleanup second.

## Official Sources Used

Corpus: Summer '26 (API 67.0) PDFs; `sfdx_dev.txt` is the Salesforce DX Developer Guide fetched from resources.docs.salesforce.com/262 and converted with `pdftotext -layout`. Line numbers are `grep -n` positions.

- `sfdx_dev.txt` L2855–2871 — authorization options (web, JWT for CI, SFDX URL for automated environments) and the high assurance session restriction on headless login (Core Concepts table, gotcha 5).
- `sfdx_dev.txt` L2924–2934 and L2948–2970 — orgs need an external client app (preferred) or a connected app; JWT steps; connected app required for a Dev Hub that runs `org create scratch|sandbox` (gotcha 4).
- `sfdx_dev.txt` L3091–3172 — creating the external client app: scopes `api`, `web`, `refresh_token, offline_access`; Enable JWT Bearer Flow; certificate upload; "Admin approved users are pre-authorized" (Core Concepts, gotcha 3, rotation-runbook.md).
- `sfdx_dev.txt` L3071–3113 — `server.key` / `server.crt` roles and the 365-day self-signed certificate example (gotcha 7).
- `sfdx_dev.txt` L3421–3430 and L3520–3524 — `sf org login sfdx-url` for CI; the URL contains all the information needed to authorize the org (gotcha 1, anti-pattern 1).
- `sfdx_dev.txt` L3446–3449 and L3494–3530 — secrets hidden from `sf org display`; `sf org auth show-*` commands print them, `--json`/`--no-prompt` bypass the prompt, `SF_TEMP_SHOW_SECRETS` workaround (gotcha 2, anti-pattern 2).
- Metadata API Developer Guide (`api_meta.txt`) L64568–64580 — `ExtlClntAppGlobalOauthSettings` holds sensitive consumer information that can't be packaged and must not be added to source control (gotcha 6, checker).
- `api_meta.txt` L63429–63558 — `ExternalClientApplication` header type, `.eca` suffix, sample definition (SKILL.md XML fence).
- `api_meta.txt` L35296–35321 — connected app `consumerSecret` and `isAdminApproved` default false (gotchas 3 and 6).
- `api_meta.txt` L3143–3163 — `NoTestRun` applies only to development environments; `RunLocalTests` is the default for production deployments with Apex (examples.md).
- Object Reference (`object_reference.txt`) L176673 — `LoginHistory.Application` records the application used to access the org (Review Checklist).
