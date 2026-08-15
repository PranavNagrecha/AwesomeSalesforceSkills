# Changelog

All notable changes to SfSkills are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The project uses semantic versioning keyed to the Salesforce release cadence (minor bumps per Spring/Summer/Winter release).

## [Unreleased]

### Changed — licence: Apache-2.0 / MIT → PolyForm Small Business 1.0.0

**SfSkills is now source-available rather than open source.** The source stays
public and forkable; what changed is that free *use* is now conditional on the
size of the organisation using it. Under the
[PolyForm Small Business License 1.0.0](./LICENSE)
(`PolyForm-Small-Business-1.0.0`), use is free for any company with fewer than
100 employees and contractors and under USD 1M in prior-year revenue; larger
organisations need a commercial licence. [`LICENSING.md`](./LICENSING.md) is
the plain-English guide and carries the contact path.

This also resolves the "License declarations disagree" known issue recorded
under 0.4.7 — but by replacing all three declarations, not by reconciling them
to a permissive one.

- Root `LICENSE` replaced with the verbatim PolyForm text plus a
  `Required Notice:` line, which the licence's Notices section obliges
  redistributors to carry.
- `mcp/sfskills-mcp/pyproject.toml` now declares a PEP 639 SPDX expression
  (`license = "PolyForm-Small-Business-1.0.0"`) with `license-files`, and the
  `License :: OSI Approved :: MIT License` trove classifier is gone — PyPI
  rejects an upload carrying both a License-Expression and a `License ::`
  classifier. The build-system floor rises to `setuptools>=77.0.3`, the first
  release with PEP 639 support; older setuptools drops the metadata silently.
- `mcp/sfskills-mcp/LICENSE` added, so the wheel and sdist finally ship one.
  It is a copy of the root file because PEP 639 `license-files` globs cannot
  reference parent directories.
- `.claude-plugin/*.json` regenerated from `scripts/build_plugin.py`, where the
  two `"license"` literals were updated. The JSON is generated — never edit it.
- `CONTRIBUTING.md` gained inbound-licence terms. There were none before, which
  is precisely how the repo ended up carrying Apache-2.0 contributions it could
  not unilaterally relicense.

**Two limits worth stating plainly.** First, this is forward-only: the repo was
public under Apache-2.0 and `sfskills-mcp` 0.4.6 / 0.4.7 shipped to PyPI
declaring MIT. Those grants are irrevocable for the copies already
distributed. Second, the licence excludes but does not collect — it says large
organisations need a licence without saying where to buy one, which is what
`LICENSING.md` exists to answer.

### Added

- **`scripts/check_license.py`** — consistency gate across every surface that
  declares a licence: root `LICENSE`, the packaged copy, the pyproject SPDX
  expression and classifier list, the plugin generator, the generated plugin
  manifests, the README badge, and the presence of `LICENSING.md`. Wired into
  `validate_repo.py` on every invocation. `--fix` re-copies the packaged
  LICENSE; everything else reports rather than rewrites, because a stale
  licence string is a decision to re-make, not a typo to patch. The 0.4.7
  known issue survived because no gate compared these surfaces to each other.

### Changed — chain of title

- Four `SKILL.md` files (`apex/cpq-custom-actions`,
  `flow/flow-email-and-notifications`, `lwc/lwc-focus-management`,
  `security/record-access-troubleshooting`) had their remaining
  externally-contributed prose rewritten before the relicence, so no passage
  contributed under the previous Apache-2.0 inbound terms is redistributed
  under terms its author never agreed to. Technical facts are unchanged
  throughout; only the expression differs. What still blames to the original
  contributor is blank lines, table separators, code fences and one closing
  brace — syntax-dictated scaffolding that carries no copyright.

## [0.4.7] — 2026-08-15 — sfskills-mcp (routing surface, documentation rewrite, release plumbing)

### Fixed — the surface that actually routes

- **The Agentforce topics→subagents rename never reached the shipped roster.**
  It landed in 39 of 53 package bodies and **0 of 53 glosses**. Bodies do not
  route: only `.claude/skills/salesforce-<domain>/references/skill-index.md`
  ships, because `vector_index/` is gitignored and a GitHub-sourced install has
  no FTS5 index. The term *was* in 8 descriptions, but always in the lead, and
  `build_gloss()` ranks triggers > NOT-for > lead against a 220-char cap that
  every Agentforce gloss already sat at (mean 217). The lead is exactly what
  gets clipped, so the rename reached zero users and nothing errored.
  Fixed with four substitutions inside existing `Triggers:` clauses — no
  appends, because there is no headroom. Both vocabularies survive:
  `agentforce-guardrails` carries `topic scope` *and* `subagent scope`. Every
  API literal is untouched (`GenAiPlugin`, `topic_sequence_match`).
- **New: `scripts/check_gloss_coverage.py`.** Answers "did this content wave
  reach the routing surface?" as a command. Exits 1 only when a term is
  declared in the `Triggers:` clause and eaten by the clip; lead-prose and
  body-only mentions are informational and must **not** be promoted — chasing
  them is the vocabulary-append that already cost 5pp of retrieval accuracy.
- **`build_plugin.py --check` now runs in CI** (`validate.yml` → `agents`).
  It previously appeared in no workflow and no hook, so a skill description
  could change while its shipped gloss silently did not.

### Fixed — documentation

- Every root and `docs/` file re-read and rewritten against the repo, with each
  factual claim re-derived by a command rather than recalled. Corrections
  include: flat-export tokens 138,334 → 138,694; index chunk count 132,743 →
  135,409; held-out re-measured to 39.0/48.7 lexical and 40.3/53.9 with
  embeddings; `vector_index/` sizes; the claim that MCP raises
  `sqlite3.OperationalError` on `100% test coverage` (fixed, and the CLI is now
  the lossy surface); "38 read-only tools" (37 are — `emit_envelope` writes);
  `AGENT_RULES` describing the uncited-skill gate as an ERROR (it is a WARN);
  `SECURITY.md` citing `stripInaccessibleFields`, which is not a real Apex API.
- Competitive claims in `docs/comparison.md` were re-sourced or cut. One was
  simply false: forcedotcom/sf-skills was described as having "no live-org
  access", while it ships three stdio MCP servers.
- The retracted "79.2% → 92.2% Hit@1" headline appears nowhere except inside
  explicit retraction framing. Router accuracy 88.3% → 96.1% stands.

### Fixed — tooling

- `scripts/new_skill.py` accepted `experience` and `servicecloud`, which the
  validator rejects, so scaffolding either produced a package that then failed
  `validate_repo.py`. It now imports `ALLOWED_CATEGORIES` from the validator.
- `check_doc_counts.py` required README to state that all 38 MCP tools are
  read-only. Since `emit_envelope` carries `readOnlyHint=False`, no truthful
  sentence could satisfy the gate. Pattern relaxed; the count stays gated.
- `registry/export_manifest.json` was 20 skills behind the tree, so
  `export_skills.py --check` failed. Regenerated.
- `publish-mcp.yml` built a data bundle advertised as containing the lexical
  index while copying a gitignored directory, so `sfskills-mcp-init` produced
  an install that answered `Coverage: NONE` for every query. It now builds the
  index before bundling.
- `.githooks/pre-push` advertised "~10–20s" for a run measured at ~8 minutes.
- Stale comments corrected in `tests.yml` (233 tests and a test class that no
  longer exists), `search_knowledge.py` (an obsolete 2 GB memory warning and a
  config flag described as temporarily disabled since 2026-08-13),
  `.gitignore`, `pr-lint.yml`, and `validate.yml`.

### Known issues

- ~~**License declarations disagree.**~~ *Resolved in [Unreleased]* — root
  `LICENSE` and `.claude-plugin/plugin.json` said Apache-2.0 while
  `mcp/sfskills-mcp/pyproject.toml` declared MIT in both the `license` field
  and the trove classifier, and the package shipped no LICENSE file. This
  predated 0.4.7 (0.4.6 shipped the same way) and was left for the owner to
  resolve. All three surfaces now declare `PolyForm-Small-Business-1.0.0`,
  guarded by `scripts/check_license.py`.
- **CLI and MCP retrieval diverge** on queries containing `_` or non-ASCII:
  `_sanitize_query_for_fts5` strips them before the shared tokenizer, so
  `with_sharing keyword` returns 2 skills on the CLI and 3 via MCP.
  `check_cli_mcp_parity.py` passes 154/154 because no held-out query contains
  either character. Documented in `docs/architecture.md`; the fix deserves its
  own change with a full fixture and held-out re-run.
- **No PyPI publish.** `PYPI_API_TOKEN` is not configured, so `publish-pypi`
  fails on tag push. The GitHub Release still publishes.
- The scheduled `org-validation` workflow has failed since 2026-08-10 with
  `INVALID_SFDX_AUTH_URL`; the org credential secret is absent.


### Retracted

- **The "79.2% → 92.2% Hit@1" routing result published on 2026-08-14 does not
  hold and is withdrawn.** Re-scoring both committed runs against a single
  label set inverts the direction: 98.5% → 92.5% excluding the 20 relabelled
  queries, with 10 regressions and 0 improvements. Two causes. First the
  comparison was circular — 41 of the baseline's 43 miss rows had `expected`
  rewritten to whatever the *baseline itself* picked, so the after-run was
  scored against labels derived from its predecessor's behaviour. Second,
  exact-match scoring charges the router for the corpus's own near-duplicate
  pairs; 8 of the 10 "regressions" are pairs where the other package is
  defensible (`mfa-enforcement-strategy` vs `mfa-enforcement-patterns`,
  `data-archival-strategies` vs `service-data-archival`).
  **Router accuracy 88.3% → 96.1% stands** — it is label-independent.
  Full analysis and the rule it establishes ("never score a corpus change
  against labels derived from a run of that same corpus") are in
  `evals/measurement/README-model-routing.md`.

### Fixed — corpus currency

- API 67.0 sweep: every remaining `WITH SECURITY_ENFORCED` reference now
  carries the removal qualifier. `apex/apex-soql-relationship-queries` was
  *recommending* the removed clause; `devops/code-review-checklist-salesforce`
  and `architect/well-architected-review` listed it as an accepted enforcement
  idiom for reviewers.
- `skills/apex/visualforce-fundamentals/scripts/` accepted
  `WITH SECURITY_ENFORCED` as satisfying FLS enforcement, so a query carrying a
  removed clause scored clean — contradicting the agent contract's rule that a
  scanner flags it rather than passing it. Fixed additively, preserving
  sub-67.0 behaviour.
- Documented the API 65.0 rule that abstract/override methods require an
  explicit access modifier, in `templates/apex/README.md`,
  `apex/trigger-framework` and `apex/fflib-enterprise-patterns`.
  `templates/apex/` itself audited clean — all pinned to 67.0 with explicit
  modifiers.
- Two blog-sourced "breaking changes" were **investigated and rejected**: the
  claimed 67.0 no-argument-constructor requirement for invocable-action input
  types, and the claimed LWS block on `data:` URIs in anchor `href`. Neither
  appears on any primary Salesforce documentation page.

### Fixed — descriptions and routing

- 25 packages had `description:` frontmatter truncated mid-word by the
  2026-08-14 wave (`(use the security secure-coding chec — use …`). The damage
  was in the SKILL.md source, so it reached the registry, the rosters, FTS5 and
  the plugin simultaneously.

### Fixed — documentation

- `docs/architecture.md` documented the FTS5 retrieval pipeline in full and
  never described the mechanism that actually ships. Restructured so the
  model-driven roster scan comes first, with the retrieval pipeline reframed as
  mechanisms 2 and 3, both of which require a local `build_index.py` run.
- `README.md` and `docs/installing-the-plugin.md` both stated the GitHub plugin
  install was blocked because `.claude-plugin/` was not on the default branch.
  It is — along with the 12 router skills, 66 commands and 48 agents.
- Corrected: 4 decision trees → 7; 66 slash commands → 67; the embeddings
  story (configured on, but inert until `fastembed` is installed, since it is
  commented out of `requirements.txt`); and the claim that golden evals do not
  gate CI, which has been false since the eval structure lint landed.
- `config/retrieval-config.yaml` held-out figures re-measured: 36.4/44.2 →
  37.0/48.7 (2026-08-13) became 39.6/48.1 → 40.9/53.9 (2026-08-14). The
  difference is corpus change, not relabelling — Hit@1 is identical against
  either label set.

### Fixed — tooling

- `scripts/skill_doctor.py` silently accepted a path argument and reported an
  existing package as missing, telling the caller to scaffold it. Now
  normalises `domain/slug`, `skills/domain/slug` and absolute paths, and fails
  loudly with a suggestion on a genuinely unknown id.
- `evals/measurement/run_model_routing.py` defaulted its `--results` path into
  a session-scratch directory and could not read the envelope the benchmark
  writes.
- Both shipped workflow scripts hardcoded an absolute developer home directory.
- `.claude/workflows/add-skill.js` restated the Apex security idiom from memory
  — the exact practice `AGENT_CONTRACT.md` rule 10 forbids — and restated it
  incorrectly. Replaced with a pointer to the canonical table plus the three
  verbatim 67.0 quotations.

## [0.4.6] — 2026-06-17 — sfskills-mcp (count reconciliation + upstream merge)

- Reconciled agent, skill and MCP tool counts across the docs and added a drift
  lint (`scripts/check_doc_counts.py`) so they cannot silently diverge again.
  Corrected in passing: runtime agents 47 → 56 → 48 as the roster settled, MCP
  tools 15 → 38, skill count 978 → 1,003.
- Merged the `upstream-learnings-2026-06-15` line: clean-room radar tooling for
  the upstream `sf-skills` repository, plus the skills it verified as genuine
  gaps.
- Standardised `apiVersion` to 67.0 (Summer '26) across `templates/`.
- De-stubbed 5 skills (apex / lwc / devops) to full content.
- Two gap-analysis runs (2026-05-18, 2026-05-26) each found 0 verified gaps,
  establishing that the catalog is saturated and that depth, not breadth, is
  the remaining work.

Version 0.4.5 was reserved for a hotfix that was never needed and never shipped.

## [0.4.4] — 2026-05-10 — sfskills-mcp (post pre-prod QA)

- `emit_envelope` enforces its schema, and the schemas use URN `$id`s; `run_id`
  now rejects `:`.
- Graceful fallback when `fastembed` is not installed, rather than an import
  error.
- `tooling_query` skips the automatic `LIMIT` on non-grouped aggregates;
  `list_custom_fields` drops an unsupported SOQL `ESCAPE` clause.
- Removed agent citations to a skill that did not exist
  (`data-cloud-reverse-etl-to-core-salesforce`), and aligned slash-command
  names in agent prompts with the actual command filenames.
- Retired a stale "950+" corpus-size fallback in the server instructions.

## [0.4.3] — 2026-05-10 — sfskills-mcp (production hardening)

10 fixes surfaced by live-org integration testing against an Education
Cloud sandbox (4,000+ ApexClass, 30,000+ CustomField, 694 Flow, 1,209 LWC).
The single biggest takeaway: **3 of the 4 heavy probes had never been
tested against a real org** — each failed on its first SOQL invocation
with a Salesforce-platform-level rejection. This release fixes them.

### Migration

Users on v0.4.2:
- **`tooling_query` default flipped**: `tooling=False` now (was `True`).
  Most ad-hoc queries target Standard sObjects (Account, Contact, etc.).
  Tooling-API-only entities (`ApexClass.Body`, `Flow.Metadata`,
  `MetadataContainer`, etc.) need explicit `tooling=True`.
- **3 probes that silently returned errors now work**. If you had
  scripts that handled `error` keys from `probe_apex_references`,
  `probe_flow_references`, or `probe_matching_rules`, they'll now
  receive populated `references` / `matching_rules` / `duplicate_rules`
  lists. Update consumers to handle the success shape.
- **`suggest_agent` returns fewer decision trees**. The new
  `min_tree_score` parameter (default 20) suppresses low-relevance
  trees. To recover v0.4.2 behavior pass `min_tree_score=0`.
- **`describe_org` adds `is_sandbox_source`** field ("cli" | "inferred-
  from-url" | absent). Existing consumers that only read `is_sandbox`
  see no breakage; consumers that want to know provenance can opt in.

### Security

- **Universal credential redactor in `sf_cli.py`.** Live test session
  leaked a Salesforce session token because `sf org display --json`
  prepended a CLI warning line, `json.loads` failed, and the error
  path returned raw stdout — which contained the access token. Added
  `_redact_credentials_text` (regex scrub for SF session, OAuth
  refresh, and Bearer patterns) and `_redact_credentials_in_payload`
  (walks parsed JSON, redacts values keyed by `accessToken`,
  `refreshToken`, `password`, `clientSecret`, `securityToken`,
  `sessionId`, `apiToken`, `authToken`). Applied to every output path
  in `run_sf_json` (TimeoutExpired stderr, JSONDecodeError stdout +
  stderr, normal payload return). 15 new unit tests cover token
  shapes, JSON-walker, and the exact live-leak failure pattern.

### Fixed

- **`probe_apex_references`** (broken since v0.4.0): Salesforce's
  Tooling API rejects `WHERE Body LIKE '%X%'` on ApexClass /
  ApexTrigger. Removed the unfilterable predicate; client-side
  word-boundary regex on fetched bodies still scopes results
  precisely. Default `limit_per_query` raised 200→2000 (Tooling API
  max) so the probe finds references in the full custom-Apex set in
  one round trip on typical orgs.
- **`probe_flow_references`** (broken since v0.4.0): When SOQL selects
  `Flow.Metadata`, Tooling API requires exactly one row in the
  response. Two-pass implementation: list Flow IDs in one bulk query,
  then fan out per-ID Metadata queries through an 8-thread pool.
- **`probe_matching_rules`** (broken since v0.4.0): four distinct
  schema errors fixed in one pass:
  1. `MatchingRule.IsActive` → `RuleStatus` (the boolean column was
     replaced with a richer picklist: Active, Activating, Deactivating,
     Inactive, ActivationFailed, RebuildIndex).
  2. `MatchingRuleItem.FieldName` → `Field` (column name typo).
  3. `MatchingRuleItem` and `DuplicateRule` queries now route through
     the Standard SOQL API (`tooling=False`); the Tooling API doesn't
     expose them.
  4. `DuplicateRule.ParentId` removed — that column has never existed.
- **`tooling_query` false positives**: substring matching on DML
  keywords blocked legitimate queries where the keyword appeared in
  string literals: `WHERE Name = 'foo INSERT bar'`,
  `WHERE Name LIKE '%UPDATE %'`, `WHERE Name = ';'`. New
  `_strip_soql_string_literals` state machine strips quoted content
  before the DML scan. All 5 stacked-DML bypass attempts still
  blocked; 4 false-positive cases now pass.
- **`tooling_query` SELECT detection** rejected multi-line SOQL
  formatted with `SELECT\n  Id\nFROM ...`. Replaced
  `startswith("SELECT ")` with `re.match(r"^\s*SELECT\b")`.

### Changed

- **`tooling_query` default flipped to `tooling=False`**. Standard
  API is the common case for ad-hoc queries; Tooling API entities
  opt in with explicit `tooling=True`.
- **`suggest_agent` filters low-score decision trees**. The Phase 6
  audit showed 6 of 8 realistic queries returned an irrelevant tree
  (e.g. "security issues" → `async-selection`, score 10.7). New
  `min_tree_score` parameter (default 20) suppresses noise. 2/8
  correct → 8/8 correct on the same suite.
- **`describe_org` infers `is_sandbox` from instance URL** when sf
  CLI omits it. ExampleOrg Dev PN (URL
  `ExampleOrg--devSandbox.sandbox.my.salesforce.com`) returned
  `isSandbox=null` from the CLI; URL inference correctly classifies
  as sandbox. New `is_sandbox_source` field tags the provenance.
- **`run_sf_json` strips warning-prefix lines before parsing**.
  `_strip_to_json_start` finds the first `{` or `[` in stdout so
  `sf` CLI update-available banners no longer cause JSON-decode
  errors (the same root cause as the security leak above).

### Test infrastructure

- 5 new test files (`test_sf_cli_redaction.py`,
  `test_tooling_query_blocklist.py`, `test_sandbox_inference.py`, plus
  expansions in `test_admin.py`).
- 45 new unit tests, all pass.
- Full suite: 205/205 tests pass (was 160 at the start of v0.4.2).
- Every fix in this release was live-verified against ExampleOrg Dev PN
  (Education Cloud + NPSP + several AppExchange managed packages).

## [0.4.2] — 2026-05-09 — sfskills-mcp (retrieval quality)

Retrieval quality release. Three of the four MCP corpora (agents, templates,
decision-trees) had no measured Hit@1 baseline before this. A 247/195/34-query
NL audit revealed catastrophic numbers — 18.2% / 24.6% / 55.9% Hit@1 — and
this release lifts them to 95.1% / 88.7% / 82.4% via a slug-aware scorer
rewrite in `mcp/sfskills-mcp/src/sfskills_mcp/library.py`. Skills retrieval
gets chunk-level fastembed embeddings as a hybrid rerank signal (NL Hit@3
+1.8pp, curated 98.6% sacred floor unchanged). The pre-commit hook is
decoupled from the multi-hour embeddings rebuild so commits stay fast.

### Added

- **Slug-aware scoring** in `library.py`: whole-word match against the
  document's slug/path/basename earns a 15× boost (vs the previous
  scorer's substring counts that let long meta-documents — e.g.
  apex-builder.AGENT.md mentioning "apex" 200+ times — drown short-named
  target documents). Plus a light suffix stemmer (-er, -or, -ing,
  -ation, -ies, -y, -ed, -es, -s, -e) so "consolidate" matches
  "consolidator" and "build" matches "builder". Plus slug coverage bonus
  (+20 × matched/total tokens) and bigram bonus (+8 per adjacent pair).
  Body weight changed from 1.0 substring to `0.6 × sqrt(count)` so
  documents that mention a term 100× contribute 6× not 100×.
- **`scripts/build_skill_embeddings.py`** — encodes one fastembed vector
  per skill (~994 vectors, ~88 sec on M-series CPU). Lightweight
  alternative to chunk-level embeddings when the 2-hour full encode
  isn't worth it. `vector_index/skill_embeddings.jsonl` is gitignored.
- **`evals/measurement/nl_query_generator_corpora.py`** + **`retrieval_eval_corpora.py`**
  + **`run_realistic_smoke.py`** + **`realistic_queries.json`** —
  reusable audit harness for the secondary corpora plus a 71-query
  hand-crafted realistic-user smoke test.
- **`evals/measurement/improvement_loop.py`** — automated
  measure → near-miss → trigger-fix-wave → re-measure runner. Stops on
  plateau (<min_lift over 2 iters) or curated regression below floor.
- **Build progress reporting** in `pipelines/embedding_backends.py`:
  emits cached/to-encode counts at start, then ~50 progress lines with
  chunks/sec rate and ETA. Suppress with `FASTEMBED_PROGRESS=0`.
- **`--skip-embeddings`** flag on `scripts/skill_sync.py`: bypass the
  embeddings encode for fast commits. Pre-commit hook now uses it.

### Changed

- **`config/retrieval-config.yaml`**: `embeddings.enabled` flipped to
  `true` by default. Backend `fastembed` (BAAI/bge-small-en-v1.5,
  384-dim, MIT, ONNX-q on CPU). Vector weight 0.2 in
  `pipelines/ranking.rerank_results()` — measured sweet spot between
  curated regression at 0.35 and no-op at 0.10.
- **`pipelines/ranking.rerank_results()`**: now takes optional
  `skill_embeddings` kwarg. Lookup order is skill-level first (by
  `skill_id`), then chunk-level (by `chunk_id`). Pure lexical when
  neither index is present (backwards compatible).
- **`pipelines/embedding_backends.write_embeddings()`**: stream per-line
  instead of building one large in-memory string before writing.
  Eliminates ~2GB peak RAM during the 126K-chunk encode that triggered
  OOMs on machines with <12GB free.
- **`scripts/skill_sync.py --changed-only`**: validation now scopes to
  STAGED skills only (was: validated every skill on disk). Pre-existing
  ERRORs in unrelated skills no longer block infra/eval/doc commits.
  Full-repo gate is preserved via `validate_repo.py` and
  `skill_sync.py --all`.
- **`scripts/validate_repo.py`**: `_git_changed_files()` returns staged
  paths when anything is staged (the pre-commit hook's natural scope).
  Falls back to staged + unstaged + untracked only when nothing is
  staged. Plus `build_state(skip_embeddings=True)` for the registry
  validation step — no need to re-encode 126K chunks just to validate
  metadata.
- **`.githooks/pre-commit`**: now invokes
  `skill_sync.py --changed-only --skip-embeddings`. Embeddings are
  rebuilt only by the explicit `python3 scripts/build_index.py`
  invocation, never as a side effect of committing.

### Performance

Measured on 2026-05-09 across three audits. All gates passed.

| Audit                                  | Lexical-only Hit@1 / Hit@3 | This release Hit@1 / Hit@3 |
| -------------------------------------- | -------------------------: | -------------------------: |
| Curated 1,285-Q (sacred floor ≥98%)    |             98.6% / 100.0% |             98.6% / 100.0% |
| Synthetic NL 1,418-Q                   |              74.3% / 86.0% |              74.5% / 87.8% |
| Realistic smoke 71-Q                   |              78.9% / 94.4% |              78.9% / 94.4% |
| Agents NL 247-Q                        |              18.2% / 36.4% |              95.1% / 98.0% |
| Templates NL 195-Q                     |             24.6% / 61.0%  |             88.7% / 100.0% |
| Decision-trees NL 34-Q                 |              55.9% / 85.3% |              82.4% / 97.1% |

Per-query latency (fastembed cold start ~14s once per process; per-query
encode ~30ms after warm-up).

## [0.4.1] — 2026-05-08 — sfskills-mcp (hygiene patch)

Patch release rebuilding the data bundle attached to the GitHub Release
without hardcoded `/Users/<author>/` paths. Wheel itself is unchanged
in behaviour — only drops 2 unused imports. `sfskills-mcp-init` (which
fetches `releases/latest`) auto-picks up the cleaned data bundle.

### Changed

- `commands/audit-router.md`, `commands/automation-migration-router.md`,
  `commands/run-queue.md`, `docs/MIGRATION.md`,
  `docs/archive/OPUS_RESEARCH_PROMPT.md`,
  `agents/_shared/harnesses/migration_router/decision_table.md`,
  `feedback/FEEDBACK_LOG.md`: replaced absolute `/Users/<author>/` paths
  with relative references, `$(git rev-parse --show-toplevel)`, or
  generic phrasing. The `/run-queue` prompt's body had `cd /Users/...`
  snippets that wouldn't run on any other contributor's machine — fixed.
- `mcp/sfskills-mcp/src/sfskills_mcp/init.py`: drop unused `tempfile`.
- `mcp/sfskills-mcp/src/sfskills_mcp/resources.py`: drop unused `Any`.

### Fixed

- `agents/duplicate-rule-designer/AGENT.md`: rephrased the Dimensions
  section so it's no longer byte-identical to `data-loader-pre-flight`'s
  (the agent validator's "duplicate prose between AGENT.md files" rule
  was rejecting both files until one of them was paraphrased).

## [0.4.0] — 2026-05-08 — sfskills-mcp (Tier A → D)

A focused 4-tier evolution of `mcp/sfskills-mcp/` from the v0.1 prototype to a v0.4 production-ready MCP server. Plan + per-tier audit history live in [`.planning/mcp-v0.2-plan.md`](./.planning/mcp-v0.2-plan.md).

### Added

- **Tier C tools (14 new):** `list_apex_classes`, `get_apex_class`, `list_apex_triggers`, `list_lwc_bundles`, `get_lwc_bundle`, `list_custom_fields` (with `include_pseudo_fields`), `describe_object_full` (composite), `list_orgs`, `search_agents`, `search_templates`, `search_decision_trees`, `get_template`, `get_decision_tree`, `suggest_agent` (free-text task → ranked agents).
- **Tier D tools:** `health` diagnostic (server / SDK / sf-CLI versions, registry size, agent counts), `SFSKILLS_TIMEOUT_SECONDS` env var for deployer-wide subprocess timeout overrides.
- **MCP Prompts:** every wrapper in `commands/*.md` registers as an MCP prompt — 68 native slash commands (`/refactor-apex`, `/audit-router`, `/build-apex`, …) for Cursor / Cline / Claude Desktop / etc.
- **MCP Resources:** 5 shapes — `sfskills://catalog`, `sfskills://skill/{id}`, `sfskills://agent/{name}`, `sfskills://decision-tree/{name}`, `sfskills://template/{path}`. Use the `domain__name` form for IDs that contain slashes.
- **Tool annotations:** every tool registers with `mcp.types.ToolAnnotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) so MCP-aware clients can auto-approve safely.
- **Probe progress notifications:** the four heavy probes (`probe_apex_references`, `probe_flow_references`, `probe_matching_rules`, `probe_automation_graph`) emit `notifications/progress` at start + completion.
- **PyPI publish path:** new `sfskills-mcp-init` console script downloads the registry + lexical index from a GitHub Release into `~/.cache/sfskills-mcp/`. End-user install becomes `pip install sfskills-mcp` + `sfskills-mcp-init`. Workflow: `.github/workflows/publish-mcp.yml`.

### Changed

- **Tier A drift fix:** `_RUNTIME_AGENTS` frozenset (37 hand-coded names) replaced with frontmatter-driven resolution from `agents/<name>/AGENT.md` (`class: runtime` + `status:` headers). Active runtime count now resolves at runtime — no more hand-edit required when adding an agent. Skill / agent counts in `SERVER_INSTRUCTIONS` and tool descriptions are loaded from `registry/skills.json` at server build time.
- **Tier B annotations:** SDK floor bumped from `mcp>=1.2.0` to `mcp>=1.4.0` (annotations stable since 1.4).
- **Tier B probes:** the four heavy probes are wrapped in async tool functions in `server.py`; `probes.py` itself stays sync to keep the test-stubbing pattern intact.
- **Shared SOQL helpers** (`_run_soql`, `_validate_api_name`, `_strip_attributes`) lifted from `admin.py` to `_shared.py`. `admin.py` re-exports for backwards compatibility.
- **Drift-prevention test** (`tests/test_meta_freshness.py`) now scans `src/` for 7 stale literals (`686+`, `_RUNTIME_AGENTS`, `twenty-three tools`, `six tools`, `56 total`, `56 run-time`, `56 runtime`) — anything that drifted before fails CI if it reappears.

### Test count

Before Tier A: 65 pass / 2 fail. After Tier D: **177 pass / 0 fail**.

## [Library] — 2026-04 — Full 8-Wave Redesign

A substantial redesign completed in April 2026, landing all 8 waves of the approved plan at `an internal redesign plan (kept locally)`. This section documents Waves 4b, 4c, 5, 6, 7 added on top of the earlier Wave 3 + 4a work (originally in commits `8bcabde` through `f7de019`).

### Added in Waves 4b + 4c + 5 + 6 + 7

- **3 new Agentforce skills** (Wave 4c): `agentforce-multi-turn-patterns`, `agentforce-tool-use-patterns`, `agentforce-eval-harness`. Each 250+ lines with full 4 reference files.
- **8 new Flow skills** (Wave 4b + extension): `flow-transactional-boundaries`, `flow-platform-events-integration`, `flow-invocable-from-apex`, `flow-rollback-patterns`, `flow-error-monitoring`, `flow-migration-from-trigger`, `flow-governor-limits-deep-dive`, `flow-performance-optimization`.
- **2 new decision trees** (Waves 4b + 4c):
  - `standards/decision-trees/flow-pattern-selector.md` — Before-Save / After-Save / Scheduled / Screen / Orchestration / Platform-Event-triggered routing.
  - `standards/decision-trees/agentforce-capability-selector.md` — Agentforce / Copilot / Prompt Builder / Next Best Action / Einstein Discovery / BYOLLM / Bots routing.
- **2 new templates**:
  - `templates/flow/PlatformEvent_Publisher_Flow.md` (Wave 4b).
  - `templates/agentforce/AgentEval_Fixture.md` (Wave 4c).
- **11 new slash commands** (Wave 5): `/build-apex`, `/design-assignment-rules`, `/configure-business-hours`, `/build-changeset`, `/design-custom-metadata`, `/design-entitlements`, `/design-experience-cloud`, `/design-flow-orchestrator`, `/build-lwc`, `/design-path`, `/migrate-profile-to-permset`. Every runtime agent now has a slash-command entry point.
- **Slash-command coverage validator rule** (Wave 5): `pipelines/agent_validators.py` fails when any `class: runtime, status != deprecated` agent lacks a matching `commands/*.md` linking its `AGENT.md`.
- **macOS CI matrix** (Wave 6): `.github/workflows/validate.yml` runs `validate-agents` and new `export-parity-matrix` jobs on both `ubuntu-latest` and `macos-latest` to catch cross-OS hash drift.
- **pr-lint hardened** (Wave 6): `build_index.py` runs before `export_skills.py --check` so the gitignored `lexical.sqlite` doesn't trip drift detection.
- **Open-source readiness docs** (Wave 7): `LICENSE` (Apache 2.0), `SECURITY.md`, `docs/MIGRATION.md` (deprecated-agent removal timeline), `docs/multi-ai-parity.md` (first-class vs second-class tier contract).

### Changed in Waves 4b+

- **`vector_index/chunks.jsonl` gitignored** — grew to ~98 MB at 700+ skills, crossing GitHub's 50 MB warning threshold. CI and local workflows rebuild via `python3 scripts/build_index.py`. `vector_index/manifest.json` stays committed as the drift-detection hash.
- **`scripts/export_skills.py` → 6 platforms** (Wave 2): `claude`, `cursor`, `mcp` first-class; `windsurf`, `aider`, `augment` second-class with documented subset contract.
- **701 skills total** (was 686 pre-redesign) — net of deletions + new additions. Breakdown:
  - +11 new Agentforce/Flow skills authored (Waves 4b + 4c).
  - +16 Flow + 3 Agentforce skills rewritten from shallow to deep (Wave 4a).
  - –8 TODO-stub skills removed.

## [Earlier] — Wave 3 + Wave 4a Redesign

Original wave 0–4a work in commits `8bcabde` through `f7de019`.

### Added

- **`automation-migration-router`** (Wave 3a) — replaces 4 retired migrators with one router dispatching on `source_type` (`wf_rule` / `process_builder` / `approval_process` / `auto`). See [MIGRATION.md](docs/MIGRATION.md).
- **`audit-router`** (Waves 3b-1 + 3b-2) — replaces 15 retired auditors with one router dispatching on `--domain` across 15 classifiers. Each finding carries a stable domain-scoped code (`VR_*`, `PICKLIST_*`, `APPROVAL_*`, etc.) for cross-run rollup.
- **`designer_base` harness** (Wave 3c) — shared conventions doc (mode contract, output shape, inventory probes, refusal patterns) for 8 existing designer agents. Agents now declare `harness: designer_base` in frontmatter.
- **4 probes promoted to first-class MCP tools** (Wave 2): `probe_apex_references`, `probe_flow_references`, `probe_matching_rules`, `probe_permset_shape`. Centralizes SOQL + post-processing across agents.
- **`claude` and `mcp` first-class export targets** (Wave 2) in `scripts/export_skills.py`, alongside existing `cursor` / `aider` / `windsurf` / `augment`.
- **`registry/export_manifest.json`** (Wave 2) — per-target content hashes + per-skill hashes. CI diffs against this baseline to detect export drift.
- **`scripts/export_skills.py --target`, `--manifest`, `--check` flags** (Wave 2).
- **`scripts/export_skills.py --check`** — non-destructive parity check against committed manifest.
- **Sharded validator** (Wave 1): `scripts/validate_repo.py --changed-only`, `--shard N/M`, `--domain <name>`, `--skip-drift`, `--skip-fixture-retrieval`. Full-repo validation time reduced from ~16 minutes to ~40 seconds across 4 CI shards.
- **In-process fixture validation** (Wave 1) — `scripts/search_knowledge.py` exposes `build_search_context()` + `run_search()` as a library API. Fixture validation loads the lexical index once instead of 744 subprocess spawns.
- **`scripts/validate_repo_bench.py`** (Wave 1) — 500-synthetic-skill benchmark. Asserts wall-clock < 30s; catches orchestration regressions.
- **GitHub Actions workflows** (Wave 1): `.github/workflows/validate.yml` (4-shard matrix + agents + bench), `.github/workflows/pr-lint.yml` (schema round-trip + export-manifest check).
- **`mcp/sfskills-mcp/tests/test_agent_frontmatter.py`** (Wave 0) — round-trip test: every `AGENT.md` frontmatter validates against the tightened schema.
- **`mcp/sfskills-mcp/tests/test_tools.py`** (Wave 2 follow-on) — 19 MCP tools registered + input validation for SOQL-injection vectors.
- **`mcp/sfskills-mcp/tests/test_export_parity.py`** (Wave 2) — 3-run determinism + first-class parity (Claude/Cursor/MCP share skill-id set).
- **Process Observations blocks** on 4 observational runtime agents (Wave 0): `deployment-risk-scorer`, `lwc-auditor`, `soql-optimizer`, `flow-analyzer`.

### Changed

- **`agent-frontmatter.schema.json`** (Wave 0): `modes` tightened from loose regex to enum (`[single, design, audit, analyze, plan, migrate, review, build, validate]`) with `uniqueItems: true`. New optional `harness` field added in Wave 3c.
- **`pipelines/frontmatter.py::stable_hash_for_files`** (Wave 1.1 hotfix): now accepts a `root` parameter and computes hashes against POSIX paths relative to the root. Prior absolute-path hashing caused macOS-vs-Linux CI drift on every contributor PR.
- **`.githooks/pre-commit`** (Wave 1): uses `validate_repo.py --changed-only` for < 5s pre-commit on single-file changes.
- **`pipelines/agent_validators.py`** (Wave 3a + 3c):
  - Deprecated agents now require only `Plan` + `What This Agent Does NOT Do` sections (not full 8-section runtime shape).
  - `harness: designer_base` declaration triggers mode-enum enforcement + required `Escalation / Refusal Rules` section.
- **16 Flow skills rewritten** (Wave 4a-1) with 2-3x depth: `fault-handling`, `flow-bulkification`, `record-triggered-flow-patterns`, `orchestration-flows`, `scheduled-flows`, `screen-flows`, `subflows-and-reusability`, `flow-testing`, `flow-runtime-error-diagnosis`, `flow-action-framework`, `flow-collection-processing`, `flow-custom-property-editors`, `flow-email-and-notifications`, `flow-for-experience-cloud`, `flow-governance`, `flow-large-data-volume-patterns`.
- **3 Agentforce skills rewritten** (Wave 4a-2) with 2x depth: `agent-actions`, `agent-topic-design`, `agentforce-persona-design`.
- **`agents/_shared/SKILL_MAP.md`** updated to reflect router consolidations and designer harness inheritance.

### Deprecated

Full list and removal timeline in [`docs/MIGRATION.md`](docs/MIGRATION.md). Stubs + aliases ship for two minor versions.

- 4 automation migrators (Wave 3a): `workflow-rule-to-flow-migrator`, `process-builder-to-flow-migrator`, `approval-to-flow-orchestrator-migrator`, `workflow-and-pb-migrator`.
- 15 auditors (Wave 3b): `validation-rule-auditor`, `picklist-governor`, `approval-process-auditor`, `record-type-and-layout-auditor`, `report-and-dashboard-auditor`, `case-escalation-auditor`, `lightning-record-page-auditor`, `list-view-and-search-layout-auditor`, `quick-action-and-global-action-auditor` (audit mode), `reports-and-dashboards-folder-sharing-auditor`, `field-audit-trail-and-history-tracking-governor`, `sharing-audit-agent`, `org-drift-detector`, `my-domain-and-session-security-auditor`, `prompt-library-governor`.

### Removed

- **8 TODO-stub skills** (Wave 1.1 + 4a-2 cleanup): `data/industries-data-model`, `admin/omnistudio-vs-standard-decision`, `flow/process-builder-to-flow-migration`, `flow/workflow-rule-to-flow-migration`, `agentforce/agentforce-in-slack`, `integration/slack-connect-patterns`, `security/security-incident-response`, `data/data-loader-and-tools`. All had 38+ unfilled `TODO:` markers and no runtime-agent citations.

### Fixed

- **8 frontmatter `modes` typos** (Wave 0): 7 agents had `[n, audit]` instead of `[design, audit]`; `csv-to-object-mapper` had `[s]` instead of `[single]`. Tightened schema enum prevents recurrence.
- **21 broken agent citations** (Wave 1.1 hotfix): `list-view-and-search-layout-auditor`, `path-designer`, `quick-action-and-global-action-auditor`, `reports-and-dashboards-folder-sharing-auditor`, `devops-skill-builder`, `security-skill-builder` cited skills that didn't resolve; fixed to point at real skill paths.
- **12 missing query fixtures** (Wave 1.1 hotfix) for skills that had no fixture entry in `vector_index/query-fixtures.json`.
- **Invalid well-architected pillars** in `architect/npsp-vs-nonprofit-cloud-decision` (`Adaptability` / `Trustworthiness` → `Scalability` / `Reliability`).
- **Stale `registry/skills/*.json`** after TODO-stub removal (Wave 1.1 hotfix).
- **CI `lexical.sqlite` drift** (Wave 1.1 hotfix): added `scripts/build_index.py` step to CI to rebuild the gitignored index before drift check.

### Security

- **SECURITY.md** added (Wave 7) with disclosure process + contributor security checklist.
- **Probe input validation**: 4 promoted probes enforce API-name regex (`^[A-Za-z][A-Za-z0-9_]*$`) before constructing SOQL. Rejects injection vectors (`Account; DROP`, `Account OR 1=1`, etc.).
- **MCP tool tests** cover SOQL-injection vector rejection on `probe_apex_references`.

### Documentation

- **`docs/MIGRATION.md`** — every deprecated agent + replacement + removal timeline.
- **`LICENSE`** — Apache 2.0.
- **`SECURITY.md`** — disclosure policy + contributor security checklist.
- **`CHANGELOG.md`** — this file.
- **Auto-regenerated**: `docs/SKILLS.md`, `registry/skills.json`, `registry/knowledge-map.json`, `vector_index/chunks.jsonl`, `vector_index/manifest.json`.

## Pre-redesign history

The redesign documented above began from commit `1c65571` ("Wave D: wire the full 39-agent roster into docs + MCP registry", 16 April 2026). Pre-redesign changes are in git history; this changelog begins tracking with the redesign.

The full as-built agent roster prior to redesign is documented in the Waves 0–D commit log. The redesign preserves every rule but consolidates the agent surface into routers + shared harnesses per `an internal redesign plan (kept locally)`.
