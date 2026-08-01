# How SfSkills Compares

An honest read of the landscape, including the places where a reader should
pick something else. Every external fact carries a URL and was checked on
**2026-07-31**; every in-repo figure came from a command run on the same day.

---

## The alternatives

**forcedotcom/sf-skills** — Salesforce's own curated Agent Skills library
(<https://github.com/forcedotcom/sf-skills>). Licensed **Apache-2.0**, 778
stars, 284 forks, last pushed 2026-07-31
(`gh api repos/forcedotcom/sf-skills --jq '{license:.license.spdx_id,stars:.stargazers_count,forks:.forks_count}'`).
It holds 112 directories under `skills/`
(`gh api repos/forcedotcom/sf-skills/contents/skills --jq '[.[]|select(.type=="dir")]|length'`),
is "optimized for Agentforce Vibes", auto-installs and auto-updates there, and
installs everywhere else with one command: `npx skills add forcedotcom/sf-skills`.
Its own README warns that skills "may be renamed, restructured, or removed
between releases" and do not carry GA stability guarantees.

**The official Salesforce DX MCP server, `@salesforce/mcp`** —
<https://www.npmjs.com/package/@salesforce/mcp>, documented at
<https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_mcp.htm>.
60+ tools organised into toolsets you enable selectively to keep the context
window small. This is first-party org access: metadata, SOQL, deploy/retrieve,
code analysis. It is a tool surface, not a knowledge layer — it will run your
query, not tell you the query is non-selective.

**The Agent Skills open format itself** — spec at
<https://agentskills.io/specification>, mirrored at
<https://github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md>.
Any `SKILL.md` directory works across a growing list of tools listed at
<https://agentskills.io/>. The format is the distribution channel, not a
competitor. The relevant comparison is against the many individually authored
Salesforce skills published in it: the spec requires only `name` and
`description` in frontmatter, so it deliberately imposes no bar on sourcing,
depth, or review. Whether a given skill is trustworthy is entirely on its
author.

**No library at all — the raw model.** The honest baseline. Frontier models
write competent Salesforce code and are wrong in consistent, predictable
places: governor limits under bulk load, mixed-DML boundaries, `System.runAs()`
in production Apex, CRUD/FLS omissions, sharing assumptions. Everything above
exists to move that specific failure rate.

---

## Side by side

| | Breadth | Depth per topic | Live-org access | Verifiability / CI | License |
|---|---|---|---|---|---|
| **SfSkills** | 1,027 skills across 11 domains | SKILL.md + examples + gotchas + Well-Architected mapping + an LLM anti-pattern list, in every package | Yes — 38 read-only MCP tools over the user's `sf` CLI session | Structural validator on every PR; golden evals and live-org harnesses exist but do **not** gate | Apache-2.0 (<https://github.com/PranavNagrecha/AwesomeSalesforceSkills>) |
| **forcedotcom/sf-skills** | 112 skill directories | Task-shaped generate/build workflows; no per-skill anti-pattern catalogue | No — skills only; pair it with `@salesforce/mcp` | Not published; upstream explicitly disclaims stability between releases | Apache-2.0 (<https://github.com/forcedotcom/sf-skills>) |
| **`@salesforce/mcp`** | n/a — 60+ tools, not skills | n/a — executes, does not advise | Yes, first-party and deepest | Salesforce-maintained release process | Salesforce npm package (<https://www.npmjs.com/package/@salesforce/mcp>) |
| **Community Agent Skills** | Effectively unbounded | Highly variable; typically one file, no sources, no tests | Only if a skill wraps a server | None | Per-author, mixed |
| **Raw model, no library** | Whatever is in the weights | Fluent syntax, no model of platform limits | No | None | n/a |

The reasonable configuration for most teams is not either/or: `@salesforce/mcp`
for first-party org operations, plus a knowledge layer that tells the model
what *not* to write.

---

## Where SfSkills Is Weaker

These are the reasons to pick something else. All measured 2026-07-31.

- **Not listed in any plugin directory, and the first run is not one command.**
  The `.claude-plugin/` manifests now exist in-tree — `plugin.json` and
  `marketplace.json`, both declaring the tiered router-skill layout — but
  nothing has been submitted to or accepted by a directory
  (<https://code.claude.com/docs/en/plugin-marketplaces>), so installing today
  still means `git clone`, a `pip install`, and a one-time retrieval-index
  build that takes minutes and fails silently if skipped.
  `npx skills add forcedotcom/sf-skills` is a materially better first-run
  experience.
- **It cannot ship as a flat skill set.** The 1,027 skill descriptions alone
  total 509,800 characters on 2026-07-31 — roughly 127,000 tokens
  (`python3 -c "import json;d=json.load(open('registry/skills.json'));print(sum(len(s.get('description','')) for s in d['skills']))"`).
  Loading the index would consume most of a context window, which is why the
  plugin manifest ships 12 router skills that delegate to search rather than
  the packages themselves — strictly more machinery than a 112-skill library
  needs, and one more layer between a question and an answer.
- **Not first-party.** No auto-install and auto-update inside Agentforce
  Vibes, no pre-GA visibility into unreleased platform behaviour, and no
  Salesforce release-train guarantee. When Salesforce ships something in a
  seasonal release, `forcedotcom/sf-skills` can be right on day one and this
  repo cannot.
- **The clone is heavy.** `.git` is 524 MB (`du -sh .git`) because generated
  retrieval artefacts are versioned. A shallow clone helps; a plain
  `git clone` does not.
- **Depth is uneven, and thin where it matters most.** Measured by markdown
  bytes per package, 112 of 1,027 packages hold under 15 KB and 152 hold under
  20 KB. Security is the thinnest domain — 18 of its 48 packages (37%) are
  under 15 KB, the worst possible place for it — followed by OmniStudio at 12
  of 34 (35%). A reader who needs Shield or event-monitoring depth may not
  find it.

  ```bash
  python3 -c "import pathlib,collections; \
  s=[(d.parts[1], sum(f.stat().st_size for f in d.rglob('*.md'))) \
  for d in (p.parent for p in pathlib.Path('skills').glob('*/*/SKILL.md'))]; \
  print(sum(v < 15*1024 for _,v in s), 'of', len(s))"
  # -> 112 of 1027
  ```
- **OmniStudio is one agent deep.** A single `omnistudio-designer` is the
  entire accelerator surface for OmniScript, FlexCards, DataRaptors,
  Integration Procedures and the Business Rules Engine — it is the only agent
  in the roster that cites an OmniStudio skill, and it carries all 34 of them.

  ```bash
  grep -rl "omnistudio/" agents/*/AGENT.md
  # -> agents/omnistudio-designer/AGENT.md
  grep -c "^    - omnistudio/" agents/omnistudio-designer/AGENT.md
  # -> 34
  ```

  Apex, LWC and architecture work is served by sixteen developer-tier agents
  by comparison. Combined with the thin-package rate above, OmniStudio is the
  domain where this library is furthest from the depth it claims elsewhere.
- **The quality gates that would prove all of this are switched off.**
  `.github/workflows/validate.yml` runs `validate_repo.py` with
  `--skip-fixture-retrieval`, so the retrieval-quality gate does not run in
  CI. No workflow runs `evals/scripts/run_evals.py`
  (`grep -rn "run_evals" .github/workflows/ .githooks/` → no hits), so the
  golden P0 cases gate nothing. The scheduled `org-validation` workflow has
  never executed (`gh run list --workflow=org-validation.yml --json conclusion`
  → `[]`); the live-org reports in `docs/validation/` are from April 2026 and
  were produced by hand.
- **Retrieval quality is measured against a friendly benchmark.** The query
  fixtures in `vector_index/query-fixtures.json` are close paraphrases of the
  `triggers:` keywords in each skill's own frontmatter — which are themselves
  indexed. Scores against them are therefore an upper bound, not an estimate
  of how the library behaves on a question phrased the way a working admin
  would phrase it. Internal held-out testing shows a materially worse rate of
  both false "no coverage" answers and adjacent-skill misrouting. Treat search
  as the weakest layer, and read `docs/SKILLS.md` directly when a query comes
  back empty.
- **Nine stars.** Public since 2026-06-17 with 9 stars and 2 forks
  (`gh api repos/PranavNagrecha/AwesomeSalesforceSkills`). There is no
  community signal yet, no third-party review, and no track record of
  responsiveness to issues. Weigh that against 778 stars upstream.

---

## On clean-room authoring

This repository does not copy text from `forcedotcom/sf-skills` or any other
library. That is an editorial choice, not a licensing constraint — both
projects are Apache-2.0, so attributed reuse would be permitted. The reason is
that every claim here has to be traceable to an official source through
[`../standards/source-hierarchy.md`](../standards/source-hierarchy.md), which
inherited prose cannot satisfy. Upstream repositories are read as a coverage
radar — "what topics exist that we lack" — and everything shipped is written
against the primary documentation.

---

*Verified on 2026-07-31.*
