# Milestone M1 — acceptance report

**Build:** `northwind-sales` · **Milestone:** M1 — Enterprise and Renewal data model
**Written by:** `milestone-verifier` (this document is written, not rendered — `standards/build-orchestration.md` § 2)
**Run:** 2026-09-18 · **Scale:** `project` (from `plan.json.scale`) · **Build mode:** `design-only`
**This is M1's first verification.** `human_gates[milestone:M1]` is `pending` and has never been approved; `milestones[M1].status` is `building`. This is not a § 8 re-verification, so the report replaces nothing and appends no dated section.

---

## Verdict: ready-with-findings

Every cross-step check passed and no declared acceptance test failed. Seven findings and eight open items are carried below for the human to weigh. **Approving the gate accepts them.**

| Step 9 condition for `not-ready` | Present in M1? |
|---|---|
| An unresolved reference | No — 0 of 28 references unresolved |
| A deployment-order contradiction | No |
| A failing acceptance test | No — both runnable declared tests exit as expected |
| A blocked step | No — both steps are `documented` |

None of the four `not-ready` triggers fired, so the verdict is not `not-ready`.

**Why this is not `ready-for-gate`.** All four literal `ready-for-gate` conditions are also satisfied, and reporting it that way would be defensible against the wording and misleading in substance. Three things are true of this milestone that a reader of the word "ready" would not expect:

1. The single most consequential artefact in M1 — `standardValueSets/OpportunityStage.standardValueSet-meta.xml` — is **a fragment, not a deployable file**. Deployed as it stands it deactivates every OpportunityStage value it does not name, including every stage the SMB team's pipeline runs on. That is `O-M1S01-01`, assumption **A24** at risk `high`, and it is the requirement this milestone was told not to break (`requirement.md` item 6).
2. A requirement this milestone is in scope for — **REQ-010**, the Opportunity Products related list — **has no artefact and no test**, and the RTM linter reports it as an ERROR.
3. Which stage a new Enterprise or Renewal Opportunity opens on is **UNVERIFIED** (`O-M1S01-04`).

None of the three is a failed check. All three are decisions a human has to make at the gate, which is what `ready-with-findings` means.

---

## 1. Blocked steps

**None.** Both steps in M1 are `documented`.

| Step | Status | `human_gate` |
|---|---|---|
| M1-S01 | `documented` | false |
| M1-S02 | `documented` | false |

Predecessor gates, per § 3's approval preconditions for `gate milestone:M1 approve`:

| Gate | Status | Notes |
|---|---|---|
| `plan` | **approved** | 2026-09-15T19:14:01Z |
| `milestone:M0` | n/a | M1 is the first milestone; there is no predecessor to require |
| `milestone:M1` | **pending** | the gate this report is evidence for |

---

## 2. The milestone and its artefacts

**Goal (from `plan.json`):** two record types exist with their own Sales Processes and stage sets; the eight new stage values carry the signed-off probabilities and forecast buckets; `Discount__c` and `Approval_Status__c` exist on Opportunity; each record type has a layout carrying both — and the SMB team's record type, stages, list views and report are untouched.

### M1-S01 — `object-model`, owner `metadata-builder`

| Artefact | Type |
|---|---|
| `artefacts/M1-S01/standardValueSets/OpportunityStage.standardValueSet-meta.xml` | StandardValueSet |
| `artefacts/M1-S01/objects/Opportunity/businessProcesses/Enterprise_Sales_Process.businessProcess-meta.xml` | BusinessProcess |
| `artefacts/M1-S01/objects/Opportunity/businessProcesses/Renewal_Sales_Process.businessProcess-meta.xml` | BusinessProcess |
| `artefacts/M1-S01/objects/Opportunity/recordTypes/Enterprise.recordType-meta.xml` | RecordType |
| `artefacts/M1-S01/objects/Opportunity/recordTypes/Renewal.recordType-meta.xml` | RecordType |
| `artefacts/M1-S01/objects/Opportunity/fields/Discount__c.field-meta.xml` | CustomField |
| `artefacts/M1-S01/objects/Opportunity/fields/Approval_Status__c.field-meta.xml` | CustomField |
| `artefacts/M1-S01/package.xml` | manifest (not a component) |
| `artefacts/M1-S01/deploy-order.md` | note (not a component) |

### M1-S02 — `ui`, owner `metadata-builder`, `depends_on: [M1-S01]`

| Artefact | Type |
|---|---|
| `artefacts/M1-S02/layouts/Opportunity-Opportunity Enterprise Layout.layout-meta.xml` | Layout |
| `artefacts/M1-S02/layouts/Opportunity-Opportunity Renewal Layout.layout-meta.xml` | Layout |
| `artefacts/M1-S02/package.xml` | manifest (not a component) |
| `artefacts/M1-S02/deploy-order.md` | note (not a component) |

**Artefact freshness.** Every `artefact_hashes` digest recorded in `tests/M1-S01/results.json` and `tests/M1-S02/results.json` was re-computed against the files on disk during this run: **13 of 13 match**. No artefact has moved since the tester last read it, so the recorded test verdicts describe the files this report verifies.

---

## 3. Reference resolution

Computed this run by parsing every `*.xml` under `artefacts/M1-*/` and resolving each reference against the M1 symbol inventory. **M1 is the first milestone, so there is no earlier-milestone inventory** — every reference either resolves inside M1 or does not resolve at all.

### Symbol inventory built from M1

| Class | Members |
|---|---|
| BusinessProcess | `Enterprise_Sales_Process`, `Renewal_Sales_Process` |
| RecordType | `Opportunity.Enterprise`, `Opportunity.Renewal` |
| CustomField | `Opportunity.Discount__c`, `Opportunity.Approval_Status__c` |
| Layout | `Opportunity-Opportunity Enterprise Layout`, `Opportunity-Opportunity Renewal Layout` |
| Picklist values — `OpportunityStage` | Qualify, Discover, Propose, Negotiate, Renewal Review, Renewal Proposed, Closed Won, Closed Lost |
| Picklist values — `Opportunity.Approval_Status__c` | Pending, Approved, Rejected |
| Object `fullName`s | **none** — M1 ships no `CustomObject` file; `Opportunity` is a standard object this build never defines |
| Queues, groups, permission sets, business hours, milestone types, entitlement processes, Flow API names | **none in M1** |

### Which reference classes were checked, and what each found

This is the boundary of the check. Five of the six classes in the verifier's own table have **zero instances in M1** — they are empty, not silently passed.

| Reference class | Instances in M1 | Result |
|---|---|---|
| Validation rule field references | 0 | Not present — validation rules are M2-S03 / M2-S04 |
| Assignment rule criteria | 0 | Not present |
| Permission set grants (`fieldPermissions` / `objectPermissions`) | 0 | Not present — access is M2-S01 / M2-S02 |
| Flow field references | 0 | Not present |
| Entitlement process milestones | 0 | Not present |
| **Layout and path assignments** | **16** | All classified; see below. No `PathAssistant` in M1 (M2-S05) |
| **RecordType → BusinessProcess** *(additional class, not in the verifier's table but present in this milestone)* | **2** | Both resolved in M1-S01 |
| **BusinessProcess → picklist value** *(additional class)* | **10** | All ten resolved against M1-S01's `OpportunityStage` |

**Totals: 28 references, 0 unresolved, 0 unclassifiable.**

### The 28 references

| Class | From | Symbol wanted | Outcome |
|---|---|---|---|
| RecordType → BusinessProcess | `Enterprise.recordType-meta.xml` | `Enterprise_Sales_Process` | resolved in M1 (M1-S01) |
| RecordType → BusinessProcess | `Renewal.recordType-meta.xml` | `Renewal_Sales_Process` | resolved in M1 (M1-S01) |
| BusinessProcess → picklist value | `Enterprise_Sales_Process` | Qualify, Discover, Propose, Negotiate, Closed Won, Closed Lost | all 6 resolved in M1 (M1-S01 `OpportunityStage`) |
| BusinessProcess → picklist value | `Renewal_Sales_Process` | Renewal Review, Renewal Proposed, Closed Won, Closed Lost | all 4 resolved in M1 (M1-S01 `OpportunityStage`) |
| Layout → field (custom) | both layouts | `Discount__c`, `Approval_Status__c` | resolved in M1 (M1-S01), 4 references |
| Layout → field (standard) | both layouts | `Name`, `AccountId`, `StageName`, `CloseDate`, `Amount`, `Probability` | **fourth outcome** — see below, 12 references |

**A fourth outcome the verifier's trichotomy does not name.** The playbook classes every reference as *resolved in this milestone*, *resolved in an earlier milestone*, or *unresolved*. Twelve of M1's references are none of the three: the six standard Opportunity fields on each layout are defined by the platform, not by any step of this build, so no symbol inventory could ever hold them. They are **not** reported as unclassifiable — each is identified exactly — and they are **not** counted as resolved-in-milestone, because they are not. They resolved against the org: `reports/MOCK-DEPLOY-M1.md` run 4 (`checkOnly`, 2026-09-18T13:57Z) validated both `Layout` components against `sfskills-dev`, which is the only evidence in this build that these six names are correct. That evidence is stronger than the inventory check, and it is an org fact, not a design-time one.

### The deploy-time error each class would have produced

Had any reference failed, per `skills/devops/deployment-error-diagnosis`:

| Failure that did not occur | The error it would have produced |
|---|---|
| A record type naming a business process not in the package | `INVALID_CROSS_REFERENCE_KEY` on the record type — traced to missing metadata in the package, not to the record type itself |
| A business process listing a stage absent from the value set | `Component error: '<Stage>' is not a valid value for type 'OpportunityStage'` — the picklist-value-missing shape |
| A layout item naming a field the org does not hold | `INVALID_CROSS_REFERENCE_KEY` on the `Layout`, resolved by adding the field to the package |

**The bare-vs-object-qualified name split is correct in both directions.** `<businessProcess>` inside each record type carries the bare name (`Enterprise_Sales_Process`); the `package.xml` member is object-qualified (`Opportunity.Enterprise_Sales_Process`). A mismatch between those two spellings is the most common `INVALID_CROSS_REFERENCE_KEY` in a package of this shape. Both forms were checked and both are right.

---

## 4. Deployment order

**Verdict: no contradiction, and no dependency runs backwards.**

The canonical sequence is objects → fields → picklists → record types → layouts → permission sets → sharing → automation → routing → SLA. Each artefact's recorded position was read from its workbook row and compared against the artefact's own type.

| Artefact | Type | Recorded position | Sequence position for that type | Agrees? |
|---|---|---|---|---|
| `Opportunity.Discount__c` | CustomField | 2 of 10 (fields) | 2 | yes |
| `Opportunity.Approval_Status__c` | CustomField | 2 of 10 (fields) | 2 | yes |
| `OpportunityStage` | StandardValueSet | 3 of 10 (picklists) | 3 | yes |
| `Opportunity.Enterprise_Sales_Process` | BusinessProcess | 4 of 10 (with record types) | — see note | yes, as documented |
| `Opportunity.Renewal_Sales_Process` | BusinessProcess | 4 of 10 (with record types) | — see note | yes, as documented |
| `Opportunity.Enterprise` | RecordType | 4 of 10 (record types) | 4 | yes |
| `Opportunity.Renewal` | RecordType | 4 of 10 (record types) | 4 | yes |
| `Opportunity-Opportunity Enterprise Layout` | Layout | 5 of 10 (layouts) | 5 | yes |
| `Opportunity-Opportunity Renewal Layout` | Layout | 5 of 10 (layouts) | 5 | yes |

**Note on BusinessProcess.** The ten-position sequence has no slot of its own for `BusinessProcess`. `workbook/01-objects-and-fields.md` records both processes at position 4 *with* the record types and states the reason: an Opportunity record type is rejected without its process. That is a documented judgement about a type the sequence does not name, not a contradiction of it. Within position 4, `artefacts/M1-S01/deploy-order.md` § 1 orders process before record type, which is the correct direction.

**Dependencies checked for backward flow:**

- Business processes (4) depend on the value set (3) — forward. A stage must exist globally before a process can list it.
- Record types (4) depend on their business processes (4, ordered process-first within the slot) — forward.
- Layouts (5) depend on the two custom fields (2) — forward.
- **No permission set grants a field defined later in the order** — M1 ships no `PermissionSet` at all. The ordering failure `skills/devops/permission-set-deployment-ordering` exists to catch cannot occur in this milestone. It becomes live at M2-S02, which is where `Profile.layoutAssignments` and `recordTypeVisibilities` ship; both M1 steps' deploy-order notes already carry that forward dependency.
- **No automation arrives before the routing it triggers** — M1 ships no `Flow`, no `FlowDefinition` and no Apex. The activation-ordering and paused-interview concerns in `skills/devops/flow-deployment-activation-ordering` have no instance here. Recorded as empty rather than as passed.

**One ordering fact this milestone's own artefacts state and no position number captures:** both layouts and both record types deploy in M1, and **neither is reachable by any user until M2-S02 lands**. `layoutAssignments` and the default record type live only on `Profile`; a permission set can grant record-type visibility but not the layout assignment. That is `O-M1S01-03`, carried below.

---

## 5. Merged manifest

**Path:** `reports/MILESTONE-M1-package.xml` (written by this run)

| Type | Members |
|---|---|
| BusinessProcess | `Opportunity.Enterprise_Sales_Process`, `Opportunity.Renewal_Sales_Process` |
| CustomField | `Opportunity.Approval_Status__c`, `Opportunity.Discount__c` |
| Layout | `Opportunity-Opportunity Enterprise Layout`, `Opportunity-Opportunity Renewal Layout` |
| RecordType | `Opportunity.Enterprise`, `Opportunity.Renewal` |
| StandardValueSet | `OpportunityStage` |

**5 types, 9 members.** Members are sorted within each `<types>` block.

| Merge check | Result |
|---|---|
| `<version>` conflict between step manifests | **None.** M1-S01 and M1-S02 both declare `62.0`; one `<version>62.0</version>` is kept |
| Member declared in two steps | **None** |
| Metadata file under `artefacts/M1-*/` reaching no `<types>` block | **None** — all 9 component files are covered |
| Non-component files excluded by kind | 4: `artefacts/M1-S01/package.xml`, `artefacts/M1-S02/package.xml`, both `deploy-order.md` notes. Excluded by kind, not dropped |

**Cross-check against the org.** The merged manifest this run produced is **byte-for-byte identical** to `reports/mock-deploy/2026-09-18T13-57-17Z/package.xml` — the manifest `scripts/mock_deploy.py` assembled and the org validated on run 4. Two independent merges of the same step manifests agreed exactly, and the org accepted the result.

**Wildcards:** none. Every member is explicit, which is what `skills/devops/metadata-api-retrieve-deploy` requires for a CI-grade manifest.

---

## 6. Acceptance-test results

M1 declares four acceptance tests. Both runnable ones were run verbatim from the build directory; the two `manual` ones are collected into § 7.

### Declared test 1 — `checker` (cross-step)

```
python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts
```

**Exit code 0** — expected `exit 0`. **PASS.**

`Scanned 6 metadata file(s): 2 record type(s), 2 layout(s); 2 finding(s) detected.`

| Severity | Finding |
|---|---|
| REVIEW | the two layouts are identical after normalisation — merge candidates |
| INFO | no Profile/PermissionSet in scope — assignment coverage not checked |

Neither fails the run: the checker is lenient without `--strict`, and the plan's test declares it without that flag deliberately. Both findings are known and carried as open items (`O-M1S02-03` and the M2-S02 dependency behind `O-M1S01-03`). This is the reading only build scope can produce — at `--manifest-dir artefacts/M1-S02` the same command sees `0 record type(s), 2 layout(s)` and is blind to half the pair.

### Declared test 2 — `manifest` (milestone consistency)

> Every StandardValueSet, BusinessProcess, RecordType, CustomField and Layout member produced in M1 appears in a milestone package.xml with a file behind it.

**Result: `consistent`. PASS.** Verified two ways against `reports/MILESTONE-M1-package.xml`:

- **member → file:** all 9 members have a file behind them.
- **file → member:** all 9 component files reach a `<types>` block; 0 unreached.

### Declared tests 3 and 4 — `manual`

Collected into § 7, not run. No declared checker was missing; no declared checker failed.

### Undeclared checkers run as extra evidence — **advisory, and two of the three assert nothing**

`build_plan.py validate` reports three § 5 checker-coverage WARNs against M1: a cited skill ships a checker that no test on the step or on the milestone runs. They cannot be declared now — both steps have already run, and `amend-step` refuses a step past `pending`/`blocked`. They were run anyway. **Because they are undeclared, none of these exit codes is a milestone acceptance-test result, and none of them changes the verdict.**

| Skill (WARN on) | Command run | Exit | What the exit code actually asserts |
|---|---|---|---|
| `admin/sales-process-mapping` (M1-S01) | `check_sales_process_mapping.py --manifest-dir artefacts` | **0** | **Nothing.** See below |
| `admin/opportunity-management` (M1-S02) | `check_opportunity_management.py --manifest-dir artefacts` | **0** | **Nothing** — the checker says so itself: `INFO: [artefacts] No Opportunity stage value set, business process, record type or pathAssistant found. Nothing in this tree is in scope for this checker.` It reads fixed paths directly under the manifest dir with `glob`, not `rglob`, so at tree root it sees an empty scope. The declared M1-S01 step test already runs this checker at `--manifest-dir artefacts/M1-S01`, which is the scope at which it asserts (`No issues found.`, exit 0) |
| `admin/products-and-pricebooks` (M1-S02) | `check_products_and_pricebooks.py --manifest-dir artefacts` | **0** | **Nothing.** It scans `classes/`, `triggers/`, `settings/`, `flows/`, `profiles/`, `objects/Product2`, `objects/PricebookEntry` — M1 contains none of these. `No issues found.` over an empty scope. Structural vacuity, not a wrong scope choice: no invocation of this checker against M1's artefacts could assert anything |

**The `sales-process-mapping` result needs its own paragraph, because a reader would otherwise take it for evidence.** At `--manifest-dir artefacts` the checker exits 0 and prints `No issues found.` It looks like a clean pass over the milestone. It is not. Its stage-metadata check reads one fixed path, `<manifest-dir>/standardValueSets/OpportunityStage.standardValueSet-meta.xml`, and the file in this build is one level deeper, at `artefacts/M1-S01/standardValueSets/…`. Not finding it is advisory in that checker, so it returns early and exits 0 having read nothing.

This was confirmed by negative control rather than by reading the source alone. A copy of the artefact tree was made **in the session scratchpad — nothing in the build directory was touched** — with two deliberate defects injected into the value set (`Propose` given `<forecastCategory>Commit</forecastCategory>`, an illegal enum member; `Closed Won` probability changed to 42):

| Invocation over the **deliberately broken** tree | Exit | Output |
|---|---|---|
| `--manifest-dir <broken>/artefacts` | **0** | `No issues found.` — the defects are invisible at this scope |
| `--manifest-dir <broken>/artefacts/M1-S01` | **1** | `ERROR: Stage 'Propose': <forecastCategory>Commit</forecastCategory> is not a member of the ForecastCategories enumeration…` |

And over the real, clean tree at step scope: `--manifest-dir artefacts/M1-S01` → exit 0, `No issues found.` — a real pass.

**So the honest reading is:** `admin/sales-process-mapping`'s checker does carry a real assertion about M1's value set, but only at `--manifest-dir artefacts/M1-S01`, and that invocation is the one that should be declared whenever M1-S01 is next rebuilt. The build-scope run in the table above is not evidence of anything and must not be quoted as though it were.

---

## 7. Manual checklist for the gate

Six lines. Four are the steps' own deferred `manual` tests, quoted verbatim from `tests/<step>/results.json` → `skipped_manual`; two are the milestone's own declared `manual` tests. Each names the step it came from, what the human does, and what counts as a tick.

### From M1-S01

**☐ 1. (BLOCKING before any real deploy) The stage value set carries the retrieve-and-merge instruction.**
Read `artefacts/M1-S01/deploy-order.md`. **Ticks when:** its first instruction is to run `sf project retrieve start --metadata StandardValueSet:OpportunityStage` against the target org and merge the retrieved active values into the shipped file, and it states in the same paragraph that a partial file deactivates every value it omits — including the SMB team's stages.
*Verifier's note: § 0 of that file does say exactly this. The tick is the human confirming they have read it and own the consequence, not a check of whether the text exists.*

**☐ 2. The eight stage values carry the signed-off probabilities and forecast buckets.**
Read the eight `standardValue` blocks. **Ticks when:** Qualify/Discover/Propose/Negotiate carry 10/25/50/75 and Pipeline/Pipeline/BestCase/Forecast; Renewal Review and Renewal Proposed carry 60/85 and Pipeline/Forecast; Closed Won carries 100 with `won` and `closed` true; Closed Lost carries 0 with `forecastCategory` Omitted — **and the word "Commit" appears nowhere in the file.**
*Verifier's note: "Commit" is the UI label for the metadata token `Forecast`; the enum is exactly Omitted, Pipeline, BestCase, Forecast, Closed. Expect SOQL and the UI to show Commit on Negotiate and Renewal Proposed — that is correct, not a defect.*

### From M1-S02

**☐ 3. (BLOCKING before any real deploy) The related-list retrieve instruction is present.**
Read `artefacts/M1-S02/deploy-order.md`. **Ticks when:** it names the exact `sf project retrieve start --metadata "Layout:Opportunity-Opportunity Layout"` command, says to copy the Opportunity Products `relatedLists` block verbatim from what the retrieve emits, and states that hand-authoring the related-list name is what the instruction exists to prevent.

**☐ 4. The layout field set and the discovery procedure are both recorded.**
Read both layout files. **Ticks when:** each carries `Name`, `AccountId`, `StageName`, `CloseDate` and `Amount`, plus `Discount__c` editable and `Approval_Status__c` read-only, and `deploy-order.md` records that the platform's layout-required set for Opportunity is unverified and is discovered by iterating `scripts/mock_deploy.py --dry-run`, one field per run.
> **⚠ This line's wording is behind its artefact, and the gap is not cosmetic.** The observable it names is still present and the test is still tickable. But since it was written, the org has named three required fields (`Probability`, `Name`, `StageName`) across `reports/MOCK-DEPLOY-M1.md` runs 1–3, a fourth (`CloseDate`) was shipped ahead of confirmation, and run 4 validated the pair 9/9. A human ticking only this line would not learn any of that. It also carries an older error: `mock_deploy.py` needs no `--dry-run` flag — the dry run is the script's only behaviour. Both are prose; the writer is `build_plan.py amend-step --prose-only` and it is the planner's call, not this agent's. Carried as `O-M1S02-04` and `O-M1S02-02`.

### The milestone's own manual tests

**☐ 5. (BLOCKING — assumption A24, risk `high`) A named owner confirms the value set is a union, not a fragment.**
**Ticks when:** a named owner confirms the `OpportunityStage` file about to be deployed is the union of the org's currently active stage values and the eight new ones — because a partial file deactivates every value it omits, which is the single way this milestone could break the SMB pipeline it is designed to leave alone.
*Verifier's note: this and line 1 are the same fact at two altitudes — line 1 checks the instruction is written down, line 5 requires a person to own having done it. Neither can be ticked by any agent in this loop, and no `checkOnly` validation can substitute:* `reports/MOCK-DEPLOY-M1.md` *run 1 records that the partial value set validated cleanly, because a check-only deploy never deactivates anything. A green dry run is not evidence here.*

**☐ 6. The milestone is additive by construction.**
**Ticks when:** the whole M1 artefact tree is listed and no file anywhere names the SMB record type, either SMB list view, or the SMB pipeline report.
*Verifier's note: this run's file walk over* `artefacts/M1-S01/` *and* `artefacts/M1-S02/` *found 13 files and no such reference — the tree contains two record types (Enterprise, Renewal), two business processes, two custom fields, one value set and two layouts, and nothing else. The human's tick is the independent confirmation; the observation above is not a substitute for it.*

**Every manual line above states an observable outcome.** None is a request to certify something undefined.

---

## 8. Optional validate-only command — for the human, not for this agent

**This agent runs no `sf` command and no deploy of any kind. The line below is printed, not executed.**

The org-facing evidence this milestone rests on **already exists** and does not need to be regenerated:

| Run | When | Mode | Result |
|---|---|---|---|
| 1 | 2026-09-18T13:34Z | manifest, M1 | Failed — 4 errors (N3-F-01, N3-F-02) |
| 2 | 2026-09-18T13:43Z | manifest, M1 | Failed — 2 errors (N3-F-03) |
| 3 | 2026-09-18T13:52Z | manifest, M1 | Failed — 2 errors (N3-F-04) |
| **4** | **2026-09-18T13:57Z** | **manifest, M1** | **Succeeded — 9/9 components, 0 errors** |

Run 4's evidence: `reports/mock-deploy/2026-09-18T13-57-17Z/summary.md` and `result.json` — `status: Succeeded`, `checkOnly: true`, `numberComponentsTotal: 9`, `numberComponentErrors: 0`, `rollbackOnError: true`, against org alias `sfskills-dev` at API 62.0. Test level `NoTestRun`, `runTestsEnabled: false`, 0 tests run, coverage n/a — **correct for this milestone, which contains no Apex**, and stated here so nobody reads run 4 as evidence that any test executed.

**The target here is a sandbox, so the validate-only form is a dry run of a deploy:**

```bash
# OPTIONAL — run by a human, never by this agent. Sandbox target.
sf project deploy start \
  --manifest .sfskills/builds/northwind-sales/reports/MILESTONE-M1-package.xml \
  --dry-run --target-org <alias>
```

`--dry-run` compiles and validates without saving. Use `sf project deploy validate` **only** against a production org: Salesforce documents it as production-only, it requires Apex tests, and it returns a job id for a later `sf project deploy quick`. Offering the production form for a sandbox sends the human into an error that has nothing to do with this build.

**Two things a green dry run here would still not prove.** Both are § 7 gate lines, and neither is closable by validation:

1. The `OpportunityStage` value set is a fragment. `checkOnly` never deactivates anything, so it validates clean and the SMB pipeline breaks only on the real deploy (`O-M1S01-01`).
2. Requirement item 2's related list is absent from both layouts. Nothing is missing that a deploy could complain about (`O-M1S02-01`).

---

## 9. Requirements this milestone closes — and the one it does not

From `traceability.md`, the build-layer RTM. The linter documented in that file was re-run this session, from the build directory:

```
python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py \
  --file traceability.md --manifest-dir artefacts --repo-root ../../..
```

**Result: 10 rows, build schema, 1 coverage gap, 0 orphans, 1 error, 14 warnings** — reproducing exactly what `traceability.md` records. `check_rtm.py` is **not** a declared acceptance test on M1, so this run changes no test verdict; it is read as the traceability evidence § 9 requires.

| req_id | Requirement | Status | Closed by M1? |
|---|---|---|---|
| REQ-001 | Eight stage values with signed-off probability and forecast category, without deactivating the SMB pipeline | In UAT | **Content yes; org safety no** — the retrieve-and-merge (`O-M1S01-01`) decides it |
| REQ-002 | Enterprise six-stage sequence | In UAT | yes |
| REQ-003 | Renewal four-stage sequence | In UAT | yes |
| REQ-004 | Enterprise record type | In UAT | **Artefact yes; selectability no** — `Profile` work is M2-S02 (`O-M1S01-03`) |
| REQ-005 | Renewal record type | In UAT | same as REQ-004 |
| REQ-006 | `Discount__c` header field | In UAT | yes |
| REQ-007 | `Approval_Status__c` | In UAT | yes |
| REQ-008 | Enterprise page layout | In UAT | **Artefact yes; assignment no** — M2-S02 (`O-M1S01-03`) |
| REQ-009 | Renewal page layout | In UAT | same as REQ-008 |
| **REQ-010** | **Reps add product lines from the Standard Price Book via the Opportunity Products related list** | **In Build** | **NO — no artefact, no test** |

### REQ-010 is the milestone's one genuine coverage gap

```
ERROR: row 11: coverage gap: REQ-010 has no test id while status is 'In Build'
```

The error is a true statement, not a formatting artefact. Neither layout ships a `relatedLists` block, **and this verifier confirmed independently that no checker cited anywhere in M1 reads for one**: a grep for `relatedList` across `check_record_type_layouts.py`, `check_opportunity_management.py` and `check_products_and_pricebooks.py` returns nothing. So the gap is a content gap that no test in M1's declared set was ever positioned to catch — which is exactly why it needs a human at the gate.

`requirement.md` item 2 ("reps add products from our price book to every Enterprise opportunity") **is not satisfied by milestone M1.** It closes one of two ways, and re-labelling the status is neither:

1. The `O-M1S02-01` retrieve produces a `relatedLists` block in both layouts, **plus** a test that reads for one; or
2. A human at this gate re-homes requirement item 2 onto a later step.

The 14 warnings are pre-existing conventions of this file — multi-valued `source` and `decision_ref` cells, and REQ-010's deliberately-absent artefact. They are not new and not caused by this milestone.

---

## 10. Open items carried to the gate

**Eight** open items stand in `decisions.md` against M1's two steps. None was resolved by this verification and none is resolvable by any agent in this loop. **Approving `milestone:M1` accepts every one of them.** The six the human most needs to weigh are first; the last two are real and lower-stakes, listed so the count in this report matches the count in `decisions.md`.

| Id | Open item | Risk | Why this build cannot close it |
|---|---|---|---|
| **O-M1S01-01** | **BLOCKING.** The shipped `OpportunityStage` value set is a fragment; it must be retrieved from the org and merged before any real deploy, or every omitted stage — including the SMB team's — is deactivated | **A24, high** | `build_mode: design-only`; no org connection to run the retrieve. A `checkOnly` run validates the fragment cleanly, so no dry run can surface this |
| **O-M1S01-04** | **UNVERIFIED (2026-09-18).** After the N3-F-01 repair neither business process carries a default, and no cited skill documents a per-process or per-record-type default-stage mechanism for Opportunity. **Which stage a new Enterprise or Renewal Opportunity opens on is unresolved** | medium | Closed only by the post-deploy SOQL in `artefacts/M1-S01/deploy-order.md` § 4, cross-checked against each process's stage subset — never by what the UI shows as selected |
| **O-M1S02-01 / REQ-010** | **BLOCKING.** Opportunity Products related list absent from both layouts; requirement item 2 unsatisfied. `check_rtm.py` reports it as an ERROR; assumption **A26** unmet | medium | The related-list API name is a retrieval alias present in no skill in this library; it must be copied verbatim from a live-org retrieve, not typed |
| **O-M1S02-03** | The Enterprise and Renewal layouts are **byte-for-byte identical** (confirmed this run: both files hash to `0ee76271…`). Keep two files, or merge to one shared layout? | low | A design question nobody answered. Recorded as a question because inventing a Renewal-specific field or collapsing the pair would each assert an answer nobody gave. **This is a decision for the human at this gate** |
| **O-M1S02-04** | **UNVERIFIED (2026-09-18).** Whether `CloseDate` is platform-required on an Opportunity layout | low | See the paragraph below |
| **O-M1S02-02** | The A25 manual-test wording still names a `--dry-run` flag on `mock_deploy.py` that does not exist, and still describes the required-field set as unverified | low | Prose only; `amend-step --prose-only`, the planner's call. One amendment closes this and O-M1S02-04's second half together |
| **O-M1S01-03** | Both record types and both layouts deploy in M1 and **none of the four is reachable by any user** until M2-S02 lands: `layoutAssignments` and the default record type live only on `Profile`, and a permission set can grant record-type visibility but not the layout assignment | low | M2-S02 is a later, human-gated step. Not a defect — but the milestone goal reads as delivered while the configuration is inert, which is worth knowing before signing |
| **O-M1S01-02** | Clarification **Q39** is unanswered and assumption **A4** relies on `OpportunitySettings.enableOpportunityFieldHistoryTracking` defaulting to `true` — no `OpportunitySettings` file ships anywhere in this build | low | It is an org setting, not a deployable component, so no metadata step in this build can close it. It matters more than a normal open question because **Opportunity field history cannot be backfilled**: if the default is off, or is turned off before go-live, no measurement of stage movement is possible after the fact |

### On `CloseDate` — what run 4 proves and what it does not

`CloseDate` carries `behavior=Required` on both layouts on the strength of an **inference**: Opportunity's three `nillable=false` standard fields are `Name`, `StageName` and `CloseDate`, and the org had just named the first two. It was set in the same repair pass as `StageName`, one round ahead of any deploy message naming it.

Run 4 then validated the pair 9/9. That proves the shipped configuration **deploys**. It cannot distinguish *"the platform requires `CloseDate` on the layout"* from *"`Required` is merely accepted there"* — because no run ever tested `CloseDate` at `Edit` after the other three were fixed. The only run that could have named it was run 3, and the one-field-per-run behaviour means its silence proves nothing either.

**This report therefore does not state as an org fact that `CloseDate` is platform-required on an Opportunity layout.** Three fields are org-confirmed: `Probability`, `Name`, `StageName`. The fourth is `UNVERIFIED (2026-09-18)`.

`reports/MOCK-DEPLOY-M1.md` run 4 says the marker "resolves to confirmed at the next doc-keeper pass", and `MOCK-DEPLOY-M1.md`'s closing line lists four org facts including `CloseDate`. **On the evidence above, that reading goes one step past what run 4 carries**, and the `UNVERIFIED` marker standing in `artefacts/M1-S02/deploy-order.md` § 6 is correct as it stands. The close condition is cheap and decisive and was **not** run here: one further `scripts/mock_deploy.py` round against a copy of either layout with `CloseDate` back at `behavior=Edit` and everything else unchanged. This matters beyond the build — the fact is on its way into the library, and a skill rule asserting `CloseDate` is layout-required would claim more than this build's evidence supports. A rule saying *the four-item set validates* is exactly what was observed.

---

## 11. Checker-coverage WARNs standing on M1

`build_plan.py validate` exits 0 with 19 warnings across the plan; three are on M1:

```
WARN step M1-S01 skills: admin/sales-process-mapping ships check_sales_process_mapping.py
  but no checker test on the step or on milestone M1 runs it
WARN step M1-S02 skills: admin/opportunity-management ships check_opportunity_management.py
  but no checker test on the step or on milestone M1 runs it
WARN step M1-S02 skills: admin/products-and-pricebooks ships check_products_and_pricebooks.py
  but no checker test on the step or on milestone M1 runs it
```

They cannot be closed now: `amend-step` refuses a step whose status is past `pending`/`blocked`, and both M1 steps are `documented`. § 6 above reports what each checker actually returns and — importantly — that two of the three assert nothing at all over M1's artefacts. The remedy for whichever of them is worth declaring is `amend-step --add-checker <skill-id>` at the next `documented → running` rebuild of the step, with `admin/sales-process-mapping` declared at `--manifest-dir artefacts/M1-S01` rather than at tree root, because that is the only scope at which its exit code carries an assertion.

---

## 12. The gate — for a human, unrun

This agent does not approve, reject or record a gate. The command below is printed for a named human.

**Read the one-page brief first:**

```bash
python3 scripts/build_plan.py brief .sfskills/builds/northwind-sales/plan.json M1
```

It gathers, from one page, what is otherwise spread across six documents: the steps, the validate WARNs, the open items from `decisions.md`, the deferred manual tests, the latest mock-deploy headline and this report's verdict.

**Then, if approving:**

```bash
python3 scripts/build_plan.py gate .sfskills/builds/northwind-sales/plan.json \
  milestone:M1 approve --by "<name>"
```

§ 3 will check, before writing: the `plan` gate is approved (**it is**), `milestone:M0` is approved (**n/a — M1 is the first milestone**), and every step in M1 is `documented` or `blocked` with a recorded reason (**both are `documented`; none is blocked**). All preconditions are satisfied, so the command will not be refused.

**Approving accepts the eight open items in § 10** — including two marked BLOCKING before any real deploy (`O-M1S01-01`, `O-M1S02-01`), two `UNVERIFIED` markers (`O-M1S01-04`, `O-M1S02-04`), and one unanswered design question (`O-M1S02-03`, the identical layouts). It also accepts that **requirement item 2 is not delivered by this milestone**.

To reject instead, substitute `reject` and give `--notes` saying what must change.

---

## Recorded

```bash
python3 scripts/build_plan.py set-milestone .sfskills/builds/northwind-sales/plan.json M1 \
  --status verified --report-path reports/MILESTONE-M1-REPORT.md
```

`--status verified` is the correct record for `ready-with-findings`. It is a statement about what the checks found, not an approval: `milestones[].status` and `report_path` are plan bookkeeping, and `human_gates[milestone:M1]` stays `pending` until a human writes it.

---

*Per-finding detail, the full envelope and the citations for this run: `envelopes/M1/<run_id>.md` and `.json`.*
