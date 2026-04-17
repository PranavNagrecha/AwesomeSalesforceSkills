# Data Loader and Tools — Operation Template

Use this template to plan and document a data load or export operation. Complete every section before executing against production.

---

## 1. Tool Selection Checklist

Work through each question in order and stop at the first match.

| # | Question | Answer | Next Step |
|---|----------|--------|-----------|
| 1 | Is the record count under 50,000? | Yes / No | If Yes → go to Q2. If No → use **Data Loader (Bulk API 2.0)**. |
| 2 | Is the target object in the supported list? (Accounts, Contacts, Leads, Cases, Campaign Members, Solutions, Person Accounts) | Yes / No | If Yes → go to Q3. If No → use **Data Loader**. |
| 3 | Is scheduling or command-line automation required? | Yes / No | If Yes → use **Data Loader (headless)** or **Salesforce CLI**. If No → use **Data Import Wizard**. |
| 4 | Is this a CI/CD or scripted pipeline context? | Yes / No | If Yes → use **Salesforce CLI**. |
| 5 | Is this an ad-hoc, read-only SOQL or REST exploration in a developer sandbox? | Yes / No | If Yes → use **Workbench** (note: sunset trajectory) or **VS Code + Salesforce Extensions**. |

**Selected tool**: ____________________

**Justification**: ____________________

---

## 2. Operation Parameters

| Parameter | Value |
|-----------|-------|
| Target object(s) | |
| Operation type | Insert / Update / Upsert / Delete / Hard Delete |
| External ID field (upsert only) | |
| Estimated record count | |
| Source file format | CSV |
| Target org | Sandbox / Production |
| Scheduled / automated? | Yes / No |

---

## 3. API Mode Selection (Data Loader only)

| Mode | When to Use |
|------|-------------|
| Bulk API 2.0 | Default for >200 records. Batching is automatic — do not set manual batch size. |
| SOAP | <200 records per batch, synchronous error feedback needed, or object not supported by Bulk API. |
| Bulk API v1 | Legacy only. Prefer Bulk API 2.0 for all new operations. |

**Selected mode**: ____________________

---

## 4. Pre-Operation Security Checklist

Complete before every load, especially against production.

- [ ] Credentials are encrypted or use OAuth JWT — no plaintext passwords in `process-conf.xml`.
- [ ] `process-conf.xml` is excluded from version control (`.gitignore` or equivalent).
- [ ] Running user's profile or permission set has been confirmed — minimum permissions for the operation only.
- [ ] If operation is **Hard Delete**: running user has the **Bulk API Hard Delete** permission. This has been confirmed with the data owner.
- [ ] Source CSV has been reviewed for PII fields that should not be exported or re-imported unnecessarily.
- [ ] If using Salesforce Inspector or any third-party browser extension: security policy allows it in this org. (Not for production data changes in regulated environments.)
- [ ] If using Workbench: operation is ad-hoc / exploratory / non-production only.

---

## 5. Sandbox Test Run

Before full production load:

- [ ] Ran a sample load of ~1,000 records against a full-copy or partial sandbox.
- [ ] Reviewed success CSV: record count matches expectation.
- [ ] Reviewed error CSV: all errors are understood and resolved or accepted.
- [ ] Field mapping verified against target object fields.
- [ ] Lookup relationships resolved correctly (no lookup failures in error CSV).

**Sample run results**: ____________________

---

## 6. Full Load Execution Log

| Item | Detail |
|------|--------|
| Date / time started | |
| Executed by | |
| Job ID (Bulk API) | |
| Total records submitted | |
| Success count | |
| Error count | |
| Error CSV archived at | |
| Success CSV archived at | |

---

## 7. Post-Load Validation

- [ ] Record count in org matches expected count (SOQL: `SELECT COUNT() FROM <Object>`).
- [ ] Spot-checked 5–10 records for field accuracy.
- [ ] Related records (lookups, relationships) resolve correctly.
- [ ] No unexpected duplicate records created (especially for Accounts/Contacts).
- [ ] Automation (Flows, triggers, process builders) triggered as expected — or was intentionally disabled and re-enabled.

**Validation sign-off**: ____________________ Date: ____________________

---

## 8. Automation / Schedule Notes (if applicable)

If this load is scheduled or run via CI:

- [ ] `process-conf.xml` uses encrypted password or OAuth JWT (no plaintext).
- [ ] Scheduler (cron, Data Loader scheduler, CI pipeline) logs are retained and monitored.
- [ ] Failure alerting is configured — job failures do not go unnoticed.
- [ ] Credentials have a rotation schedule.

**Schedule / automation details**: ____________________
