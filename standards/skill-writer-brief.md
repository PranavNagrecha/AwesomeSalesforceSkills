# Writer brief — depth wave (job type `full`) — R1 2026-10

You are an Opus skill writer. You work in an isolated git worktree of the SfSkills repo
(the orchestrator creates it). Do NOT commit, do NOT run skill_sync,
build_plugin, validate_repo --all, or anything that writes outside skills/<domain>/<slug>/.
You are assigned the skills listed at the end. Finish every one; report per skill.

## Ground truth (cite `grep -n` line numbers from these files — PDF text has form feeds, so Python splitlines() drifts)
Corpus dir: the `--corpus` path the orchestrator passes (default: the session scratchpad `corpus264/`, Winter '27 = release 264, API 68.0); if absent, fetch the PDFs named below from https://resources.docs.salesforce.com/264/latest/en-us/sfdc/pdf/<name>.pdf and run `pdftotext -layout` on each:
  api_meta.txt (Metadata API), object_reference.txt, salesforce_apex_developer_guide.txt,
  api_asynch.txt (Bulk API 2.0), api_rest.txt, api_streaming.txt, platform_events.txt,
  salesforce_data_loader.txt, salesforce_large_data_volumes_bp.txt, salesforce_app_limits_cheatsheet.txt,
  sfdx_dev.txt, pkg2_dev.txt — the 12 files in `corpus264/`, all Winter '27 (API 68.0).
Two guides are NOT published at 264 yet; use the Summer '26 (262, API 67.0) copies in the scratchpad `corpus/` (or .../262/latest/... in the URL above) and cite them as `262:`: salesforce_apex_reference_guide.txt, salesforce_security_impl_guide.txt.
Consult standards/release-delta-winter27.md before asserting any version gate.
Also fetchable with plain curl: developer.salesforce.com/docs/get_document_content/<deliverable>/<page>.htm/en-us/262.0 (JSON),
developer.salesforce.com/docs/platform/lwc/guide/<slug>.html, developer.salesforce.com/docs/ai/agentforce/**.
NOT corpus: help.salesforce.com (unfetchable), blogs, Trailhead, Component Library, npm READMEs, your memory.

## Order of work per skill
1. CLAIMS AUDIT FIRST. List every factual claim already in the package (limits, API names, metadata
   types/fields, behaviours, version gates). Grade each GROUNDED (file L<n>) / CONTRADICTED (file L<n>, what
   the doc actually says) / NOT FOUND. Correct CONTRADICTED claims in place. Keep NOT FOUND claims only
   with `UNVERIFIED (2026-10-19): <why it could not be grounded>` written INLINE beside the claim —
   never as a footnote or HTML comment, never dropped silently. Prefer replacing an unverifiable claim with a
   grounded one; when none exists, the marker is the honest outcome — a package whose count rises because you
   audited claims nobody had checked is better than one whose count stays at zero by assertion. Never mark a
   claim you did not audit.
2. Bring the package to the 12-signal bar (scripts/score_skill_depth.py; >= 10 required, 12 where the
   domain allows — architect/data analytical skills may legitimately have no XML fence; write
   "Not applicable" per standards/skill-authoring-style.md § 4 instead of inventing metadata):
   - `## Questions to Ask Before Configuring` in SKILL.md between `## Before Starting` and `## Core Concepts`,
     EXACT heading, table header row exactly `| Ask | Why it matters | What a good answer adds |`,
     7 rows, each row traceable to a gotcha; then one sentence on what a proper configuration adds over
     "just doing it". The requirements-clarifier agent harvests this table by heading and header row.
   - Skill-specific `## Recommended Workflow` (3–7 steps naming files, the checker, the tests).
   - Deployable artifact fence; XML fence for admin/flow (must parse: wrap fragments in a real root with
     an "excerpt" comment); apex fences brace-balance or are labelled excerpt.
   - references/gotchas.md: >= 5 `## Gotcha N: <title>` with What happens / When it occurs / How to avoid.
   - references/llm-anti-patterns.md: >= 5 `## Anti-pattern N:` (wrong output, why the model produces it, correct pattern, detection hint).
   - references/well-architected.md `## Official Sources Used`: >= 4 bullets, each naming the claim it supports and the file+line.
   - references/examples.md with a fenced artifact; one extra reference file (>= 500 bytes of real content:
     e.g. code-examples.md for apex/lwc, metadata-examples.md for admin/flow, worked-example.md otherwise).
   - Checker scripts/check_*.py: stdlib only; `--manifest-dir`; exit 1 on missing dir; WARN + exit 0 on empty;
     exit 1 on ERROR only; `--strict` promotes WARN; never `find(x) or find(y)` on ElementTree (leaf is falsy —
     use an `is not None` helper); at least one single-line `print("ERROR: …")` + `sys.exit(1)`. Test it on
     good/bad/empty/missing fixtures and on the skill's own extracted artifact.
   - Zero `TODO` in SKILL.md and references/.
   - Frontmatter: triggers >= 5, ADD-ONLY (never remove or reword an existing trigger — fixtures depend on them),
     verb-first natural phrasing; `salesforce-version` set from the guide you cited (e.g. "Summer '26+" only if
     the behaviour is Summer '26-specific; keep the floor otherwise, but the value must be one you verified);
     `version` bumped (minor); `updated: 2026-10-19`; description first sentence, name, category untouched.
   - Related Skills as `domain/slug` that resolve on disk (ls to check).
   - No >= 120-char paragraph duplicated between SKILL.md and references (chunk competition).
3. Run `python3 scripts/verify_skill_package.py skills/<domain>/<slug>` and your checker on /nonexistent and on an
   empty dir; fix until clean. Run `python3 scripts/score_skill_depth.py --domain <domain> --top 400 | grep <slug>`.

## Size discipline
A skill already at 8–9 gets a budgeted enrich (~40–80 net new lines); do not bulk a package for its own sake —
the lexical window is zero-sum and a bulked skill starves its neighbours.

## Report per skill (keep it to ~12 lines each)
slug · score before → after · claims audit counts (G/C/NF) · the CONTRADICTED claims you corrected (one line each,
with file L<n>) · UNVERIFIED before → after · salesforce-version set and why · checker fixtures results · anything
you could not ground or finish. End with the verbatim verify_skill_package line per skill.

## Job type `topup` (at-bar skill, score >= 10, missing the Questions table)
Same ground-truth and grounding rules as above, but the change is bounded: (1) add the
`## Questions to Ask Before Configuring` table in the exact format (7 rows, each traceable to an existing
gotcha — add a gotcha only if a question has none to trace to); (2) set `salesforce-version` from the guide you
cite for the skill's core claim, or leave it if nothing in the package is version-specific and say so;
(3) burn down `UNVERIFIED` markers where the corpus now grounds the claim; mark nothing new as UNVERIFIED unless
you also audited the claim. Budget: ≤ 40 net new lines per skill; no restructuring, no new reference files,
no trigger changes beyond add-only. Bump `version` (patch) and `updated`. Report per skill: rows added,
version decision and its citation, UNVERIFIED before → after.

## Job type `audit` (never-audited skill: no corpus cite, no UNVERIFIED marker)
Claims audit, not a rewrite. (1) List every factual claim in the package (limits, API names, metadata element
names and gates, behaviours, error texts, "removed/deprecated" statements) and check each against the corpus
with `grep -n`; (2) correct every CONTRADICTED claim in place with the cite, keeping the old figure only as
labelled history; (3) mark every claim the corpus does not hold `UNVERIFIED (YYYY-MM-DD)` inline — Help-only
figures, blog figures, product names with no Metadata API row; (4) add the Questions table only if
`verify_skill_package` FAILs without it (7 rows, traced to existing gotchas); replace template TODOs with the
package's own checklist text; re-point dead Related Skills to slugs that exist; (5) run the checker on
bad/good/empty/missing fixtures and report exit codes against the contract (ERROR findings exit 1 always;
WARN/REVIEW/INFO findings exit 0 unless `--strict`; empty dir one WARN exit 0; missing path ERROR exit 1) — fix the contract, never weaken a rule; (6) bump `version` (patch) and
`updated` (from `date`). Budget ≤ 60 net lines per skill. Report: claims audited G/C/NF, each CONTRADICTED
fix as file:line old → new + cite, UNVERIFIED added, checker table, verify line. Always followed by an
adversarial reviewer that opens every cite.

## Recipe that worked (measured 2026-10-19/20: 0/20 -> 20/20 and 5/10 -> 10/10 correct on probes the model cannot answer alone)
1. **Corpus first.** Every claim is checked against the official-guide text in `corpus264/` with `grep -n`; the cite is the line that carries the number or name. No corpus line, no assertion — `UNVERIFIED (date)` instead.
2. **Writer in a worktree, bounded job.** One writer, 9 skills, one job type from this brief, `git merge release/<ver>` first, no commits, ≤ budget lines. A writer never rewrites a skill that only needs a correction.
3. **Adversarial reviewer, always.** A second model opens EVERY cite the writer made, re-derives every number, greps the package for leftovers of the old claim, checks the Questions table header and traceability, runs the checker on bad/good/empty/missing fixtures, and adjudicates the contradictions the writer reported but left. Every one of 7 batches had reviewer-found defects; the reviewer is the quality lever, not optional.
4. **Orchestrator spot-check.** Before integrating, the orchestrator opens 2 cites or runs 2 fixtures itself. One wrong cite (L38771 for L38767) and one wrong brief sentence (heap "API 68.0+") were caught this way.
5. **Integrate by path, never by merge.** Review-commit in the worktree, remove the worktree, `git checkout <commit> -- skills/<d>/<s>`, `skill_sync --changed-only --skip-embeddings`, `validate_repo --changed-only`, commit by explicit path, push `--no-verify` (the hook rebuilds the wrong index), `release_plan.py set-status <item> running --done-skills`.
6. **Learn.** New defect classes go to `## Learned rules` below (orchestrator Step 3b). A root cause in a standard is fixed in the standard (release-delta §7 made four batches wrong).
7. **Measure.** Write one probe per corrected defect class (`evals/probes/*.json`: question, wrong_answer, correct_answer, source line, verbatim quote) and run `evals/scripts/run_lift.py --probes <file>` without and with the skill. A fix that does not move the probe is not a fix — and a fact that lives only in a reference file other than `llm-anti-patterns.md` does not reach the model.

## Reviewer brief (adversarial; the orchestrator passes this section's path to every reviewer)
You review one writer's uncommitted worktree. You may edit, you never commit. For every skill in the batch:
(1) open every corpus line the writer cited and confirm the text and the number support the sentence; a cite to a heading or a neighbouring row is a defect; (2) re-derive every arithmetic or worked example the writer changed; (3) grep the package for leftovers of every old claim the writer corrected (old number, old name, old line cite, the gate phrase) and judge each hit; (4) Questions table: exact header `| Ask | Why it matters | What a good answer adds |`, 5+ rows, each row traceable to a gotcha or section in the same package, no placeholders; (5) templates: no TODO, no invented commands; Related Skills resolve on disk and fit the topic; (6) checker on bad / good / empty / /nonexistent, default and `--strict`, against the contract (ERROR findings exit 1 always; WARN/REVIEW/INFO exit 0 unless --strict; empty one WARN exit 0; missing ERROR exit 1) — report drift, fix the contract, never weaken a rule; (7) adjudicate every "contradiction found but not fixed" the writer reported: ground it and fix it if it is inside the batch, else report it; (8) `verify_skill_package` no FAIL. Report per skill ≤ 5 lines (defects → fixed, file:line, cite), then totals: cites opened/confirmed, contradicted-and-fixed, newly UNVERIFIED, checker table, verify lines, `git status --short | wc -l`. Name every defect CLASS you found — the orchestrator appends new ones to Learned rules.

## Learned rules (append-only; one line per defect class a reviewer found; orchestrator Step 3b writes here)
- 2026-10-19 (R2-26 A/B): a gate wording in the writer brief propagates verbatim into every skill — state gates with the corpus line that proves them, never from the brief alone.
- 2026-10-20 (R3-05 A–D): a limit change is API-versioned ONLY if it appears in the guide's versioned-behaviour list (apexdev "Changes to Apex at API version N"); otherwise it is release-level and applies to every class. Example: Winter '27 heap 10/25 MB (L19780) is absent from the 68.0 list (L45116-45131) — never "API 68.0+".
- 2026-10-20 (R3-05 D): a cite must point at the line that carries the number or name; a cite to the section heading or a neighbouring row is a defect (L38771 vs L38767).
- 2026-10-20 (R3-05 F): "removed in API N" and "cannot be used at API N and later" are different claims — use the guide's words (WITH SECURITY_ENFORCED, L11926).
- 2026-10-20 (R3-05 F/H): delivery timing and limit context are independent — "runs asynchronously" does not imply async limits (PE triggers and CDC run on sync limits, pe L2338-2339); and "runs as Automated Process" is about the debug log, not the running user (pe L2190-2191).
- 2026-10-20 (R3-05 G/H): a comment or checker message that contradicts the corrected prose is a defect of the same weight as the prose — sweep scripts/ and templates/ in the same pass.
- 2026-10-20 (R3-05 H): test-context claims for platform APIs (ConnectApi SeeAllData, setTest*) come from the API's own test section, never from the generic mocking pattern.
- 2026-10-20 (R3-05, ext probes): a fact reaches the model only from SKILL.md or references/llm-anti-patterns.md (what run_lift feeds); a correction that lives only in another reference file does not change answers — put the one-line truth in SKILL.md too.
- 2026-10-20 (R2-31): two limits with the same number are not the same limit (QueryLocator 50M per job vs DailyAsyncApexExecutions 250k/24h); name the limit the guide names.
- 2026-10-20 (R2-33..36): every checker obeys one contract — findings exit 0 unless `--strict`, empty dir one WARN exit 0, missing path ERROR exit 1 — and a rule that flags the documented pattern (SeeAllData for ConnectApi) is removed, not softened.
- 2026-10-20 (R3-06 batch 1): the checker contract distinguishes severities — ERROR findings (schema breaks, a build-step gate artefact that is wrong) exit 1 always because build-loop gates depend on it; WARN/REVIEW/INFO exit 0 unless `--strict`. A brief sentence that said "findings exit 0" without the severity split made two agents disagree.
- 2026-10-20 (R3-06 batch 1): a checker rule can contradict the corpus just like prose (picklist checker flagged GVS-backed picklists as unrestricted; api_meta 264 L45920-45922 says they are restricted) — audit every rule's premise, not only its exit codes.
