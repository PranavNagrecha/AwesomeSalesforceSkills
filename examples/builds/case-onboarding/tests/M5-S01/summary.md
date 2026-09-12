# step-tester — M5-S01 — results

Step: *Pull list views for Tier 2 and Billing plus the escalation monitoring report and its folder* (type `ui`). Status before this run: `built` (rebuilt at `2026-09-12T10-08-00Z` for F-49/F-50; the prior `tested` record at `09-50-00Z` was against the pre-rebuild report and is superseded by this run).

| Test | Type | Result | First line of output |
|---|---|---|---|
| `check_list_views_and_compact_layouts.py --manifest-dir artefacts` (build scope) | checker | PASS (exit 0) | `No issues found.` |
| `check_report_inventory.py --manifest-dir artefacts/M5-S01` (step scope) | checker | PASS (exit 0) | `{"score": 100, "findings": [], "summary": "Scanned 1 report/dashboard file(s); 0 finding(s) detected."}` |
| `xml` | always-on | PASS | 6/6 `*.xml`/`*-meta.xml` files parsed with ElementTree |
| `manifest` | always-on | PASS (consistent) | 5 members across `ListView`/`Report` all covered by files; all 5 artefact files map to a manifest member; no wildcards |
| `check-outputs` | precondition | ok | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| manual (Given/When/Then) | manual | deferred to milestone gate | see Manual checklist below |

**`passed`: true.** 0 failures. `tests/M5-S01/results.json` written before the status transition, per Step 5.

## Manifest check detail

`package.xml` declares:

- `ListView`: `Case.Billing_Queue`, `Case.Tier_1_General_Queue`, `Case.Tier_2_Queue`
- `Report`: `Support_Operations`, `Support_Operations/Escalated_Open_Cases`

File to member: each of the 3 `*.listView-meta.xml` files and the 2 report-tree files (the bare folder file and the nested report file) maps to exactly one declared member. Member to file: each of the 5 declared members has exactly one corresponding file on disk. No wildcards either direction. Consistent.

## Raw captures

- `tests/M5-S01/xml_check.txt` — per-file parse result for all 6 XML files
- `tests/M5-S01/test1_list_views.txt` — stdout/exit of the build-scope list-view checker
- `tests/M5-S01/test2_report_inventory.txt` — stdout/exit of the step-scope report checker
- `tests/M5-S01/check_outputs.json` — `build_plan.py check-outputs` result

## Manual checklist (verbatim, for the milestone gate)

> Given the three views are Queue-scoped, when each listView file is read, then its `<queue>` names a queue developer name that exists under `artefacts/M2-S04/queues/`, and the Tier 1 General view is present as Tier 1's interim pull surface while M3-S05 is blocked.

Checked against the Given/When/Then shape before listing: it carries a Given (Queue-scoped views), a When (each listView file is read) and a Then with two observable outcomes (a `<queue>` value resolving under `artefacts/M2-S04/queues/`, and the Tier 1 General view's presence). Tickable as written — not flagged unusable. This agent does not tick it; verifying the referenced queue developer names actually exist under `artefacts/M2-S04/queues/` is the milestone gate's read, not a molecular test declared on this step.

## Test-coverage observation (both declared checkers, same blind spot)

Both declared checkers exited 0 on the report file the org rejected at `2026-09-12T09-47-29Z` (`reports/MOCK-DEPLOY-M5.md` run 1 — `Value too long for field: Description maximum length is:255`), before the F-49/F-50 rebuild, and both exit 0 again now on the rebuilt file — an identical verdict on two materially different report bodies. Recorded here as this run's own finding, not merely carried from the prior envelopes:

1. **`check_report_inventory.py` never sees the report body.** Its step-scope run reports `Scanned 1 report/dashboard file(s)` — the report file itself contributes to that count, but nothing in its 0 findings asserts anything about `<reportType>`, `<columns>`, `groupingsDown`, or `<description>` length. The exit-0 verdict is silent on exactly the four fields F-49/F-50 changed. A checker that scored the rejected file 100 and the accepted-shape rebuild 100 identically is not distinguishing "deployable" from "not" on this artefact's body.
2. **The declared folder filename is invisible to the same checker.** `reports/Support_Operations-meta.xml` — the filename `plan.json` declares, and the one the org accepted in `MOCK-DEPLOY-M5.md` run 1 — is not recognized by `check_report_inventory.py`'s `FOLDER_SUFFIXES` (`.reportFolder-meta.xml` / `.dashboardFolder-meta.xml`). Only 1 file is scanned where 2 would be scanned under the skill-documented suffix. `acceptance_tests[1]`'s stated assertion — "the report sits in a named folder with declared sharing, not in a personal folder" — never exercises the folder's `accessType`/`folderShares` fields inside this checker; the test still exits 0 because the report file alone keeps `scanned` above zero. `artefacts/M5-S01/deploy-order.md` § 3 records the same measurement and both remedies (deepen the checker's suffix recognition, or have the M5 gate accept the folder fields on a human read of the file).

Neither observation changes this run's `passed: true` — both declared tests did exactly what their own pass condition says (exit 0 and `check-outputs` ok) — but a green run here carries no automated signal on the report's field-level shape or the folder's sharing declaration, only on structural well-formedness and manifest consistency. That gap is why the org, not this harness, is what caught F-49 and F-50 in the first place.

## Ambiguities carried forward from the `built` envelopes (recorded verbatim, not adjudicated here)

1. **The report ships without its `Escalated` criterion.** No cited skill carries a report column code for `Case.IsEscalated`, so `Escalated_Open_Cases.report-meta.xml` returns open Cases from the last 30 days rather than escalated open Cases. See `artefacts/M5-S01/deploy-order.md` §§ 0 and 2 U1 — a post-deploy runbook step, not something a molecular test here can catch.
2. **The report body's `STATUS`/`CREATED_DATE` columns and the `equals` + `LAST_N_DAYS:30` pairing remain unvalidated end to end** per `deploy-order.md` § 0 and § 2 U2/U3 — no checker in this library asserts report-column semantics, and no further org run happened between the `10-08-00Z` rebuild and this test run.
