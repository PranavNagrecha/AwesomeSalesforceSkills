# Test summary — M1-S05

Build `tier2-webhook` · step `M1-S05` (`docs`, owner `metadata-builder`) · run `2026-09-12T12-25-04Z`

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| always-on `xml` | xml | PASS (1 file parses) | — |
| always-on `manifest` (build-wide, spans M1-S01..S04) | manifest | PASS (33/33 members, bidirectionally consistent) | — |
| `check_deployment_manifest.py --manifest-dir artefacts/M1-S05` | checker | PASS (exit 0; 2 WARN, 0 blocking) | — |
| `check-outputs` (checker precondition) | — | PASS (ok: true) | — |
| Deploy-order read at the M1 gate | manual | deferred to milestone gate (not ticked here) | — |

`passed: true`. 3 runnable tests ran and passed; 1 manual test deferred; both always-on checks completed.

## Detail

### 1. `xml` (always-on, Step 2)

Parsed every `*.xml` / `*-meta.xml` under `artefacts/M1-S05/`: one file, `package.xml`. Parses cleanly.

### 2. `manifest` (always-on, Step 3 — and the declared `manifest` acceptance test, same treatment)

This step's `package.xml` exists (no fail-vs-skip branch needed). Its own test description requires
the two-way check to span the build's aggregated members, so the check read every file under
`artefacts/M1-S01`, `M1-S02`, `M1-S03` and `M1-S04` in addition to `M1-S05` itself (which carries no
component files of its own — only `package.xml` and `deploy-order.md`).

File-to-metadata-type mapping followed `skills/devops/salesforce-dx-project-structure`'s source-format
tree: `objects/<Obj>/<Obj>.object-meta.xml` → `CustomObject`; `objects/<Obj>/fields/<f>.field-meta.xml`
→ `CustomField` member `<Obj>.<f>`; `classes/*.cls`(`-meta.xml`) → `ApexClass`; `triggers/*.trigger`
(`-meta.xml`) → `ApexTrigger`; `externalCredentials/*.externalCredential-meta.xml` →
`ExternalCredential`; `namedCredentials/*.namedCredential-meta.xml` → `NamedCredential`;
`permissionsets/*.permissionset-meta.xml` → `PermissionSet`. `package.xml` and `*.md` notes under each
step are not components and are excluded from both directions, per Step 3.5.

No `skills/devops/metadata-api-coverage-gaps` exclusion applies: none of the seven types present here
(`CustomObject`, `CustomField`, `ExternalCredential`, `NamedCredential`, `ApexClass`, `ApexTrigger`,
`PermissionSet`) is documented there as lacking a standalone source file, so both directions run over
every type with no carve-out.

**Direction 1 — file to manifest.** 33 derived members (2 `CustomObject`, 13 `CustomField`, 1
`ExternalCredential`, 1 `NamedCredential`, 13 `ApexClass`, 2 `ApexTrigger`, 1 `PermissionSet`),
`TestDataFactory` counted once even though both M1-S03 and M1-S04 ship a copy. Every derived member
is covered by a literal `<name>`/`<members>` pair in `artefacts/M1-S05/package.xml` — no wildcards
exist to check against. No member without a file.

**Direction 2 — manifest to file.** Every one of the manifest's 33 non-wildcard `<members>` entries
has a backing file. No member without a file.

**TestDataFactory — recorded as consistent, not a defect.** `artefacts/M1-S03/classes/TestDataFactory.cls`
and `artefacts/M1-S04/classes/TestDataFactory.cls` are byte-identical (SHA-256
`2f87c8c320406e1c8381f26862cdcc17130a9fe2f8a133f098ab64a271de782c`), their `.cls-meta.xml` siblings
are byte-identical (SHA-256 `a242f6e22b472afffbd726be71165de394e417355cdf1edd81b5601278ddea32`), and
both match `templates/apex/tests/TestDataFactory.cls` exactly. The manifest carries the member once.
Two source files backing one member, with identical bytes, is consistent — the discharge of decision
D-M1S03-06 checked out on inspection, not merely trusted from the prior envelope.

Totals: manifest 33 members / derived 33 members, 0 missing either direction.

### 3. `checker` — `python3 skills/admin/change-management-and-deployment/scripts/check_deployment_manifest.py --manifest-dir artefacts/M1-S05`

Run verbatim as declared, from the build directory (`skills` symlink resolves it).

```
{
  "score": 90,
  "findings": [
    {"severity": "WARN", "location": "artefacts/M1-S05/package.xml", "message": "manifest includes ExternalCredential; require explicit review and smoke tests"},
    {"severity": "WARN", "location": "artefacts/M1-S05/package.xml", "message": "manifest includes NamedCredential; require explicit review and smoke tests"}
  ],
  "summary": "Scanned 2 manifest or metadata file(s); 2 finding(s) detected."
}
```

Exit code 0. Exactly the two WARN findings the step's own acceptance-test description predicted, no
more and no fewer, both non-blocking. `check-outputs` for M1-S05 (run from the repo root, since it
takes `<build_dir>/plan.json` as its own argument) reports `{"ok": true, "missing": [], "empty": [],
"malformed": []}`, so both halves of the checker's pass condition hold.

### 4. `manual` — Deploy-order read at the M1 gate

Not run here; deferred to the milestone gate per the always-on rule for `manual` tests. Checked
against the testability bar (`admin/uat-and-acceptance-criteria` — "must be boolean, observable" —
and `admin/acceptance-criteria-given-when-then`'s Given/When/Then anatomy) before being carried
forward: the test's `expected` text is not phrased as literal Given/When/Then, but it names a
concrete, boolean-checkable outcome — a reviewer confirms five specific named items appear in
`deploy-order.md`, and confirms the `mock_deploy.py` invocation is written as prose rather than
something an agent runs — so it is tickable as declared and is carried into `skipped_manual[]`
verbatim rather than reported as unusable.

**The AuthHeader clause inside this manual checklist's source input is pre-amendment prose, recorded
verbatim.** The step's own `inputs.manual_steps_the_deploy_does_not_perform` field — the source
`deploy-order.md` § 1 quotes directly — still reads, item 1, exactly:

> "Confirm the X-API-Key AuthHeader parameterValue formula against Salesforce Help before the
> External Credential is deployed - assumption A5 records that merge-field grammar as UNVERIFIED in
> the cited skill, which says to confirm it or build the header in Apex instead."

`artefacts/M1-S05/deploy-order.md` § 3 Step 1 itself calls this framing stale ("That framing predates
two events and overstates what is still open") and records the corrected reading under decision
**D-M1S02-06** / finding **PV-007**: the parameter name and formula are now closed by a human answer
(`{!$Credential.OnCall_Tool_EC.ApiKey}`, principal parameter `ApiKey`), and what remains open is
narrower — (a) the grammar parsing on deploy, confirmed by the next manifest-mode `mock_deploy.py`
dry run, and (b) the header actually carrying the key at run time, confirmed only at UAT. This
tester does not rewrite the plan's `acceptance_tests[3].expected` text or the `inputs` field — both
are step-tester read-only per the Scope Guardrails — and reports the divergence rather than acting on
it, consistent with the metadata-builder and build-step-runner envelopes, which flagged the same
prose lag from their own runs.

## Command log

```
$ python3 skills/admin/change-management-and-deployment/scripts/check_deployment_manifest.py --manifest-dir artefacts/M1-S05
(exit 0; see checker.stdout.txt / checker.stderr.txt)

$ python3 scripts/build_plan.py check-outputs .sfskills/builds/tier2-webhook/plan.json M1-S05   # run from repo root
(exit 0; see check-outputs.json)
```

Raw captures: `tests/M1-S05/checker.stdout.txt`, `tests/M1-S05/checker.stderr.txt`,
`tests/M1-S05/check-outputs.json`, `tests/M1-S05/xml-check.txt`, `tests/M1-S05/manifest-check.txt`.
