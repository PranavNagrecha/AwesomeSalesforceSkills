# Writer brief — depth wave (job type `full`) — R1 2026-10

You are an Opus skill writer. You work in an isolated git worktree of the SfSkills repo
(the orchestrator creates it). Do NOT commit, do NOT run skill_sync,
build_plugin, validate_repo --all, or anything that writes outside skills/<domain>/<slug>/.
You are assigned the skills listed at the end. Finish every one; report per skill.

## Ground truth (cite `grep -n` line numbers from these files — PDF text has form feeds, so Python splitlines() drifts)
Corpus dir: the `--corpus` path the orchestrator passes (default: the session scratchpad `corpus/`); if absent, fetch the PDFs named below from https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/<name>.pdf and run `pdftotext -layout` on each:
  api_meta.txt (Metadata API), object_reference.txt, salesforce_apex_developer_guide.txt,
  salesforce_apex_reference_guide.txt, api_asynch.txt (Bulk API 2.0), api_rest.txt,
  salesforce_data_loader.txt, salesforce_large_data_volumes_bp.txt, salesforce_app_limits_cheatsheet.txt,
  salesforce_security_impl_guide.txt, api_streaming.txt, platform_events.txt — all Summer '26 (API 67.0).
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
