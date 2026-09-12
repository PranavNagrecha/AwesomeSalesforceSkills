# Test summary — M1-S05

Build `tier2-webhook` · step `M1-S05` (`docs`, owner `metadata-builder`) · this run

Re-run after metadata-builder regenerated `artefacts/M1-S05/package.xml` at
`2026-09-12T18-18-48Z` to add the `Tier2WebhookFinalizerTest` `ApexClass` member (closing
M1-S03's S2-F-14 repair, `artefacts/M1-S03/deploy-order.md` § 0d). This tester re-derives the
whole-tree manifest independently rather than re-using the prior 34-member run's captures,
which are now stale and are overwritten below.

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| always-on `xml` | xml | PASS (1 file parses) | — |
| always-on `manifest` (build-wide, spans M1-S01..S04) | manifest | PASS (35/35 members, 54 backing files, bidirectionally consistent) | — |
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
every type with no carve-out. Every file under `artefacts/M1-S01`–`M1-S04` mapped cleanly to a type;
the derivation script raised zero "unmapped file" cases.

**Direction 1 — file to manifest.** 35 derived members (2 `CustomObject`, 13 `CustomField`, 1
`ExternalCredential`, 1 `NamedCredential`, **15** `ApexClass`, 2 `ApexTrigger`, 1 `PermissionSet`),
`TestDataFactory` counted once even though both M1-S03 and M1-S04 ship a copy (`artefacts/M1-S03/classes/TestDataFactory.cls`
and `artefacts/M1-S04/classes/TestDataFactory.cls` both map to the single `ApexClass:TestDataFactory`
member — a member-identity fact, not a collision, matching D-M1S03-06/D-M1S04-06).
`Tier2WebhookFinalizerTest` (new since the prior test run) derives from
`artefacts/M1-S03/classes/Tier2WebhookFinalizerTest.cls` (+ `-meta.xml`). Every derived member is
covered by a literal `<name>`/`<members>` pair in `artefacts/M1-S05/package.xml` — no wildcards exist
to check against. No member without a file.

**Direction 2 — manifest to file.** Every one of the manifest's 35 non-wildcard `<members>` entries
has a backing file, including the new `Tier2WebhookFinalizerTest` entry. No member without a file.

Totals: manifest 35 members / derived 35 members, 54 backing files reconciled exactly (12 M1-S03
classes × 2 files + 2 M1-S03 triggers × 2 files + 4 M1-S04 classes × 2 files + 15 M1-S01 object/field
files + 3 M1-S02 credential/permission-set files = 54), 0 missing either direction.

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
more and no fewer, both non-blocking — unchanged in shape from the prior 34-member run despite the
member-count and content changes, since neither WARN is about `ApexClass`. `check-outputs` for M1-S05
(run from the repo root, since it takes `<build_dir>/plan.json` as its own argument) reports
`{"ok": true, "missing": [], "empty": [], "malformed": []}`, so both halves of the checker's pass
condition hold.

### 4. `manual` — Deploy-order read at the M1 gate

Not run here; deferred to the milestone gate per the always-on rule for `manual` tests. Checked
against the testability bar (`admin/uat-and-acceptance-criteria` — acceptance criteria must be
boolean/observable before UAT begins — and `admin/acceptance-criteria-given-when-then`'s
Given/When/Then anatomy, specifically that a Then names a concrete observable outcome) before being
carried forward: the test's `expected` text is not phrased as literal Given/When/Then, but it names
five concrete, boolean-checkable items plus one framing check, and this run re-read
`artefacts/M1-S05/deploy-order.md` directly and confirmed it still contains all six rather than
assuming the prior run's finding still holds:

- § 3 lists the five manual steps by number, each with an owner and a "when": confirm the
  `AuthHeader` formula, enter the API key against the `OnCall_Tool_EC` principal, assign
  `Tier2_Webhook_Admin` to the D14 assignee set, register the hourly scheduled job, confirm the
  org-wide sender is verified.
- § 7 confirms the `mock_deploy.py --mode manifest` invocation is written as prose for a human to
  run, with an explicit "never for an agent" statement in the section heading itself.

So the test is tickable as declared and is carried into `skipped_manual[]` verbatim.

**The AuthHeader clause inside this manual checklist's source input is pre-amendment prose, still
unchanged.** `deploy-order.md` § 3 Step 1 still carries the same correction this tester's prior runs
reported: the plan's `inputs.manual_steps_the_deploy_does_not_perform` item 1 quotes stale framing
(treating the AuthHeader formula as fully open), while decision **D-M1S02-06** / finding **PV-007**
record that the parameter name and formula are closed (`{!$Credential.OnCall_Tool_EC.ApiKey}`,
principal parameter `ApiKey`) and only two narrower items remain open — grammar-parses-on-deploy and
header-carries-key-at-runtime. This tester does not rewrite the plan's `acceptance_tests[3].expected`
text or the `inputs` field — both are step-tester read-only per the Scope Guardrails — and reports the
divergence rather than acting on it, same as the prior runs.

## Command log

```
$ python3 skills/admin/change-management-and-deployment/scripts/check_deployment_manifest.py --manifest-dir artefacts/M1-S05
(exit 0; see checker.stdout.txt / checker.stderr.txt)

$ python3 scripts/build_plan.py check-outputs .sfskills/builds/tier2-webhook/plan.json M1-S05   # run from repo root
(exit 0; see check-outputs.json)
```

Raw captures: `tests/M1-S05/checker.stdout.txt`, `tests/M1-S05/checker.stderr.txt`,
`tests/M1-S05/check-outputs.json`, `tests/M1-S05/xml-check.txt`, `tests/M1-S05/manifest-check.txt`.
All five were overwritten by this run with fresh captures against the 35-member manifest; none of
the prior run's (34-member) captures survive on disk.
