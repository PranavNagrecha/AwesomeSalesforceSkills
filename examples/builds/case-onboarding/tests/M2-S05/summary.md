# Test summary — M2-S05

Case org-wide default Private plus the criteria-based sharing rule that opens Support cases to Tier 2.

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| `xml` (always-on) | xml | PASS — 2/2 files parsed | — |
| `manifest` (always-on) | manifest | PASS — consistent | — |
| `skills/admin/sharing-and-visibility/scripts/check_sharing_model.py --manifest-dir artefacts` | checker | PASS — exit 0 | — |
| `check-outputs` | precondition for `checker` pass | PASS — `ok: true`, no missing/empty/malformed | — |
| Manual (B01 + B04) | manual | Deferred to milestone gate — GWT shape OK, names an observable outcome | — |

## Detail

### xml
2 files under `artefacts/M2-S05/`: `package.xml`, `sharingRules/Case.sharingRules-meta.xml`. Both parsed with `xml.etree.ElementTree`. Raw capture: `tests/M2-S05/xml_result.json`.

### manifest
Step type is `access` (a metadata step type) and `artefacts/M2-S05/package.xml` exists directly, so the manifest check runs rather than skipping.

- File to manifest: `sharingRules/Case.sharingRules-meta.xml` derives to type `SharingRules`, member `Case` (per `skills/admin/sharing-and-visibility/scripts/check_sharing_model.py`'s own `object_api_name()`, which strips the `.sharingRules-meta.xml` suffix to get the object). `package.xml` declares exactly `<types><name>SharingRules</name><members>Case</members></types>` — covered.
- Manifest to file: the only named, non-wildcard member is `Case` under `SharingRules`; the file exists.
- Consistent both directions.

**Observation carried, not treated as a failure (per the runner's note):** `deploy-order.md` (Decision 1) and the step's own test description both record that `skills/admin/sharing-and-visibility/references/metadata-examples.md` section 6 prescribes the rule-type form (`SharingCriteriaRule` with member `Case.Support_Cases_To_Tier_2`) rather than the container form (`SharingRules` : `Case`) actually manifested. The step deliberately used the container form because the tester derives the member from the file name, and the rule-type form would leave the file "uncovered" by this check's own logic. Both forms are reported to deploy the same file. This is recorded here as a plan-text divergence for the human gate, not scored as a manifest failure — the manifest as declared is internally consistent.

### checker — check_sharing_model.py --manifest-dir artefacts
Command run exactly as declared, from the build directory (`.sfskills/builds/case-onboarding/`), scope `build` per the plan. Exit 0.

```
{
  "score": 100,
  "findings": [],
  "summary": "Scanned 10 sharing-model metadata file(s) (1 object OWD(s) resolved); 0 finding(s) detected."
}
```

Confirms the step's own claim: at build scope the checker resolves the object OWD from `artefacts/M1-S01/objects/Case/Case.object-meta.xml` (1 object OWD resolved, as the step declares) rather than the vacuous 0-resolved result a step-scoped run would produce. Raw capture: `tests/M2-S05/checker_stdout.txt`, `tests/M2-S05/checker_stderr.txt` (empty).

### check-outputs
`python3 scripts/build_plan.py check-outputs <plan> M2-S05` returned `{"ok": true, "missing": [], "empty": [], "malformed": []}`. Raw capture: `tests/M2-S05/check_outputs.json`.

### Manual test (B01 + B04)
Not run by this agent. Checked against the Given/When/Then shape before listing: it has an explicit Given (M1-S01's `Case.object-meta.xml` + this step's `Case.sharingRules-meta.xml` read together), a When (reading them together), and a Then that names an observable outcome (`Private` sharingModel; exactly one criteria rule targeting `Support_Tier_2` on `RecordTypeId equals Support`; no rule naming Billing or `Billing_Team`; `case-visibility-model.md`'s one-sentence statement). Usable — carried into `skipped_manual[]` verbatim for the milestone gate, not counted as a failure.

### Manual grep confirmations run directly against artefacts (not tickable by this agent, reported for the gate)
- Exactly one `<sharingCriteriaRules>` block in `Case.sharingRules-meta.xml` — confirmed (count = 1).
- `sharedTo` group is `Support_Tier_2` — confirmed, no other group.
- No rule names the Billing record type or `Billing_Team` — confirmed; "Billing" appears only in the rule's free-text `<description>`, never as a `criteriaItems.value`, `sharedTo.group`, or second rule.
- The `Private` OWD lives on `artefacts/M1-S01/objects/Case/Case.object-meta.xml` (`<sharingModel>Private</sharingModel>`), not restated in this step's files — confirmed.
- No `Sharing.settings` / `*.settings-meta.xml` file anywhere under `artefacts/` — confirmed by `find` (zero results). The one textual hit for "Sharing.settings" is prose in `artefacts/M2-S04/queue-retirement-runbook.md` (a runbook note about `deferGroupMembership`), not a settings metadata file.

## Result

`passed: true`, `failed: []`. Status set to `tested`.
