# Skill Gap Verification — 2026-05-04

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: 933 skills (after Wave-2 cycle on 2026-05-03 added 3 industry-cloud setup skills).

## Sources scanned

- BACKLOG.yaml `RESEARCHED` pool (37 entries) — primary source for candidates this run.
- Decision trees (`standards/decision-trees/*.md`) — every cited skill resolves to an existing file.
- Cross-skill broken refs — `loyalty-management-setup` cites `loyalty-program-architecture` as a Related Skill, but the skill folder does not exist (`skills/architect/loyalty-program-architecture` missing).

## Candidate evaluation

Threshold rules (per scheduled-task brief):
- Top hit > 4.0 in same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta against existing skill.
- Top hit < 2.5 across both phrasings → ACCEPT.

### A. admin/lightning-experience-transition — ACCEPT

| Phrasing | Top skill | Score |
|---|---|---|
| `lightning experience transition project assessment org wide migration` | (none) | — |
| `lightning experience readiness assessment LEX transition` | admin/ai-use-case-assessment | 2.290 |
| `classic to lightning experience migration readiness` | admin/app-and-tab-configuration | 1.540 |
| `lightning experience readiness check Visualforce javascript button` | admin/custom-button-to-action-migration | 5.300 |

Multiple piece-skills exist (custom-button-to-action-migration, knowledge-classic-to-lightning, classic-email-template-migration, dynamic-forms-migration, visualforce-to-lwc-migration, lwc-locker-to-lws-migration, app-and-tab-configuration) but **no project-level orchestrator skill** for the full Lightning Experience Transition program. The 5.300 hit is a button-specific migration. The skill has a clear delta: end-to-end program orchestration (Readiness Check → asset triage matrix → phased pilot → user-by-user adoption telemetry → cutover criteria) that piece-skills do not address. ACCEPT.

### B. integration/salesforce-maps-setup — ACCEPT

| Phrasing | Top skill | Score |
|---|---|---|
| `salesforce maps live tracking driving directions visit planner` | (none) | — |
| `salesforce maps territory route optimization geolocation` | architect/fsl-optimization-architecture | 2.860 |
| `salesforce maps mapanything route territory plan` | admin/consumer-goods-cloud-setup | 3.379 |

Top three phrasings: Coverage NONE for the lead phrasing; FSL skills (admin/fsl-scheduling-optimization-design, architect/fsl-optimization-architecture, data/fsl-territory-data-setup) cover Field Service scheduling and FSMP polygon objects but not Salesforce Maps. Salesforce Maps (formerly MapAnything) is a distinct paid product with its own object model (`MapsTerritoryPlan`, `MapsAdvancedRoute`, `MapsLayer`, `MapsLayerProperty`), targeted at non-FSL geo workflows (sales territory planning, live tracking, route optimization for service reps, polygon visualization). Consumer Goods Cloud's `RoutePlan`/`RoutePlanEntry` (3.379) is a different product entirely. ACCEPT.

### C. architect/loyalty-program-architecture — ACCEPT

| Phrasing | Top skill | Score |
|---|---|---|
| `loyalty program architecture tier ladder partner integration` | integration/loyalty-management-setup | 6.995 |
| `loyalty program design point economy fraud prevention` | integration/loyalty-management-setup | (top hit, similar score) |

Top hit at 6.995 is the **setup skill, not the architecture skill** — and `loyalty-management-setup` SKILL.md explicitly cites `loyalty-program-architecture` as a Related Skill that does not yet exist. The setup skill covers configuration mechanics (DPE batch jobs, two-currency model, member portal); the architecture skill is distinct: pre-implementation program design (tier-ladder economics, qualifying-vs-non-qualifying split decision, fraud-prevention strategy, partner network topology, tier-descalation policy, multi-region program splits). Different audience (architect vs admin/dev) and different lifecycle phase (design vs build). The cross-reference in loyalty-management-setup confirms this is a documented gap. ACCEPT.

## Candidates rejected

| Candidate | Top hit | Score | Reason rejected |
|---|---|---|---|
| apex-string-and-regex | apex/apex-regex-and-pattern-matching | 6.842 | Already exists at high score. |
| apex-schema-describe | apex/dynamic-apex | 3.546 | Adjacent skill; dynamic-apex Section 2 covers Schema.describe hierarchy and the loop anti-pattern. Delta too thin. |
| apex-enum-patterns | apex/apex-callable-interface | 4.695 | Same-domain >4.0; callable-interface covers `switch on action` enum dispatch. |
| apex-event-bus-subscriber | apex/platform-events-apex (2.235) + apex/change-data-capture-apex (3.012) | — | Covered by combination of two existing skills + integration/error-handling-in-integrations EventBus retry section. |
| apex-jwt-bearer-flow | security/certificate-and-key-management | 3.946 | Borderline; combined with integration/oauth-flows-and-connected-apps (JWT Bearer section explicit) + devops/github-actions-for-salesforce + devops/bitbucket-pipelines-for-salesforce, JWT is fully covered across 4 skills. |
| lwc-lightning-record-forms | lwc/lwc-base-component-recipes | 4.875 | Same-domain >4.0; recipe skill explicitly templates `lightning-record-form` patterns. |
| lwc-custom-lookup | lwc/lwc-record-picker | 4.130 | Same-domain >4.0; record-picker anti-patterns the custom combobox approach. |
| lwc-datatable-advanced | lwc/lwc-data-table | 6.491 | Already exists at high score. |
| lwc-css-and-styling | lwc/lwc-styling-hooks | 4.573 | Same-domain >4.0. |
| content-document-management | integration/file-and-document-integration (3.991) + apex/apex-blob-and-content-version (1.781) | — | Covered by combination. |
| report-type-strategy | admin/reports-and-dashboards-fundamentals | 6.428 | Already exists at high score. |
| email-deliverability-monitoring | admin/email-deliverability-strategy | 6.995 | Already exists. |
| data-cloud-vs-analytics-decision | architect/data-cloud-vs-analytics-decision | 6.270 | Already exists — BACKLOG entry stale. |
| flow-large-data-volume-patterns | flow/flow-large-data-volume-patterns | 5.320 | Already exists — BACKLOG entry stale. |
| flow-dynamic-choices | flow/flow-dynamic-choices | (folder exists) | Already exists — BACKLOG entry stale. |
| flow-action-framework | flow/flow-action-framework | (folder exists) | Already exists — BACKLOG entry stale. |
| devops-center-advanced | devops/devops-center-advanced | (folder exists) | Already exists — BACKLOG entry stale. |
| oauth-token-management | security/oauth-token-management | (folder exists) | Already exists — BACKLOG entry stale. |
| revenue-cloud-architecture | admin/quote-to-cash-process | 4.418 | Same-domain >4.0; quote-to-cash covers Revenue Cloud order-to-cash. |
| salesforce-shield-architecture | security/salesforce-shield-deployment | 3.153 | Adjacent skill exists; deployment skill covers EM + Encryption + FAT bundling. Delta too thin for separate "architecture" skill. |
| sustainability-reporting | integration/net-zero-cloud-setup | 6.995 | Already exists (built 2026-05-03). |
| migration-architecture-patterns (org merge/split) | architect/multi-org-strategy | 2.907 | Borderline; multi-org-strategy anti-patterns Section 5 explicitly addresses org-merger pitfalls. Defer to later run if a focused org-merge playbook is requested. |
| classic-email-template-migration | admin/classic-email-template-migration | (exists) | Already exists. |
| crm-analytics-security-predicates | (probed under sec-predicate phrasings) | — | Defer; `crm-analytics` family of skills exists with overlapping coverage; not a verified gap. |

## Backlog observations

The BACKLOG `RESEARCHED` pool continues to drift — 6+ entries from 2026-05-03's audit (slack-workflow-builder, loyalty-management-setup, private-connect-setup, lwc-virtualized-lists, lwc-drag-and-drop, salesforce-maps-setup itself, plus today's confirmations: data-cloud-vs-analytics-decision, flow-large-data-volume-patterns, flow-dynamic-choices, flow-action-framework, devops-center-advanced, oauth-token-management) point at skills that already exist. A backlog-sweep job should mark these RESEARCHED → DUPLICATE. Out of scope for this task.

## Outcome

3 skills accepted (cap reached). Build proceeds.

## Routing scores after build

| Skill | Query | Top skill (score) |
|---|---|---|
| admin/lightning-experience-transition | `lightning experience transition project assessment org wide migration` | admin/lightning-experience-transition (6.857) |
| admin/lightning-experience-transition | `users keep switching back to Classic from Lightning Experience` | admin/lightning-experience-transition (5.021) |
| integration/salesforce-maps-setup | `salesforce maps live tracking driving directions visit planner` | integration/salesforce-maps-setup (6.995) |
| integration/salesforce-maps-setup | `salesforce maps territory route optimization geolocation` | integration/salesforce-maps-setup (6.995) |
| architect/loyalty-program-architecture | `loyalty program architecture tier ladder partner integration` | architect/loyalty-program-architecture (6.594) |
| architect/loyalty-program-architecture | `loyalty program design point economy fraud prevention tier descalation` | architect/loyalty-program-architecture (6.995) |

All three skills rank #1 in their target queries with score ≥ 5.0.

## Agent wiring

6 agent-skill citations added across 4 agents (each new skill cited by 2 runtime agents):

| Agent | Section | Skill | Why this agent benefits |
|---|---|---|---|
| `audit-router` | Mandatory Reads | admin/lightning-experience-transition | Routes LE-Transition / readiness-check audits to a program-orchestrator skill instead of the deprecated single-page LRP auditor |
| `fit-gap-analyzer` | Architecture & licensing | admin/lightning-experience-transition | Flags backlog stories that depend on LEX-only features (Dynamic Forms, LWC actions) when the org has Classic users in scope |
| `fit-gap-analyzer` | Architecture & licensing | integration/salesforce-maps-setup | Recognizes Maps license tier and product-boundary issues (Maps vs FSL vs Consumer Goods Cloud) for stories scoped to mapping/territory/routing |
| `object-designer` | Object & field shape | integration/salesforce-maps-setup | Flags custom MapTerritory__c / Geo__c proposals when Maps is licensed (mirrors the industry-cloud setup wiring pattern from 2026-05-03) |
| `fit-gap-analyzer` | Architecture & licensing | architect/loyalty-program-architecture | Flags backlog stories that conflict with the loyalty program's architectural decisions before treating them as fits |
| `waf-assessor` | Mandatory Reads | architect/loyalty-program-architecture | Loyalty architecture has WAF implications across Reliability (tier-credit reversal), Scalability (lifetime ledger summary), and Security (fraud prevention) |

## Validation result

`python3 scripts/validate_repo.py` — full repo: **936 skills, 0 errors, 543 warnings** (warnings are pre-existing baseline; none on the new skills). `--changed-only`: 0 errors, 0 warnings on the 3 new skills.
