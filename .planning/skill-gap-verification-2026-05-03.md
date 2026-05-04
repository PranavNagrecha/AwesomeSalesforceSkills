# Skill Gap Verification — 2026-05-03

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: 930 skills.

## Sources scanned

- BACKLOG.yaml `RESEARCHED` pool (37 entries) — primary source for candidates this run.
- Decision trees (`standards/decision-trees/*.md`) — every cited skill resolves to an existing file (no broken refs).
- Cross-skill lookups: probed Heroku-Connect, Private-Connect, Loyalty Mgmt, Salesforce Maps to detect stale BACKLOG entries (most BACKLOG `RESEARCHED` items were already skills — `private-connect-setup`, `loyalty-management-setup`, `lwc/virtualized-lists`, `lwc/drag-and-drop`, `slack-workflow-builder`, `salesforce-maps`).

## Candidate evaluation

Threshold rules (per scheduled-task brief):
- Top hit > 4.0 in same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta against existing skill.
- Top hit < 2.5 across both phrasings → ACCEPT.

### A. integration/automotive-cloud-setup — ACCEPT

| Phrasing | Top skill | Score |
|---|---|---|
| `automotive cloud vehicle dealer` | (none) | — |
| `automotive cloud setup vehicle lifecycle` | (none) | — |
| `automotive cloud lead distribution dealer` | admin/partner-community-requirements | 4.185 |

Top two phrasings return Coverage: NONE. Third phrasing's hit (`partner-community-requirements`) is generic Experience Cloud setup, not industry-cloud-specific. Knowledge import `salesforce-automotive-cloud.md` exists (1448 lines) but no skill consumed it. ACCEPT.

### B. integration/manufacturing-cloud-setup — ACCEPT

| Phrasing | Top skill | Score |
|---|---|---|
| `manufacturing cloud sales agreement rebate` | (none) | — |
| `manufacturing cloud account based forecasting` | architect/industries-cloud-selection | 1.867 |

Both phrasings below 2.5 floor. Read `industries-cloud-selection`: lists Manufacturing Cloud in two table rows as a vertical option, no implementation depth. The setup-and-DPE skill is genuinely missing. ACCEPT.

### C. integration/net-zero-cloud-setup — ACCEPT

| Phrasing | Top skill | Score |
|---|---|---|
| `net zero cloud carbon emission factor` | (none) | — |
| `net zero cloud sustainability scope 1 2 3` | (none) | — |

Both phrasings Coverage: NONE. `salesforce-industries-dev-guide.md` knowledge import has Scope3 / VehicleAssetCrbnFtprnt object names but no skill consumes them. ACCEPT.

## Candidates rejected

| Candidate | Top hit | Score | Reason rejected |
|---|---|---|---|
| Heroku Connect / Heroku-Salesforce integration | integration/salesforce-functions-replacement | 4.603 | Same-domain >4.0 → REJECT auto. Functions replacement skill discusses Heroku as migration target. |
| Salesforce backup-and-restore native service | architect/ha-dr-architecture | 4.444 | Same-domain >4.0 → REJECT auto. ha-dr-architecture covers native Backup & Restore + 3rd-party explicitly. |
| Slack Workflow Builder + Salesforce | integration/slack-workflow-builder | 6.091 | Already exists — BACKLOG entry stale. |
| Loyalty Management program tier setup | integration/loyalty-management-setup | 6.995 | Already exists — BACKLOG entry stale. |
| Salesforce Maps territory / route optimization | architect/fsl-optimization-architecture | 3.004 | Adjacent skill exists in 2.5–4.0 band; Maps-specific skill could exist but defer (see backlog). |
| Private Connect AWS PrivateLink | integration/private-connect-setup | 3.492 | Already exists — BACKLOG entry stale. |
| LWC virtualized lists | lwc/virtualized-lists | 3.571 | Already exists — BACKLOG entry stale. |
| LWC drag and drop | lwc/drag-and-drop | 6.451 | Already exists — BACKLOG entry stale. |
| Apex JWT bearer flow | integration/oauth-flows-and-connected-apps | 2.803 | Borderline; oauth-flows-and-connected-apps covers JWT bearer adequately. Defer. |
| Net Zero Cloud (probed first as `revenue cloud order to cash`) | admin/quote-to-cash-process | 5.777 | (separate query — Revenue Cloud rejected; Net Zero accepted) |

## Backlog observations

The BACKLOG `RESEARCHED` pool has substantial drift — at least 6 entries (slack-workflow-builder, loyalty-management-setup, private-connect-setup, lwc-virtualized-lists, lwc-drag-and-drop, salesforce-maps-setup) point at skills that already exist. Future runs of `audit_duplicates.py` should sweep RESEARCHED → DUPLICATE for these. Not in scope for this task.

## Outcome

3 skills accepted (cap reached). All three follow the existing `loyalty-management-setup` industry-cloud pattern.

## Routing scores after build

| Skill | Query | Top skill (score) |
|---|---|---|
| integration/automotive-cloud-setup | `automotive cloud setup vehicle lifecycle` | integration/automotive-cloud-setup (6.282) |
| integration/manufacturing-cloud-setup | `manufacturing cloud sales agreement rebate` | integration/manufacturing-cloud-setup (6.995) |
| integration/net-zero-cloud-setup | `net zero cloud carbon emission factor` | integration/net-zero-cloud-setup (6.995) |

All three rank #1 in their target query with score ≥ 6.0.

## Agent wiring

Each new skill cited by 2 runtime agents:

- `fit-gap-analyzer` (Architecture & licensing section) — for fit-tier classification of stories scoped to a vertical industry cloud.
- `object-designer` (Object & field shape section) — to flag custom-object proposals that shadow Industries-Cloud standard objects.

Total: 3 skills × 2 agents = 6 agent-skill citations added.
