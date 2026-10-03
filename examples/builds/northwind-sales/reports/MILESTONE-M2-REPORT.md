# Milestone M2 — verification report

Verifier: dry-run operator (Fable), 2026-09-19T15:40Z, following `agents/milestone-verifier/AGENT.md` Steps 1–11 directly (design-only build; nothing deployed; no gate written by this report).

## Verdict: ready-with-findings

All four literal ready-for-gate conditions hold: every M2 step reached `documented` (M2-S01/S03/S05 on 2026-09-19T15:11–15:15Z, M2-S04 and M2-S02 in the doc batch that follows this report), every declared milestone test that can run exited 0, the merged manifest is consistent, and the org validated the whole of M1 + M2 together (run 3). The verdict is not "ready" because three things a reader of "ready" would not expect are true: nothing in the build assigns either permission set (assignment is data), the milestone's own test prose still describes M2-S04 as blocked, and one platform behaviour the product gate relies on (re-firing after the last line item is deleted) cannot be verified by any checkOnly run.

## 1. Precondition
Gate `milestone:M1` approved 2026-09-18T15:01:29Z; gate `plan` approved; step gates `step:M2-S01` and `step:M2-S02` approved; milestone M2 status `building`; no step blocked. First verification of M2 (no `## Re-verification` section).

## 2–3. Symbol inventory and reference resolution
Definitions in the tree (M1 + M2): record types Enterprise, Renewal; layouts Opportunity Enterprise Layout, Opportunity Renewal Layout; fields Discount__c, Approval_Status__c; custom permission Bypass_Opportunity_Sales_Validation; permission sets Enterprise_Sales_Record_Types, Sales_Ops_Validation_Bypass; eight OpportunityStage values. Every reference in M2 was resolved by parsing against those definitions: both Paths' `recordTypeName`, all six `picklistValueName`s and every custom `fieldNames`; both layoutAssignments and both recordType references in the profile overlay; both fieldPermissions and the customPermissions node in the two sets; both validation rules' `$Permission` token, custom-field tokens, StageName picklist values and RecordType.DeveloperName comparisons. **0 unresolved.** The org agrees: run 3 (below) compiled both formulas and accepted every cross-reference.

## 4. Deployment order
M1 first (fields, value set, processes and record types, layouts — accepted at G3). Then M2-S01 (permission + bypass set) before M2-S03 and M2-S04 (both formulas name `$Permission.Bypass_Opportunity_Sales_Validation`; a token naming an absent permission evaluates false silently, so ordering is a correctness matter, not a compile matter). M2-S02 (record-type set + profile overlay) after M1-S02's layouts (the overlay names them). M2-S05 (Paths + setting) after M1-S01. No backward dependency; each step's deploy-order.md states the same order. Run 3 deployed all seven steps in one manifest, which is the order-insensitive proof that the set is self-consistent.

## 5. Merged manifest
`reports/MILESTONE-M2-package.xml` — 9 members across CustomPermission, PermissionSet, Profile, ValidationRule, PathAssistant, Settings; every member has a file behind it and every M2 file has a member; version 62.0 (every step). Produced by `mock_deploy.py --milestone M2 --mode manifest --plan-only` (2026-09-19T15:36:58Z) — the same merge run 3 used for M1 + M2.

## 6. Milestone acceptance tests
| # | Test | Result |
|---|---|---|
| 0 | `check_validation_rules.py --manifest-dir artefacts` | exit 0 — 2 rules scanned, 1 REVIEW (M2-S04 picklist logic has no explicit blank guard; a substring heuristic, adjudicated at build), 0 blocking |
| 1 | `check_path_and_guidance.py --manifest-dir artefacts` | exit 0 — "Checked 2 path(s): no issues found." (record types and all six stage values resolved against M1-S01) |
| 2 | `check_custom_permissions.py --manifest-dir artefacts` | exit 0 — Bypass_Opportunity_Sales_Validation: Consumers **2** (both rules), granted by Sales_Ops_Validation_Bypass |
| 3 | manifest | consistent (9/9). **The test's own description is false**: it says the product rule "appears nowhere because M2-S04 is blocked"; M2-S04 was unblocked 2026-09-15 and its rule is member 9. No writer can amend milestone-level prose while the build is `building` (driver's log friction 42). |
| 4 | manual | **Premise false** — "Given M2-S04 is blocked on a library gap": it is not; the gate should record that the product gate ships as a validation rule, not as Path guidance, and tick nothing about a deferred owner. |
| 5 | manual | For the gate: who gains the bypass (nobody by metadata — O-M2S01-01, assignment is data; intended: the sales-ops admin only) and who gains the two record types (nobody by metadata; intended: the Enterprise/Renewal persona via Enterprise_Sales_Record_Types). |

Advisory (undeclared, run for evidence): the three step-scoped checkers that assert nothing on their steps' artefacts (`check_opportunity_management.py` on M2-S03, `check_products_and_pricebooks.py` on M2-S04, `check_sales_process_mapping.py` on M2-S05) all exit 0 and prove nothing — recorded so nobody reads them as passes.

## 7. Manual checklist for the gate (from the steps' deferred manuals and the items above)
- M2-S01: the bypass set grants exactly one custom permission and nothing else.
- M2-S02: the profile overlay carries two layout assignments and no visibility block (amended wording); the persona set carries record-type visibility and the two field grants and no object permissions.
- M2-S03: `Discount__c > 0.20`, bypass first, `RecordType.DeveloperName` compared as text; error message is Q15's sentence on `Discount__c`.
- M2-S04: § 2.1 org-verified by run 1; § 2.2 still unverified, forward gate only.
- M2-S05: Enterprise path exit criteria per Q2/Q11; "a path is not the feature switched on" — M3-S05 owns the page; the Renewal page is unconfirmed (O-M2S05-04, retrieve-and-grep before deploy).
- Milestone: name who will be assigned each set (O-M2S01-01); accept that the product gate shipped as a rule (test 4's premise).

## 8. Org evidence
`reports/MOCK-DEPLOY-M2.md`: run 1 (2026-09-19T14:56Z) Failed 17/18 with two platform refusals now repaired (N3-F-05 profile default record type; N3-F-06 rule description > 255); run 2 probe 17/17 without the profile; **run 3 (2026-09-19T15:26:20Z) Succeeded 18 total, 0 errors, checkOnly, NoTestRun** — M1 + M2 in one manifest. Not proven by any run: assignment of either set; re-firing of the product gate after a line-item deletion; that the Renewal path has a page to render on.

## 9. Findings
- **MV-M2-01 (medium)** Nothing in the build assigns Sales_Ops_Validation_Bypass or Enterprise_Sales_Record_Types; the milestone goal's "the sales-ops admin is the only person who can save past that rule" is a design claim until the post-deploy SetupEntityAccess query (O-M2S01-01).
- **MV-M2-02 (medium)** Record-type scope disagreement: the discount rule gates Enterprise and Renewal (M2 goal wording); the product gate gates Enterprise only (its amended answer set) and cannot be widened by a second RecordType clause because Renewal_Sales_Process has no Propose stage (O-M2S03-01, O-M2S04-01). A gate decision, not a defect.
- **MV-M2-03 (low)** Milestone test 3's description and test 4's premise describe a blocked M2-S04; both false since 2026-09-15; no prose-only writer exists at milestone level.
- **MV-M2-04 (low)** Q3's Closed Won handoff (Finance, CS) and the "and Next Step" half of Q11's Discover→Propose gate are built by nobody in M2 (O-M2S05-01, O-M2S04-05); carry to M3/M4.
- **MV-M2-05 (info)** Three declared step-scoped checkers assert nothing on their steps (see § 6); their declarations cleared § 5 warnings without buying assertions (friction 39).

Open items carried, by step: O-M2S01-01..04, O-M2S02-02..04 (O-M2S02-01 closed by the repair), O-M2S03-01..04, O-M2S04-01..06, O-M2S05-01..06 — decisions.md is the register.

## 10. Confidence: MEDIUM
Every declared runnable test ran and exited 0; references resolved by parsing and confirmed by the org; manifest consistent; the milestone was validated in the org as a whole. Held at MEDIUM because two of the six declared tests are manual with one of them resting on a false premise, and because the verification was performed by the operator rather than by the verifier agent, on the same evidence the agent would have used.

## 11. Gate
```
python3 scripts/build_plan.py brief .sfskills/builds/northwind-sales/plan.json M2
python3 scripts/build_plan.py gate .sfskills/builds/northwind-sales/plan.json milestone:M2 approve --by "<name>"
```
Approving accepts M2 with the findings above; M3 and M4 still need their own gates.
