# M2 — Access, work pools and Case visibility · acceptance report

| | |
|---|---|
| Build | `case-onboarding` (`plan.json` v5, status `building`, `build_mode: design-only`, no org on file) |
| Milestone | **M2** — "Access, work pools and Case visibility" |
| Steps | 5, all `documented`: `M2-S01`, `M2-S02`, `M2-S03`, `M2-S04`, `M2-S05` |
| Blocked steps | **none** |
| Verdict | **`not-ready`** — one declared milestone acceptance test exits 1 where the plan declares exit 0 (**F-16**) |
| Confidence | **MEDIUM** |
| Written by | `agents/milestone-verifier/AGENT.md`, run `2026-09-12T02-10-00Z` |
| Merged manifest | [`reports/MILESTONE-M2-package.xml`](./MILESTONE-M2-package.xml) — 7 types, 19 members, `<version>62.0</version>`, no conflict |
| Org-facing evidence | `reports/MOCK-DEPLOY-M2.md` **run 3** — 32 components, 0 errors, `checkOnly: true`, human-run |

> **Nothing in this run touched an org, and nothing was deployed.** The one org-facing check in this
> layer is `scripts/mock_deploy.py`, and a human ran it (§ 6.4). The G3 gate is the human's; this
> report ends with the command and does not run it.

---

## 0. Precondition checks (Step 1)

| Check | Result |
|---|---|
| Every step in M2 is `documented` | **yes** — 5 of 5. No step is `pending`, `running`, `built`, `tested`, `failed` or `blocked`, so no refusal applies |
| Preceding milestone's gate | `human_gates[milestone:M1].status` = **`approved`** (2026-09-09T20:30:32Z, dry-run operator) |
| `plan` gate | **`approved`** (2026-09-05T19:35:19Z) |
| Per-step `step:<id>` gates | all five approved — `M2-S01` … `M2-S05`; every M2 step carries `human_gate: true` |
| `plan.json` schema + semantics | `build_plan.py validate` → `OK … 5 milestone(s), 22 step(s), 3 warning(s)`. All three WARNs are on **M5** steps (non-standard checker argument forms); none is in M2 |
| Declared outputs on disk | `check-outputs` → `{"ok": true, "missing": [], "empty": [], "malformed": []}` on all five steps |

M1's status field reads `verified` rather than `accepted` — that is the **F-12** artefact recorded in
`MILESTONE-M1-REPORT-v2.md` § 10.3, and the gate record itself still says `approved`, which is the
record that governs. **F-12 is now CLOSED at the tooling** (§ 7, F-12 row): `scripts/build_plan.py`
lines 2182–2196 carry the guard it asked for.

---

## 1. The milestone and its artefacts

Five `access`-type steps, all owned by `metadata-builder` (org-free, as `build_mode: design-only`
requires). 24 XML files, all parsing; 19 deployable members.

### M2-S01 — Intake bypass Custom Permission and the integration permission set that carries it
`depends_on: []`

- `customPermissions/Bypass_Case_Intake_Validation.customPermission-meta.xml`
- `permissionsets/Case_Intake_Integration.permissionset-meta.xml`
- `package.xml`, `deploy-order.md` *(declared in `outputs[]` at plan time — the only M2 step for which that is true without an amendment)*

### M2-S02 — Permission sets and permission set groups for Tier 1, Tier 2 and Billing
`depends_on: [M1-S01]` · rebuilt once (F-15)

- `permissionsets/` — `Case_Agent_Core`, `Case_Tier1`, `Case_Tier2`, `Case_Billing`
- `permissionsetgroups/` — `PSG_Tier1_Prod`, `PSG_Tier2_Prod`, `PSG_Billing_Prod`
- `package.xml` · `deploy-order.md` **produced but not declared** (O-M2S02-01)

### M2-S03 — Minimal base profiles carrying only default app, default record type and layout assignment
`depends_on: [M1-S02, M2-S02]` · rebuilt once (F-15) · 1 amendment

- `profiles/` — `Acme Support Tier 1`, `Acme Support Tier 2`, `Acme Billing`
- `package.xml`, `deploy-order.md` *(declared by the 2026-09-12T00:38:44Z amendment)*

**This is the step that closes M1's F-01.** See § 3.2.

### M2-S04 — Case queues and public groups for Tier 1 General, Tier 2 and Billing
`depends_on: [M2-S02]` · 1 amendment

- `queues/` — `Tier_1_General`, `Tier_2_Engineering`, `Billing`
- `groups/` — `Support_Tier_1`, `Support_Tier_2`, `Billing_Team`
- `queue-retirement-runbook.md`, `package.xml`, `deploy-order.md`

### M2-S05 — Case org-wide default Private plus the criteria-based sharing rule that opens Support cases to Tier 2
`depends_on: [M1-S01, M2-S04]` · 1 amendment · decision tree `standards/decision-trees/sharing-selection.md`

- `sharingRules/Case.sharingRules-meta.xml` — one `sharingCriteriaRules` block, `Support_Cases_To_Tier_2`
- `case-visibility-model.md`, `package.xml`, `deploy-order.md`

---

## 2. Symbol inventory (Step 2)

M1 is accepted, so its symbols count as defining. M3–M5 do not.

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
**resolved-standard-object**, not unresolved. No role exists anywhere in this build — deliberately,
per `case-visibility-model.md` § "Layers deliberately not used" (no role developer name appears in
`requirement.md`, in any of the 97 clarifications, or in an upstream artefact).

---

## 3. Reference resolution (Step 3)

**48 references over M2's 13 metadata files. 0 unresolved. 1 unclassifiable.** Raw capture:
`tests/M2/cross-step-references.stdout.txt`.

### 3.1 Which reference classes were resolved — and the boundary of the check

| Reference class | Read from | Resolves against | Count | Result |
|---|---|---|---|---|
| Permission-set / profile field grants | `<field>` under `<fieldPermissions>` | field inventory | 5 | all resolved (M1-S01) |
| Permission-set object grants | `<object>` under `<objectPermissions>` | object inventory | 5 | 1 resolved (M1-S01) + 4 standard |
| Record-type visibility | `<recordType>` under `<recordTypeVisibilities>` | record-type inventory | 9 | all resolved (M1-S01) |
| Layout assignment — layout | `<layout>` under `<layoutAssignments>` | layout inventory | 9 | all resolved (M1-S02) |
| Layout assignment — record type | `<recordType>` under `<layoutAssignments>` | record-type inventory | 6 | all resolved (M1-S01) |
| Custom-permission grant | `<name>` under `<customPermissions>` | custom-permission inventory | 1 | resolved (M2-S01) |
| PSG membership | `<permissionSets>` | permission-set inventory | 6 | all resolved (M2-S02) |
| Queue membership — public group | `<queueMembers>/<publicGroups>/<publicGroup>` | group inventory | 3 | all resolved (M2-S04) |
| Queue supported object | `<queueSobject>/<sobjectType>` | object inventory | 3 | all resolved (M1-S01) |
| Sharing rule — `sharedTo` | `<sharedTo>/<group>` | group inventory | 1 | resolved (M2-S04) |
| **Sharing-rule criteria value** | `<criteriaItems>/<value>` | record-type inventory | 1 | **unclassifiable** — see below |

**Not checked by anything in this milestone,** stated so a reader does not infer completeness from
silence: validation-rule field tokens, assignment-rule criteria, Flow field references, entitlement
milestones and path steps. None exists in the build yet (M3 and M4 are `pending`); the milestone's
reference classes above are the ones M2's artefacts actually make.

### 3.2 The five cross-step checks the gate asked for, answered directly

1. **Every permission set named by a PSG exists.** `PSG_Tier1_Prod` → `Case_Agent_Core` + `Case_Tier1`;
   `PSG_Tier2_Prod` → `Case_Agent_Core` + `Case_Tier2`; `PSG_Billing_Prod` → `Case_Agent_Core` +
   `Case_Billing`. All six references resolve to `M2-S02` files. `check_permission_set_group_composition.py`
   at build scope independently reports `GOOD: reuse: permission set 'Case_Agent_Core' is referenced by
   3 PSGs`. **PASS.**

2. **Every profile `recordTypeVisibilities` and `layoutAssignments` resolves to an M1 record type and
   layout.** 9 record-type references → `Case.Support` / `Case.Billing` (`M1-S01`); 9 layout references
   → `Case-Case Support Layout` / `Case-Case Billing Layout` (`M1-S02`); 6 record types inside those
   layout assignments likewise. **PASS — and this is what closes F-01.**

   `python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts`
   — exit **0**:

   ```json
   {
     "score": 100,
     "findings": [],
     "summary": "Scanned 15 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s) detected."
   }
   ```

   The same command with `--strict` (the form `M2-S03` declares) is identical. The comparison with
   `MILESTONE-M1-REPORT-v2.md` § 10.1 is the point: there the build-scope run printed
   `8 metadata file(s)` and resolved **zero** `layoutAssignments`, because `collect()` reads them only
   from `Profile` and `PermissionSet` roots and no `Profile` existed. **`M2-S03`'s three profiles are
   that missing root.** F-01's stale pointer to `M2-S01` in the v1 report and in two gate notes is moot:
   the finding it pointed at is closed, so there is nothing left to re-point.

   **Negative control, so the green is earned rather than quiet.** A copy of the tree in the session
   scratchpad (never the build directory) with `Acme Support Tier 1`'s layout assignment rewritten to
   `Case-Ghost Layout` / `Case.Nonexistent`:

   ```text
   LOW  layoutAssignment names layout 'Case-Ghost Layout' which is not in the scanned tree
        - confirm it exists in the target org
   exit 0 without --strict; exit 1 with --strict
   ```

   The checker names the injected layout, so the assertion is live at this scope rather than vacuous.
   A second control found the boundary — see **F-19**.

3. **Every public group a queue names exists in M2-S04.** `Tier_1_General` → `Support_Tier_1`;
   `Tier_2_Engineering` → `Support_Tier_2`; `Billing` → `Billing_Team`. All three resolve to
   `M2-S04/groups/`. No `<users>` element appears in any queue or group file, so no named user is
   hard-coded (Q29). **PASS.**

4. **The sharing rule's `sharedTo` group exists.** `Support_Cases_To_Tier_2` → `<group>Support_Tier_2</group>`
   → `artefacts/M2-S04/groups/Support_Tier_2.group-meta.xml`. **PASS** — but see **F-20** on where the
   recorded deploy positions put the two relative to each other.

5. **Every `<description>` is ≤ 255 characters (the F-15 rule).** Measured over all 26 description
   elements in M1 + M2. **PASS on the platform limit — the maximum is 250.** The distribution is what
   matters for **F-16**:

   | Range | Files |
   |---|---|
   | 246–255 (at risk) | none |
   | 201–250 | `CustomPermission Bypass_Case_Intake_Validation` 250 · **`PermissionSet Case_Intake_Integration` 244** · `Group Support_Tier_1` 229 · `Group Support_Tier_2` 220 |
   | ≤ 200 | the other 22, including all four `M2-S02` permission sets (183–199) and all three `M2-S03` profiles (147–152) after the F-15 rebuild |

   F-15 is closed on the **platform** fact everywhere. It is not closed on the **200-character
   headroom** the three access skills added alongside it, and `M2-S01` is the step that was never
   rebuilt — it was built 2026-09-06, five days before the rule existed. That is F-16.

### 3.3 The one unclassifiable reference

`artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml` →
`<criteriaItems><field>RecordTypeId</field><operation>equals</operation><value>Support</value>`.

The value is a record-type reference in bare developer-name form, which grep resolution cannot
distinguish from a literal string: `RecordTypeId` on a criteria item may take a developer name or an
18-character Id, and the Metadata API guide establishes neither (`M2-S05/deploy-order.md` Decision 3
carries the UNVERIFIED marker verbatim). Reported as unclassifiable rather than counted as resolved.
**It is nonetheless the best-evidenced item in this milestone:** `reports/MOCK-DEPLOY-M2.md` run 3
validated `SharingCriteriaRule Case.Support_Cases_To_Tier_2` with this exact value, against
`sfskills-dev`. The builder named it "the single most likely thing in this step to come back from a
mock deploy"; it did not come back.

---

## 4. Deployment order (Step 4)

Canonical sequence: objects (1) → fields (2) → picklists (3) → record types (4) → layouts (5) →
**permission sets (6)** → **sharing (7)** → automation (8) → **routing (9)** → SLA (10).

| Artefact | Type | Recorded position | Agrees with the artefact's own type? |
|---|---|---|---|
| `Bypass_Case_Intake_Validation` | CustomPermission | 6 (permission sets), pos 1 in step | yes — no slot of its own; must precede the set that grants it |
| `Case_Intake_Integration` | PermissionSet | 6, pos 2 in step | yes |
| `Case_Agent_Core`, `Case_Tier1`, `Case_Tier2`, `Case_Billing` | PermissionSet | 6 | yes |
| `PSG_Tier1_Prod`, `PSG_Tier2_Prod`, `PSG_Billing_Prod` | PermissionSetGroup | 6, after all four sets | yes — composition-only |
| `Acme Support Tier 1 / Tier 2 / Billing` | Profile | 6 (the access layer) | yes |
| `Case` | SharingRules | 7 (sharing) | yes by type — **but see the backwards dependency below** |
| `Support_Tier_1`, `Support_Tier_2`, `Billing_Team` | Group | 9 (routing), groups before queues | by type a Group has no slot; filed with the queues it feeds |
| `Tier_1_General`, `Tier_2_Engineering`, `Billing` | Queue | 9, after all three groups | yes |

**No artefact's recorded position contradicts its own type.** The ordering constraints that matter
are satisfied inside the milestone and across it:

- *Permission sets after the objects and fields they grant* — `skills/devops/permission-set-deployment-ordering`'s
  case. `Case_Agent_Core` carries `fieldPermissions` for `Case.Severity__c`, `Account.Region__c` and
  `Account.Support_Tier__c`, all `M1-S01` (position 2) and all already accepted. No `fieldPermissions`
  entry names a field this build defines later. **No violation.**
- *Profiles after the record types and layouts they assign* — `M2-S03` `depends_on: [M1-S02, M2-S02]`,
  and positions 4 and 5 precede 6. **No violation.**
- *Automation before the routing it triggers* — `skills/devops/flow-deployment-activation-ordering`'s
  case. **Not applicable to M2:** it contains no Flow, no Apex and no active-state artefact. The
  milestone's own `type` for all five steps is `access`.

### One backwards dependency (F-20)

`SharingRules:Case` sits at **7** and references `Support_Tier_2`, a `Group` filed at **9**. Read as a
staged sequence, the rule deploys two positions before the group it shares to, and a `sharedTo` naming
an absent group is a deploy failure (`M2-S05/deploy-order.md` marks the exact platform behaviour
UNVERIFIED and takes the conservative reading: "ship the group in the same package rather than testing
the assumption in production").

Three things keep this off the blocking list:

1. The **step** order is right: `M2-S05 depends_on [M1-S01, M2-S04]`, so `M2-S04` is `documented`
   before `M2-S05` runs.
2. The artefact says so itself. `M2-S05/deploy-order.md` § "Dependencies on components OUTSIDE this
   step" row 3 names `Support_Tier_2.group-meta.xml` / **M2-S04**, and its validate-only command reads
   "Deploy M1-S01 and M2-S04 first, or include them in the same request."
3. The org agrees. Mock deploy run 3 sent all seven steps as one request and validated 32 of 32.

So it is a contradiction in the ten-position bookkeeping, not in the build — and it is live for anyone
who stages a deploy by position rather than by the step graph.

### The post-deploy step without which none of this grants anybody anything

Not an ordering finding, but it belongs beside one. **`GroupMember` rows do not deploy.** The Metadata
API guide, quoted in `M2-S05/deploy-order.md`: "Members of the public group aren't migrated when you
deploy the group type." All three groups deploy empty; the sharing rule and all three queues then show
active in Setup and grant nobody anything until the rosters are loaded as data. Owner: CRM admin lead;
tracked in `artefacts/M2-S04/queue-retirement-runbook.md` § 6. `check_data_skew_and_sharing_performance.py`
reports the same fact as a WARN at step scope. **A green deploy of M2 is not a working access model.**

---

## 5. Merged manifest (Step 5)

**`reports/MILESTONE-M2-package.xml`** — written this run by merging the five step manifests: members
unioned per type, members sorted inside each `<types>` block, `<types>` blocks sorted by type name, one
`<version>`.

| Type | Members | From |
|---|---|---|
| `CustomPermission` | 1 — `Bypass_Case_Intake_Validation` | M2-S01 |
| `Group` | 3 — `Billing_Team`, `Support_Tier_1`, `Support_Tier_2` | M2-S04 |
| `PermissionSet` | 5 — `Case_Agent_Core`, `Case_Billing`, `Case_Intake_Integration`, `Case_Tier1`, `Case_Tier2` | M2-S01 (1) + M2-S02 (4) |
| `PermissionSetGroup` | 3 — `PSG_Billing_Prod`, `PSG_Tier1_Prod`, `PSG_Tier2_Prod` | M2-S02 |
| `Profile` | 3 — `Acme Billing`, `Acme Support Tier 1`, `Acme Support Tier 2` | M2-S03 |
| `Queue` | 3 — `Billing`, `Tier_1_General`, `Tier_2_Engineering` | M2-S04 |
| `SharingRules` | 1 — `Case` | M2-S05 |
| **Total** | **7 types, 19 members** | |

- **API version: no conflict.** All five step manifests declare `62.0`, as do both M1 manifests. Carried
  through as the single `<version>62.0</version>`. (`plan.json` still has no `api_version` key — this is
  now the eighth agent-side default. **F-06**, open.)
- **Member collisions inside M2: none.** No `type:member` pair appears in two steps. The `PermissionSet`
  block is the only one two steps contribute to, and their five members are disjoint.
- **Member collisions against M1: none.** No `type:member` pair appears in both milestones.
- **One member name reused across two types, which is not a collision:** `Case` appears as
  `CustomObject:Case` (M1-S01) and as `SharingRules:Case` (M2-S05). These address different components
  and coexist in one manifest.
- **Files under the milestone's artefacts reaching no `<types>` block: 12,** and all 12 are correct —
  five `package.xml` (the manifests themselves), five `deploy-order.md`, `queue-retirement-runbook.md`
  and `case-visibility-model.md`. No source-format metadata file is missing from the manifest.

### The `SharingRules:Case` container form, recorded rather than smoothed over

The manifest addresses the **container** (`<name>SharingRules</name>`, member `Case`).
`skills/admin/sharing-and-visibility/references/metadata-examples.md` § 6 prescribes the **rule-type**
form instead — `<name>SharingCriteriaRule</name>`, member `Case.Support_Cases_To_Tier_2` — and says
`SharingRules` "is not what you address". Two other skills in the library
(`admin/experience-cloud-guest-access`, `admin/data-skew-and-sharing-performance`) manifest the
container form. The container form is here for a mechanical reason the step records: the `manifest`
test derives the member from the file stem (`Case.sharingRules-meta.xml` → `SharingRules`:`Case`), so
the rule-type form would leave the file uncovered *and* declare a member with no file of its own.

**Both forms deploy the same file, and mock deploy run 3 was source-mode** — `--source-dir`, so the CLI
derived components from the tree and never opened a `package.xml`. **The container form in this merged
manifest has not been read by a deploy.** That is the same shape as F-13, one metadata type over, and it
is why § 8's optional command is worth running in `--mode manifest`.

### F-18 — the M1 merged manifest beside this one is stale

`reports/MILESTONE-M1-package.xml` still declares the **bare** member `Case_Intake` under
`CompactLayout` — the exact form mock deploy #3 rejected with *"An object 'Case_Intake' of type
CompactLayout was named in package.xml, but was not found in zipped directory"*.
`artefacts/M1-S01/package.xml` was rebuilt to the object-qualified `Case.Case_Intake` (rebuild #3,
mtime 2026-09-11 20:12); the merged M1 manifest was last written 2026-09-09 16:16 and never regenerated.

Mock deploy #4 does not discharge it. It reports "merged manifest read by the CLI", and the manifest it
read was merged **on the fly from the step files**, not this one: `scripts/mock_deploy.py`'s
`resolve_manifest_text()` reads `reports/MILESTONE-<id>-package.xml` only when exactly one
`--milestone` is named and no `--step` is mixed in, and run #4 passed `--step M1-S01 --step M1-S02`. So
**F-13 is closed in the step manifest and still open in the committed merged one.**

`MILESTONE-M2-package.xml` carries no `CompactLayout` member and is unaffected. **A human merging M1
and M2 into one manifest must take `Case.Case_Intake`, not `Case_Intake`.** Not fixed here: this agent
verifies one milestone per invocation, and M1's manifest is M1's verification run's to regenerate.

---

## 6. Acceptance-test results (Step 6)

M2 declares **4** acceptance tests. Three are executable; one is `manual` and goes to § 7. Raw captures
under `tests/M2/`. Every command was run **verbatim, from the build directory**, which carries the
`skills` symlink, exactly as `standards/build-orchestration.md` § 5 requires.

### 6.1 `M2-T1` · checker · **FAIL**

```bash
python3 skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py --manifest-dir artefacts
```

**Declared:** `exit 0`. **Actual: exit 1.**

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
  "summary": "Scanned 11 access-model metadata file(s); 1 finding(s) detected."
}
```
```text
stderr: WARN: 1 finding(s) detected
```

This is **F-16**, in full in § 7. What the test was declared to prove — "no dangerous system
permission, no migratable permission left on a profile" — **holds**: the finding is neither. The exit
code fails on a length-headroom WARN, because the checker's `main()` ends
`return 1 if normalized else 0` (line 177), so every severity including WARN exits 1.

Captures: `tests/M2/check_access_model.{stdout,stderr,exit}.txt`.

### 6.2 `M2-T2` · checker · **PASS**

```bash
python3 skills/admin/sharing-and-visibility/scripts/check_sharing_model.py --manifest-dir artefacts
```

**Declared:** `exit 0`. **Actual: exit 0.**

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
widened to build scope (B01). This run also discharges the "has not run" sentence that `M1-S01`'s
`CWB-SHARE-001` and `REQ-010` still carry — the correction is recorded in `decisions.md` **O-M2S05-02**,
and neither row is this run's to rewrite.

Captures: `tests/M2/check_sharing_model.{stdout,stderr,exit}.txt`.

### 6.3 `M2-T3` · manifest · **PASS (consistent)**

Two-way over the merged manifest and the milestone's 13 metadata files.

- **File → manifest:** all 19 derived `type:member` pairs appear. 0 missing.
- **Manifest → file:** all 19 named members have a file. 0 orphans.
- Files reaching no `<types>` block: the 12 documentation and manifest files listed in § 5.

Capture: `tests/M2/manifest.stdout.txt`.

### 6.4 The org-facing evidence § 5 now names — human-run, before G3

`standards/build-orchestration.md` § 5 names `scripts/mock_deploy.py` as the validation a human runs
after a milestone verifies and before the G3 decision. It has been run three times for M2
(`reports/MOCK-DEPLOY-M2.md`), and **run 3 is the evidence for this gate**:

```bash
python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev \
  --step M1-S01 --step M1-S02 --step M2-S01 --step M2-S02 --step M2-S03 --step M2-S04 --step M2-S05
```

**Succeeded — 32 components, 0 errors, `checkOnly: true`.** Every artefact of milestones 1 and 2
validates unmodified, including the sharing rule's bare `Support` criteria value. Runs 1–2 are the
F-15 history: run 1 failed 10 of 30 on `Description: data value too large … (max length=255)` across
four permission sets and three profiles; the three access skills gained the DESC rules (4da8e6c92);
`M2-S02` and `M2-S03` were rebuilt; run 2 validated 30 of 30. **This is what makes F-16 a
checker-version drift rather than a deployability problem** — the org accepts the 244-character
description that fails `M2-T1`.

Two limits on that evidence, stated so it is not over-read: all three runs were `--mode source`, so no
`package.xml` was opened (§ 5, F-18); and `checkOnly: true` validates metadata, not access — no user
was assigned, no `GroupMember` row loaded, no record read.

### 6.5 Observation runs — not declared tests, and they gated nothing

Five checkers run at build scope because the gate should see what they say about M2 as a whole. None is
in `M2.acceptance_tests[]`; none contributed to any pass verdict. Captures:
`tests/M2/OBSERVATION-*.{stdout,stderr,exit}.txt`.

| Checker at `--manifest-dir artefacts` | Exit | What it said |
|---|---|---|
| `check_custom_permissions.py` | **0** | `Custom permissions defined: 1 / Permission sets / profiles parsed: 8 / Distinct permissions referenced: 0`; coverage row `Bypass_Case_Intake_Validation  0  permission set 'Case_Intake_Integration'`; `0 error(s), 0 warning(s), 0 info`. The grant is not dangling. **`Consumers: 0` is the designed state at M2** — the consumers are M3-S01's validation rules |
| `check_permission_set_architecture.py` | **0** | one line: `WARN: PSA-DESC-02 … Case_Intake_Integration … 244 characters`. **Same file, same fact as M2-T1, and this checker exits 0 on it** |
| `check_permission_set_group_composition.py` | **0** | `GOOD: reuse: permission set 'Case_Agent_Core' is referenced by 3 PSGs`; `1 good, 0 error, 1 warn, 0 info, scanned 3 PSG file(s)`. The warn is `PSGC-DESC-02` on the same 244-character description |
| `check_queues.py` | **0** | all three queues with `Objects : Case`, all three groups, `Warnings found (2)` — `Tier 1 General` **and** `Tier 2 Engineering` have no `<email>`. Confirms O-M2S04-01: the step test's description predicts `(1)` |
| `check_data_skew_and_sharing_performance.py` | **0** | `No data skew or sharing performance issues found.` At build scope the groups are referenced by a queue and by the sharing rule, so the three "used but unmigrated" WARNs O-M2S04-04 recorded at step scope do not fire here. Record counts were skipped: skew is data, and no `--skew-plan` exists in a design-only build |

**Three checkers, one description, three different exit policies.** That is **F-17**, and it is the
whole of why M2-T1 fails while two checkers looking at the same string pass.

---

## 7. Findings

New in this run: **F-16 … F-21**. Carried from M1: **F-01** and **F-12** now close; F-02 … F-08 are
restated only where M2 changes their status.

### F-16 · HIGH · **BLOCKING the verdict** — M2's own acceptance test exits 1 on a description-length WARN

*`check_access_model.py --manifest-dir artefacts` exits 1 where `M2.acceptance_tests[0].expected` says
`exit 0`.*

**The fact.** `artefacts/M2-S01/permissionsets/Case_Intake_Integration.permissionset-meta.xml` carries a
244-character `<description>`. `admin/permission-sets-vs-profiles` v1.2.0 added `PSVP-DESC-01` (ERROR
> 255) and `PSVP-DESC-02` (WARN > 200), and the checker exits 1 on any finding.

**Why it is red now and was green then.** `M2-S01` was built and tested on **2026-09-06**. The DESC
rules landed on **2026-09-11** in commit `4da8e6c92`, to close F-15. That fix rebuilt `M2-S02`
(descriptions 419 → 192, 290 → 193, 456 → 199, 380 → 183) and `M2-S03` (280 → 152, 279 → 152, 407 → 147)
and **did not rebuild `M2-S01`**, which was already `documented` and had passed. `tests/M2-S01/check_access_model.exit.txt`
records `0`; re-running the identical step-scoped command today gives **exit 1** with the same WARN.
Nothing about the artefact changed. The checker moved under a finished step.

**What it is not.** Not a deployability problem: 244 < 255, and mock deploy run 3 validated this exact
file among 32 components with 0 errors. Not a security or access finding: `M2-T1`'s declared assertion
— no dangerous system permission, no migratable permission on a profile — holds, and the only finding
is a length WARN. `MOCK-DEPLOY-M2.md` already noted this file "passed by luck" at run 1.

**Deploy-time error it predicts,** per `skills/devops/deployment-error-diagnosis`: **none.** This
finding has no deploy-time consequence at all. Its consequence is inside the build: a declared
acceptance test does not pass, so the milestone cannot be recommended `ready-for-gate`.

**Remedies, either one closes it.**
- **(a) Rebuild `M2-S01`.** `set-status M2-S01 running --reason "F-16: trim description under the
  200-char PSVP-DESC-02 headroom"` → `metadata-builder` trims the `<description>` (and the 250-character
  `CustomPermission` one, which no checker reads today but is one word from 255) → tester → doc keeper →
  re-run `/verify-milestone`. The `documented → running` rebuild path exists for exactly this ("a
  finding that reached it late — a milestone report, a mock deploy, a skill fix", § 4), and `M2-S01`'s
  `step:M2-S01` gate is already approved so the rebuild does not reach around it.
- **(b) The planner accepts the WARN** and restates `M2.acceptance_tests[0].expected` to what a
  headroom WARN should mean at milestone scope. That is a v6 decision about whether a 200-character
  advisory should be able to fail a milestone, and it is not this agent's to make.

Remedy (a) is the smaller change and leaves the test's exit code meaning what it says.

---

### F-17 · MEDIUM · The three DESC-rule checkers disagree on whether a WARN exits non-zero

Three checkers read the same 244-character description in this run. Same file, same fact, three
different exit codes:

| Checker | Rule | Exit on this WARN |
|---|---|---|
| `permission-sets-vs-profiles/scripts/check_access_model.py` | `PSVP-DESC-02` | **1** (`return 1 if normalized else 0`, line 177) |
| `permission-set-architecture/scripts/check_permission_set_architecture.py` | `PSA-DESC-02` | **0** |
| `permission-set-group-composition/scripts/check_permission_set_group_composition.py` | `PSGC-DESC-02` | **0** |

So whether a description-length advisory can fail a milestone depends on which of three checkers the
plan happened to declare — not on anything about the artefact. The three rules were added in one change
to close one finding; their exit policies were not aligned in that change. F-16 is the first time it has
mattered. **Fix owner:** the three skills, in one change, deciding once whether a WARN is exit-worthy.
Worth noting that `check_permission_set_group_composition.py` was rebuilt this session precisely to make
naming-convention violations WARN-and-exit-0 (O-M2S02-01 narrative), so two of the three already agree.

---

### F-18 · MEDIUM · `reports/MILESTONE-M1-package.xml` is stale; F-13's fix never reached it

Full statement in § 5. Summary: the committed merged M1 manifest still carries the bare `CompactLayout`
member `Case_Intake` that mock deploy #3 rejected by name; `artefacts/M1-S01/package.xml` carries the
corrected `Case.Case_Intake`; mock deploy #4's manifest-mode success read an on-the-fly merge of the
step files, not this file (`mock_deploy.py:resolve_manifest_text` takes the report only when a single
`--milestone` is named with no `--step`). **Deploy-time error it predicts:** `An object 'Case_Intake' of
type CompactLayout was named in package.xml, but was not found in zipped directory` — already observed
once, on this exact member. Remedy: regenerate `MILESTONE-M1-package.xml` on M1's next verification, or
a human takes `Case.Case_Intake` when merging M1+M2 by hand. Not fixed here (one milestone per
invocation).

---

### F-19 · MEDIUM · `check_record_type_layouts.py` resolves the layout half of a profile reference and not the record-type half

Second negative control, same scratchpad copy, `Acme Support Tier 2`'s `recordTypeVisibilities`
rewritten from `Case.Billing` to **`Case.Ghost`** — a record type that exists nowhere:

```json
{ "score": 100, "findings": [], "summary": "Scanned 15 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s) detected." }
```
```text
exit 0 — identical with and without --strict
```

A dangling `layoutAssignments/layout` fires a LOW and exits 1 under `--strict` (§ 3.2); a dangling
`recordTypeVisibilities/recordType` fires nothing at any scope.

**Nothing is wrong in this build** — all 9 `recordTypeVisibilities` references resolve, proven
independently in § 3 rather than by this exit code. What is wrong is what the exit code is claimed to
carry. `steps[M2-S03].acceptance_tests[1].description` says the run resolves "any `Profile`-sourced
record-type reference (12)", and `traceability.md` `REQ-026` repeats it; `decisions.md` D-M2S03-07
sources F-01's closure to the same run. The layout half of that claim is earned. The record-type half is
not asserted by the checker.

**Deploy-time error a dangling one would produce:** `INVALID_CROSS_REFERENCE_KEY` on the Profile
component — the same error class F-01 predicted for the layout half. **Remedy:** add the
record-type-resolution rule to `admin/record-types-and-page-layouts`' checker, then narrow the test
description to what it proves until that lands.

---

### F-20 · LOW · The recorded deploy positions put the sharing rule ahead of the group it shares to

Full statement in § 4. `SharingRules:Case` at position 7 references `Support_Tier_2`, a `Group` filed at
position 9. Mitigated three ways (step graph, the step's own `deploy-order.md`, and mock run 3's single
atomic request) and live only for a human staging by position. **Remedy at v6:** record the group at the
access layer alongside the permission sets it is peer to, or annotate position 9 with "groups must
precede position 7's sharing rule".

---

### F-21 · LOW · F-08 is closed across all five M2 steps and still open on both M1 steps

`MILESTONE-M1-REPORT-v2.md` F-08: both M1 `deploy-order.md` files print the production-only
`sf project deploy validate` against an alias the same line calls a sandbox. **Unchanged** —
`artefacts/M1-S01/deploy-order.md:141` and `artefacts/M1-S02/deploy-order.md:135` still read
`sf project deploy validate --target-org <your-sandbox-alias>`.

**All five M2 steps get it right.** M2-S01 emits `deploy start --dry-run` for the sandbox and a separate
`deploy validate --target-org <your-production-alias> --test-level RunLocalTests` for production; the
other four emit `deploy start --dry-run` only. So `metadata-builder` applies the correct form to new
work, and F-08's residue is confined to two files that predate it. Fix owner: `metadata-builder`, on
M1's next rebuild. Not fixed here — this agent does not edit artefacts other agents wrote.

---

### Findings carried from M1 that change status in this run

| id | Was | Now | Why |
|---|---|---|---|
| **F-01** · HIGH | open — "the record-type ↔ layout binding is asserted nowhere" | **CLOSED** | `M2-S03`'s three Profiles are the `layoutAssignments` root `collect()` needed. `check_record_type_layouts.py --manifest-dir artefacts` → `Scanned 15 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s) detected.`, exit 0, and a negative fixture naming a ghost layout is caught (§ 3.2). The stale `M2-S01` pointer in the v1 report and in the `milestone:M1` / `step:M2-S01` gate notes is **moot**, not re-pointed — per `decisions.md` O-M2S01-01's own conclusion. **Partial:** the record-type half of the same assertion is F-19 |
| **F-12** · MEDIUM | new — `set-milestone` overwrote an `accepted` milestone with no guard | **CLOSED at the tooling** | `scripts/build_plan.py` lines 2182–2196 now carry the guard it asked for: an `accepted` milestone keeps its status, the verdict is appended to `reverifications[]`, and the CLI prints the `gate … reject` line as the only way to withdraw a human's G3. M2 is `building`, so this run writes the status directly and the guard is not exercised |
| **F-13** · MEDIUM | new — merged manifest never read by a deploy; `CompactLayout` member form disputed | **CLOSED in the step manifest, OPEN in the merged one** | See **F-18** |
| **F-15** · HIGH | new (mock deploy M2 run 1) | **CLOSED on the 255-char platform limit; the 200-char headroom is F-16** | Max description in M1+M2 is 250; runs 2 and 3 validate at 30/30 and 32/32. `M2-S01` was never rebuilt under the new headroom rule |
| **F-02** · INFO | open by design | unchanged | `CaseStatus` value resolution is a per-target-org precondition; run 3 discharges it on `sfskills-dev` only |
| **F-04** · MEDIUM | `deploy-order.md` undeclared | **improved, not closed** | See § 9's declaration table: 4 of 5 M2 steps now declare it; `M2-S02` and both M1 steps do not |
| **F-06** · INFO | API version defaulted | **defaulted an eighth time** | All seven step manifests and the two merged ones read `62.0`; `plan.json` still carries no `api_version` |
| **F-03 / F-05 / F-07 / F-08 / F-09 / F-10 / F-11 / F-14** | — | unchanged by M2 | F-08's M2 half is **F-21**. F-03 and F-11's planner half wait on M3-S01 and a v6 re-plan |

---

## 8. Manual checklist for the human (Step 7)

Six lines: five deferred by the step testers (`skipped_manual[]`) plus M2's own milestone manual test.
Each names its origin, what the human does, and what counts as a tick. **Where a tester gathered
file-checkable evidence it is quoted — that narrows a line, it never ticks it.** No agent in this loop
ticks any of these.

### ☐ 1 — M2 (milestone) · No named user is hard-coded, and the Billing visibility reading is the one you want

**From:** `M2.acceptance_tests[3]` (`manual`). **Who:** the support manager **and** the admin lead,
jointly. **Ticks when** both halves hold.

*Half one — no hard-coded user.* **Evidence gathered this run:** no `<users>` element appears in any of
the three queue files or the three group files. Queue membership is expressed only as
`<queueMembers><publicGroups><publicGroup>`, naming `Support_Tier_1`, `Support_Tier_2` and
`Billing_Team`. `check_queues.py` lists all three groups with `Members : (no members listed)`.
**Verifiable from disk; the two named humans still have to accept it as the design.**

*Half two — the A1 reading.* **Not evidenceable from any artefact, and it is the real content of this
line.** Q13 ("is the Billing restriction record-level or field-level?") was **deferred**. Assumption
**A1** (`risk: high`) takes the record-level reading: a Tier 1 agent cannot open a Billing case at all,
rather than opening it with a field hidden. Every access artefact in this milestone is shaped by that
reading. D5's stated consequence if it is wrong: **`M2-S05` is re-planned, not patched** — the OWD may
relax, the rule set changes, and FLS on the Billing fields becomes the mechanism. **Ticking this line is
accepting A1.**

### ☐ 2 — `M2-S01` · The integration permission set grants the bypass and nothing else

**From:** `tests/M2-S01/results.json` → `skipped_manual[0]` (plan-verifier B01, rewritten as an
assertion over artefacts because `PermissionSetAssignment` is record data, not metadata).

**Evidence gathered by the tester** (`tests/M2-S01/manual-evidence.stdout.txt`, re-read this run):

```text
Top-level child elements (4): <label> <description> <hasActivationRequired> <customPermissions>
absent  <objectPermissions> <fieldPermissions> <userPermissions> <classAccesses> <pageAccesses>
        <recordTypeVisibilities> <tabSettings> <applicationVisibilities> <flowAccesses>
        <customSettingAccesses> <customMetadataTypeAccesses> <externalDataSourceAccesses>
        <externalCredentialPrincipalAccesses>
PRESENT x1  <customPermissions>  -> Bypass_Case_Intake_Validation = true
ASSERTION 'grants the bypass and nothing else': HOLDS
deploy-order.md post-deploy assignment instruction: PRESENT
deploy-order.md named owner for that assignment: PRESENT ("Security architect")
```

**Ticks when** a human accepts that reading. **The residue is not evidenceable in this build at all:**
whether the set is assigned to the integration identity and to **no human user** is
`PermissionSetAssignment` data in a target org. Two recorded absences to see while here: `ApiEnabled` is
deliberately **not** granted (`decisions.md` D-M2S01-02) and the grant carries **no expiry** (D-M2S01-03).

### ☐ 3 — `M2-S04` · All six components are present, named, and every queue supports Case

**From:** `tests/M2-S04/results.json` → `skipped_manual[0]`.
**Tester's evidence: PASS** — all six files present under `artefacts/M2-S04/queues/` and
`.../groups/`; all three queue files carry `<queueSobject><sobjectType>Case</sobjectType></queueSobject>`
(Q30). Independently re-confirmed this run by `check_queues.py` (`Objects : Case` on all three) and by
the manifest test (6 members ↔ 6 files). **Ticks on acceptance of the listing.**

### ☐ 4 — `M2-S04` · The per-queue email posture (Q88) — **one criterion does not hold; adjudicate, do not tick blind**

**From:** `tests/M2-S04/results.json` → `skipped_manual[1]` (W02 1 of 3).
**Tester's evidence: PARTIAL MISMATCH.**

| Criterion | Artefact | Holds? |
|---|---|---|
| `Tier_1_General` carries no `<email>` (Omni-Channel push, not email) | no `<email>` element | **yes** |
| `Billing` carries the billing@ queue address | `<email>billing@acme.example</email>` | **yes** |
| `Tier_2_Engineering` carries the Tier 2 shared mailbox | **no `<email>` element at all** | **NO** |

`check_queues.py` independently confirms it: `Warnings found (2)`, naming Tier 1 General **and** Tier 2
Engineering. **This is not a defect in the artefact.** Q88 answers a *posture* for Tier 2 ("a shared
mailbox") and names no address anywhere on file, and `metadata-builder` will not invent one
(`decisions.md` D-M2S04-02, O-M2S04-02). The criterion is the thing that states a fact the build never
grounded. **The step test's own description is stale too** — it predicts `Warnings found (1)`
(O-M2S04-01).

**The human's choice, explicitly:** (a) supply Tier 2's mailbox address and rebuild `M2-S04`, after
which the criterion becomes true; or (b) accept the decided state — no address,
`doesSendEmailToMembers=false`, nobody notified, the record visible in the queue list view — and have
the criterion reworded at v6. **Do not tick as written.**

### ☐ 5 — `M2-S04` · Membership is by group and role, never by named user, and the rosters are current

**From:** `tests/M2-S04/results.json` → `skipped_manual[2]` (W02 2 of 3).
**Tester's evidence: PASS on the file-checkable half** — no `<users>` element in any of the six files;
`Tier_1_General`'s `queueMembers/publicGroups/publicGroup` names exactly `Support_Tier_1`.
**The roster half is not file-checkable in a design-only build:** a support manager confirms the three
public-group memberships match the current rosters (12 Tier 1 / 4 Tier 2 / 2 Billing, Q8).

**Read alongside it:** `<doesIncludeBosses>true</doesIncludeBosses>` is on all three groups as a *skill
default*, not an answered decision (D-M2S04-01), and `<queueMembers>` names no `<roles>` member even
though Q29 answers "by role and public group" (D-M2S04-03). And the groups deploy **empty** — the
`GroupMember` load is a post-deploy data step (§ 4).

### ☐ 6 — `M2-S05` · Private OWD plus exactly one sharing rule, and no rule reaches Billing

**From:** `tests/M2-S05/results.json` → `skipped_manual[0]` (B01 + B04; B04 rewritten so it is tickable
at the M2 gate from artefacts on disk rather than deferred to M5, which had deadlocked this step).
**Tester's evidence** (`tests/M2-S05/summary.md` § "Manual grep confirmations", re-read this run):

- exactly **one** `<sharingCriteriaRules>` block — confirmed, count = 1;
- `sharedTo` group is `Support_Tier_2` and no other — confirmed;
- no rule names the Billing record type or `Billing_Team` — confirmed; "Billing" appears only in the
  rule's free-text `<description>`, never as a `criteriaItems.value`, a `sharedTo.group`, or a second rule;
- `<sharingModel>Private</sharingModel>` lives on `artefacts/M1-S01/objects/Case/Case.object-meta.xml`
  and is not restated here — confirmed;
- no `*.settings-meta.xml` anywhere under `artefacts/` — confirmed by `find`, zero results.

**Ticks when** a human also accepts that `case-visibility-model.md` states, in one sentence, why a
Tier 1 agent cannot open a Billing case and names the file the default lives on. It does — quoted in
§ 10. **Note what this line is and is not:** it certifies the *configuration*. Proving the *denial*
against a live user is M5's `UserRecordAccess` test, where a sandbox exists.

---

## 9. Planner carry-forward — every open item the gate should see in one place

None of these blocks the milestone; all are `plan.json` text or declarations, and
`standards/build-orchestration.md` § 2 gives `build_plan.py` sole authority over them. This agent
touches `plan.json` only through its single `set-milestone` call.

### 9.1 The five M2 open-item series, from `decisions.md`

| id | Item | Status after this run |
|---|---|---|
| **O-M2S01-01** | F-01's remedy named `M2-S01`; `layoutAssignments` is `M2-S03`'s | **Moot, as its own text predicted.** The finding is closed, so re-pointing it is no longer the applicable fix. Record F-01 as CLOSED, sourced to `M2-S03` |
| **O-M2S02-01** | `deploy-order.md` undeclared in `outputs[]` on `M2-S02` — a regression after `M2-S01` fixed it | **Still open, and now the only M2 step affected.** See the table below |
| **O-M2S02-02** | `Case_Tier1` and `Case_Tier2` are identical | **Confirmed, and it now has a twin.** See § 9.3 |
| **O-M2S02-03** | `A1.steps[]` does not list `M2-S02` | Open. See § 9.2 |
| **O-M2S02-04** | F-15 closed at the skills, but no `M2-S02` test description mentions the DESC rules | Open — and **F-16 is what that drift costs** when a checker's rule set moves under a plan that already cites it |
| **O-M2S03-01** | `acceptance_tests[1].description` predicts `Scanned 14 metadata file(s)`; the run prints 15 | **Confirmed by this run: 15.** Same perishable shape as F-07's residue — a build-scoped test whose description quotes a whole-tree file count is invalidated by any later step that writes a file the suffix list matches |
| **O-M2S03-02** | Two Questions-to-Ask rows unanswered by any of the 97 clarifications: managed packages forcing a profile assignment; Person Accounts enabled | Open. The three profiles were built on the unstated assumption that neither applies |
| **O-M2S03-03** | `A1.steps[]` does not list `M2-S03` | Open. See § 9.2 |
| **O-M2S04-01** | `acceptance_tests[0].description` predicts `Warnings found (1)`; the run prints `(2)` | **Confirmed by this run: `Warnings found (2)`**, Tier 1 General and Tier 2 Engineering |
| **O-M2S04-02** | Manual W02 (1 of 3)'s Tier 2 mailbox criterion does not match the artefact | **Confirmed.** Staged for adjudication as § 8 line 4 |
| **O-M2S04-03** | Two plan-level orderings: `M3-S05` (Omni-Channel) sequenced after `M2-S04` against the cited reference's own order; the step's `type` (`access`) disagrees with § 4's artefact table (`routing`) | Open, neither fixable at step level. The `type` disagreement is why M2-S04's workbook rows are filed under Section 6 |
| **O-M2S04-04** | Correction of record: the data-skew checker's exit-1 gap is closed (v1.1.1 counts `queueMembers/publicGroups` as use) | **Confirmed and extended.** At *build* scope the checker now reports `No data skew or sharing performance issues found.` — 0 findings, not the 3 reclassified WARNs it gives at step scope |
| **O-M2S05-01** | Billing's own access (queue ownership, `M2-S04`) and Tier 1's exclusion (absence of a rule, `M2-S05`) are two mechanisms in two steps, and nothing reconciles them | **Partly discharged by an artefact, still open in the plan.** See § 10 |
| **O-M2S05-02** | Correction of record: `M1-S01`'s `CWB-SHARE-001` and `REQ-010` both say the build-scope `check_sharing_model.py` assertion "has not run" | **It has now run twice and passed twice** — at `M2-S05`'s step test and again as `M2-T2` in this run. Both stale sentences are `M1-S01`'s doc-keeper's to correct |

### 9.2 `A1.steps[]` lists one step and shapes four

`plan.json` → `assumptions[A1].steps[]` reads **`["M2-S05"]`**. Four steps carry artefacts A1 shaped:

| Step | What A1 shaped | Recorded as a gap in |
|---|---|---|
| `M1-S01` | the `Private` OWD — **the mechanism that actually makes A1 true** | verifier **W03** |
| `M2-S02` | `Case_Tier1`/`Case_Tier2` withhold `Case.Billing`; `Case_Billing` withholds `Case.Support` | **O-M2S02-03** |
| `M2-S03` | the same mirror-image `recordTypeVisibilities` / `layoutAssignments` split on all three profiles | **O-M2S03-03** |
| `M2-S05` | the deliberate absence of a Billing rule | listed |

Three separate agents recorded the same omission three times, on three different steps, and it is still
one line in `plan.json`. **The concrete cost:** `M5-S04`'s compile run builds the assumptions section
from `assumptions[].steps[]` "rather than from step-note prose" — its own acceptance test says so — so
the compiled document will name one carrier of a `risk: high` assumption where four exist. **Remedy at
v6:** `A1.steps[] = ["M1-S01", "M2-S02", "M2-S03", "M2-S05"]`. Note the distinction all three entries
preserve and the fix should not blur: `recordTypeVisibilities` governs which record type a user may
*select*; the Private OWD plus `M2-S05`'s rule governs whether an existing record can be *opened*.

### 9.3 `deploy-order.md` in `outputs[]` — exactly which steps declare it

The gate asked for this precisely, and the honest answer is not "S03–S05 only":

| Step | Declared? | How |
|---|---|---|
| `M1-S01` | **no** | — (F-04 / O-M1S02-02) |
| `M1-S02` | **no** | — (F-04 / O-M1S02-02) |
| `M2-S01` | **yes** | **at plan time, in v5** — 0 amendments. The first step in this build to declare it |
| `M2-S02` | **no** | — the regression O-M2S02-01 records: the step immediately after `M2-S01` did not inherit the fix |
| `M2-S03` | **yes** | `amend-step`, 2026-09-12T00:38:44Z, by "dry-run operator (Fable)" |
| `M2-S04` | **yes** | the same amendment run |
| `M2-S05` | **yes** | the same amendment run |

So: **declared on four of five M2 steps — S01 at plan time, S03/S04/S05 by amendment — and undeclared
on S02 alone**, plus both M1 steps. All seven files exist and all seven are non-empty; the four declared
ones are the only ones `check-outputs` confirms. **Why it matters beyond bookkeeping:**
`agents/build-doc-keeper/AGENT.md` Step 10 compiles `M5-S04`'s build-wide deploy order from exactly
these seven files, three of which no gate in the loop confirms. **Remedy at v6:** declare
`artefacts/<step-id>/deploy-order.md` on every `metadata-builder`-owned step at once, rather than case
by case as each gap is found.

### 9.4 Test descriptions that no longer describe their run

Four confirmed in this run. Each `expected` still holds; only the prose is stale. Grouped because they
are one defect: a test's `description` is authored prose, not derived from the checker's current rule
set or from the tree it walks.

| Where | Says | Run says |
|---|---|---|
| `steps[M2-S03].acceptance_tests[1]` | `Scanned 14 metadata file(s)` | **15** (O-M2S03-01) |
| `steps[M2-S04].acceptance_tests[0]` | `Warnings found (1)`, Tier 1 General only | **`Warnings found (2)`**, Tier 1 General and Tier 2 Engineering (O-M2S04-01) |
| `steps[M2-S02].acceptance_tests[0..2]` | no mention of the DESC rules the checkers now enforce | the rules ran and were the only thing found (O-M2S02-04) — **and they are what F-16 trips on** |
| `steps[M2-S03].acceptance_tests[1]` | the run resolves "any `Profile`-sourced record-type reference (12)" | the layout half is asserted; the record-type half is not (**F-19**) |

### 9.5 Two identical pairs, at two layers of the same stack

`Case_Tier1` and `Case_Tier2` are **byte-identical apart from `<label>` and `<description>`** (confirmed
by diff this run): the same `fieldPermissions` edit on `Case.Severity__c`, the same
`recordTypeVisibilities` on `Case.Support`. `Acme Support Tier 1` and `Acme Support Tier 2` are
**byte-identical apart from `<description>`**.

No answered clarification distinguishes Tier 2's *access* from Tier 1's — the requirement's Tier 1/Tier 2
split is routing (pushed vs pulled work, `M2-S04`/`M3-S05`) and escalation (untouched 8 business hours,
`M4-S04`), neither of which is access. Four files exist because `outputs[]` declares four.

**Not a defect to fix by re-running a step** — both steps built exactly what the plan declared and both
pass every check declared against them. **The v6 question, now at two layers:** collapse each pair into
one artefact composed into both personas, or keep four declared outputs and accept that they diverge
only when a future requirement gives one team an access the other lacks. O-M2S02-02 asks it for the
permission sets; the profiles are the twin it does not mention.

---

## 10. The Billing visibility reconciliation, stated plainly for the gate (O-M2S05-01)

The gate asked for this in one place, so here it is in one place.

**Billing's access to Billing cases and Tier 1's exclusion from them are two different mechanisms,
built by two different steps, and only one of them is a file you can point at.**

| Who | Support case | Billing case | Mechanism | Step |
|---|---|---|---|---|
| Tier 1 (`Support_Tier_1`) | as **owner**, once `M3-S04`'s assignment rule transfers the case to `Tier_1_General` and a member takes it | **no access** | the Private OWD, and **the absence** of any rule naming `Billing_Team` or the Billing record type | `M1-S01` (OWD) + `M2-S05` (the absence) |
| Tier 2 (`Support_Tier_2`) | `Edit`, by `Support_Cases_To_Tier_2` (`RecordTypeId equals Support`, `includeRecordsOwnedByAll: true`) | no access — the criterion filters it out | a criteria-based sharing rule | `M2-S05` |
| Billing (`Billing_Team`) | no standing access | as **owner**, through the `Billing` queue | **queue ownership — not a sharing rule** | `M2-S04` (the queue) + `M3-S04` (the transfer, `pending`) |

**The asymmetry is deliberate and it is not symmetrical to verify.** Tier 1's exclusion is proved by
finding *no file*; Billing's own access is proved by finding a queue *in a different step*, and it does
not work until `M3-S04` (`pending`) transfers ownership to that queue. A reviewer reading only `M2-S05`
would not learn where Billing's access comes from.

**What has changed since O-M2S05-01 was written.** The entry says "nothing reconciles them". An
**artefact** now does: `artefacts/M2-S05/case-visibility-model.md` § "How each team actually reaches a
case" states all three rows above, and names queue ownership explicitly — *"**This is queue ownership,
not a sharing rule.** No sharing rule was written for Billing, because A1's conservative reading is
about keeping others out, and the Billing team's own access already exists through the queue."* The same
document's one-sentence statement is quoted below.

> A Tier 1 agent cannot open a Billing case because `Case` carries `<sharingModel>Private</sharingModel>`
> in `artefacts/M1-S01/objects/Case/Case.object-meta.xml`, which grants a non-owner nothing, and the only
> sharing rule in this build — `Support_Cases_To_Tier_2` — matches `RecordTypeId equals Support` and
> shares to `Support_Tier_2`, so no rule names the Billing record type or the `Billing_Team` group as a
> target and nothing lifts a Billing case above the Private default for Tier 1.

**What is still open, and it is the part that matters.** Nothing in **`plan.json`** records the
composition. `A1.steps[]` names `M2-S05` alone (§ 9.2), and no decision entry ties `M2-S04`'s queue to
`M2-S05`'s absence as two halves of one answer. **The consequence O-M2S05-01 names:** a later change to
`M2-S04`'s queue — a second Billing queue, or dropping queue-based ownership for direct assignment —
could silently break Billing's access to its own cases without touching anything `M2-S05` owns, and
nothing in the build would flag the connection.

**What the gate should do with it:** accept, in the same breath as § 8 line 1, that Billing visibility =
queue ownership (`M2-S04`) **+** no competing restriction (`M2-S05`'s deliberate absence), and ask for
that to be recorded at plan level rather than only in one step's documentation artefact.

---

## 11. Requirement closure (Step 9)

M2 serves **REQ-016 … REQ-029** — 14 rows in `traceability.md`. Every row's *machine* half passes.
**No row reaches `Done`,** and two reach `In UAT`:

| Status | Requirements | What that means |
|---|---|---|
| **In UAT** — only the gate tick remains | `REQ-016` (integration-only bypass grant), `REQ-025` (queue retirement does not orphan records) | no further step in `plan.json` depends on either artefact |
| **In Build** — a later step serving the requirement remains | `REQ-017`–`REQ-024`, `REQ-026`–`REQ-029` (12 rows) | the access layer exists; the mechanism that exercises it does not yet |

The named dependencies, so "In Build" is a fact rather than a hedge: `REQ-018`–`020`, `REQ-026`–`028`
wait on nothing in M2 — they read `In Build` because `recordTypeVisibilities` governs *selection* while
*opening* a record is the Private OWD plus `M2-S05`'s rule, and those rows were written when `M2-S05`
was still `pending`. **That dependency has now landed** (`M2-S05` is `documented`, `M2-T2` passes at
build scope), so six of the twelve are closer than their recorded status says; correcting the status
cells is `build-doc-keeper`'s on a future pass, not this agent's. The rest genuinely wait: `REQ-021`,
`REQ-024` on `M3-S03`/`M3-S04` (`pending`), `REQ-022` on `M3-S05` (**`blocked`** — deferred Q32–Q35),
`REQ-023` on `M4-S04` and `M5-S01`, `REQ-029` on `M5-S02` (**`blocked`** — a borrowed agent's missing
inputs, unrelated to this row).

**Still open across the milestone, both from deferred blocking questions:**

- **Q13 → assumption A1 (`risk: high`)** — the lineage of `REQ-010`, `REQ-018`–`020`, `REQ-023`,
  `REQ-026`–`029`. Nine of M2's fourteen requirements rest on a deferred answer. § 8 line 1 is where a
  human accepts it.
- **Q57 → assumption A13 (`risk: medium`)** — `REQ-014`. Unverifiable until `M3-S01`'s validation rules
  exist, and A13's own stated verification route does not exist (**F-03**).

---

## 12. Optional validate-only command — for the human, and this agent did not run it

**This agent runs no `sf` command at all.** The line below is for a human, and nothing in this loop
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
`mock_deploy.py:resolve_manifest_text()` reads `reports/MILESTONE-M2-package.xml` rather than merging
the step files on the fly. `checkOnly: true` is hard-coded and the script has no deploy option.

### Go / no-go items before any deploy of this manifest, per `skills/devops/pre-deployment-checklist`

| # | Item | State |
|---|---|---|
| 1 | M1 is in the target org first | **required** — 9 of M2's 48 references resolve to M1-S01 fields/record types and 9 to M1-S02 layouts. Profiles fail with `INVALID_CROSS_REFERENCE_KEY` without them |
| 2 | Deploy M2-S04's groups before or with M2-S05's sharing rule | **required** — F-20. One request satisfies it; staging by position does not |
| 3 | `GroupMember` rows loaded after deploy | **required, and not in this deploy** — all three groups deploy empty; the sharing rule and all three queues then grant nobody anything. Owner: CRM admin lead |
| 4 | `PermissionSetAssignment` for `Case_Intake_Integration` to the integration identity and no human user | **required, and not in this deploy** — record data. § 8 line 2 |
| 5 | Users assigned to the three PSGs; poll `PermissionSetGroup.Status` for `Updated` before UAT (Q96) | **required, post-deploy** |
| 6 | Target org's `CaseStatus` value set carries the values M1's business processes select | **F-02** — discharged on `sfskills-dev` only; a per-target-org precondition |
| 7 | API version `62.0` is right for the target org | **F-06** — defaulted by the owning agent eight times, never decided in the plan |
| 8 | The merged manifest's `SharingRules:Case` container form is accepted by the CLI | **unverified** — § 5. The `--mode manifest` run above is the check |
| 9 | Sharing recalculation has finished before believing any access reading | **required** — `case-visibility-model.md` says so explicitly |
| 10 | The 244-character description on `Case_Intake_Integration` | **deploys fine** (< 255, proven by run 3) and **fails M2-T1** (> 200). F-16 |

---

## 13. Verdict, confidence, and what the human decides at G3

### Verdict: **`not-ready`**

Per `agents/milestone-verifier/AGENT.md` Step 9, `not-ready` follows from "at least one unresolved
reference, ordering contradiction, failing test, or blocked step". **One declared milestone acceptance
test fails** (`M2-T1`, exit 1 against a declared exit 0). That is the whole of it, and the rest of the
milestone is in better shape than that verdict sounds:

| Check | Result |
|---|---|
| Steps documented | 5 of 5. **No blocked step** |
| References resolved | **48 of 48.** 1 unclassifiable (a criteria value the org has since validated) |
| Ordering contradictions | **0 by artefact type.** 1 backwards dependency in the recorded positions, mitigated three ways (F-20) |
| Merged manifest | built, **no collision, no version conflict**, consistent two-way |
| Milestone acceptance tests | **2 of 3 executable tests pass; `M2-T1` fails** |
| Org-facing validation | mock deploy run 3: **32 components, 0 errors** — every M1 and M2 artefact validates unmodified |
| Closed from M1 | **F-01** (the milestone's headline job) and **F-12** |

This verdict is a recommendation, not a decision. It is recorded as
`set-milestone --status rejected`, which is a statement about what the checks found — **it is not a
gate, and it does not block the human from approving G3.**

### Confidence: **MEDIUM**

Per the Step 10 table. HIGH requires that every declared acceptance test ran **and** no reference was
unclassifiable. One unclassifiable reference (§ 3.3) puts it at MEDIUM by itself; every declared test
did run, every step was documented, the merged manifest built without conflict, and no declared checker
was missing — so nothing pulls it to LOW. The failing test is a finding, not an unrun check.

### What the human decides at G3 — five things, in order of consequence

1. **Assumption A1, and whether M2 was built on the right reading of a deferred question.** Q13 was
   deferred; A1 (`risk: high`) takes the record-level reading, and **nine of M2's fourteen requirements
   rest on it**. If the answer is field-level masking, D5's stated consequence is that `M2-S05` is
   **re-planned, not patched**. § 8 line 1 is the tick; § 10 is the reading.
2. **The Billing composition (§ 10).** Billing sees Billing cases as *queue owner* (`M2-S04`, and only
   once `M3-S04` transfers ownership); Tier 1 is excluded by the *absence* of a rule (`M2-S05`). Both are
   individually grounded; `plan.json` records neither as half of the other. Accept the composition, and
   ask for it recorded at plan level.
3. **F-16 — rebuild `M2-S01`, or accept the WARN.** A 244-character description deploys (proven) and
   fails M2's own test (measured). Remedy (a) is one rebuild cycle on one step and leaves the test's exit
   code meaning what it says; remedy (b) is a v6 decision that a length advisory should not fail a
   milestone. Either way **F-17** should be fixed once, in the three skills, rather than per plan.
4. **§ 8 line 4 — the Tier 2 mailbox criterion that does not hold.** Supply Tier 2's address and
   rebuild `M2-S04`, or accept "no address, nobody notified" and have the criterion reworded. **This one
   must not be ticked as written.**
5. **F-18 before any manifest-driven deploy.** `MILESTONE-M1-package.xml` still carries the bare
   `CompactLayout` member a deploy has already rejected by name. `MILESTONE-M2-package.xml` is clean; a
   hand-merge of the two must take `Case.Case_Intake`.

Approving G3 with this report in hand accepts: assumption A1; the Billing composition; one failing
declared test whose artefact deploys; one manual criterion that does not hold against its artefact; and
the carry-forward in § 9 — `A1.steps[]` naming one of four carriers, `deploy-order.md` undeclared on
`M2-S02`, four stale test descriptions, and two identical pairs awaiting a collapse decision.

---

## 14. Recorded verdict, and the gate command

The verdict and this report's path were recorded with the one plan write this agent makes — a
subcommand, never a hand edit:

```bash
python3 scripts/build_plan.py set-milestone .sfskills/builds/case-onboarding/plan.json M2 \
  --status rejected --report-path reports/MILESTONE-M2-REPORT.md
```

`set-milestone` takes `--report-path`, not `--file`: no JSON body was handed to the CLI, so nothing was
written under `inputs/`. This run's envelope is at `envelopes/M2/2026-09-12T02-10-00Z.{json,md}`; this
report and the merged manifest are under `reports/`. The three trees do not borrow each other's paths.

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

So the command will succeed if run. **It does not check this report's verdict**, and `milestones[M2].status`
is now `rejected` — plan bookkeeping that records what the checks found. There is no blocked step in M2,
so approving accepts no unbuilt gap; it accepts the five decisions in § 13.

To reject instead — which sets `milestones[M2].status` to `rejected` and leaves the build at `building`:

```bash
python3 scripts/build_plan.py gate .sfskills/builds/case-onboarding/plan.json milestone:M2 reject \
  --by "<name>" --notes "<why>"
```

If F-16 is to be closed before the gate, the rebuild path is `documented → running` on `M2-S01`
(§ 4 of the contract), then `/test-build-step`, `/keep-build-docs`, and `/verify-milestone` again —
which is what "leaves the milestone above it stale until `/verify-milestone` is re-run" means.

---

## 15. Process observations

**Healthy.**
- The F-15 → rebuild → mock-deploy → re-test loop worked end to end, and the org caught what three
  green checkers did not. `MOCK-DEPLOY-M2.md` runs 1→2→3 (10 errors → 0 → 0 across 32 components) is the
  clearest evidence in this build that § 5's human-run validation earns its place.
- `M2-S03` did the job M1's report assigned it. F-01 was open for two milestones because
  `layoutAssignments` lives on a root no step had produced; three profiles closed it, and the negative
  control proves the checker is reading them (§ 3.2).
- Every one of the five steps' `deploy-order.md` files names its own ungrounded elements rather than
  smoothing them over — `M2-S05`'s Decision 1 argues *against* the manifest form it wrote and says what
  to do if a deploy rejects it. That is why § 5 could report the container-form question at all.
- Three of the six manual lines arrived with file-checkable evidence already gathered by the tester
  (`tests/M2-S01/manual-evidence.stdout.txt`, `tests/M2-S04/results.json`, `tests/M2-S05/summary.md`),
  which narrows what a human at the gate has to judge to the part that genuinely needs judgment.

**Concerning.**
- **A skill version bump moved a finished step from green to red with no signal** (F-16). `M2-S01` was
  `documented` and passing on 2026-09-06; a rule added on 2026-09-11 to fix a *different* step's failure
  made it fail, and nothing in the loop re-ran its tests. O-M2S02-04 named the drift in the test
  *descriptions*; this is the same drift in the *exit codes*, and it is the more expensive half.
- **Three checkers, one fact, three exit policies** (F-17). Whether a WARN can fail a milestone is
  currently an accident of which checker the plan cited.
- **The same omission recorded three times is still one line in `plan.json`** (§ 9.2). `A1.steps[]` is
  the standing example: W03, O-M2S02-03 and O-M2S03-03 are three agents finding the same gap on three
  steps. Per-step documentation runs can only record; no agent in the loop is scoped to fix a
  plan-level field, so a v6 pass is the only route and the backlog grows one entry per step.
- **A merged manifest regenerated by no one** (F-18). `MILESTONE-M1-package.xml` went stale the moment
  M1-S01 was rebuilt, and the tool that would have caught it took a different code path. Every other
  derived view in this build is regenerated from `plan.json`; the merged manifest is written once, by
  hand, per verification run.

**Ambiguous — for the human, not for this agent.**
- Whether a 200-character headroom WARN should be able to fail a milestone acceptance test. Two
  defensible answers; the plan currently gives both, depending on the checker.
- Whether `Case_Tier1`/`Case_Tier2` and the two Tier profiles should collapse (§ 9.5). It depends on
  whether the two teams are expected to diverge on *access* later, which no clarification answers.
- The `SharingRules` container versus `SharingCriteriaRule` rule-type manifest form (§ 5). The cited
  skill says one thing, two other skills in the library do the other, and no deploy has read either form
  for this file.
- Tier 2's queue mailbox (§ 8 line 4): a posture with no address. The artefact is right and the test
  criterion is not, and only a human can say which should change.

**Suggested follow-ups — recommendations only; this agent invoked neither.**
- `deployment-risk-scorer` — to risk-score `reports/MILESTONE-M2-package.xml` against the target org
  before the human runs the § 12 command, since 19 members across `Profile`, `PermissionSet` and
  `SharingRules` is the change class where an org's existing state matters most.
- `permission-set-architect` — to adjudicate § 9.5's collapse question on the two identical pairs with
  the persona model in view, which is a design call rather than a verification one.

---

## Citations

| type | id / path | used for |
|---|---|---|
| standard | `standards/build-orchestration.md` | § 2 (this report is written not rendered; recorded with `set-milestone --report-path`; the three output trees), § 3 (the G3 conditions checked in § 14), § 4 (the `documented → running` rebuild path in F-16), § 5 (checker scope; run commands verbatim from the build directory; `mock_deploy.py` as the pre-G3 human-run validation cited as § 6.4), § 7 (return so the human can act), § 8 (`build_plan.py` is the single writer) |
| standard | `AGENT_RULES.md` | run-time rules for this invocation: no org write, no auto-chaining, no hand edit of generated state |
| standard | `agents/_shared/AGENT_CONTRACT.md` | section shape, the Process Observations block (§ 15), the confidence rubric this agent's Step 10 overrides |
| standard | `agents/_shared/DELIVERABLE_CONTRACT.md` | atomic write of the envelope/report pair; `dimensions_skipped` states; the build-scoped persistence deviation recorded in the envelope |
| standard | `agents/_shared/REFUSAL_CODES.md` | checked and not used — no refusal condition was met |
| standard | `agents/_shared/schemas/build-plan.schema.json` | the `milestones[]`, `human_gates[]`, `steps[].amendments[]` and `assumptions[]` fields read in § 0, § 9 |
| standard | `agents/_shared/schemas/output-envelope.schema.json` | envelope shape; the `report_path` / `extensions.report_path` distinction |
| skill | `skills/devops/metadata-api-retrieve-deploy` | the manifest grammar and the single `<version>` element in § 5; what one deploy request does and does not carry across |
| skill | `skills/devops/permission-set-deployment-ordering` | § 4's check that no `fieldPermissions` entry names a field defined later in the order — the `Case_Agent_Core` → `M1-S01` fields row |
| skill | `skills/devops/flow-deployment-activation-ordering` | § 4: where automation sits in the order, and the recorded finding that M2 contains none, so the check is not-applicable rather than silently passed |
| skill | `skills/devops/deployment-error-diagnosis` | the deploy-time error each finding predicts: `INVALID_CROSS_REFERENCE_KEY` (F-19, go/no-go 1), the `CompactLayout … not found in zipped directory` message (F-18), and F-16's explicit *none* |
| skill | `skills/devops/pre-deployment-checklist` | § 12's ten go/no-go items, so "verified" means checked rather than quiet |
| skill | `skills/admin/uat-and-acceptance-criteria` | § 8's Given/When/Then shape, the tick condition on every line, and the judgment that § 8 line 4 is not tickable as written |
| skill | `skills/admin/requirements-traceability-matrix` | § 11's closure statement in `traceability.md`'s own REQ ids and `In Build` / `In UAT` vocabulary |
| skill | `skills/admin/sharing-and-visibility` | `check_sharing_model.py` (M2-T2); § 5's `SharingRules` vs `SharingCriteriaRule` manifest-form divergence, read from `references/metadata-examples.md` § 6 |
| skill | `skills/admin/permission-sets-vs-profiles` | `check_access_model.py` (M2-T1) and its `PSVP-DESC-01/02` rules and exit policy — the substance of F-16 and F-17 |
| skill | `skills/admin/permission-set-architecture` | `check_permission_set_architecture.py` at build scope (§ 6.5); `PSA-DESC-02` in F-17 |
| skill | `skills/admin/permission-set-group-composition` | `check_permission_set_group_composition.py` at build scope; the `PSG_<persona>_<env>` convention the three PSGs adopt; `PSGC-DESC-02` in F-17 |
| skill | `skills/admin/record-types-and-page-layouts` | `check_record_type_layouts.py` — F-01's closure (§ 3.2) and its boundary (F-19) |
| skill | `skills/admin/queues-and-public-groups` | `check_queues.py` at build scope; the `GroupMember`-does-not-deploy fact in § 4 and go/no-go 3 |
| skill | `skills/admin/custom-permissions` | `check_custom_permissions.py` at build scope; why `Consumers: 0` is the designed state at M2 |
| skill | `skills/admin/data-skew-and-sharing-performance` | `check_data_skew_and_sharing_performance.py` at build scope, and the step-versus-build scope difference recorded against O-M2S04-04 |
| decision_tree | `standards/decision-trees/sharing-selection.md` | branch **Q3**, plan decision **D5** — cited by `M2-S05` and read to confirm § 10's mechanism table and that a restriction rule is not available on `Case` (Q8's eligible-object list) |

### Provenance of this report

Written by `agents/milestone-verifier/AGENT.md` (v1.0.0, `status: beta`, `requires_org: false`) on run
`2026-09-12T02-10-00Z`. Every exit code in § 6 is from a command run in this session from
`.sfskills/builds/case-onboarding/`, captured under `tests/M2/`. The two negative controls ran against a
copy of `artefacts/` in the session scratchpad; **no file under the build directory was modified by this
run except the three this agent owns** — `reports/MILESTONE-M2-REPORT.md`,
`reports/MILESTONE-M2-package.xml`, and `envelopes/M2/2026-09-12T02-10-00Z.{json,md}` — plus the test
captures under `tests/M2/` and the single `set-milestone` write to `plan.json`. No skill, agent,
standard or script was edited. No org was contacted and nothing was deployed.

**Deviation from the Wave 10 persistence default, recorded rather than silent:** the contract's default
pair is `docs/reports/milestone-verifier/<run_id>.{md,json}`. This run is build-scoped and persists to
`.sfskills/builds/case-onboarding/envelopes/M2/` instead — the path
`agents/milestone-verifier/AGENT.md` Step 11 and the envelope schema's build-layer pattern both
prescribe, and the path both M1 verification runs used. `docs/reports/milestone-verifier/` does not
exist in this repo, and the invocation scoped all writes to the build directory.
