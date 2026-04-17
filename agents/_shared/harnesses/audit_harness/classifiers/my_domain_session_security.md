# Classifier: my_domain_session_security

## Purpose

Audit a target org's login-time and session-time security posture: My Domain (enhanced domains, legacy hostname cutover, Experience Cloud site hosts), MFA coverage, session settings, password policy, IP ranges + login hours, and connected-app OAuth policies. Not for auditing code (that's `security-scanner`) or record-level sharing (that's `sharing`). Does not change settings, reset users, or rotate secrets.

## Replaces

`my-domain-and-session-security-auditor` (now a deprecation stub pointing at `audit-router --domain my_domain_session_security`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `focus` | no | `all` (default) \| `my-domain` \| `mfa` \| `session` \| `ip-and-login-hours` \| `password-policy` |
| `skip_connected_apps` | no | default `false` |
| `benchmark` | no | `baseline` (default) \| `high-trust` (stricter for regulated orgs) |

## Inventory Probe

1. `describe_org(target_org)` — edition, license, domain.
2. My Domain: `tooling_query("SELECT Id, Status, MyDomainName, ReleaseSubdomains FROM Domain")` + `DomainConfiguration` where available.
3. Active users: `tooling_query("SELECT Id, Username, IsActive, LastLoginDate, Profile.Name FROM User WHERE IsActive = true")`. Separate human from integration users.
4. Org-wide security settings: `tooling_query` on `SecuritySettings` (fallback to `.securitySettings-meta.xml` via Metadata API).
5. Profile-level session/password settings: `tooling_query("SELECT Id, Name, SessionTimeout, PasswordPolicy_MinimumPasswordLength, PasswordPolicy_PasswordComplexity FROM Profile")`.
6. User Access Policies: `tooling_query("SELECT Id, DeveloperName, IsActive, Description FROM UserAccessPolicy")` + rule detail.
7. IP ranges: `tooling_query("SELECT Id, StartAddress, EndAddress, Description FROM IpAddress")` + profile-level `LoginIpRange`.
8. Login hours: part of profile metadata.
9. Connected Apps (if not skipped): `tooling_query("SELECT Id, Name, IsActive, PermittedUsers, CallbackUrl, OptionalProperties FROM ConnectedApplication")`.
10. MFA method registration: `tooling_query` on `TwoFactorMethodsInfo` / `UserAppMenuCustomization`.

Inventory columns (beyond id/name/active): `domain_status`, `mfa_required_profiles`, `mfa_registered_users`, `password_min_length_min`, `session_timeout_max`, `trusted_ip_count`, `connected_app_count`.

## Rule Table

### My Domain

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `MD_ENHANCED_NOT_DEPLOYED` | P0 | `Domain.Status` is not `Deployed` in the enhanced format | domain + status | Plan enhanced domains deployment — deferred exceptions are expiring |
| `MD_LEGACY_HOSTNAME_TRAFFIC` | P0 | Login history shows traffic on a non-enhanced hostname | hostname + sample login date | Redirect traffic + communicate to users |
| `MD_REDIRECT_NOT_PERMANENT` | P1 | Incoming traffic to legacy hostname does not permanent-redirect | domain + redirect config | Enable permanent redirect |
| `MD_EXP_CLOUD_LEGACY_HOST` | P1 | Experience Cloud site still serves via `.force.com` | site + hostname | Migrate to `my-domain-site.com` |
| `MD_EXP_CLOUD_CERT_EXPIRING` | P0 | Custom domain TLS cert < 30 days from expiry | site + cert expiry | Renew / rotate cert |
| `MD_PARTITIONED_DOMAINS_NOT_ADOPTED` | P2 | Enhanced Domains live but partitioned-domains (site-specific subdomains) not adopted | org | Evaluate for adoption per Salesforce release |
| `MD_SSO_IDP_LEGACY_HOST` | P0 | SSO IDPs reference a legacy `salesforce.com` hostname | SAML/OIDC IDP + URL | Update IDP configuration |

### MFA

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `MFA_NOT_REQUIRED_HUMAN_PROFILE` | P0 | Profile SessionSettings missing `RequireMfa=true` for a human-user profile | profile | Enable MFA requirement |
| `MFA_USER_NO_METHOD` | P0 | Human user active + MFA-eligible + no verified method registered | user | User must register a verified MFA method before next login |
| `MFA_REQUIRED_ON_INTEGRATION` | P1 | Integration-profile user flagged `RequireMfa=true` | user + profile | Exempt integration profile (integration users are exempt per Salesforce policy) |
| `MFA_BYPASS_GRANTED` | P0 | Any permission set grants MFA Bypass / legacy exempt permission | perm set + assignees | Remove MFA bypass — change management escalation |
| `MFA_IDENTITY_VERIFY_OFF` | P1 | Identity Verification setting off despite MFA required | org setting | Enable Identity Verification |
| `MFA_NO_PASSKEY_HIGH_TRUST` | P2 | `benchmark=high-trust` AND no passkey method registered for > 20% privileged users | user list + benchmark | Roll out passkeys / FIDO2 |

### Session

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `SESSION_TIMEOUT_TOO_LONG` | P0 if `benchmark=high-trust` else P1 | Session timeout > 8 hours | profile / UAP + value | Reduce to 4–8h window |
| `SESSION_NO_REAUTH_SENSITIVE` | P1 | "Force re-auth on sensitive ops" disabled | org setting | Enable |
| `SESSION_IP_NOT_LOCKED` | P1 | "Lock sessions to IP" disabled | org setting | Enable (where corporate VPN policy permits) |
| `SESSION_HTTPS_NOT_REQUIRED` | P0 | "Require secure connections (HTTPS)" disabled | org setting | Enable |
| `SESSION_CLICKJACK_PROTECTION_OFF` | P0 | Clickjack protection disabled for customer VF pages | org setting | Enable |
| `SESSION_BROWSER_CLOSE_NOT_TERMINATED` | P1 | "Browser close terminates session" disabled AND timeout > 2h | org setting | Enable session termination on close |
| `SESSION_API_ONLY_HAS_UI_SESSION` | P1 | API-only user holds an interactive UI session | user + session type | Investigate + terminate anomalous session |
| `SESSION_NO_CONCURRENT_CAP` | P2 | No session cap on admin profiles | profile | Add concurrent-session cap |

### Password policy

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `PWD_MIN_LENGTH_LOW` | P0 for admin profiles, P1 others | Minimum password length < 12 | profile + UAP + current length | Raise to ≥ 12 |
| `PWD_COMPLEXITY_LOW` | P1 | Password complexity < 3 requirements | profile / UAP | Raise complexity |
| `PWD_EXPIRATION_LONG` | P1 | Password expiration > 180 days | profile / UAP | Set to ≤ 180 days |
| `PWD_LOCKOUT_WEAK` | P1 | Lockout threshold > 5 attempts | profile / UAP | Set to ≤ 5 |
| `PWD_HISTORY_LOW` | P1 | Password history retention < 3 | profile / UAP | Set to ≥ 3 |
| `PWD_RESET_NO_MFA` | P0 | Forgotten-password reset does not require MFA | org setting | Require MFA on password reset |

### IP ranges + login hours

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `IP_NO_TRUSTED_RANGE_PRIVILEGED` | P0 for integration profiles, P1 for admin | Privileged profile has no IP restrictions | profile + IP range count | Add Trusted IP ranges per corporate policy |
| `IP_RANGE_OPEN_WORLD` | P0 | Any IP range in the list resolves to `0.0.0.0–255.255.255.255` | range | Remove the open-world range |
| `LH_INTEGRATION_UNRESTRICTED` | P2 | Integration user profile has no login-hour restriction AND org policy requires restriction | profile + policy | Add login hours if policy requires |
| `IP_VPN_POLICY_CONFLICT` | P2 | Login IP range conflicts with corporate VPN policy | profile + VPN range | Ambiguous — reconcile with IT/security policy |

### Connected Apps (if not skipped)

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `CA_UNRESTRICTED_AUTH` | P1 | `PermittedUsers='all users may self-authorize'` on org with > 500 users | connected app + user count | Restrict to admin-approved users |
| `CA_REFRESH_NO_EXPIRATION` | P1 | OAuth policy allows refresh token with no expiration | connected app | Set refresh-token expiration |
| `CA_HIGH_PRIV_INACTIVE_OWNER` | P0 | Full / `refresh_token` scope granted to app whose consumer-key owner is inactive | connected app + owner | Transfer owner; review grant |
| `CA_CALLBACK_HTTP` | P0 | Callback URL uses HTTP (not HTTPS) | connected app + URL | Migrate to HTTPS |
| `CA_ADMIN_APPROVED_NO_USERS` | P2 | Admin-approved user policy with no approved users | connected app | Retire dead config |

## Patches

None. Identity-and-session configuration is audit-sensitive and mostly Setup-bound (User Access Policies, profile settings, Session Settings, Connected App policies). Patches would bypass the change-management trail expected of security-posture changes.

## Mandatory Reads

- `skills/security/mfa-enforcement-strategy`
- `skills/security/session-management-and-timeout`
- `skills/security/ip-range-and-login-flow-strategy`
- `skills/security/network-security-and-trusted-ips`
- `skills/security/org-hardening-and-baseline-config`
- `skills/security/login-forensics`
- `skills/security/security-health-check`
- `skills/admin/user-access-policies`
- `skills/admin/user-management`
- `skills/security/connected-app-security-policies`

## Escalation / Refusal Rules

- Org edition lacks User Access Policy queries (some Developer Edition orgs) → best-effort audit + `REFUSAL_FEATURE_DISABLED` on unavailable sections.
- Active `MFA Bypass` permission assigned to current human users → refuse to propose remediation touching those users without explicit confirmation. `REFUSAL_SECURITY_GUARD`.
- > 50 User Access Policies → top-20 by assignment count + `REFUSAL_OVER_SCOPE_LIMIT`.

## What This Classifier Does NOT Do

- Does not enable / disable any setting.
- Does not reset user MFA registrations.
- Does not rotate Connected App consumer secrets.
- Does not evaluate Apex / Flow / LWC — that's `security-scanner`.
- Does not evaluate record-level sharing — that's `sharing`.
