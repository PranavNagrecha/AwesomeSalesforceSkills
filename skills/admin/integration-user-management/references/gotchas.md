# Gotchas — Integration User Management

## Gotcha 1: A Connected App Can Silently Discard the Profile's Entire IP Allowlist

**What happens:** The integration profile carries a carefully scoped `loginIpRanges` allowlist, the security review signs it off, and the credential still works from anywhere. Nothing in the profile looks wrong, because the setting that neutralised it lives on the connected app.

**When it occurs:** Whenever the connected app's `ipRelaxation` is set to anything other than `ENFORCE`. The Metadata API guide defines the four values: `ENFORCE` (the default) "Enforces the IP restrictions configured for the org, such as the IP ranges assigned to a user profile"; `BYPASS` "Allows a user to run this app without org IP restrictions"; `BYPASS_2FACTOR` relaxes them for web-server-flow apps; and `ENFORCE_RELAXREFRESH` enforces them except when the app uses refresh tokens to get access tokens (`api_meta.txt` L35655–35672). Only the first of those actually applies the profile allowlist to every request.

**How to avoid:** Deploy `<ipRelaxation>ENFORCE</ipRelaxation>` explicitly on any connected app an integration user authenticates through, rather than relying on the default surviving whoever edits the app next. Treat `ipRelaxation` and `Profile.loginIpRanges` as one control reviewed together — an audit that reads only the profile will report an allowlist that is not in force. Note the inverse failure too: with `ENFORCE` in place, a middleware IP change that nobody told you about presents as a login failure, not a permission error, which is why Gotcha 4 says to read `LoginHistory.Status` before assuming MFA.

---

## Gotcha 2: Admin Profile Grants Interactive Login — Defeating the API-Only Design

**What happens:** An integration user with System Administrator or a cloned admin profile can log into the Salesforce web UI through a browser, in addition to making API calls. Any person or system with the integration user's credentials can access the full Salesforce UI with admin privileges. This is invisible in standard security audits unless profile assignments are specifically checked.

**When it occurs:** Whenever an admin grants a non-API-only profile (System Administrator, Standard User, or any custom profile without the API-only flag) to an integration user for "simplicity" or to resolve permission errors quickly.

**How to avoid:** The Minimum Access - API Only Integrations profile is the only profile that enforces API-only access at the platform level for the Salesforce Integration user license. Never assign any other profile to a Salesforce Integration user. When permission errors occur, add a permission set — do not change the profile.

---

## Gotcha 3: Login History UI Truncates to 20,000 Records

**What happens:** An admin attempts to audit an integration user's login activity over the past month using Setup > Users > Login History. The history only shows records from the past few days — older records are not visible.

**When it occurs:** High-frequency integrations making thousands of API calls per day can exhaust the 20,000-record UI display limit within days. The records still exist in the platform (6-month retention) but are not visible in the Setup UI.

**How to avoid:** For full audit history on high-frequency integration users, use the SOQL LoginHistory object via the Salesforce API:
```soql
SELECT UserId, Status, LoginType, SourceIp, LoginTime 
FROM LoginHistory 
WHERE UserId = '<integration_user_id>'
ORDER BY LoginTime DESC
```
The API returns up to 6 months of login records regardless of the UI display limit. For compliance or security auditing, always use the API query rather than the Setup UI.

---

## Gotcha 4: The Org-Wide MFA Setting Is Scoped to Direct UI Logins, So an "MFA Failure" on an API-Only User Is Usually Something Else

**What happens:** An integration user starts failing authentication shortly after the security team turns on org-wide MFA, and the failure is attributed to MFA. Waivers are granted, MFA is toggled, nothing changes — because the actual blocker is the profile's IP range, its login hours, or the session security level, and the MFA setting was never in the path.

**When it occurs:** During any MFA rollout, because MFA is the change everyone remembers. The metadata guide describes the org switch as `SecuritySettings.enableMFADirectUILoginOptIn`: "Requires all users in your Salesforce org to provide an additional verification method when logging in **directly to the UI** with their username and password... The Waive Multi-Factor Authentication for Exempt Users user permission overrides this setting" (`api_meta.txt` L126248–126252). A user carrying the API Only User permission "can access Salesforce only via APIs, regardless of their other permissions" (`api_meta.txt` L121360–121363) and therefore has no direct-UI-login path for that setting to act on.

**How to avoid:** Before granting an MFA waiver, read the actual `Status` value on the failing `LoginHistory` row. If it names a restricted IP, a login-hours violation, or a session-level requirement, the MFA waiver will not fix it. Reserve the waiver permission for users that genuinely do log in through the UI.

> UNVERIFIED (2026-09-05): the scoping above is grounded, but whether a Salesforce org can *additionally* enforce MFA on API logins through some separate control is not confirmable from the Metadata API guide, Object Reference, REST guide, or App Limits cheat sheet extracts available offline — no such control appears in any of them. If your org's Setup exposes one, it overrides this guidance; check before concluding that MFA cannot be the cause.

---

## Gotcha 5: `LoginHistory` Cannot Be Filtered on `Status` or `SourceIp`

**What happens:** A monitoring query written as `WHERE Status != 'Success'` or `WHERE SourceIp LIKE '52.30.%'` fails outright rather than returning zero rows. The alert built on it never fires, and because a broken scheduled job is quieter than a broken integration, nobody notices until an audit asks for the failed-login report.

**When it occurs:** Any time the monitoring query is authored from the field list rather than from the filterability list. The Object Reference is explicit: "Not all fields are filterable. You can only filter on the following fields" — `AuthenticationServiceId`, `CipherSuite`, `CountryIso`, `Id`, `LoginTime`, `LoginType`, `LoginUrl`, `NetworkId`, `OptionsIsGet`, `OptionsIsPost`, `TlsProtocol`, `UserId` (`object_reference.txt` L177012–177025). `SourceIp` carries a second restriction on top: "The SourceIp field doesn't support the LIKE comparison operator" (`object_reference.txt` L176979).

**How to avoid:** Filter on `UserId` and `LoginTime` only, select `Status` and `SourceIp` into the result set, and evaluate them client-side. When you need a server-side filter on the source, use `CountryIso` or `LoginUrl`, both of which are filterable. Reading `LoginHistory` at all needs Manage Users or Monitor Login History (`object_reference.txt` L176639–176641), so a monitoring integration reading its own history needs that grant explicitly.

---

## Gotcha 6: `LoginType` Has No Value Called "API" or "OAuth"

**What happens:** A dashboard filters integration logins with `LoginType = 'OAuth'` or `LoginType = 'API'` and shows an empty chart. `LoginType` is a restricted picklist, so the filter matches nothing rather than erroring in a way anyone investigates.

**When it occurs:** Whenever the query is written from intuition. The documented values relevant to integrations are `Oauth, Remote Access Client`, `Oauth2, Remote Access 2.0`, `Certificate` (certificate-based login), `Application`, and `OtherApi` (Other Apex API) (`object_reference.txt` L176849–176905). The finer distinction lives on `LoginSubType`, whose values include `OauthClientCredentials`, `OAuthDevice` and `OauthHybridRefreshToken` (`object_reference.txt` L176798–176812).

**How to avoid:** Confirm the exact strings by first running an unfiltered query for the user and reading back the values the org actually produces, then pin the dashboard to those. Use `LoginType` for the broad flow family and `LoginSubType` to tell a client-credentials login apart from a refresh-token login.

---

## Gotcha 7: A HIGH_ASSURANCE Session Requirement Blocks JWT and Client-Credentials Logins Outright

**What happens:** Hardening work sets `requiredSessionLevel` to `HIGH_ASSURANCE` on the integration user's profile, or applies a High Assurance connected-app session policy, and every headless authentication starts failing. Because the change was filed as "session hardening" rather than "MFA", nobody connects it to the outage.

**When it occurs:** When High Assurance is applied to a flow that has no user approval step. The metadata guide spells out the consequence under `ConnectedAppSessionPolicy.policyAction`: `RaiseSessionLevel` "applies to authorization flows that include a user approval step for API logins. These flows are the OAuth 2.0 refresh token flow, web server flow, and user-agent flow. All other flows, such as the JSON Web Token (JWT) bearer token flow, don't include a user approval step. **For flows without a user approval step, API logins with the High Assurance session security level are blocked**" (`api_meta.txt` L35826–35836).

**How to avoid:** Keep `ProfileSessionSetting.requiredSessionLevel` at `STANDARD` for any profile that anchors an integration user, and leave the connected app's session policy off. Do not substitute `LOW` — the guide warns that "users assigned to this level experience unpredictable and reduced functionality" (`api_meta.txt` L98880–98883). Achieve the hardening through `loginIpRanges` and `loginHours` instead, which act on the same threat without breaking the flow.

---

## Gotcha 8: `User.LastLoginDate` Is Throttled and Cannot Measure Integration Frequency

**What happens:** A "is this integration still alive?" report keys off `User.LastLoginDate` and reports a call volume far below what the middleware logs show, or shows an integration as idle when it authenticated seconds ago.

**When it occurs:** With any integration that authenticates more than once per minute — a retry storm, a fan-out job, or a client that requests a fresh token per request. The Object Reference states the throttle plainly: `LastLoginDate` is "The date and time when the user last successfully logged in. This value is updated if 60 seconds elapses since the user's last login" (`object_reference.txt` L295476–295483).

**How to avoid:** Use `LastLoginDate` only as a liveness signal ("has this account authenticated at all in the last N days?"), never as a counter. For volume and pattern, count `LoginHistory` rows over a `LoginTime` window, or read Event Monitoring — `EventLogFile` access itself requires the View Event Log Files and API Enabled permissions (`object_reference.txt` L112541–112542).

---

## Gotcha 9: The API Request Allocation Is Org-Wide, So One Integration User Can Starve Every Other

**What happens:** A misbehaving integration exhausts the org's daily API allocation and every other integration — plus Data Loader, plus the mobile app — starts receiving HTTP 403 with `REQUEST_LIMIT_EXCEEDED` (`api_rest.txt` L1146). Admins look for a per-user limit to raise and find none.

**When it occurs:** Always, structurally. The App Limits cheat sheet is unambiguous: "Limits and allocations are enforced against the aggregate of all API calls made to the org in a 24-hour period. **Limits and allocations are not on a per-user basis**" (`salesforce_app_limits_cheatsheet.txt` L616–618). The concurrency ceiling behaves the same way: 25 concurrent inbound requests lasting 20 seconds or longer for production orgs and sandboxes, 5 for Developer Edition and trials, also returning `REQUEST_LIMIT_EXCEEDED` (`salesforce_app_limits_cheatsheet.txt` L481–494). The `Sforce-Limit-Info` response header reports the same org-level number — "the daily API usage for the organization against which the call was made" (`api_rest.txt` L921–931) — so it cannot attribute consumption to a user either.

**How to avoid:** Because the platform will not isolate integrations from each other, attribution has to come from monitoring rather than from limits: one integration user per system, so `LoginHistory` and Event Monitoring can name the offender, plus API Usage Notifications configured in Setup so the org is warned before the allocation is gone (`salesforce_app_limits_cheatsheet.txt` L636–642). Rate-limiting belongs on the middleware side; the platform provides no per-user throttle to fall back on.

---

## Gotcha 10: Changing an Integration User's Profile Silently Changes Its License

**What happens:** An admin "temporarily" moves an integration user to a different profile to test a permission theory, and the user's license changes underneath them. Moving it back may fail if the original license has no seats free, leaving the integration stranded on the wrong profile.

**When it occurs:** On any profile reassignment. The Object Reference states the coupling on `User.ProfileId`: "If you change the user's profile, the user's license also changes, because every profile belongs to exactly one user license type" (`object_reference.txt` L295693–295696). Seat availability then becomes the constraint on getting back: "Each inserted User also counts as a license. Every organization has a maximum number of licenses. If you attempt to exceed the maximum number of licenses by inserting User records, the create request is rejected" (`object_reference.txt` L295874–295876).

**How to avoid:** Never diagnose a permission problem by swapping the profile. Add a temporary permission set instead, then remove it — permission set assignment does not touch the license. Before any planned profile move, check headroom on both licenses with `SELECT Name, TotalLicenses, UsedLicenses FROM UserLicense`, and note that `UsedLicenses` "isn't filterable in API version 64.0 or later when using it in a WHERE clause in a SOQL query" (`object_reference.txt` L299685–299687) — select it and compare in the client.

---

## Gotcha 11: Deploying the Integration Profile Overlays the Target Instead of Replacing It

**What happens:** A permission is disabled in source control, the profile is deployed, and the permission is still enabled in the target org. Source and org disagree, and the source-controlled profile becomes evidence for a state that does not exist.

**When it occurs:** On every `Profile` deploy. The guide flags it as a design decision: "We designed Profile metadata deployment to overlay the existing Profile settings in a target org. For example, if you disable permissions for a profile, the newly disabled permission information isn't exported. To force all Profile changes to deploy through metadata, including permission disablement, add code that explicitly indicates disabled permissions" (`api_meta.txt` L97623–97627). The same section adds a second trap: a profile that does not yet exist in the target and ships with no permissions specified "contains all permissions and settings in the standard Minimum Access - Salesforce profile (API version 60.0 and later) or the standard Standard User profile (API version 59.0 and earlier)" (`api_meta.txt` L97629–97632).

**How to avoid:** Write `<enabled>false</enabled>` explicitly for every elevated permission the integration profile must not have — `ModifyAllData`, `ViewAllData`, `AuthorApex`, `ManageUsers` — rather than relying on their absence. Permission sets behave the opposite way and can be relied on: from API v40.0, a permission not specified in a permission set deployment "is disabled" (`api_meta.txt` L94867–94873). Confirm the deployed state afterwards against `SetupAuditTrail`, which retains Setup changes "for at least the last 180 days" and records actions such as `PermSetCreate` (`object_reference.txt` L261537–261566).
