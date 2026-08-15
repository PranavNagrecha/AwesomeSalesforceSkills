# How SfSkills Compares

An honest read of the landscape, including the places where a reader should
pick something else.

**How to read the numbers on this page.** Every in-repo figure came from a
command run on **2026-08-15**, and the command is printed next to it so you can
re-run it. Every external fact carries a URL and was re-checked the same day.
Nothing here is quoted from memory. Where a claim about another project could
not be checked against something public, it has been cut rather than softened.

---

## The alternatives

### forcedotcom/sf-skills — Salesforce's own curated Agent Skills library

<https://github.com/forcedotcom/sf-skills>. Apache-2.0, **827 stars, 293
forks**, last pushed 2026-08-14. It holds **138 skill directories**.

```bash
gh api repos/forcedotcom/sf-skills \
  --jq '{license:.license.spdx_id,stars:.stargazers_count,forks:.forks_count,pushed:.pushed_at}'
# -> {"license":"Apache-2.0","stars":827,"forks":293,"pushed":"2026-08-14T21:58:17Z"}

gh api repos/forcedotcom/sf-skills/contents/skills \
  --jq '[.[]|select(.type=="dir")]|length'
# -> 138
```

Its README states that the library "is optimized for Agentforce Vibes and can
be used with any AI tool that supports skills", that in Agentforce Vibes
"skills are auto-installed and auto-updated", and that everywhere else the
install line is `npx skills add forcedotcom/sf-skills`. It also carries its own
stability warning, verbatim: skills "may be renamed, restructured, or removed
between releases — they do not follow the same stability guarantees as GA
platform APIs."

Skill packages there may carry `scripts/`, `references/` and `assets/`
subdirectories. Two of the 138 ship a reference file specifically about
anti-patterns:

```bash
gh api "repos/forcedotcom/sf-skills/git/trees/main?recursive=1" \
  --jq '.tree[]|select(.type=="blob")|.path' | grep -E "^skills/.*anti-patterns\.md$"
# -> skills/experience-lwc-generate/references/template-anti-patterns.md
# -> skills/platform-soql-query/references/anti-patterns.md
```

(Match on `anti-patterns\.md$`, not on `anti` — "semantic" contains the
substring and a loose grep returns four unrelated styling-hook files.)

One thing worth knowing before you file this as "skills only": the repo also
ships a packaged Claude plugin. `.claude-plugin/marketplace.json` lists a single
plugin, `salesforce-development`, sourced from
`plugins/builder/salesforce-development/`, whose `.mcp.json` declares three
stdio MCP servers — `salesforce-api-context`, `salesforce-metadata-experts` and
`salesforce-lsp` — wired through a bundled Node proxy. So it is a skills library
*and* a tool surface, not just the former.

That is the whole of what can be checked from outside. This page makes no claim
about the quality, depth, or sourcing of the content inside those packages.

### The official Salesforce DX MCP server, `@salesforce/mcp`

Package: <https://www.npmjs.com/package/@salesforce/mcp> — latest **0.30.15**,
Apache-2.0. Source: <https://github.com/salesforcecli/mcp>. Docs:
<https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_mcp.htm>.

```bash
curl -s https://registry.npmjs.org/@salesforce/mcp \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['dist-tags']['latest'], d['versions'][d['dist-tags']['latest']]['license'])"
# -> 0.30.15 Apache-2.0
```

Its README says "The DX MCP Server includes over 60 MCP tools" and organises
them into toolsets you enable selectively to keep the context window small.
This is first-party org access, and it is not read-only: the tool tree includes
`deploy_metadata`, `create_scratch_org`, `delete_org` and
`assign_permission_set` alongside the read paths. It is a tool surface, not a
knowledge layer — it will run your query; it does not tell you the query is
non-selective.

### The Agent Skills open format itself

Spec at <https://agentskills.io/specification>. The format is a distribution
channel, not a competitor — SfSkills, `forcedotcom/sf-skills` and everything
else in the ecosystem all publish into it.

What is worth knowing is how low the format's own bar is, because that decides
how much a "Salesforce skill" published in it tells you. The spec's frontmatter
table marks exactly two fields Required — `name` (max 64 chars) and
`description` (max 1024 chars, non-empty) — and everything else, including
`license`, optional. There is no sourcing, depth, or review requirement in the
format. Whether any given skill is trustworthy is entirely on its author, and
you have to open it to find out.

### No library at all — the raw model

The honest baseline, and the one this repo has **not** measured. There is no
controlled comparison in this repository between a model with the library and
the same model without it. What exists instead is a per-topic catalogue of the
wrong output — 1,027 `references/llm-anti-patterns.md` files, each naming
concrete generations the skill exists to prevent — which documents the
hypothesis rather than testing it. Read that as a design record, not evidence.

---

## Side by side

Checkable properties only. Blank cells are where nothing public could be
verified.

| | Breadth | Package shape | Live-org access | What gates a merge | License |
|---|---|---|---|---|---|
| **SfSkills** | 1,027 skills across 11 domains | Every package: `SKILL.md` + `references/{examples,gotchas,well-architected,llm-anti-patterns}.md` + a non-empty `templates/` + a `scripts/` holding at least one Python file, all ERROR gates | Yes — 38 MCP tools over the user's `sf` CLI session; every org-touching tool is read-only | On every PR to `main` and push to `main`: skill validator (4 shards, including the retrieval fixtures), agent validator (ubuntu + macos), export-parity, eval structure lint, full 248-test MCP suite | Apache-2.0 |
| **forcedotcom/sf-skills** | 138 skill directories at `skills/`, plus a bundled `salesforce-development` Claude plugin its own marketplace describes as "41 skills" | `SKILL.md` required; `scripts/`, `references/`, `assets/` optional | Yes, in the bundled plugin — its `.mcp.json` wires three stdio servers (`salesforce-api-context`, `salesforce-metadata-experts`, `salesforce-lsp`) | `.github/workflows/validate-skills.yml` runs `npm run validate:skills` (`scripts/validate-skills.ts`) on every PR, changed-skills-only when `skills/` is touched; plus a conventional-commit PR-title gate | Apache-2.0 |
| **`@salesforce/mcp`** | "over 60 MCP tools", per its README | n/a — executes, does not advise | Yes, first-party; read **and** write (`deploy_metadata`, `create_scratch_org`, `delete_org`) | 14 workflows in `salesforcecli/mcp/.github/workflows/`, including unit tests on Linux and Windows, an `e2e` job, and a staged publish/promote release path | Apache-2.0 |
| **Any Agent Skill** | Unbounded | Spec requires only `name` + `description`; everything else optional | Only if the skill wraps a server | Whatever its author chose | Per-author |

The reasonable configuration for most teams is not either/or: `@salesforce/mcp`
for first-party org operations, plus a knowledge layer that tells the model what
*not* to write.

---

## Where SfSkills Is Weaker

These are the reasons to pick something else. All measured 2026-08-15.

### Nobody can find it

Nothing has been submitted to or accepted by any third-party plugin directory
(<https://code.claude.com/docs/en/plugin-marketplaces>), and the MCP registry
returns nothing:

```bash
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=sfskills"
# -> {"servers":[],"metadata":{"count":0}}
```

Installing works — that is not the gap. The repository is its own marketplace
and the manifests are on the default branch:

```bash
git ls-tree origin/main .claude-plugin/
# -> 100644 blob 1f3ebf0d…  .claude-plugin/marketplace.json
# -> 100644 blob fab6adae…  .claude-plugin/plugin.json
```

so `/plugin marketplace add PranavNagrecha/AwesomeSalesforceSkills` then
`/plugin install sfskills@sfskills` works today, with no Python and no index
build. `pip install` and `build_index.py` are needed only for the CLI and MCP
*search* surfaces, never to reach a skill. Discovery is the real gap:
`npx skills add forcedotcom/sf-skills` is still a shorter first line to type,
and it is a line strangers actually encounter.

### 13 stars

Public since 2026-06-17 with 13 stars and 3 forks. There is no community
signal, no third-party review, and no track record of responsiveness to issues.
Weigh that against 827 stars upstream.

```bash
gh api repos/PranavNagrecha/AwesomeSalesforceSkills \
  --jq '{stars:.stargazers_count,forks:.forks_count,created:.created_at}'
# -> {"stars":13,"forks":3,"created":"2026-06-17T17:22:18Z"}
```

### Not first-party

No auto-install and auto-update inside Agentforce Vibes, no pre-GA visibility
into unreleased platform behaviour, and no Salesforce release-train guarantee.
When Salesforce ships something in a seasonal release,
`forcedotcom/sf-skills` can be right on day one and this repo cannot.

### The claimed source-tier tagging does not exist in the content

`standards/skill-content-contract.md` requires an inline tier tag — `[T1]`,
`[T2]`, `[T3: source-name]` — on every factual claim, and states that "a claim
with no tag and no URL is a contract violation". Not one file in any skill
package carries such a tag:

```bash
python3 -c "
import pathlib,re
md=list(pathlib.Path('skills').glob('*/*/**/*.md'))
print(sum(1 for f in md if re.search(r'\[T[1234][\]:]', f.read_text())), 'of', len(md))"
# -> 0 of 6176
```

`validate_repo.py` does not check for it either, so nothing surfaced the drift.
What *is* real and enforced is one level coarser: every package carries a
non-empty `## Official Sources Used` block in
`references/well-architected.md`, guarded by two ERROR gates
(`pipelines/validators.py:351` and `:357`), holding 5,748 salesforce.com
documentation URLs in total. Twenty-six of those blocks name their sources in
prose with no URL at all, which the contract also forbids and no gate catches.
Treat "sourced" as "a named official source is listed per package", not "graded
per claim".

### Depth is uneven, and thinnest where it matters most

Measured by markdown bytes per package, **7 of 1,027** packages hold under
15 KB and **50** hold under 20 KB. Security is the thinnest domain — 4 of its 48
packages, the worst possible place for it — followed by Agentforce at 3 of 53.
Every other domain has none. A reader who needs Shield or event-monitoring depth
may still find a thin package.

```bash
python3 -c "
import pathlib
s=[sum(f.stat().st_size for f in d.rglob('*.md'))
   for d in (p.parent for p in pathlib.Path('skills').glob('*/*/SKILL.md'))]
print(sum(v < 15*1024 for v in s), 'of', len(s))"
# -> 7 of 1027
```

Two earlier revisions of this page reported wildly different figures (112/152
with security at 37%; then 12/55). Both predate a depth pass and both were
refuted by the command above. Re-run it rather than trusting the prose.

### OmniStudio is one agent deep

A single `omnistudio-designer` is the entire accelerator surface for OmniScript,
FlexCards, DataRaptors, Integration Procedures and the Business Rules Engine.
It is the only agent in the roster that cites an OmniStudio skill, and it
carries all 34 of them.

```bash
grep -rl "omnistudio/" agents/*/AGENT.md
# -> agents/omnistudio-designer/AGENT.md
grep -c "^    - omnistudio/" agents/omnistudio-designer/AGENT.md
# -> 34
```

Apex, LWC and architecture work is served by a sixteen-agent developer tier by
comparison (`agents/_shared/RUNTIME_VS_BUILD.md`, "Developer + architecture tier
(16)"). OmniStudio is the domain where this library is furthest from the depth
it claims elsewhere.

### Live-org validation has never produced a result

CI is stronger than this page used to claim — the retrieval-fixture gate and the
eval structure lint both run now (see
[the corrected record](#what-changed-since-the-last-revision) below). The hole
that remains is the live-org layer.

`org-validation.yml` is `workflow_dispatch` plus a Monday cron. It has fired
exactly once, on the schedule, and failed in all three layers at the same step —
`Authenticate to validation org` — because the `SFDX_AUTH_URL` secret is not
set:

```bash
gh run list --workflow=org-validation.yml --json conclusion,createdAt,event
# -> [{"conclusion":"failure","createdAt":"2026-08-10T08:50:33Z","event":"schedule"}]
```

So the live-org reports in `docs/validation/` are still the hand-run ones from
April 2026, and the workflow that was supposed to keep them fresh has produced
no result of any kind.

### Retrieval is the weakest layer, and only one of its three mechanisms is measured well

There are three ways to reach a skill, and they perform very differently. Do not
let a number measured on one be read as a claim about another.

| # | Mechanism | Setup needed | How it is measured |
|---|---|---|---|
| 1 | Roster scan — the model reads 12 router `description:` values, opens one `references/skill-index.md`, and picks | None. This is what a plugin install gets | `evals/measurement/run_model_routing.py` |
| 2 | MCP `search_skill` | `sfskills-mcp` installed **and** connected; not auto-wired | `check_cli_mcp_parity.py`, against mechanism 3 |
| 3 | FTS5 via `scripts/search_knowledge.py` | `pip install -r requirements.txt` + `python3 scripts/build_index.py`, because `vector_index/` is gitignored and never ships | `evals/measurement/run_heldout.py` |

**On mechanism 3**, the query fixtures in `vector_index/query-fixtures.json` are
close paraphrases of the `triggers:` keywords in each skill's own frontmatter —
and `pipelines/sync_engine.py` appends those same keywords to the skill's
indexed text. Scoring against them measures recall of indexed vocabulary, not
recall of a practitioner's phrasing, so fixture scores are an upper bound. The
hand-written held-out set is the honest counterpart, and it is much harder:

```bash
python3 evals/measurement/run_heldout.py
# Held-out benchmark: evals/measurement/heldout-queries.json
#   Hit@1       : 40.3%   Hit@3 : 53.9%   NONE rate : 0.0%

python3 evals/measurement/run_heldout.py \
    --queries vector_index/query-fixtures.json --use-domain
# Held-out benchmark: vector_index/query-fixtures.json
#   Hit@1       : 98.4%   Hit@3 : 100.0%  NONE rate : 0.0%
```

**98.4% against 40.3% on the same binary and the same index.** The second row is
the configuration `validate_repo.py` step 5 runs, and it is the number that
would flatter a README. The first row is the same stack asked a question nobody
indexed. Read `evals/measurement/README-heldout.md` before quoting either side
of that gap; it documents the scoring caveats, including that each query carries
exactly one accepted label, so a defensible alternative answer scores as a miss —
which makes 40.3% a floor rather than an estimate.

**On mechanism 1**, the one robust result from the 2026-08-14 routing wave is
**router accuracy 88.3% → 96.1%** — which of the 12 routers gets opened. That
metric is independent of the skill labels, which were rewritten mid-experiment.
The Hit@1 figures from that same wave are confounded and must not be quoted in
any form — re-scoring against a single label set inverts their direction, and
the headline improvement derived from them has been retracted.
`evals/measurement/README-model-routing.md` sets out both defects (circular
relabelling, and exact-match scoring that charges the router for the corpus's
own near-duplicate pairs). Read it before writing any number about routing
quality.

**Mechanisms 1 and 3 do agree** on one thing: when a query comes back empty,
open `docs/SKILLS.md` or the domain roster directly rather than concluding the
topic is uncovered.

### The clone is heavy, and pruning will not fix it

`.git` is 489 MB, of which 406.68 MiB is packfile.

```bash
du -sh .git                    # -> 489M
git count-objects -vH | grep size-pack   # -> size-pack: 406.68 MiB
```

The cause is history, not the current tree: the large retrieval artefacts
(`vector_index/chunks.jsonl`, `lexical.sqlite`, `embeddings.jsonl`) are
gitignored now, but 206 committed revisions of `chunks.jsonl` alone are already
in the pack. The `.gitignore` documents the measurement and the decision not to
rewrite history, which would invalidate every existing clone and fork. A shallow
clone helps; a plain `git clone` does not.

### The plugin cannot ship as a flat skill set

The 1,027 skill descriptions total **517,654 characters**, so loading the
catalogue as a flat skill list would consume most of a context window before the
user has asked anything.

```bash
python3 -c "import json;d=json.load(open('registry/skills.json'));print(sum(len(s.get('description','')) for s in d['skills']))"
# -> 517654
```

The plugin therefore ships 12 router skills whose descriptions total 7,361
characters, each pointing at a per-domain roster; the 11 rosters together are
291,682 bytes on disk and exactly one is ever opened. That is a real fix, and it
is also strictly more machinery than a 138-skill library needs — one more layer
between a question and an answer, and one more place for the routing to be
wrong.

---

## What changed since the last revision

Three "we are weaker here" claims on the previous version of this page were true
when written and are false now. They are listed rather than silently deleted,
because a reader who saw them deserves the correction:

| Retired claim | Status on 2026-08-15 | Evidence |
|---|---|---|
| "CI runs `validate_repo.py` with `--skip-fixture-retrieval`, so the retrieval-quality gate does not run in CI" | **False.** The flag was removed from CI on 2026-08-14 and survives only in `.githooks/pre-push`, where it saves ~4 min per push | `grep -rn "skip-fixture-retrieval" .github/workflows/` → no hits; `.githooks/pre-push:31` still has it |
| "No workflow runs `evals/scripts/run_evals.py`, so the golden P0 cases gate nothing" | **False.** An `evals` job runs both the golden and agent structure lints | `.github/workflows/validate.yml:202` `run: python3 evals/scripts/run_evals.py --structure` |
| "The scheduled `org-validation` workflow has never executed" | **Stale.** It has now run once and failed at authentication — which is a different, and worse, problem | `gh run list --workflow=org-validation.yml` → one `failure`, 2026-08-10 |

---

## On clean-room authoring

This repository does not copy text from `forcedotcom/sf-skills` or any other
library. That is an editorial choice, not a licensing constraint — both projects
are Apache-2.0, so attributed reuse would be permitted. The reason is that every
claim here has to be traceable to an official source through
[`../standards/source-hierarchy.md`](../standards/source-hierarchy.md), which
inherited prose cannot satisfy. Upstream repositories are read as a coverage
radar — "what topics exist that we lack" — and everything shipped is written
against the primary documentation.

---

*Verified 2026-08-15. Every command on this page was run on that date against
the working tree; re-run them rather than trusting the prose.*
