# Mock deploy — milestone M1 (northwind-sales)

## Run 1 — 2026-09-18T13:34Z, MANIFEST mode, milestone M1 (M1-S01 + M1-S02; API 62.0)

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --mode manifest --milestone M1` → `reports/mock-deploy/2026-09-18T13-34-25Z/`

- status: **Failed** (checkOnly). Components 9 total, 6 ok, 4 errors. The value set, both record types and both fields validate.
- **N3-F-01 (HIGH).** `BusinessProcess Opportunity.Enterprise_Sales_Process` and `…Renewal_Sales_Process`: *"Cannot specify a default on: Opportunity"*. Both processes carry `<default>true</default>` on their opening stage — the runner's decision D-M1S01-01 put the per-motion default on the BusinessProcess, following `admin/opportunity-management` metadata-examples § 2. The org refuses a default on an Opportunity business process. Fix: drop `<default>` from both processes (M1-S01 re-run); library: the skill's example is wrong for Opportunity — gotcha + checker rule (BusinessProcess on Opportunity with `<default>true</default>` → ERROR).
- **N3-F-02 (HIGH).** Both layouts: *"Layout must contain an item for required layout field: Probability"*. Assumption A25 (the platform's Opportunity layout-required set is unverified — discover by dry run) is discharged by this run: Probability is required. Fix: add `Probability` to both layouts (M1-S02 re-run); library: record-types-and-page-layouts gotcha 13 generalised for Opportunity (Probability is layout-required, as Status is on Case) + checker rule.
- Not a finding: the partial `OpportunityStage` value set validated — checkOnly never deactivates anything; O-M1S01-01 (retrieve-and-merge before a real deploy) stands.

## Run 2 — 2026-09-18T13:43Z, MANIFEST mode, milestone M1 after both repairs (API 62.0)

- 8/9 ok, 2 errors (both layouts). **N3-F-01 closed by the org**: both business processes validate without the default. The remaining `<default>false</default>` elements on the other stages were accepted, so the platform rejects a *true* default, not the element.
- **N3-F-03 (HIGH).** Both layouts: *"Field:Name must be Required"*. The second required-field discovery of A25's iterate-the-dry-run procedure: on an Opportunity layout, `Name` must carry `behavior=Required` (the runner had it as `Edit`, per Q11's "enforcement lives in validation rules"). Fix: M1-S02 re-run, `Name` → `Required`; expect the org to reveal any third field on run 3. Library (Cursor task 18): the Opportunity layout rule is now two-part — `Probability` present, `Name` Required.

## Run 3 — 2026-09-18T13:52Z, MANIFEST mode, milestone M1 after the Name repair (API 62.0)

- 8/9 ok. N3-F-03 closed (Name accepted as Required). **N3-F-04 (HIGH):** both layouts — *"Field:StageName must be Required"*. Third discovery of A25. Pattern now clear: every field that is required at the field level on Opportunity (Name, StageName, CloseDate) must carry `behavior=Required` on the layout, and Probability must be present. Repair sets StageName AND CloseDate together to save a round; run 4 confirms or names a fifth. Library (Cursor task 18): RTL-REQ-02 generalised to the three field-level-required standard fields.

## Run 4 — 2026-09-18T13:57Z, MANIFEST mode, milestone M1 after StageName + CloseDate set Required (API 62.0)

- **Succeeded.** 9/9 components validate. N3-F-04 closed; the CloseDate inference is confirmed by the org's silence (the run would have named it otherwise) — the `UNVERIFIED (2026-09-18)` marker in `artefacts/M1-S02/deploy-order.md` § 6 resolves to confirmed at the next doc-keeper pass. A25 is now closed for these two layouts: Probability present; Name, StageName and CloseDate Required.
- Four rounds, 23 minutes, four org facts none of which any checker or the verifier held: no default on an Opportunity business process; Probability present on Opportunity layouts; Name, StageName, CloseDate Required. All four go to the library via Cursor task 18.
