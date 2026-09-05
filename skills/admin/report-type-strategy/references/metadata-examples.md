# Metadata Examples — Report Type Strategy

Deployable `ReportType` metadata for the three join topologies this skill routes between, plus the
manifest, the retrieve/deploy commands, and the verification step.

Scope note: `admin/reports-and-dashboards` owns the `Report`, `Dashboard`, `ReportFolder` and
`FolderShare` XML, and carries one `ReportType` example (Accounts with or without Cases). This file
owns the **topology** side — base-object choice, the join chain, lookup-path columns, and the
governance queries — and does not repeat the sibling's report or dashboard XML.

## DX layout

```text
force-app/main/default/
└── reportTypes/
    ├── Accounts_With_Cases.reportType-meta.xml
    ├── Accounts_With_Or_Without_Contacts_And_Opportunities.reportType-meta.xml
    └── Cases_With_Contact_And_Account_Lookups.reportType-meta.xml
```

The guide states the file suffix is `.reportType`, there is one file per custom report type, and
report types live in the `reportTypes` directory of the package directory. Custom report types are
available in API version 14.0 and later.
(Metadata API Developer Guide, *ReportType* → Declarative Metadata File Suffix and Directory
Location / Version.)

---

## 1. Inner join — Accounts with Cases

`force-app/main/default/reportTypes/Accounts_With_Cases.reportType-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ReportType xmlns="http://soap.sforce.com/2006/04/metadata">
    <baseObject>Account</baseObject>
    <category>accounts</category>
    <deployed>true</deployed>
    <description>Accounts that have at least one Case. Inner join: an Account with zero Cases returns no row. For every Account regardless of Cases, use Accounts with or without Cases instead.</description>
    <join>
        <outerJoin>false</outerJoin>
        <relationship>Cases</relationship>
    </join>
    <label>Accounts with Cases</label>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Name</field>
            <table>Account</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <displayNameOverride>Segment</displayNameOverride>
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
            <displayNameOverride>Account Owner Active?</displayNameOverride>
            <field>Owner.IsActive</field>
            <table>Account</table>
        </columns>
        <masterLabel>Account</masterLabel>
    </sections>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>CaseNumber</field>
            <table>Account.Cases</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <displayNameOverride>Case Status</displayNameOverride>
            <field>Status</field>
            <table>Account.Cases</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>Priority</field>
            <table>Account.Cases</table>
        </columns>
        <masterLabel>Case</masterLabel>
    </sections>
</ReportType>
```

### How to read it

- `baseObject` is **required**, and the guide states you can't edit it after initial creation.
  It also states that **all objects, including custom and external objects, are supported** as the
  base object (external-object support from API version 38.0). There is no documented allow-list of
  "reportable" standard objects to work around — if you cannot find the object in the picker, that
  is a permissions or feature-enablement question, not a metadata restriction.
- `outerJoin` is the whole join semantic. `false` here is the inner join: the report type can only
  ever produce Account rows that have a Case. No report filter can bring the childless Accounts
  back, because the report type never emitted them.
- `relationship` is the **child relationship name** as seen from the object being joined to, not an
  object API name — `Cases`, not `Case`.
- `table` is the relationship *path* from the base object: `Account` for base-object columns,
  `Account.Cases` for columns on the joined child.
- `displayNameOverride` renames the column in the report builder only. It does not rename the field
  and it does not affect the report's filter logic — a filter still targets the underlying field.
- `masterLabel` is **required** on every `sections` element. `columns` is not required, so a section
  with a label and no columns deploys cleanly and contributes nothing (see `gotchas.md`).

---

## 2. Three-object chain with directional outer joins

"Every Account, with its Contacts when it has them, and with those Contacts' Opportunities when they
exist." Nothing may be dropped at either level.

`force-app/main/default/reportTypes/Accounts_With_Or_Without_Contacts_And_Opportunities.reportType-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ReportType xmlns="http://soap.sforce.com/2006/04/metadata">
    <baseObject>Account</baseObject>
    <category>accounts</category>
    <deployed>true</deployed>
    <description>Every Account, with or without Contacts, and with or without Opportunities on the resulting dataset. Both joins are outer, so no level can drop a parent row. Three objects of the four-object maximum are used.</description>
    <join>
        <join>
            <outerJoin>true</outerJoin>
            <relationship>Opportunities</relationship>
        </join>
        <outerJoin>true</outerJoin>
        <relationship>Contacts</relationship>
    </join>
    <label>Accounts with or without Contacts and Opportunities</label>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Name</field>
            <table>Account</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <displayNameOverride>Segment</displayNameOverride>
            <field>Industry</field>
            <table>Account</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>Type</field>
            <table>Account</table>
        </columns>
        <masterLabel>Account</masterLabel>
    </sections>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <displayNameOverride>Contact Name</displayNameOverride>
            <field>Name</field>
            <table>Account.Contacts</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>Title</field>
            <table>Account.Contacts</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <displayNameOverride>Contact Owner Email</displayNameOverride>
            <field>Owner.Email</field>
            <table>Account.Contacts</table>
        </columns>
        <masterLabel>Contact</masterLabel>
    </sections>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <displayNameOverride>Opportunity Name</displayNameOverride>
            <field>Name</field>
            <table>Account.Contacts.Opportunities</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>StageName</field>
            <table>Account.Contacts.Opportunities</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Amount</field>
            <table>Account.Contacts.Opportunities</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>CloseDate</field>
            <table>Account.Contacts.Opportunities</table>
        </columns>
        <masterLabel>Opportunity</masterLabel>
    </sections>
</ReportType>
```

### How to read it

- **Nesting is join order, and it reads inside-out relative to the XML indentation.** The guide is
  explicit: "The `baseObject` is first joined to the object specified in `relationship`; the
  resulting dataset is then joined with any objects specified in this field [`join`]." So the
  *outer* `<join>` element's `relationship` (`Contacts`) is join #1, and the *nested* `<join>`
  element's `relationship` (`Opportunities`) is join #2. Reading the file top-down gives the join
  order backwards, which is a reliable source of review mistakes.
- Because join #2 is applied to the **dataset** produced by join #1, not to `Contact` in isolation,
  the second `relationship` name is resolved against that dataset. Confirm the exact name by
  retrieving an existing report type of the same shape rather than guessing from the schema.
- **Direction matters and it is one-way.** The guide states a maximum of four objects can be joined
  in one custom report type, and that "when more than two objects are joined, an inner join isn't
  allowed if there has been an outer join earlier in the join sequence." Both joins are outer here,
  so the rule is satisfied. Had join #1 been outer and join #2 inner, this file would be invalid.
- Three objects are used (`Account`, `Contact`, `Opportunity`), leaving exactly one join slot. That
  budget is the reason to reach for lookup-path columns (example 3) before spending a slot.
- `table` extends with each level: `Account` → `Account.Contacts` → `Account.Contacts.Opportunities`.
- `category` is a restricted enum. The valid values per the guide are `accounts`, `opportunities`,
  `forecasts`, `cases`, `leads`, `campaigns`, `activities`, `busop`, `products`, `admin`,
  `territory`, `territory2`, `usage_entitlement`, `wdc`, `calibration`, `other`, `content`,
  `quotes`, `individual`, `employee`, `data_cloud`, `commerce`, `flow`, `semantic_model`.

---

## 3. Lookup-path columns — reaching a parent without spending a join

"Report on Cases, showing the related Contact's details and that Contact's Account industry."
`Contact` and `Account` are **lookup parents** of `Case`, so they are reached as dotted `field`
paths on the `Case` table — not as joins.

`force-app/main/default/reportTypes/Cases_With_Contact_And_Account_Lookups.reportType-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ReportType xmlns="http://soap.sforce.com/2006/04/metadata">
    <baseObject>Case</baseObject>
    <category>cases</category>
    <deployed>true</deployed>
    <description>Cases with Contact and Account attributes pulled through lookup paths rather than joins, plus an optional Case Comments join. Only one of the four join slots is spent.</description>
    <join>
        <outerJoin>true</outerJoin>
        <relationship>CaseComments</relationship>
    </join>
    <label>Cases with Contact and Account lookups</label>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>CaseNumber</field>
            <table>Case</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Status</field>
            <table>Case</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <displayNameOverride>Case Owner Email</displayNameOverride>
            <field>Owner.Email</field>
            <table>Case</table>
        </columns>
        <masterLabel>Case</masterLabel>
    </sections>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <displayNameOverride>Contact Full Name</displayNameOverride>
            <field>Contact.Name</field>
            <table>Case</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <displayNameOverride>Contact Email</displayNameOverride>
            <field>Contact.Email</field>
            <table>Case</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <displayNameOverride>Contact Account Industry</displayNameOverride>
            <field>Contact.Account.Industry</field>
            <table>Case</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <displayNameOverride>Contact Owner Mobile</displayNameOverride>
            <field>Contact.Owner.MobilePhone</field>
            <table>Case</table>
        </columns>
        <masterLabel>Contact (via lookup)</masterLabel>
    </sections>
    <sections>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <displayNameOverride>Comment Body</displayNameOverride>
            <field>CommentBody</field>
            <table>Case.CaseComments</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>CreatedDate</field>
            <table>Case.CaseComments</table>
        </columns>
        <masterLabel>Case Comment</masterLabel>
    </sections>
</ReportType>
```

### How to read it

- **A lookup parent's fields are columns, not joins.** `table` stays `Case`; the traversal lives in
  the `field` value. The guide's own sample does exactly this: `<field>Owner.IsActive</field>` with
  `<table>Account</table>`, and `<field>ReportsTo.CreatedBy.Contact.Owner.MobilePhone</field>` with
  `<table>Account.Contacts</table>`.
- That second sample is a **five-segment** field path, so the four-object maximum constrains the
  **join chain**, not the depth of a lookup-path column. Conflating the two is the most common
  authoring error in this area — it makes people burn join slots on objects they could have reached
  for free.
- Grouping the lookup columns into their own `sections` element (`Contact (via lookup)`) is a
  layout choice, not a structural one: every column in that section still declares
  `<table>Case</table>`. The section label is what tells a report author where the data came from.
- A lookup path returns blank rather than dropping the row when the lookup is empty. That is why
  this shape is not a substitute for an outer join to a **child** — it answers "attributes of my
  parent", never "how many children do I have".
- Because these columns are not joins, they are also not subject to the inner-after-outer ordering
  rule. Adding one to an existing report type cannot invalidate its join sequence.

---

## "A without B" is a report-level recipe, not a report type

There is no negation join. `ObjectRelationship` exposes only `outerJoin` (boolean), `relationship`
and a recursive `join` — nothing that expresses "must not have". The deployable pattern is:

1. Build (or reuse) the simplest report type that emits every parent — `Accounts with or without
   Cases`, or a bare `Account` type with no `join` at all.
2. Express the negation on the **report**, as a cross filter with `operation` `without`.

The cross-filter XML lives on the `Report` metadata type and is owned by
`admin/reports-and-dashboards` — see its `references/metadata-examples.md` for the `crossFilters`
block and its gotcha on outer joins and `with` cross filters cancelling each other out. Do not build
a second report type for the negation; the report type stays the superset and the report subtracts.

---

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>ReportType</name>
    </types>
    <version>62.0</version>
</Package>
```

### How to read it

- `ReportType` **accepts the `*` wildcard**, unlike `Report`, `Dashboard`, `Folder` and
  `FolderShare`. See `admin/reports-and-dashboards` → `references/gotchas.md`, which grounds this
  against the guide's per-type wildcard statements. This is what makes a whole-org report-type
  inventory a one-command operation, and it is the starting point for every sprawl audit below.
- A wildcard retrieve also pulls **autogenerated** types — the guide's `autogenerated` field marks
  report types created automatically when historical trending was enabled for an entity (API version
  29 and later). Exclude those from a sprawl review; they are not yours to curate.
- Named members are the developer name (`fullName`), which "can contain only underscores and
  alphanumeric characters. It must be unique, begin with a letter, not include spaces, not end with
  an underscore, and not contain two consecutive underscores." A member with a space is a pasted
  label.

---

## Retrieve and deploy

```bash
# Inventory every report type in the org — the wildcard makes this exhaustive.
sf project retrieve start --manifest manifest/package.xml --target-org myOrg

# Retrieve one type by name, e.g. to copy a working relationship name before authoring a new chain.
sf project retrieve start \
  --metadata "ReportType:Accounts_With_Or_Without_Contacts_And_Opportunities" \
  --target-org myOrg

# Lint the source tree before you deploy anything.
python3 skills/admin/report-type-strategy/scripts/check_report_type_strategy.py \
  --manifest-dir force-app/main/default

# Validate without committing.
sf project deploy start --manifest manifest/package.xml --dry-run --target-org myOrg

# Deploy.
sf project deploy start --manifest manifest/package.xml --target-org myOrg
```

Deploy order: the report type must land before any `Report` that names it in `<reportType>`. A
single `package.xml` deploy resolves that itself; splitting report types and reports across two
deploys does not.

---

## Verification

### 1. The report type is deployed and visible

```bash
sf org list metadata --metadata-type ReportType --target-org myOrg
```

The retrieved XML is the authority on `deployed`. A type with `<deployed>false</deployed>` is
present in this listing and still absent from the report builder for everyone without Manage Custom
Report Types.

### 2. Report inventory

```sql
SELECT Id, Name, DeveloperName, FolderName, Format, LastRunDate
FROM Report
ORDER BY FolderName, DeveloperName
```

`Format` values are `Tabular`, `Summary`, `Matrix`, `Multiblock` (Object Reference, *Report*).
`Multiblock` is the joined-report signal — a cluster of them usually means someone worked around a
report type that couldn't express the shape.

### 3. Reports per report type — **not queryable**

The `Report` standard object's documented fields are `Description`, `DeveloperName`, `FolderName`,
`Format`, `IsDeleted`, `LastReferencedDate`, `LastRunDate`, `LastViewedDate`, `Name`,
`NamespacePrefix` and `OwnerId`. **None of them is the report type**, and the Object Reference
documents no `ReportType` standard object at all. So there is no SOQL that counts reports per report
type.

The report type lives only in the `Report` **metadata**, where `reportType` is required and
`reportTypeApiName` exists from API version 48.0. Count it from a retrieve:

```bash
# Retrieve reports (enumerate folders first — Report does not accept the wildcard), then count.
grep -ho '<reportType>[^<]*</reportType>' \
  force-app/main/default/reports/**/*.report-meta.xml \
  | sed 's|</\{0,1\}reportType>||g' \
  | sort | uniq -c | sort -rn
```

Zero-count types in that output are deletion candidates; a type with one report is a candidate for
merging into a broader type. UNVERIFIED (2026-09-04): the Setup UI is documented to show a report
type's dependent reports, but help.salesforce.com cannot be fetched from this environment, so the
exact Setup path is not asserted here — the metadata count above is the verifiable route.

### 4. Limits

UNVERIFIED (2026-09-04): the Salesforce App Limits Cheat Sheet contains **no** occurrence of the
word "report", so it publishes no per-edition cap on the number of custom report types, reports per
type, or fields per type. The only numeric constraint this skill asserts from a primary source is
the four-object join maximum in the Metadata API Developer Guide. Field-count figures elsewhere in
this package rest on the help-topic sources listed in `well-architected.md`.

---

## Sources

- Metadata API Developer Guide — *ReportType*, *ObjectRelationship*, *ReportLayoutSection*,
  *ReportTypeColumn*, the Declarative Metadata Sample Definition, and the Usage note on historical
  (`_hst`) field names.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — *Report* (`reportType`, `reportTypeApiName`, `block`, `format`).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform — *Report* standard object field list and
  `Format` picklist values.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- `admin/reports-and-dashboards` → `references/metadata-examples.md`, `references/gotchas.md`
  (wildcard support, cross filters, folder sharing).
