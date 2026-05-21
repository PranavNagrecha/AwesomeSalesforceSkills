# Skill Gap Verification — 2026-05-21

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **1000 skills**.

## Sources scanned

### Source A — Decision-tree branch gaps

Walked all 7 decision trees in `standards/decision-trees/*.md`. Extracted
every `domain/slug` reference, filtered to valid domains (61 unique).
Cross-referenced against actual `skills/<domain>/<slug>/` paths. 18 paths
"missing" but inspection showed all are slug-drift to existing skills:

- `admin/permission-set-groups`, `admin/permission-sets` → `admin/permission-set-architecture`, `admin/permission-set-group-composition`, `admin/permission-sets-vs-profiles`
- `admin/record-page-performance` → `admin/lightning-page-performance-tuning` (verified 8.584 retrieval)
- `agentforce/agent-creation` → `agentforce/agentforce-agent-creation`
- `architect/event-driven-salesforce-architecture` → `architect/event-driven-architecture`
- `flow/record-triggered-flows` → `flow/record-triggered-flow-patterns`
- `integration/callouts-and-http-integrations` → `apex/callouts-and-http-integrations` (3.418, cross-domain)
- `integration/change-data-capture` → `integration/change-data-capture-integration`
- `integration/graphql` → `integration/graphql-api-patterns`
- `integration/named-credentials` → `integration/named-credentials-setup`
- `integration/oauth-flows` → `integration/oauth-flows-and-connected-apps`
- `integration/salesforce-connect` → `integration/salesforce-connect-external-objects`
- `security/org-hardening` → `security/org-hardening-and-baseline-config`
- glob-only fragments (`apex/async-`, `apex/batch-`, `apex/queueable-`, `apex/scheduled-`) parsed from trees' grouped headings, no real refs

Net branch gaps: **0**.

### Source B — Cross-skill broken references

Grepped every `SKILL.md` and reference file for `domain/slug` patterns.
4,218 unique refs across 11 valid domain prefixes; 387 unique slugs that
don't resolve to a present skill path. Top candidates verified
individually below (Source D table). Most "missing" refs are noise
(`data/v62`, `data/v60`, `ingest/egress`, structural prose) or
slug-drift to existing skills.

Net new gaps: **0**.

### Source C — Salesforce release notes (Summer '26 / API v254)

Same posture as 2026-05-18 / 2026-05-19 — `WebFetch` against
`help.salesforce.com` returns a CSS-error shell because the
release-notes pages are client-rendered. Skipped.

### Source D — BACKLOG.yaml TODO entries + deferred backlog

44 entries are `status: TODO` in `BACKLOG.yaml`. Re-verified the
deferred backlog entry from `2026-05-19` (`related-list-configuration`)
plus a fresh sweep of TODO entries not previously verified.

## Threshold rules (from scheduled-task brief)

- Top hit score > 4.0 same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta or REJECT.
- Top hit < 2.5 across all phrasings → ACCEPT.

## Candidates verified

| # | Candidate | Source | Top hit (score, domain) | Decision |
|---|---|---|---|---|
| 1 | `admin/related-list-configuration` | Deferred (2026-05-19 backlog) + D | Phrase A `related list enhanced configuration quick related list page layout assignment columns` → `admin/fsl-sla-configuration-requirements` 3.072 (FSL-scoped); Phrase B `related list filtering sorting view all configure related records page` → `admin/lightning-page-performance-tuning` 2.752 (performance-only); Phrase C `Enhanced Related Lists Spring 24 filter sort related records` → `admin/health-cloud-timeline` 1.674 (different feature) | **ACCEPT** |
| 2 | `apex/polymorphic-field-data-patterns` | D | `admin/activity-and-task-patterns` 4.268; `apex/apex-polymorphic-soql` 3.160 | **REJECT auto** (activity-and-task covers the polymorphic Activity surface; apex-polymorphic-soql covers the SOQL angle) |
| 3 | `admin/salesforce-mobile-app-customization` | D | `admin/list-views-and-compact-layouts` 10.904 | **REJECT auto** |
| 4 | `admin/record-ownership-patterns` | D | `admin/mass-transfer-ownership` 8.262 | **REJECT auto** |
| 5 | `admin/page-layout-assignment-strategy` | D | `admin/record-type-strategy-at-scale` 6.365 | **REJECT auto** |
| 6 | `security/event-log-file-analysis` | D | `security/event-monitoring` 4.341; `security/security-incident-response` 4.435 | **REJECT auto** |
| 7 | `integration/composite-api-advanced` | D | `integration/composite-api-patterns` 11.736 | **REJECT auto** |
| 8 | `devops/change-set-dependency-patterns` | D | `devops/change-set-deployment` 3.813 | **REJECT** — read top hit; covers explicit/implicit dependencies and the View/Add Dependencies tooling |
| 9 | `admin/account-and-opportunity-teams` | D | `admin/opportunity-management` 6.911 on team-selling phrasing | **REJECT auto** |
| 10 | `admin/global-value-sets-and-picklists` | D | `admin/picklist-data-integrity` 4.752 | **REJECT auto** |
| 11 | `apex/chatter-and-feed-patterns` | D | `apex/apex-connect-api-chatter` 5.321 | **REJECT auto** |
| 12 | `admin/territory2-model-architecture` | D | `admin/enterprise-territory-management` 9.879 | **REJECT auto** |
| 13 | `integration/external-credentials-setup` | D | `integration/named-credentials-setup` 6.232 | **REJECT auto** |
| 14 | `admin/feedback-management-setup` | D | `admin/salesforce-surveys` 7.585 | **REJECT auto** |
| 15 | `admin/experience-cloud-builder-patterns` | D | `admin/experience-cloud-cms-content` 10.417 | **REJECT auto** |
| 16 | `integration/event-relay-patterns` | D | `integration/event-relay-configuration` 10.221 | **REJECT auto** |
| 17 | `admin/formula-field-limits-and-patterns` | D | `apex/formula-field-performance-and-limits` 7.234 | **REJECT auto** |
| 18 | `apex/visualforce-pdf-rendering` | D | `apex/pdf-generation-patterns` 9.856 | **REJECT auto** |
| 19 | `data/data-loader-cli-patterns` | D | `data/data-loader-and-tools` 5.542 | **REJECT auto** |
| 20 | `apex/apex-webservice-annotation` | D | `apex/apex-rest-services` 3.123 (same domain, borderline) | **REJECT** — read top hit; `@RestResource` / `@HttpGet` / `@HttpPost` patterns are core to apex-rest-services |
| 21 | `data/salesforce-inspector-patterns` | D | `data/data-loader-and-tools` 11.477 | **REJECT auto** |
| 22 | `admin/sales-path-and-kanban` | D | `admin/path-and-guidance` 11.720 | **REJECT auto** |
| 23 | `lwc/lwc-service-worker-patterns` | D | `lwc/lwc-mobile-offline-and-briefcase` 7.308 | **REJECT auto** |
| 24 | `admin/public-sector-solutions-setup` | D | `admin/industries-public-sector-setup` 11.788 | **REJECT auto** |
| 25 | `devops/salesforce-api-version-strategy` | D | `devops/api-version-management` 7.754 | **REJECT auto** |
| 26 | `admin/chatter-administration` | D | `admin/chatter-notification-tuning` 6.899 | **REJECT auto** |
| 27 | `admin/report-and-dashboard-subscriptions` | D | `admin/reports-and-dashboards-fundamentals` 8.883 | **REJECT auto** |
| 28 | `integration/cross-org-data-sync-patterns` | D | `integration/salesforce-to-salesforce-integration` 10.848 | **REJECT auto** |
| 29 | `admin/salesforce-release-impact-assessment` | D | `admin/salesforce-release-preparation` 5.135 | **REJECT auto** |
| 30 | `apex/apex-data-cloud-sdk` | D | `integration/data-cloud-query-api` 6.963 | **REJECT auto** |
| 31 | `lwc/lwc-lightning-out` | D | `lwc/visualforce-to-lwc-migration` 8.045 (read fully: Lightning Out is documented as Pattern 4 — Coexistence — with `$Lightning.use()`, `$Lightning.createComponent()`, `apex:includeLightning` wrapper VF page, and Example 4 worked code) | **REJECT** — full coverage in vf-to-lwc-migration |
| 32 | `data/integration-data-quality` | D | `integration/api-error-handling-design` 7.131 on inbound-validation phrasing | **REJECT auto** |
| 33 | `data/integration-testing-requirements` | D | `apex/apex-http-callout-mocking` 4.192; `devops/environment-strategy` 3.721; `admin/uat-and-acceptance-criteria` 1.905 — coverage distributed across mocking + environments + UAT skills | **REJECT** — articulated delta absent |
| 34 | `data/data-mapping-requirements` | D | `admin/analytics-requirements-gathering` 7.875 | **REJECT auto** |

## ACCEPT delta articulation — #1 `admin/related-list-configuration`

**Best existing hit:** `admin/fsl-sla-configuration-requirements` at score
3.072 on Phrase A. Read its content: skill is explicitly FSL-scoped,
focused on WorkOrderMilestone configuration on Work Order page layouts.
The related-list mention is only in the "Layout Checklist" section as a
required FSL step (`WorkOrderMilestone related list added to Work Order
page layout`). It does not cover general related-list configuration
mechanics.

The second-best hit on Phrase B (`admin/lightning-page-performance-tuning`
at 2.752) addresses one specific tradeoff — Related List - Single vs.
Related Lists full component — as a Gotcha (Gotcha 3) for performance
optimization. It does not cover related-list column choice, sort, per-
record-type divergence, Enhanced Related Lists feature surface, or
Search Filter Field interaction.

**What no existing skill covers:**

- The classic 10-column silent-drop cap on Page Layout related lists.
- Sort field selection rules (cross-object formulas and long-text fields
  silently fall back to default sort).
- Enhanced Related Lists (Spring '24+) component features: filter, mass
  actions, 30 rows inline, per-list placement vs. all-in-one block.
- Component choice on Lightning record pages (Related Lists / Related
  List - Single / Related Lists - Quick Links / Enhanced Related Lists)
  and the tradeoffs between them.
- Per-record-type related-list divergence via separate Page Layouts,
  with the layout description as the intent-documentation surface.
- The anti-pattern of using Lightning App Builder visibility filters
  for related-list hiding (component is hidden but Page Layout block
  remains visible to the next layout-editing admin).
- FLS blank-cell behavior on related-list columns (looks like a layout
  bug; it isn't).
- Mobile column truncation to ~4 columns and the column-order
  implication.

**Why this is a separate skill, not an extension of an existing one:**
Adding this material to either FSL-SLA-config or
lightning-page-performance-tuning would mis-scope both (FSL into a
generic admin topic; performance into a feature-coverage topic). The
existing `record-types-and-page-layouts` skill covers Page Layout +
Record Type relationships at the layout-shell level but does not drill
into related lists specifically — its name explicitly scopes elsewhere.

## Built skills

- `admin/related-list-configuration` (1 skill)
  - Wired into agents: `audit-router`, `config-workbook-author`
  - Query-fixture scores (target skill rank in top-3):
    - `related list enhanced configuration quick related list page layout assignment columns` → **11.633 (#1)**
    - `related list filtering sorting view all configure related records page` → **8.824 (#1)**
    - `Enhanced Related Lists Spring 24 filter sort related records page layout` → **11.042 (#1)**
  - Validation: 0 errors, 0 warnings on the new skill (`validate_repo.py --domain admin --skip-drift`)

## Outcome

Catalog size after run: **1001 skills**. One verified gap shipped; 33
candidates rejected with reasons documented above. No additional backlog
entries deferred this run.
