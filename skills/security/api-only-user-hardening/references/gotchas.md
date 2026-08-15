# Gotchas — API-Only User Hardening

Non-obvious behaviours when provisioning and hardening integration identities.
Grounded in the Metadata API Developer Guide, the Salesforce Security Guide, and
Salesforce Help (Summer '26, API 67.0).

## Gotcha 1: API Only User Overrides Every Other Permission — Including Ones You Wanted

**What happens:** An admin grants a permission set to an API-only user so they can
"just check the record page," and nothing changes. Or worse: an identity is given
API Only User for hardening, and a Visualforce page or Lightning Out embed that
depended on it silently stops working.

> "If a user has the API Only User permission, they can access Salesforce only via
> APIs, regardless of their other permissions."
> — Metadata API Developer Guide, `OrgPreferenceSettings`, describing the Spring '20
> critical update that extended the restriction to Lightning Out

The login page itself is redirected — `SecuritySettings.apiOnlyUserHomePageURL` is
"The URL to which users with the API Only User permission are redirected instead of
the login page."

**When it occurs:** When someone treats API Only User as one permission among many
rather than as a mode switch, and when an integration identity is quietly doing
double duty behind a UI component.

**How to avoid:** Establish before flipping it whether anything renders UI as this
identity — Visualforce, Lightning Out, an Experience Cloud embed, a scheduled report
delivered as the user. If something does, that is a second integration wearing the
same identity, and it needs its own. Set `apiOnlyUserHomePageURL` deliberately so a
confused admin lands somewhere with an explanation rather than a blank page.

---

## Gotcha 2: The Client Credentials Flow Refuses a User Who Can Log In

**What happens:** A connected app is configured for the OAuth 2.0 client credentials
flow, bound to a convenient existing service account, and token requests fail.

> "`oauthClientCredentialUser` — The execution user for the OAuth 2.0 client
> credentials flow. Salesforce returns access tokens on behalf of this user. **This
> user must have the API Only permission.**"
> — Metadata API Developer Guide, `ConnectedAppOauthConfig`

And the other half of the pair:

> "`isClientCredentialEnabled` — If set to `true`, the connected app can use the
> OAuth 2.0 client credentials flow. To use the client credentials flow, you must
> also specify a user for `oauthClientCredentialUser`."

**When it occurs:** On the first client-credentials migration in an org, usually
after the credential-based flow has already been decommissioned in the client.

**How to avoid:** Read the constraint as a design instruction rather than an
obstacle: the platform will not let you attach a machine flow to an identity that
can also drive the UI. Provision the API-only user first, confirm the permission is
set, then configure the app. Both fields are API 56.0 and later, so a pipeline
pinned to an older `package.xml` version cannot deploy them at all.

---

## Gotcha 3: A Cloned Profile Inherits a Password Expiry Nobody Chose

**What happens:** A password-based integration works for exactly one password-policy
period and then fails with an authentication error, at 02:00, on a date with no
corresponding change record.

`ProfileSessionSetting.passwordExpiration` is a required field with values `0`, `30`,
`60`, `90`, `180`, `365`, where "`0`—If set to 0, the password never expires." A
profile cloned from a human profile carries that human policy, and there is no human
to receive the expiry warning.

**When it occurs:** With every cloned profile, and specifically on day 30/60/90 after
provisioning — long enough after go-live that nobody connects the two events.

**How to avoid:** The real fix is to remove the password: client credentials or JWT
bearer. Where that cannot happen in this release, set `passwordExpiration` to `0`
**as a deliberate, commented decision with an owner and a target date**, not as an
inherited default. A never-expiring password is a worse control than no password at
all, so it should read as debt in the source.

---

## Gotcha 4: A Connected App Can Cancel the Profile's IP Restriction

**What happens:** An integration profile is locked to two addresses, the security
review records it, and the credential works from anywhere — because the connected
app's OAuth policy was set to `BYPASS`.

| `ipRelaxation` | Effect |
|---|---|
| `ENFORCE` (default) | "Enforces the IP restrictions configured for the org, such as the IP ranges assigned to a user profile." |
| `BYPASS` | "Allows a user to run this app without org IP restrictions." |
| `BYPASS_2FACTOR` | Bypasses when the app has its own allowed IP list and uses the web server flow, or when the user passes identity verification on a new browser or device. |
| `ENFORCE_RELAXREFRESH` | Enforces, "however, this option bypasses these restrictions when the connected app uses refresh tokens to get access tokens." |

**When it occurs:** Whenever the connected app and the profile are configured by
different people, which is the normal division of labour.

**How to avoid:** Treat the profile's `loginIpRanges` and the app's `ipRelaxation` as
one control reviewed together. Anything other than `ENFORCE` needs a named approver
and a written reason. `ENFORCE_RELAXREFRESH` is the defensible middle for a job whose
token refresh comes from a rotating egress; `BYPASS` almost never is.

---

## Gotcha 5: The Salesforce Integration Licence Is Not a Free Upgrade

**What happens:** A design assumes every integration gets its own dedicated
identity, and the org runs out of Salesforce Integration licences partway through
the migration.

> "One or more Salesforce Integration user licenses are available by default in
> Enterprise, Unlimited, Performance, and Developer editions, with more add-on
> licenses available to purchase."
> — Salesforce Help, *Assign the New Salesforce Integration User License to Grant
> API Only Access*

"One or more ... by default" is not a number you can plan against, and additional
licences are a purchase.

**When it occurs:** Halfway through a "one identity per integration" programme,
after the first few are provisioned and the pattern is established.

**How to avoid:** Count the integrations and check the org's available licences
*before* committing to the pattern, and treat any shortfall as a procurement item
with a lead time. Note also the usage boundary, which is contractual rather than
technical: the Salesforce Integration permission set license "may not be used for
human users to access Salesforce data or features through any user interface." A
human using an integration licence is a licence-compliance problem as well as a
security one.

---

## Gotcha 6: One Shared Identity Destroys Attribution and Multiplies Rotation Cost

**What happens:** Event Monitoring shows 4M rows exported at 02:00 by
`integration@company.com`. Six systems use that account. Nobody can say which one
did it, and when one is compromised all six must be rotated simultaneously.

**When it occurs:** Under time pressure during onboarding, when creating a second
user looks like ceremony and reusing the first looks like efficiency.

**How to avoid:** One user, one profile, one connected app, one named owner per
integration. Detect existing violations with Login History rather than by asking:

```sql
SELECT UserId, Application, LoginType, SourceIp, Status, COUNT(Id) logins
FROM LoginHistory
WHERE LoginTime = LAST_N_DAYS:7 AND UserId IN :integrationUserIds
GROUP BY UserId, Application, LoginType, SourceIp, Status
```

Several distinct `Application` values under one `UserId` is a shared identity, and
the query is proof rather than opinion.

---

## Gotcha 7: Login History Holds Far Less Than You Think

**What happens:** An investigation asks "when did this integration first start
calling from that address," and the Login History page has already rolled over.

> "The Login History page shows up to 20,000 records of user logins for the past 6
> months. To see more records, download the information to a CSV or GZIP file."
> — Salesforce Security Guide, *Monitor Login History*

For an integration authenticating frequently, 20,000 records is days.

**When it occurs:** During the incident, which is the only time anyone looks.

**How to avoid:** Do not treat Login History as the system of record for integration
authentication. Export on a schedule, or stream login events to a SIEM. Decide this
while provisioning the identity, because the data you did not retain cannot be
recovered later.

---

## Gotcha 8: Legacy Auth Flows Keep Working After You "Migrate"

**What happens:** A migration to client credentials is declared complete. Months
later a security review finds username-password logins still occurring — an old
code path, a fallback branch, or a second deployment nobody knew about.

Login History surfaces the flow. The Security Guide enumerates the subtypes —
client credentials flows, user-agent flows including hybrid and ID-token variants,
username-password flows, and web-server flows including the hybrid web-server flow —
and gives an unambiguous instruction:

> "**Important:** For security, we recommend blocking user-agent and
> username-password flows."

**When it occurs:** Whenever a migration adds a new path without removing the old
one, which is the safe way to migrate and the unsafe way to finish.

**How to avoid:** Make "no username-password subtype in Login History for 30 days"
the completion criterion for the migration, not "the new flow works." Then block the
legacy flows at the org level so the old path cannot silently resume.

---

## Gotcha 9: `Modify All Data` Is Almost Never the Permission You Needed

**What happens:** The integration hits a record-visibility error, **Modify All Data**
makes it disappear, and the identity now has read, create, edit, and delete on every
object in the org — more power than most administrators, held in a middleware config
file.

**When it occurs:** During go-live troubleshooting, under time pressure, when the
error message names sharing rather than the permission that would fix it.

**How to avoid:** Diagnose which object and which operation actually failed. For an
extract that must see all records, the correct lever is `viewAllRecords` on that
object's `objectPermissions` — narrower, per object, and visible in a review:

```xml
<objectPermissions>
    <object>Opportunity</object>
    <allowRead>true</allowRead>
    <viewAllRecords>true</viewAllRecords>
    <allowCreate>false</allowCreate>
    <allowEdit>false</allowEdit>
    <allowDelete>false</allowDelete>
    <modifyAllRecords>false</modifyAllRecords>
</objectPermissions>
```

Add an assertion to your release checks that no integration permission set grants
`ViewAllData` or `ModifyAllData`, so a future troubleshooting session cannot
reintroduce it quietly.

---

## Gotcha 10: The Integration User Is Invisible in Most Access Reviews

**What happens:** A quarterly access review covers human users by manager and by
role. Integration identities have no manager and no role, so they fall out of the
report entirely and are never re-certified.

**When it occurs:** In every org whose access review process was designed around
people, which is every org.

**How to avoid:** Give each integration identity a named human owner recorded
somewhere queryable — a custom field on User, or a custom object keyed to the
connected app — and include integration identities as a distinct section of the
access review with their own questions: is the integration still live, is the
permission set still minimal, is the IP range still correct, when was the secret last
rotated, and is the licence still needed. Put the owner and the renewal date in the
permission set's `description` too, so the answer travels with the metadata.
