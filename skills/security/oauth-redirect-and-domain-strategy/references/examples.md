# Examples — OAuth Redirect and Domain Strategy

Every OAuth failure in Salesforce that is not a permission problem is a *string
matching* problem: the `redirect_uri` the client sent is not one of the strings
stored on the connected app, or the login host the client used is not the one the
org actually serves.

Grounded in the Metadata API Developer Guide (`ConnectedApp`,
`ExternalClientApplication`) and Salesforce Help (Summer '26, API 67.0).

---

## The three strings that have to line up

| String | Owned by | Where it lives |
|---|---|---|
| **Login host** | The org | `https://<mydomain>.my.salesforce.com` (production), `https://<mydomain>--<sandbox>.sandbox.my.salesforce.com` (sandbox) |
| **`redirect_uri`** | The client | Sent on the authorize request and again on the token request |
| **Callback URL** | The connected app | `ConnectedAppOauthConfig.callbackUrl` — the allow-list `redirect_uri` is matched against |

> "`callbackUrl` — Required. The endpoint that Salesforce calls back to your
> connected app during OAuth. It's the OAuth `redirect_uri`."
> — Metadata API Developer Guide, `ConnectedAppOauthConfig`

---

## Example 1: One connected app, every environment, in one field

**Context:** A single web application is deployed to production, UAT, and two
developer environments. Each deployment has its own callback host.

**Problem:** The team creates one connected app per environment "so each has its own
callback," which triples the consumer keys the client must manage, and then
discovers that a consumer key cannot be changed after creation:

> "In API version 32.0 and later, you can set this field's value only during
> creation. After you define and save the value, it can't be edited. The value must
> be alphanumeric, can't contain special characters or spaces, and must be between
> 8–256 characters. Consumer keys must be globally unique."
> — `ConnectedAppOauthConfig.consumerKey`

**Solution:** `callbackUrl` holds a list.

> "You can enter multiple callback URL values. At run time, Salesforce validates the
> callback URL specified by the app by matching it with one of the values. You must
> separate each callback URL with line breaks. To enter a new line programmatically,
> use the `\r` line break character."

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Order Portal</label>
    <contactEmail>platform-team@example.com</contactEmail>
    <description>Customer order portal. One app, four deployments.</description>
    <oauthConfig>
        <callbackUrl>https://orders.example.com/oauth/callback
https://uat.orders.example.com/oauth/callback
https://dev1.orders.example.com/oauth/callback
http://localhost:3000/oauth/callback</callbackUrl>
        <isPkceRequired>true</isPkceRequired>
        <scopes>
            <scopes>Api</scopes>
            <scopes>RefreshToken</scopes>
        </scopes>
    </oauthConfig>
    <oauthPolicy>
        <ipRelaxation>ENFORCE</ipRelaxation>
        <refreshTokenPolicy>infinite</refreshTokenPolicy>
    </oauthPolicy>
</ConnectedApp>
```

Note the literal newlines inside the element — that is the documented separator, not
a comma and not a space. Programmatically, join with `\r`.

**Why it works:** one consumer key, four deployments. At runtime Salesforce matches
the incoming `redirect_uri` against the list and accepts any exact member.

**The `localhost` entry** is a deliberate, reviewable decision rather than an
oversight: it lets developers run the flow locally, and it means anyone who can run
something on a developer's machine can complete an authorization. Keep it in
non-production connected apps, and if it must exist in production, record why and
when it will be removed.

---

## Example 2: Matching is exact — the failures that look like configuration bugs

**Context:** The callback URL is stored as `https://orders.example.com/oauth/callback`.
Authorization fails.

**Problem:** All four of these are *different strings* from the stored value, and any
one of them fails the match:

```text
https://orders.example.com/oauth/callback/          trailing slash
https://Orders.example.com/oauth/callback           host case (path case matters too)
http://orders.example.com/oauth/callback            scheme
https://orders.example.com:443/oauth/callback       explicit default port
```

The documented behaviour is a match against one of the stored values, with no
prefix, wildcard, or normalisation semantics offered. The practical rule is: the
string the client sends must be byte-identical to a stored line.

**Query parameters are the subtle one.** Many OAuth libraries append state or
tracking parameters to the redirect they send. If your library does that, the
`redirect_uri` is no longer the stored string. Use the `state` parameter — which is
carried separately by the protocol and is *not* part of the redirect URI — to pass
anything you need round-tripped.

### Diagnosis, in order

1. **Log the exact `redirect_uri` the client sends**, from the client, on both the
   authorize *and* the token request. Do not read it from a config file; read it
   from the wire. The two requests must send the same value.
2. **Copy the stored value out of the connected app** into the same buffer and
   compare character by character. Trailing whitespace in the stored value is
   invisible in the UI and is a real cause.
3. **Confirm the environment.** A UAT client pointing at a production connected app
   is the most common version of this, and the error is identical.

**Why this matters more than it should:** the failure surfaces as a browser
redirect with an error parameter rather than as a Salesforce log entry, so there is
often nothing on the Salesforce side to look at. The client's own logs are the
primary evidence.

---

## Example 3: Login host per environment

**Context:** The client library has a single `loginUrl` configuration value.

**Problem:** `login.salesforce.com` and `test.salesforce.com` still work for initial
authentication but redirect to the org's My Domain. Some OAuth libraries follow that
redirect cleanly; others cache the pre-redirect host, or drop the `state` parameter
across it, and produce failures that look intermittent.

**Solution — point clients at the org's My Domain directly.**

| Environment | Login host |
|---|---|
| Production | `https://acme.my.salesforce.com` |
| Full/partial/dev sandbox `uat` | `https://acme--uat.sandbox.my.salesforce.com` |
| Sandbox `dev1` | `https://acme--dev1.sandbox.my.salesforce.com` |

The sandbox format is `https://<mydomain>--<sandboxname>.sandbox.my.salesforce.com`.
Enhanced domains — "the current version of My Domain that meets the latest browser
requirements" — are what produce these formats.

**Make the host configuration, not code:**

```javascript
// WRONG — the sandbox name is embedded in a build artifact, so a refresh
// under a different name, or a new sandbox, needs a code change.
const LOGIN_URL = 'https://acme--uat.sandbox.my.salesforce.com';

// RIGHT — one environment variable, set per deployment.
const LOGIN_URL = process.env.SF_LOGIN_URL;
if (!LOGIN_URL) {
    throw new Error('SF_LOGIN_URL is required');
}
```

**Why it works:** no redirect bounce, so no library-specific redirect behaviour to
debug, and the environment is a deployment concern rather than a build concern.

**The identity URL follows the same shape** — a SAML issuer of
`https://mydomainname.my.salesforce.com` appears in the platform's own metadata
samples. Anything that hardcodes an instance-based host (`na123`, `eu45`) is
pre-My-Domain and will break.

---

## Example 4: PKCE, and the default that changed underneath you

**Context:** A mobile app and a single-page application both use the authorization
code flow. Neither can keep a client secret confidential.

**Problem:** Without PKCE, an attacker who intercepts the authorization code — via a
custom URL scheme hijack on mobile, or a redirect leak in a browser — can exchange it
for a token.

**Solution:**

```xml
<oauthConfig>
    <callbackUrl>com.example.orders://oauth/callback</callbackUrl>
    <isPkceRequired>true</isPkceRequired>
</oauthConfig>
```

The field's own description explains the mechanism and the recommendation:

> "Determines whether the Proof Key for Code Exchange (PKCE) extension is required
> for variations of the OAuth 2.0 authorization code flow configured for the
> connected app, including the web server flow and Authorization Code and Credentials
> Flow. For public client apps that can't keep the consumer secret confidential, such
> as mobile apps, the PKCE extension helps ensure that the client that initiates an
> authorization flow is the same client that completes it. For this reason, we always
> recommend implementing PKCE for public clients. We also strongly recommend that you
> implement PKCE for private clients."
>
> "If set to `true`, the PKCE extension is required and any authorization code flow
> variations that don't implement it fail. If set to `false`, you can still implement
> PKCE but it isn't required."

**The default differs between the two app models**, which is a real migration
hazard:

| Type | `isPkceRequired` default |
|---|---|
| `ConnectedApp` | **`false`** — "The default value is `false`." (API 59.0 and later) |
| `ExternalClientApplication` | **`true`** — "If set to `true` (default) Proof Key for Code for Exchange (PKCE) is required for OAuth integration." |

The two defaults are opposites.

So a client that worked against a connected app can fail immediately against an
External Client App, because PKCE is now required and the client never implemented
it. Always write `isPkceRequired` explicitly on both, and verify the client sends
`code_challenge` on authorize and `code_verifier` on token exchange before flipping
it on.

---

## Example 5: The redirect matrix as a reviewable artifact

**Context:** An enhanced-domains cutover, or a sandbox refresh, is coming.

**Problem:** Nobody can enumerate which strings will change and who owns each one,
so the change is executed by discovery.

**Solution:** build the matrix before touching anything.

| Connected app | Env | Login host | `redirect_uri` (client sends) | Stored callback | Owner | Verified |
|---|---|---|---|---|---|---|
| Order Portal | Prod | `https://acme.my.salesforce.com` | `https://orders.example.com/oauth/callback` | ✅ line 1 | platform-team@ | 2026-08-14 |
| Order Portal | UAT | `https://acme--uat.sandbox.my.salesforce.com` | `https://uat.orders.example.com/oauth/callback` | ✅ line 2 | platform-team@ | 2026-08-14 |
| Warehouse ETL | Prod | `https://acme.my.salesforce.com` | *(client credentials — no redirect)* | n/a | data-platform@ | 2026-08-14 |
| Partner Portal | Prod | `https://acme.my.salesforce.com` | `https://partner.vendor.example.com/sf/cb` | ✅ line 1 | vendor, via alliances@ | ⚠ vendor confirms |

Then sweep for hardcoded hosts, because a domain change is only partly a Salesforce
change:

```bash
# Instance-based hosts (pre-My-Domain) and hardcoded My Domain strings.
grep -rEn '\.(na|eu|ap|cs|um)[0-9]+\.salesforce\.com' .
grep -rn 'my.salesforce.com' --include='*.cls' --include='*.js' \
                              --include='*.html' --include='*.xml' .
```

Search the same patterns in places that are not the repository:

- Apex string literals, Named Credentials, Remote Site Settings, Trusted URLs
- LWC and Aura `fetch` targets
- Email template absolute links
- **External systems**: webhook registrations, IdP SAML/OIDC configuration, partner
  allow-lists. These are the ones that bite, because they are outside your change
  control and their owners are outside your organisation.

**Why it works:** the matrix turns "some things might break" into a finite list with
owners and verification dates, which is the only form in which a domain change can
be reviewed rather than survived.

---

## Anti-Pattern: Creating a connected app per environment

**What practitioners do:** one connected app in each org — production, UAT, each
sandbox — each with a single callback URL.

**What goes wrong:** the consumer key is unique per app and, from API 32.0,
immutable once saved. Every environment now has a different client id and secret,
so the client's configuration diverges per environment, secret rotation is N
operations instead of one, and a sandbox refresh destroys the sandbox's app and its
key — breaking every client pointed at it until someone reissues and redistributes
credentials.

**Correct approach:** one connected app definition, deployed to every org, with every
environment's callback URL as a line in `callbackUrl`. The client then varies only
its login host, which is an environment variable. Where a sandbox genuinely needs a
different consumer key — for example to keep production and sandbox tokens
non-interchangeable — make that an explicit decision with the extra rotation cost
written down, not the accidental consequence of clicking New in each org.
