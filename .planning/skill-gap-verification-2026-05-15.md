# Skill Gap Verification — 2026-05-15

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **997 skills**.

## Sources scanned

- **BACKLOG.yaml TODO entries** — pulled from `python3 -c "import yaml; ..."` filter for `status: TODO`. Excluded entries already verified in prior runs (2026-05-10 through 2026-05-14).
- **Decision-tree branch gaps (Step A)** — last walked 2026-05-10; all branch-recommended technologies still resolve to existing skills at score ≥ 5. Not re-walked.
- **Cross-skill broken references (Step B)** — last walked 2026-05-13; doc-hygiene only. Skipped.
- **Recent Salesforce release notes (Step C)** — last fresh scan 2026-05-11. Skipped this run; no signal change expected within a week.

## Threshold rules from scheduled-task brief

- Top hit > 4.0 same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta in plain language.
- Top hit < 2.5 across all phrasings → ACCEPT.

## Candidates verified (8 total)

| # | Candidate | Phrasing | Best hit (score, same domain) | Decision |
|---|---|---|---|---|
| 1 | `managed-package-installation` (subscriber-side) | "managed package installation pre-install checks post-install configuration version" | none above threshold (top chunk score 1.145) | **ACCEPT** (see delta below) |
| 1b | same | "AppExchange managed package install upgrade subscriber org sandbox dependencies" | `devops/second-generation-managed-packages` 2.997 | borderline; see delta |
| 1c | same | "install managed package subscriber org check before install side effects post-install steps" | `devops/managed-package-development` 2.628 | borderline; see delta |
| 1d | same | "install AppExchange package readiness sandbox dry run package limits validate before production" | `devops/second-generation-managed-packages` 1.575 | confirms gap |
| 2 | `visualforce-pdf-rendering` | "Visualforce renderAs PDF page generation CSS print font landscape" | `apex/pdf-generation-patterns` 10.108 | **REJECT auto** |
| 3 | `chatter-and-feed-patterns` (dev) | "Chatter feed FeedItem FeedComment ConnectApi mention publisher action" | `apex/apex-connect-api-chatter` 10.399 | **REJECT auto** |
| 3b | `chatter-administration` (admin) | "Chatter setup admin feed tracking groups topics email notifications unlicensed users" | `admin/chatter-notification-tuning` 11.512 | **REJECT auto** |
| 4 | `recycle-bin-and-undelete` | "recycle bin undelete ALL ROWS soft delete cascade purge retention" | `data/batch-data-cleanup-patterns` 4.340 | **REJECT auto** |
| 5 | `apex-wsdl2apex-patterns` | "Apex SOAP callout WSDL import wsdl2apex stub class generation parsing" | `integration/soap-api-patterns` 7.918 | **REJECT auto** |
| 6 | `lwc-console-workspace-api` (dev `lightning/platformWorkspaceApi`) | "Lightning Console API workspace tab subtab utility bar API navigation" | `admin/service-console-configuration` 9.357 (admin angle, not dev) | borderline; see delta |
| 6b | same | "Service Console LWC workspaceAPI tab API focus enclosing tab refresh" | `lwc/lwc-cross-tab-state-sync` 3.368 | borderline |
| 6c | same | "lightning/platformWorkspaceApi getFocusedTabInfo openSubtab focusTab close tab LWC console developer" | `lwc/lightning-navigation-dead-link-handling` 3.252 | borderline |
| 6d | same | "openTab openSubtab setTabLabel refreshTab IsConsoleNavigation LWC service console programmatic" | `lwc/lightning-navigation-dead-link-handling` 3.278 | **ACCEPT** (clear delta) |
| 7 | `salesforce-optimizer-usage` | "Salesforce Optimizer report run feature adoption cleanup recommendations" | `admin/org-cleanup-and-technical-debt` 9.388 | **REJECT auto** |
| 8 | `related-list-configuration` / `page-layout-assignment-strategy` | "page layout assignment record type profile matrix UI assignment logic" | `admin/record-type-strategy-at-scale` 5.695 | **REJECT auto** |
| 8b | `salesforce-search-configuration` | "Salesforce search configuration searchable objects search layouts SOSL search groups Einstein search" | `data/sosl-search-patterns` 8.040 | **REJECT auto** |

## ACCEPT decisions — delta articulation

### Candidate 1 — `admin/managed-package-installation-and-upgrade`

**Best existing hit:** `devops/managed-package-development` at score 2.997 (top phrasing 1b) / 2.628 (top phrasing 1c).

**Delta:** `managed-package-development` is firmly **publisher-side** — its frontmatter says "Use when building or maintaining Salesforce first-generation managed packages (1GP) for ISV distribution" and its patterns cover namespace registration, the packaging-org structure, authoring the `InstallHandler` Apex interface, push upgrades, and Flow version management. It is the ISV's perspective: "I'm building a package to ship to subscribers." The candidate skill targets the **subscriber admin** perspective: "I'm about to install a third-party AppExchange package in my org — what should I check before, during, and after install?" That workflow includes evaluating the AppExchange listing (security review status, last update date), running the install URL in a developer sandbox first, verifying license-count and dependency limits against the org, reviewing the subscriber-side override matrix for permission sets and profile settings the package will inject, executing post-install configuration steps the publisher's `InstallHandler` cannot do (Named Credential secrets, Flow version activation, Permission Set Group assignment to live users), and the uninstall/rollback fallback. None of that is in `managed-package-development`. The complementary skills (`devops/unlocked-package-development`, `devops/second-generation-managed-packages`, `devops/package-development-strategy`) are all publisher-side as well.

### Candidate 6 — `lwc/lwc-console-workspace-api`

**Best existing hit:** `lwc/lightning-navigation-dead-link-handling` at score 3.278 (top phrasing 6d) / 3.368 (phrasing 6b) — also `lwc/lwc-cross-tab-state-sync` 3.368, `lwc/lwc-focus-management` 2.595.

**Delta:** No LWC skill targets the **`lightning/platformWorkspaceApi`** module surface — the dedicated developer API for Service Console workspace tab manipulation. `lightning-navigation-dead-link-handling` is about NavigationMixin failure handling (deleted records, missing pages); it has **one** Anti-Pattern (#3 — "No console-context detection") and **one** Gotcha (#4 — "Console workspace navigation differs from page navigation") that touch console behavior, and one Example that uses `openSubtab` as a fallback. `lwc-cross-tab-state-sync` is about BroadcastChannel coordination between browser tabs; its console mention is a single Gotcha (#4 — subtab close doesn't auto-broadcast). `lwc-focus-management` is keyboard/accessibility focus, not tab focus. **None** owns `openTab`, `openSubtab`, `closeTab`, `refreshTab`, `setTabLabel`, `setTabIcon`, `setTabHighlighted`, `getFocusedTabInfo`, `getAllTabInfo`, `getEnclosingTabId`, `getTabInfo`, or `IsConsoleNavigation` as a primary surface. `admin/service-console-configuration` (top hit 9.357 on phrasing 6) covers the **declarative** console setup (App Manager, navigation rules, utility bar configuration) — not the runtime LWC API. The candidate skill is the runtime-API counterpart.

## Outcome

**2 skills built** — both verified-gap accept decisions with clear deltas. Catalog goes from 997 → 999.

## Skills delivered

1. `admin/managed-package-installation-and-upgrade` — subscriber-side workflow for installing, upgrading, and rolling back AppExchange managed packages.
2. `lwc/lwc-console-workspace-api` — `lightning/platformWorkspaceApi` and `lightning/platformUtilityBarApi` module surface for Service Console developer integration.

## Rejected candidates (summary)

- `visualforce-pdf-rendering` — `apex/pdf-generation-patterns` 10.108
- `chatter-and-feed-patterns` (dev) — `apex/apex-connect-api-chatter` 10.399
- `chatter-administration` — `admin/chatter-notification-tuning` 11.512
- `recycle-bin-and-undelete` — `data/batch-data-cleanup-patterns` 4.340
- `apex-wsdl2apex-patterns` — `integration/soap-api-patterns` 7.918
- `salesforce-optimizer-usage` — `admin/org-cleanup-and-technical-debt` 9.388
- `page-layout-assignment-strategy` — `admin/record-type-strategy-at-scale` 5.695
- `salesforce-search-configuration` — `data/sosl-search-patterns` 8.040

## Validation result

`python3 scripts/validate_repo.py` — **Validated 999 skill(s); 0 error(s), 19 warning(s)**. All 19 warnings are pre-existing on other skills (none on the two new skills).

`python3 scripts/validate_repo.py --changed-only` — **Validated 2 skill(s) [changed-only]; 0 error(s), 0 warning(s)**.

## Retrieval routing scores (new skills)

For each new skill, the most relevant trigger queries route as expected:

### `admin/managed-package-installation-and-upgrade`

| Query | Top hit | Score |
|---|---|---|
| "how do I safely install a managed package in production" | admin/managed-package-installation-and-upgrade | 5.202 |
| "subscriber side AppExchange package install upgrade post-install configuration" | admin/managed-package-installation-and-upgrade | 10.149 |

### `lwc/lwc-console-workspace-api`

| Query | Top hit | Score |
|---|---|---|
| "openSubtab refreshTab LWC service console workspace API" | lwc/lwc-console-workspace-api | 11.184 |
| "IsConsoleNavigation detect LWC running service console" | lwc/lwc-console-workspace-api | 10.009 |

Both skills surface at top-1 with ≥5.0 routing scores — well above the 2.5 noise floor and the 3-result top_k requirement from the brief.

## Agent wiring

- `admin/managed-package-installation-and-upgrade` → `release-train-planner`, `fit-gap-analyzer` (with hand-written one-line descriptions)
- `lwc/lwc-console-workspace-api` → `lwc-builder`, `lwc-auditor` (with hand-written one-line descriptions)
- `agents/_shared/SKILL_MAP.md` updated for the Wave A/B/C tier `release-train-planner` entry (developer-tier `lwc-builder` / `lwc-auditor` are tracked only in their own AGENT.md per AGENT_RULES Step 6).

## BACKLOG.yaml hygiene

- `managed-package-installation` TODO entry reclassified `DUPLICATE` with a note pointing at the shipped `admin/managed-package-installation-and-upgrade` slug so the queue dashboard does not re-surface it.
