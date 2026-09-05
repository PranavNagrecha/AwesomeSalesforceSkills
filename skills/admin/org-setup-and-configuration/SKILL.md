---
name: org-setup-and-configuration
description: "Use when configuring org-wide platform settings: MFA enforcement, My Domain setup and deployment, session timeout and security settings, password policies, trusted IP ranges (Network Access), and CSP Trusted Sites. Owns these settings as deployable Settings metadata (Security.settings, MyDomain.settings, Company.settings, Language.settings) and the order in which a new org is stood up. Trigger keywords: 'MFA setup', 'My Domain', 'session settings', 'password policy', 'trusted IP ranges', 'CSP trusted sites', 'Security.settings', 'SecuritySettings metadata', 'MyDomainSettings', 'settings-meta.xml', 'enhanced domains', 'deploy org settings', 'new org setup order', 'sessionTimeout enum', 'lockSessionsToIp', 'enableAdminLoginAsAnyUser'. NOT for user-level login restrictions (use user-management), NOT for permission model design (use permission-sets-vs-profiles), NOT for security audit and hardening review (use security/org-hardening-and-baseline-config)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
tags:
  - org-setup
  - mfa
  - my-domain
  - session-settings
  - csp-trusted-sites
triggers:
  - "how do I enable MFA for all users in my Salesforce org"
  - "how to set up and deploy My Domain in Salesforce"
  - "configure session timeout and login security settings"
  - "set password expiration and complexity rules for the org"
  - "add a trusted IP range so users skip email verification"
  - "CSP trusted site blocked external resource on Lightning page"
  - "deploying Security.settings wiped our trusted IP ranges"
  - "sessionTimeout deploy failed with an invalid enum value"
  - "stand up a brand new production org in the right order"
  - "changing myDomainName in MyDomain.settings does nothing"
  - "users on cellular keep getting logged out of Salesforce"
  - "MFA is enabled org-wide but some users are never prompted"
  - "what order do I configure My Domain, MFA and session settings"
  - "how do I tell if enhanced domains are on from the metadata"
inputs:
  - "target org type (production, sandbox, scratch org, developer org)"
  - "identity provider or SSO requirements if applicable"
  - "list of external domains that must load on Lightning pages (for CSP)"
  - "network access requirements: office IP ranges, VPN ranges"
  - "retrieved settings/ directory from the target org (Security, MyDomain, Company, Language)"
outputs:
  - "step-by-step configuration guidance for each org-level setting"
  - "review checklist confirming all settings are configured and deployed"
  - "decision table for session, password, and IP settings"
  - "deployable settings/*.settings-meta.xml plus the package.xml that carries them"
  - "verification SOQL against the Organization object"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Org Setup And Configuration

Use this skill when the task is configuring org-wide platform settings that govern how all users authenticate, how sessions behave, how passwords are managed, and which external resources can load. These settings live under Setup > Security and Setup > Company Settings. They are set once (or reviewed periodically) and affect every user in the org.

This skill covers hands-on configuration steps. For security auditing and governance review, use `security/org-hardening-and-baseline-config`.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is this a net-new org setup or a reconfiguration of an existing production org?
- Are there SSO or identity provider requirements that depend on My Domain being deployed first?
- What external systems (CDN providers, embedded analytics, third-party widgets) load resources inside Lightning pages — these require CSP Trusted Sites entries.
- Are there office networks or VPN IP ranges that should bypass email verification for logins?

---

## Questions to Ask Before Configuring

Ask these before opening Setup or writing a `.settings` file. Each one maps to a documented platform behaviour that turns a "successful" deploy into an incident.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Has anyone retrieved this org's `Security.settings` yet, and where is it?" | `networkAccess` is replace-in-place: deploying a file with one IP range deletes every other range in the org | A retrieved baseline file to edit, plus the current trusted-IP list to diff against |
| "Is My Domain already registered and deployed, and is it enhanced?" | The domain name is read-only in the API — it cannot be promoted from a sandbox, and `myDomainSuffix` is the only enhanced-domains signal | The stand-up order: domain first, then SSO callbacks, then MFA |
| "Who holds the MFA waiver permission today?" | The **Waive Multi-Factor Authentication for Exempt Users** permission overrides the org-wide MFA setting | The exempt-user inventory, so "MFA is on" means something |
| "What fraction of users are on cellular, VPN, or shifting NAT egress?" | `lockSessionsToIp` invalidates a session the moment the source IP changes | A yes/no on IP-locking with a stated user population behind it |
| "What is the real timeout requirement in minutes, and what enum is nearest?" | `sessionTimeout` is an enum — there is no 45-minute option, and a number fails the deploy | The rounding decision recorded before it becomes a deploy error |
| "Which environments must differ, and which must match?" | `canOnlyLoginWithMyDomainUrl` set to `true` in a sandbox disables the Sandboxes-page Log In action | A per-environment value list, so a diff tool does not "fix" a deliberate divergence |
| "Which Connected Apps, IdP configs, and CSP entries reference the current URLs?" | A domain change breaks callbacks; an API-version bump changes CSP default-grant behaviour | The blast-radius list to re-verify after the deploy |

What a proper configuration adds over just clicking through Setup: the org's authentication baseline exists as a reviewable, diffable file that can be validated before it lands, the settings that genuinely cannot be deployed are named rather than silently assumed, and the exceptions — waivers, per-environment divergences, IP-locking carve-outs — are written down instead of discovered by a locked-out user.

---

## Core Concepts

### Org-Wide Settings Are Deployable Metadata, With Sharp Edges

Most of what this skill configures is one metadata type per Setup page, retrieved and deployed as a single file. "Each settings component gets stored in a single file in the `settings` directory … The filename uses the format `Setting feature.settings`" (Metadata API Developer Guide, `Settings`). The manifest name is always `Settings`; the member is the type name minus the suffix, so `SecuritySettings` is `<members>Security</members>`.

| Setup area | Metadata type | Manifest member | File |
|---|---|---|---|
| Session Settings, Password Policies, Network Access, SSO, login-as | `SecuritySettings` | `Security` | `settings/Security.settings-meta.xml` |
| My Domain routing, redirects, cookies | `MyDomainSettings` | `MyDomain` | `settings/MyDomain.settings-meta.xml` |
| Fiscal year | `CompanySettings` | `Company` | `settings/Company.settings-meta.xml` |
| ICU locale formats, translation, end-user languages | `LanguageSettings` | `Language` | `settings/Language.settings-meta.xml` |
| CSP Trusted Sites / Trusted URLs | `CspTrustedSite` (not a settings file) | site name or `*` | `cspTrustedSites/<Name>.cspTrustedSite-meta.xml` |

Three constraints govern every deploy of these files:

1. **Whole containers replace, they do not merge.** Documented explicitly for `networkAccess.ipRanges`: deploy every range you want to keep, or the ones you omit are gone. Always retrieve before you edit.
2. **Some fields are read-only in the API.** `myDomainName`, `myDomainSuffix`, `domainPartition`, `edgeRoutingMethod` and `useEdge` are all marked read-only — the domain is a Setup action, not a promotable artefact.
3. **Not everything is in the API at all.** "Not all feature settings are available in Metadata API," and for unsupported types "you must do it manually in each of your organizations." Check the Metadata Coverage report before promising a setting will travel.

The org's default locale, time zone and currency are not in any of these files — they are updatable fields on the `Organization` standard object (`DefaultLocaleSidKey`, `TimeZoneSidKey`, `LanguageLocaleKey`). See `references/metadata-examples.md` for the deployable files, the package.xml, and the verification SOQL.

### Stand-Up Order For A New Org

Order matters because each step's output is the next step's input, and two of the steps are irreversible.

| # | Step | Blocks | Why this position |
|---|---|---|---|
| 1 | Company Information: locale, time zone, currency, fiscal year | Everything date- or money-shaped | These become baked into records; changing fiscal year can purge quotas and adjustments |
| 2 | Register My Domain, test, then Deploy to Users | SSO, OAuth, Lightning, packages | The login URL every later step references |
| 3 | Update Connected App callbacks and IdP metadata | SSO cutover | Must happen against the final domain, not the old one |
| 4 | `Security.settings`: session, password, network access, login-as | User provisioning | The baseline every user inherits on creation |
| 5 | MFA enforcement plus the waiver inventory | Go-live | Needs step 3 done, so SSO users are exempt via the IdP rather than double-prompted |
| 6 | CSP Trusted Sites | Lightning pages with external content | Needs the component inventory, which usually lands last |

Steps 1 and 2 are the irreversible ones in practice: fiscal-year changes can purge forecast data, and a deployed My Domain becomes the org's identity across every integration.


### MFA Is Required For All Direct UI Logins

Salesforce enforced Multi-Factor Authentication for all users who access the Salesforce UI directly (Service Cloud, Sales Cloud, Experience Cloud internal users, Setup, etc.) starting February 1, 2022. This is a contractual requirement, not optional. SSO users whose identity provider performs MFA are exempt from the Salesforce-side enforcement because the IdP satisfies the requirement.

Configure MFA from Setup, using the Quick Find box to find and select **Identity Verification**, then selecting **Require multi-factor authentication (MFA) for all direct UI logins to your Salesforce org**. That single setting enables MFA for all applicable users. (Setup also has a separate **Multi-Factor Authentication Assistant** node — a rollout guide, not the enforcement switch. There is no Setup node named "MFA Management and Setup".) Per-profile or permission-set-level MFA can also be set using the **Multi-Factor Authentication for User Interface Logins** system permission.

### My Domain Is Required For Many Features

My Domain assigns a unique subdomain to your org (e.g., `mycompany.my.salesforce.com`). It is required for:
- Lightning Experience login (must be deployed before enabling Lightning)
- Single Sign-On (SSO) configurations — SAML IdPs require a stable login URL
- OAuth authorization flows using the org's custom domain
- OmniStudio and many AppExchange managed packages
- Salesforce1 mobile app custom branding

My Domain has two phases: **Register** (requests the subdomain from Salesforce infrastructure — can take up to 24 hours) and **Deploy to Users** (switches users to the new login URL). Do not deploy until you have tested the new domain in a sandbox or developer org first.

Navigate to: **Setup > Company Settings > My Domain**

### Session Settings Control Authentication Behavior Org-Wide

Session settings define how long an authenticated session lasts, whether sessions are locked to the originating IP, whether HTTPS is enforced, and clickjack protection levels. These settings apply to all users unless a Connected App or profile overrides session timeout.

Navigate to: **Setup > Security > Session Settings**

Key settings:

| Setting | Metadata field | Behavior |
|---|---|---|
| Timeout value | `sessionTimeout` | An enum, not a number of minutes. The documented members are `FifteenMinutes`, `ThirtyMinutes`, `SixtyMinutes`, `NinetyMinutes` (API 58.0+), `TwoHours`, `FourHours`, `EightHours`, `TwelveHours`, `TwentyFourHours` (API 38.0+) — so 15 minutes to 24 hours, with no 45-minute option. UNVERIFIED (2026-09-04): the commonly cited 2-hour default is not stated as a default in the `SessionSettings` field table; check the target org rather than assuming. For regulated orgs, 15–30 minutes is recommended. |
| Lock sessions to the IP address from which they originated | `lockSessionsToIp` | Invalidates the session if requests arrive from a different IP. Breaks users on cellular, shifting VPN egress, or DHCP/NAT pools. |
| Force logout on session timeout | `forceLogoutOnSessionTimeout` | `true` (the documented default): at timeout the session becomes invalid, the browser refreshes and returns to the login page. |
| Show the timeout warning popup | `disableTimeoutWarning` | Inverted: `true` **disables** the warning. Independent of forced logout — set both explicitly. |
| Require secure connections (HTTPS) | `requireHttps` | "Enabled by default for security reasons and can't be disabled." The field exists only in API versions 40.0–60.0; `enableRequireHttpsConnection` is deprecated from 47.0. It is not a lever you set on a current API version. |
| Clickjack protection | `enableClickjackSetup`, `enableClickjackNonsetupSFDC`, `enableClickjackNonsetupUser`, `enableClickjackNonsetupUserHeaderless` | Four separate booleans, not one dropdown: setup pages, non-setup Salesforce pages, and customer Visualforce pages with and without standard headers. Enable all four unless a specific page must be framed externally. |

### Password Policies Are Org-Wide By Default But Can Be Overridden Per Profile

Password policies govern complexity, minimum length, expiration, and lockout. The org-wide policy lives at **Setup > Security > Password Policies** and deploys as the `passwordPolicies` container inside `Security.settings`. Individual profiles can override these settings in Setup — go to **Setup > Profiles > [Profile Name]** and scroll to Password Policies.

That profile-level override does **not** travel in a `Profile` deploy: the `Profile` metadata type's field table contains no password-policy fields at all (it carries `loginHours` and `loginIpRanges`, but nothing about passwords). Treat profile password overrides as per-org manual configuration and record them in the template, or the promoted org-wide policy will silently be the only thing that moves between environments.

Documented platform defaults and their metadata fields:

| Policy | Field | Default | Range |
|---|---|---|---|
| Minimum length | `minimumPasswordLength` | 8 | a number, 5 to 50 |
| Complexity | `complexity` | `AlphaNumeric` | up to `Any3UpperLowerCaseNumericSpecialCharacters` (API 46.0+) |
| Expiration | `expiration` | `NinetyDays` | `Never`, `ThirtyDays`, `SixtyDays`, `NinetyDays`, `SixMonths`, `OneYear` — there is no 180-day member |
| Max invalid login attempts | `maxLoginAttempts` | `TenAttempts` | `NoLimit`, `ThreeAttempts`, `FiveAttempts`, `TenAttempts` |
| Lockout period | `lockoutInterval` | `FifteenMinutes` | `FifteenMinutes`, `ThirtyMinutes`, `SixtyMinutes`, `Forever` |
| Passwords remembered | `historyRestriction` | 3 | 0 to 24 (24 max applies to API 31.0+) |

### Trusted IP Ranges Bypass Email Verification But Not MFA

**Setup > Security > Network Access** defines org-wide trusted IP ranges. When a user logs in from a trusted IP range, Salesforce does not send the email verification challenge that would otherwise occur for new browser/device logins. This is an org-wide setting.

Profile-level **Login IP Ranges** (under **Setup > Profiles > [Profile Name] > Login IP Ranges**) are a separate, more restrictive control — they block logins entirely from outside the specified ranges, rather than just skipping the email challenge. These are covered in the `admin/user-management` skill.

Trusted IP ranges do not bypass MFA. They only bypass the email verification step that occurs when Salesforce does not recognize the browser or device.

### CSP Trusted Sites Allow External Resources On Lightning Pages

Lightning Experience uses a Content Security Policy that blocks external resources by default. If a Lightning page, LWC, or Visualforce page must load resources from an external domain, that domain must be added to **Setup > Security > CSP Trusted Sites** (also labeled **Trusted URLs** in newer API versions).

For each entry you specify the directive context:

| Directive | Allows |
|---|---|
| connect-src | `fetch()` / `XHR` / WebSocket calls to the domain (API calls from LWC) |
| style-src | CSS stylesheets from the domain |
| img-src | Images from the domain |
| font-src | Font files from the domain |
| frame-src | Iframes embedding content from the domain |
| media-src | Audio/video content from the domain |

**Important:** `script-src` cannot be relaxed via CSP Trusted Sites. Salesforce does not allow external JavaScript execution via this control — `unsafe-inline` and external script hosts are blocked by platform design. Loading JavaScript from an external domain requires a different approach (e.g., static resources).

A CSP violation does not produce a Salesforce error message visible to the user — it is a browser console error. This makes blocked resources harder to diagnose.

---

## Common Patterns

### New Org Security Baseline Setup

**When to use:** A new production or sandbox org needs all baseline security settings configured before users are provisioned.

**How it works:**
1. Navigate to **Setup > Company Settings > My Domain**. Register the domain. Wait for Salesforce to provision it (up to 24 hours for production).
2. Test the My Domain URL in a browser. Navigate to **My Domain > Deploy to Users** only after verifying logins work.
3. From Setup, Quick Find > **Identity Verification**. Enable **Require multi-factor authentication (MFA) for all direct UI logins to your Salesforce org**.
4. Navigate to **Setup > Security > Session Settings**. Set timeout to 2 hours (or lower for regulated environments). Enable HTTPS. Set clickjack protection to "Allow framing by same origin only."
5. Navigate to **Setup > Security > Password Policies**. Set minimum length to 10 characters, complexity to require alphanumeric plus special characters, expiration to 90 days or Never (if relying solely on SSO/MFA), lockout to 5 attempts.
6. Navigate to **Setup > Security > Network Access**. Add office/VPN IP ranges that should bypass the email verification challenge.
7. Navigate to **Setup > Security > CSP Trusted Sites**. Add only the external domains required for existing integrations or components.

### Adding A CSP Trusted Site For An Integration

**When to use:** A LWC or Lightning page tries to call an external API and you see CORS or CSP errors in the browser console.

**How it works:**
1. Open browser DevTools (F12). Check the Console for a CSP violation message. The message will name the blocked domain and the violated directive (e.g., `connect-src`).
2. Navigate to **Setup > Security > CSP Trusted Sites > New Trusted Site**.
3. Enter the domain (include the protocol: `https://api.example.com`). Check only the directive types that are actually needed — avoid checking all directives as a shortcut.
4. Save and refresh the Lightning page. Test the resource load.
5. For Apex-side callouts (server-side HTTP requests), CSP Trusted Sites are not needed — instead use **Setup > Security > Remote Site Settings**.

### MFA Enforcement Without Disrupting API-Only Integration Users

**When to use:** The org has API-only integration users (for data sync tools, ETL, managed packages) that connect via username/password and cannot use MFA.

**How it works:** API-only users should be assigned the **API Only** user profile flag (`userLicense: Salesforce Integration` or the legacy `System Administrator` profile with the **API Only** system permission). Users with `User Interface: No` or the **Waive Multi-Factor Authentication for Exempt Users** permission can bypass MFA enforcement. Check: **Setup > Identity > MFA Exemptions**.

Alternatively, convert API integrations to OAuth 2.0 JWT bearer flow or Connected App client credential flow, which do not use username/password and are not subject to MFA requirements.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New org, Lightning Experience required | Deploy My Domain first, then enable Lightning | Lightning Experience requires My Domain |
| SSO via SAML required | Deploy My Domain before configuring the IdP | SAML callback URL must include the custom domain |
| Users on mobile networks losing sessions | Do NOT lock sessions to originating IP | Mobile users frequently change IP; locking breaks sessions |
| Regulated environment (HIPAA, SOC 2) | Set session timeout to 15–30 min, lockout at 3–5 attempts | Compliance frameworks often mandate short session lifetimes |
| External resource blocked in Lightning page | Add CSP Trusted Site for that domain + directive | Salesforce LWC CSP blocks all external origins by default |
| API integration user must bypass MFA | Use OAuth JWT/client credential flow or apply MFA waiver permission | Username/password API flows should not be MFA-exempt without a deliberate policy decision |
| Multiple office locations with different IPs | Add all office/VPN CIDR ranges to Network Access | Users in trusted ranges skip unnecessary email challenges |

---


## Recommended Workflow

1. **Answer the seven questions above**, then retrieve the current state — `sf project retrieve start --metadata "Settings:Security" "Settings:MyDomain" "Settings:Company" "Settings:Language"`. Never author a settings file from a template; `networkAccess` replaces rather than merges, so the retrieved file is the only safe starting point (`references/gotchas.md` gotcha 6).
2. **Fix the stand-up position** using the order table above. If My Domain is not yet deployed, stop and do that first — steps 3 to 6 all reference the final login URL, and `myDomainName` cannot be deployed (gotcha 7).
3. **Edit the retrieved files** against the field tables and enum lists in `references/metadata-examples.md`. Every value in `sessionTimeout`, `maxLoginAttempts`, `lockoutInterval`, `complexity` and `expiration` must be one of the documented enum members — the guide's lists are reproduced there so you do not have to guess (gotcha 9).
4. **Lint before you deploy** — `python3 scripts/check_org_setup_and_configuration.py --manifest-dir force-app/main/default`. It catches invalid enums, a password minimum below the platform default, IP-locking and admin-login-as risk flags, a non-enhanced My Domain suffix, and duplicate `Settings` members in package.xml.
5. **Validate, then deploy to a sandbox first** — `sf project deploy validate`, then `sf project deploy start` against the sandbox. Confirm `Organization.IsSandbox` is `true` before you run it and `false` before you repeat it in production.
6. **Verify in the org, not in the file** — run the `Organization` verification SOQL and walk the 8-row Setup checklist at the end of `references/metadata-examples.md`. Re-retrieve `Settings:Security` and diff: the stored value is the only proof the enum you wrote is the enum the org kept.
7. **Record the exceptions** in `templates/org-setup-and-configuration-template.md` — MFA waiver holders, per-environment divergences such as `canOnlyLoginWithMyDomainUrl`, and every CSP trusted site with its business justification. These are the items no gate can re-derive later.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] My Domain is registered, deployed, and all users log in via the custom domain URL.
- [ ] MFA is enforced org-wide (or via IdP) for all human UI users.
- [ ] Session timeout is a documented `sessionTimeout` enum member that matches org security policy (`TwoHours` as a baseline; `FifteenMinutes`/`ThirtyMinutes` for regulated orgs).
- [ ] HTTPS-only and clickjack protection are enabled in Session Settings.
- [ ] Password policy minimum length is at least 10 characters with complexity requirements.
- [ ] Trusted IP ranges added for office/VPN networks; no unnecessary CIDR ranges included.
- [ ] CSP Trusted Sites entries exist only for domains actually required; no wildcard entries.
- [ ] API-only integration users either use OAuth flows or have an explicit MFA waiver policy.
- [ ] Settings have been verified in a sandbox before deploying to production.
- [ ] `Security.settings` was **retrieved** from the target org before editing, and the deployed `ipRanges` list contains every range that must survive.
- [ ] Every enum value (`sessionTimeout`, `maxLoginAttempts`, `lockoutInterval`, `complexity`, `expiration`) is a documented member, not a number or an invented name.
- [ ] `scripts/check_org_setup_and_configuration.py --manifest-dir <path>` reports no ERROR, and every WARN and INFO has been read and accepted rather than tuned away.
- [ ] Per-environment divergences (`canOnlyLoginWithMyDomainUrl`, and any others) are recorded in the template so a later diff does not "fix" them.
- [ ] The MFA waiver-permission holder list has been enumerated — the org-wide toggle alone does not prove enforcement.
- [ ] Profile-level password overrides, which do not travel in a `Profile` deploy, are documented as manual per-org configuration.
- [ ] `SELECT IsSandbox, InstanceName FROM Organization` was run against the target org before the production deploy.

---

## Salesforce-Specific Gotchas

The five that bite most often are below. `references/gotchas.md` carries all thirteen with the full **What happens / When it occurs / How to avoid** treatment, including the deploy-time behaviours that only appear once these settings are source-controlled: `networkAccess` replacing rather than merging, `myDomainName` being read-only in the API, `redirectPriorMyDomain` resetting on every domain deploy, the enum-vs-number trap, the MFA waiver overriding the org switch, `disableTimeoutWarning` being inverted, `canOnlyLoginWithMyDomainUrl` disabling the sandbox Log In action, and the CSP default-grant behaviour changing across API versions.

1. **My Domain changes break hardcoded login URLs in integrations** — After deploying My Domain, any external system that uses the old `login.salesforce.com` or `test.salesforce.com` URL in OAuth callbacks or SAML redirects must be updated to the new `mycompany.my.salesforce.com` URL. This includes managed packages, Connected Apps, and IdP configurations.
2. **Locking sessions to IP breaks mobile users** — The "Lock sessions to IP address" setting in Session Settings causes session invalidation whenever the client IP changes. Mobile users on cellular networks change IP frequently; enabling this causes unexpected logouts. Do not enable for orgs with significant mobile usage.
3. **Trusted IP ranges skip email verification, not MFA** — A common misunderstanding is that adding an office IP to Network Access (Trusted IP Ranges) will remove MFA prompts for those users. It does not. It only removes the one-time email identity verification challenge that occurs on new browsers. MFA challenges remain unless explicitly waived.
4. **CSP violations appear only in browser console** — When a CSP Trusted Site is missing or misconfigured, users see a generic "resource blocked" or silent failure — not a Salesforce error. Always open DevTools/Console when diagnosing missing images, broken API calls, or missing styles on Lightning pages.
5. **Password policy changes do not force an immediate reset** — Tightening the password policy (e.g., reducing expiration from 90 to 30 days) does not immediately expire existing passwords. The new policy applies at the user's next natural expiration or manual reset. If an immediate reset is required, use the mass **Expire All Passwords** action at the bottom of the Password Policies page.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Org settings configuration checklist | Completed review checklist confirming all org-level settings are configured |
| CSP Trusted Sites list | Documented list of external domains and directive types with business justification |
| My Domain deployment status | Confirmation that My Domain is deployed and all callback URLs are updated |
| `settings/*.settings-meta.xml` + `package.xml` | The deployable org baseline: Security, MyDomain, Company, Language (`references/metadata-examples.md`) |
| Checker output | `scripts/check_org_setup_and_configuration.py` findings, with each WARN/INFO accepted or actioned |
| Exception register | MFA waiver holders, per-environment divergences, profile-level password overrides, CSP entries with justification |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the deployable XML: `Security.settings`, `MyDomain.settings`, `Company.settings`, `Language.settings`, `CspTrustedSite`, package.xml, retrieve/deploy commands, verification SOQL |
| `references/gotchas.md` | Before any settings deploy — the thirteen platform behaviours that turn a green deploy into a lockout |
| `references/examples.md` | Working an end-to-end scenario: new-org go-live, a CSP violation, a password-expiry cliff |
| `references/well-architected.md` | Justifying a tradeoff (Salesforce MFA vs IdP MFA, timeout vs convenience, IP-locking vs MFA) and finding the official sources |
| `references/llm-anti-patterns.md` | Reviewing AI-generated org-setup guidance before acting on it |
| `templates/org-setup-and-configuration-template.md` | Recording the work: settings values, waiver holders, IP ranges, CSP justifications |

---

## Related Skills

- `security/org-hardening-and-baseline-config` — use when the goal is auditing/reviewing security controls across the org baseline, not initial configuration.
- `admin/user-management` — use when the goal is profile-level login hours, per-user login IP restrictions, or freezing/deactivating users.
- `admin/permission-sets-vs-profiles` — use when configuring which users require MFA via the system permission rather than the org-wide toggle, or when placing `loginIpRanges` on a Profile.
- `security/mfa-enforcement-patterns` — use when designing the MFA rollout itself: verification methods, enrolment waves, exemption policy.
- `security/mfa-enforcement-strategy` — use when the question is the org-level MFA position and its compliance framing rather than the setting that expresses it.
- `security/session-management-and-timeout` — use when the session policy needs designing across profiles, Connected Apps and Experience Cloud rather than expressed as one org value.
- `security/session-high-assurance-policies` — use when specific operations must demand a stronger session than the org baseline.
- `security/ip-range-and-login-flow-strategy` — use when deciding between trusted IP ranges, profile login IP ranges, and Login Flows as the network control.
- `security/oauth-redirect-and-domain-strategy` — use when a My Domain change affects OAuth callbacks, redirect URIs, or hard-coded URLs in integrations.
- `admin/salesforce-release-preparation` — use when a seasonal release or Release Update changes one of these settings' defaults.
