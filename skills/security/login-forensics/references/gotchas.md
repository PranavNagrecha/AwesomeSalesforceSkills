# Gotchas — Login Forensics

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LoginHistory Purges at 6 Months With No Admin Override and No Recovery

**What happens:** `LoginHistory` records are automatically deleted after 6 months. There is no Recycle Bin for system audit objects, no "extend retention" configuration in Setup, and no Salesforce support process to recover purged records. Any investigation requiring data older than 6 months will simply return zero results for the affected period — without any error, warning, or indication that records were deleted.

**When it occurs:** Any incident response that references a compromise that began more than 6 months ago. Also affects compliance audits with annual lookback requirements (PCI DSS, SOX) where the org was not exporting login data to a SIEM.

**How to avoid:** Implement a scheduled job or Data Export Service workflow that periodically exports `LoginHistory` to an external store (S3, SIEM, BigQuery). Run it at least monthly. Include `LoginTime`, `UserId`, `SourceIp`, `Status`, `LoginType`, `Browser`, and `Platform` in the export schema. Document the export cadence in the org's security runbook.

---

## Gotcha 2: 'Trusted' Status in IdentityVerificationHistory Does Not Mean MFA Was Performed

**What happens:** Security reviewers querying `IdentityVerificationHistory` see records with `Status = 'Trusted'` and interpret them as successful MFA completions. In reality, `Trusted` means Salesforce skipped the MFA prompt because the user's device or network was registered as trusted — no MFA challenge was issued or completed.

**When it occurs:** Orgs that allow trusted devices or have Login IP Ranges set to bypass identity verification. Any time a user logs in from a trusted device or IP, a `Trusted` record is written to `IdentityVerificationHistory` with no corresponding MFA challenge. This shows up in audit reports as an "MFA verification event," which misleads auditors.

**How to avoid:** When reviewing `IdentityVerificationHistory` for compliance evidence, always include the `Activity` field in your query and distinguish `High Assurance Login` (actual MFA challenge) from `Trusted` (bypass due to trusted device/IP). If the org's security policy prohibits trusted-device bypasses, audit `IdentityVerificationHistory` for `Status = 'Trusted'` records and remediate by removing trusted devices in Setup > Identity Verification or restricting Login IP Ranges.

---

## Gotcha 3: SourceIp Reflects a Salesforce Internal IP for Some OAuth Flows, Not the True Client IP

**What happens:** `LoginHistory` records for integrations using the OAuth Username-Password flow, JWT Bearer flow, or client credentials flow sometimes show a Salesforce datacenter IP (`136.147.x.x` or similar) in the `SourceIp` field rather than the client application's IP. This causes allowlist checks to pass (because the datacenter IP appears trusted) and makes geo-based anomaly detection unreliable for API-originated logins.

**When it occurs:** Specifically when the OAuth token is issued via Salesforce's token endpoint from within a Salesforce server-side context, or when Salesforce proxies the request internally. Browser-initiated logins and most external REST API clients correctly surface the client IP.

**How to avoid:** Filter your IP-anomaly queries by `LoginType` when doing geo-analysis. API-originated logins show `LoginType = 'Remote Access 2.0'` or `'Remote Access 1.0'`; treat their `SourceIp` values as unreliable for geo checks. Use Connected App policies and JWT validation to enforce client constraints on API logins instead of relying on IP-based `LoginHistory` analysis for those login types.

---

## Gotcha 4: 'View Login Forensics' Permission Is Separate From Event Monitoring Access

**What happens:** A System Administrator enables Event Monitoring and grants a security analyst the "View Event Log Files" permission. When the analyst navigates to Setup > Login Forensics, they receive a "Insufficient Privileges" or 403 error. Event Monitoring access and Login Forensics UI access are controlled by different permissions.

**When it occurs:** Any org that grants Event Monitoring access via permission sets without explicitly checking for the `View Login Forensics` permission. This permission does not appear in the standard permission set UI alongside other Event Monitoring permissions, so it is easy to miss.

**How to avoid:** When provisioning security analyst access, explicitly add both "View Event Log Files" and "View Login Forensics" to the permission set. Validate access by having the analyst navigate to Setup > Login Forensics in a sandbox before going to production.

---

## Gotcha 5: LoginHistory SOQL Returns at Most 30,000 Rows Per Query — High-Volume Orgs Will Get Truncated Results

**What happens:** A SOQL query against `LoginHistory` without a tight `LoginTime` filter (e.g., `WHERE LoginTime >= LAST_N_DAYS:180`) against a high-volume org hits the 30,000-row query result limit and silently truncates results. Because `LoginHistory` has no ID-based cursor like standard objects with `queryMore`, analysts may not realize their dataset is incomplete.

**When it occurs:** Orgs with large user populations (thousands of users) or orgs being queried over long time windows without per-user filtering. Automated reporting scripts that run weekly without narrow date filters are especially prone to this.

**How to avoid:** Always add both a `LoginTime` range filter (narrow to a specific day or week) and, where relevant, a `UserId` filter to every `LoginHistory` query. For full-history exports, paginate by date range — query one day at a time and concatenate results in the calling script. The REST API `queryMore` endpoint does support pagination via the `nextRecordsUrl` in the response, but the underlying 30,000-row-per-query limit still applies.
