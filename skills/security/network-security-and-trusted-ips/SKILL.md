---
name: network-security-and-trusted-ips
description: "Configure and audit Salesforce network security controls — trusted IP ranges (org-wide Network Access), login IP ranges on profiles, CSP Trusted Sites for Lightning components, CORS allowlists for external JavaScript, and TLS requirements — and troubleshoot login-blocked-by-IP or CSP violation errors. NOT for org-wide session settings, MFA configuration, or real-time Transaction Security Policies."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "users are getting an error that login is restricted from their IP address and I need to configure trusted IP ranges"
  - "a Lightning web component is throwing a CSP violation and external resources are being blocked"
  - "how do I lock down admin logins to only allow access from our office network"
  - "we need to allow an external JavaScript library hosted on a CDN to load inside our Lightning pages"
  - "I need to audit all network access restrictions in a Salesforce org before go-live"
  - "CORS error when an external web app tries to call Salesforce REST API"
  - "sandbox refresh removed our IP restrictions and we need to restore them"
tags:
  - trusted-ip-ranges
  - network-access
  - csp-trusted-sites
  - cors
  - login-ip-ranges
  - lightning-security
inputs:
  - "Salesforce org with System Administrator profile"
  - "List of IP addresses or CIDR ranges to allow (for configuration tasks)"
  - "External domain(s) requiring CSP or CORS allowlisting"
  - "Profile name(s) for login IP range restrictions"
  - "For auditing: access to Setup > Security > Network Access and Setup > CSP Trusted Sites"
outputs:
  - "Configured org-wide Trusted IP Ranges (Setup > Security > Network Access)"
  - "Configured Login IP Ranges on one or more profiles"
  - "CSP Trusted Site records for Lightning component external resource loading"
  - "CORS allowlist entries for external JavaScript callers"
  - "Audit report of existing network restrictions across the org"
  - "Troubleshooting guidance for login-blocked-by-IP or CSP violation errors"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Network Security and Trusted IPs

This skill activates when a practitioner needs to configure, audit, or troubleshoot Salesforce network-layer security controls: org-wide Trusted IP Ranges, profile-level Login IP Ranges, CSP Trusted Sites for Lightning components, CORS allowlists for external API callers, and My Domain TLS requirements. It covers all three operational modes — configuring from scratch, auditing existing restrictions, and diagnosing login failures or CSP violations caused by network controls.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Trusted IP Ranges vs. Login IP Ranges are different controls with different scopes** — Trusted IP Ranges (Setup > Security > Network Access) apply org-wide and bypass the email verification challenge when logging in. Login IP Ranges on profiles enforce hard IP-based login restrictions for users on that profile — logins from outside the range are denied entirely. Conflating the two is the most common misconfiguration.
- **CSP Trusted Sites and CORS are separate allow-lists** — CSP Trusted Sites govern what external content Lightning pages can load (fonts, scripts, images, iframes). CORS governs which external domains can send JavaScript requests to the Salesforce REST, SOAP, and Bulk APIs. A domain can be in one list but not the other.
- **My Domain is a prerequisite for most Lightning security controls** — CSP Trusted Sites, CORS, and Lightning Experience itself require My Domain to be deployed. Confirm My Domain is deployed before attempting to configure these.
- **Sandbox IP restrictions do not carry over from production after a full sandbox refresh** — All Network Access and profile Login IP Ranges must be re-entered manually after a sandbox refresh. Document them before refreshing.
- **TLS 1.2+ is mandatory** — Salesforce enforces TLS 1.2 as the minimum for all inbound and outbound connections. Any external system calling Salesforce or being called by Salesforce must support TLS 1.2 or higher.

---

## Core Concepts

### Concept 1 — Trusted IP Ranges (Org-Wide Network Access)

**Location:** Setup > Security > Network Access

Trusted IP Ranges define a set of IP addresses or CIDR blocks that Salesforce considers trusted for all users in the org. When a user logs in from a trusted IP:

- Salesforce **skips the email verification challenge** that would otherwise be required when logging in from an unrecognized device or location.
- MFA is **not** bypassed — if MFA is enforced, it is still required even from a trusted IP. Trusted IPs only bypass the email verification step, not MFA.
- Trusted IP Ranges are purely about skipping the email challenge, not about restricting access.

**Configuration:** Setup > Security > Network Access > New. Provide a Start IP Address and End IP Address. IPv4 ranges are expressed as start/end pairs (e.g., `203.0.113.10` to `203.0.113.254`). IPv6 is supported but must be entered in full expanded form — CIDR notation is not accepted directly in the UI for IPv6.

**Limit:** Salesforce does not publish a hard maximum for the number of trusted IP entries per org, but keep the list to the minimum needed for operational coverage.

### Concept 2 — Login IP Ranges on Profiles

**Location:** Setup > Profiles > [Profile Name] > Login IP Ranges

Login IP Ranges are a profile-level hard restriction. Users on that profile **cannot log in at all** from an IP outside the configured range — they receive an error, not just an email challenge. This is the appropriate control for locking privileged profiles (e.g., System Administrator) to known office or VPN IP blocks.

Key distinctions from Trusted IP Ranges:

| Dimension | Trusted IP Ranges (Org-Wide) | Login IP Ranges (Per Profile) |
|---|---|---|
| Scope | All users, all profiles | Only users on the specific profile |
| Effect | Skips email verification challenge | Hard deny — login refused outside range |
| MFA | Not affected — MFA still required | Not affected — MFA still required |
| Audit trail | LoginHistory SourceIp field | LoginHistory Status = 'No Salesforce.com Access' |
| Config location | Setup > Security > Network Access | Setup > Profiles > [Profile] > Login IP Ranges |

**Important:** If a profile has Login IP Ranges set and a user on that profile attempts to log in from outside those ranges, the login is denied with `Status = 'No Salesforce.com Access'` in `LoginHistory`. There is no email challenge fallback.

### Concept 3 — CSP Trusted Sites for Lightning Components

**Location:** Setup > CSP Trusted Sites

Salesforce Lightning Experience enforces a Content Security Policy (CSP) that restricts what external resources can be loaded in Lightning pages. By default, Lightning blocks all external `script-src`, `img-src`, `frame-src`, `font-src`, `connect-src`, and `style-src` origins not already on Salesforce's internal allowlist.

When a Lightning component (LWC or Aura) loads an external resource — a CDN-hosted JS library, an external image, a web font, or a third-party iframe — the browser will block it with a CSP violation unless the source domain is added to the CSP Trusted Sites list.

Each CSP Trusted Site entry specifies:
- **Site Name** — a human-readable label
- **Site URL** — the origin (e.g., `https://cdn.example.com`)
- **CSP Directives** — which directives the entry applies to: `connect-src`, `font-src`, `frame-src`, `img-src`, `media-src`, `object-src`, `script-src`, `style-src`, or `worker-src`

**Scope:** CSP Trusted Sites apply to all Lightning pages in the org. There is no profile-level or component-level scoping — adding an entry allows that resource org-wide in Lightning.

### Concept 4 — CORS Allowlist

**Location:** Setup > CORS

Cross-Origin Resource Sharing (CORS) governs which external web application origins are allowed to make JavaScript-initiated HTTP requests to Salesforce REST, SOAP, Bulk, and streaming APIs. This is relevant when a third-party web application (not hosted on Salesforce) makes API calls directly from the browser using JavaScript.

A CORS entry requires:
- **Origin URL Pattern** — the full origin of the external site, e.g., `https://app.example.com`. Wildcard subdomains are supported with `*.example.com`.

Without a CORS entry, the browser's preflight `OPTIONS` request will be denied and the API call will fail with a CORS error. Note: CORS only applies to browser-initiated calls — server-to-server API calls (cURL, Apex callouts, integration middleware) are not subject to CORS and do not need entries here.

---

## Common Patterns

### Mode 1: Configuring Network Security Controls from Scratch

**When to use:** A new org is being hardened pre-go-live, or an existing org has never had explicit network restrictions configured.

**How it works:**

1. **Identify IP requirements.** Collect the office IP ranges, VPN exit nodes, and any CI/CD pipeline IP blocks that need to be trusted or restricted.

2. **Configure org-wide Trusted IP Ranges** (skips email challenge for all users):
   - Setup > Security > Network Access > New
   - Enter Start IP and End IP for each range (one entry per range)
   - Repeat for each office location and VPN exit IP block

3. **Configure Login IP Ranges on privileged profiles** (hard restrict by IP):
   - Setup > Profiles > System Administrator > Login IP Ranges > New
   - Enter Start IP and End IP for each allowed range
   - Repeat for any other privileged profiles (e.g., custom admin profiles)
   - Test from a known-good IP before saving, to avoid locking out your own session

4. **Configure CSP Trusted Sites** for any external resources in Lightning:
   - Setup > CSP Trusted Sites > New
   - Enter the origin URL (e.g., `https://cdn.jsdelivr.net`)
   - Select the applicable CSP directives (most CDN JS libraries need `script-src` and `connect-src`)

5. **Configure CORS** if any external web applications call the Salesforce API from a browser:
   - Setup > CORS > New
   - Enter the exact origin URL (e.g., `https://portal.example.com`)

6. **Verify My Domain** is deployed: Setup > My Domain. Lightning security controls require My Domain.

**Why not rely on org-wide trusted IPs alone for admin lockdown:** Trusted IP Ranges bypass the email challenge but do not prevent logins from outside those IPs. Only Login IP Ranges on profiles provide hard login denial.

### Mode 2: Auditing Existing Network Security Configuration

**When to use:** Pre-go-live review, post-incident investigation, or compliance audit requiring a full inventory of network restrictions.

**How it works:**

1. **Export Trusted IP Ranges**: Setup > Security > Network Access. Review for stale ranges, overly broad CIDR blocks, or documentation gaps.

2. **Export Login IP Ranges per profile**: For each profile with sensitive access (System Administrator, custom admin), review Setup > Profiles > [Profile] > Login IP Ranges. Check that every range is documented and intentional.

3. **Export CSP Trusted Sites**: Setup > CSP Trusted Sites. Flag any `script-src` entries pointing to non-authoritative domains or entries added without a documented justification.

4. **Export CORS entries**: Setup > CORS. Verify each origin is still an active application and that wildcard entries are justified.

5. **Cross-reference with LoginHistory** for `Status = 'No Salesforce.com Access'` entries — these indicate users who were denied login due to IP restrictions. Unexpected denials may indicate a range misconfiguration.

   ```soql
   SELECT UserId, LoginTime, SourceIp, Status, LoginType
   FROM LoginHistory
   WHERE Status = 'No Salesforce.com Access'
     AND LoginTime >= LAST_N_DAYS:30
   ORDER BY LoginTime DESC
   LIMIT 500
   ```

6. **Document findings** in the work template, noting any gaps, over-broad ranges, or undocumented entries.

### Mode 3: Troubleshooting Login Blocked by IP or CSP Violations

**When to use:** A user reports they cannot log in, or a Lightning component is failing to load external resources.

**How it works — Login IP restriction troubleshooting:**

1. Check the user's profile: Setup > Users > [User] > Profile. Navigate to that profile's Login IP Ranges.
2. Confirm the user's current IP (ask them to visit `whatismyip.com` or check the `SourceIp` field in `LoginHistory`).
3. If their IP is outside the configured ranges, either add a new range entry or move the user to a profile without Login IP Ranges.
4. Check `LoginHistory` to confirm the denial:
   ```soql
   SELECT LoginTime, SourceIp, Status, LoginType
   FROM LoginHistory
   WHERE UserId = '005XXXXXXXXXXXXXXX'
   ORDER BY LoginTime DESC
   LIMIT 20
   ```
5. For org-wide Trusted IP Range additions (to stop email verification challenges), add the IP range under Setup > Security > Network Access.

**How it works — CSP violation troubleshooting:**

1. Open the browser Developer Tools (F12) > Console tab. CSP violations appear as red errors beginning with `Content Security Policy`.
2. Identify the blocked origin from the error message (e.g., `Refused to load script from 'https://cdn.example.com/...'`).
3. Navigate to Setup > CSP Trusted Sites > New.
4. Enter the blocked origin URL and select the appropriate directives based on the resource type:
   - External JS files → `script-src`
   - API calls from JS → `connect-src`
   - External CSS → `style-src`
   - Web fonts → `font-src`
   - Embedded iframes → `frame-src`
   - Images → `img-src`
5. Save and reload the Lightning page. The browser cache may need clearing.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Skip email verification challenge for office network users | Trusted IP Ranges (Setup > Security > Network Access) | These are org-wide and bypass email challenge only, not MFA |
| Prevent logins to the System Administrator profile from outside the VPN | Login IP Ranges on the System Administrator profile | Login IP Ranges enforce hard denial; Trusted IP Ranges do not |
| Allow a CDN-hosted JavaScript library in an LWC | CSP Trusted Sites with `script-src` directive | CSP Trusted Sites is the correct Lightning-layer allowlist for resource loading |
| Allow an external portal to call Salesforce REST API from the browser | CORS allowlist entry for the portal's origin | CORS governs browser-initiated cross-origin API calls |
| Block logins from unauthorized countries in real time | Transaction Security Policy (separate skill) | Real-time enforcement requires the Event Monitoring add-on and is not a static IP range |
| Restrict a community or Experience Cloud user to specific IPs | Login IP Ranges on their profile (e.g., Customer Community User profile) | Profile-level ranges work for all profile types including Experience Cloud |
| Audit all network restrictions before a security review | Mode 2 audit pattern: review Network Access, all profile Login IP Ranges, CSP Trusted Sites, and CORS | No single Setup page shows all four lists together |

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

- [ ] Confirmed distinction between Trusted IP Ranges (email challenge bypass) and Login IP Ranges (hard login denial) — applied the correct one for the use case
- [ ] Login IP Ranges on privileged profiles tested from a known-good IP before saving, to avoid self-lockout
- [ ] CSP Trusted Sites entries use the minimum set of directives needed (not all directives for every entry)
- [ ] CORS entries use exact origin URLs; wildcard entries documented and justified
- [ ] My Domain is deployed (required for CSP Trusted Sites and Lightning Experience)
- [ ] Sandbox network access configuration documented separately — it will be lost on full refresh
- [ ] LoginHistory queried for `Status = 'No Salesforce.com Access'` to confirm no unintended login denials
- [ ] TLS 1.2+ confirmed for any external systems in CORS or CSP entries

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Trusted IP Ranges do not prevent logins from untrusted IPs — they only skip the email challenge** — Many practitioners configure Trusted IP Ranges expecting them to restrict logins to those IPs. They do not. A user outside a Trusted IP range still logs in successfully; they just receive an email verification challenge first. To actually restrict login to specific IPs, use Login IP Ranges on the user's profile.

2. **Login IP Ranges on a profile lock out all users on that profile, including System Administrators** — If you configure Login IP Ranges on the System Administrator profile and your own IP is not in the range, you will be locked out of your own session on next login. Always test from a confirmed IP-in-range browser session before saving profile-level IP restrictions.

3. **CSP Trusted Sites scope is org-wide — there is no component-level or profile-level scoping** — Adding a CSP Trusted Site entry for a domain allows that resource to be loaded anywhere in Lightning for any user in the org. There is no way to restrict a CSP entry to specific pages, components, or user profiles.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Trusted IP Range entries | Org-wide Network Access IP ranges that bypass the email verification challenge |
| Profile Login IP Range entries | Per-profile hard-deny IP restrictions for one or more profiles |
| CSP Trusted Site records | Origin allowlist entries for Lightning component external resource loading |
| CORS allowlist entries | Origin entries for external web applications making browser-initiated API calls |
| LoginHistory audit query | SOQL to surface `No Salesforce.com Access` denials within a date range |
| Network security audit checklist | Inventory of all four control types across the org |

---

## Related Skills

- `login-forensics` — Use when investigating who was denied login due to IP restrictions, or to reconstruct login timelines for a specific user
- `org-setup-and-configuration` — Use for MFA configuration, session timeout settings, and My Domain deployment
- `transaction-security-policies` — Use when you need real-time dynamic enforcement (e.g., block login from a country) rather than static IP allowlists
- `event-monitoring` — Use when you need to stream real-time login events or download bulk EventLogFile login logs for SIEM ingestion
