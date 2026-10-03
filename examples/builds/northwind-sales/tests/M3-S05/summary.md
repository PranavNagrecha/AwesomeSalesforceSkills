# Test summary — M3-S05

Step: `Opportunity Enterprise Lightning record page carrying the Path and the discount panel, with its org-default assignment`
Run from: `.sfskills/builds/northwind-sales/` (build directory, via the `skills` symlink)

| Test | Type | Result | First line of output |
|---|---|---|---|
| xml | always-on | pass | 3 of 3 XML files parsed (flexipage, object override, package.xml) |
| manifest | always-on | pass (consistent) | FlexiPage `Opportunity_Enterprise_Record_Page` and CustomObject `Opportunity` each file-backed, both directions |
| `check_lightning_record_page_configuration.py --manifest-dir artefacts/M3-S05` | checker (scope: step) | pass (exit 0) | `No errors found (0 warning(s)).` |
| `check-outputs M3-S05` | precondition | ok | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |

No `command`-type acceptance test is declared for this step.

Manifest detail: `package.xml` names two members (`FlexiPage` and `CustomObject`), and this is one of the metadata step types (`ui`) for which the always-on manifest check runs for real rather than skipping — see `tests/M3-S05/manifest_check.txt` for the full two-directional trace. No exclusion from `skills/devops/metadata-api-coverage-gaps` was needed since both types ship as ordinary standalone source files here.

Manual (deferred to the M3 milestone gate, never ticked here): 2 lines, both Given/When/Then-shaped with a named observable outcome, per `skills/admin/acceptance-criteria-given-when-then`:
1. The object file carries exactly two `actionOverrides` blocks (View/Flexipage/`Opportunity_Enterprise_Record_Page`, formFactor Large and Small) and nothing else, and `deploy-order.md` § 3.1 states the app-override-wins-and-must-be-re-pointed caveat — spot-checked, both match.
2. The flexipage has the Path component in `subheader` (`hideUpdateButton` false), `discountApprovalPanel` in `sidebar` (`discountThreshold` 20), and every `componentInstance` carries an `identifier` ≤ 120 characters — spot-checked, all three identifiers present and short (`runtime_sales_pathassistant_pathAssistant`, `force_detailPanel`, `c_discountApprovalPanel`); matches.

Neither manual line's spot-check is part of the pass/fail contract — manual tests are ticked by a human at the milestone gate, never by this agent — but both are recorded here as due diligence and neither is reported as unusable.

Two `UNVERIFIED` markers on the flexipage file (the `sidebar` region name for this template, and the `c:` prefix on the custom LWC) are the org's to settle, per the operator's framing of this run — not evaluated here, and not something this checker can see (it validates identifiers, region capacity, operators and assignment, not a template's real region set or a component namespace against an org's component list). The parallel operator mock-deploy dry run, if any, writes only under `reports/mock-deploy/` and was not read as part of this test pass.

**passed: true** (failed[] is empty; manual lines never count toward failed).

Raw checker captures: `tests/M3-S05/xml_check.txt`, `tests/M3-S05/manifest_check.txt`, `tests/M3-S05/checker1_lightning_record_page_configuration.txt`, `tests/M3-S05/check_outputs.txt`, `tests/M3-S05/check_outputs_hashes.json`.
