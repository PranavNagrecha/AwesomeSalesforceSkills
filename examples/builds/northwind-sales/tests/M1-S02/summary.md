# M1-S02 — Test Summary

Step: One page layout per new record type, carrying Discount__c and Approval_Status__c
Re-run after three org-driven layout repairs (N3-F-02/03/04). `reports/MOCK-DEPLOY-M1.md` run 4:
Succeeded, 9/9 components. Repair history: `artefacts/M1-S02/deploy-order.md` § 6.

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| xml (always-on) | xml | PASS — 3/3 files parse | — |
| manifest (always-on) | manifest | PASS — consistent (2 Layout members, 2 files) | — |
| `check_record_type_layouts.py --manifest-dir artefacts` | checker (scope: build) | PASS — exit 0, check-outputs ok | — (1 REVIEW + 1 INFO, both expected — see below) |
| Manual: deploy-order.md names the retrieve-and-copy instruction for the Opportunity Products relatedLists block (A26) | manual | deferred to milestone gate | — |
| Manual: both layouts carry the five required standard fields plus Discount__c editable / Approval_Status__c read-only, with deploy-order.md recording the unverified-until-dry-run status (A25) | manual | deferred to milestone gate | — |

**Checker findings (both pre-existing, exit-policy lenient, non-blocking):**
- REVIEW — the two layouts are identical after normalisation (known item O-M1S02-03; by design per decision D2, unaffected by the N3-F-02/03/04 repairs since both files were repaired identically).
- INFO — no Profile/PermissionSet in scope yet (those ship in M2-S02).

**check-outputs:** `{"ok": true, "missing": [], "empty": [], "malformed": []}`

**Overall:** `passed: true`. 0 failures. 2 manual tests carried to the M1 milestone gate.

Raw checker stdout/stderr: `tests/M1-S02/checker_check_record_type_layouts.stdout.txt` / `.stderr.txt`.
check-outputs raw JSON: `tests/M1-S02/check-outputs.json`; hashes: `tests/M1-S02/check-outputs-hashes.json`.
