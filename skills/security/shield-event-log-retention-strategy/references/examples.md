# Shield Event Log Retention — Examples

## Example 1: Split By Value With Splunk + S3

**Context:** Regulated org, 7-year retention for login events, 1-year for API events, 90 days for UI events.

**Design:**
- Hot: Splunk index `sf_security` for 90 days — all events.
- Warm: Splunk index `sf_api` for 1 year — API events only.
- Cold: S3 lifecycle'd from Splunk → Glacier Deep Archive for 7 years — login/LoginAs/ReportExport only.

**Query runbook:** "Did user X export any reports between 2021-01 and 2021-06?"
1. Splunk check (last 90 days) — no results expected.
2. Splunk warm (if within 1 year).
3. S3 Athena scan over `/sf_security/report_export/YYYY/MM/*.csv` (Glacier restore if deep).

---

## Example 2: Big Objects For In-Platform Audit

**Context:** Healthcare org prefers staying in Salesforce for audit.

**Design:**
- Weekly scheduled Apex copies high-value ELF rows into a custom Big Object `Security_Audit_Event__b`.
- Auditors query via a Lightning App with a pre-built search UI.

**Why it works:** No SIEM round-trip; in-platform sharing rules cover auditor access.

---

## Anti-Pattern: "Keep Everything Forever In Splunk"

A team kept all event types in Splunk hot tier for 7 years. Ingest cost dominated the security budget within 18 months. Fix: tier by value, move cold to object storage.
