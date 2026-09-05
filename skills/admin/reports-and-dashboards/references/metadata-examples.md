# Metadata Examples: Reports, Dashboards, Report Types, Folders

Deployable source-format XML for the four metadata types this skill produces, shaped from the
sample definitions and field tables in the Metadata API Developer Guide (Summer '26 / v62 PDF).

Source-format layout (`sf project` / SFDX):

```text
force-app/main/default/
├── reportTypes/
│   └── Accounts_With_Or_Without_Cases.reportType-meta.xml
├── reports/
│   ├── Revenue_Ops.reportFolder-meta.xml
│   └── Revenue_Ops/
│       └── Open_Cases_By_Owner.report-meta.xml
└── dashboards/
    ├── Revenue_Ops.dashboardFolder-meta.xml
    └── Revenue_Ops/
        └── Support_Load.dashboard-meta.xml
```

The Metadata API guide names the *MDAPI* suffixes for these types: reports live in the `reports`
directory with the extension `.report`; dashboards in `dashboards` with `.dashboard`; report types
in `reportTypes` with `.reportType`; and each folder gets an accompanying
`FolderName.folderType-meta.xml` file at the same directory level as the folder. The `-meta.xml`
suffixes above are the source-format equivalents the `sf` CLI reads and writes.

---

## 1. Custom Report Type — Accounts with or without Cases

`force-app/main/default/reportTypes/Accounts_With_Or_Without_Cases.reportType-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ReportType xmlns="http://soap.sforce.com/2006/04/metadata">
    <baseObject>Account</baseObject>
    <category>accounts</category>
    <deployed>true</deployed>
    <description>Accounts with or without Cases. Outer join so Accounts with zero Cases still return a row.</description>
    <join>
        <outerJoin>true</outerJoin>
        <relationship>Cases</relationship>
    </join>
    <label>Accounts with or without Cases</label>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Name</field>
            <table>Account</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Industry</field>
            <table>Account</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>AnnualRevenue</field>
            <table>Account</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>Owner.IsActive</field>
            <table>Account</table>
        </columns>
        <masterLabel>Accounts</masterLabel>
    </sections>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>CaseNumber</field>
            <table>Account.Cases</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Status</field>
            <table>Account.Cases</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Priority</field>
            <table>Account.Cases</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>CreatedDate</field>
            <table>Account.Cases</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>Owner.Email</field>
            <table>Account.Cases</table>
        </columns>
        <masterLabel>Cases</masterLabel>
    </sections>
</ReportType>
```

### How to read it

- `baseObject` is **required and permanently fixed** — the guide states you can't edit it after
  initial creation. Changing the primary object means a new report type, not an edit.
- `outerJoin` is the single element that decides whether Accounts with zero Cases appear.
  `true` = A-with-or-without-B; `false` = inner join, only Accounts that have at least one Case.
- `join` nests recursively to chain objects. A maximum of **four objects** can be joined in one
  custom report type, and once an outer join appears in the sequence, no inner join is allowed
  later in that sequence.
- `deployed` is what makes the report type visible to report authors. `false` leaves it "in
  development" — deployable, invisible, and a common cause of "the report type isn't in the list."
- `sections` are the column groups the report builder shows. `table` is the relationship path from
  the base object (`Account`, `Account.Cases`); `field` is the field API name on that table.
- `checkedByDefault` only pre-selects the column for a *new* report. It changes nothing on reports
  that already exist.
- `category` is a restricted enum: `accounts`, `opportunities`, `forecasts`, `cases`, `leads`,
  `campaigns`, `activities`, `busop`, `products`, `admin`, `territory`, `territory2`,
  `usage_entitlement`, `wdc`, `calibration`, `other`, `content`, `quotes`, `individual`,
  `employee`, `data_cloud`, `commerce`, `flow`, `semantic_model`.

---

## 2. Summary report — Cases grouped by Owner, with a cross filter and a bucket

`force-app/main/default/reports/Revenue_Ops/Open_Cases_By_Owner.report-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://soap.sforce.com/2006/04/metadata">
    <buckets>
        <bucketType>number</bucketType>
        <developerName>BucketField_AccountSize</developerName>
        <masterLabel>Account Size</masterLabel>
        <nullTreatment>z</nullTreatment>
        <sourceColumnName>SALES</sourceColumnName>
        <values>
            <sourceValues>
                <to>1000000</to>
            </sourceValues>
            <value>SMB</value>
        </values>
        <values>
            <sourceValues>
                <from>1000000</from>
                <to>50000000</to>
            </sourceValues>
            <value>Mid-Market</value>
        </values>
        <values>
            <sourceValues>
                <from>50000000</from>
            </sourceValues>
            <value>Enterprise</value>
        </values>
    </buckets>
    <chart>
        <chartSummaries>
            <column>RowCount</column>
        </chartSummaries>
        <chartType>HorizontalBar</chartType>
        <groupingColumn>BucketField_AccountSize</groupingColumn>
        <legendPosition>Bottom</legendPosition>
        <location>CHART_TOP</location>
        <size>Medium</size>
    </chart>
    <columns>
        <field>ACCOUNT_NAME</field>
    </columns>
    <columns>
        <field>BucketField_AccountSize</field>
    </columns>
    <columns>
        <field>STATUS</field>
    </columns>
    <columns>
        <field>AGE</field>
        <aggregateTypes>Average</aggregateTypes>
        <aggregateTypes>Maximum</aggregateTypes>
    </columns>
    <crossFilters>
        <criteriaItems>
            <column>Status</column>
            <operator>notEqual</operator>
            <value>Closed</value>
        </criteriaItems>
        <operation>with</operation>
        <primaryTableColumn>ACCOUNT_ID</primaryTableColumn>
        <relatedTable>Case</relatedTable>
        <relatedTableJoinColumn>Account</relatedTableJoinColumn>
    </crossFilters>
    <description>Open cases by owner, bucketed by account revenue band. Owned by Revenue Ops.</description>
    <filter>
        <booleanFilter>1 AND 2</booleanFilter>
        <criteriaItems>
            <column>STATUS</column>
            <operator>notEqual</operator>
            <value>Closed</value>
        </criteriaItems>
        <criteriaItems>
            <column>PRIORITY</column>
            <operator>notEqual</operator>
            <value>Low</value>
        </criteriaItems>
    </filter>
    <format>Summary</format>
    <groupingsDown>
        <field>USERS.NAME</field>
        <sortOrder>Asc</sortOrder>
    </groupingsDown>
    <name>Open Cases by Owner</name>
    <reportType>Accounts_With_Or_Without_Cases</reportType>
    <scope>organization</scope>
    <showDetails>false</showDetails>
    <showGrandTotal>true</showGrandTotal>
    <showSubTotals>true</showSubTotals>
    <timeFrameFilter>
        <dateColumn>CREATED_DATE</dateColumn>
        <interval>INTERVAL_LAST90</interval>
    </timeFrameFilter>
</Report>
```

> **UNVERIFIED (2026-09-04) — do not deploy the column codes as written.** The codes above
> (`ACCOUNT_NAME`, `STATUS`, `PRIORITY`, `AGE`, `USERS.NAME`, `SALES`, `CREATED_DATE`,
> `ACCOUNT_ID`) are taken from the column codes the Metadata API guide uses in its own `Report`
> and `Dashboard` sample definitions. The guide does **not** publish the code list for a *custom*
> report type built on Account + Cases, so the exact codes for this report type are unconfirmed.
> Retrieve one working report on the same report type from the target org and copy its codes
> before deploying. Every other element in the block — structure, enums, element names — is from
> the guide's field tables.

### How to read it

- **Report column codes are not field API names.** `<columns><field>` takes a report column code
  (`AMOUNT`, `AGE`, `OPPORTUNITY_NAME`, `ACCOUNT_ID`) whose value depends on the report type. The
  guide's own samples use `Object$Field` form for custom report types (`CRT_Object__c$Name`).
  Never guess these — retrieve an existing report on the same report type and read them off.
- `filter` vs `crossFilters` are different mechanisms. `filter/criteriaItems` narrows *rows*.
  `crossFilters` narrows the *parent object by child existence*: `operation` is `with` or
  `without`, `relatedTable` is the child object, and `relatedTableJoinColumn` is the child field
  that joins back to the parent. Up to five sub-filters per cross filter.
- `booleanFilter` numbers the `criteriaItems` in document order, starting at 1. Reordering the
  `criteriaItems` blocks silently rewires the logic.
- `operator` is a fixed enum: `equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`,
  `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`, and `within`
  (DISTANCE criteria only).
- `groupingsDown` is capped at **3** for Summary and **2** for Matrix; `groupingsAcross` is capped
  at 2 and only applies to Matrix. Add `dateGranularity` (`Day`/`Week`/`Month`/`Quarter`/`Year`/
  `FiscalQuarter`/`FiscalYear`/…) when the grouping field is a date.
- `format` is `Tabular`, `Summary`, `Matrix`, or `Joined` in the metadata enum. Note that the
  guide's own joined-report sample writes `<format>MultiBlock</format>`, and the `Report` sObject's
  `Format` picklist returns `Multiblock` for joined reports — three spellings for one concept.
  Match whatever a retrieve of the target org returns.
- `timeFrameFilter` is a separate element from `filter`. `interval` is an enum (`INTERVAL_LAST90`,
  `INTERVAL_CURFY`, `INTERVAL_THISMONTH`, …); use `INTERVAL_CUSTOM` with `startDate`/`endDate`
  only when the range genuinely must not move.
- `scope` decides whose records the report considers. Values depend on the report type — for
  Accounts reports the guide lists `MyAccounts`, `MyTeamsAccounts`, `AllAccounts`; the guide's
  sample report uses `organization`. This is a *third* independent layer on top of record sharing
  and the dashboard running user.
- Numeric `buckets` use `to` only on the first value and `from` only on the last; every value in
  between needs both. `nullTreatment` is `z` (empty = zero) or `n`. `developerName` must start
  with `BucketField_` and is what `columns`, `groupingsDown` and `chart/groupingColumn` reference.
- `rowLimit` exists but is not compatible with historical trend reports.

---

## 3. Dashboard — two components on that report, with a filter and a stated running user

`force-app/main/default/dashboards/Revenue_Ops/Support_Load.dashboard-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Dashboard xmlns="http://soap.sforce.com/2006/04/metadata">
    <backgroundEndColor>#FFFFFF</backgroundEndColor>
    <backgroundFadeDirection>Diagonal</backgroundFadeDirection>
    <backgroundStartColor>#FFFFFF</backgroundStartColor>
    <chartTheme>light</chartTheme>
    <colorPalette>colorSafe</colorPalette>
    <dashboardFilters>
        <dashboardFilterOptions>
            <operator>equals</operator>
            <values>Manufacturing</values>
        </dashboardFilterOptions>
        <dashboardFilterOptions>
            <operator>equals</operator>
            <values>Technology</values>
        </dashboardFilterOptions>
        <name>Industry</name>
    </dashboardFilters>
    <dashboardType>LoggedInUser</dashboardType>
    <description>Open support load by owner and account size. Each viewer sees only their own records.</description>
    <leftSection>
        <columnSize>Medium</columnSize>
        <components>
            <chartAxisRange>Auto</chartAxisRange>
            <componentType>Bar</componentType>
            <dashboardFilterColumns>
                <column>INDUSTRY</column>
            </dashboardFilterColumns>
            <displayUnits>Auto</displayUnits>
            <drillEnabled>true</drillEnabled>
            <drillToDetailEnabled>false</drillToDetailEnabled>
            <enableHover>true</enableHover>
            <expandOthers>false</expandOthers>
            <header>Open cases</header>
            <legendPosition>Bottom</legendPosition>
            <report>Revenue_Ops/Open_Cases_By_Owner</report>
            <showPercentage>false</showPercentage>
            <showValues>true</showValues>
            <sortBy>RowValueDescending</sortBy>
            <title>By owner</title>
            <useReportChart>false</useReportChart>
        </components>
    </leftSection>
    <rightSection>
        <columnSize>Medium</columnSize>
        <components>
            <componentType>Metric</componentType>
            <dashboardFilterColumns>
                <column>INDUSTRY</column>
            </dashboardFilterColumns>
            <displayUnits>Auto</displayUnits>
            <drillEnabled>false</drillEnabled>
            <drillToDetailEnabled>false</drillToDetailEnabled>
            <header>Total open</header>
            <metricLabel>Open cases (last 90 days)</metricLabel>
            <report>Revenue_Ops/Open_Cases_By_Owner</report>
            <title>Volume</title>
            <useReportChart>false</useReportChart>
        </components>
    </rightSection>
    <textColor>#000000</textColor>
    <title>Support Load</title>
    <titleColor>#000000</titleColor>
    <titleSize>12</titleSize>
</Dashboard>
```

### How to read it

- **Running user semantics.** `dashboardType` has three values and it, not `runningUser`, is the
  security decision:
  - `LoggedInUser` — each logged-in user sees data at their own access level. That is what this
    example uses, and it is why no `runningUser` element appears.
  - `SpecifiedUser` — **all** users see data at the access level of the one user named in
    `runningUser`, regardless of their own security settings. The guide's own wording: "Regardless
    of their security settings, all users viewing a dashboard see exactly the same data."
  - `MyTeamUser` — managers can view the dashboard from the point of view of subordinates in the
    role hierarchy.
- `runningUser` takes a **username**, and the guide states that on deploy, if the value is
  undefined or doesn't match a valid user, the field is populated with the username of the user
  performing the deployment. A `SpecifiedUser` dashboard therefore never fails loudly on a bad
  username — it quietly re-points at whoever ran the deploy.
- `backgroundEndColor`, `backgroundFadeDirection`, `backgroundStartColor`, `textColor`, `title`,
  `titleColor`, `titleSize`, `leftSection` and `rightSection` are all **required**.
  `middleSection` is optional. A three-section dashboard is the Salesforce Classic shape; for the
  Lightning grid set `isGridLayout` to `true` and use `dashboardGridLayout`
  (`numberOfColumns`, `rowHeight`, and `dashboardGridComponents` with `colSpan`/`rowSpan`/
  `columnIndex`/`rowIndex`).
- `<report>` is `folderDeveloperName/reportDeveloperName` — a **developer name**, not a title.
- **A dashboard filter only reaches a component that declares `dashboardFilterColumns`.** The
  guide: "Each report-based component must have a dashboard filter column that defines the column
  that the filter applies to." A component missing this element renders normally and silently
  ignores the filter.
- `dashboardFilterOptions/operator` accepts `between`, which takes two operands and is
  min-inclusive / max-exclusive. Every other dashboard filter operator takes one operand.
- `componentType` is required. Valid values include `Bar`, `Column`, `Donut`, `Funnel`, `Gauge`,
  `Line`, `Metric`, `Pie`, `Table`, `FlexTable`, `Scatter`, `Image`, `RichText`,
  `PulseMetricCard`, `LightningWebComponent`, `VisualforcePage`, `SControl`.
- `drillDownUrl` overrides `drillEnabled`, which in turn overrides `drillToDetailEnabled`. Setting
  all three does not combine them; the highest-precedence one wins.

---

## 4. Folders — access type and sharing

`force-app/main/default/reports/Revenue_Ops.reportFolder-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ReportFolder xmlns="http://soap.sforce.com/2006/04/metadata">
    <accessType>Shared</accessType>
    <name>Revenue Ops</name>
    <folderShares>
        <accessLevel>View</accessLevel>
        <sharedTo>Support_Manager</sharedTo>
        <sharedToType>Role</sharedToType>
    </folderShares>
    <folderShares>
        <accessLevel>Manage</accessLevel>
        <sharedTo>Revenue_Ops_Admins</sharedTo>
        <sharedToType>Group</sharedToType>
    </folderShares>
</ReportFolder>
```

`force-app/main/default/dashboards/Revenue_Ops.dashboardFolder-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DashboardFolder xmlns="http://soap.sforce.com/2006/04/metadata">
    <accessType>Shared</accessType>
    <name>Revenue Ops</name>
    <folderShares>
        <accessLevel>View</accessLevel>
        <sharedTo>Support_Manager</sharedTo>
        <sharedToType>Role</sharedToType>
    </folderShares>
</DashboardFolder>
```

### How to read it

- `accessType` is required and has four values: `Shared` (only the specified set of users),
  `Public` (all users **including portal users**), `PublicInternal` (all users excluding portal
  users — report and dashboard folders in orgs with a partner portal or Customer Portal), and
  `Hidden`.
- `Public` on a report folder is not "public to the company." It is public to portal users too.
  `PublicInternal` is the setting most orgs mean when they say public.
- `publicFolderAccess` (`ReadOnly` / `ReadWrite`) only has meaning when `accessType` is `Public`.
- `folderShares/accessLevel` is `View`, `EditAllContents`, or `Manage`. `sharedToType` covers
  `Role`, `RoleAndSubordinatesInternal`, `Group`, `Manager`, `ManagerAndSubordinatesInternal`,
  `Organization`, `Territory`, `User`, and the portal variants.
- **Folder access is not record access.** `View` on the folder lets a user run the report; which
  rows come back is still decided by sharing and by the report's `scope`.
- The guide carries an explicit warning: **during package installation, `FolderShare` for
  `DashboardFolder` and `ReportFolder` is ignored.** Folder sharing that rides in a managed or
  unlocked package does not land. Re-apply it in the target org.

---

## 5. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Accounts_With_Or_Without_Cases</members>
        <name>ReportType</name>
    </types>
    <types>
        <members>Revenue_Ops</members>
        <members>Revenue_Ops/Open_Cases_By_Owner</members>
        <name>Report</name>
    </types>
    <types>
        <members>Revenue_Ops</members>
        <members>Revenue_Ops/Support_Load</members>
        <name>Dashboard</name>
    </types>
    <version>62.0</version>
</Package>
```

### How to read it

- **Neither `Report` nor `Dashboard` accepts `<members>*</members>.** The guide states the
  restriction separately for each type, and `Folder` and `FolderShare` don't accept it either.
  `ReportType` **does** support the wildcard — it is the one type in this package that can.
- A report or dashboard member is `<folder developer name>/<item developer name>`, and the guide is
  explicit that "the names used in package.xml must be developer names, not dashboard titles."
  A member containing a space is almost always a pasted label.
- To retrieve `ReportFolder` / `DashboardFolder`, use the **`Report` / `Dashboard`** type in
  `package.xml` and list the folder as a bare member (`Revenue_Ops` above). There is no
  `ReportFolder` entry in `describeMetadata()`; `Report` comes back with `inFolder` set to `true`,
  which is how you know to construct the folder type name.
- A **nested** folder referenced on its own needs a trailing slash:
  `<members>TopLevel/SubLevel/</members>`. Omitting it fails with
  `Entity of type 'Report' named 'TopLevel/SubLevel' cannot be found` — the API reads the path as
  a report named `SubLevel`.
- Only *custom* reports are supported by the `Report` metadata type. Standard reports are not.

To enumerate members for a real org (no wildcard available):

```bash
# 1. list the report folders
sf org list metadata --metadata-type ReportFolder --target-org myOrg

# 2. list the reports inside each folder returned by step 1
sf org list metadata --metadata-type Report --folder Revenue_Ops --target-org myOrg

# 3. same two steps for dashboards
sf org list metadata --metadata-type DashboardFolder --target-org myOrg
sf org list metadata --metadata-type Dashboard --folder Revenue_Ops --target-org myOrg
```

---

## 6. Retrieve and deploy

```bash
# Retrieve the existing shape first — this is the only reliable way to learn the
# report column codes for a given report type.
sf project retrieve start \
  --metadata "ReportType:Accounts_With_Or_Without_Cases" \
  --metadata "Report:Revenue_Ops/Open_Cases_By_Owner" \
  --metadata "Dashboard:Revenue_Ops/Support_Load" \
  --target-org myOrg

# Validate without committing anything.
sf project deploy start --manifest manifest/package.xml --dry-run --target-org myOrg

# Deploy for real.
sf project deploy start --manifest manifest/package.xml --target-org myOrg
```

Deploy order matters within one package: the report type must exist before the report that names
it in `<reportType>`, and the report before the dashboard that names it in `<report>`. A single
`package.xml` deploy resolves this itself; splitting it across deploys does not.

---

## 7. Verification

Run the skill's checker against the source tree before deploying:

```bash
python3 scripts/check_report_inventory.py --manifest-dir force-app/main/default
```

After deploying, verify in the org with SOQL. Both `Report` and `Dashboard` are read-only sObjects
supporting `query()`, `retrieve()` and `search()`:

```sql
SELECT Id, DeveloperName, Name, FolderName, Format, LastRunDate, OwnerId
FROM Report
WHERE FolderName = 'Revenue Ops'
```

```sql
SELECT Id, DeveloperName, Title, FolderName, Type, RunningUserId, LastViewedDate
FROM Dashboard
WHERE FolderName = 'Revenue Ops'
```

Expected: `Format` = `Summary` for the report, `Type` = `LoggedInUser` for the dashboard.

Two traps in reading those results:

- **`RunningUserId` is populated even on a `LoggedInUser` dashboard.** The guide states that for a
  dashboard created in Lightning Experience and configured to run as the viewing user, the field
  returns the *creator's* user ID; for one created in Salesforce Classic and set to run as the
  logged-in user, it returns the last specified running user. Filter on `Type`, never on
  `RunningUserId IS NOT NULL`, when hunting `SpecifiedUser` dashboards.
- **`LastViewedDate` is per-querying-user**, and null means the current user may have accessed but
  not viewed the record. `LastRunDate` on `Report` is org-wide but is bumped by dashboard
  refreshes and API runs, not only by humans.

To sweep private folders you need `USING SCOPE`. The supported scopes on both objects are
`allPrivate`, `created`, `everything` and `mine`; `Report` adds `organizationOwned` (records in
Unfiled Public Reports, shown as "Public Reports" in Lightning). `allPrivate` requires the
**Manage All Private Reports and Dashboards** permission plus Enhanced Analytics Folder Sharing:

```sql
SELECT Id, Name, OwnerId FROM Report USING SCOPE allPrivate WHERE LastRunDate = NULL
```

Setup check, for the two things SOQL cannot see: open the dashboard and confirm the filter
actually moves every component (a component with no `dashboardFilterColumns` will not move), and
open **Setup → Report Types** to confirm the new report type shows as *Deployed*, not *In
Development*.
