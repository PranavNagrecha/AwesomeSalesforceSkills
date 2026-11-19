# FAQ

**Who this is for:** first-time readers with a specific question: do I need an
org, how is a skill found, why do the CLI and the MCP server disagree, how true
is a skill.

Where an answer depends on a tuning decision that changes, it names the file to
read instead of quoting a number.

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

## How does Claude actually find a skill?

It reads a chain of increasingly specific markdown files, and the whole chain
ships in the repository. Nothing is searched.

At session start the host loads only the `description:` frontmatter of the 12
router skills under `.claude/skills/` (a top-level `salesforce` router plus 11
domain routers), the slash commands and the run-time agent loaders. No bodies.

From there:

1. The entry router names the 11 domains and hands off to one.
2. That domain router opens its own
   `references/skill-index.md` — the **roster** of just that domain's
   packages, one **gloss** per package.
3. The model scans the roster and opens one
   `skills/<domain>/<slug>/SKILL.md` plus its `references/`.

Claude reads **one** roster, not eleven. That indirection is the reason the
tier exists: a flat list of every skill description costs far more context than
the routers do. `python3 scripts/build_plugin.py --measure` prints both figures.

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
   router descriptions carry explicit negative routing for the overlapping
   cases (a callout is Apex *and* integration; a sharing question is admin
   *and* security), but they only help if your phrasing reaches the right one.
2. **Read the gloss it picked.** Most glosses carry a `NOT for X - use Y`
   clause naming the package to open instead. If your question is X, that
   clause is the answer.
3. **Open the roster yourself.**
   `.claude/skills/salesforce-<domain>/references/skill-index.md` is plain
   markdown and greppable. Paste the right skill id at Claude.
4. **Get a second opinion from search**, if you have run bootstrap:
   `python3 scripts/search_knowledge.py "<your question>"`. It ranks by a
   different signal entirely, so it disagrees usefully.

A skill's `description:` frontmatter is what becomes its gloss, so if a package
is routinely missed, the fix is usually its description rather than the router.

What is measured, and what is not. **Router accuracy rose from 88.3% to 96.1%**
across the 2026-08-14 rewrite of the router descriptions, over 154 held-out
queries; that is only *which of the 12 routers gets opened*. At package level
there is no current number for mechanism 1: the published "79.2% → 92.2% Hit@1"
**is retracted** (post-mortem in
[../evals/measurement/README-model-routing.md](../evals/measurement/README-model-routing.md)).
The package-level number that does exist is for keyword search, mechanism 3, on
the same 154 held-out queries: **Hit@1 0.41, Hit@3 0.50** (2026-10-20,
`scripts/release_gate.sh`).

## Do I need a Salesforce org to use this?

No, for almost everything. Skill routing, the skill packages themselves, the
agents, the templates and the decision trees are plain files and work with no
org, no credentials and no network.

An org is required only for the org-touching MCP tools — the ones that describe
your org's metadata or run read-only SOQL against it (`describe_org`,
`list_custom_objects`, `list_flows_on_object`, `validate_against_org`,
`tooling_query` and their siblings; 26 of the 50 tools carry the
`_ANN_ORG_READ` annotation). Those borrow the Salesforce CLI's existing
authenticated session; this project stores no credentials of its own. If you
never authenticate, the other 24 tools still work.

## What is the difference between a skill and an agent?

A **skill** is reference material about one Salesforce topic: what the
platform does, the failure modes, worked examples, and the specific wrong code
a language model tends to produce. It answers "what is true here", to the
extent its claims are right (see the last question on this page).

An **agent** is a procedure: a numbered plan for one job, a list of skills and
templates it must read first, an output contract, and refusal conditions. It
answers "what do I do now, in what order". Agents cite skills; skills never
cite agents. Of the 70 run-time agents, 7 are `stable`, 8 `beta` and 55
`experimental` (ungraded); [docs/agents.md](agents.md) gives each one's status.

Concretely: `skills/apex/recursive-trigger-prevention/SKILL.md` explains why a
static Boolean guard silently drops records.
`agents/trigger-consolidator/AGENT.md` (experimental) is the procedure that
finds every trigger on an object, collapses them into one handler, and produces
a deactivation order. The second reads the first.

## Why are there far more skills than runtime agents?

Because the two grow along different axes. Skills track platform surface area,
which is enormous. Agents track *jobs people repeatedly ask for*, which is a
much smaller set, and each one is expensive: an agent must declare and read
every skill it depends on before producing output.

About half the skill packages are cited by no agent. Do not read that as a
defect. **The orphan check is a WARN, not an error** (`scripts/validate_repo.py`,
`_check_orphan_skills`). It used to be an ERROR, and the docstring on that
function records what that produced: hundreds of machine-generated citations
whose description was just the slug title-cased. What errors now is a Mandatory
Reads description that is an exact echo of the skill slug, on the reasoning that
a citation an agent will not actually read is worse than none.

Every package is reachable through mechanism 1 regardless of who cites it.
`python3 scripts/check_doc_counts.py` prints the current skill, agent and tool
totals.

## Is command-line search slow?

Not on a current checkout: `search_knowledge.py` loads only the lexical index,
plus skill-level vectors when embeddings are installed. The MCP server is faster
in a warm process because it never opens `chunks.jsonl` at all, so use it when
you are iterating on phrasing.

## Why do the CLI and the MCP server give different answers?

On a repository checkout, they should not — but they are different code paths,
not two settings of one path. `mcp/sfskills-mcp/src/sfskills_mcp/skills.py`
never calls `scripts/search_knowledge.py`; it imports `aggregate_skill_scores`
and `rerank_results` from `pipelines` directly and runs a shorter pipeline. Both
gate coverage on the same `config/retrieval-config.yaml` thresholds and reach
FTS5 through `pipelines.lexical_index.tokenize_query`.

`evals/measurement/check_cli_mcp_parity.py --heldout` runs both over the 154
held-out queries in `.github/workflows/tests.yml` and fails on any difference in
the gated skill list.

What still differs:

- **Where the vectors come from.** Both embed the query, but only when
  `vector_index/skill_embeddings.jsonl` is present. It is on a checkout that
  has `fastembed` installed *and* has run
  `python3 scripts/build_skill_embeddings.py` (one vector per skill). It is
  never in the PyPI data bundle, so a pip-only install is lexical-only and
  *will* score differently, and the parity check does not cover it.
- **Speed.** The MCP path answers faster once warm because it never reads
  `chunks.jsonl`. The first call still pays a model load when vectors exist.

The full comparison is in
[architecture.md](architecture.md#the-two-surfaces-do-not-share-a-code-path).

## Can I just install all of this as a flat Claude Code skill set?

No. A flat export of every skill description — the short strings a tool must
hold in context simply to know what exists — would consume most of a context
window before a single question was asked
(`python3 scripts/build_plugin.py --measure`, key `flat_export_tokens`).

Any packaging has to be tiered, which is what the 12 routers and their 11
rosters are: the routers load up front and the roster you need is opened on
demand. `python3 scripts/export_skills.py --target claude` produces that shape.
Use `--domain` or `--skill` if you want a flat subset small enough to carry.

## Where do the generated files come from, and why can't I edit them?

`registry/`, `vector_index/`, `.claude/skills/`, `.claude/agents/`,
`docs/SKILLS.md`, `docs/queue-progress.md` and `standards/validation-gates.md`
are all derived from the skill packages and the agent files. `python3
scripts/skill_sync.py --all --skip-embeddings` regenerates the first group
(without `--skip-embeddings` it starts a multi-hour embedding encode);
`python3 scripts/build_plugin.py` regenerates the routers, the rosters and the
agent loaders.

Both are gated:

- `scripts/validate_repo.py` recomputes `registry/skills.json`,
  `registry/knowledge-map.json`, every `registry/skills/*.json`,
  `docs/SKILLS.md`, `vector_index/chunks.jsonl`, `vector_index/manifest.json`,
  `standards/validation-gates.md` and `docs/queue-progress.md`, and errors if
  the committed copy differs (`pipelines/sync_engine.py`, `diff_state`).
- `python3 scripts/build_plugin.py --check` does the same for the plugin
  artifacts under `.claude/`, and `.github/workflows/validate.yml` runs it on
  every push and pull request to `main`.

`docs/reports/duplicate-candidates.md` is regenerated by
`scripts/audit_duplicates.py` and checked by nothing. Either way the fix is to
rerun the generator, never to patch the artifact.

One consequence is worth stating plainly: a skill's `description:` frontmatter
feeds `registry/skills.json`, which feeds its gloss in a roster, which is what
the model reads when deciding whether to open it. Editing a description is
editing routing behaviour.

## Does a fresh clone find anything before I build the index?

Yes, through mechanism 1. `CLAUDE.md`, the 12 routers, the 11 rosters and the
agent loaders under `.claude/` are tracked and present the moment `git clone`
finishes.

What a fresh clone does **not** have is the keyword-search index. `git ls-files
vector_index` returns three files — `manifest.json`, `query-fixtures.json` and
`query-variants.json`. Everything else there is gitignored.

The failure that follows is silent. `pipelines.lexical_index.search_index`
returns an empty list rather than raising when the SQLite file is absent, and
`search_knowledge.py` then prints `Coverage: NONE` and **exits 0**. That is
indistinguishable from a library with nothing on the topic. Run
`python3 scripts/bootstrap.py` once and it works. Full walkthrough in
[installing.md](installing.md); symptom-first version in
[troubleshooting.md](troubleshooting.md).

Use `scripts/bootstrap.py` rather than `scripts/build_index.py`: the latter
rewrites every registry record, leaves a large set of modified tracked files,
and starts the embedding pass.

## Are embeddings required?

No. `config/retrieval-config.yaml` sets `embeddings.enabled: true` with the
`fastembed` backend, but `fastembed` is commented out of `requirements.txt`. A
plain `pip install -r requirements.txt` does not install it, and when the
package is absent `pipelines/embedding_backends.py` logs a warning and falls
back to lexical-only. So they are **configured on and inert until you install a
backend yourself**:

```bash
python3 -m pip install 'fastembed>=0.4,<1.0'
python3 scripts/build_skill_embeddings.py
```

`scripts/build_skill_embeddings.py` is the only producer of
`vector_index/skill_embeddings.jsonl`; `bootstrap.py` does not build it. A PyPI
install of the MCP server is lexical-only, since the data bundle carries no
vector files.

What they buy is a small Hit@3 gain on the held-out set, for mechanism 3 only.
Measure it yourself rather than quoting a figure:
`python3 evals/measurement/run_heldout.py` against
`python3 evals/measurement/run_heldout.py --no-embeddings`. Neither says
anything about the routing quality a clone or plugin user experiences.

## Is anything here deploying to my org?

No. Nothing in this repository pushes metadata, runs anonymous Apex, or
performs DML. Every org-facing MCP tool carries `readOnlyHint: true`. Exactly
one of the 50 tools writes anything at all — `emit_envelope`, which saves a
runtime agent's report to `docs/reports/<agent>/<run_id>.json` and `.md` on your
own disk, and is annotated `readOnlyHint: false` so a client can see that.
Runtime agents are contractually forbidden from deploying and from writing
outside paths you supply (`agents/_shared/AGENT_CONTRACT.md`, rule 7). When the
docs say a build was "validated" in an org, they mean check-only
`sf project deploy start --dry-run` runs in a developer org, made on three of
the five example builds.

Credentials are not stored by this project; the org tools shell out to the `sf`
CLI. Credential-shaped strings are scrubbed to `[REDACTED]` on both the success
and the error path in `mcp/sfskills-mcp/src/sfskills_mcp/sf_cli.py`, with a
dedicated test module behind it.

## How do I know a claim in a skill is true?

You check it. Many are not yet checked by anyone.

- **The claims audit is partial and paused.** An audit that checks each claim
  against the official Salesforce guides has covered 108 of the 679 skills that
  had never been audited, and it corrected 503 contradicted claims in them —
  about 4.7 per skill. The other 571 have not been audited. Expect unaudited
  packages to contain wrong claims with no marker on them. Audited batches are
  logged one line per batch in `evals/measurement/audit-ledger.jsonl`, and the
  audit's status is item R3-06 in `RELEASES.yaml`.
- **UNVERIFIED markers are partial.** About 2,300 claims carry an inline
  `UNVERIFIED (YYYY-MM-DD)` marker where an author flagged them;
  `grep -rl "UNVERIFIED" skills/` lists the files. An unmarked claim is not
  thereby verified.
- **Listed sources are not per-claim evidence.** Every package's
  `references/well-architected.md` has an `## Official Sources Used` section
  (the validator fails a package without one), and
  `standards/source-hierarchy.md` ranks official documentation above everything
  else. A source on that list does not mean each sentence was checked against
  it. The `updated:` date records an edit, not a verification.
- **Knowledge lift is measured, on small samples.** On the 30 golden eval cases
  the answer with the skill loaded scored higher in 22 and lower in 6 (2 ties).
  On 20 + 10 Winter '27 fact probes, correct answers rose from 0% to 100% and
  from 50% to 100% with an audited skill loaded. The golden cases cover 10
  skills and the probes cover audited skills only ([../evals/README.md](../evals/README.md)).
- **Golden evals are thin.** They exist for 10 of the 1,040 packages, in 4 of 11
  domains. CI lints their structure (`run_evals.py --structure` in
  `validate.yml`) but does not grade answers against the rubric.

Three harnesses check the library against a live org
(`scripts/validate_probes_against_org.py`, `scripts/smoke_test_agents.py`,
`scripts/validate_skill_factuality.py`). They are re-runnable, but no results
are committed. Run them against your own org rather than reading a number off
this repo.

## Where do I report a skill that is wrong or missing?

[../CONTRIBUTING.md](../CONTRIBUTING.md) covers adding a skill, fixing one,
reporting a gap and flagging stale content. Before claiming a topic is missing,
search for it — most "missing" topics exist under a different name.
