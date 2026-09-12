# M1-S01 — molecular test summary

Run `2026-09-12T00-21-00Z` by `agents/step-tester`, after **rebuild #3** (finding F-13,
`reports/MOCK-DEPLOY-M1.md` mock deploy #3): `package.xml`'s `CompactLayout` member
`Case_Intake` was rewritten to the object-qualified `Case.Case_Intake`, per
`admin/list-views-and-compact-layouts` v1.2.0 rules CL-MEM-01/CL-MEM-02. All 12 other declared
artefacts are byte-identical to the rebuild #2 state per the metadata-builder run record. Every
command below was run **verbatim as the plan declared it**, from the build directory, after
clearing the `standards/build-orchestration.md` § 5 deny-list. Raw captures are the sibling
`*.stdout` / `*.stderr` / `*.exit` files.

| # | Test | Type | Runner invoked | Exit | Result |
|---|---|---|---|---|---|
| 1 | XML well-formedness | `xml` (always-on) | `xml.etree.ElementTree` over `artefacts/M1-S01/**` | 0 | **pass** — 11 files, 11 parsed, 0 failed |
| 2 | `package.xml` consistency | `manifest` (always-on) | two-way derivation vs. manifest | 0 | **pass** — 10 files ↔ 10 members, no wildcards, 0 unmatched; `CompactLayout` member now object-qualified (`Case.Case_Intake`) and matched against the file the same way |
| 3 | Record types + layouts | `checker` (`scope: step`) | `check_record_type_layouts.py --manifest-dir artefacts/M1-S01` | 0 | **pass** — score 100, `2 record type(s), 0 layout(s); 0 finding(s)` |
| 4 | List views + compact layouts | `checker` (`scope: step`) | `check_list_views_and_compact_layouts.py --manifest-dir artefacts/M1-S01` | 0 | **pass** — `No issues found.` — CL-MEM-01/02 clean on the object-qualified member |
| 5 | Object creation + design | `checker` (no `scope`, defaults to `step`) | `check_object_creation_and_design.py --manifest-dir artefacts/M1-S01` | 0 | **pass** — `No issues found across 1 object file(s).` |
| 6 | Record-type ID management | `checker` (no `scope`, defaults to `step`) | `check_record_type_id_management.py --manifest-dir artefacts/M1-S01` | 0 | **pass** — `No record-type ID anti-patterns detected.` |
| — | Declared-output precondition | `check-outputs` | `python3 scripts/build_plan.py check-outputs .sfskills/builds/case-onboarding/plan.json M1-S01` | 0 | **ok** — `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| 7 | Business processes beside record types | `manual` | not runnable here | — | **deferred to the M1 gate** |
| 8 | Case OWD is Private / Private | `manual` | not runnable here | — | **deferred to the M1 gate** |

`passed: true` — `failed[]` is empty. Both `checker` pass conditions held on all four declared
checkers: exit 0 **and** `check-outputs` ok.

## Manifest test detail (rebuild #3 delta)

The AGENT.md's stated file→member derivation assumes a bare stem for a `CompactLayout` member,
but this step's `package.xml` now carries the object-qualified form (`Case.Case_Intake`) per
mock-deploy finding F-13 — the org itself requires object-qualification for `CompactLayout`
members, and `admin/list-views-and-compact-layouts` was bumped to v1.2.0 to encode that as
CL-MEM-01/CL-MEM-02. Per this run's own instruction, this is recorded here as a **tester-logic
observation, not a step failure**: the manifest derivation applied in this run accepted the
object-qualified member as covering the file `objects/Case/compactLayouts/Case_Intake.compactLayout-meta.xml`,
and the manifest test still reads **consistent**. See Process Observations in the run envelope.

## Observation only — not a declared acceptance test

`check_case_management_setup.py --manifest-dir artefacts/M1-S01` → **exit 0**,
`No case management setup issues found.` Unaffected by the rebuild #3 delta (it does not
inspect `CompactLayout` members); rules CMS-STEM-01/02 (added at rebuild #2) remain clean.

This checker is **not** in `acceptance_tests[]`, so its exit code did not contribute to
`passed`.

## Manual checklist for the human at the M1 gate

Neither line below was ticked by this agent, and neither counts toward `failed[]`. Evidence read
from disk is in `manual-evidence.stdout` to make the tick fast — it is evidence, not a verdict.

1. Given B01, when `artefacts/M1-S01/` is listed, then two `businessProcess-meta.xml` files exist
   beside the two `recordType-meta.xml` files, each record type's `<businessProcess>` carries the
   BARE process name (not `Case.Support Process`), and `package.xml` lists `BusinessProcess` with
   object-qualified members.
   *On disk (unchanged since rebuild #2):* both process files present; both record types carry
   the bare `<businessProcess>Support_Process</businessProcess>` / `<businessProcess>Billing_Process</businessProcess>`;
   manifest members `Case.Support_Process`, `Case.Billing_Process` (object-qualified).

2. B01: given the Case org-wide default is what makes "a Tier 1 agent cannot open a Billing case"
   true, when `artefacts/M1-S01/objects/Case/Case.object-meta.xml` is read, then it carries
   `<sharingModel>Private</sharingModel>` and `<externalSharingModel>Private</externalSharingModel>`
   as direct children of `<CustomObject>`, and no separate settings file anywhere in the build
   claims to carry the OWD.
   *On disk (unchanged since rebuild #2):* root `<CustomObject>`; both elements present as direct
   children, both `Private`. The only other files matching `sharingModel` across `artefacts/` are
   `deploy-order.md` and `record-type-decision.md` — prose that discusses the OWD, not settings
   metadata that carries it.
