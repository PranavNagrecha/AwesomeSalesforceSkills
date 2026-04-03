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

**My Domain URL:** `https://_________________.my.salesforce.com`

---

## MFA Configuration

| Setting | Required Value | Configured Value | Status |
|---------|---------------|-----------------|--------|
| MFA enforcement org-wide toggle | Enabled | | |
| SSO users: IdP enforces MFA (exempts Salesforce MFA) | Confirmed | | |
| API-only integration users: OAuth JWT/client creds OR waiver applied | Confirmed | | |

---

## Session Settings

**Path:** Setup > Security > Session Settings

| Setting | Recommended | Current | Status |
|---------|------------|---------|--------|
| Session timeout | 2 hours (or lower for regulated) | | |
| Require secure connections (HTTPS) | Enabled | | |
| Lock sessions to IP | Disabled (unless no mobile users) | | |
| Force logout on session timeout | Enabled | | |
| Clickjack protection (non-setup pages) | Same origin only | | |

---

## Password Policies

**Path:** Setup > Security > Password Policies

| Setting | Recommended | Current | Status |
|---------|------------|---------|--------|
| Minimum password length | 10+ characters | | |
| Password complexity | Alpha + numeric + special | | |
| Password expiration | 90 days (or Never if SSO+MFA only) | | |
| Maximum invalid login attempts | 5 or fewer | | |
| Lockout effective period | 15–30 minutes | | |

- [ ] "Expire All Passwords" triggered if policy was tightened from a prior setting

---

## Network Access (Trusted IP Ranges)

**Path:** Setup > Security > Network Access

| Range | CIDR | Purpose | Date Added |
|-------|------|---------|------------|
| | | | |
| | | | |

---

## CSP Trusted Sites

**Path:** Setup > Security > CSP Trusted Sites

| Site Name | Domain | Directives Granted | Business Justification |
|-----------|--------|--------------------|----------------------|
| | | | |
| | | | |

- [ ] No wildcard domains in the list
- [ ] All `script-src` entries have documented justification
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
