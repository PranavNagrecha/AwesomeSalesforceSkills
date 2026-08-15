# Positioning

What this project claims, who it claims it for, and what it has to stop saying.
Every figure below was measured in-repo on **2026-08-15** with the command shown
beside it. Re-run the command rather than quoting the prose — several numbers on
this page have been wrong before, and every one of them moves.

---

## Positioning Statement

SfSkills gives an AI coding assistant the working knowledge a senior Salesforce
practitioner brings to a task: the platform's non-obvious failure modes, the
specific wrong code an LLM reliably generates and must refuse, a named official
source behind every package, and a read-only path into the user's live org. The
aim is guidance that survives contact with governor limits, sharing rules, and
an org's existing metadata — not merely code that compiles.

The count of skills is inventory, not the value proposition. The value
proposition is that on any one task the assistant behaves like someone who has
been burned by that task before.

---

## Audience Segments

**1. The solo Salesforce developer working in Claude Code or Cursor.**
Pain: the model writes plausible Apex that dies at 200 records, and they only
find out in a sandbox deploy. Entry point: install the plugin
(`/plugin marketplace add PranavNagrecha/AwesomeSalesforceSkills`, then
`/plugin install sfskills@sfskills`) and ask for the work normally. No Python,
no index build. Building the index is optional and buys the search CLI — see
[`../README.md`](../README.md).

**2. The consulting-partner delivery team.**
Pain: five consultants, five house styles, and a client who reviews every class.
Entry point: the run-time agents as slash commands — `/refactor-apex`,
`/gen-tests`, `/scan-security`, `/score-deployment` — each of which cites the
skills and templates it used, so a reviewer can audit the reasoning rather than
re-derive it. Roster:
[`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md).

**3. The in-house admin + developer pair with one org they cannot break.**
Pain: "does this validation rule / permission set / flow already exist?" is a
20-minute Setup crawl every time. Entry point: the MCP server
(`mcp/sfskills-mcp/`) — the assistant answers from the org's own metadata via
the `sf` CLI session.

**4. The AI-tooling builder wiring Salesforce into an agent.**
Pain: they need Salesforce domain grounding as a component, not a workflow.
Entry point: `pip install sfskills-mcp`
([PyPI](https://pypi.org/project/sfskills-mcp/)) and call `search_skill` /
`get_skill` / `suggest_agent` from their own orchestrator.

⚠ **This path is broken today and should not be advertised until it is fixed.**
The wheel ships ~50 KB of Python and no data; `sfskills-mcp-init` is supposed to
fetch the bundle from a GitHub Release, and there are zero releases:

```bash
gh api repos/PranavNagrecha/AwesomeSalesforceSkills/releases --jq 'length'   # -> 0
curl -sL -o /dev/null -w "%{http_code}\n" \
  https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
# -> 404
```

The documented fallback still works — clone the repo and point
`SFSKILLS_REPO_ROOT` at it (`paths.repo_root()` honours the env var) — but that
is the *developer* install, not the "just pip install it" pitch. Cutting the
v1.0.0 release described in [go-to-market.md](./go-to-market.md#step-0--github-hygiene-do-this-first-it-takes-an-hour)
is the prerequisite for making this segment's entry point true.

---

## Three Claims We Can Defend

### Claim 1 — It encodes the mistakes, not just the material

The differentiator is negative knowledge: a catalogue of what the model gets
wrong and why, per topic. Every skill package carries a
`references/llm-anti-patterns.md` listing concrete wrong outputs with the correct
pattern and a detection hint. The validator makes the file mandatory
(`pipelines/validators.py:283`, ERROR) and warns below five entries
(`:297`).

Evidence — 1,027 of 1,027 packages have one:

```bash
python3 -c "import pathlib; p=list(pathlib.Path('skills').glob('*/*/SKILL.md')); \
print(sum((s.parent/'references/llm-anti-patterns.md').is_file() for s in p), 'of', len(p))"
# -> 1027 of 1027
```

Worked example:
[`skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md`](../skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md)
— Anti-Pattern 2, "Using System.runAs() in Production Code to Avoid Mixed DML",
catches the exact over-generalisation an LLM makes from test-class examples in
its training data, and ships the detection hint alongside it: "`System.runAs`
appearing in a class that is not annotated with `@IsTest` and not inside a test
method."

**Scope of the claim.** This says the catalogue exists and is complete across the
corpus. It does not say the catalogue has been shown to change model output —
there is no with-library / without-library comparison in this repo. Do not
present it as one.

### Claim 2 — Every package names its official sources, and three harnesses check the library against a real org

*Source grounding, precisely.* Every package carries a non-empty
`## Official Sources Used` block in `references/well-architected.md`, guarded by
two ERROR gates (`pipelines/validators.py:351` and `:357`) and holding 5,748
salesforce.com documentation URLs across the corpus. The trust ladder those
sources are ranked on is
[`standards/source-hierarchy.md`](../standards/source-hierarchy.md): official
Salesforce docs outrank Trailhead and the Architects blog, which outrank
community writing, which outranks forum signal.

```bash
python3 -c "
import pathlib,re
wa=list(pathlib.Path('skills').glob('*/*/references/well-architected.md'))
print(sum('## Official Sources Used' in f.read_text() for f in wa), 'of', len(wa))
print(sum(len(re.findall(r'https?://(?:developer|help|architect)\.salesforce\.com', f.read_text())) for f in wa), 'salesforce.com URLs')"
# -> 1027 of 1027
# -> 5748 salesforce.com URLs
```

*The gap in that claim, stated plainly.*
[`standards/skill-content-contract.md`](../standards/skill-content-contract.md)
asks for more than this: an inline `[T1]` / `[T2]` / `[T3: source-name]` tag on
every factual claim. Nothing in the corpus carries one and no validator gate
checks for it.

```bash
python3 -c "
import pathlib,re
md=list(pathlib.Path('skills').glob('*/*/**/*.md'))
print(sum(1 for f in md if re.search(r'\[T[1234][\]:]', f.read_text())), 'of', len(md))"
# -> 0 of 6176
```

Twenty-six `well-architected.md` files also name their sources in prose with no
URL, which the contract forbids and no gate catches. So the defensible sentence
is "every package names its official sources"; the sentence "every claim is
graded per tier" is **not** currently true and should not be used.

*Live-org checking.* Three harnesses run against a real Salesforce org and write
dated reports into `docs/validation/`:

| Harness | Latest report | Result, verbatim from the report |
|---|---|---|
| `scripts/validate_probes_against_org.py` | [`probe_report_2026-04-17.md`](./validation/probe_report_2026-04-17.md) | "Total queries tested: 21 · Passed: 21 · Failed: 0" |
| `scripts/smoke_test_agents.py` | [`agent_smoke_rollup_2026-04-19.md`](./validation/agent_smoke_rollup_2026-04-19.md) | "Total agents tested: 42 · Passed: 42 · Failed: 0" — the roster was 42 active run-time agents then and is 48 now, so 6 agents are uncovered |
| `scripts/validate_skill_factuality.py` | [`skill_factuality_2026-04-17.md`](./validation/skill_factuality_2026-04-17.md) | "Sample size: 100 · testable: 32 · with wrong claims: 0" |

Read the factuality result carefully before repeating it. Its own methodology
note says it extracts `SObject.Field` references and verifies them against the
org's describe output — and across the 30 skills it itemises, **7 claims in
total** were actually verified; 26 of the 30 had zero verifiable field
references. "0 wrong claims" is therefore a very small sample of a narrow claim
type, not a clean bill of health for 100 skills.

Output quality has a separate harness: golden P0 cases with assertions, rubrics,
and reference answers under `evals/golden/` (10 flagship skills × 3 cases).

*The honest boundary.* The eval **structure** lint does gate CI now
(`.github/workflows/validate.yml:202`), which is a lint, not a model run — it
proves the files are well-formed, not that any output is good. And the scheduled
`org-validation` workflow has run exactly once, on 2026-08-10, failing all three
layers at `Authenticate to validation org` because `SFDX_AUTH_URL` is unset. The
April reports are real and re-runnable; nothing is keeping them fresh.

### Claim 3 — It can interrogate the user's own org, not just recite the platform

Most Salesforce advice is wrong for a given org because it ignores what the org
already contains. The MCP server closes that: 38 tools spanning library
retrieval (`search_skill`, `get_skill`, `get_agent`, `search_decision_trees`)
and live-org metadata (`list_validation_rules`, `describe_permission_set`,
`list_flows_on_object`, `validate_against_org`, `tooling_query`), authenticated
through the user's existing `sf` CLI session — the server never prompts for,
stores, or transmits a credential of its own.

Evidence — the tool count is derived, not asserted:

```bash
grep -c '@mcp.tool' mcp/sfskills-mcp/src/sfskills_mcp/server.py   # -> 38
```

`scripts/check_doc_counts.py` derives the same number from that source and fails
the build if any doc quotes a different one.

**Say "read-only" precisely.** The 38 tools split 24 org-read
(`_ANN_ORG_READ`), 13 repo-only (`_ANN_REPO_ONLY`) and 1 write
(`_ANN_ENVELOPE`). The first two annotations set `readOnlyHint=True`; the
exception is `emit_envelope`, which writes the report pair into `docs/reports/`
on the local disk and is annotated `readOnlyHint=False` accordingly. So "38
read-only tools" is the wrong phrasing. "Nothing this server does can change
your org" is the right one — no tool issues DML or metadata deploys, and
`tooling_query` is guarded by a DML blocklist
(`tests/test_tooling_query_blocklist.py`).

```bash
python3 -c "
import re,pathlib,collections
t=pathlib.Path('mcp/sfskills-mcp/src/sfskills_mcp/server.py').read_text()
print(collections.Counter(m.group(2) for m in re.finditer(r'@mcp\.tool\(\s*name=\"(\w+)\",\s*annotations=(\w+)', t)))"
# -> Counter({'_ANN_ORG_READ': 24, '_ANN_REPO_ONLY': 13, '_ANN_ENVELOPE': 1})
```

Access tokens *do* pass through the process — `sf org display --json` returns
one — which is why `sf_cli.py` carries an explicit redaction layer with 20 tests
behind it (`python3 -m unittest tests.test_sf_cli_redaction` → "Ran 20 tests …
OK"). The honest claim is "tokens are redacted before anything is returned", not
"no credential enters the process".

**Versions.** PyPI has exactly one release, `sfskills-mcp` **0.4.6**. The
in-tree version is **0.4.7** and is not published yet — `pyproject.toml` and
`src/sfskills_mcp/__init__.py` both read `0.4.7`, and the newest tag is
`mcp-v0.4.6`.

```bash
curl -s https://pypi.org/pypi/sfskills-mcp/json \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['info']['version'], sorted(d['releases']))"
# -> 0.4.6 ['0.4.6']
git tag | tail -1        # -> mcp-v0.4.6
```

---

## Claims We Must Stop Making

- **"1,027 skills" as the headline.** A volume number invites exactly the wrong
  inference — "the model already knows Salesforce, why would I need 1,027
  files?" — and it is unfalsifiable as a quality signal. It is also
  self-defeating on the technical side: those descriptions total **517,654
  characters**, so the catalogue physically cannot be loaded as a flat skill set,
  which is why the plugin ships 12 routers totalling 7,361 characters of
  description instead. Lead with one anti-pattern the reader recognises.
  (`python3 -c "import json;d=json.load(open('registry/skills.json'));print(sum(len(s.get('description','')) for s in d['skills']))"` → 517654)

- **Any aspirational "+" count.** None are verifiable by a reader, and the
  GitHub repository description is still stale in both directions — it says
  "982+ skills" against a registry of 1,027, and "75 agents" against a roster of
  76. A number that is both stale and inflated costs more credibility than it
  buys attention. Quote the derived figure or no figure.

  ```bash
  gh api repos/PranavNagrecha/AwesomeSalesforceSkills --jq .description
  # -> Open-source Salesforce knowledge layer for AI coding assistants. 982+
  #    source-grounded skills, 75 agents, 38-tool MCP server with live-org
  #    metadata. pip install sfskills-mcp.
  ```

- **"76 agents" as a capability claim.** 14 are deprecated redirect stubs and 14
  are build-time agents that maintain the library rather than doing user work,
  so the headline overstates the user-facing surface by more than a third — 48
  do user work. Describe the run-time tiers by what they do; if a number is
  unavoidable, re-derive it with `python3 scripts/check_doc_counts.py` rather
  than hand-typing one. (That script prints: "1027 skills, 48 active runtime +
  14 build + 14 deprecated = 76 agents, 38 MCP tools.")

- **"Golden evals prove output quality."** The `evals` CI job runs
  `run_evals.py --structure` and `run_agent_evals.py --structure`. Both are
  *structure lints* — they check that the eval files are well-formed. No model
  is invoked and no assertion is evaluated against real output. Say "we wrote
  assertions for the flagship skills and CI keeps the files well-formed", not
  "output quality is guaranteed".

- **"Every claim is graded against a source tier."** See Claim 2 — the tier tags
  do not exist in the corpus. Say "every package names its official sources".

- **"Every probe, agent, and skill is verified against a live org."** The
  harnesses are real, but the last reports are from April 2026, the factuality
  sample verified 7 claims, the smoke run covered 42 agents rather than the
  48-agent roster, and the workflow meant to keep this current has one run and
  it failed at authentication. The defensible version is "three re-runnable
  harnesses, with the dated reports in the repo".

- **"You need to build an index before it works."** Backwards. Reaching a skill
  needs no build step: the model reads the router descriptions and one domain
  roster, both of which are plain files on the default branch.
  `pip install -r requirements.txt` and `python3 scripts/build_index.py` buy the
  *second and third* ways in — the MCP `search_skill` tool and
  `scripts/search_knowledge.py`. Skip them and `search_knowledge.py` answers
  `Coverage: NONE` to every query rather than erroring, which looks like an empty
  library; it is a missing index.

- **"One command and a stranger has it."** Narrowly overclaiming.
  `.claude-plugin/plugin.json` and `marketplace.json` are on the default branch
  (`git ls-tree origin/main .claude-plugin/`), so
  `/plugin marketplace add PranavNagrecha/AwesomeSalesforceSkills` does work.
  What is missing is *discovery*: nothing has been accepted by any third-party
  plugin directory (<https://code.claude.com/docs/en/plugin-marketplaces>), and
  the MCP registry returns zero results for `sfskills`, so nobody finds it
  without being told the repo name.

---

*Verified 2026-08-15 against the working tree on branch
`overhaul/2026-08-01-checkpoint`.*
