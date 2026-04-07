---
name: experience-cloud-member-management
description: "Use this skill when adding external users to an Experience Cloud site, configuring self-registration, managing external user licenses, or customising the login and registration pages. Trigger keywords: add members to community, external user license, self-registration, customer portal login, partner user onboarding, ConfigurableSelfRegHandler. NOT for internal (Employee) user management, internal profile or permission-set assignments, or Experience Cloud page-layout / component design."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud Member Management

This skill activates when work involves granting external users access to an Experience Cloud site — including choosing the right license, setting up self-registration, adding members manually or by profile, and customising the login/registration experience. It covers only external (outside the company) user access; internal user provisioning and site content/component design are out of scope.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which Experience Cloud license type is required: Customer Community, Customer Community Plus, Partner Community, or External Identity? The answer determines which profiles are available and constrains every subsequent decision.
- Is self-registration needed, or will admins add users manually (or through automation)? Self-registration requires a default account and default profile — confirm both exist before enabling the feature.
- What are the current license counts? Deactivated external users continue to consume a license seat; check Setup > Company Information > Licenses before promising capacity.
- Has the site been activated? Unapproved/inactive sites do not process registration or login flows.

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
- **Handler** — Either the declarative "Configurable Self-Registration" page (preferred for most orgs on LWR or Aura sites using the standard page) or a custom Apex class implementing `Auth.ConfigurableSelfRegHandler`. The legacy `Auth.RegistrationHandler` interface is older and requires writing a `createUser` and `updateUser` method; `ConfigurableSelfRegHandler` is the current interface and provides a single `registerUser` method with a richer context object.

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

**Why not the alternative:** Using the legacy `Auth.RegistrationHandler` interface requires writing more boilerplate Apex and does not receive new platform improvements. Prefer `Auth.ConfigurableSelfRegHandler` on all new implementations.

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
| Need custom post-registration logic (e.g., assign to correct account dynamically) | Custom `Auth.ConfigurableSelfRegHandler` Apex class | Provides `registerUser` hook where account, profile, and user fields can be set programmatically |
| Login page must match brand guidelines | Experience Builder Login & Registration settings | No code required; publish after structural changes |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm license type and profile** — Identify which Experience Cloud license the users will need. Verify that an external profile tied to that license already exists (Setup > Profiles > filter by User License). If not, create the profile before proceeding.
2. **Check license capacity** — Navigate to Setup > Company Information and confirm there are enough available seats for the external license. Remember that deactivated users still consume seats; deactivate and free them if needed before adding new users.
3. **Configure site membership method** — In Setup > Digital Experiences > [site] > Administration > Members, add the external profile(s) for profile-based access. For manual addition, enable the portal user on the Contact record and assign the correct profile. For self-registration, proceed to step 4.
4. **Set up self-registration (if required)** — Enable self-registration in the site's Registration settings. Set the Default New User Account (catch-all account) and Default Profile. Optionally, specify a custom `Auth.ConfigurableSelfRegHandler` Apex class for advanced logic. Test the registration flow as a guest user.
5. **Customise and validate login page branding** — In Experience Builder, open Login & Registration, apply branding (logo, colours, background), enable or disable self-reg/forgot-password links, then publish the site. Confirm the login URL resolves and registration/login completes end-to-end in a browser.

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

1. **Deactivated users still consume license seats** — Deactivating an external user does not free the license. You must deactivate the user AND then go to Setup > Company Information to confirm the count drops. If license seats are exhausted, new user creation fails silently or with a generic error. Audit inactive external users regularly.
2. **Profile-license binding is permanent** — A profile created for the Customer Community license can never be reassigned to the Partner Community license or any other license. Attempting to change the license on an existing profile throws an error. If you chose the wrong license, you must create a new profile and migrate users.
3. **`Auth.ConfigurableSelfRegHandler` vs legacy `Auth.RegistrationHandler`** — The legacy interface requires implementing `createUser(portalId, userId, registrationAttributes, password)` and `updateUser(...)`. The current interface (`Auth.ConfigurableSelfRegHandler`) uses a single `registerUser(context)` method with a richer `Auth.SelfRegistrationContext` object. LLMs trained on older material often generate the legacy signature; always verify which interface is expected in the Registration settings panel.
4. **Self-registration fails silently without a Default Account** — If the Default New User Account is not set in the Registration settings, self-registration POST requests return a generic error page with no useful debug output. This is the single most common self-reg setup mistake. Confirm the account is set and is not a Person Account (standard accounts only for the catch-all).
5. **Login page changes require a publish to take effect for structural changes** — Style-only changes (CSS, background colour) may propagate without a full publish in some scenarios, but adding or removing components on the login page always requires clicking Publish in Experience Builder before external users see the change.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Site membership configuration | Profile(s) added to the site's Members list in Administration |
| Self-registration settings | Default account, default profile, and optional handler class set in Registration panel |
| Login/registration page | Branded login page published in Experience Builder |
| External user record | User record tied to a Contact with the correct external profile and license |

---

## Related Skills

- flow/flow-for-experience-cloud — when a screen flow or guided process needs to be surfaced on the Experience Cloud site for self-registered or authenticated users
- security/experience-cloud-security — for deeper CORS, CSP, guest user access, and sharing-model security configuration on Experience Cloud sites
