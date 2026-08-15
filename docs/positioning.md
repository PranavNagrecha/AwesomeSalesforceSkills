# Positioning

What this project claims, who it claims it for, and what it has to stop
saying. Every figure below was measured in-repo on **2026-07-31** with the
command shown beside it.

---

## Positioning Statement

SfSkills gives an AI coding assistant the working knowledge a senior
Salesforce practitioner brings to a task: the platform's non-obvious failure
modes, the specific wrong code an LLM reliably generates and must refuse, a
documented trust ladder behind every claim, and a read-only path into the
user's live org. The result is guidance that survives contact with governor
limits, sharing rules, and an org's existing metadata — not merely code that
compiles.

The count of skills is inventory, not the value proposition. The value
proposition is that on any one task the assistant behaves like someone who
has been burned by that task before.

---

## Audience Segments

**1. The solo Salesforce developer working in Claude Code or Cursor.**
Pain: the model writes plausible Apex that dies at 200 records, and they only
find out in a sandbox deploy. Entry point: clone the repo and open it — Claude
Code loads `CLAUDE.md` automatically — then ask for the work normally, or run
`python3 scripts/search_knowledge.py "trigger recursion"` to see what the
library already says (build the index first — see the install block in
[`../README.md`](../README.md)).

**2. The consulting-partner delivery team.**
Pain: five consultants, five house styles, and a client who reviews every
class. Entry point: the run-time agents as slash commands —
`/refactor-apex`, `/gen-tests`, `/scan-security`, `/score-deployment` — each
of which cites the skills and templates it used, so a reviewer can audit the
reasoning rather than re-derive it. Roster:
[`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md).

**3. The in-house admin + developer pair with one org they cannot break.**
Pain: "does this validation rule / permission set / flow already exist?" is a
20-minute Setup crawl every time. Entry point: the MCP server
(`mcp/sfskills-mcp/`) — the assistant answers from the org's own metadata via
the `sf` CLI session, read-only.

**4. The AI-tooling builder wiring Salesforce into an agent.**
Pain: they need Salesforce domain grounding as a component, not a workflow.
Entry point: `pip install sfskills-mcp`
([PyPI](https://pypi.org/project/sfskills-mcp/)) and call `search_skill` /
`get_skill` / `suggest_agent` from their own orchestrator.

---

## Three Claims We Can Defend

### Claim 1 — It encodes the mistakes, not just the material

The differentiator is negative knowledge: a catalogue of what the model gets
wrong and why, per topic. Every skill package carries a
`references/llm-anti-patterns.md` listing 5+ concrete wrong outputs with the
correct pattern and a detection hint.

Evidence — 1,027 of 1,027 packages have one:

```bash
python3 -c "import pathlib; p=list(pathlib.Path('skills').glob('*/*/SKILL.md')); \
print(sum((s.parent/'references/llm-anti-patterns.md').is_file() for s in p), 'of', len(p))"
# -> 1027 of 1027
```

Worked example:
[`skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md`](../skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md)
— Anti-Pattern 2 catches `System.runAs()` migrating from test classes into
production Apex, which is the exact over-generalisation an LLM makes from its
training data.

### Claim 2 — The guidance is graded against sources and checked against a real org

Two independent mechanisms, both inspectable.

*Source grading.* Every factual claim is tagged against a 4-tier ladder in
[`standards/source-hierarchy.md`](../standards/source-hierarchy.md); official
Salesforce documentation outranks Trailhead and the Architects blog, which
outrank community writing, which outranks forum signal. The content contract
in [`standards/skill-content-contract.md`](../standards/skill-content-contract.md)
makes the tag mandatory, and `python3 scripts/validate_repo.py` enforces the
structural half of it (gate list:
[`standards/validation-gates.md`](../standards/validation-gates.md)).

*Live-org checking.* Three harnesses run against a real Salesforce org and
write dated reports into `docs/validation/`:

| Harness | Latest report | Result |
|---|---|---|
| `scripts/validate_probes_against_org.py` | [`docs/validation/probe_report_2026-04-17.md`](./validation/probe_report_2026-04-17.md) | 21 probe queries executed, 21 passed |
| `scripts/smoke_test_agents.py` | [`docs/validation/agent_smoke_rollup_2026-04-19.md`](./validation/agent_smoke_rollup_2026-04-19.md) | 42 agents tested, 42 passed — the roster was 42 active run-time agents at that date; it is 48 now, so this report does not cover the 6 added since. Re-run to refresh. |
| `scripts/validate_skill_factuality.py` | [`docs/validation/skill_factuality_2026-04-17.md`](./validation/skill_factuality_2026-04-17.md) | 100-skill sample, 32 testable, 0 wrong claims |

Output quality has a separate harness: golden P0 cases with assertions,
rubrics, and reference answers under `evals/golden/` (10 flagship skills × 3
cases), lintable with `python3 evals/scripts/run_evals.py --structure`.

*The honest boundary:* the evals do not gate CI and the scheduled
`org-validation` workflow has never run — see
[`comparison.md`](./comparison.md#where-sfskills-is-weaker). The reports above
are real and re-runnable; they are not continuous.

### Claim 3 — It can interrogate the user's own org, not just recite the platform

Most Salesforce advice is wrong for a given org because it ignores what the
org already contains. The MCP server closes that: 38 read-only tools spanning
library retrieval (`search_skill`, `get_skill`, `get_agent`,
`search_decision_trees`) and live-org metadata (`list_validation_rules`,
`describe_permission_set`, `list_flows_on_object`, `validate_against_org`,
`tooling_query`), authenticated through the user's existing `sf` CLI session
so no credential ever enters the process.

Evidence — the tool count is derived, not asserted:

```bash
grep -c '@mcp.tool' mcp/sfskills-mcp/src/sfskills_mcp/server.py   # -> 38
```

`scripts/check_doc_counts.py` derives the same number from that source and
fails the build if any doc quotes a different one.

Shipping today as `sfskills-mcp` 0.4.6 on
[PyPI](https://pypi.org/project/sfskills-mcp/).

---

## Claims We Must Stop Making

- **"1,027 skills" as the headline.** A volume number invites exactly the
  wrong inference — "the model already knows Salesforce, why would I need
  1,027 files?" — and it is unfalsifiable as a quality signal. Worse, it is
  self-defeating on the technical side: those 1,027 descriptions total 509,800
  characters, roughly 127,000 tokens, so the catalogue physically cannot be
  loaded as a flat skill set. Lead with one anti-pattern the reader
  recognises. (`python3 -c "import json;d=json.load(open('registry/skills.json'));print(sum(len(s.get('description','')) for s in d['skills']))"` → 509800, 2026-07-31)
- **Any aspirational "+" count — "982+", "1097+ planned", "1119+ planned".**
  None of these are verifiable by a reader, and the GitHub repository
  description still says "982+" while the registry says 1,027
  (`gh api repos/PranavNagrecha/AwesomeSalesforceSkills --jq .description`,
  2026-07-31). A number that is both stale and inflated costs more credibility
  than it buys attention. Quote the derived figure or no figure.
- **"76 agents" as a capability claim.** 14 of them are deprecated redirect
  stubs and 14 are build-time agents that maintain the library rather than
  doing user work, so the headline overstates the user-facing surface by more
  than a third — 48 do user work. Describe the run-time tiers by what they
  do; if a number is
  unavoidable, re-derive it with `python3 scripts/check_doc_counts.py` rather
  than hand-typing one.
- **"Golden evals prove output quality."** The eval files exist and lint, but
  no workflow runs them: `grep -rn "run_evals" .github/workflows/ .githooks/`
  returns nothing (2026-07-31). They are a design artefact and a review aid,
  not a passing gate. Say "we wrote assertions for the flagship skills", not
  "output quality is guaranteed".
- **"Every probe, agent, and skill is verified against a live org."** The
  harnesses are real but the last reports are from April 2026, the factuality
  sample was 100 skills (the README claimed 200), the smoke run covered 42
  agents rather than the full run-time roster, and the scheduled
  `org-validation` workflow has zero runs
  (`gh run list --workflow=org-validation.yml --json conclusion` → `[]`,
  2026-07-31). The defensible version is "three re-runnable harnesses, with
  the dated reports in the repo".
- **"You need to build an index before it works."** Corrected 2026-08-14 — this
  claim was backwards. Reaching a skill needs no build step: Claude reads the
  router descriptions and one domain roster, both of which are plain files on
  the default branch. `pip install -r requirements.txt` and
  `python3 scripts/build_index.py` buy the *second and third* ways in —
  `scripts/search_knowledge.py` and the MCP `search_skill` tool. Skip them and
  `search_knowledge.py` answers `Coverage: NONE` to every query rather than
  erroring, which looks like an empty library; it is a missing index.
- **"One command and a stranger has it."** Still overclaiming, but narrowly.
  `.claude-plugin/plugin.json` and `marketplace.json` are on the default branch
  (`git ls-tree origin/main .claude-plugin/`), so
  `/plugin marketplace add PranavNagrecha/AwesomeSalesforceSkills` does work.
  What is missing is *discovery*: the plugin has not been submitted to or
  accepted by any third-party plugin directory
  (<https://code.claude.com/docs/en/plugin-marketplaces>), so nobody finds it
  without being told the repo name.

---

*Verified on 2026-07-31 against commit `14f9b2490`.*
