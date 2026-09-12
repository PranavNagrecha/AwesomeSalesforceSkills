# Test summary — M1-S01

Build `tier2-webhook` · step `M1-S01` (`object-model`) · run by `step-tester`.

| Test | Type | Result | First line of output |
|---|---|---|---|
| `xml` (always-on) | xml | PASS | 16/16 `*.xml`/`*-meta.xml` files parsed |
| `manifest` (always-on) | manifest | PASS | 2 CustomObject + 13 CustomField members, consistent both directions |
| `skills/admin/object-creation-and-design/scripts/check_object_creation_and_design.py` | checker | PASS (exit 0) | "No issues found across 2 object file(s) and 13 field file(s)." |
| `skills/admin/picklist-and-value-sets/scripts/check_picklist_and_value_sets.py --min-severity ERROR` | checker | PASS (exit 0) | "No findings." |
| `skills/apex/platform-events-apex/scripts/check_platform_events_apex.py` | checker | PASS (exit 0) | `{"score": 100, "findings": [], "summary": "Scanned 0 Apex file(s) and 2 object file(s); 0 platform-event finding(s)."}` |
| `check-outputs` | precondition | PASS | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| Picklist-to-code contract check | manual | DEFERRED to milestone gate | Given/When/Then shape present and names an observable outcome (exact restricted-picklist values); not ticked by this agent |

**Overall: passed = true, failed = []**

Raw checker stdout/stderr/exit codes are under `tests/M1-S01/raw/`.

## Manifest check detail

`artefacts/M1-S01/package.xml` declares 2 `CustomObject` members (`Integration_Failure__c`,
`Tier2_Escalation__e`) and 13 `CustomField` members. Every derived file→member mapping
(`objects/<Obj>/<Obj>.object-meta.xml` → CustomObject; `objects/<Obj>/fields/<F>.field-meta.xml`
→ `<Obj>.<F>` CustomField, per `skills/devops/salesforce-dx-project-structure`) is covered, and
every named member has a backing file. No wildcard members are used. `Tier2_Escalation__e`'s five
payload fields are declared inline in its own object file (deploy-order.md § 2 item 3) and are
correctly absent from both the file list and the manifest's CustomField block — the deploy-order
note is explicit that they are not separate members, and the checker classifies this consistently.

## Manual test classification

Given (Status__c.field-meta.xml and Severity__c.field-meta.xml exist) / When (a reviewer opens
them) / Then (confirms the restricted value sets read exactly New/Retrying/Resent/Resolved/Abandoned
and exactly Error/Warning) — the test names a deterministic, observable outcome per
`admin/acceptance-criteria-given-when-then` and is tickable by a human per
`admin/uat-and-acceptance-criteria`. Carried forward to `skipped_manual[]` for the milestone gate;
not counted as a pass or a failure.

## Process notes

- All three declared checkers exited 0 on the first pass with no repair needed — consistent with
  the M1-S01 build envelope's own claim.
- The M1-S02 field-permission constraint recorded in `deploy-order.md` § 6 (`Status__c` is a
  required field and cannot carry a `fieldPermissions` entry) is **M1-S02's** concern, not this
  step's; it is noted here only because the operator's amendment to M1-S02's inputs was named in
  this run's brief. Nothing in M1-S01's own artefacts or tests is affected by it.
