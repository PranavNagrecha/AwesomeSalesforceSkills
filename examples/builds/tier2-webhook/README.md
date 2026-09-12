# Worked example — Tier 2 escalation webhook and platform event (`scale: feature`, design-only)

A verbatim export of a `.sfskills/builds/<id>/` directory produced by the orchestration layer at its middle tier
(`standards/build-orchestration.md` § 3.1). One integration feature in, five deploy-ready steps out — object model
and platform event, Named/External Credential and permission set, the webhook Apex (trigger, service, Queueable +
Finalizer, tests), the hourly channel-health check, and the build-level manifest — six human decisions, four files read.
Nothing here was deployed. Scenario 2 of the five-scenario definition of done; `examples/builds/case-onboarding/` is the
same loop at `scale: project`, `examples/builds/opp-amount-lock/` at `scale: ask`.

## Read in this order

1. `requirement.md` — the ask.
2. `CLARIFICATIONS.md` — 45 questions from 8 skills and 2 decision trees; 24 blocking answered by the requester in one round.
3. `PLAN.md` — 1 milestone, 5 steps, 14 decisions; verified in two rounds (`envelopes/verification/`: 3 real refutations
   in round 1 — a missing field-level-security grant, an ungrounded queue lookup, a step with no test that could fail).
4. `artefacts/M1-S0[1-5]/` — the metadata and Apex, each step's `deploy-order.md`. Three steps were rebuilt after the org
   said no: the credential needed its header value (the clarifier had never asked the endpoint or the key parameter),
   the Apex used a method removed after API 58 and filtered a query on a long text area, and a template's hidden
   dependencies (a log object and two metadata types no step ships) blocked the builder until the plan dropped it.
5. `tests/<step>/` — every checker command run verbatim with its exit code.
6. `decisions.md`, `traceability.md` — 34 decisions, 16 requirement rows, 0 orphans.
7. `reports/MILESTONE-M1-REPORT.md` — the verifier's acceptance report (`ready-with-findings`, S2-F-06..10).
8. `reports/MOCK-DEPLOY-M1.md` — five org dry runs: run 1 found the credential defect, run 3 compiled the Apex and found
   two more, run 4 was 38/38, run 5 validated the merged manifest as one unit. The org is the only Apex compiler in the
   loop; every finding became a checker rule and a gotcha in the cited skill the same day.
9. `reports/drivers-log.md` — the human-experience record: 47 product defects surfaced and fixed during this run.

## Gates

`clarifications`, `step:M1-S02` (rejected and re-signed after an unasked fact surfaced), `plan` and `milestone:M1` were
approved by the requester via the dry-run operator so the loop could be exercised end to end.

## Regenerate

`python3 scripts/build_plan.py export .sfskills/builds/tier2-webhook/plan.json examples/builds/tier2-webhook --force`
