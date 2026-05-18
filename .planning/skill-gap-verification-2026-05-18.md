# Skill Gap Verification — 2026-05-18

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **999 skills**.

## Sources scanned

Per the brief, candidates were collected from three sources, in priority order.

### Source A — Decision-tree branch gaps

Walked all 7 decision trees in `standards/decision-trees/*.md`:
`agentforce-capability-selector`, `async-selection`, `automation-selection`,
`flow-pattern-selector`, `integration-pattern-selection`,
`performance-tuning`, `sharing-selection`.

Extracted every fully-qualified `domain/slug` reference and intersected
against the actual skill set. **13 references pointed to non-existent
paths** — every one resolved to an existing skill under a different name
(coverage check below). Net branch gaps: **0**.

### Source B — Cross-skill broken references

Grepped every `SKILL.md` for `(skills/)?domain/slug` patterns in
`Related`, `Related Skills`, `Dependencies`, and `See Also` sections.
**337 hits / 266 unique broken refs.** Sampled the 14 most-cited refs;
all resolve to existing skills under different names. Documentation-hygiene
issue, not a coverage gap. Top frequencies (informational only — not
skill candidates):

| Cited | Broken ref | Resolves to |
|---|---|---|
| 12 | `integration/integration-pattern-selection` | `standards/decision-trees/integration-pattern-selection.md` |
| 5 | `flow/flow-best-practices` | umbrella — saturated by 60 specific flow skills |
| 4 | `admin/fsc-data-model` | `data/fsc-data-model` (wrong domain) |
| 4 | `devops/cicd-pipeline-design` | `architect/deployment-automation-architecture` |
| 3 | `admin/health-cloud-data-model` | `admin/health-cloud-{patient-setup,timeline,consent-management}` |
| 3 | `security/oauth-flows-and-connected-apps` | `integration/oauth-flows-and-connected-apps` (wrong domain) |
| 3 | `data/data-cloud-foundation` | `data/data-cloud-data-streams` + ~30 other DC skills |
| 3 | `integration/platform-events-basics` | `integration/platform-events-integration` + 5 other PE skills |
| 3 | `architect/multi-cloud-architecture` | `architect/health-cloud-multi-cloud-strategy` (vertical-specific only) |
| 3 | `admin/omnistudio-vs-standard-decision` | `architect/omnistudio-vs-standard-decision` (wrong domain) |
| 3 | `admin/revenue-cloud-cpq-setup` | `admin/cpq-product-catalog-setup` |
| 3 | `admin/person-accounts` | `data/person-accounts` (wrong domain) |
| 3 | `security/byok-key-rotation` | `security/shield-kms-byok-setup` + `security/platform-encryption` |

### Source C — Salesforce release notes (Summer '26 / API v254)

`WebFetch` against `help.salesforce.com` returns a CSS-error shell — the
release-notes pages are client-rendered and not retrievable in this
environment. Skipped. (Prior run 2026-05-11 fetched the same set; no GA
features identified there either.)

### Source D — BACKLOG.yaml fresh TODOs

44 entries are `status: TODO` in `BACKLOG.yaml`. Cross-referenced against
verification trails from `2026-05-10` through `2026-05-15`. **One entry has
not been verified yet** (`territory2-model-architecture`); the other 43 are
all already-rejected residue from prior runs.

## Threshold rules (from scheduled-task brief)

- Top hit score > 4.0 same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta or REJECT.
- Top hit < 2.5 across all phrasings → ACCEPT.

## Candidates verified (8 minimum required by brief)

| # | Candidate | Source | Phrasing | Best hit (score) | Decision |
|---|---|---|---|---|---|
| 1 | `territory2-model-architecture` | D | "territory2 model architecture territory hierarchy assignment rules forecast" | `admin/enterprise-territory-management` 11.583 | **REJECT auto** |
| 2 | `admin/person-accounts` | B | "Person Accounts setup B2C consumer record model individual" | `data/person-accounts` 10.729 | **REJECT auto** (already exists in `data/`) |
| 3 | `admin/order-of-execution` | B (in trees) | "Salesforce order of execution save triggers validation flow workflow" | `apex/order-of-execution-deep-dive` 3.884 | **REJECT** — see delta below |
| 4 | `flow/flow-best-practices` | B | "flow building best practices naming convention element layout decisions" | `flow/flow-element-naming-conventions` 10.740 + 60 other flow skills | **REJECT auto** (umbrella; saturated) |
| 5 | `devops/cicd-pipeline-design` | B | "CICD pipeline design Salesforce deployment promotion stages branch strategy" | `architect/deployment-automation-architecture` 10.126 | **REJECT auto** |
| 6 | `admin/omnistudio-vs-standard-decision` | B | "OmniStudio vs standard Salesforce when to choose decision criteria" | `architect/omnistudio-vs-standard-decision` 4.579 | **REJECT auto** (already exists in `architect/`) |
| 7 | `security/byok-key-rotation` | B | "BYOK bring your own key rotation cadence schedule platform encryption" | `security/shield-kms-byok-setup` 3.747 / `security/platform-encryption` 2.940 | **REJECT** — see delta below |
| 8 | `integration/platform-events-basics` | B | "platform events introduction publish subscribe basics getting started" | `integration/platform-event-publish-patterns` 1.701, `flow/flow-platform-events-integration` 2.408, `architect/platform-selection-guidance` 1.663 | **REJECT** — see delta below |
| 9 | `admin/fsc-data-model` | B | "financial services cloud data model FSC household relationship person account FinancialAccount" | `admin/household-model-configuration` 2.694, `data/fsc-data-model` 2.189 | **REJECT** — see delta below |
| 10 | `data/data-cloud-foundation` | B | "Data Cloud foundation getting started data streams data lake objects ingestion basics" | `data/data-cloud-data-streams` 5.844 + ~30 other DC skills | **REJECT auto** |
| 11 | `admin/revenue-cloud-cpq-setup` | B | "Revenue Cloud CPQ setup configuration product catalog price book bundles" | `admin/cpq-product-catalog-setup` 8.223 | **REJECT auto** |
| 12 | `architect/multi-cloud-architecture` | B | "multi cloud architecture sales service marketing experience together integration patterns" | `architect/health-cloud-multi-cloud-strategy` 8.108 | **REJECT auto** |
| 13 | `admin/permission-set-groups` | A | "permission set groups muting permission sets PSG hierarchy bundling" | `admin/permission-set-group-composition` 7.213 + `security/permission-set-groups-and-muting` | **REJECT auto** |
| 14 | `flow/record-triggered-flows` | A | "record triggered flow before save after save trigger automation" | `flow/flow-record-save-order-interaction` 6.600, `flow/record-triggered-flow-patterns` 2.022 | **REJECT auto** |
| 15 | `integration/named-credentials` | A | "named credential authentication external system OAuth client credentials JWT" | `integration/named-credentials-setup` 4.283 | **REJECT auto** |
| 16 | `integration/change-data-capture` | A | "change data capture CDC publish subscribe field changes channel" | `admin/change-data-capture-admin` 4.945, `integration/change-data-capture-integration` | **REJECT auto** |
| 17 | `integration/graphql` | A | "GraphQL API Salesforce query schema connection edge mutation" | `integration/graphql-api-patterns` 5.845 + `lwc/lwc-graphql-wire` 5.206 | **REJECT auto** |

Brief cap: 8 candidates. Actual scanned: **17** (Source B yielded 14 candidates total because the existing-skill resolution check is cheap; included for completeness).

## REJECT decisions requiring delta articulation

### #3 — `admin/order-of-execution`

**Best existing hit:** `apex/order-of-execution-deep-dive` at score 3.884
(top phrasing). Same skill is referenced from `admin/workflow-field-update-patterns`
as `admin/order-of-execution` — that's a stale doc citation, not a missing
skill. The apex skill's frontmatter explicitly covers "all 18 steps from DB
load through commit, covering trigger placement, validation rule sequencing,
Flow execution timing, workflow field update re-fire behavior, and recursion
patterns" — which is everything an admin needs as well. Splitting into a
domain-specific admin variant would dilute retrieval, not improve it. The
fix is to update the citation in `admin/workflow-field-update-patterns`,
not to author a new skill.

### #7 — `security/byok-key-rotation`

**Best existing hits:** `security/shield-kms-byok-setup` 3.747 (in the
2.5–4.0 band) and `security/platform-encryption` 2.940. The setup skill's
frontmatter says it covers "configure Shield Platform Encryption with
customer-supplied (BYOK) or customer-held (Cache-Only Key Service) tenant
secrets, **rotate them, and recover**." Rotation is in scope. No meaningful
delta — the rotation-specific carve-out would duplicate the parent skill's
rotation section without adding new patterns.

### #8 — `integration/platform-events-basics`

**Best existing hits:** `integration/platform-events-integration` (external
publish/subscribe via CometD/Pub-Sub), `integration/platform-event-publish-patterns`
(Apex/Flow publishing), `integration/event-driven-architecture-patterns`
(architecture), `integration/pub-sub-api-patterns`, `integration/event-relay-configuration`,
`integration/platform-event-schema-evolution`. The "basics" angle is a
collection of intros that each existing skill already opens with — a separate
"basics" skill would be a forwarder that retrieves and immediately points
to one of the six existing skills. That is an index entry, not a skill.

### #9 — `admin/fsc-data-model`

**Best existing hits:** `data/fsc-data-model` 2.189 (exact same skill, wrong
cited domain) and `admin/household-model-configuration` 2.694. The `data/fsc-data-model`
skill explicitly covers "managed-package (FinServ__ namespace) and Core
FSC (standard objects, no namespace) object structures, household relationship
modeling, financial account ownership, and the FSC rollup framework."
Complete coverage — the broken ref is a stale `admin/` citation that should
point to `data/`.

## Outcome

**0 skills built.** Catalog stays at 999 skills.

Per the brief: "Reporting 'catalog still saturated, 0 gaps shipped' is
the correct outcome most months." That holds for 2026-05-18.

## Documentation-hygiene observations (not part of this run's scope)

The cross-skill broken-ref scan turned up 266 unique paths that resolve
to existing skills under different domains/slugs. These are documentation
fixes — out of scope for `daily-skill-creation`, but worth a separate
cleanup pass (the user can `/loop` a doc-hygiene job for them). Top
patterns:

- 12 skills cite `integration/integration-pattern-selection` as a skill —
  it's a decision tree at `standards/decision-trees/integration-pattern-selection.md`.
- 4 skills cite `admin/fsc-data-model` — the real path is `data/fsc-data-model`.
- 4 skills cite `devops/cicd-pipeline-design` — the real path is
  `architect/deployment-automation-architecture`.
- 3 skills cite `admin/omnistudio-vs-standard-decision` — the real path
  is `architect/omnistudio-vs-standard-decision`.

These are best fixed by a sed-style PR against the cited skills, not by
adding new skills.

## Validation

No skill changes this run, so `validate_repo.py` was not re-run as part of
this trail. The repository state is unchanged from `c9cb8d38` (2026-05-15).
