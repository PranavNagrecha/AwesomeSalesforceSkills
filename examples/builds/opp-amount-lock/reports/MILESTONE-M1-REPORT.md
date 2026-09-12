# Milestone M1 — acceptance report

`opp-amount-lock` · scale `ask` · design-only · verified 2026-09-12T08:20:00Z by `milestone-verifier`

## Verdict: `ready-with-findings` — confidence MEDIUM

Every check that can be run without an org passed: no unresolved reference, no ordering
contradiction, no failing test, no blocked step. Eleven findings are recorded; **three change what
you do before ticking** (F-02, F-05, F-08). Approving this gate accepts all eleven.

**M1 built one step, `M1-S01` (`documented`, agent `metadata-builder`):** a `ValidationRule`
`Opportunity.Amount_Locked_After_Closed_Won`, active, that blocks a save lowering `Amount` on a
Closed Won Opportunity for anyone without `Bypass_Opp_Amount_Lock`; the `CustomPermission` itself;
and `PermissionSet Opp_Amount_Lock_Bypass`, which grants it. Error message 199 chars (255 ceiling),
on the `Amount` field.

## What was checked

| Check | Result |
|---|---|
| `$Permission.Bypass_Opp_Amount_Lock` ↔ CustomPermission filename stem ↔ PermissionSet `<name>` | **identical** — the one cross-reference this milestone turns on |
| `Amount`, `StageName`, `errorDisplayField` | standard Opportunity fields; resolve against the platform, not against a build artefact |
| Assignment rules, Flow, entitlement milestones, layouts/paths | not run — M1 ships no such artefact |
| Deployment order | `CustomPermission` → (`PermissionSet` ‖ `ValidationRule`); no backwards dependency. The permission set grants no field or object permission, so the grant-before-field failure cannot arise. All three ship in one manifest |
| `package.xml`, two-way | consistent — 3 types, 3 members, 3 files, 1:1, no wildcards, no member without a file |
| API version | single `<version>67.0</version>`, no conflict. Matches the version the operator's dry run used on a scratch copy of the formula (3/3, per `deploy-order.md`) |
| Merged manifest | `reports/MILESTONE-M1-package.xml`. One file under the artefacts reaches no `<types>` block: `deploy-order.md` (F-01) |
| Milestone acceptance tests | M1 declares one and it is `manual` → the checklist below. **No exit code in this build stands for the milestone as a whole** (F-04); every green result is step-scoped (`tests/M1-S01/results.json`: ran 4, failed 0, `check-outputs` ok) |

This agent ran no `sf` command, no `mock_deploy.py`, and re-ran no step test.

## The checklist — you tick these

1. ☐ **Block half.** As a Sales user *without* `Bypass_Opp_Amount_Lock`, lower `Amount` on a Closed
   Won Opportunity and save → blocked, error verbatim: *"Amount cannot be decreased once this
   Opportunity is Closed Won. Amount is locked after close to protect the recorded deal value.
   Contact your manager to reopen the Opportunity before changing Amount."*
2. ☐ **Bypass half.** As a Sales Ops user *holding* `Opp_Amount_Lock_Bypass`, same edit → saves.
   **The permission set deploys with no assignees.** Assign it to the two named Sales Ops users
   first, or this half cannot pass (F-02).
3. ☐ Record the sandbox name and refresh date, and the two named test users — otherwise the tick is
   an opinion, not evidence, and an admin's pass proves nothing about a persona (F-03).
4. ☐ Confirm `Amount` is on the Opportunity layout(s) in scope (assumption **A1**); if not, the error
   relocates to Top of Page and line 1's outcome changes.
5. ☐ Confirm no permission set named `Opp_Amount_Lock_Bypass` already exists in the target org — a
   `PermissionSet` deploy is a full replace from API 40.0 and silently drops anything not in this
   file (F-08).
6. ☐ Accept knowingly, as already recorded at `go`: `active=true` over a handful of historical
   lowered Amounts (**D2**); the per-rule bypass name rather than the per-domain form (W5); the
   access grant behind no step gate (W1, forced by § 3.1 at `ask`).

## Findings

Evidence and remedy per finding: `findings[]` in `envelopes/M1/2026-09-12T08-20-00Z.json`.

| Id | Sev | Finding |
|---|---|---|
| **F-02** | P1 | The permission set deploys unassigned, so the bypass half of the only acceptance test is untickable as written. No plan step owns the assignment. |
| **F-05** | P1 | The printed validate-only command cannot run: there is no `sfdx-project.json` in the build dir or at the repo root, and it is required for all `sf` CLI operations. Copy the artefacts into an SFDX project first. |
| **F-08** | P1 | `PermissionSet` deploys are a full replace (API 40.0+) and this one was authored from scratch — correct only if the name is free in the target org. Design-only build; cannot be settled here. |
| F-01 | P2 | `deploy-order.md` is written every run but is absent from `outputs[]` and from every `<types>` block, so `check-outputs` never adjudicates it (verifier W8, open across both builder runs). |
| F-03 | P2 | The manual test names no environment, no tester and no build date. |
| F-04 | P2 | M1's only acceptance test is `manual`: § 5's "≥ 1 test" is met while nothing automated covers the milestone (verifier W2, accepted at `go`). |
| F-06 | P2 | `deploy-order.md` leads with `sf project deploy validate` — production-only, requires Apex tests — for an org-free build. Its command also combines `--manifest` and `--source-dir`; the library writes them as alternatives in five places and combines them in one, so this run could not settle that offline. |
| F-07 | P2 | Verifier **W3 is not closed**. W3 names `check_custom_permissions.py`; commit `8225051d9` changed `check_validation_rules.py`. Re-run this milestone, the custom-permissions checker still exits 0 with zero findings on an empty directory. No impact here — `check-outputs` is the build-loop guard and returned ok. |
| F-09 | P2 | `scale: ask` was sized `D=1 metadata type`; M1 ships **three**, which is `D=3` → `feature`. The count was honest when taken — the two access artefacts came from the answer to Q3, after the tier was fixed. § 3.1 reads the requirement before the clarifications that create the metadata. |
| F-10 | P2 | `drivers-log.md` friction (18) records that `decisions.md` is now appended at every scale; § 3.1, `build-doc-keeper`'s AGENT.md and this build's `decisions.md` all still say otherwise. |
| F-11 | INFO | `set-milestone`'s next-command hint prints `milestone:M1`, not the `ask`-scale `accept` alias promised by § 3.1 and `RUN.md`. Same record, two spellings. |

## Requirements closed

`traceability.md` is the init stub — correct at `ask`, where § 3.1 freezes it — so closure is stated
from `plan.json`. The single `fit_gap[]` requirement, *"Lock Opportunity.Amount against a decrease
once Closed Won, with a Sales-Ops-only bypass"* (`fit`, step `M1-S01`), is **built and step-tested**;
it is **not proven** until checklist lines 1–2 are ticked. Nothing else in scope, nothing left open.
A1–A6 remain assumptions; A1 is on the checklist.

## Optional — you run this, no agent does. Nothing in this build deploys.

```bash
# sandbox / scratch org: validates without saving. Run from an SFDX project (F-05).
sf project deploy start \
  --manifest .sfskills/builds/opp-amount-lock/reports/MILESTONE-M1-package.xml \
  --dry-run --target-org <alias>
```

For a **production** target the command is `sf project deploy validate` with the same manifest: it is
documented as production-only, requires Apex tests, and returns a job id for a later quick deploy.

## The gate — yours

```bash
python3 scripts/build_plan.py gate .sfskills/builds/opp-amount-lock/plan.json \
  accept approve --by "<name>" --notes "<what you ticked>"
```

`accept` is the `ask` alias that writes `milestone:M1`. It is refused unless the `plan` gate is
approved and every step in M1 is `documented` — both true as of this report. Printed here, not run.

Verdict recorded with `build_plan.py set-milestone … M1 --status verified --report-path
reports/MILESTONE-M1-REPORT.md`. That is bookkeeping about what the checks found, not an approval:
the gate record stays empty until you write it.
