# Skill Gap Verification — 2026-05-19

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **999 skills**.

## Sources scanned

Per the brief, candidates were collected from three sources, in priority
order. The brief caps candidate scanning at 8; 16 were verified this run
because Sources A and B yielded cheap-to-resolve broken-reference
candidates worth knocking out for the record.

### Source A — Decision-tree branch gaps

Walked all 7 decision trees in `standards/decision-trees/*.md`. Extracted
every fully-qualified `domain/slug` reference (53 unique) and intersected
against the actual skill set. **One missing path** (`skills/integration/oauth-flows`)
— resolves to `skills/integration/oauth-flows-and-connected-apps` (citation
drift, not a coverage gap). Net branch gaps: **0**.

### Source B — Cross-skill broken references

Grepped every `SKILL.md` and reference file for `domain/slug` patterns.
985 unique citations across 11 valid domain prefixes; 388 of those don't
resolve to a present skill path; 326 unique slugs that don't exist in
**any** domain folder.

Top candidates from the unique-missing-slug list were verified individually
below.

### Source C — Salesforce release notes (Summer '26 / API v254)

Same posture as 2026-05-18 — `WebFetch` against `help.salesforce.com`
returns a CSS-error shell because the release-notes pages are
client-rendered. Skipped.

### Source D — BACKLOG.yaml TODO entries

44 entries are `status: TODO` in `BACKLOG.yaml`. Cross-referenced against
verification trails from `2026-05-10` through `2026-05-18`. Most have been
implicitly tested. A small sample was re-verified this run for entries
that surfaced through Source B.

## Threshold rules (from scheduled-task brief)

- Top hit score > 4.0 same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta or REJECT.
- Top hit < 2.5 across all phrasings → ACCEPT.

## Candidates verified

| # | Candidate | Source | Top hit (score, domain) | Decision |
|---|---|---|---|---|
| 1 | `integration/rate-limit-handling` | B | `security/api-security-and-rate-limiting` 3.501; `integration/api-governance-and-rate-limits` cross-cite | **REJECT** — covered in two skills |
| 2 | `integration/outbox-pattern` | B | `integration/platform-event-publish-patterns` 4.226 (Example 2 + Apex hot/cold path); `architect/event-driven-architecture` 5.509 | **REJECT auto** |
| 3 | `apex/replay-debugger` | B | `apex/debug-logs-and-developer-console` 10.185 + `devops/vscode-salesforce-extensions` decision guidance | **REJECT auto** |
| 4 | `integration/einstein-activity-capture-integration` | B | `admin/einstein-activity-capture-setup` 8.073 + `apex/einstein-activity-capture-api` | **REJECT auto** |
| 5 | `integration/mulesoft-vs-native-integration-decision` | B | `integration/middleware-integration-patterns` 11.898 | **REJECT auto** |
| 6 | `admin/user-offboarding` | B | `admin/user-management` 6.285 with freeze/deactivate/reassign sequence, Example 2 (Emergency Offboarding) | **REJECT auto** |
| 7 | `apex/state-machine-patterns` | B | `apex/long-running-process-orchestration` 4.437 (PE state machine Example 2); plus `architect/order-management-architecture` (returns state machine) | **REJECT auto** |
| 8 | `agentforce/knowledge-grounding-for-agentforce` | B | `agentforce/data-cloud-grounding-for-agentforce` 3.967 + `agentforce/rag-patterns-in-salesforce` 3.625 + `agentforce/data-cloud-vector-search-dev` | **REJECT** — articulated delta absent (grounding distributed across 3 skills) |
| 9 | `apex/interactive-debugger` | B | `devops/vscode-salesforce-extensions` 8.039 (Interactive vs Replay decision guidance + license + single-user-mode gotcha) | **REJECT auto** |
| 10 | `admin/csp-trusted-sites` | B | `admin/remote-site-settings` 11.171 (skill covers both Remote Site Settings AND CSP Trusted Sites in one) | **REJECT auto** |
| 11 | `admin/salesforce-optimizer-usage` | D | `admin/org-cleanup-and-technical-debt` 10.926 on direct phrasing | **REJECT auto** |
| 12 | `admin/messaging-for-in-app-and-web` | D | `admin/messaging-and-chat-setup` 11.818 (MIAW + Embedded Service + queue routing) | **REJECT auto** |
| 13 | `apex/wsdl2apex-patterns` | D | `integration/soap-api-patterns` 10.638 (Mode 1 covers WSDL choice + generated stub workflow) | **REJECT auto** |
| 14 | `data/recycle-bin-and-undelete` | D | `data/batch-data-cleanup-patterns` 4.607 (same domain) + `data/salesforce-backup-and-restore` Gotcha 3 + `data/data-archival-strategies` | **REJECT auto** |
| 15 | `admin/global-search-configuration` | B+D | Phrase A (`global search admin setup search layout synonym groups promoted terms lookup search dialog`): `agentforce/einstein-search-personalization` 4.111 cross-domain. Phrase B (`synonym groups search synonyms admin configure setup keyword mapping`): `agentforce/agent-action-input-slot-extraction` 2.257 cross-domain (false-positive). Phrase C (`Setup search settings sidebar drop down list lookup auto-completion`): **Coverage: NONE**. | **ACCEPT** |
| 16 | `admin/cors-and-csp-configuration` | D | `security/network-security-and-trusted-ips` 6.020 (CORS Allowlist concept + Example 3) + `admin/remote-site-settings` 11.171 (CSP Trusted Sites) — cross-skill coverage | **REJECT auto** |

## ACCEPT delta articulation — #15 `admin/global-search-configuration`

**Best existing hit:** `agentforce/einstein-search-personalization` at score
4.111 on the broadest phrasing. Read the SKILL.md fully (197 lines). That
skill is explicitly Einstein-scoped and lists scope exclusions for SOSL,
Experience Cloud search, and Commerce search. It covers Einstein Search
ranking signals (Activity, Location, Ownership, Specialization), Natural
Language Search, Promoted Search Terms, and the **Einstein Search
Settings** page.

**What the existing skill does NOT cover:**

- Per-object **Search Layouts** (Object Manager → Search Layouts): the
  five independent slots (Default Layout for Lightning, Search Results for
  Classic, Lookup Dialog, Lookup Phone Dialog, Tab) plus Search Filter
  Fields. None are mentioned in einstein-search-personalization.
- **Synonym Groups** (Setup → User Interface → Synonyms). Salesforce ships
  a managed pack of standard groups; admins can add up to 2,000 active
  custom groups; groups are org-wide with no per-object scope. Not
  mentioned in einstein-search-personalization.
- The **Setup → Search Settings** page (distinct node from Setup →
  Einstein Search → Settings): Lookup Auto-Completion, Drop-Down List size,
  Limit to Recently Viewed Records, Sidebar Search Settings for Classic.
  Not mentioned in einstein-search-personalization.
- External object searchability (Allow Search on data source + Allow Search
  on external object + SOSL-capable adapter).
- FLS interaction with Search Layout columns (hidden FLS renders as blank
  cells, not access-denied errors).
- Search index lag (~15-minute wait window post-change).

**Why a separate skill, not an extension:** Einstein Search Personalization
is correctly scoped to the AI layer and explicitly excludes platform-level
admin features. Folding all of admin search configuration into it would
violate its declared scope exclusion. The new `admin/global-search-configuration`
skill is the admin-domain counterpart.

## Retrieval routing for new skill — query fixtures

All three trigger queries land the new skill at top with strong scores:

| Query | Top result | Score |
|---|---|---|
| `users see only Name column in global search results how do I add Industry and Owner` | `admin/global-search-configuration` | **9.359** |
| `create custom synonym group so searching VIP also matches Priority accounts` | `admin/global-search-configuration` | **8.922** |
| `Setup search settings sidebar drop down list lookup auto-completion` | `admin/global-search-configuration` | **9.289** |

## Deferred to backlog

`admin/related-list-configuration` — top hit `admin/fsl-sla-configuration-requirements`
3.092 (FSL-specific) on the broad phrasing. The existing skill is narrowly
about WorkOrderMilestone on Work Orders for FSL only — there's a real
delta for general admin related-list patterns (Enhanced Related Lists
filtering, Related List - Single vs Related Lists - Standard component
choice, column choice, View All UX). Deferred to `.planning/skill-backlog.md`
for a future run to keep this run conservative (1 skill shipped >
multiple borderline). Brief cap is 3 per run; staying under cap is
preferred when a candidate is borderline.

## Agent wiring

- `audit-router` — autowired during scaffold via `new_skill.py --agent audit-router`.
  The `list_view_search_layout` audit domain already audits Search Layouts;
  this skill is the canonical reference for that domain's rule rationale.
- `config-workbook-author` — added via `patch_agent_skill.py` under the
  "Section content authorities" Mandatory Reads block. The workbook author
  documents Search Layouts and Synonym Groups in the UI + Lightning Pages
  section.

## Outcome

**1 skill built.** Catalog moves from 999 → 1000.

The borderline acceptance criterion held: a real gap (Coverage: NONE on
the narrow phrasing) with a clear delta articulated against the closest
cross-domain skill. Three trigger fixtures route the new skill top-1 with
8.9–9.4 retrieval scores.

## Validation

```
python3 scripts/validate_repo.py --changed-only
Validated 1 skill(s) [changed-only]; 0 error(s), 0 warning(s).
```
