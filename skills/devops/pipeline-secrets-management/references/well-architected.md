# Well-Architected Notes — Pipeline Secrets Management

**Security:** the choice of credential type decides what a leak costs. An SFDX auth URL
embeds a refresh token — portable, non-expiring, and revocable only by disturbing the user
it belongs to. The JWT bearer flow moves the long-lived artefact to a private key you hold
and pairs it with a certificate on the connected app, so revocation is replacing one
certificate rather than an incident. That difference is the reason the JWT flow is the
documented approach for CI, where there is no human to complete a browser login.

**Security, blast radius:** one connected app and one integration user shared across
environments makes the credential that validates a pull request the credential that deploys
to production. Per-environment apps, per-environment integration users, and a permission set
sized to what the pipeline actually does keep a compromised runner from being an org
compromise. "System Administrator because it was quicker" is the single decision that turns
a leaked key into a takeover.

**Security, the log is a secret store you did not choose:** CI logs are broadly readable,
long-retained and routinely forwarded. Provider masking only covers values declared as
secrets, so anything the CLI *derives* — most importantly the auth URL printed by
`sf org display --verbose` — appears in the clear. Keeping `--verbose` and `set -x` out of
any step that touches a credential is worth more than most of the controls above it.

**Operational Excellence:** a certificate gives no gradual failure signal; it works until
the morning it does not. Rotating on a schedule rather than on the expiry date converts an
inevitable outage into a routine job, and ordering the rotation — upload, prove, publish,
retire — means every intermediate state still has a working credential. The temporary key
file needs the same discipline: `umask 077` so co-tenants on a shared runner cannot read it,
and a `trap ... EXIT` so a failed deploy does not leave it behind.

**Operational Excellence, detection:** prevention fails, so the unbounded quantity is the
time between a leak and its discovery. Push protection plus a local hook matching
`force://`, PEM headers and CLI state directories closes that window cheaply. A leaked
credential is compromise rather than a mistake to tidy away — rewriting history revokes
nothing, so the response is rotation first and cleanup second.

## Official Sources Used

- Authorize an Org Using the JWT Flow — the CI authorisation path and the `sf org login jwt` flags — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_jwt_flow.htm
- Authorization — the full set of CLI authorisation options and when each applies — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth.htm
- Resolve Common Authorization Errors — the failure modes to diagnose without printing a key — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_troubleshoot_auth_errors.htm
- Metadata API `deploy()` — `checkOnly` validation and the `testLevel` values, including `RunLocalTests` as the production default — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm
- org login sfdx-url command reference — what the auth URL is and therefore why it must not be committed — https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_org_login_sfdx-url.html
