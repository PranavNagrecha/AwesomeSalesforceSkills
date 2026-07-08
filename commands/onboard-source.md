# /onboard-source — Onboard any external source into the skill library

One entrypoint for turning outside knowledge into catalog-quality skills:

```
/onboard-source https://github.com/owner/repo      # a GitHub repository
/onboard-source https://github.com/o/r/tree/<sha>/plugins/x/skills  # a subtree at a pinned ref
/onboard-source /path/to/notes.md                  # an attachment (md/txt)
/onboard-source https://example.com/article        # a web article (distill to headings first)
/onboard-source topic: "Data Cloud code extensions"  # a bare topic
```

This supersedes ad-hoc upstream pulls. `/sync-upstream-skills` remains the
weekly radar for `forcedotcom/sf-skills`; this command is the general case.

## Model policy (fixed by design — do not "upgrade")

The pipeline was designed once by Fable; at run time it uses **only**:

| Stage | Model | Why |
|---|---|---|
| Intake + triage | none (deterministic script) | evidence must not come from a model |
| Topic screening (large sources only) | **Haiku** | high-volume, near-binary classification of short strings; survivors are re-verified downstream |
| Report load, docs verification, scaffolding | **Sonnet** | parallel retrieval + citation gathering; outputs are re-verified downstream |
| Gate, authoring, adversarial review, fixes | **Opus** | judgment and product-quality writing |

The workflow file pins these via per-agent `model:` overrides. Do not
substitute other models; do not add a planning stage. Screening happens
*before* the workflow, never inside it.

## The license wall (decides everything downstream)

`scripts/onboard_source.py` classifies the source:

- **permissive** (MIT, Apache-2.0, BSD, ISC, CC0, Unlicense, 0BSD, Zlib):
  agents may READ the source for orientation. It is still not a source of
  truth — every Salesforce claim must be confirmed against official docs. If
  any expression (not just facts) is adapted, the author flags
  `attribution_required` and the PR body must credit the source.
- **clean-room** (everything else — GPL/AGPL, CC-BY-NC, MPL/LGPL/EPL,
  missing/NOASSERTION): topic radar ONLY. The intake script fetches file
  paths + blob SHAs, never contents; every downstream agent is forbidden
  from fetching the source. Skills are authored purely from official
  Salesforce docs.

When in doubt the script defaults to clean-room. Never weaken this gate.

Mode defaults and the `--license` flag:

- **repo**: the GitHub-detected SPDX id decides. `--license clean-room`
  tightens (e.g. an MIT fork whose upstream family is CC-BY-NC);
  `--license permissive` on a non-permissive repo is **refused**.
- **file / url**: default **clean-room** — unlicensed attachments and web
  articles are the common case. `--license permissive` records a
  user-attestation in the report when you actually hold the rights.
- **topic**: nothing to read, so license class is moot (permissive).

## Pipeline

### Step 1 — Deterministic intake + triage (no LLM)

```bash
python3 scripts/onboard_source.py repo  https://github.com/owner/repo --write-manifest --update-backlog
python3 scripts/onboard_source.py repo  https://github.com/o/r/tree/<sha>/plugins/x/skills   # ref+subpath parsed from tree URLs; or pass --ref/--subpath
python3 scripts/onboard_source.py file  /path/to/attachment.md        --update-backlog
python3 scripts/onboard_source.py url   /path/to/headings.md --source-url https://example.com/article
python3 scripts/onboard_source.py topic "some salesforce capability"
```

- Discovers candidate topics (skill-shaped directories, markdown headings, or
  the topic itself) and runs each through `search_knowledge.py`, embedding the
  **verbatim top hits** and a NET_NEW / ENRICH / COVERED classification in
  `.intake-reports/<slug>-report.json` (gitignored — session artifact).
- **url mode** is for web articles: fetching is out of scope for the stdlib
  script, so distill the article into a headings file yourself (one `#`-prefixed
  Salesforce-shaped topic per line) and pass the true origin via `--source-url`
  — the report then records the URL, not the scratchpad path.
- **Confluence spaces** have their own harvester so you don't hand-distill a
  wiki: `scripts/confluence_to_headings.py --base-url https://<site>.atlassian.net
  --space-key <KEY> --out <headings.md> --manifest <lock.json>`. It reads the
  public REST v2 API (anonymous; `CONFLUENCE_EMAIL` + `CONFLUENCE_API_TOKEN` for
  private spaces), emits **topic names only** — page titles plus H2/H3 headings,
  never body prose — and drops stubs, link-dumps, and third-party clippings
  (titles carrying a publisher attribution). Feed its output to `url` mode.
  A wiki still yields ~10x more raw headings than real topics (`Details`,
  `Setup`, `Notes`, vendor product names), so **screen the headings with a
  cheap-tier model before intake** — see "Screening a large source" below.
- File/url heading extraction **skips the document's first H1** and any heading
  matching the source slug — the title is a description of the source, not a
  capability, and produced a junk NET_NEW in every early production run.
- `--subpath` (or a `/tree/<ref>/<path>` URL) scopes repo discovery to one
  directory so monorepos don't flood BACKLOG with off-topic candidates;
  `--ref` pins a commit/tag. The manifest and report record both.
- `--write-manifest` (repo mode) writes the committed lockfile
  `config/upstream-sources/<slug>.manifest.json` for future delta runs.
- `--update-backlog` appends `RESEARCH` entries (and `DUPLICATE` for COVERED,
  with the search evidence in `notes:`) to `BACKLOG.yaml`. Regenerate the
  dashboard afterwards: `python3 scripts/generate_queue_dashboard.py`.

Deterministic evidence is the anti-fabrication backbone: agents downstream
*interpret* these scores; they may never assert local coverage themselves
(memory: delegated gap analysis has fabricated "no skill found" before).

### Step 1b — Screening a large source (Haiku, optional)

`onboard_source.py` truncates at `--max-candidates` (200). A repo subtree or a
wiki routinely yields ten times that, mostly document scaffolding and vendor
product names, and every junk candidate that reaches the report burns a Sonnet
verification slot. Before intake, screen the raw topic list with a **Haiku**
fan-out (batches of ~60, one agent each, agents write verdicts to disk and
return counts so the orchestrator's context stays clean). Tier each topic:

- `core` — a durable platform capability that could headline a skill
- `legacy` — a real Salesforce topic naming a retired product (Process Builder,
  MavensMate, Classic Console). Keep it, but order it *behind* `core`.
- `drop` — scaffolding, ISV product names, personal/event notes, blog titles

Then emit `core` first, `legacy` after. **Ordering is load-bearing**: the
workflow processes `actionable.slice(0, maxVerify)` from the front of the
report, so tier order decides what the expensive stages ever see.

A false `core` costs one research agent; a false `drop` costs one topic. Tell
the screener to prefer `drop` when unsure.

### Step 2 — The `source-onboarding` workflow (Sonnet + Opus)

Launch the workflow with the report path:

```
Workflow { scriptPath: ".claude/workflows/source-onboarding.js",
           args: { report: ".intake-reports/<slug>-report.json" } }
```

(`{ name: "source-onboarding" }` also works in sessions where the named-
workflow registry has picked the file up; `scriptPath` is always reliable.)

Optional args: `maxVerify` (default 12 candidates per run), `maxBuild`
(default 6 new skills per run). For a source with hundreds of candidates,
run in waves — the BACKLOG carries the remainder.

Waves need **one report each**. The workflow always takes the front of the
list (`actionable.slice(0, maxVerify)`), so re-running the same report
re-processes the same candidates. Shard the master report into
`.intake-reports/<slug>-wave-N-report.json` containing only candidates whose
BACKLOG entry is still `RESEARCH`; that status is both the progress ledger and
the loop's termination condition.

Two more optional args govern the license wall at the workflow level:

- `license_override: "clean-room"` — treat the source as clean-room even if
  the intake report says permissive (e.g. an MIT fork whose upstream family
  is CC-BY-NC). **Tighten-only**: any other value, including `"permissive"`,
  makes the workflow throw before a single agent runs — permissive status
  must come from the intake script's detected/attested license, never from
  a workflow arg.
- `license_note: "<why>"` — free-text provenance rationale; logged at launch
  and echoed in the returned result (and thus available for the PR body).

Inside the workflow (see `.claude/workflows/source-onboarding.js`):

1. **Load** (Sonnet, low): transcribes the intake report.
2. **Verify** (Sonnet fan-out): one fact sheet per NET_NEW/ENRICH candidate —
   official Salesforce docs only, every fact carries a fetched URL + quote;
   `is_real_capability=false` → DROP, never fabricate.
3. **Gate** (Opus, high effort): build/enrich/drop against the deterministic
   evidence. Must re-run `search_knowledge.py` itself for anything it wants
   to build and paste the verbatim output. Picks domain + slug + agent wiring
   (`--agent <id>` from `agents/`, or `--runtime-orphan --orphan-reason`).
4. **Scaffold** (Sonnet, serial): `new_skill.py <domain> <slug> --strict
   --assume-yes <wiring>` one at a time (AGENT.md edits are shared state; the
   `--strict` near-duplicate gate still hard-blocks — a blocked scaffold drops
   the item, it is never overridden).
5. **Author** (Opus, per skill): fills the scaffold (or weaves enrichment
   into the existing skill) from official docs, matching the house exemplar
   `skills/agentforce/agentforce-custom-lightning-types/`.
6. **Review** (Opus, high effort): adversarial fact-check — refute every
   claim against the cited docs; repo quality gates; license hygiene.
7. **Fix** (Opus): applies blocker fixes, re-reviewed output returns in the
   final result.

Agents never run `skill_sync.py`/`validate_repo.py` and never touch
`registry/`, `vector_index/`, `docs/` — shared generated artifacts are
synced once, sequentially, in Step 3.

### What a 2026-07-08 audit measured (read before trusting an enrich)

An independent pass re-checked 24 Fix-stage corrections nobody had reviewed.
All 24 were genuinely `RESOLVED`. But that same pass found **23 new blockers**
in the fixed text. **Single-pass adversarial review does not converge — it
samples.** A `PASS` verdict is not evidence a skill is correct.

The new blockers tracked how much text was added, not the topic:

| Change | Skills | New blockers |
|---|---|---|
| build (new skill, focused fact sheet) | 1 | 0 |
| enrich **with a ~40-line budget** | 2 | 0 |
| enrich with no budget (+145…+503 lines) | 6 | 22 |

About one fabricated blocker per 70–100 new lines: invented scratch-org
definition fields, invented metadata names, a refuted "GitHub only" product
claim propagated across three files. The fabrication is not the source's
fault — clean-room held — it is the model filling gaps from stale Salesforce
priors that an old topic name primes.

Therefore:

- **Give every enrich author an explicit line budget (~40 net new lines) and
  tell it why** — retrieval is a shared, zero-sum 30-chunk window, and volume
  predicts fabrication. Budgeted authors returned +33/+36 and zero blockers.
- **Prefer build over enrich.** A bad new skill is isolated and `--strict`
  gates it. A bad enrichment corrupts a skill that already worked.
- **Pin the enrich target** rather than letting the gate pick it. A gate-chosen
  target once routed an MFA release-notes topic into an incident-response skill.
- Treat one `PASS` as one sample. For anything you intend to keep, audit the
  fixes with an agent that never saw them.

### Step 3 — Ship (deterministic, orchestrator)

1. Append the returned `query_fixtures` to `vector_index/query-fixtures.json`.
2. `python3 scripts/skill_sync.py --skill skills/<domain>/<slug>` per touched skill.
3. `python3 scripts/validate_repo.py` and `python3 scripts/check_doc_counts.py`.
4. BACKLOG: `python3 scripts/queue_reader.py --set-status DONE --id <id>` for
   built/enriched ids; `--set-status DUPLICATE` (with evidence note) for gate
   drops; then `python3 scripts/generate_queue_dashboard.py`.
5. Commit skills + generated artifacts + manifest + BACKLOG on a
   `onboard-<slug>-<date>` branch; open a **draft** PR. Never auto-merge.
   PR body: official sources used, license class, and either the clean-room
   attestation ("no source prose read/copied") or the attribution block.

## Guarantees this process keeps

- **Search-first**: coverage evidence is generated deterministically before
  any agent runs (CLAUDE.md Required Workflow, step 1-2).
- **No near-duplicates**: `--strict` scaffolding is never overridden in
  non-interactive mode (`--assume-yes` aborts on near-duplicate warnings).
- **Official-source grounding**: verification, authoring, and review all
  require fetched official URLs; reviewers actively try to refute claims.
- **License hygiene**: clean-room vs permissive is decided by the script,
  not by an agent's judgment call.
- **Saturated-catalog honesty**: an empty build list is a valid, good
  outcome. Two real gaps beat ten duplicates.

## Related

- `scripts/onboard_source.py` — deterministic intake/triage (this pipeline's step 1)
- `scripts/confluence_to_headings.py` — Confluence space → headings file for `url` mode
- `.claude/workflows/source-onboarding.js` — the Sonnet/Opus workflow (step 2)
- `commands/sync-upstream-skills.md` — the sf-skills-specific weekly radar
- `commands/new-skill.md` — the authoring standard each build follows
- `BACKLOG.yaml` / `scripts/queue_reader.py` — candidate lifecycle
  (`RESEARCH` → `RESEARCHED` → `DONE`, `DUPLICATE` for covered)
