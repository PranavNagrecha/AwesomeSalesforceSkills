# M1-S01 — molecular test summary

Run `2026-09-09T19-52-47Z` by `agents/step-tester`, after **rebuild #2** (finding F-11,
`reports/MOCK-DEPLOY-M1.md`). Every command below was run **verbatim as the plan declared it**,
from the build directory, after clearing the `standards/build-orchestration.md` § 5 deny-list.
Raw captures are the sibling `*.stdout` / `*.stderr` / `*.exit` files.

| # | Test | Type | Runner invoked | Exit | Result |
|---|---|---|---|---|---|
| 1 | XML well-formedness | `xml` (always-on) | `xml.etree.ElementTree` over `artefacts/M1-S01/**` | 0 | **pass** — 11 files, 11 parsed, 0 failed |
| 2 | `package.xml` consistency | `manifest` (always-on) | two-way derivation vs. manifest | 0 | **pass** — 10 files ↔ 10 members, no wildcards, 0 unmatched |
| 3 | Record types + layouts | `checker` (`scope: step`) | `check_record_type_layouts.py --manifest-dir artefacts/M1-S01` | 0 | **pass** — score 100, `2 record type(s), 0 layout(s); 0 finding(s)` |
| 4 | List views + compact layouts | `checker` (`scope: step`) | `check_list_views_and_compact_layouts.py --manifest-dir artefacts/M1-S01` | 0 | **pass** — `No issues found.` |
| 5 | Object creation + design | `checker` (no `scope`, defaults to `step`) | `check_object_creation_and_design.py --manifest-dir artefacts/M1-S01` | 0 | **pass** — `No issues found across 1 object file(s).` |
| 6 | Record-type ID management | `checker` (no `scope`, defaults to `step`) | `check_record_type_id_management.py --manifest-dir artefacts/M1-S01` | 0 | **pass** — `No record-type ID anti-patterns detected.` |
| — | Declared-output precondition | `check-outputs` | `build_plan.py check-outputs plan.json M1-S01` | 0 | **ok** — `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| 7 | Business processes beside record types | `manual` | not runnable here | — | **deferred to the M1 gate** |
| 8 | Case OWD is Private / Private | `manual` | not runnable here | — | **deferred to the M1 gate** |

`passed: true` — `failed[]` is empty. Both `checker` pass conditions held: exit 0 **and**
`check-outputs` ok.

## Observation only — not a declared acceptance test

`check_case_management_setup.py --manifest-dir artefacts/M1-S01` → **exit 0**,
`No case management setup issues found.` The rules added today, **CMS-STEM-01** (file stem must
equal `<fullName>`) and **CMS-STEM-02** (a record type's `<businessProcess>` must name an existing
process file stem), pass on the rebuilt artefacts.

The green is **earned, not fail-open**. Negative control: the same checker over the pre-rebuild
copy still committed at `examples/builds/case-onboarding/artefacts/M1-S01` (read-only, nothing
written) emits 4 `ERROR:` lines — CMS-STEM-01 ×2 on the spaced `<fullName>` values, CMS-STEM-02 ×2
on the record types pointing at them. The rules fire on the defect and are silent on the fix.

This checker is **not** in `acceptance_tests[]`, so its exit code did not contribute to
`passed`. See Process Observations in the run envelope.

## Manual checklist for the human at the M1 gate

Neither line below was ticked by this agent, and neither counts toward `failed[]`. Evidence read
from disk is in `manual-evidence.stdout` to make the tick fast — it is evidence, not a verdict.

1. Given B01, when `artefacts/M1-S01/` is listed, then two `businessProcess-meta.xml` files exist
   beside the two `recordType-meta.xml` files, each record type's `<businessProcess>` carries the
   BARE process name (not `Case.Support Process`), and `package.xml` lists `BusinessProcess` with
   object-qualified members.
   *On disk:* both process files present; `<businessProcess>Support_Process</businessProcess>` and
   `<businessProcess>Billing_Process</businessProcess>` (bare); manifest members
   `Case.Support_Process`, `Case.Billing_Process` (object-qualified).
   *Caveat for the ticker:* the counter-example in the test text, `Case.Support Process`, predates
   rebuild #2 and now names a form wrong on two counts (object-qualified **and** spaced). The
   assertion itself still holds; the parenthetical is stale.

2. B01: given the Case org-wide default is what makes "a Tier 1 agent cannot open a Billing case"
   true, when `artefacts/M1-S01/objects/Case/Case.object-meta.xml` is read, then it carries
   `<sharingModel>Private</sharingModel>` and `<externalSharingModel>Private</externalSharingModel>`
   as direct children of `<CustomObject>`, and no separate settings file anywhere in the build
   claims to carry the OWD.
   *On disk:* root `<CustomObject>`; both elements present as direct children, both `Private`. The
   only other files matching `sharingModel` across `artefacts/` are `deploy-order.md` and
   `record-type-decision.md` — prose that discusses the OWD, not settings metadata that carries it.
