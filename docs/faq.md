# FAQ

Questions a first-time reader actually asks. Every answer is grounded in
behaviour measured in this repository on 2026-08-15, or in the code that
produces it. Where something is a tuning decision that changes, the answer says
so and names the file to read instead.

One framing to carry through the whole page. There are **three** ways a
question reaches a skill package, and only the first works without a build
step:

1. **A model-driven roster scan.** Claude reads the router descriptions, opens
   one domain roster, scans it, opens a package. No index, no build, no API
   key. This is what a clone and a plugin install both use, and it is the path
   nearly every install exercises.
2. **The MCP `search_skill` tool.** Real, but not auto-wired: you have to
   connect the `sfskills-mcp` server yourself, and it needs an index behind it.
3. **`scripts/search_knowledge.py`.** Needs a local `python3
   scripts/bootstrap.py` run first.

Any accuracy or speed figure below names the mechanism it measures. Mixing them
up is how this project has previously published a keyword-search number as
though it described the experience a user actually has.

---

## How does Claude actually find a skill in 1,027 packages?

It reads a chain of increasingly specific markdown files, and the whole chain
ships in the repository. Nothing is searched.

At session start the host loads only the `description:` frontmatter of the 12
router skills under `.claude/skills/` (a top-level `salesforce` router plus 11
domain routers), the 67 slash commands and the 48 run-time agent loaders. No
bodies. That costs about **5,490 tokens**
(`python3 scripts/build_plugin.py --measure`, key `tier1_tokens`).

From there:

1. The entry router names the 11 domains and hands off to one.
2. That domain router opens its own
   `references/skill-index.md` — the **roster** of just that domain's
   packages, one **gloss** per package, budgeted at 220 characters
   (`scripts/build_plugin.py:281`).
3. The model scans the roster and opens one
   `skills/<domain>/<slug>/SKILL.md` plus its `references/`.

Claude reads **one** roster, not eleven. An Apex question costs the apex
roster's 158 glosses, never the corpus's 1,027. That indirection is the entire
reason the tier exists: a flat export of all 1,027 skill descriptions measures
**138,694 tokens**, so the tiered form costs **4.0%** of the naive one.

Full walkthrough, with the mermaid diagram and the roster anatomy, is in
[architecture.md](architecture.md#mechanism-1-the-model-driven-roster-scan).

## Claude opened the wrong skill. What do I do?

This is the most common real failure, and it is worth understanding why it
looks the way it does: **mechanism 1 has no coverage gate.** Mechanisms 2 and 3
compute a score, compare it to a threshold, and can refuse to answer with
`Coverage: NONE`. A model scanning a roster always finds a plausible-looking
line. So the failure mode is not silence, it is confidence in the wrong
package.

In order of effort:

1. **Name the domain.** "This is a sharing question, not an Apex one" resolves
   most of it, because the domain pick is where routing goes wrong first. The
   router descriptions carry explicit negative routing for exactly the
   overlapping cases (a callout is Apex *and* integration; a sharing question
   is admin *and* security), but they only help if your phrasing reaches the
   right one.
2. **Read the gloss it picked.** Glosses carry a `NOT for X - use Y` clause
   naming the package to open instead — **1,022 of the 1,027** have one
   (`grep -c "NOT for"` across the eleven rosters). If your question is X, that
   clause is the answer.
3. **Open the roster yourself.**
   `.claude/skills/salesforce-<domain>/references/skill-index.md` is plain
   markdown and greppable. Paste the right skill id at Claude.
4. **Get a second opinion from search**, if you have run bootstrap:
   `python3 scripts/search_knowledge.py "<your question>"`. It ranks by a
   different signal entirely, so it disagrees usefully.

Two things worth knowing before you conclude the routing is broken. Some
"wrong" picks are defensible: the corpus contains genuine near-duplicate pairs
(`security/mfa-enforcement-strategy` and `security/mfa-enforcement-patterns`),
and exact-match scoring charges the router for them. And a skill's
`description:` frontmatter is what becomes its gloss, so if a package is
routinely missed, the fix is usually its description rather than the router.

The measurement that survives scrutiny on this path is **router accuracy: 88.3%
→ 96.1%** across the 2026-08-14 rewrite of the router descriptions, over 154
held-out queries. That is *which of the 12 routers gets opened*, and it does
not depend on any skill-level label. The package-level headline this project
published first ("79.2% → 92.2% Hit@1") **is retracted** — re-scored against a
single label set the direction inverts, 10 regressions and 0 improvements. The
post-mortem is in
[../evals/measurement/README-model-routing.md](../evals/measurement/README-model-routing.md).

## Do I need a Salesforce org to use this?

No, for almost everything. Skill routing, the skill packages themselves, the
agents, the templates and the decision trees are plain files and work with no
org, no credentials and no network.

An org is required only for the org-touching MCP tools — the ones that describe
your org's metadata or run read-only SOQL against it (`describe_org`,
`list_custom_objects`, `list_flows_on_object`, `validate_against_org`,
`tooling_query` and their siblings; 24 of the 38 tools carry the `_ANN_ORG_READ`
annotation). Those borrow the Salesforce CLI's existing authenticated session;
this project stores no credentials of its own. If you never authenticate, the
other 14 tools still work.

## What is the difference between a skill and an agent?

A **skill** is knowledge about one Salesforce topic: what the platform actually
does, the failure modes, worked examples, and the specific wrong code a
language model tends to produce. It answers "what is true here".

An **agent** is a procedure: a numbered plan for one job, a list of skills and
templates it must read first, an output contract, and refusal conditions. It
answers "what do I do now, in what order". Agents cite skills; skills never
cite agents.

Concretely: `skills/apex/recursive-trigger-prevention/SKILL.md` explains why a
static Boolean guard silently drops records.
`agents/trigger-consolidator/AGENT.md` is the procedure that finds every
trigger on an object, collapses them into one handler, and produces a
deactivation order so nothing breaks mid-migration. The second reads the first.

## Why are there far more skills than runtime agents?

Because the two grow along different axes. Skills track platform surface area,
which is enormous and keeps expanding. Agents track *jobs people repeatedly ask
for*, which is a much smaller set, and each one is expensive: an agent must
declare and read every skill it depends on before producing output.

The numbers, measured 2026-08-15 by taking the union of `dependencies.skills:`
across the 76 `agents/*/AGENT.md` files — the exact set the validator builds:

| | count |
|---|---:|
| Agents declaring a `dependencies.skills:` block | 50 |
| Distinct skills cited by at least one agent | **509** |
| Skills cited by no agent | **518** |
| Citations pointing at a skill that does not exist | 0 |
| Packages recording `runtime_orphan: true` | 54 |

Do not read that as coverage in either direction, and do not read the uncited
518 as a defect. **The orphan check is a WARN, not an error**
(`scripts/validate_repo.py:397`). It used to be an ERROR whose message handed
the reader a paste-ready command that added a citation, and the docstring on
`_check_orphan_skills` records what that produced: *555 machine-generated
citations whose description was just the slug title-cased*. Severity was
deliberately inverted afterwards. What errors now is citation **quality** — a
Mandatory Reads description that is an exact echo of the skill slug — on the
reasoning that a citation an agent will not actually read is worse than no
citation at all.

So an agent existing for a topic tells you a job was worth automating, not
whether the library covers it. Every package is reachable through mechanism 1
regardless of who cites it.

Counts move. `python3 scripts/check_doc_counts.py` is the authority for the
skill/agent/tool totals and will print the current figures; treat any number
written into prose, here included, as a snapshot.

## Is command-line search slow?

Not any more. It used to be, and this page said so for months.

Measured on this checkout on 2026-08-15 with
`/usr/bin/time -p python3 scripts/search_knowledge.py "<query>"`:

| query | wall clock |
|---|---:|
| `trigger recursion` | 0.56, 0.48 s |
| `why is my LWC slow` | 0.57, 0.54 s |
| `permission sets` | 0.80, 0.52 s |

Peak resident memory 391 MB (`/usr/bin/time -l`). The figure this FAQ carried
before — a **13 s to 29 s** band, blamed on loading a 535 MB
`vector_index/embeddings.jsonl` and a 126 MB `vector_index/chunks.jsonl` on
every invocation — was accurate when measured on 2026-07-31 and is now wrong on
both counts.

Commit `d8c95d5de` found two causes. `build_search_context` called
`load_embeddings()` unconditionally with no reference to `embeddings.enabled`,
loading roughly 2 GB that `rerank_results` then never read. And it
materialised all of `chunks.jsonl` — around 856 MB of dicts — so that a single
consumer could look up `official_source_ids`, a field only 30 chunks in the
corpus populate. Both are fixed: the embeddings load is gated on config, and
only the records carrying a payload are read.

The MCP server is still faster in a warm process — 15 to 61 ms per query
measured on the same three queries — because it never opens `chunks.jsonl` at
all. If you are iterating on phrasing, use it. But the CLI is no longer a
reason to avoid mechanism 3.

## Why do the CLI and the MCP server give different answers?

On a repository checkout, they do not — but they are still different code
paths, not two settings of one path.
`mcp/sfskills-mcp/src/sfskills_mcp/skills.py` never calls
`scripts/search_knowledge.py`; it imports `aggregate_skill_scores` and
`rerank_results` from `pipelines` directly and runs a shorter pipeline.

Two divergences that used to exist have closed. **Coverage**: both surfaces now
gate on `max_score >= min_skill_max_score or score >= min_skill_score`, reading
the same `config/retrieval-config.yaml`. **Punctuation**: this page used to warn
that `search_skill("100% test coverage")` raised `sqlite3.OperationalError:
fts5: syntax error near "%"` where the CLI answered. Both surfaces reach FTS5
through `pipelines.lexical_index.tokenize_query`, which replaces every
non-bareword character with a space (`lexical_index.py:52`), so `%` never
arrives as an operator — that query returns
`agentforce/agent-testing-and-evaluation` on both.

`evals/measurement/check_cli_mcp_parity.py --heldout` runs both over all 154
held-out queries in `.github/workflows/tests.yml` and fails on any difference in
the gated skill list. Run today: `CLI/MCP retrieval parity: 154/154 queries
agree`.

What still differs:

- **Where the vectors come from.** Both embed the query, but only when
  `vector_index/skill_embeddings.jsonl` is present. It is on a checkout that
  has `fastembed` installed *and* has run
  `python3 scripts/build_skill_embeddings.py` (1,027 vectors, one per skill),
  and it is never in the PyPI wheel, so a pip-only install is lexical-only and
  *will* score differently.
- **Speed.** The MCP path answers in milliseconds once warm because it never
  reads `chunks.jsonl`. The first call still pays a model load — 408 ms here.

The full comparison is in
[architecture.md](architecture.md#the-two-surfaces-do-not-share-a-code-path).

## Can I just install all of this as a flat Claude Code skill set?

No, and this is a hard constraint rather than a missing feature. A flat export
of every skill description — the short strings a tool must hold in context
simply to know what exists — measures **138,694 tokens**
(`python3 scripts/build_plugin.py --measure`, key `flat_export_tokens`).
Loading that would consume most of a context window before a single question
was asked.

Any packaging has to be tiered, which is what the 12 routers and their 11
rosters are: **5,490 tokens** loaded up front, **4.0%** of the flat cost, and
the roster you actually need is opened on demand. `python3
scripts/export_skills.py --target claude` produces that shape. Use `--domain`
or `--skill` if you want a genuinely flat subset small enough to carry.

## Where do the generated files come from, and why can't I edit them?

`registry/`, `vector_index/`, `.claude/skills/`, `.claude/agents/`,
`docs/SKILLS.md`, `docs/queue-progress.md` and `standards/validation-gates.md`
are all derived from the skill packages and the agent files. `python3
scripts/skill_sync.py --all` regenerates the first group; `python3
scripts/build_plugin.py` regenerates the routers, the rosters and the agent
loaders.

Two different guards, with different teeth:

- **Gated.** `scripts/validate_repo.py` recomputes `registry/skills.json`,
  `registry/knowledge-map.json`, every `registry/skills/*.json`,
  `docs/SKILLS.md`, `vector_index/chunks.jsonl`, `vector_index/manifest.json`,
  `standards/validation-gates.md` and `docs/queue-progress.md`, and errors if
  the committed copy differs (`pipelines/sync_engine.py`, `diff_state`). A
  hand-edit to any of those fails the gate on the next commit.
- **Not gated.** `python3 scripts/build_plugin.py --check` does the same for
  the 121 plugin artifacts under `.claude/` and reports `OK: 121 plugin
  artifact(s) match a fresh build` — but `grep -rn "build_plugin" .github/
  .githooks/` returns nothing, so no workflow or hook runs it. Editing a router
  or a roster by hand will not be caught for you. Run it yourself.
  `docs/reports/duplicate-candidates.md` is likewise regenerated by
  `scripts/audit_duplicates.py` and checked by nothing.

Either way the fix is to rerun the generator, never to patch the artifact
again.

One consequence is worth stating plainly: a skill's `description:` frontmatter
feeds `registry/skills.json`, which feeds its gloss in a roster, which is what
the model reads when deciding whether to open it. Editing a description is
editing routing behaviour.

## Does a fresh clone find anything before I build the index?

Yes — this page used to claim otherwise and it was the most damaging thing on
it. A fresh clone reaches skill packages perfectly well through mechanism 1.
`CLAUDE.md`, the 12 routers, the 11 rosters and the 48 agent loaders under
`.claude/` are all tracked on `origin/main` and present the moment `git clone`
finishes.

What a fresh clone does **not** have is the keyword-search index. `git ls-files
vector_index` returns exactly three files — `manifest.json`,
`query-fixtures.json` and `query-variants.json`. Everything else there is
gitignored: `chunks.jsonl` at 127 MB and `lexical.sqlite` at 179 MB on this
checkout.

The failure that follows is silent, which is the real problem.
`pipelines.lexical_index.search_index` returns an empty list rather than
raising when the SQLite file is absent (`pipelines/lexical_index.py:155-156`),
and `main()` in `search_knowledge.py` has no non-zero return path, so the whole
pipeline runs, finds nothing, gates on nothing, and **exits 0**:

```text
$ python3 scripts/search_knowledge.py "trigger recursion"
Query: trigger recursion

Coverage: NONE — no skill meets the confidence threshold. Use official sources below.
Top skills:

Top chunks:
$ echo $?
0
```

That is indistinguishable from a library with nothing on the topic. It is not.
Run `python3 scripts/bootstrap.py` once — about 9 s on a fresh clone, per the
measurement in `scripts/bootstrap.py:20` — and it works. Full walkthrough in
[installing.md](installing.md); symptom-first version in
[troubleshooting.md](troubleshooting.md).

Use `scripts/bootstrap.py` rather than `scripts/build_index.py`: the latter
reaches the same outcome through `pipelines.sync_engine.write_state`, which
rewrites every registry record and leaves about 1,029 modified tracked files
you then have to recognise as noise (`scripts/bootstrap.py:33-36`).

## Are embeddings required?

No, and the honest description of their status is narrower than either phrasing
this repo has used before.

`config/retrieval-config.yaml` sets `embeddings.enabled: true` with the
`fastembed` backend, but `fastembed` is commented out of `requirements.txt`
(line 12). A plain `pip install -r requirements.txt` does not install it, and
when the package is absent `pipelines/embedding_backends.py` logs a warning and
falls back to lexical-only without crashing. So they are neither "opt-in behind
a flag" (the config already enables them) nor "on by default" (the dependency
is not installed). They are **configured on and inert until you install a
backend yourself**.

Turning them on is two commands, not one:

```bash
python3 -m pip install 'fastembed>=0.4,<1.0'
python3 scripts/build_skill_embeddings.py
```

The second one matters and this page used to omit it. `bootstrap.py` does not
produce `vector_index/skill_embeddings.jsonl` — `grep -n "skill_embeddings"
scripts/bootstrap.py` returns nothing — and `scripts/build_skill_embeddings.py`
is its only producer. Without that file the ranker has no vectors to compare
against, no matter what is installed. A PyPI install of the MCP server takes
the lexical path permanently, since the wheel carries no vector files.

What they buy, re-measured 2026-08-15 over the 154 hand-written held-out
queries with `python3 evals/measurement/run_heldout.py --json` versus
`--no-embeddings`:

| retrieval config | Hit@1 | Hit@3 | Coverage: NONE |
|---|---:|---:|---:|
| lexical-only | 39.0% | 48.7% | 0.0% |
| + skill vectors | **40.3%** | **53.9%** | 0.0% |

So **+1.3pp Hit@1 and +5.2pp Hit@3**. Both figures measure *mechanism 3*. They
say nothing about the routing quality a clone or plugin user experiences.

This corrects what this page said before. A 2026-07-31 re-measurement over 400
fixtures reported *no difference at all* — 95.5% Hit@1 and 99.8% Hit@3 in every
mode — and concluded embeddings were not buying measurable accuracy. That
conclusion does not survive the held-out set and is withdrawn. The fixtures are
close paraphrases of the `triggers:` frontmatter that is itself indexed, so
they measure the easy case and saturate near the ceiling; a saturated benchmark
cannot show a difference in either direction.

Two smaller corrections in the same area. The 0% `Coverage: NONE` rate is
itself a change worth noticing — a 2026-07-31 measurement on realistic
phrasings recorded 23.3%. And the comment block in
`config/retrieval-config.yaml` quotes earlier runs of the *same* 154 queries at
36.4/44.2 → 37.0/48.7 and then 39.6/48.1 → 40.9/53.9; same direction, drifting
absolutes, because the corpus and the ranker move underneath the benchmark.
Re-run `run_heldout.py` rather than quoting any of those pairs, this page's
included.

Cost is far lower than this page used to claim. `skill_embeddings.jsonl` is
1,027 vectors, one per skill, **5.0 MB** (`du -h`). The 535 MB figure that has appeared in
this repo's docs describes `vector_index/embeddings.jsonl`, the chunk-level
file — which the pipeline *can* build, via `python3 scripts/bootstrap.py
--with-embeddings` ("+535 MB, HOURS of encode time", per that flag's own help
text), but which is absent from this checkout and is not what the table above
measures. Per-query overhead for the skill-level vectors is roughly 50 ms once
the model is warm, with a one-off cold start.

## Is anything here deploying to my org?

No. Nothing in this repository pushes metadata, runs anonymous Apex, or
performs DML. Every org-facing MCP tool carries `readOnlyHint: true`. Exactly
one of the 38 tools writes anything at all — `emit_envelope`, which saves a
runtime agent's report to `docs/reports/<agent>/<run_id>.json` and `.md` on your
own disk, and is annotated `readOnlyHint: false` so a client can see that.
Runtime agents are contractually forbidden from deploying and from writing
outside paths you supply (`agents/_shared/AGENT_CONTRACT.md`, rule 7).

Credentials are not stored by this project; the org tools shell out to the `sf`
CLI. Credential-shaped strings are scrubbed to `[REDACTED]` on both the success
and the error path in `mcp/sfskills-mcp/src/sfskills_mcp/sf_cli.py`, with a
dedicated test module behind it.

## How do I know a claim in a skill is true?

Every skill package carries an `## Official Sources Used` section in its
`references/well-architected.md`, and the source-trust rules are defined in
`standards/source-hierarchy.md`: official Salesforce documentation outranks
Trailhead and Architects material, which outranks community writing. Search
results also return the relevant official sources alongside the skills, so you
can check the platform claim without leaving the terminal.

The honest limit, stated at its real size. Golden eval **structure** does gate
a merge — `.github/workflows/validate.yml` runs `python3
evals/scripts/run_evals.py --structure` on every pull request, and this page
previously said it gated nothing. What still gates nothing is eval **output
quality**: no workflow scores an answer against its rubric. Nor does either
retrieval benchmark run in CI. Coverage shape matters too: golden cases exist
for 10 of 1,027 packages (1.0%), across 4 of 11 domains — apex 4, integration
3, lwc 2, flow 1. `admin` is the largest domain at 253 skills and has none, as
do `data`, `security`, `devops`, `architect`, `agentforce` and `omnistudio`.

Separately, three harnesses check the library against a live org
(`scripts/validate_probes_against_org.py`, `scripts/smoke_test_agents.py`,
`scripts/validate_skill_factuality.py`). They are re-runnable, but no results
are committed — the last run was April 2026 against a smaller corpus. Run them
against your own org rather than reading a number off this repo.

## Where do I report a skill that is wrong or missing?

[../CONTRIBUTING.md](../CONTRIBUTING.md) covers adding a skill, fixing one,
reporting a gap and flagging stale content. Before claiming a topic is missing,
search for it — the corpus is large enough that most "missing" topics exist
under a different name, and every router carries a standing rule against
claiming otherwise without pasting lookup output.
