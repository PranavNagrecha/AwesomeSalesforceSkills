# step-tester — M3-S04 — results summary

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| `xml` — parse every `*.xml` / `*-meta.xml` under `artefacts/M3-S04/` | xml | PASS (3 files, all parsed) | — |
| `manifest` — package.xml vs artefacts, both directions | manifest | PASS (consistent) | — |
| `python3 skills/admin/case-management-setup/scripts/check_case_management_setup.py --manifest-dir artefacts` | checker (build scope) | PASS — exit 0, `check-outputs` ok | — |
| W02 manual: Case.assignmentRules-meta.xml routes on Origin + Account support tier, catch-all to Tier_1_General, every `assignedTo` resolves to an M2-S04 queue | manual | DEFERRED to milestone gate | see Ambiguity note below |
| Manual: exactly one auto-response entry can match, template is M3-S02's folder-qualified Classic template | manual | DEFERRED to milestone gate | — |

Raw checker stdout/stderr: `tests/M3-S04/checker_check_case_management_setup.stdout.txt` / `.stderr.txt`.
`check-outputs` raw JSON: `tests/M3-S04/check-outputs.json`.

## Ambiguity recorded verbatim (not resolved here)

The step's title — "Case assignment rules and auto-response rules driven by Origin and account
support tier" — and the first manual acceptance test both assert that the assignment rule routes
on Case.Origin **and** the Account support tier. The built artefact
(`artefacts/M3-S04/assignmentRules/Case.assignmentRules-meta.xml`) routes on Case.Origin only.
`artefacts/M3-S04/deploy-order.md` § 6 row 1 records that this was a deliberate omission by the
owning agent (`metadata-builder`): no answer names the tier→queue mapping and no skill under
`skills/` shows a `criteriaItems/field` on a related object inside a Case assignment rule, so
writing one would have been a guessed value shape. `plan.json` `steps[M3-S04].inputs.note` (Q25)
and `decisions.md` D3 are the same design intent this mismatch traces back to.

This is a plan/artefact mismatch, not a build failure and not something this test run resolves. It
is carried forward to the milestone gate: the first manual test above cannot be ticked as written
against the artefact as built, and the mismatch itself — title/test vs. artefact — is the thing the
M3 gate has to adjudicate (per `deploy-order.md` § 6 row 1: "Either an answer names the tier→queue
mapping and a live org confirms the cross-object notation, or the step's title and that manual test
are corrected to Origin-only").

Both manual tests were checked against the Given/When/Then shape (`admin/acceptance-criteria-given-when-then`)
before being carried forward: both name an explicit Given, a single When, and an observable Then, so
neither is rejected as unusable — the first is deferred with the mismatch noted above, not rejected.
