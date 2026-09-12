# Milestone acceptance report — M5: Agent surfaces, sandbox proof and the deploy package

Written by `agents/milestone-verifier` (run `2026-09-12T12-52-10Z`) per its `AGENT.md`, for
`.sfskills/builds/case-onboarding/`. This document is **written, not rendered**
(`standards/build-orchestration.md` § 2); its path is recorded with `build_plan.py set-milestone`.
`scale` is absent from `plan.json` and therefore `project` (§ 3.1), so the full report shape
applies and the `scale: ask` one-page carve-out does not.

This is the **last** milestone of the build. Nothing in this report deploys, approves a gate, or
runs `sf`. The G5 decision is the human's.

---

## Verdict

> ### `not-ready`
>
> On **one** ground, and it is a rule rather than a judgement: **`M5-S02` is `blocked`**.
> `agents/milestone-verifier/AGENT.md` Step 9 makes any blocked step a `not-ready` trigger, and
> Step 1 requires the blocked steps to be listed first so the gap is in front of the human rather
> than inferred. Every other Step 9 trigger is clear: **no unresolved reference, no ordering
> contradiction, no failing acceptance test.**

`not-ready` here is not a recommendation to stop. § 3 explicitly permits
`gate milestone:M5 approve` over a step that is `blocked` **with a recorded reason**, and
`M5-S02` has one. What the verdict does is force the decision to be made in the open: approving
M5 accepts that this build ships **no sandbox strategy document** — and the requirement's own
words are *"we must be able to prove it works in a sandbox before customers see it."*

`set-milestone --status rejected` is recorded for the same reason (Step 9 maps `not-ready` to
`rejected`). That is a statement about what the checks found. It is **not** a rejection of the
milestone, it does not write a gate record, and it does not block
`gate milestone:M5 approve` — § 3's gate preconditions read step statuses and the preceding
gate, not `milestones[].status`.

| | |
|---|---|
| Steps | 5 — four `documented`, one `blocked` with a reason |
| Preceding gate | `milestone:M4` — **approved** 2026-09-12T09:23:14Z |
| Milestone acceptance tests | 3 automated (2 `checker`, 1 `manifest`) — **3/3 pass**; 3 `manual` → checklist |
| Cross-step checks (Steps 2–5) | reference resolution **clean**; deploy order **one named divergence, resolved in this report**; merged manifest **zero drift, zero conflict** |
| New findings | 7 — **F-52 … F-58** (1 HIGH, 4 MEDIUM, 2 LOW) |
| Confidence | **LOW** — Step 10's LOW branch fires on "a step was blocked" |

---

## 1. Precondition (Step 1) — the blocked steps, first

### 1.1 `M5-S02` — blocked, in this milestone

| | |
|---|---|
| Step | `M5-S02` — *Sandbox proof plan for the Partial Copy environment* |
| Type / agent | `custom` / `sandbox-strategy-designer` (a Tier-2 agent borrowed per § 4) |
| `blocked_reason` | **`borrowed agent requires team_size, concurrent_workstreams, release_cadence, data_sensitivity`** |
| Artefacts | none — `artefacts/M5-S02/` does not exist |
| Runs | 0 |

The block is correct, and it is worth saying why rather than treating it as a formality.
`agents/sandbox-strategy-designer/AGENT.md` marks all four inputs mandatory for a design run and
its Escalation section reads, in full, *"No team size / cadence → refuse."* The step note records
that all three permitted sources were searched: `requirement.md` gives the **support** headcount
(12 / 4 / 2), not a delivery team; none of the 97 clarifications asks any of the four; and the two
`depends_on` steps produce escalation and sharing metadata. Mapping Q8's support roster onto
`team_size` would have been the invented value the block exists to prevent. Re-owning the step was
considered and rejected — no other `requires_org: false` roster agent declares a sandbox-strategy
deliverable, so a re-owned step would declare an output nobody produces.

**What the block actually costs, stated plainly.** Three things in this build hang off a sandbox
that nobody has planned:

1. **Q68's proof itself** — *"a sandbox test with real inbound email, a clock test, and a loop
   test, before go-live."* This is the milestone's own `goal` sentence.
2. **Q74's refresh rule** — *"The Email-to-Case routing addresses and the website form endpoint
   must be re-pointed on every refresh, or the sandbox will answer real customer mail."* There is
   no document holding that rule at the moment a refresh happens.
3. **Two of M5's three milestone manual tests** (`M5[4]` Billing deny-case, `M5[5]` acknowledgement
   loop) each name "the sandbox the release owner stands up for UAT" and each carries its own
   fallback: *"If no such sandbox exists when the gate is reached, the gate is signed recording
   this check as outstanding rather than ticked."*

### 1.2 `M3-S05` — blocked, in an accepted earlier milestone

Not a precondition for this gate (M3 was approved 2026-09-12T06:24:17Z over exactly this gap), but
carried here because M5 is the last milestone and this is the last report a human reads.

| | |
|---|---|
| Step | `M3-S05` — Omni-Channel push routing for Tier 1 |
| `blocked_reason` | **`deferred: Q32, Q33, Q34, Q35`** |
| Consequence | `REQ-022`'s push half is undelivered. No `ServiceChannel`, `QueueRoutingConfig`, `ServicePresenceStatus`, `PresenceUserConfig` or `PresenceDeclineReason` member exists anywhere in this build. |
| Compensating control | `M5-S01` builds `Tier_1_General_Queue.listView` as Tier 1's **interim pull surface** under assumption A7 (`decisions.md` **D-M5S01-03**) — explicitly not a reversal of decision D4. |

Both blocked steps and both verbatim reasons appear in `artefacts/M5-S05/deploy-order.md` § 2.1,
`artefacts/M5-S04/deploy-order.md`, and the build-level `package.xml` header comment. Neither is
silently absent anywhere the release owner will look. That was `M5-S04[5]`'s and `M5-S05[4]`'s
assertion and it holds.

### 1.3 Precondition result

Four steps `documented`, one `blocked` **with a recorded reason**, preceding gate approved.
The milestone is **verifiable**, and Step 1's refusal condition (`REFUSAL_OUT_OF_SCOPE`) does not
fire. No step is `pending`, `running`, `built`, `tested` or `failed`.

---

## 2. Steps and artefacts (Step 2)

| Step | Type | Agent | Status | Runs | Artefacts |
|---|---|---|---|---|---|
| `M5-S01` | `ui` | `metadata-builder` | `documented` | 8 | 3 × `listView-meta.xml`, `Escalated_Open_Cases.report-meta.xml`, `Support_Operations-meta.xml`, `package.xml` (+ undeclared `deploy-order.md`) |
| `M5-S02` | `custom` | `sandbox-strategy-designer` | **`blocked`** | 0 | **none** |
| `M5-S03` | `docs` | `story-drafter` | `documented` | 4 | `story-backlog.md` (11 stories, 4 epics) |
| `M5-S04` | `docs` | `build-doc-keeper` | `documented` | 7 | `configuration-workbook.md`, `traceability.md`, `deploy-order.md`, `acceptance-criteria.md`, `uat-test-cases.yaml` |
| `M5-S05` | `docs` | `metadata-builder` | `documented` | 4 | `package.xml` (build-level, 29 types / 56 members), `deploy-order.md` |

`M5-S01` took **eight** runs: the org rejected the report twice (F-49 `<description>` > 255; F-50
`reportType`/grouping values taken from the skill's own worked example) before it validated. That
is the fifth flywheel-adjacent record in this build and the **first left open at the skill** —
`skills/admin/reports-and-dashboards` still carries the wrong `reportType` and grouping values
(`decisions.md` **D-M5S01-01**). The next build using that skill pays the same two round-trips.

---

## 3. Reference resolution (Step 3)

M5's only metadata artefacts are `M5-S01`'s five files. Every reference they make was resolved
against the symbol inventory built from M1–M4 (accepted milestones count as defining) and from M5
itself.

### 3.1 Reference classes, per the AGENT.md Step 3 table

| Reference class | Instances in M5 | Resolved here | Resolved earlier | Unresolved | Unclassifiable |
|---|---|---|---|---|---|
| Validation-rule field references | 0 (M3-S01's, already accepted) | — | — | 0 | 0 |
| Assignment-rule criteria / `assignedTo` | 0 (M3-S04's) | — | — | 0 | 0 |
| Permission-set grants | 0 (M2's) | — | — | 0 | 0 |
| Flow field references | 0 (M4-S03's) | — | — | 0 | 0 |
| Entitlement-process milestones / business hours | 0 (M4-S02's) | — | — | 0 | 0 |
| **Layout / list-view / path field + picklist references** | **16** | 0 | 6 | **0** | **10** |

Expanding the one populated row, file by file:

| Reference | From | Resolves to | Outcome |
|---|---|---|---|
| `<queue>Billing` | `Billing_Queue.listView` | `artefacts/M2-S04/queues/Billing.queue-meta.xml` | **resolved, earlier milestone** |
| `<queue>Tier_1_General` | `Tier_1_General_Queue.listView` | `artefacts/M2-S04/queues/Tier_1_General.queue-meta.xml` | **resolved, earlier milestone** |
| `<queue>Tier_2_Engineering` | `Tier_2_Queue.listView` | `artefacts/M2-S04/queues/Tier_2_Engineering.queue-meta.xml` | **resolved, earlier milestone** |
| `<sharedTo><group>Billing_Team` | `Billing_Queue.listView` | `artefacts/M2-S04/groups/Billing_Team.group-meta.xml` | **resolved, earlier milestone** |
| `<sharedTo><group>Support_Tier_1` | `Tier_1_General_Queue.listView` | `artefacts/M2-S04/groups/Support_Tier_1.group-meta.xml` | **resolved, earlier milestone** |
| `<sharedTo><group>Support_Tier_2` | `Tier_2_Queue.listView` + `Support_Operations-meta.xml` `folderShares` | `artefacts/M2-S04/groups/Support_Tier_2.group-meta.xml` | **resolved, earlier milestone** |
| `<columns>Severity__c` | `Tier_2_Queue.listView` | `artefacts/M1-S01/objects/Case/fields/Severity__c.field-meta.xml` | **resolved, earlier milestone** |
| `CASES.CASE_NUMBER`, `CASES.SUBJECT`, `CASES.PRIORITY`, `CASES.STATUS`, `ACCOUNT.NAME`, `LAST_UPDATE` | all three list views | platform list-view column codes | **unclassifiable** — see 3.2 |
| `STATUS`, `CREATED_DATE`, `OWNER`, `PRIORITY` | `Escalated_Open_Cases.report` (`columns`, `criteriaItems`, `groupingsDown`) | `CaseList` report-type column codes | **unclassifiable** — see 3.2 |

**Unresolved references: 0.** Nothing in M5 names a symbol no step defines.

### 3.2 The ten unclassifiable references, and why that is honest rather than evasive

List-view column codes (`CASES.CASE_NUMBER`) and report column codes (`OWNER`, `CREATED_DATE`)
are **report-type- and object-scoped platform tokens**. They resolve against the target org's own
schema, not against anything this build declares, and `skills/admin/reports-and-dashboards`
SKILL.md workflow step 3 is explicit that they *"cannot be derived from field API names"* and must
be harvested from an org retrieve. A grep over this build's artefacts cannot classify them, and
reporting them as "resolved" would be the exact false-comfort `AGENT.md` Step 3 forbids.

Six of the ten were **settled by the org**, not by this agent: `MOCK-DEPLOY-M5.md` run 2
validated all three list views and the report at 60/60. Four were **not**, and F-51 is the
residue — five candidate codes for `Case.IsEscalated` were probed and all five rejected. That is
the one reference in M5 the build genuinely could not close, and it is recorded rather than
guessed (`decisions.md` **D-M5S01-02**).

### 3.3 The six cross-build checks this gate asked for

| # | Check | Result |
|---|---|---|
| 1 | Every `REQ` row's artefact is carried by an `M5-S05` member | **PASS — 49/49.** All 49 rows naming a metadata artefact resolve to a member of the build-level manifest. Nine rows are `setup-only:` documents or (REQ-058) have no artefact at all, correctly. **But the reverse direction fails — F-52.** |
| 2 | Compiled deploy order vs `M5-S05`'s note | **DIVERGENT BY ONE POSITION, and `M5-S05` is right** — § 4.2 below states which and why. |
| 3 | UAT pack covers every plan-declared manual test incl. milestone-level | **PASS on coverage — 39/39, 1:1**, plus 6 derived negative cases (45 total). **F-53** on two of them. |
| 4 | Story backlog carries the G4 obligations | **PASS — all three.** Completion proxy (`US-CASE-009` notes, verbatim, + RTM row marked "AC-1 (proxy only)"); Q24 training line (`US-CASE-004` notes + `Training impact` field + a Process Observation counting three recordings of the same gap); deploy prerequisites (P1–P6 in the affected stories' `Dependencies`, plus an observation that three stories are Blocked on day one). **F-56** on the numbering. |
| 5 | The six org prerequisites | **PASS as a list** — `artefacts/M5-S05/deploy-order.md` § 5.2 carries all six with source, owner-gate and open status. **F-56** on their propagation. |
| 6 | The version split | **PASS — recorded exactly as claimed.** Nine step manifests at `62.0`, seven at `67.0`, the build manifest at `67.0`. § 5.3 below. |

---

## 4. Deployment order (Step 4)

### 4.1 The sequence, and whether the artefacts agree with it

`agents/build-doc-keeper`'s canonical ten-slot sequence is objects → fields → picklists → record
types → layouts → permission sets → sharing → automation → routing → SLA. `M5-S05`'s note refines
it to a 17-row build-wide table. Taking each M5 artefact and comparing its recorded position
against its own type:

| Artefact | Recorded position | Type says | Agrees? |
|---|---|---|---|
| `ListView` × 3 | `M5-S04` slot 7 (sharing); `M5-S05` slot 7 | after the queues they filter on (slot 6) and the `Severity__c` field (slot 1) | **yes** |
| `ReportFolder Support_Operations` | `M5-S04` slot 8 (automation, `CWB-LAYOUT-010`); `M5-S05` slot 17 | folder before report; both put it before its report | **yes** |
| `Report Escalated_Open_Cases` | `M5-S04` slot 8 (`CWB-LAYOUT-011`); `M5-S05` slot 17 | after its folder | **yes** |
| `M5-S03`/`M5-S04`/`M5-S05` outputs | "not a component" | markdown / YAML / manifest — no deploy position | **yes** |

**No backwards dependency was found.** The two failure shapes `AGENT.md` Step 4 names were checked
specifically:

- **A permission set granting a field defined later** (`skills/devops/permission-set-deployment-ordering`)
  — not present. All five `PermissionSet` members sit at slot 5 / slot 6, after `CustomField`
  (slot 1) and `CustomObject` (slot 3). The one field any of them grants, `Case.Severity__c`,
  is the first row of the build-wide order.
- **Automation arriving before the routing it triggers**
  (`skills/devops/flow-deployment-activation-ordering`) — not present, and better than not
  present: the before-save flow is at slot 14, after the entitlement processes it reads (slot 13);
  the escalation rule is at slot 16, after every symbol it names; and it **ships
  `<active>false</active>`** per Q47, so its arrival state is a deliberate, documented decision
  with its own runbook rather than an accident of ordering.

### 4.2 The one divergence — and which order is right

This is the gate item the request asked to be settled rather than described.

| Document | `Settings:Case` | `AssignmentRules` / `AutoResponseRules` |
|---|---|---|
| `artefacts/M5-S04/deploy-order.md` (compiled, ten-slot) | slot 9, `CWB-AUT-007` — **first** | slot 9, `CWB-AUT-010`/`011` — **after** |
| `artefacts/M5-S05/deploy-order.md` (build manifest note) | slot **11** — **after** | slot **10** — **first** |

**`M5-S05` is right. Four grounds, in order of weight:**

1. **The source both documents draw on says so, without qualification.**
   `artefacts/M3-S03/deploy-order.md` § 3 lists the required sequence for any org that will
   receive real mail, with the rules at step 2 and `Settings:Case` at step 3 — *"before this file,
   not after."*
2. **`CWB-AUT-007`'s own note argues against its own position.** As quoted in `M5-S04`'s hazard
   list, the note places `Settings:Case` "before `M3-S04`'s `AssignmentRules`/`AutoResponseRules`"
   and then gives as its reason *"enabling the channels before the rules exist means live traffic
   lands unrouted."* That reason supports rules-first. The row is internally inconsistent; the
   compiled table faithfully collated the stated position and flagged the whole thing as hazard #1.
   The doc keeper did the right thing — § 10 tells it to report a conflict, not resolve one — so
   this is not a defect in `M5-S04`. It is a conflict that was correctly escalated to here.
3. **The compiled order is plan-step order, not dependency order.** `M5-S04`'s table sorts within
   each slot by row id, and row ids follow the order the steps ran (`M3-S03` before `M3-S04`).
   That is a *record* of how the build was assembled. `M5-S05`'s table is a *deploy* sequence.
   Where the two disagree, the deploy sequence governs a deploy.
4. **The downside is asymmetric and one-way.** Rules-first costs nothing. Channels-first risks
   live cases created unrouted, falling to `defaultCaseOwner` with no acknowledgement sent — and
   `M3-S03/deploy-order.md` records that *"after Email-to-Case is enabled, it can't be disabled."*

**Three qualifications, so the divergence is not over-read.** Neither order is a deploy error:
all 56 members land in one `deploy()` call and the platform resolves component dependencies within
a request regardless of `<types>` order. The real safety margin is the human step *after* slot 11
— pointing mail-server forwarding at the generated `emailServicesAddress` values and publishing
the web form — which is outside the deploy entirely. And on a greenfield org with no forwarding
configured, neither order can produce unrouted traffic. **The divergence matters when, and only
when, the release is split across windows, or forwarding is already live.** `M5-S05`
§ 3.2 names splitting the release as precisely what its table is for.

**Verdict on Step 4: no ordering contradiction.** One documented divergence, resolved in favour
of `M5-S05`, with `M5-S04`'s table correct as a compilation and wrong as a deploy instruction.

---

## 5. Merged manifest (Step 5)

**Path:** `reports/MILESTONE-M5-package.xml` — **29 types, 56 members, `<version>67.0</version>`.**

### 5.1 Drift against `artefacts/M5-S05/package.xml`: none

Verified member-by-member, not by file hash (the two carry different header comments):

```
29 types, 56 members on both sides — IDENTICAL
type-level drift: 0 · members only in merged: 0 · members only in M5-S05: 0 · version: 67.0 = 67.0
```

This is the expected result and worth saying why it is not circular. The merge unions
`artefacts/M5-S01/package.xml` (5 members) with `artefacts/M5-S05/package.xml` (56 members).
`M5-S05` is the **build-level** manifest and already aggregates M5-S01 along with the other
fifteen step manifests, so the union equals the larger set. The check that carries signal is the
one below it.

### 5.2 Conflicts, overlaps and coverage

| Check | Result |
|---|---|
| **`<version>` conflict** | **None.** Both contributing M5 manifests declare `67.0`. `AGENT.md`'s `REFUSAL_NEEDS_HUMAN_REVIEW` trigger (step manifests disagreeing on API version) **does not fire** for M5. |
| **Members in two steps** | **5** — `ListView:Case.{Billing,Tier_1_General,Tier_2}_Queue`, `Report:Support_Operations`, `Report:Support_Operations/Escalated_Open_Cases`. Identical on both sides; **overlap by design, not collision.** |
| **Manifest → file** | **56/56.** Every member resolves to a file under `artefacts/`. |
| **File → manifest** | **62/62.** Every deployable file is covered by a member. The two excluded files are `artefacts/M4-S03/flow-governance-policy.yaml` and `artefacts/M5-S04/uat-test-cases.yaml` — neither is deployable metadata. |
| **M5 artefacts reaching no `<types>` block** | **None that should.** `story-backlog.md`, the five M5-S04 documents and the two M5-S05 documents derive no member, correctly. |

`M5-S05`'s own § 5.1 claims 56/56 and 62/62. **Both re-verified independently here and both hold.**

### 5.3 The version split — checked, not taken on trust

| `<version>` | Step manifests | Count |
|---|---|---|
| `62.0` | M1-S01, M1-S02, M2-S01…M2-S05, M3-S01, M3-S02 | **9** |
| `67.0` | M3-S03, M3-S04, M4-S01…M4-S04, M5-S01 | **7** |
| `67.0` | `M5-S05` (build-level) and `reports/MILESTONE-M5-package.xml` | — |

Exactly as `decisions.md` **D-M5S05-05** records. `67.0` on the aggregate rests on two grounds,
neither of them the builder's judgement: **G3 decision 6** (recorded in
`plan.json.human_gates[milestone:M3].notes`, carried forward by the M4 note) and **the org's own
floor** — `MOCK-DEPLOY-M3.md` run 4 probes a–c show `newEntityRecordType` is *"not valid in
version 62.0"* and *"not valid in version 63.0"*, resolving from `64.0`, so M3-S03's
`Settings:Case` cannot deploy at `62.0` at all.

**The nine `62.0` manifests carry no latent risk**, and this is the first report to check rather
than assume: everything in them was validated **at 62.0** by `MOCK-DEPLOY-M1.md` and
`MOCK-DEPLOY-M2.md` run 3 (32 components, 0 errors). A release owner splitting the deploy per
step would be deploying each at a version the org has already accepted for that content.
The residual item is a plan-level `api_version` field, a `build-planner` v6 backlog entry.

---

## 6. Acceptance tests (Step 6)

Run from the build directory (`skills` symlink present), verbatim as declared, nothing rewritten.

| # | Type | Command / assertion | Expected | Exit | Result |
|---|---|---|---|---|---|
| 0 | `checker` | `python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file artefacts/M5-S04/traceability.md --manifest-dir artefacts` | exit 0 | **0** | **PASS** |
| 1 | `checker` | `python3 skills/admin/change-management-and-deployment/scripts/check_deployment_manifest.py --manifest-dir artefacts` | exit 0, with the SharingRules WARN as the documented outcome | **0** | **PASS** (see F-58) |
| 2 | `manifest` | Every list view, report, report folder and doc artefact in M5 appears in the final `package.xml` with a file behind it | consistent | — | **PASS** — § 5.2 |
| 3–5 | `manual` | three gate checks | ticked at the gate | — | → § 7 |

**3/3 runnable tests pass. No declared checker was missing; both exist on disk and both ran.**

Verbatim output, test 0:

```
WARN: row 56: coverage gap: REQ-055 has no test id (status 'Draft') — waived by decision NONE
WARN: row 57: coverage gap: REQ-056 has no test id (status 'Draft') — waived by decision NONE
WARN: row 58: coverage gap: REQ-057 has no test id (status 'Draft') — waived by decision NONE
WARN: row 59: coverage gap: REQ-058 has no artefact and no test id (status 'Draft') — waived by decision NONE
traceability.md: 58 row(s), build schema, 4 coverage gap(s), 0 orphan(s), 0 error(s), 4 warning(s)
```

Verbatim output, test 1:

```
2 finding(s) detected (0 blocking)
{"score": 90, "findings": [
  {"severity":"WARN","location":"artefacts/M2-S05/package.xml","message":"manifest includes SharingRules; require explicit review and smoke tests"},
  {"severity":"WARN","location":"artefacts/M5-S05/package.xml","message":"manifest includes SharingRules; require explicit review and smoke tests"}],
 "summary": "Scanned 117 manifest or metadata file(s); 2 finding(s) detected."}
```

**The four `check_rtm.py` WARNs are expected and are not a defect.** `decisions.md` **O-M5S04-03**
establishes the mechanism: `check_rtm.py`'s waiver rule reads a row's **`Draft` status** as the
waiver condition, not a cited decision id, so "waived by decision NONE" is the checker naming the
true state accurately. What it does **not** do is relieve the human of confirming the four rows
are meant to be `Draft` — that is G5 decision item 4 below.

### 6.1 Org-facing evidence already on file — read, not run, by this agent

`reports/MOCK-DEPLOY-M5.md`, three runs. **This agent ran none of them and ran no `sf` command.**

| Run | Mode | Result |
|---|---|---|
| 1 | source, M1-S01 … M5-S01 | 60 components, **2 errors** — F-28, plus F-49 (`Description maximum length is:255`). Operator probes then proved F-50 and left F-51 unresolvable. |
| 2 | source, after the F-49/F-50 rebuild | **60/60, one error — F-28 only.** |
| 3 | **manifest**, M1-S01 … M5-S05, over the merged `package.xml` | **60/60, one error — F-28 only.** |

Run 3 is the significant one and it closes two open items. It is the **first validation in this
build that reads a manifest carrying the Apex** — G4's F-43 note said manifest-mode validation of
M4 must wait for M5-S05, and it need wait no longer. And it is the check that caught F-13 in M1
when source mode had missed it, so it exercises the one failure class source mode is blind to:
a member named in `package.xml` with no file behind it. **60/60 at manifest scope is the
strongest org evidence this build has produced.**

---

## 7. Manual checklist for the G5 gate (Step 7)

**Twelve lines.** Nine are `skipped_manual[]` entries from `tests/<step>/results.json`, two are
`M5-S02`'s declared manual tests (the step is blocked, so no results file exists — they are
carried here rather than dropped), and three are the milestone's own. **This agent ticks none of
them.**

| # | From | The human does | A tick means |
|---|---|---|---|
| 1 | `M5-S01` | Read each of the three `listView-meta.xml` files | Each `<queue>` names a developer name present under `artefacts/M2-S04/queues/`, and the Tier 1 General view is present as Tier 1's interim pull surface while `M3-S05` is blocked. **Pre-checked by this agent: all three resolve** (§ 3.1). The reading left to the human is whether the *interim* framing is accepted. |
| 2 | `M5-S03` | Read `story-backlog.md` | Each of the three intake channels has its own story; every story names a tester persona by real profile + `PSG_Tier1_Prod` / `PSG_Tier2_Prod` / `PSG_Billing_Prod`, never the admin; every story carries ≥ 3 Given/When/Then criteria including a permission-denial path. **Read this one against `decisions.md` O-M5S03-05**: the backlog ships **four** stories over three channels — the email channel is split because Q77 gives Billing its own named tester and one story cannot carry two `As a` clauses. That is a deliberate reading of the test's intent, flagged by its author as ambiguous. |
| 3 | `M5-S04` | Read the workbook's assumptions section | All 25 deferred clarifications appear as named rows with an owner and the steps they constrain. **⚠ NOT TICKABLE AS WRITTEN — see F-54.** The compiled workbook has no assumptions section; 16 of the 28 assumptions appear nowhere in any compiled document; no assumption in `plan.json` carries an owner. |
| 4 | `M5-S04` | Read the compiled documents | `M3-S05` and `M5-S02` each appear with their blocked reason **verbatim**, and the UAT pack carries no case that depends on either. **First half PASSES** (verified in § 1). **Second half FAILS — see F-53**: `TC-M3-S05-2` and `TC-M5-S02-2` read artefacts of the blocked steps. |
| 5 | `M5-S05` | Read `deploy-order.md` | It contains no deploy command, only a validate-only command the human may choose to run. **Pre-checked: holds.** § 7 carries `mock_deploy.py --mode manifest` (which hard-codes `--dry-run`) and an `sf project deploy validate` form marked production-only. No `sf project deploy start` anywhere in the file. |
| 6 | `M5-S05` | Read `deploy-order.md` and `package.xml` | `M3-S05` and `M5-S02` are listed as excluded with their reasons verbatim, and no Omni-Channel or sandbox component appears as a member. **Pre-checked: holds** — § 2.1 carries both reasons verbatim, and the manifest contains no Omni-Channel type. |
| 7 | `M5-S05` | Read `package.xml` against the order | `StandardValueSet` before business processes and record types; queues and groups before the rules naming them; `Settings` named explicitly as `Case`, `BusinessHours` and `Flow` (no wildcard); `ApexClass`/`ApexTrigger` from M4-S05 present. **Pre-checked: all four hold.** |
| 8 | `M5-S02` **(blocked step)** | Assign the four missing inputs | `team_size`, `concurrent_workstreams`, `release_cadence`, `data_sensitivity` each have a named owner and a due date, and the gate is signed knowing `M5-S02` ships nothing until they are answered. |
| 9 | `M5-S02` **(blocked step)** | — | **Phase 2.** Not tickable now, by design: the test's own first clause is "Given this step is unblocked in a later phase." |
| 10 | **M5 milestone** | Record the outstanding sandbox proof | The release owner records that the sandbox proof plan is **OUTSTANDING** because `M5-S02` is blocked; names owner and due date for the four inputs; and confirms all 25 deferred clarifications have a named owner and a due date. **The last clause has no artefact behind it — F-54.** |
| 11 | **M5 milestone** | The Billing deny case, against a real user | A Tier 1 agent opening a Billing case's record URL is denied — **confirmed by the admin lead against a real user, not inferred from the sharing metadata.** If no sandbox exists at the gate, the gate is signed recording this **outstanding rather than ticked**. The metadata half is carried by M2-S05's build-scoped `check_sharing_model.py` and passes on artefacts alone. |
| 12 | **M5 milestone** | The acknowledgement loop test | A case created by external email, the acknowledgement observed, then **no second case created from the acknowledgement itself** and no self-loop in the email log. Same sandbox fallback as #11. |

**Accounting:** every line states an observable outcome. Three (#3, #4-second-half, #10-last-clause)
state an outcome the artefacts do **not** currently satisfy, and each is called out inline rather
than left for the human to discover at the point of ticking. Lines #9, #11 and #12 are honestly
un-tickable today and each carries its own written fallback.

---

## 8. Findings — F-52 … F-58

Continuing the build's sequence; F-51 was the last id issued (`MOCK-DEPLOY-M5.md`).

### F-52 — MEDIUM — Ten manifest members reach no traceability row, and `0 orphan(s)` does not cover it

All 49 `REQ` rows naming a metadata artefact resolve to an `M5-S05` member — check 1 passes in
that direction. **The reverse direction does not.** Ten of the 56 members are named by no row in
`traceability.md`, not even inside an `artefact_paths` cell:

| Type | Members with no traceability row |
|---|---|
| `ApexClass` | `CaseMilestoneService`, `CaseMilestoneServiceTest`, `TestDataFactory` |
| `Group` | `Billing_Team`, `Support_Tier_1`, `Support_Tier_2` |
| `PermissionSetGroup` | `PSG_Billing_Prod`, `PSG_Tier1_Prod`, `PSG_Tier2_Prod` |
| `Report` (folder) | `Support_Operations` |

The eleventh candidate, `EmailFolder:case_intake`, **is** covered — it appears in REQ-032's paths
cell.

`check_rtm.py` reports `0 orphan(s)` and is not wrong: its orphan rule runs **step → row** (does
every step trace back to a requirement), never **member → row**. So no declared test in this build
asserts this direction, which is why it survived to the last gate.

Why it matters more than a bookkeeping note: `PSG_Tier1_Prod`, `PSG_Tier2_Prod` and
`PSG_Billing_Prod` are the access constructs the **entire M2 milestone** rests on and the
constructs every story in `M5-S03` names as its tester's grant. A release owner asking "which
requirement asked for `PSG_Tier1_Prod`?" gets no answer from the compiled RTM. Adjacent rows do
imply the coverage (REQ-017…020 name the permission sets the PSGs compose; REQ-021…024 name the
queues whose membership names the groups; REQ-044 names the trigger the three classes serve), but
implication is not traceability.

**Not a deploy risk** — every one of the ten is in the manifest with a file behind it.

**Recommendation:** accept at G5 as a known RTM-coverage gap and file two items: (a) add
member-level rows at the next doc-keeper touch, and (b) deepen
`skills/admin/requirements-traceability-matrix` so `check_rtm.py` gains a manifest-member
coverage direction when `--manifest-dir` is supplied. The second is the one that stops this
recurring.

### F-53 — MEDIUM — The UAT pack carries two cases on the blocked steps, contradicting the test that certifies it

`M5-S04`'s manual test [5] asserts *"the UAT pack carries no case that depends on either"*
`M3-S05` or `M5-S02`. The pack carries four cases on those two steps, and **two of the four do
depend on artefacts nobody wrote**:

| Case | `evidence.of` | Pass rule reads |
|---|---|---|
| `TC-M3-S05-2` | `artefacts/M3-S05/` — **does not exist** | five Omni-Channel metadata files that were never built |
| `TC-M5-S02-2` | `artefacts/M5-S02/` — **does not exist** | `sandbox-proof-plan.md`'s Post-Refresh Tasks section |

The other two (`TC-M3-S05-1`, `TC-M5-S02-1`) are gate acknowledgements and are tickable now.

**Mitigation already present, and worth weighing:** each of the two carries "Given this step is
unblocked in a later phase" as its literal first step, and `sandbox:` records the block. The signal
is in the record. What is missing is a **structural** marker — both sit at `pass_fail: "Not Run"`
alongside 43 runnable cases with no `phase` or `blocked_on` key, so a tester working the pack in
order meets two cases they cannot run and must read the prose to learn why.

**Recommendation:** accept with the narrowing stated — read `M5-S04[5]` as "carries no case that
*can be mistaken for runnable*", tick it on that basis, and file a planner v6 item that the
compile stamps `phase: 2` / `blocked_on: <step>` on any case derived from a blocked step's manual
test. Do **not** delete the two cases: when the steps unblock, these are exactly the cases that
should run.

### F-54 — HIGH — `M5-S04`'s assumptions manual test is not tickable; 16 of 28 assumptions appear in no compiled document

`M5-S04`'s manual test [4] requires that *"when the workbook's assumptions section is read, then
all 25 [deferred clarifications] appear as named rows with an owner who can close each one, and
each names the steps it constrains — compiled from `assumptions[].steps[]`."* Measured:

| Measurement | Value |
|---|---|
| `## ` sections in `artefacts/M5-S04/configuration-workbook.md` | Compile-time normalizations, Sections 1–10, Other configuration — **no assumptions section** |
| Assumptions in `plan.json` | **28** |
| Deferred clarifications | **25** |
| Assumption ids appearing anywhere in the compiled workbook | **10** (A1, A2, A3, A7, A9, A13, A24, A26, A27, A28) |
| Assumption ids appearing across **all five** compiled documents | **12** |
| Appearing in **none** of them | **16** — A5, A6, A8, A10, A11, A12, A14, A15, A16, A17, A18, A19, A20, A22, A23, A25 |
| Assumptions carrying an `owner` field in `plan.json` | **0** |

`check_workbook.py` exits 0 because its `SECTION_HEADING_RE` validates the ten canonical sections
and nothing asserts the presence of an eleventh. So no automated gate in this build ever looked
for this, and the test that was supposed to catch it is the manual one now being read at the gate.

This is graded HIGH rather than MEDIUM because of what the missing sixteen are. **A17–A22 are
`M5-S02`'s own assumptions** — the sandbox-strategy inputs the blocked step could not get. **A15
and A23** are `M5-S03`'s (deferred Q81/Q82). **A16** is `M5-S04`'s own (deferred Q67). The
assumptions with no owner and no compiled row are disproportionately the ones attached to the work
this build did not do — which is precisely the set a phase-2 owner needs handed to them.

The build **does** carry all 28 assumptions with `text`, `because`, `risk` and `steps[]` in
`plan.json`, so nothing is lost — it is unpublished, not missing.

**Recommendation:** do **not** tick line #3 of the checklist. Either (a) sign the gate recording
the assumptions register as **outstanding**, with a named owner to produce it — the same treatment
the sandbox proof plan gets — or (b) hold G5 for one doc-keeper pass that renders
`plan.json.assumptions[]` into an assumptions section with an owner column. (b) is a cheap fix
against a HIGH finding: the data is structured and on file; only the render is missing. **(b) is
the recommendation.** This is also a planner v6 item — `assumptions[]` needs an `owner` field for
the render to have anything to put in the column.

### F-55 — MEDIUM — `reports/MILESTONE-M1-package.xml` still carries the member the org rejected

```
reports/MILESTONE-M1-package.xml:  <members>Case_Intake</members>   <name>CompactLayout</name>
artefacts/M1-S01/package.xml:      <members>Case.Case_Intake</members>
reports/MILESTONE-M5-package.xml:  <members>Case.Case_Intake</members>
```

The bare `Case_Intake` form is the one `MOCK-DEPLOY-M1.md` mock deploy #3 rejected — *"An object
'Case_Intake' of type CompactLayout was named in package.xml, but was not found in zipped
directory"* (F-13) — and it is the **only defect in this build that manifest-mode validation alone
has ever caught.** It was fixed in the step manifest and in the build-level manifest. The M1
merged manifest under `reports/` was never re-merged and still carries the rejected form.

F-18 flagged the M1 merged manifest as stale at the M2 gate; this report names the specific
defect still in it. The exposure is real and narrow: `M5-S05` § 3.2 names **splitting the release**
as what its order table is for, and a release owner splitting the deploy would reach for the
per-milestone merged manifests under `reports/` — where the M1 one fails on a known-rejected
member.

**Recommendation:** accept at G5 with the hazard named, and either delete
`reports/MILESTONE-M1-package.xml` and `-M2-package.xml` (superseded by
`MILESTONE-M5-package.xml`, which is the whole build) or re-merge them. Deleting is cleaner: a
stale manifest that still parses is more dangerous than an absent one. Add a line to
`artefacts/M5-S05/deploy-order.md` § 3.2 saying a split release is cut from the build-level
manifest's table, **not** from the per-milestone merged files.

### F-56 — MEDIUM — Two independently numbered prerequisite lists, and one prerequisite in neither compiled document

`artefacts/M5-S05/deploy-order.md` § 5.2 numbers six org prerequisites 1–6. `story-backlog.md`
numbers prerequisites **P1–P6** inline in its stories' `Dependencies`. The two lists are numbered
independently, cross-reference each other nowhere, and **do not hold the same items**:

| Prerequisite | `M5-S05` § 5.2 | Backlog |
|---|---|---|
| `support-noreply@acme.example` verified `OrgWideEmailAddress` (F-28) | **#1** | **P4** |
| `enableEntitlements` + `enableMilestoneStoppedTime` (F-39) | **#2** | **P1** |
| Non-routing mailboxes on the Billing / Tier 2 queues (F-44) | **#3** | **P2** |
| An `Entitlement` record per Account (F-41) | **#4** | **absent** |
| Report's "Escalated = True" criterion (F-51) | **#5** | present as prose, no P-number |
| Active `SlaProcess` with a First Response milestone (G4 dec 9) | **#6** | **P5** |
| Escalation-rule activation itself | § 4.1 / § 4.2, not § 5.2 | **P3** |
| Sandbox deliverability above System Email Only + Contact emails scrubbed (Q78) | **absent** | **P6** |

Two consequences. First, "P1" means `enableEntitlements` in one document and
`support-noreply@` is `#1` in the other — a release owner working from both meets the same label
on different things. Second, and the substantive half: **F-41 (an `Entitlement` record per Account
pointing at the right process) appears in the story backlog not at all, and in the compiled
configuration workbook not at all** (zero occurrences of "Entitlement record"). It lives only in
`M5-S05`'s deploy-order note and the M4 report. F-41 is the prerequisite without which
`Support_Tier__c`'s Premier-vs-Standard promise does not bind to anything — the flow's
`Get_Active_Entitlement` filters on `AccountId` and `Status = 'Active'` with **no tier filter**.

**Recommendation:** at G5, adopt `M5-S05` § 5.2's numbering as canonical (it is the document the
release owner deploys from), add P6 (sandbox deliverability) as a seventh item, and add F-41 to
the compiled workbook and to `US-CASE-007`'s dependencies at the next doc-keeper touch. Renumber
the backlog's P-labels to match, or drop them for explicit names.

### F-57 — LOW — The self-referential compile gap, quantified: exactly seven rows

`workbook/99-other-configuration.md` carries rows `CWB-OTHER-037` … `CWB-OTHER-043`. The
**compiled** `artefacts/M5-S04/configuration-workbook.md` stops at `CWB-OTHER-036`.

| Row | Artefact |
|---|---|
| `CWB-OTHER-037` … `041` | `M5-S04`'s own five outputs — `configuration-workbook.md`, `traceability.md`, `deploy-order.md`, `acceptance-criteria.md`, `uat-test-cases.yaml` |
| `CWB-OTHER-042`, `043` | `M5-S05`'s `package.xml` and `deploy-order.md` |

The cause is structural, not an omission: the compile ran at `M5-S04`, and the rows describing
`M5-S04`'s own outputs and `M5-S05`'s were written by doc-keeper passes that ran **after** it.
There is no second compile step to pick them up. `reports/drivers-log.md` named this; the count is
new.

The practical effect is small and worth stating both ways. The compiled workbook — the document
handed to a release owner — documents 43 of the build's non-component artefacts and not the seven
most recent, including **itself**. The data is not lost: the live `workbook/` slices carry all
seven, and `M5-S05`'s deploy-order note describes its own two.

**Recommendation:** accept as-is for this build and file the planner v6 item the drivers log
already proposes — place the compile step **last** in the plan, after the manifest step, so it can
include its own rows. Do not hand-edit the compiled document to close it: `M5-S04` is `documented`
and `agents/build-doc-keeper/AGENT.md` Step 8 leaves another step's rows byte-identical.

### F-58 — LOW — Milestone test 1's declared outcome undercounts the WARNs by one

The test declares *"exit 0, with the SharingRules WARN as the documented outcome"* — singular. At
`--manifest-dir artefacts` the checker recurses over every `package.xml` in the tree and prints
**two**, one for `artefacts/M2-S05/package.xml` and one for `artefacts/M5-S05/package.xml`, for
`score 90` rather than the `95` the step-level fixture recorded. Exit 0 either way, and the
`(0 blocking)` reading is unchanged, so nothing about the verdict turns on it.

The description was written from the step-scoped fixture (`--manifest-dir artefacts/M5-S05`, one
manifest, one WARN) and carried to the milestone-scoped command unchanged, where the tree holds
the sharing rule's own step manifest as well.

**Recommendation:** no action needed on the artefacts. If `M5`'s test description is ever touched,
correct it by `amend-step --prose-only` — the structural fields are right and only the narrated
outcome is off by one.

---

## 9. The eight decision items for the `milestone:M5` (G5) gate

Presented together, each with this agent's recommendation. **Recommendations, not decisions.**

### 1. `M5-S02` and `M3-S05` blocked — accept as phase 2, with owners

**What is being decided:** whether to accept a build that ships no sandbox strategy document and
no Omni-Channel push routing. **Recommend: ACCEPT**, on three conditions, because there is nothing
to be gained by holding — the inputs do not exist and no amount of further building creates them.

- Name an owner and a due date for `team_size`, `concurrent_workstreams`, `release_cadence`,
  `data_sensitivity` (checklist line #8), and record that `sandbox-strategy-designer` refuses at
  its own first step without them.
- Record that Q68's proof — real inbound email, a clock test, a loop test — has **no plan behind
  it**, and that checklist lines #11 and #12 are therefore signed **outstanding, not ticked**.
- Record that Q74's refresh rule (re-point both routing addresses and the form endpoint, or the
  sandbox answers real customer mail) is currently held only in `M5-S05` § 6 and has no home in
  the operational document that would be read at refresh time.

For `M3-S05`: the gap was accepted at G3 and nothing has changed, except that `M5-S01` has now
shipped the interim Tier 1 list view. Confirm that a human decides at phase 2 whether that view is
retired or repurposed (`decisions.md` **D-M5S01-03**) rather than leaving it to become permanent
by default.

### 2. F-28 — the sender prerequisite

**What is being decided:** accepting that one component in this build has failed **every** mock
deploy since M3 run 6, unchanged and expected. **Recommend: ACCEPT as a named deploy prerequisite,
already G3 decision 4** — and add the one thing not yet recorded: a due date.

`support-noreply@acme.example` must be provisioned and **verified** as an `OrgWideEmailAddress`
before `AutoResponseRules:Case` deploys. Two points a release owner should not have to re-derive:
the org validates `senderEmail` against its verified addresses **at deploy time, not at send
time**, so this fails the whole deploy rather than one email; and there is no metadata type for an
org-wide address, so no build can ever ship one. The same provisioning also serves M3-S03's
`systemUserEmail`. The expected single failure on a validation run against an org without it is
`AutoResponseRule Case.Case_Acknowledgement` **and nothing else** — not a reason to stop reading
the result.

One documentation defect remains open beside it: `artefacts/M3-S02/sender-identity-note.md` still
says `support@` where D-M3S04-01 settled `support-noreply@` (F-30, accepted at G3 as a fix at the
next M3-S02 touch). That touch has not happened.

### 3. F-51 — the report filter runbook step

**What is being decided:** shipping a report that **over-reports** — it returns open Cases from
the last 30 days, not escalated open Cases. **Recommend: ACCEPT.** Five candidate column codes
were probed against a real org and all five rejected; `reports-and-dashboards` SKILL.md workflow
step 3 says column codes are harvested from an org retrieve and *"cannot be derived from field API
names"*; this design-only build has no org to retrieve from. Inventing a sixth is refused under
`agents/metadata-builder/AGENT.md` Step 5 rule 1. Blocking the milestone converts an honestly
unresolvable item into an artificial delay.

The disclosure is genuinely thorough and this agent verified each placement: the report's own
219-character `<description>`, an XML comment directly above `<filters>`,
`M5-S01/deploy-order.md` §§ 0 and 2 U1, `M5-S05/deploy-order.md` § 5.2 item 5, the workbook's
`CWB-LAYOUT-011` row, and `story-backlog.md`. A reader in Setup sees it too.

**One thing to fix at the gate:** the owner is "the Tier 2 lead" — the **role** Q91 names, not a
person. Name the person. A runbook step with a role and no name is how post-deploy work is not
done.

### 4. `REQ-055` … `REQ-058` — the `Draft` waivers

**What is being decided:** whether four requirements sitting at `Draft` with no test coverage are
the intended state. **Recommend: ACCEPT all four, and confirm the three specific onward
obligations** rather than ticking the block as a whole.

"Waived by decision NONE" is the checker naming the true state accurately, not an unfinished
waiver: `check_rtm.py`'s waiver condition is the `Draft` **status** itself, not a cited decision id
(`decisions.md` **O-M5S04-03**). Each row's `Draft` is separately justified — `REQ-055` is an
environment precondition raised outside any plan step; `REQ-056`/`REQ-057` are UAT-programme
controls carried in the backlog's shared Background rather than as their own story;
`REQ-058` names a sandbox owner/approver that **cannot exist** while `M5-S02` is blocked.

The three things to confirm, because each is a way one of the four gets lost:
(a) `REQ-055` is raised as a deploy prerequisite rather than forgotten;
(b) `REQ-056`/`REQ-057` are read at **each** UAT session from the shared Background, which is the
failure mode of a control with no story to carry it;
(c) `REQ-058` remains blocked on `M5-S02` and is not silently dropped when item 1 is accepted.

### 5. The self-referential compile gap

**What is being decided:** accepting a compiled workbook that does not document its own five
outputs or `M5-S05`'s two. **Recommend: ACCEPT** — F-57 quantifies it at exactly seven rows, all
seven present in the live `workbook/` slices, none lost. File the planner v6 item: place the
compile step last so it can include its own rows.

**But do not accept F-54 in the same breath.** The two look alike — both are "the compile ran too
early" — and they are not the same severity. F-57 costs seven rows of provenance about documents
the reader is already holding. F-54 costs the **assumptions register**, and sixteen of the missing
assumptions are the ones attached to the work this build did not do. See the recommendation under
F-54: one doc-keeper render closes it, and the data is already structured in `plan.json`.

### 6. The deploy-order divergence

**What is being decided:** which of two documents a release owner sequences from.
**Recommend: `M5-S05`'s order — rules at slot 10, `Settings:Case` at slot 11.** § 4.2 gives the
four grounds; the short version is that `M3-S03`'s own note says so without qualification,
`CWB-AUT-007`'s note gives a reason that argues against its own stated position, and the
compiled table is plan-step order (a record of assembly) rather than dependency order (a deploy
instruction).

Record three qualifications so the divergence is not over-read: both orders deploy cleanly in a
single request; the real safety margin is the **human** step after slot 11 (mail forwarding,
form publication); and Email-to-Case, once enabled, **cannot be disabled**. The divergence matters
only for a split release or an org where forwarding is already live.

Add one line to `M5-S04`'s hazard list at the next doc-keeper touch recording that the conflict
was resolved here and in which direction — the doc keeper was right to report rather than resolve
it, and the resolution should not now live only in this report.

### 7. The four release-owner decisions

**What is being decided:** four questions this build deliberately **defaults none of**
(`decisions.md` **D-M5S05-04**). **Recommend: decide all four before the window, not at it.**

| Question | The position to take, and why |
|---|---|
| `rollbackOnError` | **Set it explicitly `true`, in every environment.** The skill documents production must set it `true`, and the guide contradicts itself on the default (`DeployOptions` says false, `DeployResult` says true) — so an unstated value is a real ambiguity. Treat `SucceededPartial` as a failure in the release gate: a half-landed sandbox is the rehearsal you were using to prove the release safe. |
| `testLevel` | This manifest **carries Apex** — one trigger, three classes — so a production deploy defaults to `RunLocalTests`: every local test, serially, inside the window. **Measure that duration in the sandbox first.** |
| Validation timing | Quick deploy is licensed by a validation against **that target** within **10 days**. Validate close to the window, not early "to be safe." |
| Backout | Deactivate-don't-delete: the two validation rules, the assignment rule, the flow's active version. The escalation rule already ships inactive. **Nobody has agreed to execute this** — assign it. And note that the before-save flow and the trigger write to Cases from the moment they are active, so a backout after real traffic needs a **data** decision, not only a metadata one. |

Two of the six questions in that table **are** answered by the build and need no decision: nothing
is deleted (no destructive manifest, and none wanted), and every component arriving needing a
switch is named in `M5-S05` § 4.

### 8. The version split

**What is being decided:** shipping a build whose step manifests declare two different API
versions. **Recommend: ACCEPT, with no rewrite** — this is already G3 decision 6 and it was right.

A merged manifest at `67.0` and a step manifest at `62.0` record two different facts: what the
step was built and accepted at, versus what the build deploys at. Rewriting the nine would misstate
that history. And `67.0` is not a preference — `MOCK-DEPLOY-M3.md` run 4 proved the floor:
`newEntityRecordType` is invalid at `62.0` and at `63.0`, so M3-S03's `Settings:Case` cannot deploy
below `64.0` at all.

**One thing this report adds:** the nine `62.0` manifests were checked, not assumed. Everything in
them validated **at 62.0** in `MOCK-DEPLOY-M1.md` and `MOCK-DEPLOY-M2.md` run 3 (32 components,
0 errors), so a split deploy per step carries no latent version risk.

The open item is a plan-level `api_version` field (`build-planner` v6), so a future build does not
have to reconstruct this from nine step manifests and a gate note the way `M5-S05` did.

---

## 10. Requirement closure (Step 7 / traceability)

`artefacts/M5-S04/traceability.md` — **58 rows**, byte-consistent with the build-root
`traceability.md` (same 58 ids, same step / artefact / status on every one; independently
diffed by this run). **0 orphans, 0 errors.**

| Status | Rows |
|---|---|
| `In UAT` | 35 |
| `In Build` | 19 |
| `Draft` | 4 — `REQ-055` … `REQ-058` |

**M5 contributes 11 rows:** `REQ-048`, `REQ-049`, `REQ-050` (`In UAT`) and `REQ-051` (`In Build`)
from `M5-S01`; `REQ-052`, `REQ-053`, `REQ-054` (`In UAT`) and `REQ-055` … `REQ-058` (`Draft`)
from `M5-S03`.

**No requirement in this build reaches a terminal status, and that is correct rather than a gap.**
The ladder tops out at `In UAT` because UAT has not run — `M5-S02` is blocked and there is no
sandbox. What M5 closes is the **build** of every requirement it owns, not their acceptance.

Two requirements remain materially open regardless of the gate decision:

- **`REQ-022`** — its push half is undelivered (`M3-S05` blocked). The queue exists; the
  Omni-Channel routing that pushes from it does not. `M5-S01`'s Tier 1 list view is the interim
  surface.
- **`REQ-058`** — names a sandbox owner and approver that cannot exist while `M5-S02` is blocked.
  It is `Draft` for that reason and will stay `Draft` until item 1 is worked.

`REQ-052` … `REQ-058` were minted by `story-drafter` continuing from `REQ-051`, and
`build-doc-keeper` adopted them unchanged. They collide with nothing. The standing gap
(`decisions.md` **O-M5S03-01**) is that **no writer owns the `REQ-` sequence** for a build —
a planner v6 contract item, not a defect in these ids.

---

## 11. Optional validate-only command — for the human, and this agent did not run it

**This agent ran no `sf` command and no `mock_deploy.py` invocation.** Everything below is text to
copy. The org evidence in § 6.1 was **read from `reports/MOCK-DEPLOY-M5.md`**, not produced here.

The build is `design-only` — `plan.json` carries no `org`, so no alias exists on file. Supply your
own. **For a sandbox target**, the validate-only form is a dry run, which compiles and validates
without saving:

```bash
# From the repo root. Manifest mode is the only check that reads a merged package.xml.
python3 scripts/mock_deploy.py .sfskills/builds/case-onboarding/plan.json \
  --org-alias <your-alias> \
  --mode manifest
```

`mock_deploy.py` hard-codes `--dry-run` (`checkOnly: true`) and has no deploy option. Its
`summary.md` under `reports/mock-deploy/<ts>/` is § 5 evidence for the gate.

Or the CLI directly, against the manifest this report merged:

```bash
sf project deploy start --manifest .sfskills/builds/case-onboarding/reports/MILESTONE-M5-package.xml \
  --dry-run --target-org <sandbox-alias>
```

**For a production target the command is different**, and naming the wrong one sends a human into
an error that has nothing to do with their build:

```bash
sf project deploy validate --manifest .sfskills/builds/case-onboarding/reports/MILESTONE-M5-package.xml \
  --test-level RunLocalTests --target-org <production-alias> --wait 60
```

Salesforce documents `deploy validate` as **production-only**; it requires Apex tests and returns
a job id for a later `sf project deploy quick` inside a **ten-day** clock.

**Expect exactly one failure** on any org without a verified `support-noreply@acme.example`:
`AutoResponseRule Case.Case_Acknowledgement` (F-28). That single expected failure is not a reason
to stop reading the result.

---

## 12. What this run recorded, and the gate line

### The `set-milestone` invocation — the one plan write this agent made

```bash
python3 scripts/build_plan.py set-milestone .sfskills/builds/case-onboarding/plan.json M5 \
  --status rejected --report-path reports/MILESTONE-M5-REPORT.md
```

`rejected` is Step 9's mapping for a `not-ready` verdict and is **plan bookkeeping, not a gate
decision**. No gate record was written. `gate milestone:M5 approve` is not blocked by it — § 3's
preconditions read the preceding gate and the step statuses, both of which are satisfied.

### The gate line — **for a human to run. This agent did not run it.**

```bash
python3 scripts/build_plan.py gate .sfskills/builds/case-onboarding/plan.json milestone:M5 approve --by "<name>"
```

§ 3 checks this command against three conditions, all of which hold today:

| Condition | State |
|---|---|
| `plan` gate approved | ✅ 2026-09-05T19:35:19Z |
| `milestone:M4` approved | ✅ 2026-09-12T09:23:14Z |
| Every step in M5 `documented`, or `blocked` with a recorded reason | ✅ four documented; `M5-S02` blocked with a reason, **which the command will print** |

**Approving anyway accepts that gap**, and approving with the recommendations above unchanged
accepts F-54 as well. If the release owner prefers to close F-54 first, that is one doc-keeper
render against data already on file — not a rebuild.

To reject instead:

```bash
python3 scripts/build_plan.py gate .sfskills/builds/case-onboarding/plan.json milestone:M5 reject --by "<name>"
```

**This is the thirteenth and last gate. Approving it takes the build to `done`.**

### Files this run wrote — and nothing else

| Path | What |
|---|---|
| `reports/MILESTONE-M5-REPORT.md` | this document |
| `reports/MILESTONE-M5-package.xml` | the merged milestone manifest — 29 types, 56 members, `67.0` |
| `envelopes/M5/2026-09-12T12-52-10Z.json` / `.md` | this run's envelope and its markdown twin |
| `plan.json` | `milestones[M5].status` and `.report_path`, via `set-milestone` only |

No artefact, test result, workbook slice, decision record or envelope written by another agent was
edited, moved or deleted. No org was contacted. No gate was written.

Per the deliverable contract's persistence-path override, this run's own report pair lives under
the build directory rather than `docs/reports/milestone-verifier/`, at the caller's explicit
instruction to write only under the build dir.

---

## 13. Process observations

**Healthy.** The org was the last reviewer in this milestone as it was in every one before it, and
the loop responded correctly each time. `M5-S01` took eight runs because `MOCK-DEPLOY-M5.md` run 1
rejected the report on a 255-character `<description>` and the operator's probes then rejected the
skill's own worked-example `reportType` and grouping values — three facts no checker in this
library encodes. The rebuild applied the org's own answers and run 2 validated 60/60.
`decisions.md` **O-M5S01-01** then says the uncomfortable part out loud: both declared checkers
scored the rejected file and the fixed file **identically**, so a reviewer reading only checker
output would have seen no difference. Recording that, rather than quietly banking the pass, is the
behaviour that makes the rest of this build's evidence trustworthy.

**Healthy.** `D-M5S03-04` records `story-drafter` checking every `skills/…` path it had written
against the registry before finalising, finding three plausible-but-nonexistent names
(`admin/web-to-case-and-email-to-case`, `admin/queue-design`, `apex/trigger-handler-pattern`) and
correcting all three. That is the exact fabrication class `AGENT_CONTRACT.md` rule 12 exists to
stop, caught by the agent itself, at the one moment it is cheapest to fix.

**Concerning — `plan.json` carries no `scale` field at all.** § 3.1 says an absent `scale` means
`project`, so the ceremony applied was correct, and `reports/drivers-log.md` records the intent in
prose ("scenario 1: an entire project at `scale: project`"). But **no sizing line was ever
recorded** — no D/S/O/X counts from the clarifier, no override note. The `AGENT.md` Output Contract
asks this agent to flag `scale` disagreeing with the counts; here there is nothing to compare
against. This build would have measured D ≥ 7, S ≥ 9, O ≥ 4 and integration implied, so `project`
is unambiguously right — which is precisely why the missing line costs nothing here and would cost
a great deal on a build near a tier boundary. This is the last milestone, so this is the last
chance to say it.

**Concerning — the compile ran before the build finished, twice over, in two different severities.**
F-54 and F-57 are the same structural cause: `M5-S04` compiles, then `M5-S05` runs, then
doc-keeper writes rows the compile can never see. F-57 is cosmetic. F-54 is not, and the reason
it is not is worth generalising: the compile also never rendered
`plan.json.assumptions[]` at all, so the gap is not only "seven rows arrived late" but "one whole
register was never in scope." A compile step placed last fixes the first and not the second.

**Concerning — nine consecutive steps shipped an undeclared artefact.** Every step from `M3-S02`
through `M5-S01` produced a `deploy-order.md` that its `outputs[]` never declared
(`decisions.md` **O-M3S02-03**, and the workbook keeps a running count). `check-outputs` reads the
filesystem, so no step ever failed on it, and the G4 gate accepted the pattern explicitly. The
cost is that the plan's declared surface understates what the build produced — which matters here
because these are the files a release owner actually reads.

**Ambiguous — the four `Draft` rows read as an unfinished waiver and are not one.** "Waived by
decision NONE" is `check_rtm.py` naming the `Draft`-status waiver rule accurately. A gate reviewer
reading the checker output alone would reasonably conclude someone forgot to cite a decision. The
build already anticipated this (`O-M5S04-03`), which is the right response; the underlying
checker message is what invites the misreading.

**Ambiguous — 111 `check_ac_format.py` WARNs, almost all on a persona that correctly has no
permission construct.** The compiled acceptance-criteria document carries 39 build-process
meta-criteria whose persona is a "Build/milestone-gate reviewer" — criteria about whether a file
exists or a checker exited 0, not about what a Salesforce user can do. Gotcha 5's rule fires on
every one. `O-M5S04-04` accepts them as expected and refuses to invent a Profile to clear the
WARN, which is right. The residual ask stands: **someone should spot-check that none of the 111
hides a genuine end-user criterion still missing a named PSG.**

**Ambiguous — four stories over three channels.** `M5-S03`'s manual test says "each of the three
intake channels has its own story"; the backlog ships four, splitting email because Q77 gives
Billing its own named tester. `story-drafter` flagged its own reading as ambiguous rather than
asserting it. Checklist line #2 is where a human settles it, and this agent's reading is that the
split is right — merging them would produce the persona drift gotcha 3 warns against.

**Suggested follow-ups.** `deployment-risk-scorer` once the human has an org: it would put a number
on the six org prerequisites in F-56 and on the `RunLocalTests` window that G5 item 7 asks a human
to measure — this agent can name them but cannot weigh them without a target.
`release-readiness-reviewer`: M5 is the last milestone before a release, which is exactly the
condition that agent exists for, and the four undecided release options in item 7 are its subject
matter. **Recommendations only — this agent invoked neither and will not.**

---

## 14. Citations

| Type | Id | Used for |
|---|---|---|
| standard | `AGENT_RULES.md` | run-time rules for this invocation: never write to an org, never chain |
| standard | `agents/_shared/AGENT_CONTRACT.md` | 8-section shape, Process Observations, confidence rubric |
| standard | `agents/_shared/DELIVERABLE_CONTRACT.md` | atomic-write rule; the persistence-path override used in § 12 |
| standard | `agents/_shared/REFUSAL_CODES.md` | the refusal enum — checked and not triggered (§ 1.3, § 5.2) |
| standard | `standards/build-orchestration.md` | § 2 (report written not rendered; `set-milestone --report-path`), § 3 (G5 preconditions; blocked-with-a-reason), § 3.1 (absent `scale` = `project`), § 4 (borrowed-agent rule behind M5-S02's block), § 5 (milestone scope is always `build`; the deploy deny-list; the Apex exception), § 7 |
| schema | `agents/_shared/schemas/build-plan.schema.json` | milestone / gate / step fields read |
| skill | `admin/requirements-traceability-matrix` | how closure is stated (§ 10); the `Draft`-status waiver rule behind item 4; the id-immutability convention behind `REQ-052`…`058` |
| skill | `admin/uat-and-acceptance-criteria` | the form a manual test must take to be tickable by someone who was not in the build loop (§ 7, and the F-54 / F-53 readings) |
| skill | `devops/metadata-api-retrieve-deploy` | manifest grammar, the `<version>` element, folder-qualified and object-qualified member forms (§ 5) |
| skill | `devops/permission-set-deployment-ordering` | the `fieldPermissions`-before-the-field failure checked for and not found (§ 4.1) |
| skill | `devops/flow-deployment-activation-ordering` | automation's position and arrival state — the flow at slot 14, the escalation rule inactive at slot 16 (§ 4.1) |
| skill | `devops/deployment-error-diagnosis` | the deploy-time error each unresolved reference would produce; the F-13 / F-55 `not found in zipped directory` shape |
| skill | `devops/pre-deployment-checklist` | the go/no-go items § 9 items 2, 3, 7 and § 11 must cover |
| artefact | `artefacts/M5-S05/deploy-order.md`, `artefacts/M5-S04/deploy-order.md`, `artefacts/M3-S03/deploy-order.md` | the § 4.2 divergence and its resolution |
| artefact | `decisions.md` D-M5S01-01…03, O-M5S01-01/02, O-M5S03-01/05, D-M5S03-04, D-M5S04-01/02, O-M5S04-03/04, D-M5S05-01…05 | the recorded decisions this report re-checks rather than re-derives |
| artefact | `reports/MOCK-DEPLOY-M5.md`, `reports/MOCK-DEPLOY-M3.md`, `reports/MOCK-DEPLOY-M1.md` | org evidence in § 6.1, the API floor in § 5.3, F-13 in F-55 |
| artefact | `plan.json.human_gates` (`milestone:M3`, `milestone:M4`) | G3 decision 6 (API 67.0); G4 decisions 1, 2, 7, 9 and the F-43 note |
| artefact | `reports/drivers-log.md` | read-only; the compile-gap and manifest-step-carve-out notes it recorded before this run |

---

*End of report. The G5 decision is the human's. This agent verified, recorded a verdict, merged a
manifest, and printed a command it did not run.*
