# M2 — Access, work pools and Case visibility · acceptance report **v2 (re-verification)**

| | |
|---|---|
| Build | `case-onboarding` (`plan.json` v5, status `building`, `build_mode: design-only`, no org on file) |
| Milestone | **M2** — "Access, work pools and Case visibility" |
| Steps | 5, all `documented`: `M2-S01`, `M2-S02`, `M2-S03`, `M2-S04`, `M2-S05` |
| Blocked steps | **none** |
| Verdict | **`ready-with-findings`** — every declared executable acceptance test now passes; the open findings are ones the human may accept |
| Confidence | **MEDIUM** |
| Written by | `agents/milestone-verifier/AGENT.md`, run `2026-09-12T02-54-59Z` |
| Supersedes | [`MILESTONE-M2-REPORT.md`](./MILESTONE-M2-REPORT.md) (run `2026-09-12T02-10-00Z`, verdict `not-ready`). **v1 is not overwritten and stays on disk as the record of what the checks found then.** |
| Merged manifest | [`reports/MILESTONE-M2-package.xml`](./MILESTONE-M2-package.xml) — 7 types, 19 members, `<version>62.0</version>`, no conflict. **Not regenerated: the freshly merged member set is byte-identical to the committed file** (§ 5) |
| Org-facing evidence | `reports/MOCK-DEPLOY-M2.md` **run 3** — 32 components, 0 errors, `checkOnly: true`, human-run |

> **Nothing in this run touched an org, and nothing was deployed.** No `sf` command was run. The G3
> gate is the human's; this report ends with the command and does not run it.

---

## 0. Why there is a v2, and what changed between the two runs

**One thing changed, and it is outside the build.** v1 returned `not-ready` on **F-16 alone**: the
milestone acceptance test `M2-T1` exited 1 against a declared `exit 0`, because
`skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py` ended
`return 1 if normalized else 0` — every severity, including a WARN, failed the run. The only finding
was a 244-character `<description>` on `Case_Intake_Integration`: under the 255-character platform
limit, over the 200-character headroom the skill had added five days after that step was built.

That checker was fixed in **commit `214da9abd`** (skill v1.2.1), which did three things:

| Change | Effect on this milestone |
|---|---|
| Blocking severities narrowed to `CRITICAL` / `ERROR` / `HIGH`; `WARN` / `INFO` print and exit 0 | `M2-T1` now exits **0**, and the JSON carries a new `"blocking": 0` field |
| `--strict` added, promoting every finding to a failure | gives a caller the old behaviour explicitly, rather than as the only behaviour |
| Check 2 — *migratable permissions still on a profile* — raised from `WARN` to **`HIGH`** | keeps the *second half of M2-T1's declared assertion blocking*. Without this raise, the narrowed exit policy would have made "no migratable permission left on a profile" a non-blocking advisory, and the test would have passed a profile carrying `objectPermissions`. **§ 6.4 control C proves it still fails.** |

**No artefact, no test declaration, no step status and no gate record changed between v1 and v2.** Every
one of M2's 24 XML files is byte-for-byte what v1 read. The re-verification therefore re-runs the
milestone's tests rather than re-judging the build, and this report's findings section is mostly a
status ledger rather than new analysis. Where it *is* new analysis, it is flagged — **F-22** and
**F-23** are new in this run, and neither existed to be found in v1.

One drift worth naming at the top, because it is the same shape as F-16: **the fix that closed F-16
invalidated a non-vacuity claim carried in three step test descriptions** (F-22). A skill's exit policy
moving under finished steps cuts both ways.

---

## 1. Precondition checks (Step 1)

| Check | Result |
|---|---|
| Every step in M2 is `documented` | **yes** — 5 of 5. No step is `pending`, `running`, `built`, `tested`, `failed` or `blocked`, so no refusal applies |
| Preceding milestone's gate | `human_gates[milestone:M1].status` = **`approved`** (2026-09-09T20:30:32Z, dry-run operator) |
| `plan` gate | **`approved`** (2026-09-05T19:35:19Z) |
| `clarifications` gate | **`approved`** (2026-09-05T15:50:00Z, 25 deferred) |
| Per-step `step:<id>` gates | all five **approved** — `M2-S01` … `M2-S05`; every M2 step carries `human_gate: true` |
| `milestone:M2` gate | **`pending`** — this run does not touch it |
| `plan.json` schema + semantics | `build_plan.py validate` → `OK … 5 milestone(s), 22 step(s), 3 warning(s)`. All three WARNs are on **M5** steps (non-standard checker argument forms); none is in M2 |
| Build directory carries the `skills` symlink | **yes** — `skills -> ../../../skills`, so every declared `skills/<domain>/<slug>/scripts/check_*.py` and `--manifest-dir artefacts` resolved exactly as written (`standards/build-orchestration.md` § 5) |

**Correction of record on M1's status.** v1 § 0 reported that `milestones[M1].status` read `verified`
rather than `accepted`, and called that the F-12 artefact. **It now reads `accepted`.** The `accepted`
value is the one the human's G3 approval leaves behind, the gate record has said `approved` throughout,
and `milestones[M1].reverifications[]` is empty — so nothing was re-recorded over it. Whatever produced
the transient `verified` reading, the guard at `scripts/build_plan.py:2182–2196` now prevents a
re-verification from moving an `accepted` milestone at all (**F-12**, closed). **M2's own status is
`rejected`, not `accepted`, so that guard does not apply to this run** and § 14's `set-milestone` writes
the status directly.

---

## 2. The milestone and its artefacts

Five `access`-type steps, all owned by `metadata-builder` (org-free, as `build_mode: design-only`
requires). **24 XML files, all parsing; 19 deployable members.** Re-confirmed this run.

### M2-S01 — Intake bypass Custom Permission and the integration permission set that carries it
`depends_on: []` · 0 amendments

- `customPermissions/Bypass_Case_Intake_Validation.customPermission-meta.xml`
- `permissionsets/Case_Intake_Integration.permissionset-meta.xml`
- `package.xml`, `deploy-order.md` *(declared in `outputs[]` at plan time — the only M2 step for which that is true without an amendment)*

**This is the step F-16 was about.** Its artefacts are unchanged; the checker that read them moved twice.

### M2-S02 — Permission sets and permission set groups for Tier 1, Tier 2 and Billing
`depends_on: [M1-S01]` · rebuilt once (F-15) · 0 amendments

- `permissionsets/` — `Case_Agent_Core`, `Case_Tier1`, `Case_Tier2`, `Case_Billing`
- `permissionsetgroups/` — `PSG_Tier1_Prod`, `PSG_Tier2_Prod`, `PSG_Billing_Prod`
- `package.xml` · `deploy-order.md` **produced but not declared** (O-M2S02-01, still open — § 9.3)

### M2-S03 — Minimal base profiles carrying only default app, default record type and layout assignment
`depends_on: [M1-S02, M2-S02]` · rebuilt once (F-15) · 1 amendment

- `profiles/` — `Acme Support Tier 1`, `Acme Support Tier 2`, `Acme Billing`
- `package.xml`, `deploy-order.md` *(declared by the 2026-09-12T00:38:44Z amendment)*

**This is the step that closes M1's F-01,** re-confirmed at build scope this run (§ 3.2).

### M2-S04 — Case queues and public groups for Tier 1 General, Tier 2 and Billing
`depends_on: [M2-S02]` · 1 amendment

- `queues/` — `Tier_1_General`, `Tier_2_Engineering`, `Billing`
- `groups/` — `Support_Tier_1`, `Support_Tier_2`, `Billing_Team`
- `queue-retirement-runbook.md`, `package.xml`, `deploy-order.md`

**This step deferred four manual tests, not three** — see § 8 and **F-23**.

### M2-S05 — Case org-wide default Private plus the criteria-based sharing rule that opens Support cases to Tier 2
`depends_on: [M1-S01, M2-S04]` · 1 amendment · decision tree `standards/decision-trees/sharing-selection.md`

- `sharingRules/Case.sharingRules-meta.xml` — one `sharingCriteriaRules` block, `Support_Cases_To_Tier_2`
- `case-visibility-model.md`, `package.xml`, `deploy-order.md`

---

## 3. Reference resolution (Steps 2 and 3)

**49 references over M2's 13 metadata files. 0 unresolved. 1 unclassifiable.** Rebuilt from scratch this
run; raw capture `tests/M2/cross-step-references.v2.stdout.txt`.

### 3.1 Symbol inventory (Step 2)

M1 is `accepted`, so its symbols count as defining. M3–M5 are `pending` and do not.

| Kind | Defined by M1 (earlier, accepted) | Defined by M2 (this milestone) |
|---|---|---|
| Object | `Case` (`M1-S01`) | — |
| Field | `Case.Severity__c`, `Account.Region__c`, `Account.Support_Tier__c` (`M1-S01`) | — |
| Record type | `Case.Support`, `Case.Billing` (`M1-S01`) | — |
| Business process | `Case.Support_Process`, `Case.Billing_Process` (`M1-S01`) | — |
| Compact layout | `Case.Case_Intake` (`M1-S01`) | — |
| Picklist value set | `StandardValueSet:CaseOrigin` (`M1-S01`) | — |
| Layout | `Case-Case Support Layout`, `Case-Case Billing Layout` (`M1-S02`) | — |
| Custom permission | — | `Bypass_Case_Intake_Validation` (`M2-S01`) |
| Permission set | — | `Case_Intake_Integration` (`M2-S01`); `Case_Agent_Core`, `Case_Tier1`, `Case_Tier2`, `Case_Billing` (`M2-S02`) |
| Permission set group | — | `PSG_Tier1_Prod`, `PSG_Tier2_Prod`, `PSG_Billing_Prod` (`M2-S02`) |
| Profile | — | `Acme Support Tier 1`, `Acme Support Tier 2`, `Acme Billing` (`M2-S03`) |
| Queue | — | `Tier_1_General`, `Tier_2_Engineering`, `Billing` (`M2-S04`) |
| Public group | — | `Support_Tier_1`, `Support_Tier_2`, `Billing_Team` (`M2-S04`) |
| Sharing rule | — | `Support_Cases_To_Tier_2` (`M2-S05`) |

Four standard objects are referenced and defined by no file in the build: `Account`, `Contact`,
`EmailMessage`, `Entitlement`. They pre-exist in every target org and are classified
**resolved-standard-object**, not unresolved. No role exists anywhere in this build, deliberately, per
`artefacts/M2-S05/case-visibility-model.md` § "Layers deliberately not used".

### 3.2 Which reference classes were resolved — and the boundary of the check

| Reference class | Read from | Resolves against | Count | Result |
|---|---|---|---|---|
| Permission-set field grants | `<field>` under `<fieldPermissions>` | field inventory | 5 | all resolved (`M1-S01`) |
| Permission-set object grants | `<object>` under `<objectPermissions>` | object inventory | 5 | 1 resolved (`M1-S01`) + 4 standard |
| Record-type visibility | `<recordType>` under `<recordTypeVisibilities>` | record-type inventory | 9 | all resolved (`M1-S01`) |
| Layout assignment — layout | `<layout>` under `<layoutAssignments>` | layout inventory | 9 | all resolved (`M1-S02`) |
| Layout assignment — record type | `<recordType>` under `<layoutAssignments>` | record-type inventory | 6 | all resolved (`M1-S01`) |
| Custom-permission grant | `<name>` under `<customPermissions>` | custom-permission inventory | 1 | resolved (`M2-S01`) |
| PSG membership | `<permissionSets>` | permission-set inventory | 6 | all resolved (`M2-S02`) |
| Queue membership — public group | `<queueMembers>/<publicGroups>/<publicGroup>` | group inventory | 3 | all resolved (`M2-S04`) |
| Queue supported object | `<queueSobject>/<sobjectType>` | object inventory | 3 | all resolved (`M1-S01`) |
| Sharing rule — `sharedTo` | `<sharedTo>/<group>` | group inventory | 1 | resolved (`M2-S04`) |
| **Sharing-rule criteria value** | `<criteriaItems>/<value>` on `RecordTypeId` | record-type inventory | 1 | **unclassifiable** — § 3.4 |
| **Total** | | | **49** | **33 earlier-milestone · 11 this milestone · 4 standard · 1 unclassifiable · 0 unresolved** |

**Correction of record: the total is 49, not 48.** v1 § 3 stated "48 references" while its own
class-by-class table summed to 49 — an arithmetic slip in the prose, not a missed reference. Every row
in v1's table matches this run's count exactly. Nothing was added, and nothing was missed by either run.

**Not checked by anything in this milestone,** stated so a reader does not infer completeness from
silence: validation-rule field tokens, assignment-rule criteria, Flow field references, entitlement
milestones and path steps. None exists in the build yet (M3 and M4 are `pending`). The classes above are
the ones M2's artefacts actually make.

### 3.3 The five cross-step checks, re-answered

1. **Every permission set named by a PSG exists.** `PSG_Tier1_Prod` → `Case_Agent_Core` + `Case_Tier1`;
   `PSG_Tier2_Prod` → `Case_Agent_Core` + `Case_Tier2`; `PSG_Billing_Prod` → `Case_Agent_Core` +
   `Case_Billing`. All six resolve to `M2-S02` files. `check_permission_set_group_composition.py` at
   build scope independently reports `GOOD: reuse: permission set 'Case_Agent_Core' is referenced by
   3 PSGs`. **PASS.**

2. **Every profile `recordTypeVisibilities` and `layoutAssignments` resolves to an M1 record type and
   layout.** 9 record-type references → `Case.Support` / `Case.Billing` (`M1-S01`); 9 layout references
   → the two `M1-S02` layouts; 6 record types inside those layout assignments likewise. **PASS — this is
   F-01's closure, and it is re-run below at build scope as the gate asked.**

   ```bash
   python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts
   ```

   exit **0**, capture `tests/M2/check_record_type_layouts.v2.stdout.txt`:

   ```json
   {
     "score": 100,
     "findings": [],
     "summary": "Scanned 15 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s) detected."
   }
   ```

   The `--strict` form (which `M2-S03.acceptance_tests[1]` declares) is byte-identical and also exits 0
   — capture `tests/M2/check_record_type_layouts.strict.v2.stdout.txt`. **Identical to v1's run in every
   number.** The comparison that matters is still with `MILESTONE-M1-REPORT-v2.md` § 10.1, where the
   same build-scope command printed `8 metadata file(s)` and resolved **zero** `layoutAssignments`,
   because `collect()` reads them only from `Profile` and `PermissionSet` roots and no `Profile` then
   existed. `M2-S03`'s three profiles are that missing root.

3. **Every public group a queue names exists in `M2-S04`.** `Tier_1_General` → `Support_Tier_1`;
   `Tier_2_Engineering` → `Support_Tier_2`; `Billing` → `Billing_Team`. **PASS.** No `<users>` element
   appears in any of the six queue or group files (`grep -rl "<users>" artefacts/M2-S04/` → 0 files), so
   no named user is hard-coded (Q29).

4. **The sharing rule's `sharedTo` group exists.** `Support_Cases_To_Tier_2` →
   `<group>Support_Tier_2</group>` → `artefacts/M2-S04/groups/Support_Tier_2.group-meta.xml`. **PASS** —
   but see **F-20** on where the recorded deploy positions put the two relative to each other.

5. **Every `<description>` is within the platform limit (the F-15 rule).** 26 description elements
   across M1 + M2; **maximum 250; zero over 255. PASS on the platform limit.** The 200-character
   headroom band, which is what F-16 turned on:

   | Length | File | Step | Does any checker read it? |
   |---|---|---|---|
   | 250 | `Bypass_Case_Intake_Validation.customPermission-meta.xml` | `M2-S01` | **no** — no DESC rule covers `CustomPermission` |
   | 249 | `Region__c.field-meta.xml` | `M1-S01` | **no** — no DESC rule covers `CustomField` |
   | **244** | `Case_Intake_Integration.permissionset-meta.xml` | `M2-S01` | **yes, by all three access checkers** — the F-16 file |
   | 235 | `Support_Tier__c.field-meta.xml` | `M1-S01` | no |
   | 229 | `Support_Tier_1.group-meta.xml` | `M2-S04` | no |
   | 224 | `Severity__c.field-meta.xml` | `M1-S01` | no |
   | 220 | `Support_Tier_2.group-meta.xml` | `M2-S04` | no |
   | ≤ 200 | the other 19, including all four `M2-S02` permission sets (183–199) and all three `M2-S03` profiles (147–152) after the F-15 rebuild | | |

   **Correction of record:** v1's § 3.2 table listed four files in the 201–250 band. There are **seven**
   — it omitted the three `M1-S01` field descriptions (249 / 235 / 224). The omission changed no verdict,
   because no checker in the library reads a `CustomField` or `CustomPermission` description at all. It
   is worth a line for the opposite reason: **`Region__c` at 249 characters is six from the platform
   limit and nothing in this build would catch it crossing.** That is the F-15 failure mode one metadata
   type over, with no rule behind it.

### 3.4 The one unclassifiable reference

`artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml` line 11 →
`<criteriaItems><field>RecordTypeId</field><operation>equals</operation><value>Support</value>`.

The value is a record-type reference in bare developer-name form, which grep resolution cannot
distinguish from a literal string: `RecordTypeId` on a criteria item may take a developer name or an
18-character Id, and the Metadata API guide establishes neither (`M2-S05/deploy-order.md` Decision 3
carries the UNVERIFIED marker verbatim). Reported as **unclassifiable**, not counted as resolved — and
this single item is what caps confidence at MEDIUM in both runs.

**It is nonetheless the best-evidenced item in this milestone.** `reports/MOCK-DEPLOY-M2.md` run 3
validated `SharingCriteriaRule Case.Support_Cases_To_Tier_2` with this exact value against
`sfskills-dev`.

---

## 4. Deployment order (Step 4)

Canonical sequence: objects (1) → fields (2) → picklists (3) → record types (4) → layouts (5) →
**permission sets (6)** → **sharing (7)** → automation (8) → **routing (9)** → SLA (10). Positions are
those the doc keeper recorded on each workbook row, re-read this run from `workbook/03`, `/04`, `/06`
and `/99`.

| Artefact | Type | Recorded position | Agrees with the artefact's own type? |
|---|---|---|---|
| `Bypass_Case_Intake_Validation` | CustomPermission | 6, pos 1 in step | yes — no slot of its own; must precede the set that grants it |
| `Case_Intake_Integration` | PermissionSet | 6, pos 2 in step | yes |
| `Case_Agent_Core`, `Case_Tier1`, `Case_Tier2`, `Case_Billing` | PermissionSet | 6 | yes |
| `PSG_Tier1_Prod`, `PSG_Tier2_Prod`, `PSG_Billing_Prod` | PermissionSetGroup | 6, after all four sets | yes — composition-only |
| `Acme Support Tier 1 / Tier 2 / Billing` | Profile | 6 (the access layer) | yes |
| `Case` | SharingRules | 7 (sharing) | yes by type — **but see the backwards dependency below** |
| `Support_Tier_1`, `Support_Tier_2`, `Billing_Team` | Group | 9 (routing), groups before queues | a Group has no slot of its own by type; filed with the queues it feeds |
| `Tier_1_General`, `Tier_2_Engineering`, `Billing` | Queue | 9, after all three groups | yes |

**No artefact's recorded position contradicts its own type.** The two ordering constraints that break a
deploy most often are satisfied:

- *Permission sets after the objects and fields they grant* — `skills/devops/permission-set-deployment-ordering`'s
  case. `Case_Agent_Core` carries `fieldPermissions` for `Case.Severity__c`, `Account.Region__c` and
  `Account.Support_Tier__c`, all `M1-S01` (position 2) and all already accepted. **No `fieldPermissions`
  entry in M2 names a field this build defines later. No violation.**
- *Profiles after the record types and layouts they assign* — `M2-S03 depends_on [M1-S02, M2-S02]`, and
  positions 4 and 5 precede 6. **No violation.**
- *Automation before the routing it triggers* — `skills/devops/flow-deployment-activation-ordering`'s
  case. **Not applicable to M2:** it contains no Flow, no Apex and no active-state artefact. Recorded as
  not-applicable rather than silently passed.

### One backwards dependency (F-20) — unchanged, and it is why the verdict is not `ready-for-gate`

`SharingRules:Case` sits at **7** and references `Support_Tier_2`, a `Group` filed at **9**. Read as a
staged sequence, the rule deploys two positions before the group it shares to, and a `sharedTo` naming
an absent group is a deploy failure.

Three things keep this off the blocking list, all re-confirmed:

1. The **step** graph is right — `M2-S05 depends_on [M1-S01, M2-S04]`, so `M2-S04` is `documented` first.
2. **The artefacts say so themselves.** `M2-S05/deploy-order.md` names `Support_Tier_2.group-meta.xml` /
   `M2-S04` under "Dependencies on components OUTSIDE this step", and quotes the skill's own words:
   *"Deploy order matters: OWD and roles first, then groups, then the rules that reference them."* The
   `Support_Tier_1` workbook row at position 9 likewise records *"Deploy the group before any queue or
   sharing rule."* **The bookkeeping contradicts itself in the same sentence that states the rule.**
3. The org agrees — mock deploy run 3 sent all seven steps as one request and validated 32 of 32.

So it is a contradiction in the ten-position bookkeeping, not in the build, and it is live only for
someone who stages a deploy **by position** rather than by the step graph. It is carried as a **LOW
finding the human may accept**, which is what puts this milestone at `ready-with-findings` rather than
`ready-for-gate` — see § 13 for that reasoning stated in full rather than assumed.

### The post-deploy step without which none of this grants anybody anything

Not an ordering finding, but it belongs beside one. **`GroupMember` rows do not deploy.** The Metadata
API guide, quoted in `M2-S05/deploy-order.md`: *"Members of the public group aren't migrated when you
deploy the group type."* All three groups deploy empty; the sharing rule and all three queues then show
active in Setup and grant nobody anything until the rosters are loaded as data. Owner: CRM admin lead;
tracked in `artefacts/M2-S04/queue-retirement-runbook.md`. **A green deploy of M2 is not a working
access model.**

---

## 5. Merged manifest (Step 5) — recomputed, and deliberately not rewritten

The five step manifests were re-merged from scratch this run: members unioned per type, members sorted
inside each `<types>` block, `<types>` blocks sorted by type name, one `<version>`.

| Type | Members | From |
|---|---|---|
| `CustomPermission` | 1 — `Bypass_Case_Intake_Validation` | `M2-S01` |
| `Group` | 3 — `Billing_Team`, `Support_Tier_1`, `Support_Tier_2` | `M2-S04` |
| `PermissionSet` | 5 — `Case_Agent_Core`, `Case_Billing`, `Case_Intake_Integration`, `Case_Tier1`, `Case_Tier2` | `M2-S01` (1) + `M2-S02` (4) |
| `PermissionSetGroup` | 3 — `PSG_Billing_Prod`, `PSG_Tier1_Prod`, `PSG_Tier2_Prod` | `M2-S02` |
| `Profile` | 3 — `Acme Billing`, `Acme Support Tier 1`, `Acme Support Tier 2` | `M2-S03` |
| `Queue` | 3 — `Billing`, `Tier_1_General`, `Tier_2_Engineering` | `M2-S04` |
| `SharingRules` | 1 — `Case` | `M2-S05` |
| **Total** | **7 types, 19 members** | |

**`reports/MILESTONE-M2-package.xml` was NOT regenerated, because its members did not change.** The
comparison, from `tests/M2/manifest.v2.stdout.txt`:

```text
committed:       7 types, 19 members, version 62.0
freshly merged:  7 types, 19 members, version 62.0
members only in committed : none
members only in fresh merge: none
MEMBER SETS IDENTICAL: True  -> regeneration NOT required
byte-identical to canonical render: True
```

The committed file is byte-identical to the canonical render of the fresh merge, so rewriting it would
change only its mtime. **Deliberate: a merged manifest whose mtime moves without its content moving is
how F-18 became hard to spot on the M1 side.** Leaving the file untouched keeps its mtime an honest
record of when its content was last decided.

- **API version: no conflict.** All five step manifests declare `62.0`, as do both M1 manifests.
  (`plan.json` still carries no `api_version` key — this is the eighth agent-side default. **F-06**,
  open.)
- **Member collisions inside M2: none.** No `type:member` pair appears in two steps. `PermissionSet` is
  the only block two steps contribute to, and their five members are disjoint.
- **Member collisions against M1: none.**
- **One member name reused across two types, which is not a collision:** `Case` appears as
  `CustomObject:Case` (`M1-S01`) and `SharingRules:Case` (`M2-S05`). Different components; they coexist.
- **Files under the milestone's artefacts reaching no `<types>` block: 12,** and all 12 are correct —
  five `package.xml` (the manifests themselves), five `deploy-order.md`, `queue-retirement-runbook.md`
  and `case-visibility-model.md`. **No source-format metadata file is missing from the manifest.**

### The `SharingRules:Case` container form, recorded rather than smoothed over

The manifest addresses the **container** (`<name>SharingRules</name>`, member `Case`).
`skills/admin/sharing-and-visibility/references/metadata-examples.md` § 6 prescribes the **rule-type**
form — `<name>SharingCriteriaRule</name>`, member `Case.Support_Cases_To_Tier_2` — and says
`SharingRules` "is not what you address". Two other skills in the library
(`admin/experience-cloud-guest-access`, `admin/data-skew-and-sharing-performance`) manifest the
container form. The container form is here for a mechanical reason the step records: the `manifest` test
derives the member from the file stem (`Case.sharingRules-meta.xml` → `SharingRules`:`Case`), so the
rule-type form would leave the file uncovered *and* declare a member with no file of its own.

**Both forms deploy the same file, and all three mock-deploy runs were source-mode** (`--source-dir`),
so the CLI derived components from the tree and never opened a `package.xml`. **The container form in
this merged manifest has still not been read by a deploy.** § 12 names the one command that would read
it.

### F-18 — the M1 merged manifest beside this one is still stale

Re-verified this run:

| File | `CompactLayout` member | Last written |
|---|---|---|
| `artefacts/M1-S01/package.xml` | **`Case.Case_Intake`** (object-qualified, correct) | 2026-09-11 20:12 |
| `reports/MILESTONE-M1-package.xml` | **`Case_Intake`** (bare — the exact form a deploy rejected by name) | **2026-09-09 16:16** |

`MILESTONE-M2-package.xml` carries no `CompactLayout` member and is unaffected. **A human merging M1 and
M2 into one manifest must take `Case.Case_Intake`, not `Case_Intake`.** Not fixed here: this agent
verifies one milestone per invocation, and M1's manifest belongs to M1's verification run.

---

## 6. Acceptance-test results (Step 6)

M2 declares **4** acceptance tests. Three are executable; the fourth is `manual` and goes to § 8. Every
command was run **verbatim, from the build directory**, as `standards/build-orchestration.md` § 5
requires. Captures under `tests/M2/` with a `.v2.` suffix, alongside — never over — v1's.

| Test | Type | Command | Declared | **v1 actual** | **v2 actual** |
|---|---|---|---|---|---|
| `M2-T1` | checker | `check_access_model.py --manifest-dir artefacts` | exit 0 | **exit 1** | **exit 0** ✅ |
| `M2-T2` | checker | `check_sharing_model.py --manifest-dir artefacts` | exit 0 | exit 0 | **exit 0** ✅ |
| `M2-T3` | manifest | two-way over the merged manifest | consistent | consistent | **consistent** ✅ |
| `M2-T4` | manual | joint tick by the support manager and admin lead | ticked at the gate | deferred | **deferred — § 8 line 1** |

**All three executable tests pass. Zero failing declared tests.**

### 6.1 `M2-T1` · checker · **PASS (exit 0)** — the F-16 line

```bash
python3 skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py --manifest-dir artefacts
```

```json
{
  "score": 97,
  "findings": [
    {
      "severity": "WARN",
      "location": "artefacts/M2-S01/permissionsets/Case_Intake_Integration.permissionset-meta.xml",
      "message": "PSVP-DESC-02 PermissionSet description is 244 characters, approaching the 255-character limit."
    }
  ],
  "summary": "Scanned 11 access-model metadata file(s); 1 finding(s) detected.",
  "blocking": 0
}
```
```text
stderr: WARN: 1 finding(s) detected (0 blocking)
exit 0
```

Captures: `tests/M2/check_access_model.v2.{stdout,stderr,exit}.txt`.

**Read this carefully, because the finding did not go away.** The 244-character description is still
reported, still on the same file, with the same rule id. What changed is that it is now classified as
non-blocking (`"blocking": 0`) rather than exit-worthy. The test's **declared** assertion — *"no
dangerous system permission, no migratable permission left on a profile"* — held in v1 and holds now;
the exit code has simply stopped disagreeing with it. **F-16 is closed at the tooling, not at the
artefact.** § 6.4's controls are what make that a verified statement rather than a hopeful one.

### 6.2 `M2-T2` · checker · **PASS (exit 0)**

```bash
python3 skills/admin/sharing-and-visibility/scripts/check_sharing_model.py --manifest-dir artefacts
```
```json
{
  "score": 100,
  "findings": [],
  "summary": "Scanned 10 sharing-model metadata file(s) (1 object OWD(s) resolved); 0 finding(s) detected."
}
```

`1 object OWD(s) resolved` is the load-bearing number: the checker read `M1-S01`'s
`<sharingModel>Private</sharingModel>` and measured `M2-S05`'s `Edit` grant against it. At step scope
the same command resolves **0** OWDs and exits 0 on any value — a vacuous pass the plan deliberately
widened to build scope (verifier item B01). Identical to v1 in every number. Captures:
`tests/M2/check_sharing_model.v2.{stdout,stderr,exit}.txt`.

This run is the second time that assertion has run and passed, which discharges the "has not run"
sentence still carried by `M1-S01`'s `CWB-SHARE-001` workbook row and `REQ-010` (O-M2S05-02). Neither
row is this agent's to rewrite.

### 6.3 `M2-T3` · manifest · **PASS (consistent)**

Two-way over the merged manifest and the milestone's 13 metadata files.

- **File → manifest:** all 19 derived `type:member` pairs appear. **0 missing.**
- **Manifest → file:** all 19 named members have a file. **0 orphans.**
- Files reaching no `<types>` block: the 12 documentation and manifest files listed in § 5.
- Always-on XML parse: **24 files parsed, 0 failures.**

Capture: `tests/M2/manifest.v2.stdout.txt`.

### 6.4 The four negative controls — why the new green is earned rather than quiet

An exit policy that was narrowed is exactly the kind of fix that can pass a milestone by no longer
looking. All four controls ran against a **copy of `artefacts/` in the session scratchpad**; no file
under the build directory was modified.

| Control | Injection | Expected | Result |
|---|---|---|---|
| **A** | none — the real tree, with `--strict` | exit 1 (the flag promotes the WARN) | **exit 1**, `"blocking": 0`. The old behaviour is still reachable, explicitly |
| **B** | `<userPermissions>ModifyAllData</userPermissions>` on `Case_Agent_Core` (check 1) | exit 1 | **exit 1**, `"blocking": 1`, `HIGH PermissionSet grants dangerous system permission 'ModifyAllData'` |
| **C** | `<objectPermissions>` on `Case` added to `Acme Support Tier 1` (check 2) | exit 1 | **exit 1**, `"blocking": 1`, `HIGH … profile grants object permissions on 1 object(s) (Case) — object CRUD has a permission-set equivalent and belongs there`, plus three INFO duplicate-grant lines |
| **D** | `Case_Intake_Integration` description pushed to 300 characters (`PSVP-DESC-01`) | exit 1 | **exit 1**, `"blocking": 1`, `ERROR PSVP-DESC-01 … 300 characters, over the 255-character limit` |

**Control C is the one that matters most.** "No migratable permission left on a profile" is half of
`M2-T1`'s declared assertion, and it was a `WARN` before commit `214da9abd`. Under the narrowed exit
policy alone, a `WARN` would now exit 0 — and that half of the test would have become unassertable
while appearing to pass. The commit raised check 2 to `HIGH` in the same change, and control C proves
the raise took effect. **Both halves of M2-T1's declared assertion are live and blocking.** The only
thing that stopped being blocking is the description-length advisory, which is the thing that should
never have been.

### 6.5 F-17 — the three access checkers now agree

The three checkers that read the same 244-character description, all at build scope this run:

| Checker | Rule | Exit on this WARN | Exit-1 policy in source | `--strict`? |
|---|---|---|---|---|
| `permission-sets-vs-profiles/scripts/check_access_model.py` | `PSVP-DESC-02` | **0** | `BLOCKING_SEVERITIES = {CRITICAL, ERROR, HIGH}` (line 182) | **yes** |
| `permission-set-architecture/scripts/check_permission_set_architecture.py` | `PSA-DESC-02` | **0** | `return 1 if any(level == "ERROR" …)` (line 422) | no |
| `permission-set-group-composition/scripts/check_permission_set_group_composition.py` | `PSGC-DESC-02` | **0** | `if errors: return 1` (line 433) | yes |

**Same file, same fact, three exit codes of 0.** In v1 this row read 1 / 0 / 0, and that disagreement
*was* F-17. **F-17 is closed:** whether a description-length advisory can fail a milestone no longer
depends on which of three checkers the plan happened to declare.

One residue, recorded because "they agree" should not be read as "they are identical":
`check_permission_set_architecture.py` has **no `--strict` flag** and no `HIGH` tier — it is
ERROR-or-nothing. So a caller who wants advisory findings to fail can get that from two of the three
and not the third. That is a smaller inconsistency than F-17 was, it changes nothing about this
milestone, and it is named here so the next person to touch those three files sees it.

### 6.6 Observation runs — not declared tests, and they gated nothing

Five checkers run at build scope because the gate should see what they say about M2 as a whole. None is
in `M2.acceptance_tests[]`; none contributed to any pass verdict. Captures
`tests/M2/OBSERVATION-*.v2.{stdout,stderr,exit}.txt`. **All five are identical to v1 except
`check_access_model` above, which is not in this table.**

| Checker at `--manifest-dir artefacts` | Exit | What it said |
|---|---|---|
| `check_custom_permissions.py` | **0** | `Bypass_Case_Intake_Validation  0  permission set 'Case_Intake_Integration'`; `0 error(s), 0 warning(s), 0 info`. The grant is not dangling. **`Consumers: 0` is the designed state at M2** — the consumers are `M3-S01`'s validation rules |
| `check_permission_set_architecture.py` | **0** | one line: `WARN: PSA-DESC-02 … Case_Intake_Integration … 244 characters` |
| `check_permission_set_group_composition.py` | **0** | `GOOD: reuse: permission set 'Case_Agent_Core' is referenced by 3 PSGs`; `1 good, 0 error, 1 warn, 0 info, scanned 3 PSG file(s)` |
| `check_queues.py` | **0** | all three queues with `Objects : Case`, all three groups, `Warnings found (2)` — `Tier 1 General` **and** `Tier 2 Engineering` have no `<email>`. Confirms O-M2S04-01: the step test's description predicts `(1)` |
| `check_data_skew_and_sharing_performance.py` | **0** | `No data skew or sharing performance issues found.` At build scope the groups are referenced by a queue and by the sharing rule, so the three "used but unmigrated" WARNs O-M2S04-04 recorded at step scope do not fire. Record counts skipped: skew is data, and no `--skew-plan` exists in a design-only build |

### 6.7 The org-facing evidence — human-run, before G3, and unchanged

`standards/build-orchestration.md` § 5 names `scripts/mock_deploy.py` as the validation a human runs
after a milestone verifies and before the G3 decision. It has been run three times for M2
(`reports/MOCK-DEPLOY-M2.md`); **run 3 remains the evidence for this gate:**

```bash
python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev \
  --step M1-S01 --step M1-S02 --step M2-S01 --step M2-S02 --step M2-S03 --step M2-S04 --step M2-S05
```

**Succeeded — 32 components, 0 errors, `checkOnly: true`.** Every artefact of milestones 1 and 2
validates unmodified, including the sharing rule's bare `Support` criteria value and the 244-character
description that F-16 was about. Runs 1–2 are the F-15 history: run 1 failed 10 of 30 on
`Description: data value too large … (max length=255)`; the three access skills gained the DESC rules
(`4da8e6c92`); `M2-S02` and `M2-S03` were rebuilt; run 2 validated 30 of 30.

Two limits on that evidence, so it is not over-read: all three runs were `--mode source`, so no
`package.xml` was opened (§ 5, F-18); and `checkOnly: true` validates metadata, not access — no user was
assigned, no `GroupMember` row loaded, no record read.

---

## 7. Findings

**Closed since v1: F-16, F-17** (both at the tooling, by commit `214da9abd`). **Already closed and
re-confirmed: F-01, F-12, F-13 (step manifest), F-15 (platform limit).** **Still open: F-18, F-19, F-20,
F-21.** **New in this run: F-22, F-23.**

### Closed

#### F-16 · was HIGH, **CLOSED at the tooling** — M2's own acceptance test no longer exits 1 on a description-length WARN

*v1: `check_access_model.py --manifest-dir artefacts` exited 1 where `M2.acceptance_tests[0].expected`
says `exit 0`. The only finding was a 244-character `<description>`.*

**What closed it.** Commit `214da9abd` (skill v1.2.1) narrowed the checker's blocking set to
`CRITICAL` / `ERROR` / `HIGH`. The same command, on the same unmodified artefacts, now exits **0** and
reports `"blocking": 0` (§ 6.1). `--strict` preserves the old all-findings-fail behaviour for a caller
who wants it (control A).

**Which remedy this was.** v1 offered two: **(a)** rebuild `M2-S01` with a shorter description, or
**(b)** the planner restates what a headroom WARN should mean at milestone scope. **Neither was taken.**
The fix landed one layer below both — in the checker's exit policy — which answers v1's own framing of
F-17 ("the three skills, in one change, deciding once whether a WARN is exit-worthy") rather than
patching this milestone. Consequences of that choice, stated plainly:

- **`M2-S01` was not rebuilt, and its artefacts are unchanged.** The 244-character `<description>` is
  still there, and `check_access_model.py` still reports it every run as `PSVP-DESC-02`. It deploys
  (proven: 244 < 255, mock run 3) and it no longer fails a test.
- **The 250-character `CustomPermission` description v1 flagged alongside it is also unchanged,** and no
  checker in the library reads it (§ 3.3). Same for `Region__c` at 249. If the human wants the headroom
  rule actually enforced on those types, that is a skills change, not a build change.
- **Nothing was re-tested at step level.** `tests/M2-S01/check_access_model.exit.txt` still records the
  `0` from 2026-09-06, produced by a checker two versions older than the one that just ran. It happens
  to agree with today's result for a different reason than it did then. See **F-22**.

**Deploy-time error it predicted:** none, in either run.

#### F-17 · was MEDIUM, **CLOSED** — the three DESC-rule checkers now agree that a WARN exits 0

Full evidence in § 6.5. In v1 the three checkers reading the same 244-character description exited
1 / 0 / 0; they now exit **0 / 0 / 0**. The fix was made in the one checker that disagreed, aligning it
to the repo policy the other two already followed (blocking = `CRITICAL` / `ERROR` / `HIGH`). Residue,
recorded not as an open finding but as a note for the next editor of those files:
`check_permission_set_architecture.py` has no `--strict` and no `HIGH` tier.

#### F-01 · HIGH · **CLOSED** (re-confirmed at build scope this run)

`M2-S03`'s three Profiles are the `layoutAssignments` root `collect()` needed.
`check_record_type_layouts.py --manifest-dir artefacts` → `Scanned 15 metadata file(s): 2 record
type(s), 2 layout(s); 0 finding(s) detected.`, exit 0, both with and without `--strict` (§ 3.3). All 9
`layoutAssignments/layout` and all 9 `recordTypeVisibilities/recordType` references resolve, proven
independently in § 3.2 rather than by that exit code. The stale `M2-S01` pointer in the v1 M1 report and
in two gate notes is **moot**, not re-pointed (O-M2S01-01's own conclusion). **Partial:** the
record-type half of the same assertion is asserted by nothing in the checker — that is **F-19**.

#### F-12 · MEDIUM · **CLOSED at the tooling** (re-confirmed)

`scripts/build_plan.py:2182–2196` carries the guard: an `accepted` milestone keeps its status, the
verdict is appended to `reverifications[]`, and the CLI prints the `gate … reject` line as the only way
to withdraw a human's G3. Read in source this run. **M2 is `rejected`, not `accepted`, so this run's
`set-milestone` writes the status directly and the guard is not exercised** — which is the difference
that makes the status move this time. `milestones[M1].status` now reads `accepted` (§ 1).

#### F-13 · MEDIUM · **CLOSED in the step manifest, still OPEN in the merged one** → see F-18

#### F-15 · HIGH · **CLOSED on the 255-character platform limit**

Maximum description across M1 + M2 is **250**; zero over 255 (§ 3.3). Mock runs 2 and 3 validate 30/30
and 32/32. The 200-character headroom half is no longer a finding about this build at all — it is an
advisory the checker now reports and does not fail on.

### Still open

#### F-18 · MEDIUM · `reports/MILESTONE-M1-package.xml` is stale; F-13's fix never reached it

Full statement in § 5, re-verified this run. The committed merged M1 manifest carries the bare
`CompactLayout` member `Case_Intake`; `artefacts/M1-S01/package.xml` carries the corrected
`Case.Case_Intake`; the merged file's mtime (2026-09-09 16:16) predates the M1-S01 rebuild
(2026-09-11 20:12) by two days. Mock deploy #4's manifest-mode success does not discharge it: it read an
on-the-fly merge of the step files, because `mock_deploy.py:resolve_manifest_text()` reads
`reports/MILESTONE-<id>-package.xml` only when exactly one `--milestone` is named with no `--step`
mixed in, and run #4 passed `--step M1-S01 --step M1-S02`.

**Deploy-time error it predicts,** per `skills/devops/deployment-error-diagnosis`: `An object
'Case_Intake' of type CompactLayout was named in package.xml, but was not found in zipped directory` —
already observed once, on this exact member. **Remedy:** regenerate `MILESTONE-M1-package.xml` on M1's
next verification, or a human takes `Case.Case_Intake` when merging M1 + M2 by hand. **Not fixed here**
— one milestone per invocation.

#### F-19 · MEDIUM · `check_record_type_layouts.py` resolves the layout half of a profile reference and not the record-type half

v1 established this with a negative control: a `layoutAssignments/layout` rewritten to a ghost fires a
LOW and exits 1 under `--strict`; a `recordTypeVisibilities/recordType` rewritten to `Case.Ghost` fires
**nothing at any scope**, exit 0 with and without `--strict`. **Unchanged** — commit `214da9abd` touched
a different skill, and this run's identical output (`15 metadata file(s)`, `0 finding(s)`) is consistent
with both a correct tree and an unasserted half.

**Nothing is wrong in this build.** All 9 `recordTypeVisibilities` references resolve, proven in § 3.2
by the inventory walk rather than by that exit code. What is wrong is what the exit code is *claimed* to
carry: `steps[M2-S03].acceptance_tests[1].description` says the run resolves "any `Profile`-sourced
record-type reference", `traceability.md` `REQ-026` repeats it, and `decisions.md` D-M2S03-07 sources
F-01's closure to the same run. The layout half of that claim is earned; the record-type half is not
asserted by the checker.

**Deploy-time error a dangling one would produce:** `INVALID_CROSS_REFERENCE_KEY` on the Profile
component. **Remedy:** add the record-type-resolution rule to `admin/record-types-and-page-layouts`'
checker, then narrow the test description to what it proves until that lands.

#### F-20 · LOW · The recorded deploy positions put the sharing rule ahead of the group it shares to

Full statement in § 4. `SharingRules:Case` at position 7 references `Support_Tier_2`, a `Group` filed at
position 9. **Unchanged.** Mitigated three ways (the step graph, the step's own `deploy-order.md`, and
mock run 3's single atomic request) and live only for a human staging by position. The sharpest form of
it: the `Support_Tier_1` workbook row at position 9 itself says *"Deploy the group before any queue or
sharing rule"* — the constraint and its violation are in the same cell. **Remedy at v6:** record the
groups at the access layer alongside the permission sets they are peer to, or annotate position 9 with
the precedence the row already states.

#### F-21 · LOW · F-08 is closed across all five M2 steps and still open on both M1 steps

Re-grepped this run, and the three lines are exactly where v1 left them:

```text
artefacts/M1-S01/deploy-order.md:141  sf project deploy validate --target-org <your-sandbox-alias> …
artefacts/M1-S02/deploy-order.md:135  sf project deploy validate --target-org <your-sandbox-alias> …
artefacts/M2-S01/deploy-order.md:134  sf project deploy validate --target-org <your-production-alias> … --test-level RunLocalTests
```

`sf project deploy validate` is documented as production-only, requires Apex tests, and returns a job id
for a later quick deploy. **Both M1 files print it against an alias the same line calls a sandbox; M2-S01
gets it right** and emits `deploy start --dry-run` for the sandbox separately, and the other four M2
steps emit `deploy start --dry-run` only. So `metadata-builder` applies the correct form to new work and
F-08's residue is confined to two files that predate it. **Fix owner:** `metadata-builder`, on M1's next
rebuild. Not fixed here — this agent does not edit artefacts other agents wrote.

### New in this run

#### F-22 · MEDIUM · The fix that closed F-16 made a non-vacuity claim false in three step test descriptions

The plan verifier's item **W09** asked each `check_access_model.py` step test to prove it was not a
discovery no-op, and three step tests answered it the same way — *an empty directory fails this
checker*:

| Test | The claim, verbatim |
|---|---|
| `steps[M2-S01].acceptance_tests[1]` | "W09 — against an empty `artefacts/M2-S01/` this checker exits 1 with 'Scanned 0 access-model metadata file(s); no files matched the provided paths', so it is not a discovery no-op: an empty step fails it." |
| `steps[M2-S02].acceptance_tests[2]` | "W09 — against an empty directory this checker exits 1 ('Scanned 0 access-model metadata file(s)'), so it is not a discovery no-op." |
| `steps[M2-S03].acceptance_tests[0]` | "W09 — an empty `artefacts/M2-S03/` exits 1 here, so this is not a discovery no-op." |

**Measured this run against an empty directory:**

```text
python3 …/check_access_model.py --manifest-dir empty
  WARN  "no profile, permission set, or permission set group metadata files found"
  "blocking": 0
  exit 0                    <-- the three descriptions say 1

… --manifest-dir empty --strict     exit 1
… --manifest-dir does-not-exist     ERROR: --manifest-dir does not exist  exit 1
```

The empty-scan finding is a `WARN`, and `WARN` no longer blocks. **None of the three declared commands
passes `--strict`,** so as declared, all three would now pass against an empty step directory. The same
is true of the milestone test `M2-T1`.

**How much this actually costs, stated honestly — it is smaller than it looks, and it is still real.**
Three independent things stop an empty step from passing in practice: `check-outputs` must confirm every
declared `outputs[]` path exists and is non-empty before `set-status <step> built` is allowed; the
always-on `manifest` test fails a metadata step with no `package.xml`; and a *missing* `--manifest-dir`
is now a usage error that exits 1 immediately. So the build is not currently exposed. What is broken is
the **claim**: W09's answer no longer follows from the checker's behaviour, and a reader who trusts that
sentence is trusting something that stopped being true on 2026-09-11.

**This is F-16's own pattern, inverted.** F-16 was a rule added under a finished step, turning green to
red. F-22 is an exit policy narrowed under three finished steps, turning a stated guarantee into an
unstated one. Both times the step tests were not re-run, and both times the plan's prose kept asserting
the older behaviour. **Remedy, either:** append `--strict` to the three step-scope commands (an
`amend-step` on each, which their `pending`-only precondition forbids while they are `documented` — so
in practice a v6 re-plan), or rewrite the three descriptions to answer W09 from `check-outputs` and the
`manifest` test, which is where the non-vacuity guarantee actually lives now. **Deploy-time error:**
none. This is a claim-versus-behaviour defect inside the build.

#### F-23 · MEDIUM · v1's manual checklist carried six lines; the testers deferred seven

`tests/M2-S04/results.json` has **four** `skipped_manual[]` entries, matching its four `manual`
acceptance tests. v1 § 8 listed three of them. The missing one is `skipped_manual[3]` —
**W02 (3 of 3) and S4**, the ownership-data-skew line over `queue-retirement-runbook.md`.

| Source | `skipped_manual[]` entries | Carried by v1 § 8 | Carried by § 8 below |
|---|---|---|---|
| `M2-S01` | 1 | 1 | 1 |
| `M2-S02` | 0 | — | — |
| `M2-S03` | 0 | — | — |
| `M2-S04` | **4** | **3** | **4** |
| `M2-S05` | 1 | 1 | 1 |
| M2's own `manual` test | 1 | 1 | 1 |
| **Total** | **7** | **6** | **7** |

v1's own sentence records the undercount in passing — "five deferred by the step testers … plus M2's own
milestone manual test" — where the testers deferred six. **Consequence:** a manual test the tester
explicitly declined to tick did not reach the checklist the human ticks at G3, so it would have been
approved without ever being put in front of anyone. The line itself carries a tester **PASS** on all
three of its criteria, so nothing about the build is wrong; the defect is in the assembly of Step 7.
**It is restored as § 8 line 7,** and it is the reason this report states the checklist total in two
places rather than one.

---

## 8. Manual checklist for the human (Step 7)

**Seven lines: six deferred by the step testers (`skipped_manual[]`) plus M2's own milestone manual
test** — see **F-23** on why v1 said six. Each names its origin, what the human does, and what counts as
a tick. **Where a tester gathered file-checkable evidence it is quoted, and every quoted item was
re-confirmed against the artefacts this run — that narrows a line, it never ticks it.** No agent in this
loop ticks any of these.

### ☐ 1 — M2 (milestone) · No named user is hard-coded, and the Billing visibility reading is the one you want

**From:** `M2.acceptance_tests[3]` (`manual`). **Who:** the support manager **and** the admin lead,
jointly. **Ticks when** both halves hold.

*Half one — no hard-coded user.* **Re-confirmed this run:** `grep -rl "<users>" artefacts/M2-S04/`
returns **zero files**. Queue membership is expressed only as
`<queueMembers><publicGroups><publicGroup>`, naming `Support_Tier_1`, `Support_Tier_2` and
`Billing_Team`. `check_queues.py` lists all three groups with `Members : (no members listed)`.
**Verifiable from disk; the two named humans still have to accept it as the design.**

*Half two — the A1 reading.* **Not evidenceable from any artefact, and it is the real content of this
line.** Q13 ("is the Billing restriction record-level or field-level?") was **deferred**. Assumption
**A1** (`risk: high`) takes the record-level reading: a Tier 1 agent cannot open a Billing case at all,
rather than opening it with a field hidden. Every access artefact in this milestone is shaped by that
reading. D5's stated consequence if it is wrong: **`M2-S05` is re-planned, not patched** — the OWD may
relax, the rule set changes, and FLS on the Billing fields becomes the mechanism. **Ticking this line is
accepting A1.** § 10 is the reading in full.

### ☐ 2 — `M2-S01` · The integration permission set grants the bypass and nothing else

**From:** `tests/M2-S01/results.json` → `skipped_manual[0]` (plan-verifier B01, rewritten as an
assertion over artefacts because `PermissionSetAssignment` is record data, not metadata).

**Re-confirmed this run by parsing the file directly:**

```text
Case_Intake_Integration.permissionset-meta.xml
  top-level children (4): label, description, hasActivationRequired, customPermissions
  absent: objectPermissions, fieldPermissions, userPermissions, classAccesses, pageAccesses,
          recordTypeVisibilities, tabSettings, applicationVisibilities, flowAccesses, …
  customPermissions x1 -> Bypass_Case_Intake_Validation = true
  ASSERTION 'grants the bypass and nothing else': HOLDS
  description length: 244  (the F-16 file; now a non-blocking advisory, § 6.1)
```

`deploy-order.md` carries the post-deploy assignment instruction and a named owner ("Security
architect"). **Ticks when** a human accepts that reading. **The residue is not evidenceable in this
build at all:** whether the set is assigned to the integration identity and to **no human user** is
`PermissionSetAssignment` data in a target org. Two recorded absences to see while here: `ApiEnabled` is
deliberately **not** granted (`decisions.md` D-M2S01-02) and the grant carries **no expiry** (D-M2S01-03).

### ☐ 3 — `M2-S04` · All six components are present, named, and every queue supports Case

**From:** `tests/M2-S04/results.json` → `skipped_manual[0]`. **Tester's evidence: PASS** — all six files
present under `artefacts/M2-S04/queues/` and `.../groups/`; all three queue files carry
`<queueSobject><sobjectType>Case</sobjectType></queueSobject>` (Q30). Independently re-confirmed this
run by `check_queues.py` (`Objects : Case` on all three) and by `M2-T3` (6 members ↔ 6 files). **Ticks
on acceptance of the listing.**

### ☐ 4 — `M2-S04` · The per-queue email posture (Q88) — **one criterion does not hold; adjudicate, do not tick blind**

**From:** `tests/M2-S04/results.json` → `skipped_manual[1]` (W02 1 of 3). **Tester's evidence: PARTIAL
MISMATCH**, re-confirmed this run.

| Criterion | Artefact | Holds? |
|---|---|---|
| `Tier_1_General` carries no `<email>` (Omni-Channel push, not email) | no `<email>` element | **yes** |
| `Billing` carries the billing@ queue address | `<email>billing@acme.example</email>` | **yes** |
| `Tier_2_Engineering` carries the Tier 2 shared mailbox | **no `<email>` element at all** | **NO** |

`check_queues.py` independently confirms it: `Warnings found (2)`, naming Tier 1 General **and** Tier 2
Engineering. **This is not a defect in the artefact.** Q88 answers a *posture* for Tier 2 ("a shared
mailbox") and names no address anywhere on file, and `metadata-builder` will not invent one
(`decisions.md` D-M2S04-02, O-M2S04-02). The criterion states a fact the build never grounded. **The
step test's own description is stale too** — it predicts `Warnings found (1)` (O-M2S04-01).

**The human's choice, explicitly:** (a) supply Tier 2's mailbox address and rebuild `M2-S04`, after
which the criterion becomes true; or (b) accept the decided state — no address,
`doesSendEmailToMembers=false`, nobody notified, the record visible in the queue list view — and have
the criterion reworded at v6. **Do not tick as written.**

### ☐ 5 — `M2-S04` · Membership is by group and role, never by named user, and the rosters are current

**From:** `tests/M2-S04/results.json` → `skipped_manual[2]` (W02 2 of 3). **Tester's evidence: PASS on
the file-checkable half**, re-confirmed — no `<users>` element in any of the six files;
`Tier_1_General`'s `queueMembers/publicGroups/publicGroup` names exactly `Support_Tier_1`. **The roster
half is not file-checkable in a design-only build:** a support manager confirms the three public-group
memberships match the current rosters (12 Tier 1 / 4 Tier 2 / 2 Billing, Q8).

**Read alongside it:** `<doesIncludeBosses>true</doesIncludeBosses>` is on all three groups as a *skill
default*, not an answered decision (D-M2S04-01), and `<queueMembers>` names no `<roles>` member even
though Q29 answers "by role and public group" (D-M2S04-03). And the groups deploy **empty** — the
`GroupMember` load is a post-deploy data step (§ 4).

### ☐ 6 — `M2-S05` · Private OWD plus exactly one sharing rule, and no rule reaches Billing

**From:** `tests/M2-S05/results.json` → `skipped_manual[0]` (B01 + B04; B04 rewritten so it is tickable
at the M2 gate from artefacts on disk rather than deferred to M5, which had deadlocked this step).
**Every one of the tester's five grep confirmations re-run this run:**

- exactly **one** `<sharingCriteriaRules>` block — `grep -c` returns **1**;
- `sharedTo` group is `Support_Tier_2` and no other — line 15, `<group>Support_Tier_2</group>`;
- no rule names the Billing record type or `Billing_Team` — "Billing" appears **only** on line 6, inside
  the rule's free-text `<description>`; never as a `criteriaItems.value`, a `sharedTo.group`, or a
  second rule;
- `<sharingModel>Private</sharingModel>` lives on `artefacts/M1-S01/objects/Case/Case.object-meta.xml`
  line 5 and is not restated in `M2-S05`;
- no `*.settings-meta.xml` anywhere under `artefacts/` — `find` returns **0**.

**Ticks when** a human also accepts that `case-visibility-model.md` states, in one sentence, why a Tier 1
agent cannot open a Billing case and names the file the default lives on. It does — quoted in § 10.
**Note what this line is and is not:** it certifies the *configuration*. Proving the *denial* against a
live user is M5's `UserRecordAccess` test, where a sandbox exists.

### ☐ 7 — `M2-S04` · The queue-retirement runbook records the ownership-skew threshold, a monitor and a remedy — **restored; v1 omitted this line (F-23)**

**From:** `tests/M2-S04/results.json` → `skipped_manual[3]` (W02 3 of 3, and verifier item S4).
**Tester's evidence: PASS on all three criteria.** Re-confirmed this run in
`artefacts/M2-S04/queue-retirement-runbook.md`:

| Criterion | Where it lands |
|---|---|
| records the 10,000-record ownership-skew threshold | § 1 table — *"10,000 records of one object owned by a single user or queue"*, citing `skills/admin/data-skew-and-sharing-performance` SKILL.md:88, which quotes the LDV guide's "Avoid having any user own more than 10,000 records" |
| names who monitors the open-case count owned by each queue | § 2 — CRM admin lead, with a weekly/monthly cadence and a `HAVING COUNT(Id) > 10000` SOQL probe |
| states the split-into-buckets remedy | § 3 — "Remedy if the threshold is approached — split into ownership buckets" |

The runbook also records the derivation the criterion does not ask for: at roughly 480 cases a day,
`Tier_1_General` as the catch-all crosses 10,000 owned Cases in about three weeks. **Ticks when** a
human accepts that the runbook says what it needs to say and that the named monitor is the right owner.
**Nothing here is wrong** — the finding is that it was deferred to the gate and then left off the gate's
checklist.

---

## 9. Planner carry-forward — every open item the gate should see in one place

None of these blocks the milestone; all are `plan.json` text or declarations, and
`standards/build-orchestration.md` § 2 gives `build_plan.py` sole authority over them. This agent
touches `plan.json` only through its single `set-milestone` call.

### 9.1 The fourteen M2 open-item series, from `decisions.md`

All fourteen `O-M2S*` ids re-read this run. **Status is unchanged from v1 on all of them except
O-M2S02-04, which the checker fix partly overtakes.**

| id | Item | Status after this run |
|---|---|---|
| **O-M2S01-01** | F-01's remedy named `M2-S01`; `layoutAssignments` is `M2-S03`'s | **Moot, as its own text predicted.** F-01 is closed, so re-pointing it is no longer the applicable fix. Record F-01 as CLOSED, sourced to `M2-S03` |
| **O-M2S02-01** | `deploy-order.md` undeclared in `outputs[]` on `M2-S02` — a regression after `M2-S01` fixed it | **Still open, and still the only M2 step affected.** § 9.3 |
| **O-M2S02-02** | `Case_Tier1` and `Case_Tier2` are identical | **Confirmed again by diff this run, and it still has a twin.** § 9.5 |
| **O-M2S02-03** | `A1.steps[]` does not list `M2-S02` | **Open.** § 9.2 |
| **O-M2S02-04** | F-15 closed at the skills, but no `M2-S02` test description mentions the DESC rules | **Still open, and now half-overtaken.** The DESC rules no longer *fail* anything, so the descriptions' silence costs less than it did. But the same three descriptions now carry a **false** claim about the same checker — that is **F-22**, and it is the larger half of this item now |
| **O-M2S03-01** | `acceptance_tests[1].description` predicts `Scanned 14 metadata file(s)`; the run prints 15 | **Confirmed again by this run: 15.** A build-scoped test whose description quotes a whole-tree file count is invalidated by any later step writing a file the suffix list matches |
| **O-M2S03-02** | Two Questions-to-Ask rows unanswered by any of the 97 clarifications: managed packages forcing a profile assignment; Person Accounts enabled | **Open.** The three profiles were built on the unstated assumption that neither applies |
| **O-M2S03-03** | `A1.steps[]` does not list `M2-S03` | **Open.** § 9.2 |
| **O-M2S04-01** | `acceptance_tests[0].description` predicts `Warnings found (1)`; the run prints `(2)` | **Confirmed again: `Warnings found (2)`**, Tier 1 General and Tier 2 Engineering |
| **O-M2S04-02** | Manual W02 (1 of 3)'s Tier 2 mailbox criterion does not match the artefact | **Confirmed.** Staged for adjudication as § 8 line 4 |
| **O-M2S04-03** | Two plan-level orderings: `M3-S05` (Omni-Channel) sequenced after `M2-S04` against the cited reference's own order; the step's `type` (`access`) disagrees with § 4's artefact table (`routing`) | **Open,** neither fixable at step level. The `type` disagreement is why M2-S04's workbook rows are filed under Section 6 |
| **O-M2S04-04** | Correction of record: the data-skew checker's exit-1 gap is closed (v1.1.1 counts `queueMembers/publicGroups` as use) | **Confirmed again.** At *build* scope the checker reports `No data skew or sharing performance issues found.` — 0 findings, not the 3 reclassified WARNs it gives at step scope |
| **O-M2S05-01** | Billing's own access (queue ownership, `M2-S04`) and Tier 1's exclusion (absence of a rule, `M2-S05`) are two mechanisms in two steps, and nothing reconciles them | **Partly discharged by an artefact, still open in the plan.** § 10 states it plainly for the gate |
| **O-M2S05-02** | Correction of record: `M1-S01`'s `CWB-SHARE-001` and `REQ-010` both say the build-scope `check_sharing_model.py` assertion "has not run" | **It has now run three times and passed three times** — `M2-S05`'s step test, `M2-T1`… `M2-T2` in v1, and `M2-T2` again here. Both stale sentences are `M1-S01`'s doc-keeper's to correct |

### 9.2 `A1.steps[]` lists one step and shapes four

`plan.json` → `assumptions[A1].steps[]` reads **`["M2-S05"]`**, re-read this run. Four steps carry
artefacts A1 shaped:

| Step | What A1 shaped | Recorded as a gap in |
|---|---|---|
| `M1-S01` | the `Private` OWD — **the mechanism that actually makes A1 true** | verifier **W03** |
| `M2-S02` | `Case_Tier1`/`Case_Tier2` withhold `Case.Billing`; `Case_Billing` withholds `Case.Support` | **O-M2S02-03** |
| `M2-S03` | the same mirror-image `recordTypeVisibilities` / `layoutAssignments` split on all three profiles | **O-M2S03-03** |
| `M2-S05` | the deliberate absence of a Billing rule | **listed** |

Three separate agents recorded the same omission three times, on three different steps, and it is still
one line in `plan.json`. **The concrete cost:** `M5-S04`'s compile run builds the assumptions section
from `assumptions[].steps[]` "rather than from step-note prose" — its own acceptance test says so — so
the compiled document will name one carrier of a `risk: high` assumption where four exist. **Remedy at
v6:** `A1.steps[] = ["M1-S01", "M2-S02", "M2-S03", "M2-S05"]`. Note the distinction all three entries
preserve and the fix should not blur: `recordTypeVisibilities` governs which record type a user may
*select*; the Private OWD plus `M2-S05`'s rule governs whether an existing record can be *opened*.

### 9.3 `deploy-order.md` in `outputs[]` — exactly which steps declare it

Re-read from `plan.json` this run. The honest answer is still not "S03–S05 only":

| Step | Declared? | How |
|---|---|---|
| `M1-S01` | **no** | — (F-04 / O-M1S02-02) |
| `M1-S02` | **no** | — (F-04 / O-M1S02-02) |
| `M2-S01` | **yes** | **at plan time, in v5** — 0 amendments. The first step in this build to declare it |
| `M2-S02` | **no** | — the regression O-M2S02-01 records: the step immediately after `M2-S01` did not inherit the fix |
| `M2-S03` | **yes** | `amend-step`, 2026-09-12T00:38:44Z |
| `M2-S04` | **yes** | the same amendment run |
| `M2-S05` | **yes** | the same amendment run |

So: **declared on four of five M2 steps and undeclared on `M2-S02` alone, plus both M1 steps.** All seven
files exist and all seven are non-empty; the four declared ones are the only ones `check-outputs`
confirms. **Why it matters beyond bookkeeping:** `agents/build-doc-keeper/AGENT.md` Step 10 compiles
`M5-S04`'s build-wide deploy order from exactly these seven files, three of which no gate in the loop
confirms. **Remedy at v6:** declare `artefacts/<step-id>/deploy-order.md` on every
`metadata-builder`-owned step at once, rather than case by case as each gap is found.

### 9.4 Test descriptions that no longer describe their run

**Five now, and the fifth is new.** Each `expected` still holds; only the prose is stale. Grouped because
they are one defect: a test's `description` is authored prose, not derived from the checker's current
rule set or from the tree it walks.

| Where | Says | Run says |
|---|---|---|
| `steps[M2-S03].acceptance_tests[1]` | `Scanned 14 metadata file(s)` | **15** (O-M2S03-01) |
| `steps[M2-S04].acceptance_tests[0]` | `Warnings found (1)`, Tier 1 General only | **`Warnings found (2)`**, Tier 1 General and Tier 2 Engineering (O-M2S04-01) |
| `steps[M2-S02].acceptance_tests[0..2]` | no mention of the DESC rules the checkers enforce | the rules ran and were the only thing found (O-M2S02-04) |
| `steps[M2-S03].acceptance_tests[1]` | the run resolves "any `Profile`-sourced record-type reference" | the layout half is asserted; the record-type half is not (**F-19**) |
| **`steps[M2-S01].acceptance_tests[1]`, `steps[M2-S02].acceptance_tests[2]`, `steps[M2-S03].acceptance_tests[0]`** | **"an empty directory exits 1, so this is not a discovery no-op"** | **exit 0 without `--strict`** (**F-22**) — new this run |

`amend-step` is the writer for a test description, and it is refused while a step's status is
`documented` (§ 2 of the contract: `pending` or `blocked` only). So all five wait on a v6 re-plan or on a
rebuild of the step they sit on. **That constraint is itself worth the planner's attention:** four
consecutive verification runs have now recorded stale prose that no agent in the loop is permitted to
correct.

### 9.5 Two identical pairs, at two layers of the same stack

Re-diffed this run, with `<label>` and `<description>` stripped:

- `Case_Tier1` and `Case_Tier2` — **byte-identical apart from `<label>` and `<description>`**: the same
  `fieldPermissions` edit on `Case.Severity__c`, the same `recordTypeVisibilities` on `Case.Support`.
- `Acme Support Tier 1` and `Acme Support Tier 2` — **byte-identical apart from `<description>`**.

No answered clarification distinguishes Tier 2's *access* from Tier 1's — the requirement's Tier 1/Tier 2
split is routing (pushed vs pulled work, `M2-S04`/`M3-S05`) and escalation (untouched 8 business hours,
`M4-S04`), neither of which is access. Four files exist because `outputs[]` declares four.

**Not a defect to fix by re-running a step** — both steps built exactly what the plan declared and both
pass every check declared against them. **The v6 question, now at two layers:** collapse each pair into
one artefact composed into both personas, or keep four declared outputs and accept that they diverge only
when a future requirement gives one team an access the other lacks. O-M2S02-02 asks it for the permission
sets; the profiles are the twin it does not mention.

---

## 10. The Billing visibility reconciliation, stated plainly for the gate (O-M2S05-01)

The gate asked for this in one place, so here it is in one place. **Nothing in it changed between v1 and
v2** — it is restated in full because it is one of the five things § 13 asks the human to decide, and a
reader of v2 should not have to open v1 to find it.

**Billing's access to Billing cases and Tier 1's exclusion from them are two different mechanisms, built
by two different steps, and only one of them is a file you can point at.**

| Who | Support case | Billing case | Mechanism | Step |
|---|---|---|---|---|
| Tier 1 (`Support_Tier_1`) | as **owner**, once `M3-S04`'s assignment rule transfers the case to `Tier_1_General` and a member takes it | **no access** | the Private OWD, and **the absence** of any rule naming `Billing_Team` or the Billing record type | `M1-S01` (OWD) + `M2-S05` (the absence) |
| Tier 2 (`Support_Tier_2`) | `Edit`, by `Support_Cases_To_Tier_2` (`RecordTypeId equals Support`, `includeRecordsOwnedByAll: true`) | no access — the criterion filters it out | a criteria-based sharing rule | `M2-S05` |
| Billing (`Billing_Team`) | no standing access | as **owner**, through the `Billing` queue | **queue ownership — not a sharing rule** | `M2-S04` (the queue) + `M3-S04` (the transfer, `pending`) |

**The asymmetry is deliberate and it is not symmetrical to verify.** Tier 1's exclusion is proved by
finding *no file*; Billing's own access is proved by finding a queue *in a different step*, and it does
not work until `M3-S04` (`pending`) transfers ownership to that queue. A reviewer reading only `M2-S05`
would not learn where Billing's access comes from.

**What an artefact now does reconcile.** O-M2S05-01 says "nothing reconciles them".
`artefacts/M2-S05/case-visibility-model.md` § "How each team actually reaches a case" states all three
rows above and names queue ownership explicitly — *"**This is queue ownership, not a sharing rule.** No
sharing rule was written for Billing, because A1's conservative reading is about keeping others out, and
the Billing team's own access already exists through the queue."* Its one-sentence statement, re-read
and re-verified against the two files it names:

> A Tier 1 agent cannot open a Billing case because `Case` carries `<sharingModel>Private</sharingModel>`
> in `artefacts/M1-S01/objects/Case/Case.object-meta.xml`, which grants a non-owner nothing, and the only
> sharing rule in this build — `Support_Cases_To_Tier_2` — matches `RecordTypeId equals Support` and
> shares to `Support_Tier_2`, so no rule names the Billing record type or the `Billing_Team` group as a
> target and nothing lifts a Billing case above the Private default for Tier 1.

Both halves check out on disk: `Case.object-meta.xml:5` carries `Private`, and the sharing rule file
mentions "Billing" only inside a `<description>` (§ 8 line 6).

**What is still open, and it is the part that matters.** Nothing in **`plan.json`** records the
composition. `A1.steps[]` names `M2-S05` alone (§ 9.2), and no decision entry ties `M2-S04`'s queue to
`M2-S05`'s absence as two halves of one answer. **The consequence O-M2S05-01 names:** a later change to
`M2-S04`'s queue — a second Billing queue, or dropping queue-based ownership for direct assignment —
could silently break Billing's access to its own cases without touching anything `M2-S05` owns, and
nothing in the build would flag the connection.

**What the gate should do with it:** accept, in the same breath as § 8 line 1, that **Billing visibility
= queue ownership (`M2-S04`) + no competing restriction (`M2-S05`'s deliberate absence)**, and ask for
that composition to be recorded at plan level rather than only in one step's documentation artefact.

---

## 11. Requirement closure (Step 9)

M2 serves **REQ-016 … REQ-029** — 14 rows in `traceability.md`. Every row's *machine* half now passes,
and after this run that statement includes `M2-T1`. **No row reaches `Done`,** and two reach `In UAT`:

| Status | Requirements | What that means |
|---|---|---|
| **In UAT** — only the gate tick remains | `REQ-016` (integration-only bypass grant), `REQ-025` (queue retirement does not orphan records) | no further step in `plan.json` depends on either artefact |
| **In Build** — a later step serving the requirement remains | `REQ-017`–`REQ-024`, `REQ-026`–`REQ-029` (12 rows) | the access layer exists; the mechanism that exercises it does not yet |

The named dependencies, so "In Build" is a fact rather than a hedge: `REQ-018`–`020` and `REQ-026`–`028`
wait on nothing in M2 — they read `In Build` because `recordTypeVisibilities` governs *selection* while
*opening* a record is the Private OWD plus `M2-S05`'s rule, and those rows were written when `M2-S05` was
still `pending`. **That dependency has landed** (`M2-S05` is `documented`; `M2-T2` passes at build
scope), so six of the twelve are closer than their recorded status says; correcting the status cells is
`build-doc-keeper`'s on a future pass, not this agent's. The rest genuinely wait: `REQ-021` and `REQ-024`
on `M3-S03`/`M3-S04` (`pending`), `REQ-022` on `M3-S05` (**`blocked`** — deferred Q32–Q35), `REQ-023` on
`M4-S04` and `M5-S01`, `REQ-029` on `M5-S02` (**`blocked`** — a borrowed agent's missing inputs,
unrelated to this row).

**Still open across the milestone, both from deferred blocking questions:**

- **Q13 → assumption A1 (`risk: high`)** — the lineage of `REQ-010`, `REQ-018`–`020`, `REQ-023`,
  `REQ-026`–`029`. **Nine of M2's fourteen requirements rest on a deferred answer.** § 8 line 1 is where
  a human accepts it.
- **Q57 → assumption A13 (`risk: medium`)** — `REQ-014`. Unverifiable until `M3-S01`'s validation rules
  exist, and A13's own stated verification route does not exist (**F-03**).

`REQ-026` carries one extra caveat this run: its recorded evidence is the build-scope
`check_record_type_layouts.py` exit code, and **F-19** is the finding that the record-type half of that
claim is not asserted by the checker. The requirement is satisfied — § 3.2's inventory walk proves it —
but not by the artefact `traceability.md` cites.

---

## 12. Optional validate-only command — for the human, and this agent did not run it

**This agent runs no `sf` command at all.** The lines below are for a human, and nothing in this loop
deploys. The merged manifest names components only; copy the artefacts into a DX source tree first — the
manifest path is relative to the build directory, the source tree is yours to assemble.

**Sandbox target — this is the right form:**

```bash
sf project deploy start \
  --manifest .sfskills/builds/case-onboarding/reports/MILESTONE-M2-package.xml \
  --dry-run --target-org <your-sandbox-alias>
```

`--dry-run` validates and compiles without saving. **Do not use `sf project deploy validate` against a
sandbox** — Salesforce documents it as production-only, it requires Apex tests, and it returns a job id
for a later quick deploy. (Two files in this build get that wrong and both are M1's: **F-21**.)

**Production target, if that is where this is going:**

```bash
sf project deploy validate \
  --manifest .sfskills/builds/case-onboarding/reports/MILESTONE-M2-package.xml \
  --target-org <your-production-alias> --test-level RunLocalTests
```

**The run that is actually worth the human's time here** is the one that reads the merged manifest,
because no deploy ever has — § 5's container-form question and **F-18** both turn on it:

```bash
python3 scripts/mock_deploy.py plan.json --org-alias <alias> --milestone M2 --mode manifest
```

Pass `--milestone M2` with **no** `--step`: that is the only invocation for which
`mock_deploy.py:resolve_manifest_text()` reads `reports/MILESTONE-M2-package.xml` rather than merging the
step files on the fly. `checkOnly: true` is hard-coded and the script has no deploy option.

### Go / no-go items before any deploy of this manifest, per `skills/devops/pre-deployment-checklist`

| # | Item | State |
|---|---|---|
| 1 | M1 is in the target org first | **required** — 33 of M2's 49 references resolve into M1: 9 to `M1-S01` record types, 9 to `M1-S02` layouts, 6 more to `M1-S01` record types via layout assignments, plus the fields and the object. Profiles fail with `INVALID_CROSS_REFERENCE_KEY` without them |
| 2 | Deploy `M2-S04`'s groups before or with `M2-S05`'s sharing rule | **required** — F-20. One request satisfies it; staging by position does not |
| 3 | `GroupMember` rows loaded after deploy | **required, and not in this deploy** — all three groups deploy empty; the sharing rule and all three queues then grant nobody anything. Owner: CRM admin lead |
| 4 | `PermissionSetAssignment` for `Case_Intake_Integration` to the integration identity and no human user | **required, and not in this deploy** — record data. § 8 line 2 |
| 5 | Users assigned to the three PSGs; poll `PermissionSetGroup.Status` for `Updated` before UAT (Q96) | **required, post-deploy** |
| 6 | Target org's `CaseStatus` value set carries the values M1's business processes select | **F-02** — discharged on `sfskills-dev` only; a per-target-org precondition |
| 7 | API version `62.0` is right for the target org | **F-06** — defaulted by the owning agent eight times, never decided in the plan |
| 8 | The merged manifest's `SharingRules:Case` container form is accepted by the CLI | **unverified** — § 5. The `--mode manifest` run above is the check |
| 9 | Sharing recalculation has finished before believing any access reading | **required** — `case-visibility-model.md` says so explicitly |
| 10 | The 244-character description on `Case_Intake_Integration` | **deploys fine** (< 255, proven by mock run 3) and **no longer fails any test** (F-16 closed). It is still reported every run as a `PSVP-DESC-02` advisory |
| 11 | Descriptions on types no checker guards | **watch item, new in v2** — `Region__c` at **249** characters and `Bypass_Case_Intake_Validation` at **250** are within six of the platform limit, and no DESC rule covers `CustomField` or `CustomPermission` (§ 3.3). F-15 was this failure mode with a rule behind it |

---

## 13. Verdict, confidence, and what the human decides at G3

### Verdict: **`ready-with-findings`**

Per `agents/milestone-verifier/AGENT.md` Step 9, `ready-with-findings` is "findings the human may
accept". The verdict moved from v1's `not-ready` because the single condition that forced it is gone:

| Step 9 `not-ready` condition | v1 | v2 |
|---|---|---|
| at least one unresolved reference | 0 unresolved | **0 unresolved** (1 unclassifiable, which is not "unresolved") |
| at least one failing acceptance test | **`M2-T1` exit 1** | **0 failing — all three executable tests pass** |
| at least one blocked step | none | **none** |
| an ordering contradiction | **judged: none by artefact type; one backwards dependency carried as LOW** | **same judgment, same evidence** |

**The ordering row is a judgment, and it is the one a reader should be able to disagree with, so here it
is explicitly.** Step 4 asks for two things: artefacts whose recorded position contradicts the sequence
(**zero**), and dependencies that run backwards through it (**one — F-20**). Read strictly, F-20 is an
ordering contradiction and this milestone is `not-ready` on it alone. This report does not read it that
way, for the reasons § 4 sets out: the step graph orders the two correctly, the artefact that would fail
names the dependency itself, and the org validated all 32 components in one request. **v1 made the same
call on the same evidence** and attributed its `not-ready` verdict to F-16 alone; consistency between the
two runs requires that removing F-16 removes the verdict. A human who weighs F-20 differently should
reject the gate and say so — the finding is in front of them either way, which is the point.

| Check | Result |
|---|---|
| Steps documented | 5 of 5. **No blocked step** |
| References resolved | **49 of 49.** 0 unresolved; 1 unclassifiable (a criteria value the org has since validated) |
| Ordering contradictions | **0 by artefact type.** 1 backwards dependency in the recorded positions, mitigated three ways (F-20) |
| Merged manifest | recomputed, **no collision, no version conflict**, two-way consistent, **byte-identical to the committed file** |
| Milestone acceptance tests | **3 of 3 executable tests pass.** The fourth is `manual` → § 8 line 1 |
| Negative controls | **4 of 4 behave** — the new green is earned, and both halves of `M2-T1`'s assertion are still blocking (§ 6.4) |
| Org-facing validation | mock deploy run 3: **32 components, 0 errors** — every M1 and M2 artefact validates unmodified |
| Closed since v1 | **F-16**, **F-17** |
| New in v2 | **F-22** (a non-vacuity claim the fix falsified), **F-23** (a manual line v1 left off the checklist) |

This verdict is a recommendation, not a decision. It is recorded as `set-milestone --status verified`,
which is a statement about what the checks found — **it is not a gate, and it neither approves G3 nor
obliges the human to.**

### Confidence: **MEDIUM**

Per the Step 10 table. HIGH requires that every declared acceptance test ran **and** no reference was
unclassifiable. **One unclassifiable reference (§ 3.4) puts it at MEDIUM by itself.** Nothing pulls it to
LOW: every step was documented, no declared checker was missing, no artefact directory was empty, the
earlier-milestone inventory built, and every declared test ran. Unchanged from v1 — and worth saying
plainly, because the verdict improved and the confidence did not: **the two measure different things.**
The verdict is about what the checks found; the confidence is about how much of the milestone the checks
could see.

### What the human decides at G3 — five things, in order of consequence

1. **Assumption A1, and whether M2 was built on the right reading of a deferred question.** Q13 was
   deferred; A1 (`risk: high`) takes the record-level reading, and **nine of M2's fourteen requirements
   rest on it**. If the answer is field-level masking, D5's stated consequence is that `M2-S05` is
   **re-planned, not patched**. § 8 line 1 is the tick; § 10 is the reading.
2. **The Billing composition (§ 10).** Billing sees Billing cases as *queue owner* (`M2-S04`, and only
   once `M3-S04` transfers ownership); Tier 1 is excluded by the *absence* of a rule (`M2-S05`). Both are
   individually grounded; `plan.json` records neither as half of the other. Accept the composition, and
   ask for it recorded at plan level.
3. **§ 8 line 4 — the Tier 2 mailbox criterion that does not hold.** Supply Tier 2's address and rebuild
   `M2-S04`, or accept "no address, nobody notified" and have the criterion reworded. **This one must not
   be ticked as written.** It is the only line on the checklist whose evidence is a mismatch.
4. **Whether F-16's remedy is finished.** The checker stopped failing on a 244-character description; the
   description is still 244 characters, `M2-S01` was never rebuilt, and its step-level test result is
   five days and two checker versions old. If the intent was "advisories should not fail a milestone",
   this is done. If the intent was also "descriptions should have headroom", **F-22** and go/no-go item 11
   are what is left of it — and neither is fixable inside this milestone.
5. **F-18 before any manifest-driven deploy.** `MILESTONE-M1-package.xml` still carries the bare
   `CompactLayout` member a deploy has already rejected by name. `MILESTONE-M2-package.xml` is clean; a
   hand-merge of the two must take `Case.Case_Intake`.

**Approving G3 with this report in hand accepts:** assumption A1; the Billing composition; one manual
criterion that does not hold against its artefact (§ 8 line 4); F-20's backwards ordering position; F-19's
unasserted record-type half; F-22's false non-vacuity claim on three step tests; and the carry-forward in
§ 9 — `A1.steps[]` naming one of four carriers, `deploy-order.md` undeclared on `M2-S02` and both M1
steps, five stale test descriptions, and two identical pairs awaiting a collapse decision. **It accepts
no unbuilt gap:** there is no blocked step in M2 and no failing test.

---

## 14. Recorded verdict, and the gate command

The verdict and this report's path were recorded with the one plan write this agent makes — a subcommand,
never a hand edit:

```bash
python3 scripts/build_plan.py set-milestone .sfskills/builds/case-onboarding/plan.json M2 \
  --status verified --report-path reports/MILESTONE-M2-REPORT-v2.md
```

`milestones[M2].status` moves **`rejected` → `verified`**, and `report_path` moves to this file.
**M2 is not `accepted`, so F-12's guard does not intercept the write** and nothing is appended to
`reverifications[]` — the status genuinely moves. `MILESTONE-M2-REPORT.md` (v1) is **not** overwritten
and stays on disk; only the pointer moves.

`set-milestone` takes `--report-path`, not `--file`: no JSON body was handed to the CLI, so nothing was
written under `inputs/`. This run's envelope is at `envelopes/M2/2026-09-12T02-54-59Z.{json,md}`; this
report is under `reports/`. The three trees do not borrow each other's paths.

### The gate is the human's. This agent did not run this line.

```bash
python3 scripts/build_plan.py gate .sfskills/builds/case-onboarding/plan.json milestone:M2 approve \
  --by "<name>"
```

`standards/build-orchestration.md` § 3 will check it against three conditions, **all of which are met**:

| Condition | State |
|---|---|
| `milestone:M1` is `approved` | **yes** — 2026-09-09T20:30:32Z |
| `plan` is `approved` | **yes** — 2026-09-05T19:35:19Z |
| every step in M2 is `documented`, or `blocked` with a recorded reason | **yes** — 5 of 5 `documented`, none blocked |

So the command will succeed if run. **It does not check this report's verdict.** There is no blocked step
in M2, so approving accepts no unbuilt gap; it accepts the five decisions in § 13.

To reject instead — which sets `milestones[M2].status` back to `rejected` and leaves the build at
`building`:

```bash
python3 scripts/build_plan.py gate .sfskills/builds/case-onboarding/plan.json milestone:M2 reject \
  --by "<name>" --notes "<why>"
```

If any finding is to be closed inside the build before the gate, the path is `documented → running` on
the step that owns it (§ 4 of the contract), then `/test-build-step`, `/keep-build-docs`, and
`/verify-milestone` again. Two candidates, both optional: rebuild `M2-S01` to trim the two long
descriptions (§ 13 item 4), or rebuild `M2-S04` with Tier 2's mailbox address (§ 8 line 4).

---

## 15. Process observations

**Healthy.**
- **The remedy landed at the right layer.** F-16 could have been closed by trimming one description, and
  was instead closed by fixing the exit policy that made a length advisory able to fail a milestone —
  which also closed F-17, the finding that said the three checkers should decide this once rather than per
  plan. Evidence: `214da9abd` touches one checker and the § 6.5 table now reads 0 / 0 / 0.
- **The fix protected the assertion it narrowed.** Raising check 2 from `WARN` to `HIGH` in the same
  commit is the part that is easy to skip and expensive to miss: without it, "no migratable permission
  left on a profile" would have become a non-blocking advisory and `M2-T1` would have passed a profile
  carrying `objectPermissions`. § 6.4 control C is the proof, and the commit message names the reasoning.
- **The merged manifest was recomputed and correctly left alone.** Member sets identical, byte-identical
  canonical render, mtime untouched (§ 5). On the M1 side, a manifest whose content and mtime drifted
  apart is F-18.
- **Every quoted piece of tester evidence re-confirmed against the artefacts.** Six manual lines arrived
  with file-checkable halves already gathered; all six halves still hold, re-run rather than copied
  (§ 8). That is what makes the checklist narrower for the human rather than just longer.

**Concerning.**
- **A skill fix moved a claim from true to false under three finished steps** (F-22). This is F-16's
  pattern inverted: F-16 was a rule added under a finished step (green → red); F-22 is an exit policy
  narrowed under three (a stated guarantee → an unstated one). **Both times nothing in the loop re-ran
  the affected step tests, and both times the plan's prose kept asserting the older behaviour.** Two
  instances in six days, in opposite directions, from two commits to the same skill. Evidence:
  `check_access_model.py --manifest-dir <empty>` exits 0 where three `description` fields say 1.
- **A deferred manual test never reached the gate's checklist** (F-23). `tests/M2-S04/results.json` has
  four `skipped_manual[]` entries; v1's § 8 carried three, and its own prose said "five" where six were
  deferred. Step 7 is a gather-all step with no count assertion behind it, so an omission is silent. The
  line's evidence is a clean PASS, so nothing was hidden — but nothing would have caught it if it had not
  been.
- **No agent in the loop may correct a stale test description** (§ 9.4, now five of them). `amend-step`
  is refused on a `documented` step, so every one of these waits on a v6 re-plan or on a rebuild of the
  step it sits on. Four consecutive verification runs have now recorded prose that no agent is permitted
  to fix, and the list grows one entry per run.
- **The 200-character headroom is now enforced on exactly the types that were already compliant.**
  `Region__c` at 249 and `Bypass_Case_Intake_Validation` at 250 are within six characters of the platform
  limit that broke mock run 1, and no checker in the library reads a `CustomField` or `CustomPermission`
  description (§ 3.3). The rule went where the failure was observed rather than where it can recur.

**Ambiguous — for the human, not for this agent.**
- Whether F-16's remedy is complete (§ 13 item 4). "Advisories should not fail a milestone" is done.
  "Descriptions should have headroom" is not, and the two were never separated.
- Whether F-20's backwards position is an ordering contradiction in the Step 9 sense (§ 13). This report
  says no, consistently with v1, and says so where it can be argued with.
- Whether `Case_Tier1`/`Case_Tier2` and the two Tier profiles should collapse (§ 9.5). It depends on
  whether the two teams are expected to diverge on *access* later, which no clarification answers.
- The `SharingRules` container versus `SharingCriteriaRule` rule-type manifest form (§ 5). The cited skill
  says one thing, two other skills in the library do the other, and no deploy has read either form for
  this file.
- Tier 2's queue mailbox (§ 8 line 4): a posture with no address. The artefact is right and the test
  criterion is not, and only a human can say which should change.

**Suggested follow-ups — recommendations only; this agent invoked neither.**
- `deployment-risk-scorer` — to risk-score `reports/MILESTONE-M2-package.xml` against the target org
  before the human runs the § 12 command, since 19 members across `Profile`, `PermissionSet` and
  `SharingRules` is the change class where an org's existing state matters most.
- `permission-set-architect` — to adjudicate § 9.5's collapse question on the two identical pairs with the
  persona model in view, which is a design call rather than a verification one.

---

## Citations

| type | id / path | used for |
|---|---|---|
| standard | `standards/build-orchestration.md` | § 2 (this report is written not rendered; recorded with `set-milestone --report-path`; the three output trees; `amend-step`'s `pending`-only precondition behind § 9.4), § 3 (the G3 conditions checked in § 14), § 4 (the `documented → running` rebuild path), § 5 (checker scope; commands run verbatim from the build directory via the `skills` symlink; `check-outputs` and the always-on `manifest` test as the non-vacuity guarantee F-22 falls back on; `mock_deploy.py` as the pre-G3 human-run validation), § 7 (return so the human can act), § 8 (`build_plan.py` is the single writer) |
| standard | `AGENT_RULES.md` | run-time rules for this invocation: no org write, no auto-chaining, no hand edit of generated state |
| standard | `agents/_shared/AGENT_CONTRACT.md` | section shape, the Process Observations block (§ 15), the confidence rubric this agent's Step 10 overrides |
| standard | `agents/_shared/DELIVERABLE_CONTRACT.md` | atomic write of the envelope/report pair; `dimensions_skipped` states; the build-scoped persistence deviation recorded in the envelope |
| standard | `agents/_shared/REFUSAL_CODES.md` | checked and not used — no refusal condition was met |
| standard | `agents/_shared/schemas/build-plan.schema.json` | the `milestones[]`, `human_gates[]`, `steps[].amendments[]`, `steps[].outputs[]` and `assumptions[]` fields read in § 1 and § 9 |
| standard | `agents/_shared/schemas/output-envelope.schema.json` | envelope shape; the `report_path` / `extensions.report_path` distinction |
| skill | `skills/devops/metadata-api-retrieve-deploy` | the manifest grammar, the single `<version>` element and the sorted-member form in § 5; what one deploy request does and does not carry across, behind § 4's `GroupMember` note |
| skill | `skills/devops/permission-set-deployment-ordering` | § 4's check that no `fieldPermissions` entry names a field defined later in the order — the `Case_Agent_Core` → `M1-S01` fields row, and go/no-go item 1 |
| skill | `skills/devops/flow-deployment-activation-ordering` | § 4: where automation sits in the order, and the recorded finding that M2 contains none, so the check is not-applicable rather than silently passed |
| skill | `skills/devops/deployment-error-diagnosis` | the deploy-time error each finding predicts: `INVALID_CROSS_REFERENCE_KEY` (F-19, go/no-go 1), the `CompactLayout … not found in zipped directory` message (F-18), and the explicit *none* for F-16 and F-22 |
| skill | `skills/devops/pre-deployment-checklist` | § 12's eleven go/no-go items, so "verified" means checked rather than quiet |
| skill | `skills/admin/uat-and-acceptance-criteria` | § 8's Given/When/Then shape, the tick condition on every line, the judgment that § 8 line 4 is not tickable as written, and the completeness check on `skipped_manual[]` that surfaced F-23 |
| skill | `skills/admin/requirements-traceability-matrix` | § 11's closure statement in `traceability.md`'s own REQ ids and `In Build` / `In UAT` vocabulary, and the `REQ-026` caveat F-19 attaches to it |
| skill | `skills/admin/sharing-and-visibility` | `check_sharing_model.py` (M2-T2); § 5's `SharingRules` vs `SharingCriteriaRule` manifest-form divergence, read from `references/metadata-examples.md` § 6 |
| skill | `skills/admin/permission-sets-vs-profiles` | `check_access_model.py` v1.2.1 (M2-T1): its `PSVP-DESC-01/02` rules, the `BLOCKING_SEVERITIES` exit policy, `--strict`, and check 2's raise to `HIGH` — the substance of F-16, F-17, F-22 and § 6.4's four controls |
| skill | `skills/admin/permission-set-architecture` | `check_permission_set_architecture.py` at build scope (§ 6.6); `PSA-DESC-02` and its ERROR-only exit policy in § 6.5 |
| skill | `skills/admin/permission-set-group-composition` | `check_permission_set_group_composition.py` at build scope; the `PSG_<persona>_<env>` convention the three PSGs adopt; `PSGC-DESC-02` and its `--strict` in § 6.5 |
| skill | `skills/admin/record-types-and-page-layouts` | `check_record_type_layouts.py` at build scope — F-01's closure (§ 3.3) and its boundary (F-19) |
| skill | `skills/admin/queues-and-public-groups` | `check_queues.py` at build scope; the `GroupMember`-does-not-deploy fact in § 4 and go/no-go 3 |
| skill | `skills/admin/custom-permissions` | `check_custom_permissions.py` at build scope; why `Consumers: 0` is the designed state at M2 |
| skill | `skills/admin/data-skew-and-sharing-performance` | `check_data_skew_and_sharing_performance.py` at build scope; the step-versus-build scope difference recorded against O-M2S04-04; SKILL.md:88's 10,000-record threshold behind § 8 line 7 |
| decision_tree | `standards/decision-trees/sharing-selection.md` | branch **Q3**, plan decision **D5** — cited by `M2-S05` and read to confirm § 10's mechanism table and that a restriction rule is not available on `Case` (Q8's eligible-object list) |

### Provenance of this report

Written by `agents/milestone-verifier/AGENT.md` (v1.0.0, `status: beta`, `requires_org: false`) on run
`2026-09-12T02-54-59Z`, superseding run `2026-09-12T02-10-00Z`. Every exit code in § 6 is from a command
run in this session from `.sfskills/builds/case-onboarding/`, captured under `tests/M2/` with a `.v2.`
suffix beside — never over — v1's captures. The four negative controls in § 6.4 ran against a copy of
`artefacts/` in the session scratchpad.

**Files this run wrote, and nothing else under the build directory changed:**

- `reports/MILESTONE-M2-REPORT-v2.md` (this file). **`reports/MILESTONE-M2-REPORT.md` was not touched.**
- `envelopes/M2/2026-09-12T02-54-59Z.json` and `.md`
- `tests/M2/*.v2.*` — 29 capture files: nine `{stdout, stderr, exit}` triples for the nine checker
  invocations, plus `manifest.v2.stdout.txt` and `cross-step-references.v2.stdout.txt`. The negative
  controls' captures stayed in the session scratchpad, because the trees they ran against did too.
- one `set-milestone` write to `plan.json` (§ 14)

`reports/MILESTONE-M2-package.xml` was **recomputed and deliberately not rewritten** (§ 5). No artefact,
no step's `results.json`, no workbook section, no `decisions.md` entry and no `traceability.md` row was
modified. No skill, agent, standard or script was edited. **No org was contacted and nothing was
deployed.**

**Deviation from the Wave 10 persistence default, recorded rather than silent:** the contract's default
pair is `docs/reports/milestone-verifier/<run_id>.{md,json}`. This run is build-scoped and persists to
`.sfskills/builds/case-onboarding/envelopes/M2/` instead — the path
`agents/milestone-verifier/AGENT.md` Step 11 and the envelope schema's build-layer pattern both
prescribe, and the path v1 and both M1 verification runs used. `docs/reports/milestone-verifier/` does
not exist in this repo, and the invocation scoped all writes to the build directory.
