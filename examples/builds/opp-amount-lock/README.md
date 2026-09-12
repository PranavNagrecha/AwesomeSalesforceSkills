# Worked example — lock Opportunity Amount after Closed Won (`scale: ask`, design-only)

A verbatim export of a `.sfskills/builds/<id>/` directory produced by the orchestration layer at its smallest
ceremony tier (`standards/build-orchestration.md` § 3.1). One-line requirement in, one deploy-ready step out,
three human decisions, four files read. Nothing here was deployed. Scenario 4 of the five-scenario definition of done;
`examples/builds/case-onboarding/` is the same loop at `scale: project`.

## Read in this order

1. `requirement.md` — the ask, one line.
2. `CLARIFICATIONS.md` — 13 questions harvested from the cited skills; 7 blocking answered by the requester, 6 defaults applied.
3. `RUN.md` — the one page the human reads at both gates: the step, its artefacts, every test with its exit code,
   defaults and answers, the manual UAT line, the gates, and the one command to run next (`scripts/mock_deploy.py`).
4. `PLAN.md` — 1 milestone, 1 step, 4 tests; `envelopes/plan/` and `envelopes/verification/` (one round, 10 warnings, 0 blockers).
5. `artefacts/M1-S01/` — the validation rule, its bypass custom permission and permission set, `package.xml` (67.0),
   `deploy-order.md`. The rule was rebuilt once: the plan's blank guard `NOT(ISBLANK(StageName))`, copied from the
   skill's own "GOOD" block, does not compile ("Field StageName is a picklist field…"); `NOT(ISBLANK(TEXT(StageName)))`
   validated 3/3 in the operator's dry run. The skill was corrected the same day (checker rule `VR-PICK-01`).
6. `tests/M1-S01/` — two checkers, xml, manifest; all pass.
7. `reports/MILESTONE-M1-REPORT.md` — the one-page verifier report (`ready-with-findings`, F-01..F-11) that the `accept` gate rests on.
8. `reports/drivers-log.md` — the human-experience record: questions, gates, files read, minutes, and the 22 product
   defects this run surfaced and fixed (CLI, agent playbooks, skills, contract).

## Gates

`go` (clarifications + plan) and `accept` (milestone M1) were approved by the requester via the dry-run operator so the
loop could be exercised end to end. Each record carries what was decided and what was knowingly accepted.

## Regenerate

`python3 scripts/build_plan.py export .sfskills/builds/opp-amount-lock/plan.json examples/builds/opp-amount-lock --force`
