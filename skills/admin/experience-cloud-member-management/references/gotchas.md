# Gotchas — Experience Cloud Member Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Profile-License Binding Is Permanent

**What happens:** If you create a profile tied to the Customer Community license and later discover you need Partner Community features (such as Opportunity access or full role hierarchy), you cannot change the license on the existing profile. Attempting to edit the User License field on a profile throws an error. All users on the old profile must be migrated to a new profile created with the correct license.

**When it occurs:** Typically surfaces mid-project when business requirements expand after initial setup, or when an admin clones the wrong base profile (e.g., clones "Authenticated Website" instead of "Partner Community User").

**How to avoid:** Confirm the correct license type before creating any external profile. Run a quick requirements check: Does the portal need Opportunity, Lead, or Order access? If yes, Partner Community. Does it need robust custom object sharing via roles? Customer Community Plus. Simple case/knowledge access? Customer Community. Identity-only? External Identity. Do this before creating users — migrating users later requires deactivating old users, creating new ones, and re-sharing records.

---

## Gotcha 2: Two Auth Registration Interfaces That Are Not Versions of Each Other

**What happens:** Salesforce has two Apex registration interfaces with confusingly similar names, and they are routinely described — including by LLMs and by a good deal of blog content — as an old one and a new one. They are not. They serve different entry points and have unrelated signatures:

| Interface | Entry point | Signature |
|---|---|---|
| `Auth.ConfigurableSelfRegHandler` | The site's own self-registration page (Experience Builder > Login & Registration) | `global Id createUser(Id accountId, Id profileId, Map<SObjectField, String> registrationAttributes, String password)` — returns the new User's Id |
| `Auth.RegistrationHandler` | Just-in-time provisioning behind an Auth. Provider (SSO, social sign-on) | `User createUser(Id portalId, Auth.UserData userData)` and `void updateUser(Id userId, Id portalId, Auth.UserData userData)` |

Self-registration never produces an `Auth.UserData`, so an `Auth.RegistrationHandler` class named in the Registration settings cannot do the job, and vice versa. The Registration settings panel accepts a class name without validating the interface, so the mismatch surfaces only when a real visitor tries to register.

**When it occurs:** When a developer — or a code generator — treats the two names as synonyms, or emits the third, entirely fictional shape `registerUser(Auth.SelfRegistrationContext)`.

**How to avoid:** Pick by entry point, not by recency. Self-registration page → `Auth.ConfigurableSelfRegHandler`. Auth. Provider → `Auth.RegistrationHandler`. Before deploying either, compile-check the signature against the Apex Reference Guide; both interfaces are current and supported, and an org can legitimately have one of each.

---

## Gotcha 3: Deactivation Frees the Seat — It Does Not Free the Username, the Record, or a Consumed Login

**What happens:** The widely repeated claim that deactivating an external user leaves the licence seat consumed is wrong for seat-based Experience Cloud licences. `UserLicense.UsedLicenses` is defined as "The number of user licenses that are assigned to **active** users in the organization" (Object Reference, `UserLicense`, object_reference.txt L299669–299672), so setting `IsActive = false` does return the seat. What deactivation never returns is anything else. The User record itself is permanent: "You can't delete a user in the user interface or the API." (object_reference.txt L297169–297170). The `Username` stays reserved — it "must also be unique across all organizations" and a duplicate insert "is rejected" (object_reference.txt L295865–295872) — so you cannot re-create a leaver under the same username, in this org or any other. And on a *Login*-based licence there is no seat to return at all: `MonthlyLoginsEntitlement` is "The maximum number of customer or partner portal logins allowed per month. A null value in this field means the user license is charged according to the number of users rather than the number of logins." (object_reference.txt L299611–299616). Logins already spent this month are spent.

**When it occurs:** During an offboarding sprint driven by a "reclaim licences" ticket. The team deactivates a batch of dormant users, watches `UsedLicenses` drop as expected on the Community SKU, and then finds that the Community *Login* SKU is unchanged — because that licence was never metered by seats. It also occurs when a leaver rejoins months later and their old username is refused.

**How to avoid:** Query both meters before you plan capacity, and branch on which one is non-null:

```sql
SELECT Name, TotalLicenses, UsedLicenses, MonthlyLoginsEntitlement, MonthlyLoginsUsed
FROM UserLicense
WHERE Name LIKE 'PID_%Community%'
```

A null `MonthlyLoginsEntitlement` means seat-metered — deactivation helps. A non-null value means login-metered — deactivation does nothing for this month's allocation, and the fix is fewer logins or a bigger entitlement. Both login fields require Digital Experiences enabled and the View Setup and Configuration permission to be visible and queryable (object_reference.txt L299617–299621, L299640–299644). Note also that `UsedLicenses` "isn't filterable in API version 64.0 or later when using it in a WHERE clause" (object_reference.txt L299672–299675), so filter on `Name` and compare in your client. Because usernames are permanently burned, adopt a username convention that tolerates a returning person (a suffix you can increment) rather than one derived only from their email.

---

## Gotcha 4: Self-Registration Silently Fails Without a Default New User Account

**What happens:** When Self-Registration is enabled in the site's Administration > Registration panel but no Default New User Account is specified, self-registration POST requests complete without error on the form but then display a generic error page. The user is not created, no error appears in Setup > Login History, and the debug log may show a `System.NullPointerException` deep in the registration stack.

**When it occurs:** When an admin enables the Self-Registration toggle but forgets to scroll down and configure the Default New User Account and Default Profile fields. Also occurs when the designated catch-all account is deleted or deactivated after the fact.

**How to avoid:** After enabling self-registration, immediately confirm both the Default New User Account and Default Profile are set. Test with a guest browser session before considering the feature live. Protect the catch-all account with a validation rule or org-level policy preventing deletion. Person Accounts cannot be used as the catch-all — it must be a business (standard) Account.

---

## Gotcha 5: Login Page Structural Changes Require a Site Publish

**What happens:** Admins editing the login page in Experience Builder assume changes take effect immediately (as some property changes do for authenticated pages). However, adding or removing components on the login/registration page, or changing the page structure, requires an explicit Publish action in Experience Builder. Until the site is published, external users see the previous version of the login page. This causes confusion in UAT when the tester's browser is caching the old page.

**When it occurs:** During iterative login-page branding work, especially when multiple changes are made across a session and the admin forgets to publish after the final change. Also occurs after a sandbox refresh where the site is in Draft state.

**How to avoid:** Establish a discipline of always clicking Publish after any login page structural change. Communicate to QA that login page changes require a publish before testing. In sandboxes, confirm the site status is Active (not Preview) before testing external login flows.

---

## Gotcha 6: Internal Users Are First-Class Site Members — the "Internal Profiles Can't Be Members" Rule Is a Myth

**What happens:** Teams design around a rule that does not exist: that only external, portal-licensed profiles can appear in a site's Members list. The platform says the opposite in four places. `NetworkMemberGroup` — "Represents a group of members in an Experience Cloud site. Members can be either users in your internal org or external users assigned portal profiles. An administrator adds members to an Experience Cloud site by adding a profile or a permission set, and any user with the profile or permission set becomes a member of the site." (Object Reference, object_reference.txt L188596–188599). `NetworkMember` repeats it — "Members can be either users in your company or external users with portal profiles." (object_reference.txt L188297). `Network` carries a dedicated switch for their credentials, `allowInternalUserLogin` — "Determines whether internal users can log in with their internal credentials on the site login page." (Metadata API Developer Guide, api_meta.txt L90687–90689). And `LoginHistory.LoginType` has a value reserved for exactly this traffic: `EmployeeLoginToCommunity` — Employee Login to Community (object_reference.txt L176871–176872).

The real constraint is a different one, and it is about the *user record shape*, not the members list. A **contact-based** external user must hold an external licence, because the profile decides the licence: "If you change the user's profile, the user's license also changes, because every profile belongs to exactly one user license type." (object_reference.txt L295686–295693). An internal user is not contact-based — `User.AccountId` is read-only and null for Salesforce users (object_reference.txt L294996–295001) — so they consume an internal licence and reach the site as an employee, not as a portal user.

**When it occurs:** When an internal support agent or channel manager needs to see the site as members see it, and the team concludes it is impossible and builds a second, duplicate internal-facing page instead. It also occurs in reverse: an admin adds an internal profile to `networkMemberGroups`, is surprised it deploys cleanly, and then cannot explain the internal licence consumption to finance.

**How to avoid:** Decide the two questions separately. *Should these people be members?* — put their profile or permission set in `networkMemberGroups`, internal or external. *Should they log in with internal credentials on the site login page?* — that is `allowInternalUserLogin`, and it is independent. Then confirm the intent held after go-live by reading `LoginType` from the site's login history rather than assuming; `EmployeeLoginToCommunity` rows you did not plan for mean an internal profile is in the members list by accident.

---

## Gotcha 7: Membership Is Applied Asynchronously, and Removing a Profile Is an Update — There Is No Delete

**What happens:** A `Network` deploy that lists profiles in `networkMemberGroups` returns success, and the site's Members list in Setup is still empty minutes later. Nothing is broken. "Profiles and permission sets are added and removed asynchronously, so you can also check the status of a profile or permission set that was updated in a site." (Object Reference, `NetworkMemberGroup` § Usage, object_reference.txt L188673–188675). The `AssignmentStatus` picklist exposes the whole state machine: `Add Calculated`, `Added`, `Failed Add`, `Failed Remove`, `Remove Calculated`, `Waiting for Add`, `Waiting for Remove` (object_reference.txt L188625–188648). `Waiting for Add` means "the profile or permission set was added to the Experience Cloud site, but the async process hasn't completed yet. After the process is complete, the status is updated to `Added`."

The removal side is stranger. `NetworkMemberGroup` supports `create()`, `describeSObjects()`, `query()`, `retrieve()`, `update()` — with an explicit note that "the `upsert()` call is not supported for this object" — and no `delete()` at all (object_reference.txt L188608–188612). You detach a profile by *updating* the row's `AssignmentStatus`: the guide's own sample sets it to `WaitingForRemove`, described as "Use this status to remove all the members belonging to a profile or permission set and remove a profile or permission set from an Experience Cloud site."

**When it occurs:** In CI, where a post-deploy smoke test asserts membership seconds after the deploy call returns and fails intermittently. And in offboarding scripts written against the intuitive `DELETE FROM NetworkMemberGroup`, which has no API to call.

**How to avoid:** Never assert membership synchronously. Poll `SELECT Id, ParentId, AssignmentStatus FROM NetworkMemberGroup WHERE NetworkId = '...'` until every row reads `Added`, and treat `Failed Add` / `Failed Remove` as the real deploy failure — the `Network` deploy itself will not report them. To remove a group, update `AssignmentStatus` to the remove status and poll again; do not attempt a delete.

---

## Gotcha 8: `User.UserType` Cannot Be Set on Insert or Update — It Is Derived From the Profile

**What happens:** A Data Loader CSV or an Apex insert includes `UserType` (`PowerPartner`, `CspLitePortal`, …) because the field is what everyone reasons about when discussing external users. `UserType`'s properties are Filter, Group, Nillable, Sort, Restricted picklist — there is no Create and no Update (Object Reference, `User`, object_reference.txt L297100–297104). The `Profile` object states the Apex side outright: "In API version 53.0 and later, you can't set the value of `UserType` using Apex." (object_reference.txt L232482). The value is a consequence of `ProfileId`, because "every profile belongs to exactly one user license type" (object_reference.txt L295690–295693).

The failure is confusing because the *symptom* appears at the wrong layer. A load that maps `UserType` does not produce a "field is not createable" message that names the real problem; the practitioner then re-maps columns for an hour instead of checking that the profile in `ProfileId` carries the licence they wanted.

**When it occurs:** On the first bulk external-user load in a project, and on any migration that carries `UserType` across from an extract of an existing org.

**How to avoid:** Leave `UserType` out of the payload entirely and choose it by choosing the profile. Verify afterwards by reading it back with the profile's licence beside it — `SELECT Id, Username, UserType, Profile.Name, Profile.UserLicense.Name FROM User WHERE ContactId != null AND CreatedDate = TODAY`. The documented values you should expect are `PowerPartner` (Partner), `CspLitePortal` (High Volume Portal), `CustomerSuccess` (Customer Portal User), `PowerCustomerSuccess` (Customer Portal Manager), with `Standard` and `Guest` for the non-portal cases (object_reference.txt L297106–297122). A row that came back `Standard` means the load pointed at an internal profile and has just consumed an internal licence.

---

## Gotcha 9: `LoginHistory.Status` Is Not Filterable, So the Obvious Login-Failure Query Does Not Compile

**What happens:** Diagnosing "our partners can't log in" starts with a query filtered on the failure reason, and Salesforce rejects it. The Object Reference enumerates the filterable fields exhaustively and `Status` is not among them: `AuthenticationServiceId`, `CipherSuite`, `CountryIso`, `Id`, `LoginTime`, `LoginType`, `LoginUrl`, `NetworkId`, `OptionsIsGet`, `OptionsIsPost`, `TlsProtocol`, `UserId` (object_reference.txt L177041–177054). `Status` is selectable — "Displays the status of the attempted login. Status is either success or a reason for failure." (object_reference.txt L176981–176983) — but only client-side filterable.

Two adjacent facts make this worse in practice. Access is gated: "only users with Manage Users or Monitor Login History permissions can access this object", with the single exception that from API 37.0 "all users can retrieve their own login history records" (object_reference.txt L176634–176638), so a delegated admin running the diagnosis may see only their own rows and conclude there is no failure traffic at all. And nothing else scopes the query to one site: `NetworkId` — "The ID of the Experience Cloud site that the user is logging in to" — is the only site filter, and it exists only from API 31.0 and only if Experience Cloud is enabled (object_reference.txt L176984–176989).

**When it occurs:** During a login incident, when the pressure to get an answer fast is highest and a `WHERE Status = 'Invalid Password'` looks like the one-line answer.

**How to avoid:** Filter on `NetworkId` plus `LoginTime`, select `Status` and `LoginType`, and aggregate the failure reasons in your client. Read `LoginType` before concluding anything about credentials — the site-relevant values are `ChatterCommunityPortalUnPwd`, `ChatterCommunityThirdPartySso`, `SamlChatterNetworks`, `EmployeeLoginToCommunity`, `NetworksPortalApiOnly`, `PasswordlessLogin`, and the legacy portal values `Portal`, `PortalThirdPartySso`, `PrmPortal`, `PrmPortalThirdPartySso`, `SamlCspPortal`, `SamlPrmPortal`, `SamlSite` (object_reference.txt L176863–176899). A user "failing to log in" whose rows all read `Oauth2` is not hitting the site login page at all.

---

## Gotcha 10: Login-Based Licences Also Carry a Twentieth of the API Allocation

**What happens:** Choosing Customer Community **Login** over Customer Community, or Partner Community **Login** over Partner Community, is normally framed as a pure pricing decision about how often members visit. It also silently changes the org's daily API budget. The Salesforce Developer Limits and Allocations Quick Reference gives API calls per licence type per 24-hour period, and the Login SKUs are an order of magnitude smaller: Partner Community 200 versus Partner Community Login 10, Customer Community Plus 200 versus Customer Community Plus Login 10, with Customer Community and Customer Community Login both at 0 (salesforce_app_limits_cheatsheet.txt L527–L547 for Enterprise/Professional, L555–L585 for Unlimited/Performance). The org total is "100,000 + (number of licenses x calls per license type) + purchased API Call Add-Ons".

External Identity moves in the other direction and by a lot: External Identity 25,000 contributes 70,000 calls, External Identity 250,000 contributes 750,000, and External Identity 1,000,000 contributes 4,000,000 — with the guide's own caveat that "the limits for the External Identity license type vary. If you're not sure whether your limit is 70,000 calls, 750,000 calls, or 4,000,000 calls, contact your Salesforce representative." (salesforce_app_limits_cheatsheet.txt L513–L518, L536–L544).

**When it occurs:** When a portal that seemed cheap on licences is later fronted by a mobile app or an integration that calls the API as the member, and the org starts tripping its 24-hour request allocation — months after the licence decision was signed off, by which point nobody connects the two.

**How to avoid:** When the licence question is on the table, ask what will call the API *as an external user*, and multiply the per-licence figure by the planned member count before comparing prices. A 5,000-member Customer Community deployment contributes 0 calls whichever variant you buy; a 5,000-member Partner Community contributes 1,000,000 and its Login twin contributes 50,000. Cross-check the choice with architect/experience-cloud-licensing-model rather than settling it here.
