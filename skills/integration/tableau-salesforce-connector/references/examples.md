# Examples — Tableau ↔ Salesforce Connector

Worked artifacts for the patterns in `SKILL.md`.

---

## Example 1: Find the fields that will silently disappear from the extract

**Context:** A finance dashboard is scoped against Opportunity. Half the agreed
metrics are formula fields.

**Problem:** Tableau's Salesforce connector excludes calculated fields and text
fields over 4096 characters from the extract. Nothing errors — the columns are
simply absent when the data source loads, usually discovered mid-build.

**Solution:** Enumerate them up front from `FieldDefinition`.

```bash
sf data query --target-org prod --result-format csv \
  --query "SELECT QualifiedApiName, Label, DataType
           FROM FieldDefinition
           WHERE EntityDefinition.QualifiedApiName = 'Opportunity'
             AND (DataType LIKE 'Formula%' OR DataType = 'Long Text Area')
           ORDER BY QualifiedApiName" \
  > opportunity-fields-not-in-extract.csv
```

**Why it works:** `FieldDefinition` reports the type as `Formula (Currency)`,
`Formula (Number)` and so on, so the `LIKE 'Formula%'` predicate catches every
flavour in one pass. The CSV becomes the decision list: for each row, either
re-implement the logic as a Tableau calculated field or materialise it into a
stored field in Salesforce. Run it per object before sign-off, not after.

---

## Example 2: A least-privilege Tableau integration user

**Context:** The Tableau connection was set up with a cloned System
Administrator profile "to unblock the pilot".

**Problem:** The extract inherits the connecting user's sharing and field-level
security, so that clone makes every dashboard an org-wide data export. It also
makes the API allocation consumed by refreshes indistinguishable from
administrator activity in the API usage report.

**Solution:** A dedicated user on a minimal profile, with a purpose-built
permission set.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Tableau Extract Read</label>
    <description>Read-only API access for the Tableau extract service account.
        Scope is the reporting surface only; widen deliberately, never by
        cloning an admin profile.</description>

    <!-- Without this the connector fails at sign-in, not at query time. -->
    <userPermissions>
        <enabled>true</enabled>
        <name>ApiEnabled</name>
    </userPermissions>

    <objectPermissions>
        <object>Opportunity</object>
        <allowRead>true</allowRead>
        <allowCreate>false</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>true</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>

    <fieldPermissions>
        <field>Opportunity.Amount</field>
        <readable>true</readable>
        <editable>false</editable>
    </fieldPermissions>
    <fieldPermissions>
        <field>Opportunity.NextStep</field>
        <readable>true</readable>
        <editable>false</editable>
    </fieldPermissions>

    <!-- No entry for Opportunity.StageName or Opportunity.CloseDate: they are
         required fields, and "In API version 30.0 and later, permissions for
         required fields can't be retrieved or deployed." Required fields ride
         on the object permission and land in the extract regardless. -->
</PermissionSet>
```

**Why it works:** `ApiEnabled` is the permission the connector actually needs and
the one most often missing when a business-user profile is cloned. `viewAllRecords`
is granted deliberately and visibly here because a reporting extract usually does
need to cross sharing — writing it in metadata makes that a reviewed decision
rather than an inherited one. Field permissions are enumerated, so the dashboard's
column list and the security model are the same artifact — with the caveat that
required fields cannot appear there and are therefore always in scope.

---

## Example 3: Refresh-schedule budget against the org's API allocation

**Context:** Twelve workbooks, and a request to move them all to hourly refresh.

**Problem:** Refreshes draw on the same 24-hour API allocation as every
integration in the org, and large extracts are long-running requests that also
compete for the concurrent-request pool (25 for production orgs and sandboxes)
whose exhaustion returns `REQUEST_LIMIT_EXCEEDED`.

**Solution:** Measure current headroom, then schedule into it.

```bash
# What is left today, and what the ceiling actually is.
sf api request rest '/services/data/v67.0/limits' --target-org prod \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
    print('DailyApiRequests', d['DailyApiRequests'])"
```

```text
Worked budget — Enterprise Edition, 300 Salesforce licences
  Allocation      100,000 base + (300 x 1,000)      = 400,000 / 24h
  Existing use    middleware + mobile, observed      = 260,000 / 24h
  Headroom                                           = 140,000 / 24h

  12 workbooks x 24 hourly refreshes                 = 288 refresh cycles
  Observed calls per refresh (measure, do not guess) = ~150
  Forecast                                           = ~43,200 / 24h  -> fits

  Staggering: refresh at :05, :20, :35, :50 in four groups of three,
  so no more than three extracts are ever in the long-running pool at once.
```

**Why it works:** The `/limits` endpoint gives the real allocation and consumption
rather than a number derived from an edition table, so the headroom figure is the
org's, not a brochure's. Calls-per-refresh is measured from one workbook's first
run and multiplied out — it varies by object width and row count far too much to
assume. Staggering addresses the concurrency ceiling, which is a separate limit
from the daily one and the one that produces `REQUEST_LIMIT_EXCEEDED` first.

---

## Anti-Pattern: Promising "live Salesforce data" through the CRM connector

**What practitioners do:** Scope operational dashboards on the premise that
Tableau will query Salesforce on each view, and label the mode "live" in the
architecture document.

**What goes wrong:** The mode does not exist. Tableau documents that Tableau
Desktop, Tableau Server and Tableau Cloud are limited to extracts when using the
Salesforce CRM connector. The commitment survives design review because nobody
tests staleness until users do, and by then the dashboards are built, the
refresh cost is discovered, and the only remaining lever is refresh frequency —
which is capped by the API allocation.

**Correct approach:** State freshness as an SLA derived from the refresh schedule
("no more than 60 minutes stale") and design the dashboard around it. If a
requirement genuinely needs current-second data, that is a Salesforce report or a
Lightning component on the record page — not a Tableau extract. Where live query
across sources is the real requirement, evaluate Data Cloud as the queryable
layer rather than trying to make the CRM connector be one.
