# Glossary

This repository's own vocabulary. These terms are assumed everywhere and
defined nowhere else. Salesforce platform terms are not covered here — the
skills themselves define those.

---

## Corpus and authoring

**skill package** — One directory under `skills/<domain>/<slug>/` holding
everything about one topic: a `SKILL.md`, a `references/` folder with exactly
four files (`examples.md`, `gotchas.md`, `well-architected.md`,
`llm-anti-patterns.md`), and optionally `templates/` and `scripts/`. The unit
of authorship, review and retrieval. Machine-generated metadata never lives
inside a package.

**SKILL.md** — The canonical file of a skill package. YAML frontmatter on top,
Markdown body below. The body must contain a `## Recommended Workflow` section
of three to seven numbered steps. Everything a machine knows about a skill is
derived from this file.

**frontmatter** — The YAML block delimited by `---` at the top of a `SKILL.md`
or `AGENT.md`. It is the single canonical metadata source: `name`,
`description`, `category`, `tags`, `triggers`, `inputs`, `outputs`,
`dependencies`, `version`, `updated`. Nothing may duplicate it in a separate
metadata file.

**trigger keywords** (or **triggers**) — The `triggers:` list in a skill's
frontmatter: phrasings a user might type that should reach this skill. Not to
be confused with an Apex trigger. These strings are indexed alongside the
skill body, which is why retrieval performs noticeably better on phrasings
close to a curated trigger than on free-form symptom descriptions.

**domain** — The top-level bucket a skill lives in, and the first path
segment of its id: `admin`, `apex`, `lwc`, `flow`, `omnistudio`,
`agentforce`, `security`, `integration`, `data`, `devops`, `architect`. A
skill id is always `<domain>/<slug>`. `--domain` filters retrieval to one
bucket.

**template** — A canonical, cross-skill building block under `templates/` —
the one `TriggerHandler`, `ApplicationLogger`, `SecurityUtils`,
`TestDataFactory`, LWC skeleton, Flow fault path, Agentforce action shell.
Skills link to these rather than inlining their own variants. A skill-local
file under `skills/.../templates/` is a placeholder or worksheet; when a
second skill starts referencing it, it gets promoted to `templates/`.

**decision tree** — A routing document under `standards/decision-trees/`
consulted *before* a technology is chosen, so that "Flow or Apex" is answered
once and cited, rather than re-argued inside every skill. Four exist:
automation selection, async selection, integration-pattern selection, sharing
selection. Agents cite the specific branch that resolved their choice.

**probe** — A read-only diagnostic query bundled with an agent, defining what
to ask a Salesforce org before making a recommendation. Probes are verified by
executing their SOQL against a real org, so a probe that references a field
that does not exist fails a harness rather than silently misleading an agent.

**envelope** — The structured JSON wrapper a runtime agent returns around its
output: the findings, the confidence score, the ambiguities, and the citations
of every skill, template and decision-tree branch consulted. Its schema is
validated by the MCP server, and consuming tools are required to preserve it
rather than flatten it into prose. See
[consumer-responsibilities.md](consumer-responsibilities.md).

## Agents

**run-time agent** — An agent that does real Salesforce work in your codebase
or org: refactor this Apex, design this permission model, audit this LWC.
Frontmatter `class: runtime`. These are what a consumer of the library
invokes.

**build-time agent** — An agent that maintains the library itself: skill
builders, the validator, the content researcher. Frontmatter `class: build`.
A consumer never runs these. The split is documented in
[../agents/_shared/RUNTIME_VS_BUILD.md](../agents/_shared/RUNTIME_VS_BUILD.md).

**deprecated alias** — A retired agent left in place as a stub with
`status: deprecated` and a `deprecated_in_favor_of` pointer, plus a
slash-command alias that redirects to the replacement. Stubs live for two
minor versions. They keep `class: runtime`, so `class` alone does not tell you
whether an agent is active — both the MCP `health` tool and
`scripts/check_doc_counts.py` read `status` as well and agree on the split
(48 runtime, 14 build, 14 deprecated, 76 total on 2026-07-31). If two agent
counts disagree, one of them is stale. See [MIGRATION.md](MIGRATION.md).

## Retrieval

**chunk** — A retrieval-sized slice of a document, typically a section under
one heading. Skill files, knowledge imports and templates are all chunked.
The index in this checkout holds 130,062 chunks across 1,027 skills. Search
operates on chunks; results are then rolled up to skills.

**lexical index** — The SQLite FTS5 full-text table at
`vector_index/lexical.sqlite`, built by `pipelines/lexical_index.py`. It
indexes each chunk's title, tags and text. Queries are lowercased, split, and
joined as prefix terms with `OR`. This layer is mandatory and needs no API
key. 166.1 MB in this checkout, and gitignored.

**embeddings** — 384-dimension vectors produced by the `fastembed` backend,
one per chunk in `vector_index/embeddings.jsonl` and one per skill in
`vector_index/skill_embeddings.jsonl`. Used to rerank lexical hits by semantic
similarity at a weight tuned in `config/retrieval-config.yaml`. Optional: when
the package is absent the system logs a warning and falls back to
lexical-only.

**vector_index** — The directory holding all retrieval artifacts: the chunk
text, the lexical index, both embedding files, a manifest recording counts and
content hashes, and the query fixtures. Everything in it is generated; the
large files are gitignored and rebuilt with
`python3 scripts/skill_sync.py --all`.

**registry/skills.json** — The whole corpus as one normalised JSON document:
every skill's id, name, category, description, tags, file location, official
sources and lifecycle status, plus a `skill_count`. Generated from the
`SKILL.md` frontmatter. It is what the MCP server enriches search hits from
and what the count lint treats as the authority on corpus size.

**coverage gate** — The decision about whether retrieval is confident enough
to answer at all, as opposed to which skill wins. A skill is kept if
`max_score >= min_skill_max_score` **or** `score >= min_skill_score`, both
thresholds from `config/retrieval-config.yaml`. Note the two numbers are
different units: the score of the single best chunk, and a cumulative sum
across every chunk the skill matched. Nothing clears the gate and the CLI
prints `Coverage: NONE`, telling the consumer to fall back to official
Salesforce sources; the MCP server returns `has_coverage: false` with an empty
`skills` list. Both surfaces apply the same predicate — they have not always,
and the divergence is worth re-checking after any tuning change. `rank_score`
is deliberately excluded: the name/description bonus decides *which* skill
answers, not *whether* to answer. See
[architecture.md](architecture.md#the-two-surfaces-do-not-share-a-code-path).

**harness** — A re-runnable verification script that checks behaviour rather
than structure. Three exist against a live org: probe SOQL execution, agent
structural and dependency checks, and skill factuality sampling. Reports land
under `docs/validation/`. Contrast with the structural validators, which only
check shape.

**golden eval** — An output-quality test case for a flagship skill, under
`evals/golden/`, carrying assertions, a rubric and a reference answer.
Markdown-based, linted by `python3 evals/scripts/run_evals.py --structure`.
Honest caveat: no CI workflow runs them, so they gate nothing today.

## Tooling

**skill_sync** — `scripts/skill_sync.py`, the one command that regenerates
everything derived from the skill packages: the registry, the chunk file, the
lexical index, the embeddings and `docs/SKILLS.md`. `--all` for the whole
repository, `--skill` for one package, `--skip-embeddings` for the fast path
the pre-commit hook uses. Run it after any skill change; run it once after
cloning.

**validate_repo** — `scripts/validate_repo.py`, the gate that must exit 0
before a change ships. It checks frontmatter, required package files,
`AGENT.md` structure, that every citation resolves to a real file, and that no
generated artifact has drifted from what the current sources would produce.
The full gate list with file and line citations is generated into
[../standards/validation-gates.md](../standards/validation-gates.md).

**MCP server** — `mcp/sfskills-mcp`, a Model Context Protocol server exposing
38 read-only tools: skill, agent, template and decision-tree retrieval, plus
live Salesforce org metadata and read-only SOQL. Published to PyPI as
`sfskills-mcp`. It runs over stdio and resolves its data root from
`SFSKILLS_REPO_ROOT`. It is the fastest way to query the library and the only
way to ask questions about your actual org.

**export target** — A tool-native rendering of the corpus produced by
`scripts/export_skills.py`: Cursor rules, Claude skills, Windsurf, Aider
conventions, Augment, Codex, the cross-tool `.agents` convention, and an
MCP-servable bundle. Targets are not equal in fidelity; the parity contract is
[multi-ai-parity.md](multi-ai-parity.md).
