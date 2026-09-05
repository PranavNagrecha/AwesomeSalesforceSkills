---
name: experience-cloud-member-management
description: "Use this skill when adding external users to an Experience Cloud site, configuring self-registration, managing external user licenses, or customising the login and registration pages. Trigger keywords: add members to community, external user license, self-registration, customer portal login, partner user onboarding, ConfigurableSelfRegHandler. NOT for choosing which external user license to buy — use architect/experience-cloud-licensing-model. Also covers the networkMemberGroups membership block, NetworkMemberGroup assignment status, external-user creation from contacts, offboarding, and LoginHistory diagnosis for site logins. NOT for what records external users can see — use security/experience-cloud-security."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
tags:
  - experience-cloud
  - external-users
  - self-registration
  - community
  - licensing
  - member-management
triggers:
  - "how do I add external users to an Experience Cloud site"
  - "set up self-registration for customer portal"
  - "external user license type for community site"
  - "ConfigurableSelfRegHandler self registration apex"
  - "partner user onboarding experience cloud"
  - "login page branding experience builder registration"
  - "default account self registration setup"
  - "add a profile to an experience cloud site members list"
  - "external user cannot log in to community diagnose login history"
  - "deactivate external user and free the community license seat"
  - "bulk create partner users from contacts data loader"
inputs:
  - Experience Cloud site name and network ID
  - Target external-user license type (Customer Community, Customer Community Plus, Partner Community, External Identity)
  - Whether self-registration is required or members are added manually / via profile
  - Default account for self-registered users (required for self-reg)
  - Branding requirements for the login page
outputs:
  - Configured site membership (profile-based or manual user records)
  - Self-registration settings with default account, default profile, and handler class
  - Login/registration page branding settings in Experience Builder
  - Validation checklist confirming license-profile alignment
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Experience Cloud Member Management

This skill activates when work involves granting external users access to an Experience Cloud site — including choosing the right license, setting up self-registration, adding members manually or by profile, and customising the login/registration experience. It covers only external (outside the company) user access; internal user provisioning and site content/component design are out of scope.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which Experience Cloud license type is required: Customer Community, Customer Community Plus, Partner Community, or External Identity? The answer determines which profiles are available and constrains every subsequent decision.
- Is self-registration needed, or will admins add users manually (or through automation)? Self-registration requires a default account and default profile — confirm both exist before enabling the feature.
- What are the current licence counts, and on which meter? Seat-metered SKUs report through `UserLicense.TotalLicenses` / `UsedLicenses`; Login-metered SKUs report through `MonthlyLoginsEntitlement` / `MonthlyLoginsUsed`. Read both before promising capacity — see gotcha 3.
- Has the site been activated? Unapproved/inactive sites do not process registration or login flows.

---

## Questions to Ask Before Configuring

Ask these before touching Setup. Each one maps to a gotcha in references/gotchas.md, and skipping it produces a site whose Members list looks correct and whose users still cannot get in.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is each audience reached through a Contact, or are they employees?" | Contact-based users need an external licence and a `ContactId`; employees are legitimate site members on an internal profile (gotcha 6) | Two membership lists instead of one, and an explicit `allowInternalUserLogin` decision |
| "Which external licence, and is it the seat variant or the Login variant?" | The licence is fixed at profile creation and can never be changed (gotcha 1), and the Login variant is metered by monthly logins, not seats (gotcha 3) | The profile list, the right capacity meter, and the per-licence API allocation (gotcha 10) |
| "Do we grant membership by profile, by permission set, or both?" | `networkMemberGroups` accepts both, but a permission set silently skips Chatter customers from a customer group (metadata-examples § How to read it) | A membership matrix that survives someone changing a user's profile |
| "Is self-registration in scope, and who owns the default account?" | `selfRegProfile` is read only when `selfRegistration` is true, and the default account is not a `Network` field — it is a runtime argument to the handler (gotcha 4) | An owner for the catch-all account and a decision on declarative vs `Auth.ConfigurableSelfRegHandler` |
| "How will external users be created — UI, Data Loader, or Apex?" | Data Loader cannot set `UserType` (gotcha 8) and `Site.createExternalUser` requires a nickname and reuses or creates a Contact by email match | The exact column list, the nickname convention, and whether a Savepoint is needed |
| "What happens to a leaver's records, and can they ever come back?" | Users can never be deleted and the username is burned across all orgs (gotcha 3) | A reassignment target and a username convention that tolerates a returning person |
| "Who will diagnose a login failure, and do they have Monitor Login History?" | `LoginHistory` is permission-gated and `Status` is not filterable, so the obvious query neither runs nor returns anything for a delegated admin (gotcha 9) | A named on-call owner with the permission, and the site-scoped `NetworkId` query written in advance |

What a proper configuration adds over just adding profiles to the Members list: the membership block, the profile licences, the user-creation path and the offboarding path all agree with each other, so capacity is predictable, a leaver's records have somewhere to go, and a login failure is diagnosed from `LoginType` rather than guessed at.

---

## Core Concepts

### External User License Types and Profile Binding

Salesforce Experience Cloud supports four main external-user license types:

| License | Typical Use Case | Object Access |
|---|---|---|
| **Customer Community** | B2C portals, basic case deflection | Accounts, Contacts, Cases, limited custom objects |
| **Customer Community Plus** | More sophisticated B2C, roles, sharing rules | Broader custom object access, reports |
| **Partner Community** | Partner relationship management, channel sales | Leads, Opportunities, full CRM access |
| **External Identity** | Identity-only / SSO scenarios, low cost | Minimal CRM access |

A profile is permanently tied to one license type at creation time. You cannot reassign a profile to a different license type after the fact, and you cannot assign a user whose profile belongs to License A to a site that requires License B. This binding is enforced at the user record level, not the site level.

### Site Membership: Manual Addition vs Profile-Based Access

There are two ways external users gain access to a site:

1. **Profile-based membership** — Add the external profile to the site's Members settings (Setup > Digital Experiences > [site] > Administration > Members). Every active user with that profile automatically becomes a site member. This is the most common approach for managed portals.
2. **Manual member addition** — Individual contacts are converted to portal users (enable portal user on the Contact record), assigned a profile and a license, and granted access. Useful when rollout is controlled and the user population is small.

Self-registration is a third path — the user creates their own account through the site's registration page. This requires additional configuration (see below).

### Self-Registration Configuration

Self-registration lets anonymous visitors register as site members without an admin manually creating each user. The key requirements are:

- **Default Account** — Every self-registered user must be associated with an account. Configure a "catch-all" account in Setup > Digital Experiences > [site] > Administration > Registration > Default New User Account. Without this, self-registration silently fails.
- **Default Profile** — The profile assigned to new self-registered users. Must be an external profile tied to the correct license. Set in the same Registration settings panel.
- **Handler** — Either the declarative "Configurable Self-Registration" page (preferred for most orgs on LWR or Aura sites using the standard page) or a custom Apex class implementing `Auth.ConfigurableSelfRegHandler`, which declares exactly one method: `global Id createUser(Id accountId, Id profileId, Map<SObjectField, String> registrationAttributes, String password)`. It returns the Id of the user it created. `Auth.RegistrationHandler` is a **different interface for a different job** — just-in-time provisioning behind an Auth. Provider (SSO / social sign-on), with `User createUser(Id portalId, Auth.UserData userData)` and `void updateUser(Id userId, Id portalId, Auth.UserData userData)`. It is not a legacy version of the self-reg handler and the two are not substitutes.

### Login Page Branding

The login and registration pages are managed inside Experience Builder under the Login & Registration settings panel. Admins can:
- Replace the default Salesforce login page with a branded page built in Experience Builder.
- Configure password reset, self-registration, and forgot-username flows.
- Enable or disable social sign-on (SSO) buttons.

Changes to the login page do not require a site re-publish if you are only adjusting styling, but structural component changes (adding/removing components) do require publishing.

---

## Common Patterns

### Pattern: Customer Portal Self-Registration

**When to use:** B2C scenario where customers should be able to sign up without admin intervention. The site uses a Customer Community or Customer Community Plus license.

**How it works:**
1. Create a dedicated "catch-all" Account (e.g., "Customer Community Users") that will own self-registered contacts.
2. Create or confirm an external profile tied to the Customer Community license.
3. In Experience Builder > Login & Registration, enable self-registration, set the Default New User Account to the catch-all account, and set the Default Profile to the external profile.
4. Choose the handler: for standard registration pages, leave it as Configurable Self-Registration (no code needed). For custom flows, implement `Auth.ConfigurableSelfRegHandler` in Apex and reference the class name in the Registration settings.
5. Test by navigating to the site's login URL as a guest and clicking Register.

**Why not the alternative:** `Auth.RegistrationHandler` is not an alternative here — it is the registration hook for an Auth. Provider (SSO or social sign-on JIT provisioning) and takes `Auth.UserData`, which self-registration never supplies. For a site's own self-registration page, `Auth.ConfigurableSelfRegHandler` is the only applicable interface.

### Pattern: Partner User Onboarding via Manual Addition

**When to use:** Partner onboarding where each partner user must be vetted by an admin before gaining access. Low volume, high-trust scenario.

**How it works:**
1. Ensure the partner's Account record exists and is of record type "Partner Account" (or equivalent).
2. Open the partner's Contact record. Click **Enable Partner User** (or **Enable Customer User** depending on the license).
3. A new User record is created. Set the Profile to a Partner Community profile, set the Username and Email.
4. Confirm the site's Members settings include this profile (or add the user directly via the site's All Members list in Administration).
5. Save and notify the partner — they will receive a welcome email with login instructions.

**Why not the alternative:** Profile-based mass membership is unsuitable here because it immediately grants access to everyone with that profile, bypassing the per-user vetting step.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Large B2C portal, users self-onboard | Self-registration with Configurable Self-Reg page or `Auth.ConfigurableSelfRegHandler` | Scales without admin touch; declarative option requires no code for standard flows |
| Small partner network, each partner vetted | Manual user creation / Enable Partner User on Contact | Per-user control without granting broad profile membership |
| Existing internal profile needs to access portal | Create a new external profile tied to the external license | You cannot reuse internal profiles for external users; license binding prevents it |
| Need custom post-registration logic (e.g., assign to correct account dynamically) | Custom `Auth.ConfigurableSelfRegHandler` Apex class | Its `createUser(accountId, profileId, registrationAttributes, password)` hook receives the configured account and profile and can override both before calling `Site.createExternalUser` |
| Login page must match brand guidelines | Experience Builder Login & Registration settings | No code required; publish after structural changes |

---

## Recommended Workflow

1. **Fix the licence and the profile, in that order.** Decide the licence per audience with architect/experience-cloud-licensing-model, then create or confirm one external profile per licence (Setup > Profiles, filtered by User License). The binding is one-way and permanent — gotcha 1. Read the current meters before committing to a volume: `SELECT Name, TotalLicenses, UsedLicenses, MonthlyLoginsEntitlement, MonthlyLoginsUsed FROM UserLicense WHERE Name LIKE 'PID_%Community%'`.
2. **Write the membership block.** Copy the `Network` skeleton from references/metadata-examples.md § "Network: the membership and registration block" into `networks/<Site>.network-meta.xml`. Every profile and permission set that should confer membership goes in `networkMemberGroups`; set `selfRegistration` / `selfRegProfile` only if self-registration is in scope; decide `allowInternalUserLogin`, `enableMemberVisibility` and `enableGuestMemberVisibility` deliberately rather than leaving the defaults.
3. **Write the member permission set** from the same file's `PermissionSet` example if you are granting membership that way. Retrieve the live version first — from API 40.0 an unspecified permission is disabled on deploy.
4. **Run the checker before the deploy.** `python3 skills/admin/experience-cloud-member-management/scripts/check_experience_cloud_member_management.py --manifest-dir force-app/main/default` — it cross-checks that every `<profile>` and `<permissionSet>` in `networkMemberGroups` resolves to a file in the manifest, that `selfRegistration` true implies `selfRegProfile`, that any external-user CSV has the required columns and no `UserType`, and that no Apex class implements a non-existent `Auth` handler shape.
5. **Deploy in dependency order** — profiles, permission sets and the handler class first, then `CustomSite`, then `Network` with `status` `UnderConstruction`. The package.xml and `sf project deploy` commands are in references/metadata-examples.md § "package.xml and deploy order".
6. **Poll membership, do not assume it.** `SELECT Id, ParentId, AssignmentStatus FROM NetworkMemberGroup WHERE NetworkId = '...'` until every row reads `Added`. `Waiting for Add` is normal for a few minutes; `Failed Add` is the real deploy failure and the `Network` deploy will not report it (gotcha 7).
7. **Create the users, then verify the shape you actually got.** Use the CSV or the `Site.createExternalUser` snippet in references/metadata-examples.md § "Creating external users", then read back `UserType`, `ContactId` and `Profile.UserLicense.Name` with the query in references/examples.md § Anti-Pattern. Flip `status` to `Live` only after that query is clean and one real login appears in `LoginHistory` for the site's `NetworkId`.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] External profile is tied to the correct license type (Customer Community, CC Plus, Partner Community, or External Identity)
- [ ] License seat count confirmed — enough available seats for planned user volume
- [ ] Site membership method configured (profile-based, manual, or self-registration)
- [ ] If self-registration: Default New User Account and Default Profile are set; registration handler (declarative or Apex) is selected and tested
- [ ] Login page branding applied and site published after any structural component change
- [ ] End-to-end login and (if applicable) self-registration tested in a browser as a guest user
- [ ] No internal profiles were used in place of external profiles

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Deactivation frees the seat but never the username** — `UserLicense.UsedLicenses` counts only licences assigned to active users, so `IsActive = false` does return a seat on a seat-metered SKU. It returns nothing on a Login-metered SKU, and it never releases the User record or the globally unique `Username`. Full detail and the branching query: gotcha 3.
2. **Profile-license binding is permanent** — A profile created for the Customer Community license can never be reassigned to the Partner Community license or any other license. Attempting to change the license on an existing profile throws an error. If you chose the wrong license, you must create a new profile and migrate users.
3. **`Auth.ConfigurableSelfRegHandler` and `Auth.RegistrationHandler` are different jobs, not old and new** — `Auth.ConfigurableSelfRegHandler` backs a site's own self-registration page and declares one method, `global Id createUser(Id accountId, Id profileId, Map<SObjectField, String> registrationAttributes, String password)`, returning the new User's Id. `Auth.RegistrationHandler` backs an Auth. Provider (SSO / social sign-on) and declares `User createUser(Id portalId, Auth.UserData userData)` plus `void updateUser(Id userId, Id portalId, Auth.UserData userData)`. Models frequently emit a third, nonexistent shape — `registerUser(Auth.SelfRegistrationContext)` returning a `User`. Neither that method nor that class exists in the Auth namespace; code using them will not compile.
4. **Self-registration fails silently without a Default Account** — If the Default New User Account is not set in the Registration settings, self-registration POST requests return a generic error page with no useful debug output. This is the single most common self-reg setup mistake. Confirm the account is set and is not a Person Account (standard accounts only for the catch-all).
5. **Login page changes require a publish to take effect for structural changes** — Style-only changes (CSS, background colour) may propagate without a full publish in some scenarios, but adding or removing components on the login page always requires clicking Publish in Experience Builder before external users see the change.
6. **Membership is asynchronous, and internal users are allowed** — a successful `Network` deploy does not mean the Members list is populated; poll `NetworkMemberGroup.AssignmentStatus` until it reads `Added`. And internal profiles are legitimate members, contrary to the common rule of thumb — gotchas 6 and 7.
7. **`UserType` cannot be set and `LoginHistory.Status` cannot be filtered** — the two facts that break the first bulk load and the first login incident respectively. Gotchas 8 and 9.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Site membership configuration | Profile(s) added to the site's Members list in Administration |
| Self-registration settings | Default account, default profile, and optional handler class set in Registration panel |
| Login/registration page | Branded login page published in Experience Builder |
| External user record | User record tied to a Contact with the correct external profile and license |

---

## Reference Files

| File | Read it when |
|---|---|
| references/metadata-examples.md | You are writing the `Network` membership block, the member `PermissionSet`, the external-user CSV or Apex, the offboarding DML, or the login-failure SOQL — every element name is cited to a guide line |
| references/gotchas.md | Something worked in Setup but not through the API, membership did not appear after a deploy, a licence count did not move, or a login query will not compile |
| references/examples.md | You want the two end-to-end walkthroughs — self-registration with a custom handler, and vetted partner onboarding — plus the internal-profile anti-pattern and its detection query |
| references/well-architected.md | You are justifying the licence, membership and self-registration tradeoffs to a reviewer, or you need the grounded source list |
| references/llm-anti-patterns.md | You are reviewing AI-generated Experience Cloud membership config or a generated `Auth` handler class |
| scripts/check_experience_cloud_member_management.py | Before every deploy — validates the membership block, self-reg config, external-user CSV and handler classes against the manifest |
| templates/experience-cloud-member-management-template.md | You are capturing the membership decisions for a new site in a reviewable document |

---

## Related Skills

- flow/flow-for-experience-cloud — when a screen flow or guided process needs to be surfaced on the Experience Cloud site for self-registered or authenticated users
- security/experience-cloud-security — for deeper CORS, CSP, guest user access, and sharing-model security configuration on Experience Cloud sites
- admin/experience-cloud-site-setup — for creating the site itself, the `CustomSite` container, URL path prefix, template choice, and activation
- admin/experience-cloud-guest-access — for the unauthenticated visitor: guest user profile, guest sharing rules, and `enableGuestMemberVisibility`
- admin/self-service-design — for deciding what a self-registered customer should be able to do once they are in
- admin/partner-community-requirements — for gathering the partner-side requirements that decide the licence and the vetting gate before any of this is configured
- admin/user-management — for the general user lifecycle, freezing, and delegated administration that this skill's offboarding step plugs into
- admin/permission-set-architecture — for designing the member permission set as part of a coherent permission-set model rather than a one-off
- architect/experience-cloud-licensing-model — for choosing and costing the licence, including the seat-vs-Login decision that gotchas 3 and 10 depend on
