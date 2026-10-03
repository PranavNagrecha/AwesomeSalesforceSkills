# Milestone M4 — verification report

Verifier: dry-run operator (Fable), 2026-10-02T21:00Z, following `agents/milestone-verifier/AGENT.md` Steps 1–11 directly. Design-only build; nothing deployed; no gate written by this report.

## Verdict: ready-with-findings

Every M4 step is `documented` on the final plan (M4-S03 re-compiled twice as the plan was corrected; M4-S04 built once). Both declared milestone checkers exit 0, the build-level manifest is consistent whole-tree, and the org validated the manifest's full member set by manifest (run 4) with the Apex tests proven separately (M3 run 5). Not "ready" because two runbook findings only a real deploy can settle (a partial object file that may replace the object definition; a stage mapping the answers denied), the report and dashboard can only validate after their type exists, and the Jest suite never ran.

## 1. Precondition
Gates plan, milestone:M1/M2/M3 approved; step:M4-S02 approved; milestone:M4 pending (first verification); four steps documented, none blocked.

## 2–3. Inventory and references
`artefacts/M4-S04/package.xml`: 23 types, 38 explicit members, version 62.0, no wildcards — the union of eleven step manifests plus M3-S03's five ApexClass members and M3-S04's bundle, which no step manifest declared. Whole-tree check (tester, `tests/M4-S04/manifest_check_wholetree.txt`): every member has a file, every file a member, M2-S04's rule exactly once. The runbook names every carried open item it must (O-M1S01-01, A26/REQ-010, O-M3S02-01, A38, O-M2S05-04, O-M4S02-02, N4-F-06, O-M2S01-01, A32 — each found by grep). **0 unresolved.**

## 4. Deployment order
Two requests: request 1 (36 members) in milestone order with four edits made in the deploy copy only (OpportunityStage merge, related-list copy, Opportunity object-file merge, dashboard runningUser); between requests the report column codes are confirmed per M4-S01; request 2 the Report then the Dashboard (N4-F-06). Pre-deploy A-1..A-17, rehearsal R-1/R-2, between B-1/B-2, post-deploy P-1..P-10, each with an owner role. No `sf project deploy start` without `--dry-run` anywhere.

## 5. Merged manifest
`reports/MILESTONE-M4-package.xml` = `artefacts/M4-S04/package.xml` (the build-level manifest is this milestone's by design). The M3 report's gap (Apex and bundle absent from any manifest) is closed here.

## 6. Milestone acceptance tests
| # | Test | Result |
|---|---|---|
| 0 | `check_deployment_manifest.py --manifest-dir artefacts` (build) | exit 0 — 78 files scanned, 0 findings |
| 1 | `check_rtm.py --file artefacts/M4-S03/traceability.md --manifest-dir artefacts` | exit 0 — 28 rows, 0 gaps, 0 orphans, 0 errors, 42 id-shape warnings |
| 2 | manifest (build-level) | consistent, 38/38, whole-tree |
| 3 | manual — nine prerequisites owned and ordered | for the gate: runbook table maps all nine (tester spot-check true) |
| 4 | manual — the 140-deal reassignment as an ordered, owned step | for the gate: P-8, **with O-M4S04-02's stage-mapping decision attached** |

## 7. Manual checklist for the gate
M4-S01 ×2 (probe runbook; new report type not SMB's); M4-S02 ×3 (folder shares + empty group; runningUser absent + B2; no product column); M4-S03 ×2 (43 assumptions with owners, A24/A28/A29 called out; REQ-010/M2-S04 row read with its amendment); M4-S04: 6 gate ticks (deny-list; M2-S04's rule in the manifest once; nine prerequisites; REQ-010 runbook step; REQ-017 b pre-deploy grep; REQ-018 b rehearsal statement) + 4 post-deploy UAT (negative cases REQ-004/016/017/018) not tickable at this gate by design.

## 8. Org evidence
`reports/MOCK-DEPLOY-M4.md`: run 1 (3 refusals: record-type column, chart sortBy, report), run 2 (chartAxisRange; column form 2), run 3 (type accepted with `RecordType`; report fails by N4-F-06), **run 4 manifest mode 43/44 with Apex + bundle by manifest** — test run aborted by the known pair. Apex tests: `MOCK-DEPLOY-M3.md` run 5, 6/6, 95.6%. Settled this milestone: the report-type record-type column form; chart components need `sortBy` and `chartAxisRange`; a report cannot validate with its new type in one deployment.

## 9. Findings
- **MV-M4-01 (high, runbook)** Partial `Opportunity.object-meta.xml` may replace the object definition on a real deploy (O-M4S04-01); blocking retrieve-and-merge E3/A-5. Unverifiable by checkOnly.
- **MV-M4-02 (high, runbook)** The 140-deal reassignment needs a stage mapping Q8/A37 denied (O-M4S04-02); P-8 blocked on the VP and the Sales Operations lead.
- **MV-M4-03 (medium)** SMB users land on the Enterprise page unless an app-level assignment outranks the org default (O-M4S04-03, A-8).
- **MV-M4-04 (medium)** Report and dashboard validated only after the type exists (N4-F-06); request 2 carries them; column codes UNVERIFIED until the split deploy (M4-S01 Phase B).
- **MV-M4-05 (low)** Test 4's "only org command is mock_deploy.py" vs the runbook's read-only retrieves and SOQL (O-M4S04-04) — gate decision.
- **MV-M4-06 (low)** Plan prose: M4-S04 inputs and A37 still describe M2-S04 as blocked and the reassignment as mapping-free; duplicate O-M4S04-01..03/-05..07 and O-M3S05-01..04 ids in decisions.md; 8 advisory checker WARNs on M4 steps.
- **MV-M4-07 (info)** Workbook sections 4, 7, 9, 10 carry no rows (no sharing change, no integration, no migration in scope) — stated, not hidden.

## 10. Confidence: MEDIUM
Every declared runnable test ran; manifest proven whole-tree and by the org; the two high findings are runbook risks no dry run can show; operator-run verification.

## 11. Gate
```
python3 scripts/build_plan.py brief .sfskills/builds/northwind-sales/plan.json M4
python3 scripts/build_plan.py gate .sfskills/builds/northwind-sales/plan.json milestone:M4 approve --by "<name>"
```
Approving the last milestone sets the build `done` (§ 3).
