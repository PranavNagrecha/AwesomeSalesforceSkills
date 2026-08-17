# SfSkills — Salesforce AI Skill Library

Make your AI coding assistant behave like a senior Salesforce practitioner on
the task in front of it: knowing the platform's non-obvious failure modes,
refusing the specific wrong code an LLM reliably produces, grounding every
claim in official Salesforce documentation, and — through the MCP server —
asking your actual org whether the thing already exists.

[![Validate](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/actions/workflows/validate.yml/badge.svg)](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/actions/workflows/validate.yml)
[![PR Lint](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/actions/workflows/pr-lint.yml/badge.svg)](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/actions/workflows/pr-lint.yml)
[![License: PolyForm Small Business](https://img.shields.io/badge/License-PolyForm_Small_Business_1.0.0-orange.svg)](./LICENSE)

---

## The problem

A general-purpose model has read enormous amounts of Salesforce code, and a
lot of it is wrong in ways that only surface in production. The output
compiles, passes review, and then hits a governor limit, a mixed-DML boundary,
or a sharing rule nobody modelled. The failure mode is not that the model
lacks syntax — it is that the model has no working theory of the platform's
constraints, so it confidently generalises a test-only idiom into production
code.

## Concretely

<!-- anti-pattern-source: skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md -->

Ask a model to create an Account and a User in one service method and it
writes this:

```apex
public class AccountService {
    public static void createAccountAndUser(String name, String email) {
        Account acc = new Account(Name = name);
        insert acc;
        System.runAs(new User(Id = UserInfo.getUserId())) {
            User u = new User(/* fields */);
            insert u;
        }
    }
}
```

With this library loaded, it writes this instead:

```apex
public class AccountService {
    public static void createAccountAndUser(String name, String email) {
        Account acc = new Account(Name = name);
        insert acc;
        UserCreationService.createUserAsync(acc.Id, email);
    }
}

public class UserCreationService {
    @future
    public static void createUserAsync(Id accountId, String email) {
        User u = new User(/* fields */);
        insert u;
    }
}
```

The rule the first version violates: `User` is a setup object and `Account` is
not, so DML against both inside one transaction throws
`MIXED_DML_OPERATION`. `System.runAs()` relaxes that restriction *in test
context only* — in production Apex it is not a fix, it is a bug that compiles.
The model reaches for it because its training data is full of test classes.
([Apex Developer Guide — sObjects That Cannot Be Used Together in DML
Operations](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_non_mix_sobjects.htm))

Both snippets above are lifted verbatim from
[`skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md`](./skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md).
All 1,034 skill packages ship a `references/llm-anti-patterns.md` in that same
shape: the wrong output, why the model produces it, the correct pattern, and a
detection hint.

---

## Install

Full setup reference, with captured transcripts and every flag:
[`docs/installing.md`](./docs/installing.md).

### 1. Clone it and start asking — no build step

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
```

Open that directory in Claude Code and ask a Salesforce question. That is the
whole setup for the main path.

A clone carries everything the AI needs to find a skill. On `origin/main`,
`git ls-tree -r --name-only origin/main` counts `CLAUDE.md`, **12 router
skills** under `.claude/skills/` (one top-level `salesforce` router plus 11
domain routers), their **11 rosters**, and **48 run-time agent loaders** under
`.claude/agents/`.

Selection is model-driven, not search-driven. Claude reads the router
descriptions, hands off to one domain router, opens that router's
`references/skill-index.md` — a roster of that domain's packages, one gloss
each, budgeted at 220 characters (`scripts/build_plugin.py:281`) — and opens
the package it picks. Eleven rosters, 1,034 glosses between them; Claude reads
one. No index is consulted and nothing is built.

That indirection is the whole design. Exporting all 1,034 skill descriptions
flat would cost about **138,694 tokens** at session start, before you type
anything. Everything actually loaded up front — 12 routers, 67 commands and 48
agent loaders — costs **5,490**, or **4.0%** of that
(`python3 scripts/build_plugin.py --measure`). The token model is an estimate,
calibrated against a real Claude Code install; the method and its caveat are in
[`docs/architecture.md`](./docs/architecture.md#why-the-library-is-tiered).

Two things are *not* in a clone, because both are generated:
`.claude/commands/` (the 67 slash commands) and the retrieval index under
`vector_index/`. Step 2 builds both.

**As a Claude Code plugin** — namespaced skills plus the slash commands,
without adding this repo to your project:

```
/plugin marketplace add PranavNagrecha/AwesomeSalesforceSkills
/plugin install sfskills@sfskills
```

This works. The default branch carries the manifests and the payload they point
at: `git ls-tree origin/main .claude-plugin/` returns both `marketplace.json`
and `plugin.json`, both name the plugin `sfskills`, and both declare
`skills: ["./.claude/skills/"]` and `commands: ["./commands/"]` — directories
that exist on `origin/main`. A plugin install gives you routers and commands,
not the 48 agent loaders; those reach you only through a clone. Flags, the
local-path variant, and the measured token cost of an install:
[`docs/installing-the-plugin.md`](./docs/installing-the-plugin.md).

**For Cursor, Windsurf, Aider, Augment, or Codex CLI** — run
`python3 scripts/export_skills.py --target cursor` and copy the generated
`exports/cursor/.cursor/` directory into your project root (the export writes
one subdirectory per target, so copying `exports/` wholesale puts the rules in
the wrong place).

### 2. Optional — build the local index, for CLI and MCP search

```bash
python3 -m pip install -r requirements.txt
python3 scripts/bootstrap.py
python3 scripts/search_knowledge.py "trigger recursion"
```

The only entry under `Top skills:` should be
`apex/recursive-trigger-prevention`. The number beside it is a ranking output
that moves whenever the ranker is retuned — assert the skill id, never the
score.

This builds the FTS5 index behind the *keyword-search* way of finding a skill —
`search_knowledge.py`, the MCP `search_skill` tool, and the build-time agents
that maintain the library. `vector_index/` is gitignored, so a fresh clone has
no index at all: `git ls-files vector_index` returns three files
(`manifest.json`, `query-fixtures.json`, `query-variants.json`) and none of
them is the index. Skip this step and `search_knowledge.py` reports
`Coverage: NONE` for every query and still exits 0, which looks like an empty
library rather than a missing index. Skipping it does **not** stop Claude from
reaching a skill package through the routers above.

Bootstrap also installs the 67 slash commands into `.claude/commands/`; restart
Claude Code afterwards, since it loads commands at session start.

Cost: about **9 s** on a fresh `git clone --depth 1`, per the measurement
recorded in the script's own header (`scripts/bootstrap.py:20`, Apple silicon
macOS, Python 3.14.4). It writes two gitignored files, **307 MB** together on
this checkout — 127 MB of `chunks.jsonl` (135,409 chunks) and 179 MB of
`lexical.sqlite` (`du -h vector_index/*`). Those are one machine's numbers, not
a guarantee.

**Embeddings, stated precisely, because this repo has described them wrong
twice.** `config/retrieval-config.yaml` sets `embeddings.enabled: true`, but
`fastembed` is commented out at `requirements.txt:12`, so
`pipelines/embedding_backends.py` logs a warning and falls back to lexical-only.
They are neither "opt-in behind a flag" nor "on by default" — they are
**configured on and inert until you install a backend yourself**. Turning them
on is two steps, not one:

```bash
python3 -m pip install 'fastembed>=0.4,<1.0'
python3 scripts/build_skill_embeddings.py     # writes vector_index/skill_embeddings.jsonl
```

The second command is not optional and `bootstrap.py` does not run it.
`skill_embeddings.jsonl` is produced *only* by `scripts/build_skill_embeddings.py`
— one vector per skill, 1,027 lines, **5.0 MB** (`du -h`) — and it is the file both
`search_knowledge.py` and the MCP server actually read for vector signal.

A separate chunk-level file, `vector_index/embeddings.jsonl`, does exist in the
pipeline: `python3 scripts/bootstrap.py --with-embeddings` builds it, and its
own `--help` puts it at **+535 MB and hours of encode time**. It is absent from
this checkout, it is not what the numbers below measure, and you almost
certainly do not want it.

What the skill-level vectors buy, re-measured 2026-08-15 over 154 hand-written
held-out queries (`python3 evals/measurement/run_heldout.py --json`, versus
`--no-embeddings`):

| retrieval config | Hit@1 | Hit@3 |
|---|---:|---:|
| lexical-only | 39.0% | 48.7% |
| + skill vectors | **40.3%** | **53.9%** |

So +1.3pp Hit@1 and +5.2pp Hit@3, with a 0.0% `Coverage: NONE` rate either way.
An earlier re-measurement in this repo reported "no difference at all" and
concluded embeddings were not worth installing; that conclusion does not
survive the held-out set and is withdrawn. Both numbers describe *keyword
search*. They say nothing about the routing path in step 1, which is the one a
clone or plugin user actually exercises —
[`docs/architecture.md`](./docs/architecture.md) keeps the three mechanisms
apart and labels every accuracy figure with the one it measures.

> **Use `scripts/bootstrap.py`, not `scripts/build_index.py`.**
> `build_index.py` reaches the same retrieval outcome through
> `pipelines.sync_engine.write_state`, which rewrites every registry record. On
> a fresh clone with no embedding backend installed it nulls `vector_embedding`
> across all 1,027 records, leaving **1,029 modified tracked files** you then
> have to recognise as noise and discard (`scripts/bootstrap.py:33-36`).
> Bootstrap never calls `write_state`, so `git status` is clean when it
> finishes.

### 3. Optional — let the AI read your real org

```bash
python3 -m pip install -e mcp/sfskills-mcp   # published as sfskills-mcp on PyPI
sf org login web --alias my-dev              # auth stays in the sf CLI
```

### What to expect

All **1,034 of 1,034** skill packages are structurally complete — `SKILL.md`
plus all four `references/` files, re-verified 2026-08-15 by walking
`skills/*/*/`. Zero incomplete.

Routing is a different question, and it is honest to say it is imperfect. Which
package Claude opens is a model decision made from router descriptions and
one-line glosses, so it is probabilistic and it does miss.

The measurement worth quoting is **router accuracy: 88.3% → 96.1%** across a
2026-08-14 rewrite of the router descriptions — that is which of the 12 routers
gets opened, over 154 held-out queries, and it does not depend on any skill
label.

The measurement *not* worth quoting is the one this project published first. A
headline of "79.2% → 92.2% Hit@1" for which *package* got opened was refuted on
re-scoring: 41 of the baseline run's 43 misses had their expected label
rewritten to whatever that same baseline had picked, so the comparison was
circular, and exact-match scoring charges the router for the corpus's own
near-duplicate pairs (`security/mfa-enforcement-strategy` vs
`security/mfa-enforcement-patterns` is not a wrong answer). Re-scored against
one label set the direction inverts — 10 regressions, 0 improvements. **That
headline is retracted.** The full post-mortem, and the rule it produced —
never score a corpus change against labels derived from a run of that same
corpus — is in
[`evals/measurement/README-model-routing.md`](./evals/measurement/README-model-routing.md).

If Claude opens the wrong package, name the domain ("this is a sharing
question") or run `python3 scripts/search_knowledge.py "<your question>"` after
step 2.

---

## Why you can trust the output

- **Verified against a live org, in April 2026.** Three re-runnable harnesses:
  `scripts/validate_probes_against_org.py` (every probe's SOQL executes),
  `scripts/smoke_test_agents.py` (structural + dependency checks on the runtime
  agents), and `scripts/validate_skill_factuality.py` (samples skills and
  checks the field/object references actually exist). Say the date out loud:
  the last run was April 2026, and the factuality run sampled 100 skills when
  the corpus was smaller than it is now. The harnesses are current; re-run them
  against your own org rather than trusting a stale number. Index:
  [`docs/validation/README.md`](./docs/validation/README.md).
- **Output quality has golden cases — for a thin slice.** P0 cases with
  assertions, rubrics and reference answers live in `evals/golden/`; lint them
  with `python3 evals/scripts/run_evals.py --structure`. Coverage is 10 of
  1,027 packages (1.0%) across 4 of 11 domains — apex 4, integration 3, lwc 2,
  flow 1. `admin` is the largest domain at 253 skills and has zero, as do
  `data`, `security`, `devops`, `architect`, `agentforce` and `omnistudio`.
- **Every claim is source-graded.** A 4-tier trust ladder — official docs beat
  Trailhead/Architects beat community blogs beat forum signal — defined in
  [`standards/source-hierarchy.md`](./standards/source-hierarchy.md) and
  enforced by the content contract in
  [`standards/skill-content-contract.md`](./standards/skill-content-contract.md).
- **Structure is machine-checked.** `python3 scripts/validate_repo.py` must
  exit 0 on every change; the full gate list is in
  [`standards/validation-gates.md`](./standards/validation-gates.md). Agent
  validation alone reports `Validated 76 agent(s); 0 error(s)`.

Honest caveat, narrower than it used to be. Golden eval **structure** does gate
a merge now (`.github/workflows/validate.yml`, the `evals` job's *golden eval
structure* step), as do the 1,356 query fixtures inside the sharded validator
run, agent-eval structure, and CLI/MCP retrieval parity across all 154 held-out
queries (`.github/workflows/tests.yml`). What still gates nothing: eval
**output quality** — no workflow scores an answer against its rubric — and
neither retrieval benchmark, since `run_heldout.py`'s Hit@1/Hit@3 thresholds
are not referenced by any workflow and the model-routing benchmark needs live
agents to run at all. Nor is plugin drift gated: `build_plugin.py --check`
exists and passes (`OK: 121 plugin artifact(s) match a fresh build`), but
`grep -rn "build_plugin" .github/ .githooks/` returns nothing, so you have to
run it yourself.

---

## What's in it

**1,034 skills · 76 agents · shared Apex/LWC/Flow templates · golden evals · live-org MCP server.**

- **Skills** (`skills/`) — 1,034 structured guides across 11 domains: admin 253,
  apex 158, architect 104, data 101, lwc 82, devops 70, flow 63, integration
  61, agentforce 53, security 48, omnistudio 34. Each carries SKILL.md
  instructions, worked examples, gotchas, Well-Architected mapping, and the
  anti-pattern list shown above. Full catalog:
  [`docs/SKILLS.md`](./docs/SKILLS.md).
- **Shared canon** — `templates/` holds the one canonical TriggerHandler,
  ApplicationLogger, SecurityUtils, HttpClient, TestDataFactory, LWC skeleton,
  Flow fault path, and Agentforce action shell that every skill points at — 73
  files ([`templates/README.md`](./templates/README.md)).
  `standards/decision-trees/` holds seven trees — automation selection, flow
  pattern, Agentforce capability, async tier, integration pattern, sharing
  mechanism, performance tuning — consulted before any code gets written.
- **Agents** (`agents/`) — instruction files any agentic AI can follow.
  **Build-time (14)** maintain the library; **Run-time (48)** do real
  Salesforce work in your codebase or org, across four tiers —
  Developer + architecture tier (16), Admin accelerators — Tier 1 (14),
  Strategic — Tier 2 (7), Vertical + governance — Tier 3 (11). Fourteen more
  are deprecated redirect stubs, for 76 `AGENT.md` files in total. Contract:
  [`agents/_shared/AGENT_CONTRACT.md`](./agents/_shared/AGENT_CONTRACT.md);
  roster: [`agents/_shared/RUNTIME_VS_BUILD.md`](./agents/_shared/RUNTIME_VS_BUILD.md);
  skill map: [`agents/_shared/SKILL_MAP.md`](./agents/_shared/SKILL_MAP.md).
- **MCP server** (`mcp/sfskills-mcp/`) — 38 tools across skill / agent /
  template / decision-tree retrieval plus live-org metadata and read-only
  SOQL, so the agent can answer "does this already exist in my org?" without
  asking you.

Shipped in v1:

- [x] 1,034 skills across Admin, Apex, LWC, Flow, OmniStudio, Agentforce, Security, Integration, Data, Architect, DevOps
- [x] Shared Apex / LWC / Flow / Agentforce templates and seven decision trees
- [x] Golden evals for 10 flagship skills (3 P0 cases each)
- [x] MCP server on PyPI exposing the library plus live-org lookups

Queue for what comes next: [`BACKLOG.yaml`](./BACKLOG.yaml) ·
[`docs/queue-progress.md`](./docs/queue-progress.md).

---

## MCP server

38 tools, all read-only except `emit_envelope`, which writes a report file — the fifteen named here cover the usual paths:
`search_skill` (lexical search
over the 1,034-skill SfSkills corpus), `get_skill`, `get_agent`, `list_agents`,
`describe_org`, `list_custom_objects`, `list_flows_on_object`,
`list_validation_rules`, `list_permission_sets`, `describe_permission_set`,
`list_record_types`, `list_named_credentials`, `list_approval_processes`,
`validate_against_org`, and `tooling_query`.

That label needs one correction, since the annotations are checkable. The 38
registrations in `server.py` split 13 `_ANN_REPO_ONLY` + 24 `_ANN_ORG_READ` +
1 `_ANN_ENVELOPE`, so **37 carry `readOnlyHint: true` and one does not**:
`emit_envelope` writes a runtime agent's report to
`docs/reports/<agent>/<run_id>.json` and `.md`. Nothing writes to your org
under any tool. And "no secrets in output" is enforced rather than assumed —
`sf_cli.py` scrubs credential-shaped strings to `[REDACTED]` at two layers, on
both the success and the error path, with 20 tests behind it
(`tests/test_sf_cli_redaction.py`).

The server reports version **0.4.8** (`meta.health()` on this checkout).
The latest release on PyPI is 0.4.7 as of 2026-08-17, so a `pip install`
may trail the repo; `python3 -m pip show sfskills-mcp` tells you what you got.

Setup for Claude Code, Claude Desktop, Cursor, Windsurf, Zed, VS Code, Cline,
Continue, Codex CLI, Gemini CLI, Goose and the generic stdio transport:
[`mcp/sfskills-mcp/docs/CONNECT.md`](./mcp/sfskills-mcp/docs/CONNECT.md).
Tool schemas and design notes: [`mcp/sfskills-mcp/README.md`](./mcp/sfskills-mcp/README.md).

---

## More

- [`docs/installing.md`](./docs/installing.md) — canonical setup reference: the one bootstrap command, every flag, what a fresh clone does and does not contain, embeddings cost, MCP install paths
- [`docs/getting-started.md`](./docs/getting-started.md) — the three entry points, each with a verification step
- [`docs/installing-the-plugin.md`](./docs/installing-the-plugin.md) — install the library as a Claude Code plugin
- [`docs/README.md`](./docs/README.md) — documentation hub: getting started, architecture, FAQ, troubleshooting
- [`docs/installing-single-agents.md`](./docs/installing-single-agents.md) — ship one agent into another project
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — add a skill, fix a skill, report a gap, flag stale content

---

## License

SfSkills is **source-available**, not open source. Read it freely; whether you
may *use* it for free depends on how big your organisation is.

- **Free** — individuals, freelancers and consultants (including on billable
  client work), and any company with **fewer than 100 people and under USD 1M
  in prior-year revenue**.
- **Needs a commercial license** — everyone above either threshold, internal
  enterprise use included.

Governed by the [PolyForm Small Business License 1.0.0](./LICENSE)
(`PolyForm-Small-Business-1.0.0`). [`LICENSING.md`](./LICENSING.md) explains the
thresholds in plain English and how to buy a commercial license.

---

**Pranav Nagrecha** — Salesforce Technical Architect ·
[Issues](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/issues) ·
[License](./LICENSE) · [Commercial use](./LICENSING.md)
