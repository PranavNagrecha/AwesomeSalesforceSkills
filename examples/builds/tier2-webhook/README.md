# Worked example — Tier 2 escalation webhook (feature tier, status `done`)

A verbatim export of a `.sfskills/builds/<id>/` build directory produced by the orchestration layer in
`standards/build-orchestration.md`. Nothing here was deployed. Scenario 2 of the definition of done: an
integration feature — external credential + named credential, a Case trigger, a webhook Queueable with
a finalizer, a platform event, an hourly channel-health Schedulable — sized `scale: feature`, 5 steps,
1 milestone, plan v2 after two verification rounds.

## Read in this order

1. `requirement.md`, then `CLARIFICATIONS.md` — the questions the cited skills said must be asked; 45 answered.
2. `PLAN.md` (rendered from `plan.json`) — five steps; `envelopes/verification/` — the two verifier rounds.
3. `artefacts/<step>/` — metadata and Apex per step with each step's `deploy-order.md`, which also carries every repair record (§ 0a–0f on M1-S03) as the build was reopened.
4. `tests/<step>/` — every checker run verbatim; `decisions.md`, `traceability.md` — the doc-keeper's records.
5. `reports/MOCK-DEPLOY-M1.md` — thirteen validate-only runs against a developer org. Runs 1–5 compiled the Apex; run 6 was the first with tests executing.
6. `reports/drivers-log.md` — the operator's log, closed twice: at the first acceptance and at the re-sign.

## Reopened and re-signed the same day (tests executing)

The first acceptance rested on compile-only Apex evidence: every dry run before run 6 carried
`runTestsEnabled: false`. Once `mock_deploy.py --test-level RunSpecifiedTests` existed, run 6 failed all
28 test methods, and six findings followed one layer at a time (runs 6–13): tests never ran as a
permissioned user; the shared factory populated a null lookup under the API 67.0 user-mode default; no
persona held Create on the platform event; the finalizer was uncovered; a re-enqueued job ran to its
designed failure; and the per-class 75% rule under `RunSpecifiedTests`. Each became a library rule or a
recorded decision, and the milestone was re-signed on run 13: the 35-member release package validates
in the org — 41/41 components, 37/37 tests, 89.9% coverage, no coverage warnings.

## Gates

Clarifications, plan, one step gate (rejected and re-approved after an amendment), and the milestone
(accepted, rejected, re-approved) — each signed by the dry-run operator on the owner's standing
instruction, with the run it rests on named in the notes. In a real build each is a human signature.

## Regenerate

`python3 scripts/build_plan.py export .sfskills/builds/tier2-webhook/plan.json examples/builds/tier2-webhook --force`
(the export replaces the folder; re-add this README afterwards — an `export` flag to preserve it is queued.)
