# Deploy order — M5-S01 (Case queue list views, the escalation monitoring report and its folder)

Written by `agents/metadata-builder` on every run, per its AGENT.md Step 7. **Nothing in this
build deploys.** The command in § 6 is validate-only text for a human to copy; this agent ran no
`sf` command of any kind.

**Note on declaration:** this file is *not* in `plan.json` `steps[M5-S01].outputs[]` — six paths
are declared (three list views, the report, the report folder, `package.xml`). It is written
anyway because the human's deploy reads it, the same undeclared-`deploy-order.md` pattern
`decisions.md` **O-M3S02-03** records for `M3-S01`..`M3-S04` and every M4 step, and which the G4
gate note accepted explicitly ("deploy-order.md undeclared on every M4 step (planner v6
declares it)"). It is reported again in this run's envelope as an undeclared artefact.

---

## 0. Rebuild record — F-49, F-50, F-51 (the org rejected the report)

This step was built at `2026-09-12T09-34-00Z`, tested (4 automated, 0 failed, 1 manual deferred),
and then **rejected by the org**. `reports/MOCK-DEPLOY-M5.md` run 1 — `checkOnly`, `sfskills-dev`,
API 67.0, 60 components, 59 ok, 2 errors (the second is F-28, unchanged) — failed with:

```text
Report Support_Operations/Escalated_Open_Cases: Value too long for field: Description maximum length is:255
```

**What run 1 also settled, and it is worth saying first: the list views and the folder validated.**
All three `ListView` files and `ReportFolder Support_Operations` passed — **including the folder at
its declared filename** `Support_Operations-meta.xml`. § 3 below is therefore a checker-recognition
gap, not a deploy defect; that section is corrected in place.

**F-49 (HIGH, build + skill).** The `09-34-00Z` build put its UNVERIFIED note into the report's
`<description>`; the field is capped at 255 characters.
`skills/admin/reports-and-dashboards` carries no description-length rule — the library's DESC rule
family covers `PermissionSet` / `Profile` / `CustomPermission` / `CustomObject`, and `Report` needs
one. Recorded for the skill; **not** fixed here, because this agent does not edit skills.

### Operator probe table — what the org said next (scratch copy; nothing in the build changed)

With the description shortened, validation moved into the report body. Verbatim from
`reports/MOCK-DEPLOY-M5.md`:

| Probe | Result |
|---|---|
| `<reportType>Cases</reportType>` (the skill's UNVERIFIED value) | `invalid report type` |
| `<reportType>CaseList</reportType>` | **accepted** — validation moved to the grouping |
| grouping `USERS.NAME` (from the skill's example) | `Grouping: Invalid value specified: USERS.NAME` |
| grouping `OWNER` | **accepted** — next error: `You can't include groupings in the selected columns list: PRIORITY` |
| grouping `OWNER_NAME` | invalid |
| escalated filter column `ESCALATED`, `IS_ESCALATED`, `CASES.ESCALATED`, `ISESCALATED`, `CASE_ESCALATED` | all `filters-criteriaItems-column: Invalid value specified` |

**F-50 (HIGH, build + skill).** Three facts, all previously UNVERIFIED in this file and all sourced
from the cited skill's own worked example, are now proven live: the standard Case report type's API
name is **`CaseList`**, not `Cases`; the owner grouping column is **`OWNER`**, not `USERS.NAME`; and
a field may not be both a `<columns>` entry and a `groupingsDown` field.

**F-51 (MEDIUM, unresolved, and now a runbook step rather than a gap).** The `Case.IsEscalated`
report column code was not found by probing — five candidates rejected. Per the skill's own rule
codes are harvested from a retrieve of an existing report, and this build has none to retrieve. The
criterion therefore **stays out of the file** and becomes a post-deploy action; see § 2 U1, which is
rewritten around it.

### What changed in this rebuild, and nothing else

| File | Change |
|---|---|
| `reports/Support_Operations/Escalated_Open_Cases.report-meta.xml` | `<description>` cut to 219 characters (the notes it carried now live here); `<reportType>` `Cases` → `CaseList`; first `groupingsDown` `USERS.NAME` → `OWNER`; `<columns><field>PRIORITY</field></columns>` **removed** (PRIORITY stays as the second grouping, which is what `M4-S04`'s note asks for); the XML comment retitled to F-51 and shortened |
| `objects/Case/listViews/*.listView-meta.xml` (×3) | **byte-identical** — sha256 unchanged |
| `reports/Support_Operations-meta.xml` | **byte-identical** — sha256 unchanged |
| `package.xml` | **byte-identical** — sha256 unchanged |
| `deploy-order.md` | this § 0; § 2 and § 3 corrected in place |

The report's column list is now `STATUS` and `CREATED_DATE`, with `OWNER` and `PRIORITY` as the two
groupings. Dropping `PRIORITY` from `<columns>` rather than from the groupings is deliberate:
`M4-S04`'s monitoring note § 2 specifies *"Grouping: Case Owner, then Priority"*, so the grouping is
the half that carries the requirement, and a grouped field still shows its value in the group
header.

**Not yet validated:** no run has taken this report past the columns error, so the filter is
unproven — `STATUS notEqual Closed` and `CREATED_DATE equals LAST_N_DAYS:30` (§ 2 U2, U3) have not
been accepted by an org. The probes that injected an escalated criterion reported an error naming
only the injected column, which is *consistent with* the other two being accepted but is not a
validation of them. Run 2 is what settles it.

---

## 1. What this step produces

| Component | Type | package.xml member | Source shape |
|---|---|---|---|
| `objects/Case/listViews/Tier_1_General_Queue.listView-meta.xml` | `ListView` | `Case.Tier_1_General_Queue` | `list-views-and-compact-layouts/references/metadata-examples.md` § 1 |
| `objects/Case/listViews/Tier_2_Queue.listView-meta.xml` | `ListView` | `Case.Tier_2_Queue` | same, plus § 2 for `filters` / `sharedTo` |
| `objects/Case/listViews/Billing_Queue.listView-meta.xml` | `ListView` | `Case.Billing_Queue` | same |
| `reports/Support_Operations-meta.xml` | `ReportFolder` | `Support_Operations` (bare, under `<name>Report</name>`) | `reports-and-dashboards/references/metadata-examples.md` § 4 |
| `reports/Support_Operations/Escalated_Open_Cases.report-meta.xml` | `Report` | `Support_Operations/Escalated_Open_Cases` | same, § 2 |

`<version>67.0</version>`, the build API version confirmed at the M3 gate (decision 6 on
`human_gates[milestone:M3]`, finding **F-31**), matching `M3-S01`..`M4-S05`. The plan itself still
carries no plan-level `api_version` key — that is the planner-v6 item the same gate note records,
and it is why this value is read from the gate decision rather than from a plan field.

Enumerated `ListView` members are object-qualified (`Case.Tier_2_Queue`) and the type accepts no
`*`; `Report` accepts no `*` either, and its folder is retrieved by listing the folder as a bare
member under `<name>Report</name>` — there is no `ReportFolder` entry in `describeMetadata()`
(`reports-and-dashboards/references/metadata-examples.md` § 5).

---

## 2. UNVERIFIED — read this before the report is deployed, scheduled or subscribed

Per the step's grounding rule, anything the cited skills leave unstated is marked here rather than
guessed. **Three items below were settled by the org on 2026-09-12 and are marked RESOLVED**
(§ 0 carries the probe table); the rest still stand. **U1 is not a footnote: as written, the report
does not yet answer Q91.**

### U1 (open — now a post-deploy runbook step) — the Escalated criterion is ABSENT

`artefacts/M4-S04/escalation-monitoring-note.md` § 2 specifies the filter as
`Escalated = True` **AND** `Closed = False` **AND** `Date/Time Opened = LAST 30 DAYS`. The first
of those three is **not in the file**, and after F-51 it is not going to be until someone reads the
code off a real report.

Report column codes are report-type specific and are not field API names
(`reports-and-dashboards/SKILL.md` workflow step 3: *"Retrieve before you write… cannot be derived
from field API names"*; `references/metadata-examples.md` § 2: *"Never guess these"*). No file in
`skills/admin/reports-and-dashboards` carries a code for `Case.IsEscalated`, and the operator's five
probe candidates — `ESCALATED`, `IS_ESCALATED`, `CASES.ESCALATED`, `ISESCALATED`, `CASE_ESCALATED` —
were each rejected with `filters-criteriaItems-column: Invalid value specified`
(`reports/MOCK-DEPLOY-M5.md`, F-51). Inventing a sixth is refused under
`agents/metadata-builder/AGENT.md` Step 5 rule 1.

**Consequence, stated plainly:** the deployed report returns **open Cases from the last 30 days**,
not **escalated** open Cases. It over-reports. A reviewer who reads the report name and trusts the
row count gets the wrong number, and the failure is silent. The same sentence is in the report's
`<description>`, so it is visible in Setup and not only here.

**This is now a deploy-runbook step, not a pre-deploy blocker.** Deploy the report as written, then
do **one** of these before anyone reviews its output:

1. **In the report builder** (no metadata round-trip): open *Escalated Open Cases*, add the filter
   `Escalated equals True`, save. Then re-export the report
   (`sf project retrieve start --metadata "Report:Support_Operations/Escalated_Open_Cases"`) and
   commit the retrieved file, so source and org stop disagreeing — and so the harvested column code
   enters the repo, where the next build gets it for free.
2. **Harvest first, deploy once**: retrieve any existing saved Case report from the target org,
   read the *Escalated* column code off it, add the criterion as a third `<criteriaItems>` block
   and change `<booleanFilter>1 AND 2</booleanFilter>` to `1 AND 2 AND 3` (the element indexes
   `<criteriaItems>` by document order — reordering the blocks rewires the logic silently), then
   deploy.

```bash
sf project retrieve start --metadata "Report:<AnyFolder>/<AnyExistingCaseReport>" --target-org <alias>
```

The equivalent SOQL, for a reviewer who wants the number before either path is done, is in
`artefacts/M4-S04/escalation-monitoring-note.md` § 3.

**Do not substitute `Status = Escalated`.** The Case status ladder built in `M1-S01`
(`businessProcesses/Support_Process`) does carry an `Escalated` value, and it is a *different*
thing from the `IsEscalated` checkbox the escalation engine sets. `M4-S04`'s note is explicit that
`IsEscalated` is the signal being monitored.

### U2 (partly RESOLVED) — the report's column and grouping codes

- **RESOLVED, live:** the owner grouping column is **`OWNER`**. The skill's example value
  `USERS.NAME` is rejected (`Grouping: Invalid value specified`), and so is `OWNER_NAME` (F-50).
- **RESOLVED, live:** a field may not appear as both a `<columns>` entry and a `groupingsDown`
  field — `You can't include groupings in the selected columns list: PRIORITY`. `PRIORITY` is now a
  grouping only.
- **Still open:** `STATUS` and `CREATED_DATE`, as `<columns>` entries and as `criteriaItems`
  columns, have **not** been accepted by an org — no run has taken this report past the columns
  error. They are quoted from the skill's worked examples, which mark the whole code list
  UNVERIFIED. Run 2 settles them.

### U3 (still open) — the `LAST_N_DAYS:30` operator pairing

`references/examples.md` pairs `LAST_N_DAYS:30` with `lessOrEqual` to mean *older than 30 days*.
The file uses `equals` to mean *within the last 30 days*, which is the reading `M4-S04`'s note asks
for, and which no cited file demonstrates. `INTERVAL_LAST30` on `timeFrameFilter` was the
alternative and is not in the documented interval list either. Validation has not reached the
filter yet, so this is unproven in both directions.

### U4 (RESOLVED) — `<reportType>`

The standard Case report type's API name is **`CaseList`**. The skill names it in prose as
*"Cases (Standard Report Type)"*, and `<reportType>Cases</reportType>` is rejected outright with
`invalid report type` (F-50). The file now carries `CaseList`, proven live.

Worth keeping in view: the checker cannot catch a wrong value here — `check_report_source` compares
`reportType` only against `*.reportType-meta.xml` files in the same tree, and a **standard** report
type has none, so the comparison is skipped. Both `Cases` and `CaseList` score 100 with 0 findings.
Only the org distinguishes them.

### U5 (still open) — `<scope>` is deliberately absent

`scope` is a third narrowing layer on top of record sharing and is report-type dependent; the guide
lists `MyAccounts` / `MyTeamsAccounts` / `AllAccounts` for Accounts reports and nothing for Cases
(`references/metadata-examples.md` § 2). Omitted rather than guessed. With OWD Private on Case
(`M1-S01`), the rows a Tier 2 lead sees are already bounded by sharing.

### U6 (still open, but the views themselves validated) — list-view column tokens

`CASES.CASE_NUMBER`, `CASES.SUBJECT`, `CASES.PRIORITY`, `CASES.STATUS`, `ACCOUNT.NAME` and
`LAST_UPDATE` are the tokens from
`list-views-and-compact-layouts/references/metadata-examples.md` § 1, which marks them UNVERIFIED:
standard-field list-view columns are **legacy tokens, not API names**, and the guide publishes no
per-object list. All three views **validated against the org** in `MOCK-DEPLOY-M5.md` run 1, so the
tokens are at least accepted at deploy time — but a wrong token renders a **blank column** rather
than failing, so deploy validation is not evidence that each column shows data. Confirm by opening
one view per persona during the sandbox proof. `Severity__c` on the Tier 2 view is the documented
custom-field form (SKILL.md workflow step 3: *"Custom fields use their API name; standard fields do
not"*) and is read from `artefacts/M1-S01/objects/Case/fields/Severity__c.field-meta.xml`.

### U7 (still open) — `<field>` vs `<filter>` inside `<filters>`

The skill records the contradiction in the guide itself: the `ListViewFilter` field table names
the element `filter` while the guide's own `ListView` sample uses `<field>`. The sample's form is
used here, and the three views carrying it validated in run 1 — which settles that the form is
*accepted*, not that the filter *matches* the rows intended. Confirm by opening a view.

## 3. The declared folder filename is a checker-recognition gap, not a deploy defect

**Corrected after `MOCK-DEPLOY-M5.md` run 1.** The earlier version of this section read the
filename mismatch as a possible deploy problem. It is not: `ReportFolder Support_Operations`
**validated against the org at its declared filename** `reports/Support_Operations-meta.xml`, in
the same run that rejected the report. What remains is a gap in the checker, and it is narrower but
still real.

`plan.json` declares the folder at `reports/Support_Operations-meta.xml`.
`check_report_inventory.py` recognises a folder only by the suffixes
`.reportFolder-meta.xml` / `.dashboardFolder-meta.xml` (`FOLDER_SUFFIXES`, line 29). Measured from
the build directory:

| Folder filename | Checker result |
|---|---|
| `Support_Operations-meta.xml` (as declared, what shipped and what the org accepted) | `Scanned 1 report/dashboard file(s); 0 finding(s)` — exit 0 |
| `Support_Operations.reportFolder-meta.xml` (scratchpad copy) | `Scanned 2 report/dashboard file(s); 0 finding(s)` — exit 0 |

So the folder file is **invisible** to the test the plan declares for it. The step's
`acceptance_tests[1]` reads *"The report sits in a named folder with declared sharing, not in a
personal folder"* — the `accessType` / `folderShares` / `Public`-folder checks
(`check_folder_source`) never execute at the declared filename. The test still passes, because the
report file alone keeps `scanned` above zero, so the W09 empty-directory guard quoted in the test
description does not catch this either.

Two remedies, both a human's, and neither is urgent now that the deploy question is answered:

1. Deepen `admin/reports-and-dashboards` so its checker recognises the bare `<Folder>-meta.xml`
   form as well — the org accepts it, so the checker should too. This is the better fix: it keeps
   the plan's declared path and closes the gap for every future build.
2. Or the M5 gate accepts the folder's `accessType Shared` + one `folderShares` entry on a human
   read of the file rather than on a checker result — in which case say so in the gate notes,
   because no automated evidence for it exists.

## 4. Order — what must already be in the org

| # | Component | Built by | Why it must precede this step |
|---|---|---|---|
| 1 | `Group:Support_Tier_1`, `Support_Tier_2`, `Billing_Team` | `M2-S04` | Each view's `<sharedTo><group>`. A share naming a group that does not exist fails on the reference |
| 2 | `Queue:Tier_1_General`, `Tier_2_Engineering`, `Billing` | `M2-S04` | Each view's `<queue>`, by **developer name** (`Tier_2_Engineering`, not the `Tier 2 Engineering` label). The cited skill: *"the `Queue` metadata must exist in the target org first"* |
| 3 | `CustomObject:Case` + `Case.Severity__c` | `M1-S01` | The views live inside the object; the Tier 2 view names the custom field as a column |
| 4 | `CompactLayout:Case.Case_Intake` and its `compactLayoutAssignment` | `M1-S01` | Not a deploy dependency of these views, but it is what makes this step's build-scoped checker pass — see § 5 |
| 5 | Standard **Cases** report type, i.e. Service Cloud Cases in use | org feature | The report names it in `<reportType>` |

Within this step, one ordering rule: **the folder deploys before the report inside it.** A single
`package.xml` deploy resolves that itself (`reports-and-dashboards/references/metadata-examples.md`
§ 6); splitting it across two deploys does not.

Nothing else in the build depends on this step's artefacts, with one exception recorded in the
plan: `M5-S03` `depends_on` `M5-S01`, and `M5-S05` aggregates these members into the build-level
manifest.

---

## 5. Decisions worth reading before deploy

1. **A Tier 1 General queue list view is built even though Tier 1 is meant to have work *pushed*
   to it.** Q31's answer is explicit that Tier 1 gets Omni-Channel push and that Billing and Tier 2
   pull from a list. `M3-S05` (Omni-Channel) is **blocked** on Q32–Q35, so no push routing ships
   this phase; assumption **A7** commits the plan to the Tier 1 pull view as the interim working
   surface. When Q32–Q35 are answered and `M3-S05` ships, decide deliberately whether this view
   stays as a supervisor overflow surface or is retired — it is not automatically obsolete, but it
   is no longer the intended Tier 1 workflow.

2. **Every queue already auto-creates a list view.** The skill's Questions-to-Ask row *"Is this view
   meant to follow a queue?"* offers two answers: author a view naming the queue, or use the
   auto-created one instead of authoring a rival. This step authors three, because the plan
   declares three and because the auto-created view carries neither the `Status != Closed` filter
   nor a reviewed column set. Expect **two** views per queue in the org after deploy (the
   auto-created one and this one), and expect the post-deploy `ListView` SOQL in
   `references/metadata-examples.md` § 7 to return developer names nobody in this build authored.
   Naming the rival is the governance decision; it is recorded here rather than discovered later.

3. **Each view carries an explicit `sharedTo` group rather than being public.** Gotcha 6: a missing
   `sharedTo` element means **public**, and the widest audience is the one with no markup to
   review. The three groups are the queue-member groups `M2-S04` already built, so the audience of
   each view is exactly the team that works that queue.

4. **`Status != Closed` on all three views.** Queue scope bounds the view to cases the queue owns,
   including closed ones; the filter is what makes it a working surface rather than an archive.
   `Closed` is a real value on both business processes (`M1-S01`
   `businessProcesses/Support_Process`, `Billing_Process`).

5. **The report has no dashboard, no subscription and no running user.** Q91 asks for a saved
   report reviewed weekly by the Tier 2 lead, and that is what this is. Note before anyone adds a
   subscription: a subscription sends the **running user's** rows to every recipient, not each
   recipient's own (SKILL.md § gotchas). The weekly review is a human opening the report, which is
   what `M4-S04`'s monitoring note describes.

6. **The folder grants `View` to `Support_Tier_2` and nothing else.** Q91 names a role (*"the
   Tier 2 lead"*), not a person, and no admin or ops group exists in this build to hold a `Manage`
   share — inventing one was refused on the same grounds as `decisions.md` **D-M2S04-02**. The
   folder owner and users with administrative permissions retain access regardless. If Support Ops
   should administer the folder, that is one `folderShares` block and an answer nobody has given
   yet.

7. **Q65 is deferred (assumption A14), so this is the only report in the phase.** Nothing here
   attempts a reporting backlog; the one report Q91 names is built and nothing else.

8. **What `M4-S04`'s note asked for and this file could not carry.** Its § 2 column list names
   Case Number, Priority, Status, Date/Time Opened, Last Modified Date, Business Hours and
   Severity. The file carries `STATUS` and `CREATED_DATE` as columns and `OWNER` / `PRIORITY` as
   groupings — Priority moved from the column list to the grouping in the F-50 rebuild, because the
   org rejects a field that is both. Case Number, Last Modified Date, Business Hours and Severity
   have no report column code in any cited file (U2), so they are absent rather than guessed. Add
   them from the same retrieve that closes U1 — `Business Hours` in particular is what tells a
   reviewer that a row was measured on an unverified clock (`M4-S04` runbook § 4, R1).

---

## 6. Validate-only command (text for a human; this agent ran nothing)

```bash
sf project deploy start \
  --source-dir .sfskills/builds/case-onboarding/artefacts/M5-S01 \
  --target-org <alias> \
  --dry-run
```

Then validate the **manifest** as well — `--source-dir` derives members from the files on disk and
can never disagree with them, so it cannot catch a wrong `<members>` value; only `--manifest` can.
That is the trap `MOCK-DEPLOY-M1.md` mock deploy #3 caught on `CompactLayout Case.Case_Intake`, and
`ListView` takes the same object-qualified form:

```bash
sf project deploy start \
  --manifest .sfskills/builds/case-onboarding/artefacts/M5-S01/package.xml \
  --target-org <alias> \
  --dry-run
```

Deploy the § 4 prerequisites first — a missing queue or group fails the deploy on the reference,
not on the view. `sf project deploy validate` is documented for **production** orgs and requires
Apex tests; against a sandbox use `--dry-run` as above.
