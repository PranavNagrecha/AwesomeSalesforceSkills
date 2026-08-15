# LLM Anti-Patterns — API-Only User Hardening

Mistakes AI assistants reliably make when asked to "set up an integration user in
Salesforce."

## Anti-Pattern 1: Cloning System Administrator

**What the LLM generates:** "Clone the System Administrator profile, name it
`Integration User`, and assign it to the service account."

**Why it happens:** It is the shortest path to an account that will not hit a
permission error during the build, and it appears in a great deal of older
integration documentation.

**Correct pattern:**

```
Start from the least-privilege baseline Salesforce ships for this purpose:

  Licence: Salesforce Integration user license
  Profile: Minimum Access - API Only Integrations
  Scope:   ONE permission set granting exactly the objects and operations
           this integration performs

A cloned admin profile carries every permission the original had, including
ones nobody can justify, and it is INVISIBLE in a permission review because it
looks purpose-built.

Note the licence boundary before designing: "One or more Salesforce Integration
user licenses are available by default in Enterprise, Unlimited, Performance,
and Developer editions, with more add-on licenses available to purchase."
Count the integrations against the org's available licences first.
```

**Detection hint:** the word "clone" applied to System Administrator, or any
integration profile that grants `ViewAllData` or `ModifyAllData`.

---

## Anti-Pattern 2: Username + Password + Security Token

**What the LLM generates:** a SOAP `login()` call, or a REST call using the
`password` grant type with a username, password, and appended security token.

**Why it happens:** It is the most-documented Salesforce authentication pattern by
volume, because it is the oldest.

**Correct pattern:**

```
Remove the password from the integration entirely.

  Server-to-server, simplest:
    OAuth 2.0 client credentials flow
      <isClientCredentialEnabled>true</isClientCredentialEnabled>
      <oauthClientCredentialUser>etl.warehouse@example.com</oauthClientCredentialUser>
    (both fields API 56.0 and later)

  Where a shared secret must never cross the wire:
    OAuth 2.0 JWT bearer flow - the client signs an assertion with a private
    key, Salesforce validates against an uploaded certificate

Three things a password-based integration inherits that nobody chose:
  - profile password expiry (ProfileSessionSetting.passwordExpiration; a
    cloned profile carries 30/60/90 and the job fails on that day)
  - the MFA requirement, since a username/password login is a direct login
  - a copyable credential sitting in a middleware config store

Salesforce's own guidance: "For security, we recommend blocking user-agent and
username-password flows."
```

**Detection hint:** `grant_type=password`, a `securityToken` parameter, or a SOAP
`login()` call in generated integration code.

---

## Anti-Pattern 3: Reaching for Modify All Data

**What the LLM generates:** "Grant **Modify All Data** so the integration can access
all records regardless of sharing."

**Why it happens:** The prompt says "the integration needs to see everything," and
this is the permission whose name matches that sentence.

**Correct pattern:**

```
Modify All Data grants read, create, edit, AND delete on EVERY object, bypasses
all sharing, and cannot be scoped. It makes the identity more powerful than most
administrators, with its credential in a config file.

Diagnose which object and which operation actually failed, then grant per object:

  <objectPermissions>
      <object>Opportunity</object>
      <allowRead>true</allowRead>
      <viewAllRecords>true</viewAllRecords>   <!-- sees all records, read only -->
      <allowCreate>false</allowCreate>
      <allowEdit>false</allowEdit>
      <allowDelete>false</allowDelete>
      <modifyAllRecords>false</modifyAllRecords>
  </objectPermissions>

viewAllRecords is the narrow, per-object, review-visible answer to "must see all
records." Use modifyAllRecords only on objects the job actually writes.
```

**Detection hint:** `ModifyAllData` or `ViewAllData` in a generated permission set,
or the phrase "needs to see all records" answered with an org-wide permission.

---

## Anti-Pattern 4: One Integration User for Everything

**What the LLM generates:** "Create a user `integration@company.com` and use it for
your integrations."

**Why it happens:** The prompt is usually singular ("set up an integration user"),
and reusing one account reads as tidy.

**Correct pattern:**

```
One user, one profile, one connected app, one named owner PER INTEGRATION.

A shared identity costs you:
  - attribution: Event Monitoring shows the account, not the system
  - blast radius: one compromise rotates every consumer at once
  - decommissioning: nobody dares delete an account six systems might use

The cost of the pattern is licences, which is why the licence count belongs in
the design conversation rather than at the end of it.

Detect an existing violation rather than asking:

  SELECT UserId, Application, LoginType, SourceIp, Status, COUNT(Id) logins
  FROM LoginHistory
  WHERE LoginTime = LAST_N_DAYS:7 AND UserId IN :integrationUserIds
  GROUP BY UserId, Application, LoginType, SourceIp, Status

Several distinct Application values under one UserId is a shared identity.
```

**Detection hint:** a single generic username offered for an unspecified number of
integrations, or a design with no per-integration owner recorded.

---

## Anti-Pattern 5: Setting Login IP Ranges Without Checking `ipRelaxation`

**What the LLM generates:** a complete profile IP restriction, presented as the
network control, with no mention of the connected app.

**Why it happens:** The two settings live on different Setup screens, are owned by
different teams, and therefore appear in different documents.

**Correct pattern:**

```
A connected app decides whether the profile's restriction applies to it at all:

  ENFORCE (default)      honours the org's IP restrictions
  BYPASS                 "Allows a user to run this app without org IP
                          restrictions"
  BYPASS_2FACTOR         bypasses given an app IP list + web server flow, or
                          identity verification on a new browser/device
  ENFORCE_RELAXREFRESH   enforces, but "bypasses these restrictions when the
                          connected app uses refresh tokens to get access
                          tokens"

Always emit <ipRelaxation>ENFORCE</ipRelaxation> explicitly in a generated
connected app, and include an audit step in any IP restriction plan. Anything
other than ENFORCE needs a named approver.
```

**Detection hint:** a generated `ConnectedApp` with no `<ipRelaxation>` element, or
an IP hardening plan with no connected app audit.

---

## Anti-Pattern 6: Assuming API Only User Is Just Another Permission

**What the LLM generates:** "Grant API Only User, and also assign a permission set
so an admin can log in and verify the data."

**Why it happens:** Permissions are normally additive, so a mode switch that
overrides everything else is out of pattern.

**Correct pattern:**

```
API Only User is a MODE, not a permission among many:

  "If a user has the API Only User permission, they can access Salesforce only
   via APIs, regardless of their other permissions."

Consequences to state whenever recommending it:
  - No UI access, ever. Not Visualforce, not Lightning Out, not Experience
    Cloud. The Spring '20 critical update closed the Lightning Out gap.
  - The login page is replaced: SecuritySettings.apiOnlyUserHomePageURL is
    "The URL to which users with the API Only User permission are redirected
    instead of the login page."
  - Verification must happen through the API, or as a different identity.

Before enabling on an EXISTING account, check whether anything renders UI as
that identity. If something does, that is a second integration sharing the
account, and it needs its own.
```

**Detection hint:** advice to "log in as the integration user to check," or a plan
that grants API Only User to an account with a Visualforce or Experience Cloud
dependency.

---

## Anti-Pattern 7: Treating Provisioning as the Whole Job

**What the LLM generates:** licence, profile, permission set, connected app — and
stops.

**Why it happens:** The prompt asks how to create the user, so the answer ends when
the user exists.

**Correct pattern:**

```
An integration identity is an operational asset with a lifecycle:

  Monitoring   Login History is capped - "up to 20,000 records of user logins
               for the past 6 months." For a frequent integration that is DAYS.
               Export on a schedule or stream to a SIEM. Decide this at
               provisioning; unretained data cannot be recovered.

  Alerting     Off-hours logins, unexpected source IPs, sudden query-volume
               changes, and any username-password subtype appearing after a
               migration.

  Rotation     A named owner, a secret rotation cadence, and a dual-range
               overlap procedure for IP changes.

  Review       Integration identities have no manager and no role, so they fall
               out of manager-based access reviews entirely. Give them their own
               review section: still live? permission set still minimal? IP
               range current? secret rotated? licence still needed?
```

**Detection hint:** an integration setup answer with no monitoring, no owner, and no
rotation cadence.

---

## Anti-Pattern 8: Declaring a Migration Complete When the New Flow Works

**What the LLM generates:** "Once the client credentials flow returns a token, the
migration is done — you can remove the old credentials."

**Why it happens:** The success criterion the prompt implies is "the new thing
works."

**Correct pattern:**

```
Adding the new path is safe; removing the old one is the migration. Legacy flows
keep working silently - a fallback branch, an old deployment, a second consumer
nobody documented.

Completion criterion: NO username-password subtype in Login History for the
integration identity for 30 days. Login History distinguishes the flow (client
credentials, user-agent including hybrid and ID-token variants,
username-password, and web-server including hybrid web-server).

Then block the legacy flows at the org level so the old path cannot resume, per
Salesforce's own recommendation to block user-agent and username-password flows.
```

**Detection hint:** a migration plan whose final step is "verify the new flow
works," with no observation window and no step that blocks the old flow.
