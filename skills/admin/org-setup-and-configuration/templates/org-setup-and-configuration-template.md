# Org Setup And Configuration — Work Template

Use this template when setting up or reviewing org-level configuration settings.

---

## Scope

**Org:** _______________
**Environment:** Production / Sandbox / Scratch Org / Developer Org (circle one)
**Task type:** New setup / Reconfiguration / Review (circle one)
**Requested by:** _______________

---

## Context Gathered

- [ ] Is SSO / SAML configured or planned? If yes, My Domain must be deployed first.
- [ ] Are there external domains that need to load inside Lightning pages? List them:
  - `https://`
  - `https://`
- [ ] Are there office/VPN IP ranges that should be in Network Access (Trusted IPs)?
  - Range 1: ___ . ___ . ___ . ___ / ___
  - Range 2: ___ . ___ . ___ . ___ / ___
- [ ] Are there API-only integration users that must bypass MFA?

---

## My Domain

| Step | Status | Notes |
|------|--------|-------|
| Register My Domain (`company.my.salesforce.com`) | | |
| Verify new domain URL loads in browser | | |
| Update Connected App callback URLs to new domain | | |
| Update IdP / SSO metadata with new domain | | |
| Deploy to Users | | |
| Confirm enhanced domains (`myDomainSuffix` = `MySalesforce`, not `MySalesforceLimited`) | | |
| Re-assert `redirectPriorMyDomain` — it resets to `true` on every new domain deploy | | |
| `canOnlyLoginWithMyDomainUrl`: production value ______ / sandbox value ______ (must differ) | | |

**My Domain URL:** `https://_________________.my.salesforce.com`

---

## MFA Configuration

| Setting | Required Value | Configured Value | Status |
|---------|---------------|-----------------|--------|
| MFA enforcement org-wide toggle (`enableMFADirectUILoginOptIn`) | Enabled | | |
| SSO users: IdP enforces MFA (exempts Salesforce MFA) | Confirmed | | |
| API-only integration users: OAuth JWT/client creds OR waiver applied | Confirmed | | |
| **Waive Multi-Factor Authentication for Exempt Users** holders enumerated — this permission OVERRIDES the org toggle | Listed below | | |

---

## Session Settings

**Path:** Setup > Security > Session Settings

| Setting | Recommended | Metadata field (`sessionSettings`) | Current | Status |
|---|---|---|---|---|
| Session timeout | 2 hours (or lower for regulated) | `sessionTimeout` = `TwoHours` — enum, not minutes | | |
| Timeout warning popup shown | Yes | `disableTimeoutWarning` = `false` — `true` means NO warning | | |
| Force logout on session timeout | Enabled | `forceLogoutOnSessionTimeout` = `true` | | |
| Lock sessions to IP | Disabled (unless no mobile/VPN users) | `lockSessionsToIp` = `false` | | |
| Lock sessions to domain | Enabled | `lockSessionsToDomain` = `true` | | |
| Clickjack protection (non-setup Salesforce pages) | Enabled | `enableClickjackNonsetupSFDC` = `true` | | |
| Clickjack protection (setup pages) | Enabled | `enableClickjackSetup` = `true` | | |
| MFA required for direct UI logins | Enabled | `enableMFADirectUILoginOptIn` = `true` | | |
| Login IP Ranges enforced on every request | Per policy | `enforceIpRangesEveryRequest` | | |

---

## Password Policies

**Path:** Setup > Security > Password Policies

| Setting | Recommended | Metadata field (`passwordPolicies`) | Current | Status |
|---|---|---|---|---|
| Minimum password length | 10+ characters | `minimumPasswordLength` — a number 5–50, default 8 | | |
| Password complexity | Alpha + numeric + special | `complexity` = `UpperLowerCaseNumericSpecialCharacters` | | |
| Password expiration | 90 days (or `Never` if SSO+MFA only) | `expiration` = `NinetyDays` \| `Never` | | |
| Maximum invalid login attempts | 5 or fewer | `maxLoginAttempts` = `FiveAttempts` — enum, not a number | | |
| Lockout effective period | 15–30 minutes | `lockoutInterval` = `ThirtyMinutes` | | |
| Passwords remembered | 10+ | `historyRestriction` — 0–24, default 3 | | |

- [ ] "Expire All Passwords" triggered if policy was tightened from a prior setting

---

## Network Access (Trusted IP Ranges)

**Path:** Setup > Security > Network Access

> Deploying `Security.settings` REPLACES this list. Record every range that must survive the next deploy, not just the new one.

| Range description | Start IP | End IP | Purpose | Date Added |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

## CSP Trusted Sites

**Path:** Setup > Security > CSP Trusted Sites

| Site Name | Domain | Directives Granted | Business Justification |
|-----------|--------|--------------------|----------------------|
| | | | |
| | | | |

- [ ] No wildcard domains in the list
- [ ] Every entry grants only the directive(s) the browser console violation named (`isApplicableTo*`), each with a documented justification — there is no `script-src` grant in this type
- [ ] Stale/unused entries removed

---

## Final Verification Checklist

- [ ] My Domain deployed and all integration callback URLs updated
- [ ] MFA enforced; SSO users exempted via IdP; API users on OAuth flows
- [ ] Session timeout set; HTTPS enforced; clickjack protection configured
- [ ] Password policy meets minimum length and complexity requirements
- [ ] Trusted IP ranges added for legitimate office/VPN ranges only
- [ ] CSP Trusted Sites entries limited to required domains and specific directives
- [ ] Tested in sandbox before applying to production
- [ ] Change communicated to users where applicable (password expiry, domain change)

---

## Notes

(Record any deviations from standard guidance, exceptions granted, or follow-up items.)
