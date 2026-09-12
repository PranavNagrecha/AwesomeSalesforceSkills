# step-tester — M5-S05 — results

Step: *Build-level package.xml and the deploy-order note across all five milestones* (type `docs`, agent `metadata-builder`). Status before this run: `built`.

| Test | Type | Result | First line of output |
|---|---|---|---|
| `check_deployment_manifest.py --manifest-dir artefacts/M5-S05` (step scope) | checker | PASS (exit 0) | `{"score": 95, "findings": [{"severity": "WARN", ... "manifest includes SharingRules; require explicit review and smoke tests"}], "summary": "Scanned 2 manifest or metadata file(s); 1 finding(s) detected."}` |
| `xml` | always-on | PASS | 1/1 `*.xml`/`*-meta.xml` file under `artefacts/M5-S05/` parsed with ElementTree (`package.xml` — `deploy-order.md` is markdown, not counted) |
| `manifest` | always-on | PASS (consistent) — **whole-`artefacts/` tree**, not just `artefacts/M5-S05/` | see § Manifest check detail |
| `check-outputs` | precondition | ok | `{"ok": true, "step": "M5-S05", "missing": [], "empty": [], "malformed": []}` |
| manual ×3 (W12 1/2/3) | manual | deferred to milestone gate | see Manual checklist below |

**`passed`: true.** 0 failures. `tests/M5-S05/results.json` written before the status transition, per Step 5.

## Manifest check detail — why this step reads the whole tree, not its own directory

`M5-S05`'s own artefact directory holds only `package.xml` and `deploy-order.md` — no CustomObject,
field, permission-set or any other component file. `package.xml` is the **build-level** manifest:
it aggregates the members of the 16 other steps' own manifests (`artefacts/*/package.xml`) plus
M4-S05's four Apex members, which that step declares without a manifest of its own (`standards/build-orchestration.md`
§ 5, "The Apex exception"). The step's own `acceptance_tests[2]` ("manifest") reads *"Every
type/member **produced by M5-S05** appears in package.xml and every member has a file"* — read
literally against only `artefacts/M5-S05/`, "every member has a file" would be vacuously
unsatisfiable (the directory has no component files at all), so the only reading that matches what
this step actually produces is the one `deploy-order.md` § 5.1 states explicitly: the two-way check
run "over the whole `artefacts/` tree."

`agents/step-tester/AGENT.md` Step 3 does not carry an explicit carve-out for a build-level manifest
step — its rules 2–3 are written as "for every artefact file [under the step's artefact directory]" —
so this widening is inference from the step's own declared test and from `deploy-order.md`'s own
self-check, not from an explicit branch in the playbook. Recorded as an ambiguity below and in
Process Observations, per the runner's instruction to note that the playbook has no carve-out for
this case.

**File → manifest** (every derived member from a file anywhere under `artefacts/` must appear in
`package.xml`, or be covered by a `*`): checked across all 117 files under `artefacts/`. 55 excluded
as non-deployable (17 step-level `package.xml` files including this step's own, and 38 `.md`/`.yaml`
notes/runbooks/workbook/traceability/story-backlog files — none of them a deployable component).
62 deployable files remain, 6 of them `-meta.xml` siblings that travel with a body file
(`*.cls-meta.xml` ×3, `*.trigger-meta.xml`, `*.email-meta.xml` ×2, per `skills/devops/salesforce-dx-project-structure`)
and so name no member of their own. The remaining 56 files each derive exactly one (type, member)
pair per the source-format filename-to-type mapping. **Result: every derived member appears in the
manifest. 0 missing.**

**Manifest → file** (every named, non-wildcard member in `package.xml` must have a backing file
somewhere under `artefacts/`): 29 types, 56 members, no wildcards anywhere in this manifest.
**Result: every member has a backing file. 0 missing.**

Both directions match `deploy-order.md` § 5.1's own count ("All 56 members resolve to a file... All
62 deployable files under `artefacts/` are covered by a member").

Full working (file classification, per-type member lists, both directions) is in
`tests/M5-S05/manifest_check_wholetree.txt`.

## Raw captures

- `tests/M5-S05/xml_check.txt` — per-file parse result for the 1 XML file under `artefacts/M5-S05/`
- `tests/M5-S05/checker_stdout.txt`, `tests/M5-S05/checker_stderr.txt` — the declared checker's captured output
- `tests/M5-S05/manifest_check_wholetree.txt` — the whole-tree file↔manifest cross-check, both directions, with the excluded-file and sibling lists
- `tests/M5-S05/check_outputs.json` — `build_plan.py check-outputs` result

## Manual checklist (verbatim, for the milestone gate)

Each checked against the Given/When/Then shape before listing; none flagged unusable — each names
an observable outcome. This agent does not tick any of them.

1. > W12 (1 of 3): a release owner confirms the deploy-order note contains no deploy command, only a
   > validate-only command they may choose to run themselves.

   If/then-shaped rather than literal Given/When/Then, but it names an actor (release owner), an
   artefact (`deploy-order.md`) and a binary observable (absence of any `sf … deploy` line; presence
   of exactly one validate-only command). Tickable as written.

2. > W12 (2 of 3): given two steps ship nothing in this phase, when deploy-order.md and package.xml
   > are read, then M3-S05 and M5-S02 are listed as excluded with their blocked reasons verbatim
   > rather than silently absent, and no Omni-Channel or sandbox component appears as a manifest
   > member.

   Full Given/When/Then. Two observables named (verbatim blocked-reason strings; absence of a named
   component family from the manifest). Tickable as written.

3. > W12 (3 of 3): given the build-level manifest aggregates every step's members, when package.xml
   > is read, then the order in deploy-order.md follows admin/case-management-setup/references/metadata-examples.md
   > § 5 — StandardValueSet before the business processes and record types, queues and groups before
   > the assignment and escalation rules that name them, Settings named explicitly as Case and Flow
   > because feature settings do not accept the wildcard — and ApexClass and ApexTrigger members
   > from M4-S05 are present here, because that step declares no manifest of its own (B09).

   Full Given/When/Then. Observable outcomes named (a specific ordering, and the presence of two
   named component types). Tickable as written.

Verifying that the referenced facts hold (the release-owner read, the verbatim blocked-reason text,
the deploy-order sequence) is the milestone gate's read, not a molecular test declared on this step.
