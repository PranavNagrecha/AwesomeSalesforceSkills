# Worked example — Acme case intake (design-only build, status `done`)

This directory is a verbatim export of a `.sfskills/builds/<id>/` build directory produced by the
orchestration layer described in `standards/build-orchestration.md`. Nothing here was deployed. It is
scenario 1 of the definition of done: the largest of the worked examples (project tier, 5 milestones,
22 steps, 13 gates), run before the ask/feature tiers existed — which is why it has 97 clarifications.

## Read in this order

1. `requirement.md` — the owner's input, verbatim.
2. `CLARIFICATIONS.md` + `answers-key.md` — 97 questions the cited skills said must be asked; the answers used; 25 deferred.
3. `PLAN.md` (rendered from `plan.json`) — plan v5: 5 milestones, 22 steps, 130 acceptance tests, 28 assumptions.
4. `envelopes/plan/` and `envelopes/verification/` — five planner/verifier rounds; blockers 19 → 11 → 13 → 1 → 0.
5. `artefacts/<step>/` — the metadata, Apex and documents each built step produced, plus each step's
   `deploy-order.md`. Two steps are blocked by design and ship nothing (M3-S05 Omni-Channel on deferred
   answers; M5-S02 sandbox strategy on inputs never supplied) — their reasons are in `PLAN.md`.
6. `tests/<step>/` — every checker command run verbatim, with stdout/stderr/exit captured.
7. `workbook/`, `traceability.md`, `decisions.md` — the doc-keeper's configuration workbook slices, RTM and
   decision log; `artefacts/M5-S04/` holds the compiled ten-section workbook, UAT pack, acceptance criteria and
   build-wide deploy order; `artefacts/M5-S05/package.xml` is the build-level manifest (29 types, 56 members).
8. `reports/MILESTONE-M1..M5-REPORT.md` — the milestone verifier's five acceptance reports (F-01..F-58).
9. `reports/MOCK-DEPLOY-M1..M5.md` — `--dry-run` validations against a developer org after every milestone.
   The final manifest-mode run of the whole build validates 60/60 components at API 67.0 except one named
   org prerequisite (a verified sender address, F-28). Every org rejection along the way (18 distinct) became
   a checker rule, gotcha or example in the library — this is the loop finding its own gaps.
10. `reports/drivers-log.md` — the operator's retrospective: cost, gates, what hurt, graded in five lines at the end.

## Gates

Thirteen gates — clarifications, plan, six step gates, five milestone gates — were approved by the dry-run
operator on the owner's standing instruction so the loop could be exercised end to end; each gate's notes
name the report it rests on and the findings it accepts knowingly. In a real build each is a human signature.

## Regenerate

`python3 scripts/build_plan.py export .sfskills/builds/case-onboarding/plan.json examples/builds/case-onboarding --force`
