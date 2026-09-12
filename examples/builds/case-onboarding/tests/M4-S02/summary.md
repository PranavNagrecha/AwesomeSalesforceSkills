# Test results — M4-S02 (Entitlement processes + First Response milestone type)

Run by `step-tester`, from the build directory (`.sfskills/builds/case-onboarding/`), against a step
whose status was `built`. All commands run verbatim as declared in `plan.json`
`steps[M4-S02].acceptance_tests[]`; nothing was rewritten, no path substituted.

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| always-on `xml` | xml | PASS — 4/4 files parse | — |
| always-on `manifest` | manifest | PASS — consistent both directions | — |
| `check_entitlements_and_milestones.py --manifest-dir artefacts --strict` | checker | PASS — exit 0, check-outputs ok | — |
| A27 file-count / minutesToComplete / businessHours-name manual line | manual | deferred to milestone gate | n/a |

## Detail

### xml (always-on)

Parsed every `*.xml` / `*-meta.xml` under `artefacts/M4-S02/` with `xml.etree.ElementTree`, recursively:

- `artefacts/M4-S02/entitlementProcesses/First_Response_Premier.entitlementProcess-meta.xml` — parsed
- `artefacts/M4-S02/entitlementProcesses/First_Response_Standard.entitlementProcess-meta.xml` — parsed
- `artefacts/M4-S02/milestoneTypes/First Response.milestoneType-meta.xml` — parsed
- `artefacts/M4-S02/package.xml` — parsed

4/4 parsed, 0 failed. Raw capture: `tests/M4-S02/xml_check.txt`.

### manifest (always-on)

`package.xml` exists under `artefacts/M4-S02/` (declared in `outputs[]`).

File → manifest (per `skills/devops/salesforce-dx-project-structure` folder/file → type/member
mapping): `entitlementProcesses/First_Response_Premier.entitlementProcess-meta.xml` →
`EntitlementProcess.First_Response_Premier`; `entitlementProcesses/First_Response_Standard.…` →
`EntitlementProcess.First_Response_Standard`; `milestoneTypes/First Response.milestoneType-meta.xml`
→ `MilestoneType.First Response`. All three derived members appear as literal `<members>` entries
(no wildcard used) in `package.xml`.

Manifest → file: every non-wildcard `<members>` entry in `package.xml`
(`First_Response_Premier`, `First_Response_Standard` under `EntitlementProcess`; `First Response`
under `MilestoneType`) has a corresponding file on disk. No exclusions from
`skills/devops/metadata-api-coverage-gaps` apply — neither `EntitlementProcess` nor `MilestoneType`
is a no-standalone-file type.

Consistent both directions.

### checker — `check_entitlements_and_milestones.py --manifest-dir artefacts --strict`

Run exactly as declared (`scope: build`), from the build directory:

```text
$ python3 skills/admin/entitlements-and-milestones/scripts/check_entitlements_and_milestones.py --manifest-dir artefacts --strict
INFO  W4  [First_Response_Premier.entitlementProcess-meta.xml] Milestone 'First_Response_Premier / First Response' has neither <timeTriggers> nor <successActions>: ...
INFO  W4  [First_Response_Standard.entitlementProcess-meta.xml] Milestone 'First_Response_Standard / First Response' has neither <timeTriggers> nor <successActions>: ...

0 error(s), 0 warning(s), 2 info note(s).
OK: no ERROR findings.
EXIT=0
```

Full capture: `tests/M4-S02/checker_stdout.txt` / `checker_stderr.txt` / `checker_exit.txt`. The two
W4 findings are INFO, not WARN, since `admin/entitlements-and-milestones` commit `a18f9164d`
(v1.1.2) — `--strict` promotes only ERROR/WARN, never INFO, so these do not fail the gate. This
matches `artefacts/M4-S02/deploy-order.md` § 0's own re-run of the same command.

`check-outputs`:

```json
{"ok": true, "step": "M4-S02", "missing": [], "empty": [], "malformed": []}
```

Full capture: `tests/M4-S02/check_outputs.json`. Checker exit 0 **and** check-outputs ok -> PASS.

### manual — deferred to the milestone gate

> Given assumption A27, when `artefacts/M4-S02/` is listed, then it holds exactly two
> `entitlementProcesses` files (`First_Response_Premier`, `First_Response_Standard`) and exactly one
> `milestoneTypes` file (`First Response`), the Premier process carries `minutesToComplete` 240, and
> both processes name a `<businessHours>` that is a `<name>` in M4-S01's BusinessHours settings file.

Checked against the Given/When/Then shape (`skills/admin/acceptance-criteria-given-when-then`) and
the UAT testability bar (`skills/admin/uat-and-acceptance-criteria` — a criterion must be boolean,
observable pass/fail): this line names an explicit Given (A27), an explicit When (list the
directory), and a Then made of concrete, checkable facts — two exact file names, one exact file
count per subfolder, one exact numeric value, and one exact cross-file name match. It names an
observable outcome and is tickable by a human without re-interpretation. Not flagged as unusable.
Not ticked here — this agent does not tick manual tests. Carried verbatim to `milestone-verifier`
and the M4 gate.

## Process Observations (from this test run only — see the run envelope for the full block)

- **Healthy.** The checker's own W4 finding, once corrected to INFO by `a18f9164d`, is exactly
  consistent with this step's own design record (`milestone-completion-decision.md` D10): completion
  is an after-update Apex trigger in M4-S05, not a workflow action, so an action-less milestone here
  is intended, not an oversight.
- **Concerning.** Nothing new beyond what `deploy-order.md` §§ 1-7 already records as open at the M4
  gate (derived 720 minutes for Standard, file-name case vs `NameNorm`, member form with versioning
  off, the EMEA-case-on-US-hours split, and `Settings:Entitlement` owned by no step). This run adds
  no new finding — it re-confirms the artefacts are unchanged from the run those items were written
  against.
- **Ambiguous.** None encountered by this test run; the ambiguity that previously blocked this step
  was closed at the source before this run started (commit `a18f9164d`), per `plan.json`
  `steps[M4-S02].runs[]` and `deploy-order.md` § 0.
- **Suggested follow-ups.** `build-doc-keeper` next, now that the step is `tested`. `milestone-verifier`
  once every M4 step is `documented`, to carry the manual line and the seven open items in
  `deploy-order.md` into the M4 acceptance report.
