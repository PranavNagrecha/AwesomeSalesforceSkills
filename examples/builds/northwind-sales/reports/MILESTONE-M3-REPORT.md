# Milestone M3 — verification report

Verifier: dry-run operator (Fable), 2026-10-02T17:14Z, following `agents/milestone-verifier/AGENT.md` Steps 1–11 directly (design-only build; nothing deployed; no gate written by this report).

## Verdict: ready-with-findings

All four ready-for-gate conditions hold: every M3 step is `documented` (M3-S03 re-documented today after its test repair), both declared milestone checkers exit 0, the merged manifest is consistent for the types it carries, and the org validated M1 + M2 + M3 together in source mode with the Apex tests passing (run 5). Not "ready" because: the Jest suite has never run (no harness), two runtime behaviours no checkOnly run can see remain open (manager routing when the owner has no Manager; the product gate after a line-item deletion), and the milestone manifest by plan design omits the Apex and the bundle until M4-S04 declares them.

## 1. Precondition
Gates `plan`, `milestone:M1`, `milestone:M2` approved; `milestone:M3` pending, never approved (first verification); five steps `documented`, none blocked.

## 2–3. Symbol inventory and reference resolution (by parsing)
Workflow alerts `Notify_Owner_Discount_Approved/Rejected` → templates `Sales_Approvals/Discount_Approved/Rejected` (M3-S01) ✓; four field updates → `Approval_Status__c` (M1-S01) ✓; approval process actions → those alerts and field updates ✓; process `emailTemplate` → `Sales_Approvals/Discount_Approval_Request` ✓; entry-criteria stages and record types → M1-S01 ✓; Apex `setProcessDefinitionNameOrId('Discount_Approval')` → the process ✓; LWC `@salesforce/apex/OpportunityApprovalController.submitForApproval` → M3-S03 ✓; FlexiPage `c:discountApprovalPanel` → M3-S04 ✓; object `actionOverrides` → the FlexiPage ✓. **0 unresolved.** The org agrees: run 5 compiled all 38 components.

## 4. Deployment order
M1 → M2 → M3-S01 (folder, templates) → M3-S02 (workflow before the process that names its actions; both in one `Workflow`/`ApprovalProcess` pair) → M3-S03 (Apex, names the process) → M3-S04 (bundle, imports the controller) → M3-S05 (page references the bundle; object override references the page). No backward dependency. Run 5 deployed all nine steps in one source-mode run.

## 5. Merged manifest
`reports/MILESTONE-M3-package.xml` — 8 members: ApprovalProcess, CustomObject, EmailFolder, EmailTemplate ×3, FlexiPage, Workflow; version 62.0. **By plan design it carries no `ApexClass` or `LightningComponentBundle`:** M3-S03 and M3-S04 ship no manifest and M4-S04 declares their members. A manifest-mode deploy of M3 alone therefore fails on the page's component reference (run 2); the build-wide manifest in M4-S04 is where M3 becomes deployable by manifest. Finding MV-M3-03.

## 6. Milestone acceptance tests
| # | Test | Result |
|---|---|---|
| 0 | `check_approval_design.py --manifest-dir artefacts artefacts` | exit 0 — 0 findings; resolved all six actions and the template cross-step |
| 1 | `check_approval_process_apex_patterns.py` (build scope) | exit 0 — 1 process, 5 Apex files, 0 findings |
| 2 | manifest | consistent for its 8 members (see § 5 for what it omits by design) |
| 3 | manual (Q33 four outcomes) | for the gate: submit → Pending + lock; approve → Approved + unlock + email; reject → Rejected + unlock + email; recall → status cleared — all present in `Opportunity.workflow-meta.xml` and the process; **re-firing on recall of a closed record is excluded by the narrowed entry criteria (D-M3S02-01)** |
| 4 | manual (mock_deploy run for M3) | **run 5 (2026-10-02T17:10:46Z) Succeeded 38/38, tests 6/6, coverage 95.6%** — `reports/MOCK-DEPLOY-M3.md` |

## 7. Manual checklist for the gate
- M3-S01: sender = current user (D-M3S01-01); `showApprovalHistory` true on the process (O-M3S01-01 — present ✓).
- M3-S02: entry criteria exclude closed stages; approver = owner's Manager (runtime risk O-M3S02-01).
- M3-S03: API 62.0 on four classes, 67.0 on the template copy; the process name is a literal in the call; the test seeds its own object grant (D-M3S03-03).
- M3-S04: Jest suite reviewed, never run (O-M3S04-01); percent comparison 20 vs 0.20 UNVERIFIED (O-M3S04-02).
- M3-S05: org-default activation; A38 app assignments unknown (O-M3S05-02); Renewal page unconfirmed (O-M3S05-03 / O-M2S05-04).

## 8. Org evidence
`reports/MOCK-DEPLOY-M3.md`: run 1 (M3-S01/S02 only) 30/30; run 2 manifest mode failed on the page's bundle reference (plan shape); run 3 source mode: Apex compiled, bundle rejected ×13 — all in the Jest file (tooling, N3-F-07, fixed); run 4: 38/38 compile, 6/6 tests failed on the persona's missing object permission (N3-F-08); **run 5: Succeeded 38/38, 6/6 tests passed, 95.6% coverage.** Settled: approval process and workflow shapes; `sidebar` region and `c:` prefix on the page; `ActionOverride` activation; `RecordType.DeveloperName` in approval entry criteria.

## 9. Findings
- **MV-M3-01 (medium)** Jest never executed (O-M3S04-01); the bundle compiles and renders only as far as the deploy proves.
- **MV-M3-02 (medium)** Two runtime behaviours unverifiable by checkOnly: owner without Manager fails at submit (O-M3S02-01); product gate after line-item deletion (M2-S04 § 2.2).
- **MV-M3-03 (low)** Milestone manifest omits Apex and the bundle by plan design until M4-S04 (§ 5).
- **MV-M3-04 (low)** Static Apex checkers were green before and after a repair the org forced (O-M3S03-04): `tested` on an Apex step is not test evidence; the org run is.
- **MV-M3-05 (info)** Eight § 5 checker-coverage WARNs on M3 steps: all are checkers that would scan nothing on those steps' artefacts (friction 39/52/54); accepted as advisory.

## 10. Confidence: MEDIUM
Every declared runnable test ran; references resolved by parsing and confirmed by the org; the org ran the tests. Held at MEDIUM because the verification was operator-run and the two medium findings rest on runtime behaviour no dry run can show.

## 11. Gate
```
python3 scripts/build_plan.py brief .sfskills/builds/northwind-sales/plan.json M3
python3 scripts/build_plan.py gate .sfskills/builds/northwind-sales/plan.json milestone:M3 approve --by "<name>"
```
