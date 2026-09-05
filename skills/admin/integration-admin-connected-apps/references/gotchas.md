# Gotchas — Integration Admin: Connected Apps

## Gotcha 1: Pre-Authorized Mode Blocks All Users Until Profile/Permission Set Assignment Is Made

**What happens:** After setting "Admin approved users are pre-authorized" in OAuth Policies, all OAuth authentication attempts — including the admin's — return a generic OAuth error such as `error=access_denied` or `error=invalid_grant`. No specific message indicates the profile assignment is missing.

**When it occurs:** Immediately after saving the "Admin approved users are pre-authorized" setting when no Profile or Permission Set has been assigned the connected app. Common when admins follow documentation steps in the wrong order (set policy before assignment).

**How to avoid:** Always complete the profile/permission set assignment in the same configuration session as setting pre-authorized mode. After saving the OAuth policy, immediately navigate to the Profile > Connected App Access or Permission Set > Assigned Apps and enable the connected app. Test authentication before considering the configuration complete.

---

## Gotcha 2: Uninstalled Connected Apps Blocked by Default (September 2025)

**What happens:** Integrations that were using a connected app that was subsequently uninstalled continue to fail silently with OAuth errors after September 2025. Previously, uninstalled connected app tokens continued to work. After the September 2025 policy change, Salesforce blocked uninstalled connected apps by default for most user contexts.

**When it occurs:** Any org that has connected apps that were installed from the AppExchange or a managed package and later uninstalled, but whose OAuth tokens are still being used by active integrations (ETL tools, middleware, browser extensions). Common in orgs that have been on Salesforce for several years with multiple integration generations.

**How to avoid:** Audit connected apps in Setup > Apps > Connected Apps > OAuth and Connected App Usage. Review which apps have active OAuth sessions. For any app still in active use that has been uninstalled, re-authorize the app or migrate the integration to a new connected app. Proactively run this audit quarterly to identify orphaned integrations before they fail. Note that the historical override for this — the Use Any API Client permission — no longer works for uninstalled apps in orgs with API Access Control enabled; see Gotcha 4.

---

## Gotcha 3: EventLogFile Requires Event Monitoring Add-On — Not Available in Standard Audit Trail

**What happens:** An admin tries to investigate connected app authentication issues using Setup > Security > Login History. Login History shows the integration user's login events but does not show OAuth token grants, refreshes, revocations, or the specific connected app used for each authentication. The admin cannot determine whether token issues are the cause of integration failures.

**When it occurs:** Any attempt to investigate OAuth token-level events using the standard Setup UI without the Event Monitoring add-on. Admins from orgs without this add-on often spend hours investigating the wrong place.

**How to avoid:** For thorough OAuth investigation, the Event Monitoring add-on is required. If the add-on is not available, partial information is available via: (a) the integration user's Session ID in Login History, (b) manually triggering a test authentication and checking for errors in the API response, and (c) enabling Field Audit Trail on the ConnectedApplication object if available. For production integrations with OAuth-sensitive flows, budget for the Event Monitoring add-on.

---

## Gotcha 4: "Use Any API Client" No Longer Self-Authorizes Uninstalled Apps (Week of December 8, 2025)

**What happens:** A user holds **Use Any API Client** — for years the blanket override for connected-app restrictions — and still cannot complete OAuth authorization for an app that is not installed in the org. Salesforce "is changing the behavior of the 'Use Any API Client' permission so that users with this permission are restricted from self-authorizing uninstalled connected apps," "Starting the week of December 8, 2025." The permission's other capabilities are untouched, so it still looks correct in a permission-set audit.

**When it occurs:** Salesforce publishes the resulting behavior only for orgs that have the API Access Control preference **"For admin-approved users, limit API access to only allowlisted connected apps"** enabled, and says nothing about orgs where that preference is off. Do not read that silence as "nothing to do": uninstalled connected apps are blocked by default for most users under the September 2025 policy (Gotcha 2) independently of this preference, so confirm behavior in a sandbox rather than assuming the old override still works. Published behavior for preference-enabled orgs:

| Use Any API Client | Approve Uninstalled Connected Apps | Self-authorize an uninstalled app |
|---|---|---|
| TRUE | FALSE | Blocked — this is the change |
| TRUE | TRUE | Allowed |
| FALSE | TRUE | Allowed |
| FALSE | FALSE | Blocked |

Only *new* authorization requests are blocked: "The existing active sessions of uninstalled connected apps remain unaffected." The failure therefore surfaces later, when a client re-authorizes, not on the day of the change.

**How to avoid:** Install and allowlist the connected app in the org — that is the remedy Salesforce directs admins to. Reserve **Approve Uninstalled Connected Apps** (introduced September 2025) for the few admins or developers who must test an app before installing it; Salesforce states it "should only be assigned to highly trusted users, such as administrators and those involved in managing or testing connected app integrations." This is a dated security enforcement, not a versioned feature, so it applies regardless of the org's release and will not appear in a seasonal release-notes diff.

---

## Gotcha 5: There Is No `delete()` on `OauthToken` — Revocation Is an HTTP Call, and It Does Not End a Live Session

**What happens:** A runbook says "revoke the integration's token," so someone writes a Flow, an Apex
`delete`, or a Data Loader job against `OauthToken` — and every one of them fails. The Object
Reference lists the object's supported calls as exactly two: `describeSObjects()` and `query()`.
Revocation is not DML. The documented mechanism is the row's own `DeleteToken` field — "a token that
can be used at the revoke OAuth token endpoint to remove this token" — sent to the endpoint:
"the URL `https://MyDomainName.my.salesforce.com/services/oauth2/revoke?token=(the Delete Token)`
causes the deletion of the token."

The second half bites during incident response. Revoking one grant removes the token; it is not
documented as terminating a session already running. Salesforce states that boundary for the
adjacent control, `refreshTokenPolicy` `zero`: "The refresh token is invalid immediately. The user
can use the current session (access token) already issued, but can't obtain a new session when the
access token expires." The only control the guide describes as ending live sessions is
`sessionPolicy/policyAction` `Block`, which "ends all current user sessions with the connected app
and prevents all new sessions."
<!-- UNVERIFIED (2026-09-04): the guides do not state, for the revoke endpoint specifically, whether
an access token already issued keeps working until it expires. The `zero` refresh-token-policy
wording above is the closest documented statement and describes a different control. Confirm in a
sandbox before writing a "revocation is immediate" claim into an incident runbook. -->

**When it occurs:** Whenever a revoke step is written by someone who assumed a queryable sObject is a
writable one, and again at the moment a security incident needs a hard stop rather than a token
removal.

**How to avoid:** Put the two paths in the runbook explicitly and separately. Per-grant: query
`DeleteToken` (as a user with Customize Application, or you will only see your own rows), then call
the revoke endpoint with it. Org-wide hard stop: **Block** the app on the Connected Apps OAuth Usage
page, or deploy `policyAction` `Block`. Rehearse the per-grant path once in a sandbox and record the
date — see `templates/connected-app-review-checklist.yaml`. Token lifecycle mechanics in depth are in
`security/oauth-token-management`.

---

## Gotcha 6: `OauthToken` Stops Returning Rows at 2,500, So Your Token Inventory Silently Under-Reports

**What happens:** A quarterly review queries `OauthToken` to enumerate everyone holding a grant, gets
2,500 rows, and files the result as the complete picture. It is not. The Object Reference states the
ceiling outright: "In API version 34.0 and later, this object was enhanced to help manage high
instance counts. A `query()` call returns up to 500 rows. A `queryMore()` call returns 500 more, up
to 2,500 total. **No more records are returned after 2,500.**" No error, no truncation warning — the
result set simply ends.

The documented workarounds each have their own limit. "Divide queries by filtering on fields like
`UserId` to return subsets of less than 2,500 records," or "Use `OFFSET` to get batches of 2,000
records" — and `OFFSET` itself is capped: "The `OFFSET` clause is limited to 2,000 rows. Requesting
an offset greater than 2,000 results in a `NUMBER_OUTSIDE_VALID_RANGE` error." You also cannot page
by primary key, because on this object `Id` is "Reserved for future use. Currently, the value is
always null."

**When it occurs:** In any org large enough for a widely-authorized app — a mobile client, an
Experience Cloud partner app, a browser extension — to have more than 2,500 outstanding grants. The
review that most needs completeness is exactly the one that hits the ceiling.

**How to avoid:** Always run `SELECT COUNT() FROM OauthToken` first, before the detail query, and
compare it to the row count you got back. If the count exceeds 2,500, page by `UserId` or with
`LIMIT 2000 OFFSET n` (incrementing by 2,000), and never key or de-duplicate results on `Id`. Record
the count, not just the rows, in the review checklist — `token-count-query-run` exists so the next
reviewer can tell a real zero from an unrun query.

---

## Gotcha 7: You Cannot Filter `LoginHistory` by `Application`, and the LoginType Values Contain Commas

**What happens:** The obvious monitoring query — "show me every login through this connected app" —
does not compile. `LoginHistory` publishes a closed filterable list, and the app-name field is not on
it: "Not all fields are filterable. You can only filter on the following fields:
`AuthenticationServiceId`, `CipherSuite`, `CountryIso`, `Id`, `LoginTime`, `LoginType`, `LoginUrl`,
`NetworkId`, `OptionsIsGet`, `OptionsIsPost`, `TlsProtocol`, `UserId`." `Application` — "the
application used to access the organization" — carries only `Group, Nillable, Sort`. So does
`Status`, and so does `SourceIp`. `WHERE Application = 'Billing Sync JWT'`, `WHERE Status =
'Success'`, and `WHERE SourceIp = '203.0.113.10'` are all rejected.

`LoginType` *is* filterable, and this is where the second trap sits. The values that mean "a
connected app produced this session" are `Application`, `Oauth, Remote Access Client`, and
`Oauth2, Remote Access 2.0` — two of the three contain a comma and a space inside the picklist value
itself, which breaks naive string-splitting in scripts and looks like a typo to a reviewer. The value
`Application` also collides by name with the unrelated `Application` field.

**When it occurs:** The first time someone builds a scheduled connected-app monitoring report, and
again whenever an incident calls for "logins from an unexpected IP" — `SourceIp` cannot anchor a
`WHERE` clause, so that hunt has to be built differently.

**How to avoid:** Filter on `UserId` and `LoginTime` (both filterable), then read `Application`,
`SourceIp` and `Status` off the returned rows, or aggregate with `GROUP BY Application, LoginType,
Status`. Quote the comma-bearing `LoginType` values exactly as published. Remember the access gate
too: "only users with Manage Users or Monitor Login History permissions can access this object,"
with the exception that "in API version 37.0 and later, all users can retrieve their own login
history records." Ready-made queries are in `references/metadata-examples.md` § 4c.

---

## Gotcha 8: `ipRelaxation` `ENFORCE` Points at a List You Can Delete by Deploying It

**What happens:** An app is hardened to `ENFORCE`, which "enforces the IP restrictions configured for
the org, such as the IP ranges assigned to a user profile." The value is a *pointer*, not a rule —
its entire strictness comes from a list maintained somewhere else. Two things then go wrong. If that
list is empty for the integration user's profile, `ENFORCE` constrains nothing while reading as the
strictest option in every audit. And if someone later adds a range by deploying a hand-written
`NetworkAccess` file, the org's other ranges are destroyed: "To add an IP range, deploy all existing
IP ranges, including the one you want to add. Otherwise, the existing IP ranges are replaced with the
ones you deploy."

Note that the app's own `ipRanges` element is a different list — those are "the ranges of IP
addresses that can access the app without requiring the user to authenticate with the connected app."
Populating it does not populate the org list that `ENFORCE` consults.

**When it occurs:** At the moment `ENFORCE` is set on an app whose integration user's profile has no
login IP ranges — nothing breaks, so nothing is noticed. And during an unrelated network change,
when a partial `NetworkAccess` deploy silently drops the ranges this app depended on and the
integration starts failing with no connected-app change in `SetupAuditTrail`.

**How to avoid:** Verify the org and profile trusted-IP entries exist before claiming `ENFORCE` is a
control, and name the owner of that list in the review checklist. Treat any `NetworkAccess` deploy as
a full-list replacement — the trap and its remedy are covered in
`admin/org-setup-and-configuration` (Gotcha 6) and `security/network-security-and-trusted-ips`. If
the caller cannot enumerate its egress ranges, say so in writing rather than choosing a looser
`ipRelaxation` value silently; the four values are not a strictness ladder, which
`admin/connected-apps-and-auth` covers.

---

## Gotcha 9: A Dated Permission-Set Assignment Un-Pre-Authorizes the Integration on a Day Nobody Diarised

**What happens:** The connected app is correctly configured — `isAdminApproved` `true`,
`permissionSetName` naming a real permission set, deployed and verified. Months later OAuth begins
failing and nothing in the connected app changed. The grant did not break at the app; it broke at the
assignment. `PermissionSetAssignment.ExpirationDate` is "the date that the assignment of the
permission set or permission set group expires for the specified user" (API 52.0 and later). When it
passes, the integration user leaves the app's pre-authorized population, and every diagnostic aimed
at the connected app comes back clean.

The reverse direction hides it as well. The app's grantee list is stored as `permissionSetName` on
`ConnectedApp` — the guide describes managing it as "editing each permission set's **Assigned
Connected App** list", but the deployable representation sits on the app. So retrieving or diffing
the `PermissionSet` metadata shows no connected-app grant at all, and an access review that
enumerates permission sets will not see the pre-authorization it is supposed to be reviewing.

**When it occurs:** Most often when an integration user was provisioned through the same
time-boxed-access process as human users, or when a temporary elevation was granted during a
migration and never re-granted permanently.

**How to avoid:** Query `SELECT Assignee.Username, PermissionSet.Name, ExpirationDate FROM
PermissionSetAssignment WHERE PermissionSet.Name = '<pre-auth set>'` as part of every review, and
treat any non-null `ExpirationDate` on an integration user as a finding. Deploy the `PermissionSet`
and the `ConnectedApp` together so the pairing is never half-applied. Access to the object is itself
gated — "only users who have one of these permissions can access this object: View Setup and
Configuration, Assign Permission Sets, Manage User." The expiry model in general is
`admin/permission-set-expiration`.

---

## Gotcha 10: Rotating the Key or Secret Needs an Ignore-Warnings Deploy — and a Connected App Has No Rotation Field At All

**What happens:** A security policy says "rotate the integration credentials annually," so someone
edits `consumerKey` in the retrieved `connectedApp-meta.xml` and deploys. Nothing rotates. The
Metadata API Developer Guide is explicit: "In API version 32.0 and later, you can set this field's
value only during creation. After you define and save the value, it can't be edited." `consumerSecret`
is the same — "After you save the value, it can't be edited" — and worse for a rotation plan, "When
set, the value isn't returned in Metadata API requests," so the retrieved file has no secret to
compare against in the first place.

The rotation fields exist only on the External Client App's global OAuth settings:
`shouldRotateConsumerKey` — "the OAuth external client app's consumer key is replaced with a newly
generated key on metadata deploy" — and `shouldRotateConsumerSecret`, both defaulting to `false`.
Both carry the same deploy requirement: "To maintain security, if this field is set to `true`, you
must include the ignore warnings attribute in the deploy command." A rotation deploy without
`--ignore-warnings` is rejected by design, which reads like a broken pipeline rather than a guardrail.

**When it occurs:** At the first scheduled credential rotation after the integration went live —
typically a year in, when the person who built it has moved on and the runbook says only "rotate the
secret."

**How to avoid:** Decide the rotation path at build time and write it into the template, because the
two paths cost very different amounts. Connected app: rotation is a replacement app plus a
coordinated caller cutover, so plan a change window. External Client App: set both flags `true`,
deploy with the ignore-warnings attribute, then set them back to `false` — otherwise the next deploy
of that file regenerates the credentials again. Either way the caller holds the key/secret pair, not
the repo. The rotation commands are in `references/metadata-examples.md` § 6; rotation as a security
programme is `security/connected-app-security-policies`.

---

## Gotcha 11: Your Only Evidence That a Policy Changed Expires After 180 Days, and `COUNT(Id)` Won't Query It

**What happens:** An audit asks who loosened `ipRelaxation` on a production integration. The
connected app itself carries no history — `ConnectedApplication` is "a connected app and its details;
all fields are read-only" and shows current state only. The evidence lives in `SetupAuditTrail`,
which "represents changes you or other admins made in your org's Setup area for **at least the last
180 days**." A change made two or three quarters ago may simply not be there, and its absence is
indistinguishable from "nobody changed it."

The object also fails the reflex query used to size an audit: "Aggregate queries aren't supported on
this object. For example, `SELECT count() FROM SetupAuditTrail` works but `SELECT count(Id) FROM
SetupAuditTrail` fails." Supported calls are `query()` and `retrieve()` only, so nothing can archive
rows out of it with DML either.

**When it occurs:** During an annual review or a post-incident investigation — the two moments that
are, by definition, further back than 180 days from the change that caused them.

**How to avoid:** Set the review cadence *inside* the 180-day window (quarterly leaves margin) so
each review's `SetupAuditTrail` sweep overlaps the previous one's date, and record the policy values
you observed in `templates/connected-app-review-checklist.yaml` — the checklist becomes the durable
record the platform does not keep. Use `SELECT count()` without a field when sizing. Note
`DelegateUser`, "the Login-As user who executed the action in Setup", when attributing a change: a
change made through Login As is credited to the delegating context, not only the named user. For
retention beyond the platform window, `security/shield-event-log-retention-strategy` covers the
add-on path.
