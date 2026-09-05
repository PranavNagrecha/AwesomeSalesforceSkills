# Examples — Report Type Strategy

## Example 1: A-with-B inner join (primary requires secondary)

**Use case:** Renewals team needs Opportunities that have at least
one Quote. An Opportunity with no Quote should not appear.

**CRT design:**

- Primary object: Opportunity
- Secondary object: Quote
- Relationship to Primary: "Each 'A' record must have at least
  one related 'B' record"

**Why:** Inner join semantics. The report row exists only if the
Opportunity has a Quote. Opportunities without Quotes are
silently excluded from the report — which is exactly what the
renewals team wants.

---

## Example 2: A-with-or-without-B outer join

**Use case:** Sales Ops needs every Account, with the count of
Open Cases when present (zero when absent). An Account without
Cases must still appear.

**CRT design:**

- Primary object: Account
- Secondary object: Case
- Relationship: "'A' records may or may not have related 'B'
  records"

**Why:** Outer join. Account row appears regardless. Case fields
are blank when no Case exists — `RowCount` of Cases is 0.

A common bug: setting the join to "must have at least one" for
this shape, then writing a formula `IF(ISBLANK(Case.Id), 0, 1)`
to count — but the row never appears at all because the inner
join already filtered it out.

---

## Example 3: A-without-B (subtraction via joined report)

**Use case:** Find Accounts that have no Open Opportunities. CRTs
cannot directly model this — there's no "must NOT have related"
join.

**Joined report design:**

- Block 1: "Accounts" CRT, all Accounts.
- Block 2: "Accounts with Opportunities" CRT, filtered to Open.
- Filter: Block 1's Account.Id NOT IN Block 2's Account.Id.

Joined reports do not support `NOT IN` directly across blocks.
The practical workaround:

- Use a Cross Filter on a single CRT: "Accounts WITH Opportunities
  where Stage = 'Open'" → invert with the Cross Filter operator
  "without".

Cross Filters are the per-CRT mechanism for negation joins —
they avoid joined-report fragility.

---

## Example 4: Three-level CRT with related-via-lookup

**Use case:** Report on Cases, with the related Account's Industry
and the Account Owner's Region.

**CRT design:**

- Primary: Case
- Secondary: Account (via Case.AccountId)
- Tertiary: User as related to Account.OwnerId — this is a
  *related-via-lookup* join through the Owner lookup. Salesforce
  treats Owner specially; some CRTs surface "Account Owner" fields
  directly without needing the third level.

**Why:** The four-object maximum applies to the **join chain**.
Account and User here are lookup *parents* of Case, so neither
needs a join slot at all — both are dotted `field` paths on the
`Case` table. Only child relationships you want to count or list
spend budget.

Read the design as a decision table before writing any XML:

| Wanted on the row | Reached from | Costs a join slot? | Written as |
|---|---|---|---|
| Case number, status | `Case` (base) | no | `field: CaseNumber`, `table: Case` |
| Account industry | `Case.AccountId` lookup parent | no | `field: Account.Industry`, `table: Case` |
| Account owner's region | `Account.OwnerId` lookup parent of a lookup parent | no | `field: Account.Owner.Region__c`, `table: Case` |
| Every Case Comment | `Case` child relationship | **yes** (1 of 4) | `field: CommentBody`, `table: Case.CaseComments` |
| Count of Cases per Account | requires `Account` as base, not `Case` | changes `baseObject` | new report type |

The last row is the one that forces a decision: a count of
children is a join, and a join hangs off the base object, so
"count of Cases per Account" is an Account-based type — not a
Case-based type with an extra column. `baseObject` cannot be
edited later, so this is settled before creation, not after.

Deeper lookup paths are fine: the Metadata API guide's own
sample definition ships a five-segment path
(`ReportsTo.CreatedBy.Contact.Owner.MobilePhone`). See
`references/metadata-examples.md` § 3 for the full deployable
file.

---

## Example 5: Curated field layout for a 200-field object

**Bad:** All 200 fields visible in the field picker. Users scroll
endlessly, can't find "Annual Revenue", and end up using "Amount"
by mistake.

**Good:**

- **Account Information** (8 fields): Name, Owner, Industry,
  Annual Revenue, Type, Rating, Phone, Website
- **Renewal Tracking** (5 fields): Renewal Date, Renewal Owner,
  Renewal Stage, Renewal Amount, Auto-Renew Flag
- **System Fields** (4 fields): Created Date, Last Modified Date,
  Last Activity, Record Type

Hide the other 183. They are still searchable for power users
but no longer clutter the default field picker. The 60-field
display limit becomes irrelevant when the layout is this tight.

The curation is expressed entirely in `sections` and
`checkedByDefault` — the fields you leave out simply have no
`columns` entry:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: two of the three sections from
     reportTypes/Accounts_Renewal_Tracking.reportType-meta.xml.
     Wrapped in its real ReportType root so the fragment parses
     standalone; the full file also carries baseObject, category,
     deployed, description, join and label. -->
<ReportType xmlns="http://soap.sforce.com/2006/04/metadata">
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
            <displayNameOverride>ARR</displayNameOverride>
            <field>AnnualRevenue</field>
            <table>Account</table>
        </columns>
        <masterLabel>Account Information</masterLabel>
    </sections>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Renewal_Date__c</field>
            <table>Account</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Renewal_Stage__c</field>
            <table>Account</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <displayNameOverride>Auto-Renew?</displayNameOverride>
            <field>Auto_Renew__c</field>
            <table>Account</table>
        </columns>
        <masterLabel>Renewal Tracking</masterLabel>
    </sections>
</ReportType>
```

Two things to read off it. `displayNameOverride` is doing the
real disambiguation work — `ARR` is what the business calls
`AnnualRevenue`, and renaming it here is why nobody reaches for
`Amount` by mistake. And `checkedByDefault` is not visibility:
the `false` columns are still in the picker, they are just not
pre-selected on a new report. Removing a field from the picker
means deleting its `columns` element, not flipping the flag.

---

## Example 6: Documenting the CRT for the report-builder picker

**Bad description:** "Custom report type for Accounts."

**Good description:** "Use for renewal pipeline analysis.
Includes only Accounts with at least one open Renewal
Opportunity. Excludes closed-lost. For all-Accounts reporting
use the standard 'Accounts' report type instead."

The description appears in the report-builder picker. A good
description steers users to the right CRT and away from the
ones with side-effecting filters they didn't expect.
