# Multi-Site Architecture — Decision Template

Use this template when designing or reviewing a multi-site Experience Cloud strategy. Fill in each section before making architecture decisions.

---

## Project Context

**Org:** (org name and My Domain name)
**Edition:** (Essential / Professional / Enterprise / Unlimited / Developer)
**Request summary:** (what the business has asked for)
**Date:** YYYY-MM-DD

---

## Site Inventory (Current State)

Run `Setup > Digital Experiences > All Sites` and record the current count.

| Status | Count |
|---|---|
| Active (live) | |
| Preview (admin only) | |
| Inactive (deactivated) | |
| **Total** | |
| **Remaining quota** (100 − Total) | |

Sites to consider deleting before this project:
- (list names of inactive or abandoned sites)

---

## Proposed Site Topology

For each site in the new topology, complete one row:

| Site Name | API Name (path segment) | Audience Type | License Type | URL (prod) | URL (sandbox) | Guest access? |
|---|---|---|---|---|---|---|
| | | | | | | Yes / No |
| | | | | | | Yes / No |
| | | | | | | Yes / No |

Total new sites this project adds: ___
Total org site count after project: ___

---

## Domain Strategy

**Custom domain required?** Yes / No
- If yes: confirm org is Enterprise+ and that configuration will be done in production only.

**Production URL base:** `https://_______________`
**Sandbox URL base:** `https://_______________`.sandbox.my.site.com

**Per-site URL paths:**
| Site | Prod URL | Sandbox URL |
|---|---|---|
| | | |
| | | |

**DNS and SSL requirements:**
- CNAME target: (provided by Salesforce during custom domain setup)
- SSL certificate: (Salesforce-managed or customer-provided)

**Site base URL configuration approach:**
- [ ] Custom Metadata (`Site_Config__mdt`) with per-environment records
- [ ] Named Credential
- [ ] Other: (describe)

---

## Shared Component Library

List LWC components that will be shared across two or more sites:

| Component Name | Shared Across Sites | Configurable `@api` Properties | Guest Access Required? |
|---|---|---|---|
| | | | Yes / No |
| | | | Yes / No |
| | | | Yes / No |

For each component that requires guest access, record the per-site guest profile permissions required:

| Component | Site | Object / Field | Permission Required |
|---|---|---|---|
| | | | Read / Read+Create |
| | | | |

---

## Cross-Site Navigation Design

| Journey | Source Site | Target Site | Auth state at boundary | SSO handles it? | UX if no SSO |
|---|---|---|---|---|---|
| | | | Authenticated | Yes / No | Login page |
| | | | Guest | Yes / No | N/A |

**SSO configuration:**
- External IdP in use: (Okta / Azure AD / Ping / None)
- Sites registered as Service Providers with IdP: (list)
- If no SSO: document the expected re-authentication UX at each cross-site boundary

---

## License Allocation

| Audience | Site | License Type | Estimated User Count | Notes |
|---|---|---|---|---|
| Customers | | Customer Community / Customer Community Plus | | |
| Partners | | Partner Community | | |
| Employees | | Employee Community / Salesforce license | | |

Users needing access to multiple sites with different license type requirements:
- (identify user segments that need both Customer and Partner access, for example)
- License resolution: (higher-tier license, separate login, or not supported)

---

## Security Configuration Checklist (per site)

Complete once for each site in the topology:

**Site: _______________________**
- [ ] Guest user profile reviewed — least-privilege access only
- [ ] HTTPS enforcement enabled
- [ ] Clickjack protection set to appropriate level
- [ ] CSP trusted sites configured (references correct environment URL — not a hardcoded prod URL)
- [ ] CORS allowed origins configured if site calls external APIs
- [ ] Shared LWC components verified under this site's guest user profile
- [ ] Login page customization reviewed (no PII leakage in error messages)

---

## Site Lifecycle Policy

| Site | Owner | Purpose | Planned deletion date (if temporary) | Review date |
|---|---|---|---|---|
| | | | | |
| | | | | |

Scheduled review of inactive sites: (quarterly / annually)
Responsible team for site quota monitoring: _______________

---

## Architecture Decision Record Summary

**Decision made:** (single org multi-site / multi-org — and justification)

**Sites approved for creation:** (list)
**Sites approved for deletion:** (list)
**Shared component library scope:** (list components)
**Domain strategy:** (custom / default / mixed)
**SSO approach:** (IdP name and sites covered / not in scope)

**Risks and mitigations:**
| Risk | Likelihood | Mitigation |
|---|---|---|
| Approaching 100-site limit | | Site lifecycle policy + quarterly audit |
| Cross-site auth confusion | | SSO configuration or documented UX for re-auth |
| Guest profile misconfiguration | | Per-site verification step in deployment checklist |

**Open questions:**
- (list any decisions not yet made)

---

## Review Checklist

- [ ] Site inventory completed and total count confirmed below 100
- [ ] Org edition confirmed as appropriate for custom domain requirements
- [ ] Custom domain configuration documented as production-only
- [ ] Each site has a documented audience, license type, and URL
- [ ] Guest user profile configuration verified per site
- [ ] Shared LWC components use `@api` properties for per-site configuration
- [ ] Cross-site navigation boundaries documented with auth behavior
- [ ] SSO configuration in scope or re-authentication UX designed
- [ ] Site lifecycle policy defined with owner and review cadence
- [ ] License allocation confirmed with Salesforce Account team
