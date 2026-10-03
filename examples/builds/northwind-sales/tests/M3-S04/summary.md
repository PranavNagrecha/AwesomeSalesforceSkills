# Test summary — M3-S04

Step: `discountApprovalPanel LWC — discount, approval status and a Submit button enabled only above the threshold — with its Jest suite`
Run from: `.sfskills/builds/northwind-sales/` (build directory, via the `skills` symlink)

| Test | Type | Result | First line of output |
|---|---|---|---|
| xml | always-on | pass | 1 of 1 `*-meta.xml` files parsed (`discountApprovalPanel.js-meta.xml`) |
| manifest | always-on | skipped-not-applicable | LightningComponentBundle member deferred to M4-S04's build-level manifest — see Process Observations for why this is an analogy to, not a literal instance of, the Apex exception |
| `check_lwc_base_component_recipes.py --manifest-dir artefacts/M3-S04` | checker (scope: step) | pass (exit 0) | `1 bundle(s), 0 loose template(s) scanned — 0 ERROR, 0 WARN` |
| `check-outputs M3-S04` | precondition | ok | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |

No `command`-type acceptance test is declared for this step. In particular, **no declared test invokes Jest** — the two `manual` entries ask a human to *read* the Jest file's content, not run it. Verified independently that Jest could not run here regardless: no `package.json`, `node_modules` or `sfdx-lwc-jest` anywhere from the repo root up to `/Users/pranavnagrecha`, and `npx --no-install sfdx-lwc-jest --version` fails ("could not determine executable to run"). `node --check` was not substituted for a Jest run or reported as a parse check — LWC modules use decorators and ESM that `node --check` cannot evaluate, so no such check was run.

Manual (deferred to the M3 milestone gate, never ticked here): 2 lines, both Given/When/Then-shaped with a named observable outcome:
1. Four named button-`disabled` assertions (20→disabled, 25/null→enabled, 25/Pending→disabled, 25/Approved→disabled) — spot-checked and all four are verbatim present in the test file. Due-diligence note: the same describe block actually contains 7 button-state cases, not 4 (also covers a Rejected-reopens-the-button case, the pre-wire-emit closed state, and the `discountThreshold` string-coercion case) — the line's "four cases" undercounts the file. The four it names are correct; a human ticking this box should read the whole block, not stop at four.
2. `discountThreshold` design attribute (default 20, description naming `Opportunity_Discount_Requires_Approval`), `supportedFormFactors` Large+Small only, target `lightning__RecordPage` scoped to Opportunity — spot-checked against `discountApprovalPanel.js-meta.xml` and matches exactly.

**passed: true** (failed[] is empty; manual lines never count toward failed).

Raw checker captures: `tests/M3-S04/xml_check.txt`, `checker1_lwc_base_component_recipes.txt`, `check_outputs.txt`, `check_outputs_hashes.json`.
