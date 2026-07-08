# /onboard-source — Onboard any external source into the skill library

One entrypoint for turning outside knowledge into catalog-quality skills:

```
/onboard-source https://github.com/owner/repo      # a GitHub repository
/onboard-source /path/to/notes.md                  # an attachment (md/txt)
/onboard-source topic: "Data Cloud code extensions"  # a bare topic
```

This supersedes ad-hoc upstream pulls. `/sync-upstream-skills` remains the
weekly radar for `forcedotcom/sf-skills`; this command is the general case.

## Model policy (fixed by design — do not "upgrade")

The pipeline was designed once by Fable; at run time it uses **only**:

| Stage | Model | Why |
|---|---|---|
| Intake + triage | none (deterministic script) | evidence must not come from a model |
| Report load, docs verification, scaffolding | **Sonnet** | parallel retrieval + citation gathering; outputs are re-verified downstream |
| Gate, authoring, adversarial review, fixes | **Opus** | judgment and product-quality writing |

The workflow file pins these via per-agent `model:` overrides. Do not
substitute other models; do not add a planning stage.

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

## Pipeline

### Step 1 — Deterministic intake + triage (no LLM)

```bash
python3 scripts/onboard_source.py repo  https://github.com/owner/repo --write-manifest --update-backlog
python3 scripts/onboard_source.py file  /path/to/attachment.md        --update-backlog
python3 scripts/onboard_source.py topic "some salesforce capability"
```

- Discovers candidate topics (skill-shaped directories, markdown headings, or
  the topic itself) and runs each through `search_knowledge.py`, embedding the
  **verbatim top hits** and a NET_NEW / ENRICH / COVERED classification in
  `.intake-reports/<slug>-report.json` (gitignored — session artifact).
- `--write-manifest` (repo mode) writes the committed lockfile
  `config/upstream-sources/<slug>.manifest.json` for future delta runs.
- `--update-backlog` appends `RESEARCH` entries (and `DUPLICATE` for COVERED,
  with the search evidence in `notes:`) to `BACKLOG.yaml`. Regenerate the
  dashboard afterwards: `python3 scripts/generate_queue_dashboard.py`.

Deterministic evidence is the anti-fabrication backbone: agents downstream
*interpret* these scores; they may never assert local coverage themselves
(memory: delegated gap analysis has fabricated "no skill found" before).

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
- `.claude/workflows/source-onboarding.js` — the Sonnet/Opus workflow (step 2)
- `commands/sync-upstream-skills.md` — the sf-skills-specific weekly radar
- `commands/new-skill.md` — the authoring standard each build follows
- `BACKLOG.yaml` / `scripts/queue_reader.py` — candidate lifecycle
  (`RESEARCH` → `RESEARCHED` → `DONE`, `DUPLICATE` for covered)
