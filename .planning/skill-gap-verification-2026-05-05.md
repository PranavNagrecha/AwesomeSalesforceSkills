# Skill Gap Verification — 2026-05-05

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: 950 skills (after 14 skills shipped between 2026-05-04 and 2026-05-05 from BACKLOG `RESEARCHED` items + duplicate-cleanup wave).

## Sources scanned

- **Decision-tree branch gaps** — every skill cited under `standards/decision-trees/*.md` resolves to an existing skill; one stale label-mismatch (`skills/integration/oauth-flows` vs the actual `oauth-flows-and-connected-apps`) is a doc fix, not a skill gap. No real gaps surfaced from the decision-tree sweep.
- **Cross-skill broken references** — grepped `skills/**/SKILL.md` and `skills/**/references/*.md` for `skills/<domain>/<slug>` paths, then tested existence. 10 broken paths surfaced; 9 were stale label references to skills that exist under different names (e.g. `skills/apex/dynamic-soql` → exists as `apex/apex-dynamic-soql-binding-safety`). **One** broken reference pointed at a skill that does not exist anywhere: `skills/lwc/lwc-lds-writes` is cited in `skills/lwc/lwc-wire-refresh-patterns/SKILL.md` (description scope-exclusion + Related Skills section). That is a verified, repo-self-documented gap.
- **`BACKLOG.yaml` `RESEARCHED` pool** — 28 entries; spot-probed the entries not already eliminated by 2026-05-04's audit. All probed RESEARCHED items either already exist (the BACKLOG rows are stale) or were eliminated.
- **Topic-driven probing** — broader probes against `search_knowledge.py` for likely-uncovered architecture and operational topics (Hyperforce, Data Export Service, UI API, Setup Audit Trail, LDS, Connect REST API, hyperforce assistance program, etc.). Two NONE-coverage topics with real architectural depth surfaced.

## Candidate evaluation

Threshold rules (from scheduled-task brief):
- Top hit > 4.0 in same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta.
- Top hit < 2.5 across both phrasings → ACCEPT.

### A. lwc/lwc-lds-writes — ACCEPT

| Phrasing | Top skill | Score |
|---|---|---|
| `lwc updateRecord createRecord deleteRecord lightning uiRecordApi` | (none — no skill above threshold; top chunk is `lwc/wire-service-patterns/llm-anti-patterns` at 1.100) | — |
| `lightning data service write update create delete record lwc` | (none — top chunk `lwc/lwc-wire-refresh-patterns/SKILL.md` at 1.100) | — |
| `wire service decorator pattern apex call lwc` | apex/fsl-mobile-app-extensions | 2.654 |

NONE coverage on the lead phrasings. The reference path `skills/lwc/lwc-lds-writes` is **explicitly named as a Related Skill in `skills/lwc/lwc-wire-refresh-patterns/SKILL.md`** (description scope exclusion: "NOT for Lightning Data Service writes (use lwc-lds-writes)" + Related Skills bullet) but the directory does not exist. The closest sibling (`lwc/wire-service-patterns`) covers the read path explicitly and references writes only as a passing hand-off; it does not cover `recordInput` shape, error envelope (`output.fieldErrors` / `output.errors`), `notifyRecordUpdateAvailable` cross-component refresh, or the `lightning-record-edit-form` vs imperative decision. ACCEPT — verified gap reinforced by repo-self-documentation.

### B. admin/data-export-service — ACCEPT

| Phrasing | Top skill | Score |
|---|---|---|
| `salesforce data export service weekly export csv schedule limit` | (none) | — |
| `data export service export attachment 2gb 48 hour download` | (none) | — |
| `weekly export utility browser download attachment 48 hour` | architect/ha-dr-architecture | 1.522 |
| `salesforce native backup and restore product configure retention policy point in time restore` | architect/ha-dr-architecture | 4.131 |

NONE coverage on the operational mechanics phrasings. `architect/ha-dr-architecture` mentions Backup and Restore (the paid product) and the Native Data Export at strategic level (RPO/RTO framing, tradeoffs vs third-party tools) but does not cover the *operational* mechanics of the free Data Export Service: 48-hour download window, weekly vs monthly cadence eligibility by edition, file-size split, attachment-inclusion behavior, Big Object / External Object exclusions, runbook discipline, the "weekly export = backup" anti-pattern. The 4.131 hit is in a different domain (architect, not admin) and is strategic; the new skill is operational and admin-domain. ACCEPT — domain split is clean (architect = strategy, admin = operate-the-feature), the new skill does not duplicate ha-dr-architecture.

### C. architect/hyperforce-architecture — ACCEPT

| Phrasing | Top skill | Score |
|---|---|---|
| `hyperforce migration first generation infrastructure switch upgrade` | (none) | — |
| `hyperforce migration first generation infrastructure customer migration` | architect/ha-dr-architecture (1.717), integration/salesforce-functions-replacement (1.854) | — |
| `hyperforce migration runbook check data residency change` | architect/ha-dr-architecture (1.505), architect/health-cloud-data-residency (3.687) | — |
| `hyperforce architecture cloud provider aws azure region selection` | architect/ha-dr-architecture (1.900), architect/health-cloud-data-residency (2.464) | — |

NONE-or-weak coverage on every phrasing. Hyperforce is *mentioned* in ~10 existing skills (ha-dr-architecture, health-cloud-data-residency, government-cloud-compliance, hybrid-integration-architecture, integration-security-architecture, salesforce-support-escalation, etc.) but no skill is *centered* on it. The new skill addresses a distinct architect-level concern: migration readiness, region selection, customer-side IP allowlisting, validation test plan, and the residency-vs-sovereignty distinction. The vertical-specific health-cloud-data-residency at 3.687 is health-cloud-only; hyperforce-architecture is the cross-vertical baseline that those vertical skills layer on top of. ACCEPT.

## Candidates rejected

| Candidate | Top hit | Score | Reason rejected |
|---|---|---|---|
| salesforce-backup-and-restore (paid product, configure-mechanics skill) | architect/ha-dr-architecture | 4.131–4.322 | Configure-mechanics for the *paid* product is too narrow as a standalone skill; the strategic context lives in ha-dr-architecture and the new admin/data-export-service explicitly delineates the gap. Defer until concrete configure-mechanics demand emerges. |
| setup-audit-trail | admin/compliance-documentation-requirements | 3.874 | Compliance skill already covers Setup Audit Trail's 180-day retention limit, archival need, and the LLM-anti-pattern of treating it as long-term audit record. Delta too thin. |
| connect-rest-api-chatter | apex/apex-connect-api-chatter | 5.551 | Already covered at high score. |
| ui-api-record-defaults | admin/list-views-and-compact-layouts | 6.206 | Top hit covers the UI-API record-defaults use case via compact-layout-driven rendering; close-adjacent skills (lwc/wire-service-patterns, lwc/lwc-base-component-recipes) cover programmatic defaults. |
| salesforce-functions-replacement | integration/salesforce-functions-replacement | (exists) | Already exists; not a gap. |
| slack-workflow-builder | integration/slack-workflow-builder | 6.467 | Already exists. |
| private-connect-setup | integration/private-connect-setup | 2.577 | Already exists at borderline retrieval; the skill is real and complete. |
| lwc-drag-and-drop | lwc/drag-and-drop | 6.449 | Already exists. |
| lwc-getRecord-cache-invalidation | lwc/wire-service-patterns + lwc/lwc-wire-refresh-patterns | (combined) | Read-path is fully covered across two existing skills; the new gap is on the *write* side, addressed by lwc-lds-writes. |
| hyperforce-data-residency-vertical | architect/health-cloud-data-residency, architect/government-cloud-compliance | 2.464–6.270 | Vertical-specific residency already covered in dedicated skills; the cross-vertical Hyperforce baseline is now in hyperforce-architecture. |
| RESEARCHED-pool stale entries (multiple) | various existing skills | varies | Confirmed by previous gap-verification runs; rows are pending a backlog-sweep job. |

## Outcome

3 skills accepted (cap reached). Build proceeds.

## Routing scores after build

| Skill | Query | Top skill (score) |
|---|---|---|
| lwc/lwc-lds-writes | `lwc updateRecord createRecord deleteRecord lightning uiRecordApi` | lwc/lwc-lds-writes (6.995) |
| lwc/lwc-lds-writes | `lightning data service write update create delete record lwc` | lwc/lwc-lds-writes (6.497) |
| admin/data-export-service | `salesforce data export service weekly export csv schedule limit` | admin/data-export-service (6.845) |
| admin/data-export-service | `is weekly data export a backup salesforce native restore` | admin/data-export-service (5.759) |
| architect/hyperforce-architecture | `hyperforce migration first generation infrastructure customer migration` | architect/hyperforce-architecture (6.995) |
| architect/hyperforce-architecture | `hyperforce region selection data residency ip allowlist update` | architect/hyperforce-architecture (6.995) |

All three skills rank #1 in their target queries with score ≥ 5.0 (well above the >2.5 fixture-required ranking).

## Agent wiring

8 agent-skill citations added across 7 agents (Wave-3 LWC dev tier, Wave-3b admin auditor, Wave-3 architect tier):

| Agent | Section | Skill | Why this agent benefits |
|---|---|---|---|
| `lwc-builder` | Data binding (UI API / GraphQL / Apex) | lwc/lwc-lds-writes | Generated LWC bundles writing records via LDS need correct `recordInput` shape, structured error mapping, and refresh strategy |
| `lwc-auditor` | Data binding | lwc/lwc-lds-writes | Audits existing LWCs for LDS-write anti-patterns: Id placement, schema-import dereferencing, dirty-field whitelisting, error-envelope handling |
| `lwc-debugger` | Data axis | lwc/lwc-lds-writes | Diagnoses LDS-write failure modes (INVALID_FIELD_FOR_INSERT_UPDATE, DUPLICATES_DETECTED, INSUFFICIENT_ACCESS_OR_READONLY) and post-write cache misses |
| `audit-router` | Mandatory Reads | admin/data-export-service | Routes "is our backup strategy real?" claims through the real-backup-vs-evidence-archive disambiguation |
| `sandbox-strategy-designer` | Mandatory Reads | admin/data-export-service | Sandbox-seeding workflows reference Data Export's role and limits honestly |
| `waf-assessor` | Mandatory Reads | architect/hyperforce-architecture | WAF Reliability + Security pillars need Hyperforce-aware framing (region selection, customer-managed-failover assumptions, IP allowlisting) |
| `sandbox-strategy-designer` | Mandatory Reads | architect/hyperforce-architecture | Sandbox migration cadence differs from production; refresh windows shift post-Hyperforce-migration |
| `fit-gap-analyzer` | Architecture & licensing | architect/hyperforce-architecture | Flags backlog stories dependent on Hyperforce-only features (Private Connect, regional Data Cloud) when org is on First-Generation infrastructure |

`agents/_shared/SKILL_MAP.md` updated for the three Wave-3-tracked agents (`audit-router`, `sandbox-strategy-designer`, `waf-assessor`); developer-tier agents (lwc-builder/auditor/debugger) and `fit-gap-analyzer` are tracked only in their own AGENT.md per AGENT_RULES Step 6 guidance.

## Validation result

`python3 scripts/validate_repo.py --changed-only` — **3 skills, 0 errors, 0 warnings.** All three skills pass retrieval fixtures and structural gates. Full-repo validation pending.

## Backlog observations

The `RESEARCHED` pool of `BACKLOG.yaml` continues to drift. By 2026-05-05 around half of the 28 RESEARCHED rows point at skills that already exist (the rows are stale relative to recent shipping waves). A dedicated backlog-sweep job remains the right cleanup; today's run only flags this for visibility.
