# M4-S04 tests (step-tester)

| Test | Type | Runner | Exit | Result |
|---|---|---|---|---|
| xml | always-on | ElementTree over `artefacts/M4-S04/**/*.xml` (1 file: package.xml) | n/a | pass, 1 of 1 parsed (`xml_check.txt`) |
| manifest | always-on, whole-tree | `manifest_check_wholetree.py`: 23 types / 38 members vs files under every step's `artefacts/` | 0 | pass, consistent, 0 unclassified, no wildcard (`manifest_check_wholetree.txt`) |
| check_deployment_manifest.py --manifest-dir artefacts/M4-S04 | checker (scope step) | declared command, verbatim, from build dir | 0 | pass, score 100, 0 findings (`checker_stdout.txt`) |
| check-outputs M4-S04 | precondition | `scripts/build_plan.py check-outputs` | 0 | ok, 2/2 outputs, hashes recorded |
| 10 manual tests (4-13) | manual | not runnable here | n/a | deferred: 6 to the M4 gate, 4 post-deploy UAT (tests 8, 9, 10, 12); all Given/When/Then with an observable outcome |

The declared `manifest` test is judged whole-tree because package.xml is the build-level manifest: every member's file lives under another step's artefacts/ folder (case-onboarding M5-S05 precedent). Failing it for files absent under artefacts/M4-S04/ would be wrong.
