# FAQ

Questions a first-time reader actually asks. Every answer is grounded in
behaviour measured in this repository on 2026-07-31, or in the code that
produces it. Where something is a tuning decision that changes, the answer
says so and names the file to read instead.

---

## Do I need a Salesforce org to use this?

No, for almost everything. Skill search, the skill packages themselves, the
agents, the templates and the decision trees are plain files and work with no
org, no credentials and no network.

An org is required only for the org-touching MCP tools — the ones that
describe your org's metadata or run read-only SOQL against it
(`describe_org`, `list_custom_objects`, `list_flows_on_object`,
`validate_against_org`, `tooling_query` and their siblings). Those borrow the
Salesforce CLI's existing authenticated session; this project stores no
credentials of its own. If you never authenticate, the rest of the 38 tools
still work.

## What is the difference between a skill and an agent?

A **skill** is knowledge about one Salesforce topic: what the platform
actually does, the failure modes, worked examples, and the specific wrong code
a language model tends to produce. It answers "what is true here".

An **agent** is a procedure: a numbered plan for one job, a list of skills and
templates it must read first, an output contract, and refusal conditions. It
answers "what do I do now, in what order". Agents cite skills; skills never
cite agents.

Concretely: `skills/apex/recursive-trigger-prevention/SKILL.md` explains why a
static Boolean guard silently drops records.
`agents/trigger-consolidator/AGENT.md` is the procedure that finds every
trigger on an object, collapses them into one handler, and produces a
deactivation order so nothing breaks mid-migration. The second reads the
first.

## Why are there far more skills than runtime agents?

Because the two grow along different axes. Skills track platform surface area,
which is enormous and keeps expanding. Agents track *jobs people repeatedly
ask for*, which is a much smaller set, and each one is expensive: an agent
must declare and read every skill it depends on before producing output.

Do not read the ratio as coverage in either direction. `validate_repo.py`
errors on any skill that neither an agent cites nor declares
`runtime_orphan: true`, and the cheapest way to clear that gate is bulk
citation — so a large share of agents' "Mandatory Reads" are machine-generated
stubs whose description is just the skill slug with the dashes replaced by
spaces. Counting only the citations a human wrote, roughly 488 of the 1,027
skills are reachable through an agent that genuinely needs them. The rest are
reachable by search, which is how most people find them anyway. Whether an
agent exists for a topic tells you a job was worth automating, not whether the
library covers it.

Counts move. `python3 scripts/check_doc_counts.py` is the authority and will
print the current figures; treat any number written into prose, here included,
as a snapshot.

## Why is command-line search so slow?

Because every invocation is a cold process that reads the whole index off
disk. `vector_index/embeddings.jsonl` is 535.0 MB and
`vector_index/chunks.jsonl` is 126.2 MB, and both are loaded before the first
query is scored. Measured across 2026-07-31 on one Apple-silicon machine, the
same three queries landed anywhere in a **13 s to 29 s** band with a warm page
cache — `"trigger recursion"` 13.14 s, 15.34 s and 17.37 s on three separate
runs, `"why is my LWC slow"` 17.73 s and 18.77 s,
`"permission sets" --domain admin` 19.32 s and 29.25 s. On a cold page cache
earlier the same day the same commands took 52 s to 90 s, and one run
alongside a competing index rebuild took 83.08 s. Budget for the band, not for
a number.

The search itself is not slow. The same query through the MCP server, in a
warm process that never touches the chunk-embeddings file, measured 0.03 s to
0.28 s in the morning session and 0.01 s to 0.18 s in the afternoon one; the
very first call in a process cost 0.79 s, which is the skill-vector load. If
you are iterating on phrasing, use the MCP server.

## Why do the CLI and the MCP server give different answers?

On a repository checkout, mostly they do not any more — but they are still
different code paths, not two settings of one path.
`mcp/sfskills-mcp/src/sfskills_mcp/skills.py` never calls
`scripts/search_knowledge.py`; it imports `aggregate_skill_scores` and
`rerank_results` from `pipelines` directly and runs a shorter pipeline.

The coverage rule used to differ and no longer does. Both surfaces now gate on
`max_score >= min_skill_max_score or score >= min_skill_score`, reading the
same `config/retrieval-config.yaml`. Checked on 2026-07-31,
`search_skill("xylophone")` returns `has_coverage: false` with zero skills,
and `"trigger recursion"` and `"why is my LWC slow"` produce identical scores
on both surfaces (2.505 and 2.507).

What still differs:

- **Punctuation.** The CLI strips characters FTS5 treats as operators before
  searching; the MCP path passes the query through, so
  `search_skill("100% test coverage")` raises
  `sqlite3.OperationalError: fts5: syntax error near "%"`. Strip punctuation
  client-side if you are building an integration.
- **Where the vectors come from.** Both embed the query, but the MCP server
  only does so when `vector_index/skill_embeddings.jsonl` is present. It is on
  a checkout and is not in the PyPI wheel, so a pip-only install is
  lexical-only and *will* score differently.
- **Speed.** The MCP path never reads the 535 MB chunk-embedding file, which
  is worth two to three orders of magnitude.

The full comparison is in
[architecture.md](architecture.md#the-two-surfaces-do-not-share-a-code-path).

## Can I just install all of this as a flat Claude Code skill set?

No, and this is a hard constraint rather than a missing feature. The skill
descriptions alone — the short strings a tool must hold in context simply to
know what exists — total roughly half a million characters, about 128k tokens.
Loading the index would consume most of a context window before a single
question was asked.

Any packaging has to be tiered: a small number of router entries that delegate
to `scripts/search_knowledge.py` or the MCP server, which then return only the
handful of skills that matter. That is what
`python3 scripts/export_skills.py --target claude` and the MCP server are for.
Use `--domain` or `--skill` if you want a genuinely flat subset.

## Where do the generated files come from, and why can't I edit them?

`registry/`, `vector_index/`, `docs/SKILLS.md`, `docs/queue-progress.md` and
`standards/validation-gates.md` are all derived from the skill packages and
the agent files. `python3 scripts/skill_sync.py --all` regenerates them.

They are not editable because `scripts/validate_repo.py` runs a drift check:
it recomputes what the current sources would produce and errors if the
committed artifact differs. A hand-edit therefore fails the gate on the next
commit, and the fix is always to rerun the sync rather than to patch the
artifact again.

## Why does a fresh clone find nothing?

Because the search index is not in the repository. `vector_index/lexical.sqlite`,
`vector_index/chunks.jsonl`, `vector_index/embeddings.jsonl` and
`vector_index/skill_embeddings.jsonl` are gitignored — together about 832 MB,
past what GitHub will carry. The lexical search helper returns an empty list
when the SQLite file is missing rather than raising, so the failure is silent
and looks like an empty library.

Run `python3 scripts/skill_sync.py --all` once after cloning. Full walkthrough
in [getting-started.md](getting-started.md); symptom-first version in
[troubleshooting.md](troubleshooting.md).

## Are embeddings required?

No. `config/retrieval-config.yaml` has `embeddings.enabled: true` with the
`fastembed` backend, but `fastembed` is commented out of `requirements.txt`
(line 12). When the package is absent the embedding layer logs a warning and
falls back to lexical-only retrieval without crashing. A PyPI install of the
MCP server takes that path permanently, since the wheel carries no vector
files.

Enabling them costs a full corpus encode (documented in
`config/retrieval-config.yaml` as 2:20 on an M-series CPU for a 126,618-chunk
corpus, and noted in `requirements.txt` as 2 to 3 hours on CPU generally) plus
about 50 ms per query once warm.

The benefit is contested and you should know both numbers. The benchmark
recorded in `config/retrieval-config.yaml`, **dated 2026-05-09**, measured
+1.8pp Hit@3 on 1,418 generated natural-language queries, no movement on 1,285
author-curated triggers, and no movement on 71 realistic phrasings. A
**2026-07-31** re-measurement over 400 fixtures found *no difference at all*:
lexical-only, skill-vector and full chunk-vector modes each scored 95.5% Hit@1
and 99.8% Hit@3. On the current corpus the 535 MB `embeddings.jsonl` and the
fastembed dependency are not buying measurable accuracy. Treat them as
optional and measure before paying for the encode.

## Is anything here deploying to my org?

No. Nothing in this repository pushes metadata, runs anonymous Apex, or
performs DML. The org-facing MCP tools are read-only by construction and carry
MCP annotations saying so. Runtime agents are contractually forbidden from
deploying and from writing outside paths you supply.

## How do I know a claim in a skill is true?

Every skill package carries an `## Official Sources Used` section in its
`references/well-architected.md`, and the source-trust rules are defined in
`standards/source-hierarchy.md`: official Salesforce documentation outranks
Trailhead and Architects material, which outranks community writing. Search
results also return the relevant official sources alongside the skills, so you
can check the platform claim without leaving the terminal.

The honest limit: source *grading* is enforced structurally, but the golden
output-quality evals under `evals/golden/` are not wired into CI, so they
gate nothing today. See [positioning.md](positioning.md).

## Where do I report a skill that is wrong or missing?

[../CONTRIBUTING.md](../CONTRIBUTING.md) covers adding a skill, fixing one,
reporting a gap and flagging stale content. Before claiming a topic is
missing, search for it — the corpus is large enough that most "missing" topics
exist under a different name.
