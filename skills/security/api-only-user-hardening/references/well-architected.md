# Well-Architected Notes — API-Only User Hardening

## Relevant Pillars

- **Security** — Primary pillar. An integration identity is the highest-value
  credential in most orgs: it is long-lived, it usually carries broad object access,
  and its secret sits in a config store outside Salesforce's control. Four controls
  compose to bound the damage of a full compromise — the API Only User mode (no UI,
  ever), a permission set scoped to named objects and operations, an IP restriction
  where the caller's address is genuinely static, and an authentication flow with no
  password in it. Each is independently weak; together they reduce a stolen
  credential to "someone can read eight objects from the partner's data centre."

- **Operational Excellence** — Integration identities have no manager and no role,
  so they fall out of every access-review process designed around people. The
  artifacts that make them governable are a named human owner recorded somewhere
  queryable, a rotation cadence for the secret, an alert on login failures, and a
  review section of their own. None of these are technical controls; all of them are
  the difference between an inventory and a shadow estate.

- **Reliability** — The failure modes are scheduled and silent. A cloned profile's
  password expiry fires on day 90 at 02:00 with no warning and no human to receive
  it. A partner's NAT rotation breaks authentication on a date nobody in Salesforce
  knows. Building for reliability here means removing the password entirely and
  putting renewal dates in the `description` of every IP range.

- **Performance** — Indirect: an integration granted **Modify All Data** bypasses
  sharing, which changes query plans and can turn a selective extract into a
  full-table scan. Scoping with per-object `viewAllRecords` keeps the access model —
  and therefore the optimiser's assumptions — legible.

## Architectural Trade-offs

**Salesforce Integration licence vs a full user licence.** The Integration licence
is purpose-built and carries a contractual boundary: it "may not be used for human
users to access Salesforce data or features through any user interface." That
restriction is the point — it makes accidental human reuse a compliance event rather
than a quiet convenience. The trade is availability: "One or more Salesforce
Integration user licenses are available by default in Enterprise, Unlimited,
Performance, and Developer editions, with more add-on licenses available to
purchase." A one-identity-per-integration design is a procurement conversation
before it is a Setup task.

**Client credentials vs JWT bearer.** Client credentials is simpler — a consumer key
and secret, a token minted for `oauthClientCredentialUser`, and the platform enforces
that this user holds the API Only permission. JWT bearer never puts a shared secret
on the wire and makes rotation a certificate swap, at the cost of key management on
the client side and a certificate expiry to track. For most server-to-server
integrations client credentials is right; where the client already has a key
management story, or where the secret would otherwise sit in a shared config store,
JWT bearer is materially stronger.

**One identity per integration vs a shared service account.** Sharing costs
licences up front and everything else later: attribution disappears from Event
Monitoring, one compromise forces simultaneous rotation of every consumer, and
nobody can safely decommission an account six systems might still use. The
separation is worth paying for and the payment is visible on day one, which is why
it is so often skipped.

**IP restriction vs accepting network mobility.** Where the partner has provisioned
static egress, a hard IP block on the integration profile is the strongest and
cheapest control available and is safe precisely because there is no human to lock
out. Where they have not, the honest answer is that this control is unavailable —
allow-listing a cloud provider's published range admits everyone with an account at
that provider and is worse than recording no control, because it stops the search
for a real one. Make static egress a contractual term during onboarding, not a
technical request during build.

**`viewAllRecords` vs `ViewAllData`.** Per-object `viewAllRecords` grants exactly
what an extract needs, is visible per object in a review, and survives an access
audit. Org-wide **View All Data** is one checkbox and covers every object including
ones added after the review. The per-object form is more XML and is the only version
you can defend line by line.

## Anti-Patterns

1. **Cloning System Administrator.** The clone carries every permission the original
   had and is invisible in a review because it looks purpose-built. Start from
   `Minimum Access - API Only Integrations`.

2. **Username, password, and security token.** Inherits password expiry from a
   cloned profile, is subject to the MFA requirement as a direct login, and leaves a
   copyable credential in a config store. Salesforce's own guidance is to block
   username-password flows.

3. **Granting Modify All Data to fix a visibility error.** Grants read, create,
   edit, and delete on every object and bypasses all sharing, when the actual problem
   was record visibility on one object.

4. **One shared service account.** Destroys attribution, multiplies rotation cost,
   and makes decommissioning impossible.

5. **Setting profile IP ranges without auditing `ipRelaxation`.** One connected app
   set to `BYPASS` cancels the restriction and the two settings live on screens owned
   by different teams.

6. **Treating API Only User as an ordinary permission.** It overrides every other
   permission and replaces the login page. Enabling it on an account that quietly
   renders UI somewhere breaks that path with no obvious cause.

7. **Stopping at provisioning.** Login History holds "up to 20,000 records of user
   logins for the past 6 months" — days, for a frequent integration. Monitoring,
   alerting, ownership, and rotation are part of the deliverable, and the retention
   decision must be made before the data is needed.

8. **Declaring a flow migration complete when the new flow works.** The old path
   keeps working silently. Completion is thirty days with no username-password
   subtype in Login History, followed by blocking the legacy flows.

## Official Sources Used

- Salesforce Help — Give Integration Users API Only Access — https://help.salesforce.com/s/articleView?id=platform.integration_user.htm&type=5
- Salesforce Help — Assign the New Salesforce Integration User License to Grant API Only Access (licence availability by edition; the "may not be used for human users" boundary) — https://help.salesforce.com/s/articleView?id=release-notes.rn_api_integration_license.htm&type=5
- Salesforce Help — Secure API Access with the New Least-Privilege User Profile (`Minimum Access - API Only Integrations`) — https://help.salesforce.com/s/articleView?id=release-notes.rn_api_new_user_profile.htm&type=5
- Salesforce Help — Integration Permission Sets — https://help.salesforce.com/s/articleView?id=platform.perm_sets_integration.htm&type=5
- Metadata API Developer Guide — ConnectedApp / ConnectedAppOauthConfig (`isClientCredentialEnabled`, `oauthClientCredentialUser` and its API Only requirement, `isPkceRequired`, `scopes`, `sessionTimeout`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_connectedapp.htm
- Metadata API Developer Guide — ConnectedApp OAuth policy `ipRelaxation` and its four values — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_connectedapp.htm
- Metadata API Developer Guide — SecuritySettings (`apiOnlyUserHomePageURL`, password `complexity`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_securitysettings.htm
- Metadata API Developer Guide — Profile / ProfileSessionSetting (`passwordExpiration` values including `0` = never expires, `passwordComplexity`, `loginIpRanges`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_profile.htm
- Metadata API Developer Guide — OrgPreferenceSettings, `enableApiUserLtngOutAccessPref` ("If a user has the API Only User permission, they can access Salesforce only via APIs, regardless of their other permissions") — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_orgpreferencesettings.htm
- Salesforce Security Guide — Monitor Login History (20,000-record / 6-month cap; OAuth flow subtypes; "For security, we recommend blocking user-agent and username-password flows") — https://help.salesforce.com/s/articleView?id=platform.security_login_history.htm&type=5
- Salesforce Security Guide — Salesforce Security Basics (MFA required for all logins) — https://help.salesforce.com/s/articleView?id=platform.security_overview.htm&type=5
- Salesforce Help — OAuth 2.0 Client Credentials Flow for Server-to-Server Integration — https://help.salesforce.com/s/articleView?id=platform.remoteaccess_oauth_client_credentials_flow.htm&type=5
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

<!-- UNVERIFIED: the exact number of Salesforce Integration user licences
     included by default per edition. Salesforce Help states "One or more ...
     available by default in Enterprise, Unlimited, Performance, and Developer
     editions"; no specific count was confirmed in this pass, and this package
     deliberately makes no numeric claim. A widely-repeated "5 free" figure
     appears in community sources and was NOT confirmed against Salesforce
     documentation - do not reintroduce it without a citation. -->
<!-- UNVERIFIED: the assertion that a username/password (SOAP login or
     grant_type=password) integration login is subject to the MFA requirement.
     Salesforce states unconditionally that "all logins" require MFA and
     recommends blocking username-password flows, but no source consulted in
     this pass states the interaction for API-only identities explicitly.
     Treat the recommendation to migrate off passwords as well grounded and the
     specific MFA-blocks-this-integration mechanism as inference. -->
<!-- UNVERIFIED: the OAuth 2.0 JWT bearer flow details (client signs an
     assertion with a private key, validated against a certificate uploaded to
     Salesforce) are stated from general platform knowledge and were not
     re-verified against the OAuth flow documentation in this pass. -->
