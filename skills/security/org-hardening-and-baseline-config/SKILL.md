---
name: org-hardening-and-baseline-config
description: "Use when defining or reviewing baseline org hardening settings, especially Security Health Check gaps, clickjack and browser protections, CSP and CORS governance, password/session policies, network restrictions, and release-update hygiene. NOT for feature-level app permissions or record-sharing design — use security/security-health-check."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
tags:
  - org-hardening
  - security-health-check
  - csp
  - cors
  - clickjack
triggers:
  - "baseline security checklist for a Salesforce org"
  - "Health Check is green but what else should we review"
  - "clickjack CSP CORS settings in Salesforce"
  - "password session IP restriction review"
  - "critical updates and release hardening cadence"
  - "harden a new Salesforce org before go-live"
  - "deploy our security settings baseline as metadata"
inputs:
  - "org type and risk profile"
  - "existing hardening settings and exception history"
  - "browser, integration, and network-control requirements"
outputs:
  - "baseline hardening checklist"
  - "review findings for missing or risky org controls"
  - "operational cadence for release and security settings review"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Org Hardening And Baseline Config

Use this skill when the question is "what should every serious org have locked down before feature work keeps expanding the blast radius?" Hardening is not one setting. It is the baseline combination of browser protections, session and password controls, network policy, trust exceptions, and release-update discipline.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is this a new org baseline, an inherited production org, or a regulated environment with stricter controls?
- Which browser, mobile, integration, and network behaviors are actually required?
- Does the org track exceptions for CSP Trusted Sites, CORS allowlist entries, trusted IP ranges, and similar trust decisions?
- Which profiles carry their own session timeout or password policy? Those override the org-wide values for their users.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Which Health Check baseline is the target: the Salesforce Baseline Standard or a custom baseline? | Health Check scores against the selected baseline, supports up to five custom baselines, and Fix Risks can't change every setting. | A named baseline and the list of settings that need manual edits. | The score means the same thing every quarter. |
| Do any profiles set their own session timeout or password policy? | ProfileSessionSetting and ProfilePasswordPolicy override the org-wide values for that profile's users; org-wide changes don't reach them. | A per-profile exception list. | Org-wide hardening actually applies to everyone it should. |
| Must logins be restricted to corporate networks, or only exempted from device activation there? | Trusted IP ranges (org `networkAccess`) let users log in without device activation; profile Login IP Ranges restrict login, and `enforceIpRangesEveryRequest` enforces them on every request. | Picks the right control for the threat. | No false sense of "office-only access". |
| Does any custom or packaged JavaScript read the session ID cookie? | `requireHttpOnly=true` makes the session cookie inaccessible to JavaScript, which breaks such code. | An inventory before the switch. | The hardening change ships without an outage. |
| Who owns each CSP Trusted Site and CORS origin, and why does it exist? | CSP headers over about 12 KB cause problems, malformed trusted URLs are silently excluded, and a CORS origin is honored only if it matches the allowlist pattern rules. | An exception register with owner and review date. | Trust sprawl is visible and reversible. |
| Will the security settings be deployed as metadata? | Deploying `networkAccess` replaces every existing trusted IP range with the ones in the file. | A rule that the file always carries the full list. | No accidental wipe of trusted ranges during a settings deploy. |

---

## Core Concepts

### Health Check Is a Starting Point

Health Check compares security settings against a baseline (the Salesforce Baseline Standard or one of up to five custom baselines) and groups them as High-Risk, Medium-Risk, Low-Risk, and Informational. New settings are added to the Salesforce Baseline Standard with default values, and a custom baseline prompts you to add them. Not every setting can be fixed with **Fix Risks**; some need the Edit link (Salesforce Security Guide, Security Health Check). A good score does not replace deliberate review of trust exceptions, profile-level overrides, and release updates.

### Browser Controls Live in Session Settings

Clickjack protection, CSRF protection, HttpOnly cookies, referrer policy, HSTS for sites, and session locking are fields of `sessionSettings` inside `Security.settings`:

| Control | Field | Hardened value |
|---|---|---|
| Clickjack protection, Setup pages | `enableClickjackSetup` | `true` |
| Clickjack protection, non-Setup Salesforce pages | `enableClickjackNonsetupSFDC` | `true` |
| Clickjack protection, customer Visualforce pages (with / without headers) | `enableClickjackNonsetupUser` / `enableClickjackNonsetupUserHeaderless` | `true` after testing embedded pages |
| CSRF protection on GET / POST (non-Setup pages) | `enableCSRFOnGet` / `enableCSRFOnPost` | `true` |
| HttpOnly session cookie | `requireHttpOnly` | `true` after checking custom JavaScript |
| Lock sessions to the domain they started on | `lockSessionsToDomain` | `true` |
| Enforce profile Login IP Ranges on every request | `enforceIpRangesEveryRequest` | `true` where profiles restrict IPs |
| HTTPS for Visualforce, sites, Experience Cloud | `hstsOnForcecomSites` | `true` |
| Referrer policy header | `referrerPolicy` + `referrerPolicyDirective` | `true` + `strict-origin-when-cross-origin` |

### Trust Exceptions Need Governance

`CspTrustedSite` entries open Lightning components, Visualforce (when `cspHeader` is true), and Experience Builder sites to external resources per directive (`isApplicableToConnectSrc`, `...ImgSrc`, and so on). `CorsWhitelistOrigin` entries let browser JavaScript on another origin call Salesforce APIs. Every entry is a risk decision and needs an owner, a reason, and a review date.

### Session and Password Policy Are Baseline Security

`passwordPolicies` (complexity, expiration, history, lockout, maximum attempts, minimum length) and `sessionTimeout` define how much damage routine credential compromise can do. Profile-level policies override them, so review both layers.

### Release Updates Are Part of Hardening

UNVERIFIED (2026-10-03): the Release Updates page and enforcement dates are documented only in Salesforce Help. Treat security-related release updates as scheduled operational work, reviewed on the same cadence as Health Check.

---

## Common Patterns

### New-Org Baseline as Metadata

**When to use:** A new org or business unit needs a repeatable security baseline.

**How it works:** Keep `Security.settings-meta.xml`, the `CspTrustedSite` files, and the `CorsWhitelistOrigin` files in source control. Deploy them to every org. Review Health Check after each deploy. The deployable files are in [references/metadata-examples.md](references/metadata-examples.md).

**Why not the alternative:** Click-configured baselines drift between sandboxes and production, and nobody can show what changed.

### Exception Register for Trusted Sites and Origins

**When to use:** The org uses CSP Trusted Sites, CORS allowlists, or trusted IP ranges.

**How it works:** Record owner, purpose, directives, and review date for each entry. Use the `description` field on `CspTrustedSite` and `IpRange` for the short form.

### Quarterly Hardening Review

**When to use:** The org runs continuously and needs a practical cadence.

**How it works:** Review Health Check against the chosen baseline, profile-level session and password overrides, trust exceptions, and pending release updates on a fixed schedule and after each major release.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New org or major environment setup | Deploy a baseline `Security.settings` early | Easier than retrofitting later |
| Many trusted-site and allowlist exceptions | Exception register plus periodic removal | Trust sprawl is still risk |
| Team relies only on the Health Check score | Add profile overrides, trust exceptions, and release updates to the review | The score covers baseline settings only |
| Need office-only access | Profile Login IP Ranges plus `enforceIpRangesEveryRequest` | Trusted IP ranges only skip device activation |
| Custom JavaScript reads the session cookie | Remove the dependency before `requireHttpOnly=true` | The setting blocks JavaScript access to the cookie |

---

## Recommended Workflow

1. Retrieve the current baseline: `sf project retrieve start --metadata "Settings:Security" CspTrustedSite CorsWhitelistOrigin ProfileSessionSetting ProfilePasswordPolicy --target-org <org>`.
2. Run `python3 skills/security/org-hardening-and-baseline-config/scripts/check_org_hardening_and_baseline_config.py --manifest-dir force-app` to flag weak session, password, CSP, and CORS values.
3. Compare the findings with Health Check against the chosen baseline, and list settings that Fix Risks can't change.
4. Decide each exception (owner, reason, review date) and edit `Security.settings-meta.xml`, keeping the full `networkAccess` list if the file carries it.
5. Deploy to a sandbox, test embedded Visualforce, integrations, and custom JavaScript, then deploy to production and re-run Health Check.
6. Put the next review date and the pending security release updates on the operations calendar.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Health Check reviewed against a named baseline; settings that Fix Risks can't change are listed.
- [ ] Profile-level session timeouts and password policies reviewed, because they override org-wide values.
- [ ] Clickjack, CSRF, HttpOnly, and session-locking fields set deliberately in `sessionSettings`.
- [ ] CSP Trusted Sites and CORS origins documented with owner and review date; header size under 12 KB.
- [ ] Login restriction uses profile Login IP Ranges, not trusted IP ranges.
- [ ] Any `networkAccess` deploy carries the full list of trusted ranges.
- [ ] Security release updates have an operating cadence.

---

## Salesforce-Specific Gotchas

Full write-ups with sources are in [references/gotchas.md](references/gotchas.md).

| Gotcha | One-line summary |
|---|---|
| `networkAccess` deploy | Deploying trusted IP ranges replaces all existing ranges. |
| Trusted vs Login IP ranges | Trusted ranges skip device activation; they don't block logins. |
| Profile overrides | Profile session timeout and password policy override org-wide values. |
| `requireHttpOnly` | Breaks custom or packaged JavaScript that reads the session cookie. |
| CSP header size | Keep the CSP header under 12 KB; malformed trusted URLs are excluded. |
| CORS patterns | Wildcards must precede a second-level domain; IP and domain are separate origins. |
| Health Check Fix Risks | Not every setting can be fixed from the Fix Risks screen. |
| Doc sample | The Security.settings sample in the Metadata API guide has a mismatched `logoutURL` tag. |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Hardening checklist | Baseline control list for the org or environment |
| Security config review | Findings on browser, session, network, and release controls |
| Exception register guidance | Operational model for trusted-site, origin, and IP range governance |
| Baseline metadata | `Security.settings`, `CspTrustedSite`, and `CorsWhitelistOrigin` files under source control |

---

## Related Skills

- `security/permission-set-groups-and-muting`: use when access-bundle design is the real issue instead of baseline org controls.
- `admin/connected-apps-and-auth`: use when connected apps and integration auth are the main hardening focus.
- `security/security-health-check`: use when the question is specifically about interpreting or using Health Check itself.
