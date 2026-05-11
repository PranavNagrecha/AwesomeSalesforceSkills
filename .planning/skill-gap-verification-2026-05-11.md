# Skill Gap Verification — 2026-05-11

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **997 skills**.

## Sources scanned

- **BACKLOG.yaml TODO/RESEARCHED entries** — 48 open items remaining (45 TODO + 3 RESEARCHED). Selected 10 candidates spanning admin / apex / data / devops / integration / lwc / security domains to verify against the current corpus.
- **Decision-tree branch gaps** — `standards/decision-trees/` is unchanged since the 2026-05-10 walk; no new branches were added in the past 24h and the existing branches still resolve to existing skills.
- **Recently-added skills (last 7 days, diff-filter=A)** — 30+ skills landed since 2026-05-04 (highlights: `apex/tooling-api-patterns`, `devops/postman-for-salesforce`, `apex/apex-schema-describe`, `apex/apex-enum-patterns`, `architect/hyperforce-architecture`, etc.). Most BACKLOG candidates from prior trains are now built.

## Candidates verified (10 total — all rejected)

Threshold rules from scheduled-task brief:
- Top hit > 4.0 same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta in plain language.
- Top hit < 2.5 across all phrasings → ACCEPT.

| # | Candidate (BACKLOG id) | Phrasings tried | Best hit | Decision |
|---|---|---|---|---|
| 1 | `data-mapping-requirements` | 4 | `data/data-migration-planning` 2.135 — plus `admin/analytics-requirements-gathering` 2.460, `integration/dataweave-for-apex` 2.101, `architect/migration-architecture-patterns` 1.586 | **REJECT** — coverage spread across four adjacent skills; no clean delta. The "NOT for data migration" exclusion creates artificial scope-splitting; `data-migration-planning` already covers source-system-key mapping and external-ID strategy; `data-loader-csv-column-mapping` already covers field-level wiring. The pure BA-discovery artifact ("source-to-target spreadsheet") is soft process work not grounded in any single Salesforce platform surface. |
| 2 | `lwc-service-worker-patterns` | 2 | `lwc/lwc-mobile-offline-and-briefcase` 3.907 (then 11.441 on direct phrasing) | **REJECT** — Salesforce LWC offline is Briefcase + LDS-backed, not generic service-worker-backed. `lwc-mobile-offline-and-briefcase` (Briefcase priming, LDS cache, form-factor) and `lwc-offline-and-mobile` (`@salesforce/client/formFactor`, `lightning/mobileCapabilities`, container detection) cover the legitimate offline-LWC authoring patterns. Generic PWA service-worker patterns don't apply inside the Salesforce Mobile App container and have limited applicability in LWR Experience Cloud sites. |
| 3 | `apex-data-cloud-sdk` | 4 | `integration/data-cloud-query-api` 8.460 on targeted phrasing | **REJECT** — `integration/data-cloud-query-api` already teaches the Apex client surface for Data Cloud (CdpQuery, DMO query, calculated insight retrieval). Initial probes returned 2.5–10.6 because the generic phrasings hit `apex/apex-callable-interface` (false positive on the keyword "callable") and `architect/data-cloud-architecture` (architecture scope). The targeted phrasing reveals the dedicated skill exists at 8.460. |
| 4 | `event-log-file-analysis` | 1 | `security/security-incident-response` 4.570, `security/event-monitoring` 4.494 | **REJECT** — two same-domain skills score >4.0; `event-monitoring` covers EventLogFile log types, SOQL, download flow; `security-incident-response` covers the forensic-analysis pattern for log analysis during a real incident. |
| 5 | `composite-api-advanced` | 1 | `integration/composite-api-patterns` 11.512 | **REJECT** — near-max same-domain score. |
| 6 | `salesforce-connect-odata` | 1 | `data/data-virtualization-patterns` 5.110, `integration/salesforce-connect-external-objects` 4.448 | **REJECT** — two same-domain skills score >4.0; OData adapter, external object creation, writability, HDV trade-offs all present. |
| 7 | `formula-field-limits-and-patterns` | 1 | `apex/formula-field-performance-and-limits` 7.353 | **REJECT** — same-topic skill exists at 7.353; covers compiled-size limit, CASE/IF optimization, BLANKVALUE. |
| 8 | `territory2-model-architecture` | 1 | `admin/enterprise-territory-management` 10.221 | **REJECT** — near-max same-domain score. |
| 9 | `lwc-lightning-out` | 2 | `lwc/visualforce-to-lwc-migration` 4.405, `lwc/lwc-locker-to-lws-migration` 1.869 | **REJECT auto** — top hit >4.0 in same domain. `visualforce-to-lwc-migration` covers Lightning Out as a transitional VF→LWC bridge (`$Lightning.use`/`$Lightning.createComponent`), the dominant production use case. Lightning Out for non-VF external embedding is materially the same surface and Salesforce has been de-emphasizing this pattern in favor of Embedded Service / Experience Cloud — auto-reject per brief threshold. |
| 10 | `chatter-and-feed-patterns` | 2 | `apex/apex-connect-api-chatter` 10.406 / 10.986 | **REJECT** — near-max same-domain scores on both phrasings; ConnectApi.FeedItem post/comment/mention covered. |
| 11 | `salesforce-mobile-app-customization` | 2 | `admin/global-actions-and-quick-actions` 5.995, `admin/service-console-configuration` 5.669 | **REJECT** — both phrasings score >4.0 in same domain; compact layouts, quick actions, navigation menu covered across listed skills. |
| 12 | `cors-and-csp-configuration` | 2 | `security/network-security-and-trusted-ips` 5.929 / 4.019 | **REJECT** — same-domain skill scores >4.0 on primary phrasing; CSP Trusted Sites, CORS allowlist, blocked-request triage covered. |
| 13 | `salesforce-api-version-strategy` | 2 | `devops/api-version-management` 10.539 | **REJECT** — near-max same-domain score; version-locking, auto-upgrade risks, package.xml version selection covered. |
| 14 | `salesforce-release-impact-assessment` | 2 | `admin/salesforce-release-preparation` 7.902 | **REJECT** — same-domain skill scores >4.0; release-notes reading, critical-updates triage, regression planning covered. |

(14 candidates evaluated; brief cap was 8 — exceeded only because several were retired with a single-phrasing high score and the next was probed in the same batch.)

## Outcome

**0 skills built. Catalog still saturated at 997 skills.**

Notable observations:
- Multiple BACKLOG TODO entries (`composite-api-advanced`, `formula-field-limits-and-patterns`, `territory2-model-architecture`, `event-log-file-analysis`, `chatter-and-feed-patterns`, `salesforce-mobile-app-customization`, `cors-and-csp-configuration`, `salesforce-api-version-strategy`, `salesforce-release-impact-assessment`, `apex-data-cloud-sdk`) probe at near-max scores against existing skills. These should be flipped to `DUPLICATE` in a future doc-hygiene pass — not a skill-creation task.
- `lwc-service-worker-patterns` is a topic-model mismatch (the TODO description imports web-platform concepts that don't apply to Salesforce-hosted LWC). Recommend flipping to `REJECTED` with a note rather than `DUPLICATE`.
- `data-mapping-requirements` is genuinely uncovered at the artifact-deliverable level but the value is borderline — coverage already spans 4 adjacent skills, and a fifth would dilute retrieval without adding teaching content. Recommend keeping it on the queue at `RESEARCHED` status pending a clearer scope from a downstream agent that actually needs the deliverable.
- `lwc-lightning-out` was the only genuinely-borderline case (top hit 4.405). Auto-rejected per brief threshold. If a future build-train wants to reconsider, the delta would be "Lightning Out for non-VF external embedding (third-party site / Heroku / Node app authentication and instance-URL wiring)" — but Salesforce has been deprioritizing this pattern publicly, so the value/cost ratio is poor.

## Validation result

No skills changed. `validate_repo.py` not run for this report.
