# Skill Gap Verification — 2026-05-22

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **1001 skills**.

## Sources scanned

### Source A — Decision-tree branch gaps

Skipped fresh re-walk. The 2026-05-21 verification ran the exhaustive 7-tree
audit and recorded `Net branch gaps: 0` (slug-drift to existing skills only).
No new decision tree was added today; verification posture rolls forward.

### Source B — Cross-skill broken references

Same posture as 2026-05-21 — top-tier broken-refs were re-verified individually
in Source D (the BACKLOG TODO sweep covers the same surface). No net new gaps.

### Source C — Salesforce release notes

Skipped — `WebFetch` against `help.salesforce.com` continues to return CSS-only
shells for release-notes pages (client-rendered). Tracked as a known limitation.

### Source D — BACKLOG.yaml TODO sweep (10 candidates not covered by 2026-05-21)

The 2026-05-21 run audited 34 candidates from BACKLOG.yaml. Identified 10 TODO
entries that were not yet verified individually; ran two phrasings each.

## Threshold rules (from scheduled-task brief)

- Top hit score > 4.0 same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta after reading the top hit's SKILL.md or REJECT.
- Top hit < 2.5 across all phrasings → ACCEPT.

## Candidates verified

| # | Candidate | Phrase 1 top hit (score) | Phrase 2 top hit (score) | Decision |
|---|---|---|---|---|
| 1 | `apex/apex-wsdl2apex-patterns` | `integration/soap-api-patterns` 3.444 | `integration/soap-api-patterns` 8.273 (keyword overlap noise — soap-api-patterns is INBOUND only) | **ACCEPT** (delta articulated below) |
| 2 | `admin/salesforce-optimizer-usage` | `admin/org-cleanup-and-technical-debt` 3.59 | `admin/org-cleanup-and-technical-debt` 10.57 | **REJECT auto** |
| 3 | `admin/org-data-export-patterns` | `admin/data-export-service` 10.43 | `admin/data-export-service` 11.60 | **REJECT auto** |
| 4 | `admin/salesforce-search-configuration` | `admin/global-search-configuration` 9.39 (shipped 2026-05-18) | `admin/commerce-catalog-strategy` 3.24 | **REJECT auto** |
| 5 | `lwc/lightning-console-api` | `lwc/lwc-console-workspace-api` 4.65 / `admin/service-console-configuration` 5.59 | `lwc/lwc-console-workspace-api` 10.56 | **REJECT auto** |
| 6 | `data/recycle-bin-and-undelete` | `admin/system-field-behavior-and-audit` 2.15 | `data/salesforce-backup-and-restore` 2.74 / `data/batch-data-cleanup-patterns` 4.24 | **REJECT** — read top hits; `system-field-behavior-and-audit` covers `Database.undelete()`, `IsDeleted ALL ROWS`, 15-day window, and `Database.UndeleteResult` handling. `batch-data-cleanup-patterns` covers Recycle Bin storage / `emptyRecycleBin`. Articulated delta absent. |
| 7 | `admin/messaging-for-in-app-and-web` | `admin/messaging-and-chat-setup` 11.79 | `admin/messaging-and-chat-setup` 11.24 | **REJECT auto** |
| 8 | `security/cors-and-csp-configuration` | `security/network-security-and-trusted-ips` 5.97 (4 concepts cover Trusted IPs, Login IP Ranges, CSP Trusted Sites, CORS Allowlist) | `security/network-security-and-trusted-ips` 5.82 | **REJECT** — full coverage verified in top hit |
| 9 | `integration/salesforce-connect-odata` | `integration/salesforce-connect-external-objects` 9.25 | `integration/salesforce-connect-external-objects` 8.75 | **REJECT auto** |
| 10 | `data/data-export-and-backup-patterns` | `data/salesforce-backup-and-restore` 10.30 | `admin/data-export-service` 11.25 | **REJECT auto** |

## ACCEPT delta articulation — #1 `apex/apex-wsdl2apex-patterns`

**Best existing hit:** `integration/soap-api-patterns` at score 8.273 on Phrase 2.

Read the skill in full: it is exclusively about the **inbound** direction —
Salesforce-as-SOAP-server, where external Java/.NET/Python clients call Salesforce's
enterprise or partner WSDL. Mode 1 / 2 / 3 are about implementing, reviewing, and
troubleshooting integrations INTO Salesforce. Authentication is via `login()` +
`sessionId`. Both examples (`.NET Enterprise WSDL`, `Java ISV Partner WSDL`) show
client-side stub generation against Salesforce's WSDL, not Apex consuming a vendor
WSDL.

The 8.273 score is **keyword overlap noise** — "SOAP" + "WSDL" + "stub" + "generate"
appear in both topics but cover opposite directions.

**What `integration/soap-api-patterns` does NOT cover:**

- The Setup > Apex Classes > **Generate from WSDL** tool — the parser-imposed
  1 MB WSDL cap, the 1 MB compiled-Apex cap, unsupported XSD constructs
  (`xsd:choice`, `xsd:any`, external `<xsd:import>`, mixed content, recursive
  types), SOAP 1.2 rejection.
- The generated stub's `_x`-suffixed HTTP control properties (`endpoint_x`,
  `timeout_x`, `inputHttpHeaders_x`, `outputHttpHeaders_x`, `clientCertName_x`).
- The two-catch ladder: `System.WebServiceCalloutException` (SOAP fault, HTTP 500
  with `<faultcode>` body) vs. `System.CalloutException` (transport-level).
- `WebServiceMock` interface for outbound SOAP test coverage — the literal
  `response.put('response_x', element)` runtime contract, and why `HttpCalloutMock`
  silently fails to intercept these callouts.
- Named-Credential wiring: `endpoint_x = 'callout:<NC>'` and the silent-strip
  behavior of `Authorization` headers set in `inputHttpHeaders_x` when the
  endpoint resolves to an NC.
- The hand-edit-vs-regen workflow: edits to the cleaned WSDL on disk vs. the
  generated `.cls` (which is destroyed on regen).
- Queueable / Batch wrapping rules: stub instances are not Serializable, so they
  must be instantiated inside `execute()`, not stored as Queueable member fields.

**Why this is a separate skill, not an extension of `soap-api-patterns`:**
The inbound and outbound directions are categorically distinct integration
patterns with non-overlapping tooling, auth models, exception types, and test
mocks. Bundling them into one skill would dilute both — `soap-api-patterns`
already excludes outbound in its `NOT for ...` clause. The new skill explicitly
links to it as the inbound counterpart.

## Built skills

- `apex/apex-wsdl2apex-patterns` (1 skill)
  - Wired into agents: `apex-builder` (under "Bulk APIs (REST / SOAP / Continuation / events)"), `apex-refactorer` (under "Callouts (refactor to HttpClient + Named Credentials)")
  - Query-fixture scores (target skill rank in top-3):
    - `Apex stub class generate WSDL import third-party SOAP service` → **11.468 (#1)**
    - `outbound SOAP callout from Apex WSDL parse generate proxy class` → **11.310 (#1)**
    - `WebServiceMock mock SOAP callout Test setMock wsdl2apex generated stub` → **10.392 (#1)**
  - Validation: 0 errors, 0 warnings on changed-only; full repo `0 errors, 19 warnings` (all 19 warnings pre-existing on unrelated skills)

## Outcome

Catalog size after run: **1002 skills**. One verified gap shipped (closing a
TODO entry from BACKLOG.yaml that has been outstanding since the initial queue
import). Nine candidates rejected with reasons documented above. No additional
backlog entries deferred this run.
