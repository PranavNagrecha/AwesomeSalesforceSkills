# Deploy order: M4-S02, the Enterprise pipeline report type, report, dashboard, folders and group

Build: `northwind-sales` · Milestone: M4 (pipeline visibility, the handover pack and the cutover) · Step type: `ui` · API version 62.0 (the AGENT.md fallback: `plan.json` carries no `api_version`; every `package.xml` in the build is at 62.0)

`agents/metadata-builder` wrote this note under Step 7 of its playbook. **It is text for a human.** No agent
and no acceptance test runs any command in it, and this agent ran no `sf` command and no `scripts/mock_deploy.py`.

Read `artefacts/M4-S01/deploy-order.md` first. It is the probe runbook this step depends on, and every
"Phase A", "Phase B" and "§ n of M4-S01" below refers to it.

Sources: `skills/admin/reports-and-dashboards` (SKILL.md Questions to Ask and Recommended Workflow;
`references/metadata-examples.md` §§ 1–7; `references/gotchas.md`, including F-49, F-50 and F-51; `templates/dashboard-design-template.md`;
`scripts/check_report_inventory.py`), `skills/admin/queues-and-public-groups` (`references/metadata-examples.md`,
`scripts/check_queues.py`), and the Metadata API Developer Guide sections those references cite (Summer '26 `api_meta.pdf`:
Report, ReportColumn, ReportGrouping, UserDateGranularity, ReportSummaryType, Dashboard, DashboardComponent, the
SpecifiedUser grid-layout sample definition, DashboardComponentSection, ReportType, Group). Precedent:
`examples/builds/case-onboarding/artefacts/M5-S01/` and `reports/MOCK-DEPLOY-M5.md`. Build inputs: `plan.json`
Q23–Q26, Q54–Q57, Q63, Q4, Q8, Q9; A28–A32, A40–A43; D7; `artefacts/M1-S01/` for the two fields, the `Enterprise`
record type and the `Closed Won` / `Closed Lost` stage values.

---

## 0. Before anything in this step deploys: the blocking items

These four would each produce a **silently wrong** result if skipped. None of them is a follow-up.

| # | Item | Owner (from the answers) | Where |
|---|---|---|---|
| B1 | Confirm every report column code by M4-S01's Phase B harvest, and rebuild M4-S02 with the confirmed codes. This covers the six codes (U1) plus this step's record-type filter code and value (U8). | Sales Operations lead (Q26's owner) | §§ 2–4 |
| B2 | Set the dashboard's `runningUser` to the VP's username in the deploy copy. Without it, the platform puts in the username of whoever runs the deploy. | Sales-ops admin, with the VP's username from the VP | § 6 |
| B3 | Decide whether each manager really sees only their own reps' rows. That depends on the Opportunity org-wide default, which this build does not record (U12). | VP Sales Operations | § 8 |
| B4 | Split the M4 deploy so that Phase B can run: deploy the `Group`, the `ReportType` and M1-S01's fields first; the `Report` and the `Dashboard` follow after the harvest. | The person deploying, decided at the M4 gate | §§ 1–2 |

One more item is post-deploy but mandatory: add the two Enterprise managers and the VP to the
`Enterprise_Managers` group (§ 5). Until that is done, nobody can open either folder except the folder's owner and
users with administrative permissions.

---

## 1. Components and the order they deploy in

| Order | Component (`package.xml` type : member) | File | Why it sits here |
|---|---|---|---|
| prerequisite | `CustomField : Opportunity.Discount__c`, `CustomField : Opportunity.Approval_Status__c`, `RecordType : Opportunity.Enterprise`, `StandardValueSet : OpportunityStage` | `artefacts/M1-S01/…` | The report type lists both custom fields in its `sections`. The report filters on the `Enterprise` record type and on the `Closed Won` / `Closed Lost` stage values. All four come from M1-S01, so they must already be in the org, or be in the same request. |
| 1 | `Group : Enterprise_Managers` | `groups/Enterprise_Managers.group-meta.xml` | Both folder files name it in `folderShares/sharedTo`. The queues skill's rule is *"Deploy the group before any queue or sharing rule that names it"*; a folder share names it the same way. |
| 2 | `ReportType : Enterprise_Opportunity_Pipeline` | `reportTypes/Enterprise_Opportunity_Pipeline.reportType-meta.xml` | *"the report type must exist before the report that names it in `<reportType>`"* (`metadata-examples.md` § 6). Phase B needs it in the org before any report is built on it. |
| 3 | `Report : Enterprise_Sales` (the folder) | `reports/Enterprise_Sales.reportFolder-meta.xml` | A report lives in a folder, so the folder goes first. |
| 4 | `Report : Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage` | `reports/Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage.report-meta.xml` | Needs steps 2 and 3. **Only after B1.** |
| 5 | `Dashboard : Enterprise_Sales` (the folder) | `dashboards/Enterprise_Sales.dashboardFolder-meta.xml` | *"the folder must exist before the dashboard deploys"* (`dashboard-design-template.md`). |
| 6 | `Dashboard : Enterprise_Sales/Enterprise_Pipeline` | `dashboards/Enterprise_Sales/Enterprise_Pipeline.dashboard-meta.xml` | *"the report before the dashboard that names it in `<report>`"* (§ 6). **Only after B1 and B2.** |

**One request or two.** *"A single `package.xml` deploy resolves this itself; splitting it across deploys does not"*
(`metadata-examples.md` § 6). Without Phase B, everything could go in one request. With Phase B (B4), the person
splitting it deploys in two requests: first the prerequisite fields plus orders 1, 2, 3 and 5, then orders 4 and 6
after the rebuild. The folders can go in the first request, because they name only the group.

**`package.xml` notes.** Neither `Report` nor `Dashboard` accepts `*`. Each folder is a bare member under the `Report`
or `Dashboard` type name, because `describeMetadata()` exposes no `ReportFolder` or `DashboardFolder` type
(`metadata-examples.md` § 5). `ReportType` and `Group` would accept `*`, but they are named explicitly too.

---

## 2. Phase B, as it applies to this step

M4-S01's § 3 is the procedure. What this step adds is the list of things the scratch report must carry, so that one
retrieve returns every code this step's files use:

1. The six fields in § 3 below: Name, Amount (**summarised as Sum**), Discount and Approval Status as columns, and
   Stage and Close Date as the two groupings in item 2.
2. Grouping 1 = Stage. Grouping 2 = Close Date, grouped **by calendar month**.
3. A filter `Record Type equals Enterprise`, and the two filters `Stage not equal to Closed Won` and `Stage not equal
   to Closed Lost`.
4. Optional but useful: one dashboard on the scratch report with a column chart, X-axis = close month, value = Sum of
   Amount. Retrieve it as well (`sf project retrieve start --metadata "Dashboard:<Scratch_Folder>/<Scratch_Dashboard>"`),
   in the same scratch DX project M4-S01 U5 describes. It answers U9.

Then diff the retrieved file(s) against this step's report and dashboard. **A code that survives the diff is
confirmed. A code that does not is replaced through a rebuild of M4-S02** (`built → running` before it is tested,
`tested → failed → pending → running` after, `documented → running` once documented), never by a hand edit of a
tested artefact. That keeps the
tester and the documentation in step with the file.

If a code still cannot be harvested, apply gotchas F-51: ship the report without that column or criterion, record it
as a post-deploy runbook step, and add it in the report builder after deploy. One case is different: the record-type
criterion (U8). If it cannot be confirmed, the report must not ship without it. Without it, the "Enterprise" report and
the VP's tile would total every opportunity record type, SMB and Renewal included, under an Enterprise title.

---

## 3. The six provisional column codes, carried from M4-S01

Verbatim from `artefacts/M4-S01/deploy-order.md` § 4. The `§ 3 step 4` in the last column header is M4-S01's.

| # | Column (label) | Field | Provisional code (M4-S02) | Status | Confirmed code (fill in at § 3 step 4) |
|---|---|---|---|---|---|
| 1 | Opportunity Name | `Opportunity.Name` (standard) | `Opportunity$Name` | **UNVERIFIED (2026-10-02)** | |
| 2 | Stage | `Opportunity.StageName` (standard) | `Opportunity$StageName` | **UNVERIFIED (2026-10-02)** | |
| 3 | Amount | `Opportunity.Amount` (standard) | `Opportunity$Amount` | **UNVERIFIED (2026-10-02)** | |
| 4 | Discount | `Opportunity.Discount__c` (M1-S01, Percent 5,2) | `Opportunity$Discount__c` | **UNVERIFIED (2026-10-02)** | |
| 5 | Close Date | `Opportunity.CloseDate` (standard) | `Opportunity$CloseDate` | **UNVERIFIED (2026-10-02)** | |
| 6 | Approval Status | `Opportunity.Approval_Status__c` (M1-S01, restricted picklist) | `Opportunity$Approval_Status__c` | **UNVERIFIED (2026-10-02)** | |

**Where each one sits in this step's files.**

| # | Code | Report (`Open_Enterprise_Pipeline_By_Stage`) | Dashboard (`Enterprise_Pipeline`) |
|---|---|---|---|
| 1 | `Opportunity$Name` | `<columns>` | — |
| 2 | `Opportunity$StageName` | `<groupingsDown>` 1 (`sortOrder` `Asc`), and `filter` items 2 and 3 | — |
| 3 | `Opportunity$Amount` | `<columns>` with `<aggregateTypes>Sum</aggregateTypes>` | `chartSummary/column`, `aggregate` `Sum` |
| 4 | `Opportunity$Discount__c` | `<columns>` | — |
| 5 | `Opportunity$CloseDate` | `<groupingsDown>` 2, `dateGranularity` `Month` | `groupingColumn` |
| 6 | `Opportunity$Approval_Status__c` | `<columns>` | — |

**Close Date is a grouping, not a column.** The report is by stage for the managers. The VP's tile is by close
month. This build assumes a dashboard component can chart only a field its source report groups by (the guide's
sample groups its components by `TITLE`, a grouping of its source report; the assumption is part of U9). `plan.json`
declares one report for both, so Close Date becomes the report's second grouping, at month granularity. A field cannot be both a grouping and
a column (RPT-GRP-01; proven live in F-50: *"You can't include groupings in the selected columns list"*). So Close
Date appears on the report as the month heading under each stage, rather than as a date on each row. A43 lists Close
Date in the row. The month heading carries it at month precision, and this is the one place the build departs from
A43's wording.

**What the checker says, and why that is expected.** The declared checker printed *"Scanned 5 report/dashboard
file(s); 6 finding(s) detected."* at score 95 and exit 0. Five findings are RPT-COL-01 at INFO: `Opportunity$Name`,
`Opportunity$Amount`, `Opportunity$Discount__c`, `Opportunity$Approval_Status__c` and `Opportunity$RecordTypeId`.
The sixth is the MEDIUM `SpecifiedUser`-with-no-`runningUser` finding (§ 6). RPT-COL-01 fires on every provisional
code by design: the checker cannot verify a code offline. These lines are the expected state and are **not** fixed
by changing codes. The step's acceptance-test description predicted six RPT-COL-01 lines. There are five because
RPT-COL-01 skips a report's own grouping fields. `StageName` and `CloseDate` are groupings here, and M4-S01 § 4
already says that skip is not confirmation. The record-type filter code adds one. Seven provisional codes are in
the file; the checker names five of them.

---

## 4. What this step adds beyond the six

M4-S01 § 5 anticipated this: *"M4-S02 may also write codes for a record-type filter, an open-or-closed filter … Every
such code is provisional under the same A28 rule."*

- **Record-type filter (U7, U8).** Q9 says the SMB pipeline report filters on Record Type = Master. A43 and the M4 goal
  ask for *Enterprise* opportunities only, and Q8 moves about 140 open Enterprise deals onto the `Enterprise` record type
  after go-live. The report type therefore lists `RecordTypeId` in its section (U7), and the report filters
  `Opportunity$RecordTypeId` `equals` `Enterprise` (U8). M1-S01's record type has both its developer name and its label
  set to `Enterprise`, so the value matches either way the org keys it. Phase A3's retrieve of the SMB report shows the
  form this org uses for a record-type filter, though only as evidence: that report is on a different report type.
- **Open-only filter: no new code.** "Open" is expressed as `Opportunity$StageName` `notEqual` `Closed Won` and
  `notEqual` `Closed Lost`. The code is code 2, and the values are M1-S01's `OpportunityStage` `fullName`s. With the
  record-type filter in place, those are the only two closed stages the Enterprise process has. An `IsClosed` filter
  would have added an eighth provisional code.
- **The dashboard component (U9).** The shape is the Metadata API guide's own `SpecifiedUser` dashboard sample:
  `autoselectColumnsFromReport` `false`, a `chartSummary` (`aggregate` `Sum`, `axisBinding` `y`, `column`) and a
  `groupingColumn`. `componentType` is `Column`, which puts months on the horizontal axis. No `sortBy` is written (it is
  optional). The intent is that the chart keeps the report's ascending month order; that default is part of U9, and
  the scratch dashboard in § 2 item 4 shows it. The guide's field table names the auto-select field
  `isAutoSelectFromReport`, while its sample writes `autoselectColumnsFromReport`. The sample's spelling is used here,
  and the dry run will settle it.
- **One tile, empty right section (U10).** `leftSection` and `rightSection` are both required. A section's `components`
  list is optional (guide, DashboardComponentSection), so the right section carries only `columnSize`. The left
  section is `Wide`, so the single tile uses the space.

---

## 5. Folder sharing and the empty group (manual test 1)

- **Both folders** (`reports/Enterprise_Sales.reportFolder-meta.xml`, `dashboards/Enterprise_Sales.dashboardFolder-meta.xml`)
  are `accessType` `Shared` with a **single** `folderShares` entry: `accessLevel` `View`, `sharedTo` `Enterprise_Managers`,
  `sharedToType` `Group` (Q25; `plan.json` `inputs.folder_share`). Reps get no folder access (A31, Q63's default).
  `Shared` is used rather than `Public`, because `Public` includes portal users (gotchas).
- **The group ships with no members.** Group metadata carries no membership. The Metadata API guide: *"Members of the
  public group aren't migrated when you deploy the group type"*; the queues skill: *"Group membership is not part of
  `Group` metadata; add members in Setup or with `GroupMember` records via the API after deploy"* (A32). **After deploy,
  the sales-ops admin adds the two Enterprise managers and the VP to `Enterprise Managers` in Setup → Public Groups.**
  Until then, the folders are open only to their owner and to users with administrative permissions.
- **`doesIncludeBosses` is `false`.** The guide marks it required. It decides whether records shared with the group are
  also shared with users above its members in the role hierarchy. Q25 names the folder audience exactly (the two
  managers, the VP and the sales-ops admin), so nobody above them gains anything through this group. Whether the
  checkbox affects folder shares at all is U11.
- **The sales-ops admin "manages" the folders (Q25), but no `Manage` share is written.** The plan asks for a single
  `View` entry, so the admin's management rights rest on an administrative permission, which no answer names (U13).
  If the admin lacks one, add a second `folderShares` entry with `accessLevel` `Manage` through a rebuild. Approving
  this gate means approving who can read deal amounts and discounts.
- **Deploy, don't package.** *"During package installation, `FolderShare` for `DashboardFolder` and `ReportFolder` is
  ignored."* A direct `sf project deploy` carries the shares; a package install does not.
- Folder access is not record access. `View` on the folder lets a user run the report; sharing still decides which
  rows come back (§ 8).

---

## 6. The dashboard's running user (manual test 2)

- `dashboardType` is `SpecifiedUser` (Q24: *"the dashboard tile shows the full Enterprise pipeline as the running user
  (the VP)"*; D7's consequence). **No `runningUser` element is present** (A29).
- **Mandatory pre-deploy step (B2).** Insert the VP's username into the dashboard file *in the copy being deployed*:
  `<runningUser>` goes between `</rightSection>` and `<textColor>`, which is where the Metadata API guide's samples put
  it. The value is the VP's username **in the target org**, and it differs per sandbox:

  ```xml
      </rightSection>
      <runningUser><!-- the VP's username in the target org; no answer supplies it --></runningUser>
      <textColor>#000000</textColor>
  ```

  Replace the comment with the real username. Do not commit a username to the build: the gotchas treat `runningUser` as
  an environment-specific value, *"like a Named Credential endpoint"*. If it is skipped, the platform substitutes the
  deploying user. The guide: *"When you deploy a dashboard and the value in this field is not defined or does not
  correspond to a valid user, the field is populated with the username of the user performing the deployment."* There
  is no error and no warning. The dashboard then runs as the release engineer, who typically has the broadest access
  in the org.
- **What `SpecifiedUser` means for every viewer.** *"All users see data at the access level of one specific running
  user … regardless of their own security settings"* (guide, `dashboardType`). Each manager who opens the tile sees the
  VP's whole Enterprise pipeline, not their own reps' slice. That is what Q24 asked for, and the folder share in § 5
  is the only control on who sees it.
- **Two risks the skill names, recorded and not resolved here.** The skill recommends that a `SpecifiedUser` dashboard
  run as *"a named integration/service user that never leaves, not a human"*, because *"SpecifiedUser Dashboards Die
  With the Running User"*. Q24 named the VP. If the VP leaves or is deactivated, the tile stops refreshing, so re-point
  it in the same change as the deactivation. Second, the VP's own access level is what every viewer sees.
- **Verify after deploy** (`metadata-examples.md` § 7; check `Type`, never `RunningUserId` alone):

  ```sql
  SELECT DeveloperName, Title, Type, RunningUserId, FolderName FROM Dashboard WHERE FolderName = 'Enterprise Sales'
  ```

  Expected: `Type` = `SpecifiedUser`, and `RunningUserId` = the VP's user Id, not the deployer's.

---

## 7. Why there is no product-count column (manual test 3)

Q23 was answered *"Yes, show it — with the product count column so the manager sees the gap."* The report shows every
open Enterprise opportunity, with or without products: it is on Opportunity alone with no join, so nothing filters out
opportunities that have no product lines. But it carries **no product-count column**, for two reasons:

1. **There is no line-item count in this build to show.** `plan.json` descoped the column *"with M2-S04's block as its
   reason"*: M2-S04 was blocked because no skill documented how to count an opportunity's line items. That block has
   since been lifted. M2-S04 was unblocked on 2026-09-15 (`plan.json` `steps[M2-S04].amendments[0]`) and is
   `documented`, but it was unblocked through `HasOpportunityLineItem`, which is a has-at-least-one flag, not a count.
   So the line-item **count** M2-S04 was originally blocked on still does not exist in this build.
2. **A join to Opportunity Product was rejected.** It returns one row per line item and would double-count the Amount
   this same report is meant to total (`plan.json` `steps[M4-S02].inputs.note`).

`HasOpportunityLineItem` could serve Q23's "see the gap" as a yes/no column, with no join and no count. Adding it is a
plan change (`amend-step` on this step, then a rebuild), not something this step does on its own (§ 12, item O-3).

---

## 8. Whose rows each manager sees (U12)

The report carries **no `scope` element**. Under `plan.json`'s note and D7, rows follow each viewer's record access,
which is how Q24 described it: *"Each manager sees only their own reps' pipeline on the report (role hierarchy does
that)"*. The skill documents `scope` values only for Accounts reports (`MyAccounts`, `MyTeamsAccounts`, `AllAccounts`)
plus the sample's `organization`. It documents none for an Opportunity report type, so there is nothing to write.

**This is UNVERIFIED (2026-10-02), and it may be wrong.** Q4 was answered *"SMB and Enterprise see each other's
pipeline; no sharing change."* If that visibility comes from a Public Read Only or Public Read/Write org-wide default
on Opportunity, each manager can see every rep's deals, and the role hierarchy narrows nothing. The report would then
show each manager the whole Enterprise pipeline, which is not what Q24 asked for. D7 shows that a manager *can* see
their own reps' deals (sharing tree Q2). It does not show that they *cannot* see anyone else's. The same tree's Q1
reads *"Public Read-Only / Public Read-Write → Tighten OWD before adding anything → Q2"* (`standards/decision-trees/sharing-selection.md`), and Q4 rules out any sharing change. So if the OWD is public, Q4 and
Q24 conflict for this report, and only a human can rank them. The Opportunity OWD is not on file. Decide this before
deploy (B3):

- If the OWD is Private, D7 holds and nothing changes.
- If the OWD is public, either accept that each manager sees all Enterprise rows and record that against Q24, or have
  the managers narrow the report at run time, or harvest a "my team's opportunities" `scope` value in Phase B (save the
  scratch report with that setting and the retrieve returns the value) and add it through a rebuild. M4-S01 § 2 says
  not to copy the SMB report's `scope`. This note does not override that; it puts the choice in front of the human.

---

## 9. Defaults applied (no answer on file)

| Question | Default (assumption) | Effect in the files |
|---|---|---|
| Q54 — does an existing report type back other reports? | A40: build a **new** report type; edit nothing existing. Phase A2/A3/A4 confirms SMB's report type. | `Enterprise_Opportunity_Pipeline` is new. |
| Q55 — dashboard filter? | A41: none. | No `dashboardFilters`, so no component needs `dashboardFilterColumns`. Adding one later is additive. |
| Q56 — historical trending? | A42: current snapshot only. **Trending collects only forward from the day it is enabled**, so every month this stays unanswered is a month of history that cannot be recovered. | No historical trend report, no reporting snapshot. |
| Q57 — what is on the row? | A43: Name, Stage, Amount, Discount, Close Date, Approval Status; base Opportunity, no join. | As § 3, with Stage and Close Date carried as groupings. |
| Q63 — can reps open it? | A31: no folder access for reps; no field-level hiding. | One `View` share, to the group only. |
| Q53 — subscriptions? | A30: none built (no proposed default existed). | No subscription. A `SpecifiedUser` subscription would mail the VP's rows to every recipient. |

---

## 10. Validate-only commands (text for a human; this agent ran none of them)

`scripts/mock_deploy.py` hard-codes `--dry-run` (checkOnly) and has no option that deploys. Its arguments below are
read from its source; the script was not run.

```bash
# First request of the split (B4): validate M1-S01 plus this step WITHOUT the report and the dashboard.
# --probe validates a temporary copy and is never gate evidence; use it to see the first request validate.
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json --org-alias <alias> \
  --step M1-S01 --step M4-S02 --probe \
  --without "Report:Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage" \
  --without "Dashboard:Enterprise_Sales/Enterprise_Pipeline"

# After Phase B and the rebuild with confirmed codes: validate everything that is built, tested or documented,
# from the merged manifest (gate evidence goes in reports/mock-deploy/<ts>/summary.md).
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json --org-alias <alias> --mode manifest
```

The same check in a person's own Salesforce DX project (`metadata-examples.md` § 6) is below. Run it there, never
against this build directory:

```bash
sf project deploy start --manifest manifest/package.xml --dry-run --target-org <alias>
```

Validate in a sandbox first, in the same two-request order you will use in production (`skills/admin/change-management-and-deployment`,
Mode 1 step 4: *"Validate in lower environments with the same order you will use in production"*). Gotchas F-50: *"A `--dry-run` deploy is not optional verification here."* U4 (inherited) records that it is still
unknown whether a dry run rejects a wrong column code on a new custom report type.

After deploy, also run the report check from `metadata-examples.md` § 7, and open **Setup → Report Types** to confirm
`Enterprise Opportunity Pipeline` shows as *Deployed*:

```sql
SELECT Id, DeveloperName, Name, FolderName, Format, LastRunDate, OwnerId FROM Report WHERE FolderName = 'Enterprise Sales'
```

Expected: `Format` = `Summary`.

---

## 11. UNVERIFIED (2026-10-02)

### Inherited from M4-S01 (verbatim from `artefacts/M4-S01/deploy-order.md` § 7; not resolved here)

| Id | Marker | Closed by |
|---|---|---|
| U1 | The six column codes in § 4, and any further code in § 5 (A28, risk high). | § 3 step 4 |
| U2 | Which report type the SMB pipeline report uses, and whether other reports share it (A40, Q54). A40's build-new decision does not depend on the answer. The answer only confirms that nothing here touches SMB. | § 2 A3, plus A4 if custom |
| U3 | The API name of this org's standard Opportunity report type. Gotchas F-50: expect `…List`-style names (`CaseList`), but *"confirm each one, don't extrapolate the suffix."* M4-S02 does not use this name. | § 2 A3, if SMB is on a standard type |
| U4 | Whether a single-request dry run of the new `ReportType` and the `Report` together rejects a wrong column code. If it does, the dry run alone would be a negative check without Phase B. No cited source and no precedent covers a custom report type: case-onboarding's report was on the standard `CaseList` type. Until proven, Phase B is the confirmation and the dry run is the backstop. | The first § 6 run over M4-S02 |
| U5 | `sf project retrieve start` writes into a Salesforce DX project's package directory, and the commands in §§ 2 and 3 assume they run inside one. No cited skill states the CLI's project requirement. Run them in a scratch DX project outside `.sfskills/builds/northwind-sales/`, so that org files never land in `artefacts/`. | The first A3 run |
| U6 | Whether a report saved in a personal (private) folder can be listed by folder name with `sf org list metadata --metadata-type Report --folder`. § 3 step 2 says to use a shared folder for this reason. | Not needed if a shared folder is used |

### New in M4-S02

| Id | Marker | Closed by |
|---|---|---|
| U7 | The report type lists the record type as `RecordTypeId`, the field's API name, which follows the rule *"The custom report type refers to fields by using their API names"* (guide, ReportType). For a lookup, the org may expect the relationship name instead. No cited source shows a report-type column for a record type. | The first dry run of the first request (§ 10). A wrong name fails loudly there. |
| U8 | The report's record-type filter: code `Opportunity$RecordTypeId` (the `Object$Field` form applied to U7's name) and value `Enterprise`. The code may need the relationship name. The value may need another form, and a wrong *value* could filter silently to zero rows rather than fail. | § 2 Phase B: the scratch report's record-type filter |
| U9 | Whether a dashboard component can chart a summary report's **second** grouping (`groupingColumn` = `Opportunity$CloseDate`) on its own. Also which spelling of the auto-select element the org accepts: the guide's sample writes `autoselectColumnsFromReport`, while its field table says `isAutoSelectFromReport`. | § 2 item 4 (scratch dashboard retrieve), then the dry run |
| U10 | Whether the org accepts a `rightSection` with no `components` (schema-optional per the guide). | The dry run |
| U11 | Whether the group's `doesIncludeBosses` (*"records shared with users in this group are also shared with users higher in the role hierarchy"*) also applies to folder shares. `false` is the narrow choice either way. | Not needed for correctness. Confirm in Setup after deploy if anyone above the VP should, or must not, open the folders. |
| U12 | Whether each manager's report rows narrow to their own reps. That depends on the Opportunity org-wide default, which is not on file, and Q4 suggests cross-team visibility (§ 8). | B3, before deploy |
| U13 | Whether the sales-ops admin holds an administrative permission that lets them manage a `Shared` folder they were not shared to (Q25 "the admin manages it"; the plan writes only a `View` share). | Check the admin's permissions before deploy, or add a `Manage` share through a rebuild |
| U14 | The VP's username in the target org. No answer supplies it (A29), so it is absent rather than guessed. | B2, at deploy time |

---

## 12. Open items for the human

| Id | Item | Decide at |
|---|---|---|
| O-1 | Split the M4 deploy (B4) so that Phase B can confirm the codes, or accept the F-51 fallback for any code that cannot be harvested. The record-type criterion (U8) is the one code that cannot ship absent (§ 2). | M4 gate |
| O-2 | Settle U12 (§ 8): is the Opportunity OWD Private? If not, decide how Q24's "only their own reps" is met. | Before deploy |
| O-3 | Q23's "see the gap": the plan could add an `Opportunity.HasOpportunityLineItem` yes/no column through `amend-step`, with no join and no count (§ 7). The step's `inputs.note` and its third manual test still call M2-S04 blocked; M2-S04 is `documented`. That prose can be corrected with `amend-step --prose-only`. | Next plan amendment |
| O-4 | The checker-test description on this step predicts six RPT-COL-01 lines and seven findings. The built files give five and six, for the reasons in § 3. The test's pass condition (exit 0) holds. Only its prose differs, and `amend-step --prose-only` corrects it. | Next plan amendment |
| O-5 | `check_queues.py` (cited skill `admin/queues-and-public-groups`) is not declared on this step (`build_plan.py next` advises `amend-step --add-checker admin/queues-and-public-groups`). This agent ran it as a self-check: exit 0, also under `--strict`. | Next plan amendment |
| O-6 | B2: get the VP's username for each target org, and decide whether a service user should run the dashboard instead (§ 6). | Before deploy |

---

## 13. Repair after run 1 (MOCK-DEPLOY-M4, 2026-10-02T17:53Z, validate-only, `sfskills-dev`)

Text for a human. This repair pass ran no `sf` command and no `scripts/mock_deploy.py`. Sections 0 to 12 above are the
original build and are unchanged by this repair, so every `RecordTypeId` and `Opportunity$RecordTypeId` mention in §§ 3, 4
and 11 (U7, U8) is **superseded by the table below**. Do not re-derive the filter code from those older lines.

| Finding | Component | The org said | Repair | Grounding |
|---|---|---|---|---|
| N4-F-01 | `reportTypes/Enterprise_Opportunity_Pipeline.reportType-meta.xml` | "Could not find field RecordTypeId in table Opportunity" | The `sections` column for the record type changed from `<field>RecordTypeId</field>` to `<field>RecordType.Name</field>` (table `Opportunity` unchanged, `checkedByDefault` still `false`). | Metadata API Developer Guide (Summer '26 `api_meta.pdf`), ReportType, "Declarative Metadata Sample Definition": its lookup columns are written relationship name, dot, field (`obj_lookup__c.Id`, `obj_lookup__c.Name`, table `Account`). The standard relationship for `RecordTypeId` is `RecordType`. The guide gives no sample for a standard-object record type, so the exact column name is **UNVERIFIED (2026-10-02): org run 2 settles the column name**. |
| N4-F-02 | the Report | "invalid report type" | No change of its own: it failed only because its type did. The record-type filter column moved with the type: `Opportunity$RecordTypeId` became `Opportunity$RecordType.Name`, the `Object$Field` form (guide, Report sample, `CRT_Object__c$Name`) applied to the new field name. The filter value `Enterprise` is unchanged, which suits a `.Name` column better than the Id did. Its five other column codes are untouched and keep their U1 markers. | Same as above, plus the Report sample's `Object$Field` form. Also **UNVERIFIED (2026-10-02): org run 2 settles the column name**. U8 stays open. |
| N4-F-03 | `dashboards/Enterprise_Sales/Enterprise_Pipeline.dashboard-meta.xml` | "Chart dashboard components require the sortBy attribute" | Added `<sortBy>RowLabelAscending</sortBy>` to the chart component, after `showValues` and before `title`. | Guide, `DashboardComponentFilter` enumeration: `RowLabelAscending` ("Sorts in alphabetical order by the label"), `RowLabelDescending`, `RowValueAscending`, `RowValueDescending`. The tile groups by close month, so the label order is the one that matches "by close month". The guide's own samples carry `<sortBy>RowLabelAscending</sortBy>`. The guide's `GroupingSortProperties` row says that a component with groupings keeps its sort information there from API 46.0, "otherwise, it is stored in the sortBy field". The org's message asks for `sortBy` regardless, so only `sortBy` was added. Whether the org also wants `groupingSortProperties` is a question for run 2. |

Two changes in the Report's and the ReportType's own XML comments record the repair. Nothing else in the six metadata files changed,
and `package.xml`, both folders and the group are byte-identical to the first build.

### Library gap recorded by this repair

`skills/admin/reports-and-dashboards` is silent on both defects, and both reached an org before a human saw them.

- Its dashboard chart example in `references/metadata-examples.md` carries no `sortBy` on the chart component. The only `sortBy` in the skill
  (`RowValueDescending`) sits on a different component in the dashboard example. The org requires it on a chart component. This is the
  fourth skill-versus-guide mismatch the first build listed (O-M4S02-04).
- Its report-type guidance carries no column form for a record-type lookup on a standard object, and says only that the type refers to
  fields by API name. For a lookup that rule gave `RecordTypeId`, and the org rejected it. The library needs a verified example
  of that column, and `check_report_inventory.py` cannot catch either defect offline.

### Next step for the human

Re-run the same validate-only command as the first time (§ 10; the operator runs `scripts/mock_deploy.py`). If the org rejects
`RecordType.Name`, the error will name the column it wants. Record the accepted name here and close U7 and U8.

---

## 14. Repair after run 2 (MOCK-DEPLOY-M4, 2026-10-02T18:00Z, validate-only, `sfskills-dev`)

Text for a human. This repair pass ran no `sf` command and no `scripts/mock_deploy.py`. Sections 0 to 13 above are unchanged.
Wherever §§ 3, 4, 11 or 13 name `RecordTypeId`, `RecordType.Name` or `Opportunity$RecordType.Name`, **this section supersedes
them**: the report-type column is now `RecordType`, and the report's filter column is now `Opportunity$RecordType`.

What run 2 taught: `sortBy` was accepted (N4-F-03 closed). The `RecordType.Name` column resolved the relationship to the Record Type
table but failed on `Name` in it, so a dotted relationship form is wrong for this column. The operator's read-only retrieve of the
org's twelve custom report types found none with a record-type column, so there is no org example to copy.

| Finding | Component | The org said | Repair | Grounding |
|---|---|---|---|---|
| N4-F-04 | `dashboards/Enterprise_Sales/Enterprise_Pipeline.dashboard-meta.xml` | "Chart dashboard components require the chartAxisRange attribute" | Added `<chartAxisRange>Auto</chartAxisRange>` to the chart component, as its second element (after `autoselectColumnsFromReport`, before `chartSummary`). `sortBy` stays. | The guide's dashboard samples and `skills/admin/reports-and-dashboards/references/metadata-examples.md` write `<chartAxisRange>Auto</chartAxisRange>`. The guide's `ChartRangeType` table lists the value as lowercase `auto`. The two differ in case; the samples' form is used, and the org judges it on run 3. |
| N4-F-05 | `reportTypes/Enterprise_Opportunity_Pipeline.reportType-meta.xml` | "Could not find field Name in table Record Type" | The `sections` column changed from `<field>RecordType.Name</field>` to `<field>RecordType</field>`, table `Opportunity` unchanged, `checkedByDefault` still `false`. This is the lookup field's own relationship name. **UNVERIFIED (2026-10-02): org run 3 settles the column name; runs 1–2 rejected RecordTypeId and RecordType.Name.** | The remaining documented form for a lookup column in a custom report type is the relationship name itself. The guide has no standard-object record-type sample. |
| N4-F-05 (follow-on) | the Report | no message of its own; it fails while its type fails | Filter column changed from `Opportunity$RecordType.Name` to `Opportunity$RecordType`. The value `Enterprise` is kept. All other column codes, groupings and U1 markers are untouched. | The `Object$Field` form with the report type's column name. Also **UNVERIFIED (2026-10-02): org run 3 settles the column name**. U8 stays open. |

Risk to read on run 3: if the org treats `RecordType` as an Id-typed lookup column, the value `Enterprise` (the label) may be rejected
or match nothing, and the developer name form of the record type would be needed instead. The report type's column rejection, if
any, will name the column it wants; a value mismatch would show only as an empty report, which the M4 manual tests cover.

Files changed by this pass: the report type, the report and the dashboard (XML comments plus the one element each). `package.xml`,
both folders, the group and §§ 0 to 13 are byte-identical to the previous build.

### Library gap recorded by this repair

`skills/admin/reports-and-dashboards` has still not given a verified record-type column for a custom report type, and the
chart-component `chartAxisRange` requirement is only visible in its example, not in its checker. `check_report_inventory.py` cannot catch
either defect offline. This is the second missing-element finding after `sortBy` (O-M4S02-04).

### Next step for the human

Re-run the same validate-only command as run 2 (§ 10; the operator runs `scripts/mock_deploy.py`). Record the accepted record-type
column name here and close U7 and U8.
