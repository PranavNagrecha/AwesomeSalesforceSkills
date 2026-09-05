# Worked example — Acme case intake (design-only build)

This directory is a verbatim export of a `.sfskills/builds/<id>/` build directory produced by the
orchestration layer described in `standards/build-orchestration.md`. Nothing here was deployed.

## Read in this order

1. `requirement.md` — the owner's input, verbatim.
2. `CLARIFICATIONS.md` + `answers-key.md` — 97 questions the cited skills said must be asked; the answers used.
3. `PLAN.md` (rendered from `plan.json`) — plan v5: 5 milestones, 22 steps, 130 acceptance tests.
4. `envelopes/plan/` and `envelopes/verification/` — five planner/verifier rounds; blockers 19 → 11 → 13 → 1 → 0.
5. `artefacts/M1-S01/`, `artefacts/M1-S02/`, `artefacts/M2-S01/` — the metadata each built step produced, plus
   each step's `deploy-order.md`.
6. `tests/<step>/` — every checker command run verbatim, with stdout/stderr/exit captured.
7. `workbook/`, `traceability.md`, `decisions.md` — the doc-keeper's configuration workbook, RTM and decision log.
8. `reports/MILESTONE-M1-REPORT.md` — the milestone verifier's acceptance report (ready-with-findings, F-01..F-08).
9. `reports/MOCK-DEPLOY-M1.md` — a `--dry-run` validation of M1 against a developer org: 10/12 components pass;
   the artefacts as built fail on four platform rules no checker encoded (F-09..F-11: required layout fields ContactId/Description/SuppliedEmail, Status must be Required, business-process fullName must equal the file stem); with those fixed in a scratch copy all 12 components validate. This is the loop finding its own gaps.

## Gates

G1 (clarifications), G2 (plan), step:M1-S01, milestone:M1 and step:M2-S01 were approved by the dry-run operator
so the loop could be exercised end to end. In a real build each is a human signature.

## Regenerate

`python3 scripts/build_plan.py export .sfskills/builds/case-onboarding/plan.json examples/builds/case-onboarding --force`
