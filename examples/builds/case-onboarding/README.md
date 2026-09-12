# Worked example — Acme case intake (design-only build)

This directory is a verbatim export of a `.sfskills/builds/<id>/` build directory produced by the
orchestration layer described in `standards/build-orchestration.md`. Nothing here was deployed.

## Read in this order

1. `requirement.md` — the owner's input, verbatim.
2. `CLARIFICATIONS.md` + `answers-key.md` — 97 questions the cited skills said must be asked; the answers used.
3. `PLAN.md` (rendered from `plan.json`) — plan v5: 5 milestones, 22 steps, 130 acceptance tests.
4. `envelopes/plan/` and `envelopes/verification/` — five planner/verifier rounds; blockers 19 → 11 → 13 → 1 → 0.
5. `artefacts/<step>/` — the metadata each built step produced (M1: object model and layouts; M2: custom permission,
   permission sets, PSGs, profiles, queues, groups, sharing rule; M3: validation rules, email templates, Case settings
   with Email-to-Case / Web-to-Case, assignment + auto-response rules), plus each step's `deploy-order.md`.
6. `tests/<step>/` — every checker command run verbatim, with stdout/stderr/exit captured.
7. `workbook/`, `traceability.md9. `reports/MOCK-DEPLOY-M{1,2,3}.md` — `--dry-run` validations against a developer org, run by the operator between
   milestones. M1 run 1: 10/12 components pass, four platform rules no checker encoded (F-09..F-11). M2 run 3: 32/32.
   M3 run 5: 38/38 at API 67.0 after three more org-only rules (F-25 `systemUserEmail`, F-26 `newEntityRecordType`
   is API ≥ 64.0 and object-qualified, F-27 `casePriority` required per routing address); run 6 fails on one component
   only — the auto-response sender must exist as a verified org-wide address in the target org (F-28, a prerequisite).
   Every finding became a checker rule, a gotcha and an example in the cited skill, then the step was rebuilt and the
   org validated it. This is the loop finding its own gaps.

` — a `--dry-run` validation of M1 against a developer org: 10/12 components pass;
   the artefacts as built fail on four platform rules no checker encoded (F-09..F-11: required layout fields ContactId/Description/SuppliedEmail, Status must be Required, business-process fullName must equal the file stem); with those fixed in a scratch copy all 12 components validate. This is the loop finding its own gaps.

## Gates

G1 (clarifications), G2 (plan), every step gate through M2-S05 and milestones M1, M2 and M3 were approved by the
dry-run operator so the loop could be exercised end to end; each gate record carries the decisions taken. In a real build each is a human signature.

## Regenerate

`python3 scripts/build_plan.py export .sfskills/builds/case-onboarding/plan.json examples/builds/case-onboarding --force`
