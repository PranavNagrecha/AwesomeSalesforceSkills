# Test summary — M3-S02

Step: Opportunity.Discount_Approval process plus the two workflow alerts and four field updates it fires
Status before run: `built` (repaired at 2026-09-19T16:46:52Z; amendments withdrew the email-checker test and narrowed entry criteria to exclude Closed Won/Closed Lost)

| Test | Type | Result | First line of output |
|---|---|---|---|
| `xml` | always-on | PASS | 3 files parsed (`package.xml`, `approvalProcesses/Opportunity.Discount_Approval.approvalProcess-meta.xml`, `workflows/Opportunity.workflow-meta.xml`) |
| `manifest` | always-on | PASS | `ApprovalProcess:Opportunity.Discount_Approval` and `Workflow:Opportunity` both present with a backing file; no unmatched files, no unmatched members |
| `skills/admin/approval-processes/scripts/check_approval_design.py --manifest-dir artefacts artefacts` | checker (scope: build) | PASS | exit 0 — `{"score": 100, "findings": [], "summary": "Scanned 1 approval-process metadata file(s); 0 finding(s) detected."}` |
| `check-outputs` | precondition | PASS | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| manual (Q31/Q33 process shape) | manual | deferred | GWT well-formed, observable outcome named; content spot-checked and consistent with the artefact |
| manual (deploy-order.md active/order/Apex) | manual | deferred | GWT well-formed, observable outcome named; content spot-checked and consistent with `deploy-order.md` |
| manual (alert recipients non-empty) | manual | deferred | GWT well-formed, observable outcome named; content spot-checked and consistent with the workflow XML |

Raw captures: `check_approval_design.stdout.txt`, `check_approval_design.stderr.txt`, `check_approval_design.exit.txt`, `check_outputs.stdout.txt`, `check_outputs_hashes.stdout.txt` in this directory.

`passed: true` — 0 runnable tests failed. Three manual tests deferred to the M3 milestone gate, not counted as failures.
