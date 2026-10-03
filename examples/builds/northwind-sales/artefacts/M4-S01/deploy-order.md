# Deploy order: M4-S01, the report-type and column-code probe runbook

Build: `northwind-sales` · Milestone: M4 (pipeline visibility, the handover pack and the cutover) · Step type: `custom` · API version 62.0 (the build's value; this step stamps no file with it)

`agents/metadata-builder` wrote this note under Step 7 of its playbook. **It is text for a human.** No agent
and no acceptance test runs any command in it. This agent ran no `sf` command of any kind.

**This step writes no metadata.** It has no `-meta.xml` and no `package.xml`, because `plan.json` declares
this file as its only output. It exists for one reason. Q26 was answered *"No — confirm the report type
name and column codes from a retrieve during the build; never guess them (we learned that on another
project)"*, and a design-only build cannot run that retrieve.

**The retrieve is a pre-deploy prerequisite, not a build step.** No step of this build runs it. M4-S02
builds its report with provisional column codes, and that report must not be deployed until § 3 has been
done and its result is in § 4.

Sources: `skills/admin/reports-and-dashboards/SKILL.md` (Questions to Ask, last two rows; Recommended
Workflow steps 3, 5 and 6), `references/metadata-examples.md` §§ 2, 5, 6 and 7,
`references/gotchas.md` (F-50, F-51, and "`baseObject` on a Report Type Is Permanent…"),
`references/examples.md` ("Case Aging Report with Cross-Filter"), `scripts/check_report_inventory.py`
(RPT-COL-01, RPT-GRP-01). Precedent: `examples/builds/case-onboarding/reports/MOCK-DEPLOY-M5.md` and
`artefacts/M5-S01/deploy-order.md`. Build inputs: `plan.json` Q9, Q23, Q26, Q54, Q57, A28, A40 and A43;
`artefacts/M1-S01/objects/Opportunity/fields/` for the two custom fields.

---

## 1. Why the codes cannot be written from memory

- **Report column codes are not field API names.** `<columns><field>` takes a column code whose value
  depends on the report type (`metadata-examples.md` § 2: *"Never guess these — retrieve an existing
  report on the same report type and read them off"*; SKILL.md Recommended Workflow step 3, *"Retrieve
  before you write"*).
- **The org is the only judge, and it judges only at deploy.** Case-onboarding is the precedent. Values
  that looked right were rejected by a `--dry-run` against a real org. `<reportType>Cases</reportType>`
  failed with `invalid report type`, and the correct value is `CaseList`. Grouping `USERS.NAME` failed with
  `Grouping: Invalid value specified`, and the correct value is `OWNER`. Five guesses at the
  `Case.IsEscalated` code were all rejected with `filters-criteriaItems-column: Invalid value specified`
  (gotchas F-50 and F-51; `MOCK-DEPLOY-M5.md`). No offline check caught any of them.
- **On this build the codes cannot be harvested from what is in the org today.** M4-S02 ships a *new*
  report type, `Enterprise_Opportunity_Pipeline` (A40). Two of its six columns are *new* fields from
  M1-S01: `Discount__c` (Percent, 5,2) and `Approval_Status__c` (restricted picklist). No report in the
  target org today can carry a code for that report type or for those fields. This is the F-51 shape: the
  harvest needs a report built on the new report type, which is § 3, Phase B.

## 2. Phase A: read-only probes (run any time before M4-S02 is deployed)

These three commands are the ones `plan.json` names for this step, verbatim:
`sf org list metadata --metadata-type ReportFolder`,
`sf org list metadata --metadata-type Report --folder <name>`, and
`sf project retrieve start --metadata "Report:<Folder>/<Name>"`. They are written below with the
`--target-org` flag that the skill's own fenced examples carry (`metadata-examples.md` §§ 5 and 6).
`sf org list metadata` only lists. `sf project retrieve start` reads from the org and writes local files.

```bash
# A1. List the report folders. Find the one that holds the SMB pipeline report (Q9 says the report exists;
#     its folder and developer name are not on file in this build).
sf org list metadata --metadata-type ReportFolder --target-org <alias>

# A2. List the reports in that folder. Note the SMB pipeline report's developer name.
sf org list metadata --metadata-type Report --folder <SMB_Folder> --target-org <alias>

# A3. Retrieve the SMB pipeline report.
sf project retrieve start --metadata "Report:<SMB_Folder>/<SMB_Pipeline_Report>" --target-org <alias>
```

**Copy these three things out of the A3 file (`reports/<SMB_Folder>/<SMB_Pipeline_Report>.report-meta.xml`):**

1. **`<reportType>`. This is the check that closes A40 and Q54.** This build makes a **NEW,
   Enterprise-scoped report type** (`Enterprise_Opportunity_Pipeline`, baseObject `Opportunity`). It does
   **not** edit whatever report type the SMB pipeline report uses, because requirement.md item 6 says
   nothing may break SMB. The retrieve confirms that decision against the org instead of assuming it:
   - If the value names a custom report type, retrieve that report type too. Record its `<baseObject>`,
     its `<join>` and which other reports are built on it. That list is the blast radius Q54 asked about
     (gotchas: *"Before editing a shared report type, list what depends on it"*).
     ```bash
     # A4. Only if A3's <reportType> is a custom report type.
     sf project retrieve start --metadata "ReportType:<value from A3>" --target-org <alias>
     ```
     The outcome is the same either way: nothing retrieved here is edited. If the SMB type could have been
     reused, the org ends up with two report types where one would have done. A40 already accepts that cost.
   - If the value is a standard report type, record its API name exactly as the org returned it. That is
     Q26's "exact API name" for this org's standard Opportunity report type. M4-S02 does not use a
     standard report type (A40), so the name goes into the cutover record, not into any M4-S02 file.
2. **The code forms this org uses for Name, Stage, Amount, Close Date, Record Type and Owner.** Look in the
   `<columns><field>`, `<groupingsDown><field>` and `<filter><criteriaItems><column>` values. Q9 says this
   report filters on Record Type = Master, so the report carries a record-type filter code. Treat these as
   **evidence, not confirmation**: codes are report-type-specific, and the SMB report is on a different
   report type from the one M4-S02 ships. If the SMB report sits on a custom report type with baseObject
   `Opportunity`, its `Opportunity$…` codes are the closest evidence available before Phase B.
3. **Nothing else.** Do not copy the SMB report's `<scope>`, folder or filters into M4-S02. M4-S02's note
   leaves `<scope>` out on purpose (D7, Q24).

## 3. Phase B: the harvest that confirms the codes (after the report type is in the org, before the report is)

This is the only way to confirm the six codes, for the reason given in § 1, third bullet. It follows the
route gotchas F-51 documents: *"build the filter once by hand, retrieve that report, and copy the code into
source."*

1. **Deploy M1-S01's two fields and M4-S02's `ReportType` first.** This is a real deploy of part of
   the build, so it is the human's decision at the M4 gate. Validate that subset first with the
   skill's `--dry-run` form in § 6, in the person's own DX project. The report type must exist before a
   report that names it. One `package.xml` deploy resolves that order by itself; *"splitting it across
   deploys does not"* (`metadata-examples.md` § 6). So the person splitting it deploys the report type
   first.
2. **Build one scratch report on `Enterprise_Opportunity_Pipeline` in the report builder.** It appears
   under the `<label>` M4-S02 gives it. If it is missing from the list, check that it shows as
   *Deployed* in Setup → Report Types: `deployed` `false` leaves a report type *"deployable,
   invisible"* (`metadata-examples.md` § 1). Add the six fields in § 4 as columns. Add every filter and
   grouping M4-S02's report uses (see § 5). Save it in a shared folder you can name on the command line.
3. **List the scratch report and retrieve it:**
   ```bash
   sf org list metadata --metadata-type Report --folder <Scratch_Folder> --target-org <alias>
   sf project retrieve start --metadata "Report:<Scratch_Folder>/<Scratch_Report>" --target-org <alias>
   ```
4. **Diff each code against M4-S02's report file**
   (`artefacts/M4-S02/reports/Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage.report-meta.xml`).
   **A code that survives the diff is confirmed. A code that does not is replaced before deploy.** The
   replacement goes in through a rebuild of M4-S02 so that its tester and documentation re-run, never
   through a hand edit of a tested artefact. Write each result in § 4's last column.
5. **If a code still cannot be harvested,** do not guess it. Gotchas F-51: ship the report without that
   column or criterion, record it as a post-deploy runbook step, and add it in the report builder after
   deploy. *"Deploying an honestly incomplete filter beats deploying a guessed column code."*
6. **Delete the scratch report** once its codes are copied, so it does not sit beside the real one.
7. **Run the § 6 validate-only command over M4-S02** with the confirmed codes in place. Gotchas F-50:
   *"A `--dry-run` deploy is not optional verification here."*

## 4. The six provisional column codes M4-S02 ships

They come from A43 (the row is Opportunity Name, Stage, Amount, Discount, Close Date and Approval Status;
base object Opportunity; no join) and from this step's first acceptance test. All six use the
`Object$Field` form. `metadata-examples.md` § 2 says the Metadata API guide's own samples use that form for
custom report types (*"`CRT_Object__c$Name`"*). **The form is documented. The individual codes are not.**

| # | Column (label) | Field | Provisional code (M4-S02) | Status | Confirmed code (fill in at § 3 step 4) |
|---|---|---|---|---|---|
| 1 | Opportunity Name | `Opportunity.Name` (standard) | `Opportunity$Name` | **UNVERIFIED (2026-10-02)** | |
| 2 | Stage | `Opportunity.StageName` (standard) | `Opportunity$StageName` | **UNVERIFIED (2026-10-02)** | |
| 3 | Amount | `Opportunity.Amount` (standard) | `Opportunity$Amount` | **UNVERIFIED (2026-10-02)** | |
| 4 | Discount | `Opportunity.Discount__c` (M1-S01, Percent 5,2) | `Opportunity$Discount__c` | **UNVERIFIED (2026-10-02)** | |
| 5 | Close Date | `Opportunity.CloseDate` (standard) | `Opportunity$CloseDate` | **UNVERIFIED (2026-10-02)** | |
| 6 | Approval Status | `Opportunity.Approval_Status__c` (M1-S01, restricted picklist) | `Opportunity$Approval_Status__c` | **UNVERIFIED (2026-10-02)** | |

**What the checker says about them, and why that is expected.** `check_report_inventory.py` rule
**RPT-COL-01** reports every one of these six as unverifiable offline. That is by design. It fires at INFO
on each `<columns>` or `criteriaItems` code that is neither one of the report's own grouping fields nor in
the checker's `KNOWN_GOOD_COLUMN_CODES`. That set holds four codes confirmed live for the standard
`CaseList` report type only (`STATUS`, `PRIORITY`, `OWNER`, `CREATED_DATE`), so none of these six can match
it. INFO never affects the exit code, with or without `--strict`. M4-S02's own checker test expects six
RPT-COL-01 lines at exit 0 for exactly this reason. Two refinements from the checker source:

- RPT-COL-01 **skips a report's own grouping fields.** If M4-S02 groups by stage (`Opportunity$StageName`
  in `<groupingsDown>`) or by close month, the rule says nothing about that code. That silence is not
  confirmation. The code stays provisional until § 3.
- **A field cannot be both a grouping and a column** (RPT-GRP-01, ERROR; proven live in F-50: *"You can't
  include groupings in the selected columns list"*). If M4-S02 groups by one of the six, that code appears
  only under `<groupingsDown>`.

Both points were checked by running the checker on two throwaway fixtures outside the build on
2026-10-02. A `Report` with the six codes as `<columns>` gave six RPT-COL-01 INFO lines and exited 0,
and also exited 0 with `--strict`. The same report with `Opportunity$StageName` moved into
`<groupingsDown>` gave five lines, none of them for `StageName`.

## 5. Codes beyond these six

`plan.json` lists six codes: A43 and this step's first acceptance test. The M4 goal says *"open Enterprise
opportunities"*, and the dashboard shows the pipeline *"by close month"*. So M4-S02 may also write codes
for a record-type filter, an open-or-closed filter, an owner grouping or a `dashboardFilterColumns` column.
**Every such code is provisional under the same A28 rule.** Harvest it in the same Phase B scratch report:
add that filter or grouping in step 2, and it arrives in the retrieve. This note proposes no code string
for any of them. None is in the plan, and the cited skill documents none for this report type.

## 6. Validate-only command (text for a human; this agent never runs it)

M4-S01 ships no component, so it has nothing of its own to validate. The command below validates
M4-S02's tree, together with M1-S01's fields that its report type names, once § 3 has run.
`scripts/mock_deploy.py` hard-codes `--dry-run` (checkOnly). It has no flag that deploys.

```bash
# From the repo root. With no --milestone, it selects every step that is built, tested or documented.
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json --org-alias <alias> --mode manifest
```

The equivalent in a person's own Salesforce DX project (the skill's fenced form, `metadata-examples.md`
§ 6) is below. Run it there, never against this build directory:

```bash
sf project deploy start --manifest manifest/package.xml --dry-run --target-org <alias>
```

## 7. UNVERIFIED (2026-10-02): what M4-S02 inherits until the retrieves are run

| Id | Marker | Closed by |
|---|---|---|
| U1 | The six column codes in § 4, and any further code in § 5 (A28, risk high). | § 3 step 4 |
| U2 | Which report type the SMB pipeline report uses, and whether other reports share it (A40, Q54). A40's build-new decision does not depend on the answer. The answer only confirms that nothing here touches SMB. | § 2 A3, plus A4 if custom |
| U3 | The API name of this org's standard Opportunity report type. Gotchas F-50: expect `…List`-style names (`CaseList`), but *"confirm each one, don't extrapolate the suffix."* M4-S02 does not use this name. | § 2 A3, if SMB is on a standard type |
| U4 | Whether a single-request dry run of the new `ReportType` and the `Report` together rejects a wrong column code. If it does, the dry run alone would be a negative check without Phase B. No cited source and no precedent covers a custom report type: case-onboarding's report was on the standard `CaseList` type. Until proven, Phase B is the confirmation and the dry run is the backstop. | The first § 6 run over M4-S02 |
| U5 | `sf project retrieve start` writes into a Salesforce DX project's package directory, and the commands in §§ 2 and 3 assume they run inside one. No cited skill states the CLI's project requirement. Run them in a scratch DX project outside `.sfskills/builds/northwind-sales/`, so that org files never land in `artefacts/`. | The first A3 run |
| U6 | Whether a report saved in a personal (private) folder can be listed by folder name with `sf org list metadata --metadata-type Report --folder`. § 3 step 2 says to use a shared folder for this reason. | Not needed if a shared folder is used |

M4-S02's own `deploy-order.md` owns the rest of that step's pre-deploy items: the dashboard `runningUser`
(A29), the empty `Enterprise_Managers` group (A32) and the folder shares. This note does not repeat them.
