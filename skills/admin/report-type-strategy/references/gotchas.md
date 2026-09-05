# Gotchas — Report Type Strategy

Non-obvious Custom Report Type behaviors that bite in production.

---

## Gotcha 1: The CRT's join shape cannot be changed after creation

Once you click Save with "must have at least one related",
switching to "may or may not have" later requires deleting the
CRT and recreating it. All reports built on the CRT break. Get
the join semantics right the first time.

---

## Gotcha 2: 60-field display limit, 1,000-field hard limit

The CRT layout shows 60 fields by default. Past 60, fields are
findable only via search in the report builder. The hard cap is
1,000 fields; past 1,000, the CRT will not save. Curate fields
intentionally — most CRTs need under 50.

---

## Gotcha 3: Cross Filter is the way to do "without"

Salesforce supports "Accounts without Opportunities" through the
Cross Filter mechanism (the report's Filters tab), not through a
CRT join. Trying to model this in the CRT alone produces wrong
results.

---

## Gotcha 4: Person Account fields appear on both Account and Contact

In a Person Account org, fields you defined on Contact also
appear on Account in CRTs. This is expected but confusing — the
report builder may show "Account: Email" sourced from the Contact
side. Always check the field's source object before relying on
its values.

---

## Gotcha 5: Standard report types update implicitly with object changes

Standard report types add new fields to their layout when admins
add fields to the object — without a manual update. CRTs do not.
A new field on Account does not appear in your CRT until an admin
adds it. This is an upside (no surprises) and a downside (stale
field lists drift).

---

## Gotcha 6: Master-detail traversal is automatic; lookup is not

In a CRT, you can pull fields from a master-detail parent
automatically through the parent's API name. For a lookup parent,
you must add the parent as a "related via lookup" object on the
CRT — it is not auto-resolved.

---

## Gotcha 7: Deleted CRTs delete every report on them

Reports built on a deleted CRT do not migrate; they show "report
type unavailable" and must be rebuilt against a different CRT.
Before deleting, list dependent reports (Setup → Reports →
filter by Report Type).

---

## Gotcha 8: Activity reports are special

Tasks and Events have a custom storage model and do not appear as
a normal secondary object on most CRTs. The "Tasks and Events"
standard report type, the "Activities with X" standard report
types, and a few CRT options exist. Avoid trying to add Task as
a generic secondary — it produces incomplete data.

---

## Gotcha 9: Joined reports cannot use cross-block bucket fields

Bucket fields work per-block in joined reports. There is no
cross-block bucket. If you need a bucket grouping that spans
blocks, build the bucket as a formula field on the underlying
record before reporting.

---

## Gotcha 10: `<deployed>false</deployed>` Hides Reports From Non-Admins, Not From Dashboards

**What happens:** A custom report type left **In Development** is visible only to Manage Custom Report Types (typically admins). Reports on that type keep running for admins and for dashboard components, and are **invisible to everyone else** — including folders named for end users. One undeployed type can carry dozens of live reports.

**When it occurs:** "We'll deploy the type when the reports are ready" — then the reports ship and the type never flips.

**How to avoid:** Treat Deployed vs In Development as a **visibility gate**, not a WIP flag. Before sharing a folder, confirm every report's type is Deployed. Deploying a type without checking folder `sharedTo` can newly expose a pile of reports.

---

## Gotcha 11: Inner-Join Type Plus a WITHOUT Cross-Filter Is a Contradiction

**What happens:** "Accounts with Contacts" (inner join) cannot answer "accounts with no contacts." Adding `Account WITHOUT Contact` **and** a filter on `Contact.CreatedDate` is contradictory: a filter on a child field cannot coexist with a demand that the child be absent. The report silently undercounts (often by 80%+).

**When it occurs:** Cloning a with-contacts report to answer a without-contacts question.

**How to avoid:** For "A without B", use a with-or-without report type **or** a WITHOUT cross-filter — not both a child-field filter and WITHOUT. Joined (MultiBlock) reports are the unused tool for "Account + Referral + Campaign on one canvas."

---

## Gotcha 12: "Just Use the Standard Report Type" Can Be Blocked Org-Wide by a Sharing Setting

**What happens:** The obvious answer to a reporting request is a standard report type, so no custom
type is built. Users still report the data as missing. The cause is not the report type at all:
`SharingSettings.enableStandardReportVisibility` "indicates whether users can view reports based on
standard report types that may expose data of users to whom they don't have access," and the
Metadata API guide states **this field has a default value of `false`**. In an org that never
changed it, certain standard types are simply not an option for non-admin users, and a custom report
type — whose columns you control — becomes the only route.

**When it occurs:** Any standard-vs-custom decision made purely on field curation, especially in
orgs created with restrictive defaults, and in every "the standard type already covers this" review
comment.

**How to avoid:** Treat the standard-vs-custom choice as having a third input beyond join shape and
field set: the org's `enableStandardReportVisibility` value. Retrieve `SharingSettings` and read it
before recommending reuse of a standard type. If it is `false` and the requirement touches
user-owned data across the hierarchy, design the custom type. Do not flip the setting to make a
report work — it is a record-visibility control, not a reporting convenience; route that decision
through `admin/analytics-permission-and-sharing`.

---

## Gotcha 13: The Org Preference That Auto-Added New Fields to Custom Types Was Removed

**What happens:** An admin adds a field to Account and assumes it will surface in the custom report
types built on Account, because "there was a setting for that." There was:
`AnalyticsSettings.enableReportCrtAutoAddPref` — "indicates whether the feature to automatically add
new fields to relevant custom Lightning Experience report types when they're created is available."
The guide records it as **available in API version 50.0 and 51.0, removed in API version 52.0**. It
is gone. Standard report types still pick up new fields; custom ones never do.

**When it occurs:** Months after a report type is built, when a field added for an unrelated project
is expected to appear in an existing report and does not. Also in migrations, where a source org's
type and a target org's object have drifted apart.

**How to avoid:** Book the report-type column update into the same change as the field. Treat
`reportTypes/*.reportType-meta.xml` as a downstream consumer of every field addition, alongside page
layouts and permission sets — `admin/analyze-field-impact` should list report types among the
affected artifacts. A retrieve-and-diff of the type after each field wave is the cheap version.

---

## Gotcha 14: The Four-Object Maximum Constrains Joins, Not Lookup-Path Depth

**What happens:** A design is abandoned or padded with formula fields because "custom report types
only go three levels deep." The guide's actual constraint is on the join chain: "A maximum of four
objects can be joined in a custom report type." A **column** is a different thing. The guide's own
sample definition ships a five-segment lookup path —
`<field>ReportsTo.CreatedBy.Contact.Owner.MobilePhone</field>` on `<table>Account.Contacts</table>`
— which no join budget applies to.

**When it occurs:** Whenever the requested fields belong to lookup *parents* (Owner, Created By,
Contact, the Contact's Account) rather than to child records. Reviewers conflate the two limits and
send the design back for denormalization it does not need.

**How to avoid:** Before counting objects against the four-object maximum, sort each one into
"records I need to count or list" (a join) and "attributes of something already on the row" (a
column). Only the first group spends budget. `references/metadata-examples.md` § 3 shows the second
group written out; the give-away in the XML is that `table` never changes.

---

## Gotcha 15: A Section With No Columns Deploys Successfully and Produces Nothing

**What happens:** A report type is authored or trimmed until a `sections` element carries only its
`masterLabel`. The deploy succeeds. The guide is explicit that `masterLabel` is **required** on
`ReportLayoutSection` while `columns` is not — "Though columns aren't strictly required, a report
without columns isn't useful." The type appears in the report builder with a named, empty field
group, and there is no error anywhere to explain it.

**When it occurs:** Hand-edited XML, generated XML where a column loop produced nothing, and merges
that dropped columns while keeping the section wrapper. Also when a column referenced a field that
was removed and the section was emptied instead of deleted.

**How to avoid:** Make "every section has at least one column" a lint rule rather than a review
habit — `scripts/check_report_type_strategy.py` flags it. When a section legitimately empties out,
delete the section, not just its columns; an empty labelled group is worse than an absent one
because report authors keep opening it.

---

## Gotcha 16: You Cannot Count Reports Per Report Type in SOQL

**What happens:** A sprawl cleanup starts with "query the reports grouped by report type" and
stalls. The `Report` standard object's documented fields are `Description`, `DeveloperName`,
`FolderName`, `Format`, `IsDeleted`, `LastReferencedDate`, `LastRunDate`, `LastViewedDate`, `Name`,
`NamespacePrefix` and `OwnerId` — the report type is not among them, and the Object Reference
documents no `ReportType` standard object at all. The linkage exists only in the `Report` **metadata**
(`reportType`, required; `reportTypeApiName`, API version 48.0 and later). SOQL cannot see it.

**When it occurs:** Every attempt to answer "is anything using this type before I delete it?", and
every dashboard that tries to report on reporting.

**How to avoid:** Do the count from metadata. Retrieve report types with the wildcard, retrieve
reports folder by folder (`Report` rejects the wildcard), then aggregate `<reportType>` across the
retrieved XML — the command is in `references/metadata-examples.md` § Verification. Run it before
any delete, and keep the output as the evidence, because the answer is not reproducible from the org
at query time.

---

## Gotcha 17: Historical-Trending Report Types Are Autogenerated and Use `_hst` Field Names

**What happens:** Someone tries to add trended history to a hand-authored report type by adding the
normal field, or tries to curate a type they did not create. The guide's `ReportType.autogenerated`
field "indicates that the report type was automatically generated when historical trending was
enabled for an entity" (API version 29 and later), and its Usage note states that for a historical
field (one with `trackTrending` set to `true`) "the API name includes `hst`, such as
`Field2__c_hst`", on a table like `CustomTrendedObject__c.CustomTrendedObject__c_hst`. A column
naming the plain field simply reports current values.

**When it occurs:** During a wildcard retrieve, when autogenerated types show up alongside authored
ones and get pulled into a curation or deletion pass. Also whenever a "show me how this field
changed" request is answered with a normal column.

**How to avoid:** Filter `autogenerated` types out of any sprawl audit — they are a byproduct of
enabling historical trending, not a design decision, and editing them is not the supported path to
change trending. When history is genuinely needed, the field must be trended on the object first;
the `_hst` API name and its own table path are the signal that you are reading the trended copy
rather than the live field.
