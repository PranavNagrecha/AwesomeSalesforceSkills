# step-tester — M2-S02 (rebuild #3 retest — F-60 repair)

Retest after REBUILD #3 (`reports/MOCK-DEPLOY-M5.md` run 5, finding F-60: 7
`fieldPermissions` added to `Case_Agent_Core` for the standard Case fields the
agent persona writes; `EntitlementId`/`Type`/`Reason` deliberately excluded).
See `envelopes/M2-S02/2026-09-12T18-00-00Z.md` and
`artefacts/M2-S02/deploy-order.md` section "Rebuild #3 — F-60 standard-field
permissions on `Case_Agent_Core`". This run supersedes the stale rebuild-#2
result previously recorded in this file (rebuild #2's `documented` run
predates F-60 and predates today's PSVP-FLS-01/PSVP-FLS-02 checker rules).

| Test | Type | Runner | Exit | Result | First line of output |
|---|---|---|---|---|---|
| `xml` | always-on | ElementTree over `artefacts/M2-S02/` | n/a | PASS | 8/8 files parsed (`package.xml`, 4 `.permissionset-meta.xml`, 3 `.permissionsetgroup-meta.xml`) |
| `manifest` | always-on | file<->`package.xml` cross-check | n/a | PASS | every `PermissionSet`/`PermissionSetGroup` member has a matching file and vice versa; no coverage-gap exclusions apply to either type |
| `check_permission_set_architecture.py --manifest-dir artefacts` | checker (scope: build) | `python3 skills/admin/permission-set-architecture/scripts/check_permission_set_architecture.py --manifest-dir artefacts` | 0 | PASS | `INFO: PSA-DESC-02 artefacts/M2-S01/permissionsets/Case_Intake_Integration.permissionset-meta.xml: PermissionSet description is 244 characters, approaching the 255-character limit.` -- pre-existing M2-S01 INFO, outside this step's scope; nothing about M2-S02 flagged |
| `check_permission_set_group_composition.py --manifest-dir artefacts/M2-S02` | checker (scope: step) | `python3 skills/admin/permission-set-group-composition/scripts/check_permission_set_group_composition.py --manifest-dir artefacts/M2-S02` | 0 | PASS | `GOOD: reuse: permission set 'Case_Agent_Core' is referenced by 3 PSGs (PSG_Billing_Prod, PSG_Tier1_Prod, PSG_Tier2_Prod)`. Summary: 1 good, 0 error, 0 warn, 0 info, scanned 3 PSG file(s). |
| `check_access_model.py --manifest-dir artefacts/M2-S02` | checker (scope: step) | `python3 skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py --manifest-dir artefacts/M2-S02` | 0 | PASS | `WARN: 1 finding(s) detected (0 blocking)` -- `{"score": 97, "findings": [{"severity": "WARN", "location": ".../Case_Agent_Core.permissionset-meta.xml", "message": "PSVP-FLS-01 permission set grants Create/Edit on EmailMessage with no field permissions on any of its standard fields ..."}], "summary": "Scanned 7 access-model metadata file(s); 1 finding(s) detected.", "blocking": 0}` |
| `check-outputs` | precondition for every checker + for `set-status tested` | `python3 scripts/build_plan.py check-outputs plan.json M2-S02` (run from repo root) | 0 | PASS | `{"ok": true, "step": "M2-S02", "missing": [], "empty": [], "malformed": []}` |

No `command` or `manual` acceptance tests declared on this step.

## The residual WARN, explained rather than treated as a failure

`check_access_model.py` exits **0** with `blocking: 0` even though it reports
one WARN-severity finding (`PSVP-FLS-01` on `Case_Agent_Core`'s `EmailMessage`
grant). The checker distinguishes `blocking` findings (ERROR-tier) from
advisory ones, and this finding is advisory. Per
`artefacts/M2-S02/deploy-order.md` section "Rebuild #3", this is a **named
ambiguity left for the human gate** -- no layout, workbook row or decision in
this build enumerates which standard `EmailMessage` fields a reply populates,
so granting them now would be a guess the plan's own Step 5 discipline
forbids. It is recorded here as a WARN, not counted as a failure, and not
silently dropped: it appears in the table above verbatim and again in Process
Observations.

`PSVP-FLS-02` (the sibling rule, for an empty profile with no PSG anywhere in
the tree) did not fire at step scope because no `.profile-meta.xml` exists
under `artefacts/M2-S02/` -- this step's outputs are permission sets and PSGs
only, so the rule has nothing to scan. That is expected, not a gap.

## File-checkable facts (all 8 metadata files under `artefacts/M2-S02/`)

| File | `<description>` length | `viewAllRecords: true`? | `modifyAllRecords: true`? |
|---|---|---|---|
| `permissionsets/Case_Agent_Core.permissionset-meta.xml` | 193 | no | no |
| `permissionsets/Case_Billing.permissionset-meta.xml` | 183 | no | no |
| `permissionsets/Case_Tier1.permissionset-meta.xml` | 193 | no | no |
| `permissionsets/Case_Tier2.permissionset-meta.xml` | 199 | no | no |
| `permissionsetgroups/PSG_Billing_Prod.permissionsetgroup-meta.xml` | 187 | no | no |
| `permissionsetgroups/PSG_Tier1_Prod.permissionsetgroup-meta.xml` | 194 | no | no |
| `permissionsetgroups/PSG_Tier2_Prod.permissionsetgroup-meta.xml` | 132 | no | no |

All descriptions stay <= 255 (all <= 200). No `viewAllRecords` or
`modifyAllRecords` set `true` anywhere in the step's artefacts -- confirmed
independently of the checkers' own PSA/PSVP sharing-bypass checks.

Raw checker captures: `check_permission_set_architecture.{stdout,stderr,exit}.txt`,
`check_permission_set_group_composition.{stdout,stderr,exit}.txt`,
`check_access_model.{stdout,stderr,exit}.txt`, `check_outputs.{stdout,stderr,exit}.txt`,
`xml_parse.json`, `manifest_check.json`.

**passed: true** (0 failed, 0 manual deferred).
