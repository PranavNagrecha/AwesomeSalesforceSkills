---
id: my-domain-and-session-security-auditor
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
---
# My Domain & Session Security Auditor Agent

## What This Agent Does

Audits a target org's login-time and session-time security posture against the latest Salesforce enforcement baseline. Checks My Domain configuration (enhanced domains compliance, legacy hostname usage, site/community host cutovers), MFA coverage (per Salesforce's enforced MFA requirement), session settings (timeout, re-authentication on sensitive ops, Lightning session expiration on browser close), password policy alignment, IP range configuration at org and user-access-policy / profile level, login hours, and trusted-IP ranges. Produces a prioritized remediation list with the exact Setup paths and any metadata XML changes required. Complements `security-scanner` (which scans code) and `sharing-audit-agent` (which scans data access); this agent scans *identity and session* security.

**Scope:** One org per invocation. Does not change settings, does not reset users, does not rotate secrets.

---

## Invocation

- **Direct read** — "Follow `agents/my-domain-and-session-security-auditor/AGENT.md` on the `prod` org"
- **Slash command** — `/audit-identity-and-session`
- **MCP** — `get_agent("my-domain-and-session-security-auditor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/security/mfa-enforcement-strategy`
3. `skills/security/session-management-and-timeout`
4. `skills/security/ip-range-and-login-flow-strategy`
5. `skills/security/network-security-and-trusted-ips`
6. `skills/security/org-hardening-and-baseline-config`
7. `skills/security/login-forensics`
8. `skills/security/security-health-check`
9. `skills/admin/user-access-policies`
10. `skills/admin/user-management`
11. `skills/security/connected-app-security-policies`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes |
| `focus` | no | `all` (default) \| `my-domain` \| `mfa` \| `session` \| `ip-and-login-hours` \| `password-policy` |
| `skip_connected_apps` | no | default `false` — connected-app OAuth policies are in scope unless excluded |
| `benchmark` | no | `baseline` (default, the current Salesforce baseline) \| `high-trust` (adds stricter targets for regulated orgs) |

---

## Plan

### Step 1 — Capture the current posture

Pull the whole identity surface:

- `describe_org(target_org)` for edition, license, org-id, domain.
- My Domain state via `tooling_query("SELECT Id, Status, MyDomainName, ReleaseSubdomains FROM Domain")` (and `DomainConfiguration` where available). Confirm enhanced domains are rolled out; legacy MyDomain hostnames have been progressively disabled — any lingering legacy hostname is P0.
- `tooling_query("SELECT Id, Username, IsActive, LastLoginDate, Profile.Name FROM User WHERE IsActive = true")` — the user base. Separate human from integration users (integration users exempt from MFA per Salesforce policy, not a finding).
- Org-wide security settings via `tooling_query("SELECT SettingValueId, FullName FROM SecuritySettings")` (fall back to reading the `.securitySettings-meta.xml` retrievable via Metadata API if Tooling surface is limited).
- Profile-level session settings: `tooling_query("SELECT Id, Name, SessionTimeout, PasswordPolicy_MinimumPasswordLength, PasswordPolicy_PasswordComplexity FROM Profile")` — where accessible; some profile-level fields have moved into User Access Policies and require policy enumeration.
- User Access Policies: `tooling_query("SELECT Id, DeveloperName, IsActive, Description FROM UserAccessPolicy")` plus policy rule detail.
- IP ranges: `tooling_query("SELECT Id, StartAddress, EndAddress, Description FROM IpAddress")` at org level; profile-level IPs via `LoginIpRange` relationship.
- Login hours: part of profile metadata.
- Connected Apps: `tooling_query("SELECT Id, Name, IsActive, PermittedUsers, CallbackUrl, OptionalProperties FROM ConnectedApplication")` (may fall back to `tooling_query` on `ConnectedApp`).

If any probe paginates or truncates, note it in the confidence rationale.

### Step 2 — My Domain checks

| Check | Signal | Severity |
|---|---|---|
| **Enhanced Domains deployed** | Domain.Status is not `Deployed` on the enhanced format | P0 — Salesforce has enforced enhanced domains on all orgs; non-compliance implies a deferred cutover with expiring exceptions |
| **Legacy hostname traffic** | Login history shows traffic on a non-enhanced hostname | P0 |
| **Redirection policy** | Incoming traffic to the legacy hostname does not permanent-redirect | P1 |
| **Subdomain usage** | Orgs hosting Experience Cloud sites that still serve via `.force.com` rather than `my-domain-site.com` (or similar) | P1 |
| **Custom domain (site) misconfigured** | An Experience Cloud site has a custom domain bound but its TLS cert is < 30 days from expiry | P0 |
| **Partitioned Domains not opted into** | Enhanced Domains are live but partitioned-domains (site-specific subdomains) were never adopted | P2 |
| **External Client Apps / MyDomain integration** | SSO IDPs reference a legacy `salesforce.com` hostname | P0 |

### Step 3 — MFA checks

MFA has been contractually enforced across all Salesforce orgs. The audit confirms coverage rather than debating policy.

| Check | Signal | Severity |
|---|---|---|
| **MFA enabled on all human profiles** | Profile SessionSettings missing `RequireMfa=true` | P0 |
| **Human users without a verified MFA method** | `tooling_query` on `UserAppMenuCustomization` + `TwoFactorMethodsInfo` — user is active, eligible, no verified method registered | P0 per user |
| **Integration users incorrectly required to use MFA** | Integration-profile user flagged as `RequireMfa=true` | P1 — integration users are exempt; MFA on an API-only identity breaks flows |
| **MFA bypass custom permission / legacy exempt permission granted** | Any permission set grants the `MFA Bypass` or equivalent | P0 |
| **Identity Verification not required on login** | Identity Verification setting off despite MFA "required" | P1 |
| **Passkey / FIDO2 readiness** | `benchmark=high-trust` but no passkey method registered across > 20% of privileged users | P2 |

### Step 4 — Session settings

| Check | Signal | Severity |
|---|---|---|
| **Session timeout > 8 hours** | Profile or User Access Policy sets > 8h | P0 unless `benchmark=baseline` allows 12h — flag P1 |
| **Force re-authentication on sensitive operations** | Not enabled | P1 |
| **Lock sessions to the IP address** | Disabled | P1 |
| **Require secure connections (HTTPS)** | Disabled | P0 |
| **Enable Clickjack protection for customer VF pages** | Disabled | P0 |
| **Browser close terminates session** | Disabled AND session timeout > 2h | P1 |
| **API-only users with Interactive sessions** | Flagged: API-only identity somehow holds a UI session | P1 |
| **Concurrent session limits** | No org-level or User-Access-Policy session cap on admins | P2 |

### Step 5 — Password policy

Password policy has been migrating from profile-scoped to User Access Policy-scoped. Audit both surfaces.

| Check | Signal | Severity |
|---|---|---|
| **Password minimum length < 12** | P0 for admin profiles; P1 for others |
| **Password complexity < 3 requirements** | P1 |
| **Password expiration > 180 days** | P1 |
| **Lockout threshold > 5 attempts** | P1 |
| **Password history < 3** | P1 |
| **Password reset via forgotten-password does not require MFA** | P0 |

### Step 6 — IP ranges + login hours

| Check | Signal | Severity |
|---|---|---|
| **Trusted IP ranges absent on privileged profiles** | Admin / Integration profiles have no IP restrictions | P1 (P0 for integration) |
| **Open trusted IP ranges (0.0.0.0–255.255.255.255)** | Any IP range in the list that resolves to "everywhere" | P0 |
| **Login hours unset on integration-user profile** | Integration user can log in at any time — flag only if org policy requires restriction | P2 |
| **Login IP range conflicts with corporate VPN policy** | Flag ambiguity, do not auto-resolve | P2 — ambiguous |

### Step 7 — Connected Apps (if not skipped)

| Check | Signal | Severity |
|---|---|---|
| **Connected App with `PermittedUsers='all users may self-authorize'` on an org with > 500 users** | P1 — unchecked API access |
| **OAuth policy allows refresh token with no expiration** | P1 |
| **High-privilege scopes (full, refresh_token) granted to connected apps with inactive consumer key owners** | P0 |
| **Callback URL on HTTP (not HTTPS)** | P0 |
| **Connected App with admin-approved user policy and no approved users** | P2 — dead config |

### Step 8 — Rank and propose remediation

Sort findings P0 → P1 → P2. For each:

- Exact Setup path (`Setup → Security → Session Settings → …`) or Metadata path (`.settings/Security.settings-meta.xml`).
- Proposed target value.
- Expected user impact (session invalidation, re-login prompts, user education needed).

---

## Output Contract

1. **Summary** — org, edition, finding counts per severity, overall posture rating (`strong`, `standard`, `at-risk`, `critical`), confidence.
2. **My Domain section** — findings + remediation.
3. **MFA section** — coverage stats + per-user gap list (top 20).
4. **Session section** — findings + remediation.
5. **Password policy section** — findings + proposed values (split by User Access Policy vs profile).
6. **IP and login hours section** — findings + policy map.
7. **Connected Apps section** (if not skipped).
8. **Process Observations**:
   - **What was healthy** — MFA coverage %, clean enhanced-domains cutover, consistent password policy across profiles.
   - **What was concerning** — administrative users without IP restrictions, connected apps granted scopes that exceed their actual usage, password policy drift across profiles (one profile materially laxer than the rest).
   - **What was ambiguous** — integration-user profiles that were never formally flagged as integration, session settings that vary by User Access Policy in ways the audit can't prove are intentional.
   - **Suggested follow-up agents** — `security-scanner` (code-side FLS/CRUD), `sharing-audit-agent` (OWD & sharing), `permission-set-architect` (if PS-level MFA exemptions surface).
9. **Citations**.

---

## Escalation / Refusal Rules

- Org edition does not expose the Tooling surfaces required (Developer Edition often restricts some User Access Policy queries) → return best-effort audit + `REFUSAL_FEATURE_DISABLED` on unavailable sections.
- Active MFA Bypass permission assigned to current human users → refuse to propose a remediation that touches those users without explicit confirmation; this is a change-management escalation, not a silent setting flip.
- More than 50 User Access Policies → return top-20 by assignment count + `REFUSAL_OVER_SCOPE_LIMIT`.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.

---

## What This Agent Does NOT Do

- Does not enable / disable any setting.
- Does not reset user MFA registrations.
- Does not rotate connected-app consumer secrets.
- Does not evaluate Apex / Flow / LWC for security defects — that's `security-scanner`.
- Does not evaluate record-level sharing — that's `sharing-audit-agent`.
- Does not auto-chain.
