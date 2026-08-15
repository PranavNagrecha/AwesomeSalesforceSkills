# Examples — API-Only User Hardening

An integration identity is a credential that never sleeps, never rotates itself,
and usually has more access than any human in the org. Hardening it is four
decisions — licence, profile, permission scope, and authentication flow — plus a
monitoring commitment.

Grounded in the Metadata API Developer Guide, the Salesforce Security Guide, and
Salesforce Help (Summer '26, API 67.0).

---

## The API Only User permission is absolute

> "If a user has the API Only User permission, they can access Salesforce only via
> APIs, regardless of their other permissions."
> — Metadata API Developer Guide, `OrgPreferenceSettings`
> (`enableApiUserLtngOutAccessPref`, describing the Spring '20 critical update)

"Regardless of their other permissions" is the important half. Granting a UI-facing
permission set to an API-only user does not open the UI; it only widens what the API
can reach. And the login page itself is redirected:

> "`apiOnlyUserHomePageURL` — The URL to which users with the API Only User
> permission are redirected instead of the login page."
> — Metadata API Developer Guide, `SecuritySettings`

So an admin trying to "just log in as the integration user to check something"
cannot, by design. That is the control working.

---

## Example 1: Provision a new ETL integration identity

**Context:** A data warehouse extracts 10M rows nightly through Bulk API 2.0. It
needs read access to eight objects and nothing else.

**Problem:** The org's existing pattern is to clone the System Administrator profile
"so it doesn't break," and to reuse one `integration@company.com` account across
every integration.

**Solution — four decisions, in order.**

### 1. Licence: Salesforce Integration

The Salesforce Integration user license exists precisely for this. Salesforce Help
is explicit about the boundary:

> "The Salesforce Integration API permission set license extends and restricts
> specific user and object permissions for system-to-system integrations. It may not
> be used for human users to access Salesforce data or features through any user
> interface."

> "One or more Salesforce Integration user licenses are available by default in
> Enterprise, Unlimited, Performance, and Developer editions, with more add-on
> licenses available to purchase."

Check what the org actually has before designing around it — the default allocation
is small, and this is a procurement conversation, not a Setup click.

### 2. Profile: `Minimum Access - API Only Integrations`

Salesforce ships this profile for use with the Integration licence. Start there, not
from a clone of an existing profile. A cloned profile carries every permission the
original had, including ones nobody can now justify, and the clone is invisible in a
permission review because it looks purpose-built.

### 3. Scope: one permission set, eight objects, read only

```xml
<!-- permissionsets/ETL_Warehouse_Extract.permissionset-meta.xml (excerpt) -->
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>ETL Warehouse Extract</label>
    <description>Read-only extract scope for the nightly warehouse job.
        Owner: data-platform@example.com. Reviewed 2026-08.</description>
    <hasActivationRequired>false</hasActivationRequired>

    <objectPermissions>
        <object>Account</object>
        <allowRead>true</allowRead>
        <allowCreate>false</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>true</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
    <!-- repeat per object; do NOT grant modifyAllRecords for a read job -->

    <userPermissions>
        <name>ApiEnabled</name>
        <enabled>true</enabled>
    </userPermissions>
</PermissionSet>
```

`viewAllRecords` on the object is the correct lever for an extract job that must see
everything — it is narrower than the org-wide **View All Data**, and it is visible
per object in a review. Reaching for **Modify All Data** because the extract "needs
to see everything" grants write and delete on every object in the org.

### 4. Authentication: OAuth 2.0 client credentials flow

```xml
<!-- connectedApps/ETL_Warehouse.connectedApp-meta.xml -->
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>ETL Warehouse</label>
    <contactEmail>data-platform@example.com</contactEmail>
    <description>Nightly Bulk API 2.0 extract to the warehouse.</description>
    <oauthConfig>
        <callbackUrl>https://warehouse.example.com/oauth/callback</callbackUrl>
        <isClientCredentialEnabled>true</isClientCredentialEnabled>
        <oauthClientCredentialUser>etl.warehouse@example.com</oauthClientCredentialUser>
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

Two documented constraints on these fields:

> "`isClientCredentialEnabled` — If set to `true`, the connected app can use the
> OAuth 2.0 client credentials flow. To use the client credentials flow, you must
> also specify a user for `oauthClientCredentialUser`." (API 56.0 and later)

> "`oauthClientCredentialUser` — The execution user for the OAuth 2.0 client
> credentials flow. Salesforce returns access tokens on behalf of this user. **This
> user must have the API Only permission.**"

That last sentence is the design closing itself: the platform will not let you bind
the client credentials flow to a user who can also log into the UI.

**Why it works:** there is no password in the integration at all. The client
obtains a token with a client id and secret, and the token acts as one specific,
UI-incapable identity with eight read grants.

---

## Example 2: Remove the password from the equation

**Context:** A legacy integration authenticates with username + password + security
token via the SOAP `login()` call.

**Problem:** Three separate failure modes, all of which arrive without warning:

1. **Password expiry.** The profile's password policy applies to the integration
   user like any other. `ProfileSessionSetting.passwordExpiration` accepts
   `0`, `30`, `60`, `90`, `180`, `365`, where "`0`—If set to 0, the password never
   expires." A cloned profile inherits whatever the original had, so the job breaks
   on day 90 with an authentication error and no prior signal.
2. **MFA.** A username/password login is a direct login and is subject to the MFA
   requirement. There is no supported way to exempt an integration from that while
   still using a password.
3. **The credential is copyable.** A password plus token is a string that works from
   anywhere the IP rules allow, and it lives in whatever config store the middleware
   uses.

### WRONG — password-based, with a profile that expires it

```xml
<!-- profiles/ETL_Integration.profile-meta.xml -->
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Cloned from a human profile. passwordExpiration is inherited as 90.
         The nightly job will fail on day 90 with INVALID_LOGIN and nobody
         will connect the two events. -->
</Profile>
```

### RIGHT — no password in the flow at all

Use the client credentials flow (Example 1) or the JWT bearer flow. Both remove the
password from the integration entirely:

- **Client credentials** — the client holds a consumer key and secret and receives a
  token minted for `oauthClientCredentialUser`. Simplest for server-to-server.
- **JWT bearer** — the client holds a private key and signs an assertion; Salesforce
  validates it against an uploaded certificate. No shared secret ever crosses the
  wire, and rotation is a certificate swap.

If a password genuinely cannot be removed in this release, set the profile's
password policy to never expire **as an explicit, documented decision** rather than
inheriting it from a clone, and put the migration on the roadmap:

```xml
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <profileSessionSetting>
        <!-- 0 = never expires. Deliberate: this identity has no human to
             perform a rotation. Migrating to client credentials in Q4;
             owner data-platform@example.com. -->
        <passwordExpiration>0</passwordExpiration>
    </profileSessionSetting>
</Profile>
```

A never-expiring password is a worse control than no password, so treat that XML
comment as a debt marker with a date, not a solution.

---

## Example 3: Lock the identity to the caller's network

**Context:** The integration authenticates from a partner's provisioned NAT
addresses.

**Solution:** Login IP Ranges on the *integration profile only*, which is safe
precisely because the identity has no human to lock out.

```xml
<!-- profiles/Minimum_Access_API_Only_ETL.profile-meta.xml (excerpt) -->
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <loginIpRanges>
        <description>Warehouse primary NAT — owner data-platform@, renewal 2027-03</description>
        <startAddress>203.0.113.10</startAddress>
        <endAddress>203.0.113.10</endAddress>
    </loginIpRanges>
    <loginIpRanges>
        <description>Warehouse DR NAT — owner data-platform@, renewal 2027-03</description>
        <startAddress>198.51.100.20</startAddress>
        <endAddress>198.51.100.20</endAddress>
    </loginIpRanges>
</Profile>
```

Then make sure nothing cancels it. The connected app's OAuth policy decides whether
the profile restriction applies at all:

```xml
<oauthPolicy>
    <ipRelaxation>ENFORCE</ipRelaxation>
</oauthPolicy>
```

`ENFORCE` is the default and "Enforces the IP restrictions configured for the org,
such as the IP ranges assigned to a user profile." `BYPASS` — "Allows a user to run
this app without org IP restrictions" — silently undoes everything above.

**Why it works:** a leaked client secret is only usable from two addresses. Combined
with a UI-incapable identity and eight read grants, the blast radius of a full
credential compromise is "someone can read eight objects from the partner's data
centre," which is a survivable incident.

**If the partner cannot provide static egress**, say so plainly rather than
allow-listing a cloud provider's published range — that admits everyone with an
account at that provider. See `security/ip-relaxation-and-restriction`.

---

## Example 4: One identity per integration, and how to prove it

**Context:** An org has `integration@company.com` used by six systems.

**Problem:** When Event Monitoring shows 4M rows exported at 02:00, there is no way
to tell which of the six systems did it. When one is compromised, all six must be
rotated. When one is decommissioned, nobody dares delete the account.

**Solution:** one user, one profile, one connected app, one owner per integration.
The cost is licences; the benefit is that every question about the integration has
an answer.

**Proving it, as a query you can schedule:**

```sql
-- Which identities are actually calling, and from where?
SELECT UserId, Application, LoginType, SourceIp, Status, COUNT(Id) logins
FROM LoginHistory
WHERE LoginTime = LAST_N_DAYS:7
  AND UserId IN :integrationUserIds
GROUP BY UserId, Application, LoginType, SourceIp, Status
```

A single `UserId` showing several distinct `Application` values is a shared
identity. A `SourceIp` you do not recognise on an IP-restricted profile means the
restriction is being bypassed somewhere — check `ipRelaxation` first.

Login History also distinguishes the OAuth flow in use. The Security Guide lists the
subtypes it surfaces — client credentials flows, user-agent flows, username-password
flows, and web-server flows — and attaches an unambiguous recommendation:

> "**Important:** For security, we recommend blocking user-agent and
> username-password flows."

A username-password subtype appearing for an identity you believed was on client
credentials means an old code path is still live.

**Retention limit worth knowing:** "The Login History page shows up to 20,000
records of user logins for the past 6 months. To see more records, download the
information to a CSV or GZIP file." For a high-frequency integration, 20,000 logins
is days, not months — export or stream to a SIEM if you need real history.

---

## Anti-Pattern: Granting Modify All Data because "the integration needs to see everything"

**What practitioners do:** the integration hits a sharing-related error on one
object, and the fastest fix that makes it go away is **Modify All Data** on the
profile.

**What goes wrong:** the permission grants read, create, edit, and delete on *every*
object in the org, bypasses all sharing, and cannot be scoped. It also makes the
identity strictly more powerful than most administrators. The original problem was
almost always record visibility on one object, for which the correct lever is
`viewAllRecords` on that object's permission — narrower, per-object, and visible in
a permission review.

**Correct approach:** diagnose which object and which access level actually failed.
Grant `viewAllRecords` per object where the job genuinely needs to see all records;
grant `modifyAllRecords` per object only where it genuinely writes. Reserve org-wide
**View All Data** and **Modify All Data** for cases you can name, and never grant
them to an identity whose credential lives in a middleware config file.
