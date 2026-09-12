# Traceability — REQ → step → artefact → test

Written by the build doc keeper.

| req_id | clarification_id | step_id | artefact_paths | test_result | status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 (Email the Account Owner, with Case Number and Subject, whenever a Case on that Account is escalated) | Q1, Q2, Q3, Q4, Q11, Q12 | M1-S01 | artefacts/M1-S01/flows/Case_Escalation_Notify_Account_Owner.flow-meta.xml \| artefacts/M1-S01/package.xml \| artefacts/M1-S01/deploy-order.md | xml: pass \| manifest: pass \| checker (check_record_triggered_flow_patterns.py): pass, exit 0 \| milestone M1 manual test: outstanding (observable only after deploy) | In UAT |

Coverage: 1 requirement, 1 step, 0 requirements with no step, 0 steps with no requirement, 1 manual test outstanding (M1's own, awaiting a post-deploy UAT pass).

Note (scale: feature — deliberate simplification): the full ten-section configuration workbook is not produced for this build. `standards/build-orchestration.md` § 3.1 marks the workbook **optional** at `scale: feature` (only `traceability.md` is required), and a ten-section workbook for a single Flow step would be mostly empty sections. This traceability row, `decisions.md`, and `PLAN.md` together carry the requirement-to-delivery join for this build.
