---
name: org-setup-and-configuration
description: "Use when configuring org-wide platform settings: MFA enforcement, My Domain setup and deployment, session timeout and security settings, password policies, trusted IP ranges (Network Access), and CSP Trusted Sites. Trigger keywords: 'MFA setup', 'My Domain', 'session settings', 'password policy', 'trusted IP ranges', 'CSP trusted sites'. NOT for user-level login restrictions (use user-management), NOT for permission model design (use permission-sets-vs-profiles), NOT for security audit and hardening review (use security/org-hardening-and-baseline-config)."
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
inputs:
  - "target org type (production, sandbox, scratch org, developer org)"
  - "identity provider or SSO requirements if applicable"
  - "list of external domains that must load on Lightning pages (for CSP)"
  - "network access requirements: office IP ranges, VPN ranges"
outputs:
  - "step-by-step configuration guidance for each org-level setting"
  - "review checklist confirming all settings are configured and deployed"
  - "decision table for session, password, and IP settings"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
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

## Core Concepts

### MFA Is Required For All Direct UI Logins

Salesforce enforced Multi-Factor Authentication for all users who access the Salesforce UI directly (Service Cloud, Sales Cloud, Experience Cloud internal users, Setup, etc.) starting February 1, 2022. This is a contractual requirement, not optional. SSO users whose identity provider performs MFA are exempt from the Salesforce-side enforcement because the IdP satisfies the requirement.

Configure MFA at: **Setup > Identity > MFA Management and Setup**

The org-level MFA enforcement toggle at **Setup > Security > Identity Verification** enables MFA for all applicable users in one step. Per-profile or permission-set-level MFA can also be set using the **Multi-Factor Authentication for User Interface Logins** system permission.

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
- **Timeout value**: Ranges from 15 minutes to 24 hours. The default is 2 hours. For regulated orgs, 15–30 minutes is recommended.
- **Lock sessions to the IP address from which they originated**: Prevents session hijacking by invalidating the session if requests arrive from a different IP. Has a side effect for users on mobile networks or DHCP-assigned IPs — sessions can break unexpectedly.
- **Force logout on session timeout**: On timeout, the user is logged out rather than silently having their session invalidated. Improves user experience when combined with short timeouts.
- **Require secure connections (HTTPS)**: Should always be enabled. Prevents plain-HTTP access.
- **Clickjack protection for non-setup Salesforce pages**: Prevents the org pages from being embedded in iframes on external sites. Should be set to **Allow framing by same origin only** unless there is a specific requirement to embed.

### Password Policies Are Org-Wide By Default But Can Be Overridden Per Profile

Password policies govern complexity, minimum length, expiration, and lockout. The org-wide policy lives at **Setup > Security > Password Policies**. Individual profiles can override these settings — go to **Setup > Profiles > [Profile Name]** and scroll to Password Policies.

Org-wide defaults (Salesforce baseline):
- Minimum length: 8 characters
- Complexity requirement: Must mix alpha and numeric (configurable to require special characters)
- Password expiration: 90 days (can be disabled or extended to 180 days or Never)
- Maximum invalid login attempts: 10 (can be reduced to 3 or 5 for higher-security orgs)
- Lockout effective period: 15 minutes after too many failed attempts

### Trusted IP Ranges Bypass Email Verification But Not MFA

**Setup > Security > Network Access** defines org-wide trusted IP ranges. When a user logs in from a trusted IP range, Salesforce does not send the email verification challenge that would otherwise occur for new browser/device logins. This is an org-wide setting.

Profile-level **Login IP Ranges** (under **Setup > Profiles > [Profile Name] > Login IP Ranges**) are a separate, more restrictive control — they block logins entirely from outside the specified ranges, rather than just skipping the email challenge. These are covered in the `admin/user-management` skill.

Trusted IP ranges do not bypass MFA. They only bypass the email verification step that occurs when Salesforce does not recognize the browser or device.

### CSP Trusted Sites Allow External Resources On Lightning Pages

Lightning Experience uses a Content Security Policy that blocks external resources by default. If a Lightning page, LWC, or Visualforce page must load resources from an external domain, that domain must be added to **Setup > Security > CSP Trusted Sites** (also labeled **Trusted URLs** in newer API versions).

For each entry you specify the directive context:
- **connect-src**: Allows `fetch()` / `XHR` / WebSocket calls to the domain (API calls from LWC)
- **style-src**: Allows CSS stylesheets from the domain
- **img-src**: Allows images from the domain
- **font-src**: Allows font files from the domain
- **frame-src**: Allows iframes embedding content from the domain
- **media-src**: Allows audio/video content from the domain

**Important:** `script-src` cannot be relaxed via CSP Trusted Sites. Salesforce does not allow external JavaScript execution via this control — `unsafe-inline` and external script hosts are blocked by platform design. Loading JavaScript from an external domain requires a different approach (e.g., static resources).

A CSP violation does not produce a Salesforce error message visible to the user — it is a browser console error. This makes blocked resources harder to diagnose.

---

## Common Patterns

### New Org Security Baseline Setup

**When to use:** A new production or sandbox org needs all baseline security settings configured before users are provisioned.

**How it works:**
1. Navigate to **Setup > Company Settings > My Domain**. Register the domain. Wait for Salesforce to provision it (up to 24 hours for production).
2. Test the My Domain URL in a browser. Navigate to **My Domain > Deploy to Users** only after verifying logins work.
3. Navigate to **Setup > Identity > MFA Management and Setup** (or **Setup > Security > Identity Verification**). Enable the **Require MFA for all direct logins** org-level toggle.
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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] My Domain is registered, deployed, and all users log in via the custom domain URL.
- [ ] MFA is enforced org-wide (or via IdP) for all human UI users.
- [ ] Session timeout reflects org security policy (default 2 hours; lower for regulated orgs).
- [ ] HTTPS-only and clickjack protection are enabled in Session Settings.
- [ ] Password policy minimum length is at least 10 characters with complexity requirements.
- [ ] Trusted IP ranges added for office/VPN networks; no unnecessary CIDR ranges included.
- [ ] CSP Trusted Sites entries exist only for domains actually required; no wildcard entries.
- [ ] API-only integration users either use OAuth flows or have an explicit MFA waiver policy.
- [ ] Settings have been verified in a sandbox before deploying to production.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **My Domain changes break hardcoded login URLs in integrations** — After deploying My Domain, any external system that uses the old `login.salesforce.com` or `test.salesforce.com` URL in OAuth callbacks or SAML redirects must be updated to the new `mycompany.my.salesforce.com` URL. This includes managed packages, Connected Apps, and IdP configurations.
2. **Locking sessions to IP breaks mobile users** — The "Lock sessions to IP address" setting in Session Settings causes session invalidation whenever the client IP changes. Mobile users on cellular networks change IP frequently; enabling this causes unexpected logouts. Do not enable for orgs with significant mobile usage.
3. **Trusted IP ranges skip email verification, not MFA** — A common misunderstanding is that adding an office IP to Network Access (Trusted IP Ranges) will remove MFA prompts for those users. It does not. It only removes the one-time email identity verification challenge that occurs on new browsers. MFA challenges remain unless explicitly waived.
4. **CSP violations appear only in browser console** — When a CSP Trusted Site is missing or misconfigured, users see a generic "resource blocked" or silent failure — not a Salesforce error. Always open DevTools/Console when diagnosing missing images, broken API calls, or missing styles on Lightning pages.
5. **Password policy changes do not force an immediate reset** — Tightening the password policy (e.g., reducing expiration from 90 to 30 days) does not immediately expire existing passwords. The new policy applies at the user's next natural expiration or manual reset. If an immediate reset is required, use the mass "Expire Passwords" button at the bottom of the Password Policies page.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Org settings configuration checklist | Completed review checklist confirming all org-level settings are configured |
| CSP Trusted Sites list | Documented list of external domains and directive types with business justification |
| My Domain deployment status | Confirmation that My Domain is deployed and all callback URLs are updated |

---

## Related Skills

- `security/org-hardening-and-baseline-config` — use when the goal is auditing/reviewing security controls across the org baseline, not initial configuration.
- `admin/user-management` — use when the goal is profile-level login hours, per-user login IP restrictions, or freezing/deactivating users.
- `admin/permission-sets-vs-profiles` — use when configuring which users require MFA via the system permission rather than the org-wide toggle.
