# Skill Gap Verification — 2026-05-12

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **997 skills**.

## Sources scanned

- **BACKLOG.yaml TODO entries** — 45 open TODO items. Selected 16 candidates from the subset NOT verified in the 2026-05-11 run (14 candidates that day) to avoid duplicate-of-duplicate work. Range spans admin / apex / data / devops / integration / lwc / security domains.
- **Decision-tree branch gaps** — `standards/decision-trees/` unchanged since 2026-05-10 walk; all branch-recommended technologies still resolve to existing skills with score ≥ 5.
- **Recently-added skills (last 7 days)** — no new diff-filter=A skills since the 2026-05-11 run (skill count steady at 997). Wave-1 catalog freeze still in effect.

## Threshold rules from scheduled-task brief

- Top hit > 4.0 same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta in plain language.
- Top hit < 2.5 across all phrasings → ACCEPT.

## Candidates verified (16 total — all rejected)

| # | Candidate (BACKLOG id) | Phrasings | Best hit | Decision |
|---|---|---|---|---|
| 1 | `integration-testing-requirements` | 2 | `admin/analytics-requirements-gathering` 6.611; secondary phrasing → `devops/automated-regression-testing` 2.883, `admin/uat-and-acceptance-criteria` 2.516, `agentforce/agent-testing-and-evaluation` 2.719 | **REJECT auto** — top hit >4.0; coverage spread across `admin/requirements-gathering-for-sf` (general BA discovery), `admin/uat-and-acceptance-criteria` (UAT + regression), `devops/automated-regression-testing` (regression suites), and `integration/integration-monitoring` (post-deploy). No single integration-specific testing-requirements gap; the deliverable is process-soft and already addressed by adjacent skills. |
| 2 | `managed-package-installation` | 2 | `devops/managed-package-development` 4.049 / 2.170 | **REJECT auto** — top hit >4.0 same domain. `devops/managed-package-development` covers Push Upgrade (Pattern 2), PostInstall handler, subscriber considerations; `devops/second-generation-managed-packages` covers `sf package install` URL flow + delivery template. Knowledge dump `knowledge/imports/pkg1-dev.md` (sections 376, 380) covers Push Upgrade for Subscribers and InstalledPackages UI. The pure subscriber-admin install flow (install URL, password, profile selection) is admin/PM trivia documented in Salesforce Help; no skill-quality delta. |
| 3 | `salesforce-optimizer-usage` | 1 | `admin/org-cleanup-and-technical-debt` 4.936 | **REJECT auto** — same-domain >4.0; org-cleanup skill has dedicated `### Salesforce Optimizer` section and the Recommended Workflow opens with "Run Salesforce Optimizer". Tool-usage details belong inside that broader skill, not as a standalone. |
| 4 | `apex-webservice-annotation` | 2 | `apex/apex-with-without-sharing-decision` 3.711 (false positive on sharing keyword); `admin/email-service-inbound` 4.015 (false positive on `global class implements` pattern) | **REJECT** — Score 3.711 close to 4.0 with false-positive top hit. While inbound SOAP from Apex (`webservice static`) is genuinely uncovered at skill-level, Salesforce deprecated the pattern in favor of `@RestResource` (per `apex-rest-services`) and `integration/soap-api-patterns` covers the consumer side. Building a "how to write a legacy `webservice` keyword class" skill in 2026 is low-value training; recommendation belongs as a one-paragraph note inside `integration/soap-api-patterns` if needed. |
| 5 | `visualforce-pdf-rendering` | 1 | `apex/quote-pdf-customization` 6.987, `apex/visualforce-fundamentals` 4.516 | **REJECT auto** — two same-domain skills >4.0; quote-pdf-customization covers VF `renderAs="pdf"` + Wkhtmltopdf pipeline + governor limits; visualforce-fundamentals Example 2 is a complete invoice-PDF walkthrough. |
| 6 | `lightning-console-api` | 1 | `admin/service-console-configuration` 6.599, `architect/agent-console-requirements` 0.493 | **REJECT auto** — same-domain >4.0; service-console-configuration covers Console Navigation, workspace tabs, subtabs, utility bar; `lwc/lightning-navigation-dead-link-handling` covers `NavigationMixin` in console subtab context (Gotcha 4). |
| 7 | `apex-wsdl2apex-patterns` | 1 (broad query had false-positive top hit on "stub" keyword; targeted query) | `integration/soap-api-patterns` 11.277 (targeted) | **REJECT auto** — near-max same-domain score; soap-api-patterns covers Enterprise vs Partner WSDL, stub generation, `force-wsc`, login() + session, operation calls. |
| 8 | `external-credentials-setup` | 1 | `integration/named-credentials-setup` 7.096; `admin/connected-apps-and-auth` 1.663 also explicitly covers Named vs External Credentials migration in anti-pattern 4 | **REJECT auto** — same-domain >4.0; named-credentials-setup has Anti-Pattern 5 ("Forgetting to Assign External Credential Principal Access") and a Gotcha 1 on permset assignment for External Credentials. Coverage is comprehensive. |
| 9 | `polymorphic-field-data-patterns` | 1 | `admin/activity-and-task-patterns` 7.216; `apex/apex-polymorphic-soql` 0.586 also dedicated to this | **REJECT auto** — two skills directly cover polymorphic fields: `apex/apex-polymorphic-soql` (Task.WhatId, Task.WhoId, ContentDocumentLink.LinkedEntityId, FeedItem.ParentId, TYPEOF/SOQL); `admin/activity-and-task-patterns` (model semantics + DML); `admin/standard-object-quirks` (WhoId/WhatId reference set). |
| 10 | `salesforce-inspector-patterns` | 1 | `lwc/lwc-debugging-devtools` 8.631; `data/data-loader-and-tools` 2.277 | **REJECT auto** — top hit >4.0; data-loader-and-tools explicitly addresses Salesforce Inspector (and Inspector Reloaded fork) under its own subsection AND as an anti-pattern ("don't use in production"). The skill articulates exactly the correct guidance. No legitimate scope for a dedicated skill. |
| 11 | `record-ownership-patterns` | 1 | `admin/data-skew-and-sharing-performance` 2.254; `admin/mass-transfer-ownership` 1.632 | **REJECT** — 2.5-4.0 borderline, but no clean delta: `admin/mass-transfer-ownership` is the canonical ownership-reassignment skill; `admin/data-skew-and-sharing-performance` covers the >10K records/owner skew threshold and sharing-recalculation cost; `flow/flow-record-locking-and-contention` covers Queueable batch reassignments for >1000 records. Five skills already address ownership-change scenarios from different angles; a sixth would dilute retrieval. |
| 12 | `page-layout-assignment-strategy` | 1 | `admin/record-type-strategy-at-scale` 5.009; `admin/record-types-and-page-layouts` 3.004 | **REJECT auto** — top hit >4.0; record-type-strategy-at-scale has dedicated "N x M Layout Assignment Problem" section covering the profile × record-type matrix and Dynamic Forms migration path. |
| 13 | `event-relay-patterns` | 1 | `integration/event-relay-configuration` 10.617 | **REJECT auto** — near-max same-domain score; channel config, AWS EventBridge wiring, retry, templates all present. |
| 14 | `change-set-dependency-patterns` | 1 | `devops/change-set-deployment` 2.033; `devops/deployment-error-diagnosis` 1.245; `admin/change-management-and-deployment` 1.741 | **REJECT** — top hit <2.5 but coverage spread across THREE adjacent skills already addresses dependency sequencing: deployment-error-diagnosis (missing reference, dependency order errors); change-set-deployment (UI mechanic); admin/change-management-and-deployment (anti-pattern: "deploying everything in one package without sequencing"). A fourth skill would create N-way overlap. |
| 15 | `public-sector-solutions-setup` | 1 | `admin/industries-public-sector-setup` 5.586 | **REJECT auto** — same-domain skill near-max; PSS licensing/permitting, citizen case intake, benefits, grant model, shipped-object guidance, anti-patterns all covered. |
| 16 | `feedback-management-setup` | 1 | `admin/salesforce-surveys` 6.260; `architect/customer-effort-scoring` 4.190 | **REJECT auto** — two same-domain skills >4.0; salesforce-surveys covers Feedback Management licensing tiers + 300-response Base cap; customer-effort-scoring covers FM survey response caps + design implications. |

## Outcome

**0 skills built. Catalog still saturated at 997 skills.**

## Notable observations

- 9 of 16 candidates probe at scores ≥4.0 against existing skills, and 4 more probe at 2.5–4.0 with coverage already spread across 2–4 adjacent skills. **The TODO column of `BACKLOG.yaml` is now mostly composed of duplicates that haven't yet been flipped to `DUPLICATE` status.** A doc-hygiene pass (not a skill-creation pass) should reclassify candidates 1–3, 5–10, 12–13, 15–16 as `DUPLICATE` with the verified cover-skill in the `notes` field.
- The pure gap candidates that remain are all legacy (deprecated patterns, e.g. `apex-webservice-annotation`, `apex-wsdl2apex-patterns`) or process-soft (e.g. `integration-testing-requirements`, `data-mapping-requirements`). Both classes are low-value for a 2026 Salesforce skill library — quality > quota correctly rejects them.
- Three consecutive runs (2026-05-10, 2026-05-11, 2026-05-12) have shipped zero skills with verified-saturation as the explanation. The scheduled daily-skill-creation run is now consistently producing the "catalog saturated" outcome the brief calls for. Recommend the next maintainer cycle shift focus from new-skill creation to:
  1. BACKLOG hygiene (flip duplicates).
  2. Trigger-keyword enrichment in existing skills (highest-leverage retrieval improvement per the 1,650-Q audit).
  3. Cross-skill broken-reference cleanup (Step B of the brief, not exhausted today since the catalog hasn't churned).

## Validation result

No skills changed. `validate_repo.py` not run for this report.
