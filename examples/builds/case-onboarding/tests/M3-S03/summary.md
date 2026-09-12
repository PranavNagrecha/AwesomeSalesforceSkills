# step-tester — M3-S03 (rebuild) — results summary

Build: `.sfskills/builds/case-onboarding` · step `M3-S03` (routing) · rebuilt artefacts (run
`2026-09-12T04-39-20Z`), tested after `build-step-runner` set the step back to `built`
(run `2026-09-12T04-46-00Z`).

| # | Test | Type | Result | First line of output |
|---|---|---|---|---|
| 1 | `check_case_management_setup.py --manifest-dir artefacts` (declared, build scope) | checker | **PASS** (exit 0, check-outputs ok) | `No case management setup issues found.` |
| 2 | XML well-formedness | xml | **PASS** (2/2 parsed) | — |
| 3 | Manifest consistency | manifest | **PASS** (consistent) | `Settings:Case` member matches `settings/Case.settings-meta.xml` |
| 4 | Manual — Case.settings-meta.xml field-level GWT | manual | deferred to milestone gate | — |
| 5 | Manual — web-to-case-form-contract.md GWT | manual | deferred to milestone gate | — |

`passed: true` — `failed` is empty. Full checker stdout/stderr and `check-outputs` JSON are in this
directory (`check_case_management_setup.stdout.txt`, `.stderr.txt`, `.exitcode.txt`,
`check-outputs.json`).
