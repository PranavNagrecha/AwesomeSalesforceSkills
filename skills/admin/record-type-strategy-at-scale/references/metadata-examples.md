# Metadata Examples — Record Type Strategy At Scale

This file treats the **record type × persona × layout × picklist matrix as a governed artefact**: you
author the matrix first, then render it into `Profile` and `PermissionSet` XML in bulk, then migrate
records and retire the rows you removed.

It deliberately does **not** re-teach the shapes it builds on:

| For | Read instead |
|---|---|
| A single `RecordType` / `BusinessProcess` / `Layout` file, and the `businessProcess` four-object rule | `admin/record-types-and-page-layouts` → `references/metadata-examples.md` |
| Resolving a record type Id in Apex, Flow, or a formula | `admin/record-type-id-management` |
| `recordTypeVisibilities` in the context of a permission set architecture | `admin/permission-set-architecture`, `admin/permission-sets-vs-profiles` |
| The FlexiPage that replaces a layout | `admin/dynamic-forms-and-actions` |
| Whether the picklist values justify a record type at all | `admin/picklist-and-value-sets` |

---

## 1. The assignment matrix

One row per **(object, record type, persona)** cell. This is the artefact you review, version, and
diff — the XML below is generated from it, not the other way round.

Worked example: Opportunity is being consolidated from four record types to three. `Enterprise_New`
and `Mid_Market_New` merge into `New_Business`; `Renewal` and `Partner_Sourced` survive unchanged.

**Target state:**

| Object | Record Type | Persona | Grant carrier | `visible` | `default` | Layout (`layoutAssignments/layout`) |
|---|---|---|---|---|---|---|
| Opportunity | `New_Business` | Sales Rep | Profile `Sales_User` | true | **true** | `Opportunity-Opportunity New Business` |
| Opportunity | `Renewal` | Sales Rep | PSet `Opportunity_Renewals` | true | n/a | `Opportunity-Opportunity Renewal` |
| Opportunity | `Partner_Sourced` | Sales Rep | — | false | false | — |
| Opportunity | `New_Business` | Sales Manager | Profile `Sales_Manager` | true | **true** | `Opportunity-Opportunity New Business` |
| Opportunity | `Renewal` | Sales Manager | PSet `Opportunity_Renewals` | true | n/a | `Opportunity-Opportunity Renewal` |
| Opportunity | `Partner_Sourced` | Sales Manager | PSet `Opportunity_Partner_Deals` | true | n/a | `Opportunity-Opportunity Partner` |
| Opportunity | *(no record type)* | every persona | Profile | — | — | `Opportunity-Opportunity New Business` *(fallback row)* |

Four properties of this table decide whether the render is correct:

- **`default` has exactly one `true` per (object, persona), and it can only live on the profile.**
  `ProfileRecordTypeVisibility` carries `default` and `personAccountDefault`;
  `PermissionSetRecordTypeVisibility` carries only `recordType` and `visible` — there is no `default`
  field on it at all (Metadata API Developer Guide, *PermissionSet* and *Profile* field tables).
  A cell whose grant carrier is a permission set therefore reads `n/a`, never `false`.
- **The layout column is profile-only too.** `layoutAssignments` is a field of `Profile`
  (`ProfileLayoutAssignments`: `layout` required, `recordType` optional). `PermissionSet` has no
  equivalent field. So a permission-set-first org still edits profiles, once per record type — see
  `gotchas.md` #6.
- **The last row is not decoration.** `ProfileLayoutAssignments.recordType` is optional: "If the
  `recordType` of the record matches a layout assignment rule, it uses the specified layout." The
  entry with no `recordType` is the one that applies when nothing matches. Consolidation must not
  delete it along with the record type rows.
- **A persona with no `true` in the `default` column does not fail loudly.** It falls back to the
  Master record type, which `Schema.RecordTypeInfo.isMaster()` documents as "the default record type
  that's used when a record has no custom record type associated with it" — and Master applies no
  picklist filtering. See `gotchas.md` #5.

---

## 2. Rendering the matrix — permission set fragment

The two rows whose grant carrier is a permission set, as one deployable file. Visibility only.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: force-app/main/default/permissionsets/Opportunity_Renewals.permissionset-meta.xml
     Only the record type blocks are shown. A real file also carries objectPermissions,
     fieldPermissions, and tabSettings. -->
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <hasActivationRequired>false</hasActivationRequired>
    <label>Opportunity - Renewals</label>
    <recordTypeVisibilities>
        <recordType>Opportunity.Renewal</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>
    <recordTypeVisibilities>
        <recordType>Opportunity.Partner_Sourced</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>
</PermissionSet>
```

## 3. Rendering the matrix — profile fragment

The same object, the rows the permission set cannot carry: the default, and every layout assignment.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: force-app/main/default/profiles/Sales_User.profile-meta.xml
     Only the record type and layout blocks are shown. A real profile file is far larger. -->
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <custom>true</custom>
    <layoutAssignments>
        <layout>Opportunity-Opportunity New Business</layout>
        <recordType>Opportunity.New_Business</recordType>
    </layoutAssignments>
    <layoutAssignments>
        <layout>Opportunity-Opportunity Renewal</layout>
        <recordType>Opportunity.Renewal</recordType>
    </layoutAssignments>
    <layoutAssignments>
        <layout>Opportunity-Opportunity New Business</layout>
    </layoutAssignments>
    <recordTypeVisibilities>
        <default>true</default>
        <personAccountDefault>false</personAccountDefault>
        <recordType>Opportunity.New_Business</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>
    <recordTypeVisibilities>
        <default>false</default>
        <recordType>Opportunity.Renewal</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>
</Profile>
```

**How to read these two files:**

- `recordType` is object-qualified in both files (`Opportunity.New_Business`), matching the guide's
  own `Account.MyRecordType` example. The layout in `layoutAssignments/layout` is *not* — it is the
  layout's file-name form: object, hyphen, layout name.
- The third `layoutAssignments` entry has no `recordType`. That is the fallback row from the matrix.
- `personAccountDefault` is shown once for shape. The guide states its value "has no impact" when
  Person Accounts is disabled — it is inert, not wrong, in a non-Person-Account org.
- `visible` and `default` are both **Required** booleans on `ProfileRecordTypeVisibility`. Omitting
  `default` on a profile entry is not "leave it alone"; write it explicitly on every row.
- Neither file will retrieve or deploy these blocks for a record type whose `active` is `false`:
  `Profile.recordTypeVisibilities` "isn't retrieved or deployed for inactive record types" in API
  29.0+, and `PermissionSet.recordTypeVisibilities` "is never retrieved or deployed for inactive
  record types". This is the single largest source of surprise diffs during a consolidation —
  `gotchas.md` #8.
- The permission set grants *visibility*, so a rep who holds `Opportunity_Renewals` can select
  `Renewal`. It does not make `Renewal` their default and it does not give `Renewal` a layout; both
  of those still come from `Sales_User.profile-meta.xml`.

---

## 4. Consolidation: merging two record types into one

Merging `Enterprise_New` and `Mid_Market_New` into `New_Business`. The order matters, and it is not
the intuitive order — the records move **before** anything is deactivated.

| # | Step | Why this position |
|---|---|---|
| 1 | Merge the two layouts into the surviving `Opportunity-Opportunity New Business` layout | The target layout must already show every field the retiring types showed, or the migration hides data the day it runs |
| 2 | Union the picklist values: every value valid on either retiring type must be valid on `New_Business` | A value absent from the target is **blanked** on reassignment, silently (`admin/record-types-and-page-layouts` gotchas #1) |
| 3 | Preflight query: count records, and find rows whose picklist values are not in the union | Gives the at-risk row count before any write |
| 4 | Bulk update `RecordTypeId` on the surviving record type | Records must not be pointing at a type you are about to deactivate |
| 5 | Deactivate the retiring record types (`active` → `false`) | Deactivation, not deletion — deletion reassigns by owner profile default, which is not the mapping you chose (`gotchas.md` #2) |
| 6 | Remove their `recordTypeVisibilities` and `layoutAssignments` rows from every profile and permission set | Do this *after* step 5 and the blocks are already gone from the retrieve; do it *before* and you are deploying visibility for a type users can still pick |
| 7 | Verify | Section 6 |

### Step 3 — preflight

```sql
SELECT RecordTypeId, RecordType.DeveloperName, COUNT(Id) RecordCount
FROM Opportunity
WHERE RecordType.DeveloperName IN ('Enterprise_New', 'Mid_Market_New')
GROUP BY RecordTypeId, RecordType.DeveloperName
```

```sql
SELECT Id, Name, StageName, RecordType.DeveloperName
FROM Opportunity
WHERE RecordType.DeveloperName IN ('Enterprise_New', 'Mid_Market_New')
AND StageName NOT IN ('Prospecting', 'Qualification', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost')
```

The second query lists the rows whose `StageName` is **not** in the value set you unioned onto
`New_Business`. Every row it returns loses that value at step 4. Repeat it per record-type-filtered
picklist on the object, not just `StageName`.

### Step 4 — the migration itself

Extract the Ids, then update with the target record type's Id in the surviving org:

```sql
SELECT Id FROM Opportunity WHERE RecordType.DeveloperName IN ('Enterprise_New', 'Mid_Market_New')
```

```text
Id,RecordTypeId
0065f00000AAAAAAAA,0125f000000BBBBAAA
0065f00000CCCCCCCC,0125f000000BBBBAAA
```

```bash
# Resolve the target record type Id in THIS org first — Ids are not portable.
sf data query --query "SELECT Id, DeveloperName FROM RecordType WHERE SobjectType='Opportunity' AND DeveloperName='New_Business'" --target-org my-sandbox

sf data query --query "SELECT Id FROM Opportunity WHERE RecordType.DeveloperName IN ('Enterprise_New','Mid_Market_New')" \
  --result-format csv --target-org my-sandbox > migrate.csv
# add the RecordTypeId column with the Id from the first query, then:

sf data update bulk --sobject Opportunity --file migrate.csv --target-org my-sandbox --wait 30
```

Driving Bulk API 2.0 directly instead of through the CLI, the ingest job is created with the same
shape as the guide's insert example, with `update` as the operation:

```json
{
  "object": "Opportunity",
  "contentType": "CSV",
  "operation": "update",
  "lineEnding": "LF"
}
```

`POST /services/data/v62.0/jobs/ingest/`, then `PUT .../jobs/ingest/<jobId>/batches/` with the CSV,
then `PATCH .../jobs/ingest/<jobId>/` with `{"state":"UploadComplete"}`. Set `lineEnding` to match
the file you actually produced — the guide's default is `LF`, and a Windows-authored CSV is `CRLF`.

**This step is not a metadata change.** Each row is a real `update`, so it runs the full save order:
before-save record-triggered flows, before triggers, **all custom validation rules**, duplicate rules
(a `block` action stops the row and no after-trigger runs), after triggers, assignment rules, and
escalation rules. See `gotchas.md` #7 before you size the run.

---

## 5. Per-persona availability audit in Apex

`SELECT ... FROM PermissionSet` cannot tell you which record types a persona can pick — the
Metadata API models that as `recordTypeVisibilities`, and there is no `ObjectPermissions`-style
standard object for it. **UNVERIFIED (2026-09-04): `RecordTypeVisibility` does not appear anywhere in
the extracted Object Reference, so do not promise a SOQL-based visibility audit; if you find it in a
Tooling API describe for the target org, verify its fields before relying on it.** What *is*
available at runtime, and is fully grounded, is the describe evaluated for the running user:

```apex
// Execute Anonymous while logged in as the persona under audit, or wrap in System.runAs in a test.
Schema.DescribeSObjectResult d = Opportunity.SObjectType.getDescribe();
List<String> rows = new List<String>{ 'developerName|active|available|isDefault|isMaster' };
Integer defaults = 0;

for (Schema.RecordTypeInfo rti : d.getRecordTypeInfos()) {
    if (rti.isDefaultRecordTypeMapping()) {
        defaults++;
    }
    rows.add(String.join(new List<String>{
        rti.getDeveloperName(),
        String.valueOf(rti.isActive()),
        String.valueOf(rti.isAvailable()),
        String.valueOf(rti.isDefaultRecordTypeMapping()),
        String.valueOf(rti.isMaster())
    }, '|'));
}

System.debug(String.join(rows, '\n'));
System.debug('default mappings for this user: ' + defaults);
```

Read the output against the matrix:

- `isAvailable() == true` should hold for exactly the record types the matrix marks `visible` for
  this persona, from **either** carrier. A `true` you did not expect is an over-grant; a `false` you
  did expect is a missing `recordTypeVisibilities` row.
- Exactly one row should have `isDefaultRecordTypeMapping() == true`. If that row also has
  `isMaster() == true`, the persona has no governed default and is creating records with the
  unfiltered picklist set — the failure `gotchas.md` #5 describes.
- `isActive() == false` on a row that still appears means the record type is deactivated but records
  and references still point at it.

`getRecordTypeInfosByDeveloperName()` returns the same objects keyed by developer name when you need
one specific type rather than the whole list.

---

## 6. `package.xml`

`RecordType` does not support the wildcard. The guide is explicit: "This metadata type doesn't
support the wildcard character `*` (asterisk) in the package.xml manifest file." Every member is
named, which is why an org-wide audit manifest has to be **generated** from a `RecordType` query
rather than hand-written — see `gotchas.md` #9.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Opportunity.New_Business</members>
        <members>Opportunity.Renewal</members>
        <members>Opportunity.Partner_Sourced</members>
        <members>Opportunity.Enterprise_New</members>
        <members>Opportunity.Mid_Market_New</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Opportunity-Opportunity New Business</members>
        <members>Opportunity-Opportunity Renewal</members>
        <members>Opportunity-Opportunity Partner</members>
        <name>Layout</name>
    </types>
    <types>
        <members>Sales_User</members>
        <members>Sales_Manager</members>
        <name>Profile</name>
    </types>
    <types>
        <members>Opportunity_Renewals</members>
        <members>Opportunity_Partner_Deals</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

The two retiring record types are listed **while they are still active**. Once step 5 has flipped
`active` to `false`, their visibility blocks stop coming back and the manifest can no longer describe
the state you are migrating away from — capture the snapshot first.

Generate the member list rather than typing it:

```bash
sf data query --target-org my-sandbox --result-format csv \
  --query "SELECT SobjectType, DeveloperName FROM RecordType WHERE IsActive = true ORDER BY SobjectType, DeveloperName" \
  | tail -n +2 | awk -F, '{print "        <members>" $1 "." $2 "</members>"}'
```

## 7. Retrieve, check, deploy

```bash
# 1. One manifest, every profile and permission set in it, or the profile diffs are meaningless.
sf project retrieve start --manifest manifest/opportunity-record-types.xml --target-org my-sandbox

# 2. Lint the matrix that came back.
python3 skills/admin/record-type-strategy-at-scale/scripts/check_record_type_strategy_at_scale.py \
  --manifest-dir force-app/main/default --profile-count 65

# 3. Validate, then deploy.
sf project deploy start --manifest manifest/opportunity-record-types.xml --target-org my-sandbox --dry-run
sf project deploy start --manifest manifest/opportunity-record-types.xml --target-org my-sandbox
```

Order across the whole consolidation:

1. Deploy the **merged layout and the unioned picklist values** (steps 1–2) on their own. Nothing is
   retired yet, so this deploy is reversible.
2. Run the **data migration** (step 4). No metadata moves.
3. Deploy the **deactivation plus the pruned profiles and permission sets** (steps 5–6) as one
   package, so no window exists where a user can pick a record type that has no layout assignment.

Retrieving a `RecordType` or a `Layout` "makes the component appear in any `Profile` and
`PermissionSet` components that are retrieved in the same package" — so a narrow retrieve produces
profiles that are missing assignments they really have, and deploying those files removes them.
`admin/record-types-and-page-layouts` gotchas #7 has the full mechanism.

## 8. Verify after deploy

```sql
SELECT SobjectType, DeveloperName, Name, IsActive, BusinessProcessId, IsPersonType
FROM RecordType
WHERE SobjectType = 'Opportunity'
ORDER BY DeveloperName
```

Expect `New_Business`, `Renewal`, `Partner_Sourced` with `IsActive = true`, and the two retired types
with `IsActive = false`. "Only active record types can be applied to records" (Object Reference,
`RecordType.IsActive`), so a `true` you meant to retire is a live gap.

```sql
SELECT RecordTypeId, RecordType.DeveloperName, COUNT(Id) RecordCount
FROM Opportunity
GROUP BY RecordTypeId, RecordType.DeveloperName
```

Expect **zero rows** for the retired developer names, and the surviving `New_Business` count to equal
its pre-migration count plus the two preflight counts from step 3. Any shortfall is rows the save
order rejected — pull the Bulk job's `failedResults` before assuming the difference is rounding.

Then re-run the Apex audit in section 5 once per persona. That is the only check that reads the
matrix the way a user experiences it.

> **UNVERIFIED (2026-09-04).** There is no standard object in the extracted Object Reference that
> exposes the profile / permission set record type visibility matrix to SOQL, so the two queries
> above verify record type state and record placement only — **not** who can see what.
> `admin/record-types-and-page-layouts` carries the same marker for the same gap. The visibility half
> of the verification is the Apex describe audit in section 5, plus the Setup path: Object Manager >
> Opportunity > Record Types, and Page Layouts > Page Layout Assignment.

## Sources for this file

- Metadata API Developer Guide, *RecordType* — `active`, `businessProcess`, `picklistValues`,
  the "appear in any Profile and PermissionSet" retrieve note, and "doesn't support the wildcard
  character `*`".
- Metadata API Developer Guide, *Profile* — `recordTypeVisibilities`
  ("isn't retrieved or deployed for inactive record types", API 29.0+), `ProfileRecordTypeVisibility`
  (`default`, `personAccountDefault`, `recordType`, `visible`), `ProfileLayoutAssignments`
  (`layout` required, `recordType` optional).
- Metadata API Developer Guide, *PermissionSet* — `PermissionSetRecordTypeVisibility`
  (`recordType`, `visible` only) and "never retrieved or deployed for inactive record types".
- Object Reference, *RecordType* — supported calls, `DeveloperName`, `IsActive`
  ("Only active record types can be applied to records"), `BusinessProcessId`, `IsPersonType`.
- Apex Reference Guide, *RecordTypeInfo Class* — `getRecordTypeInfos()`,
  `getRecordTypeInfosByDeveloperName()`, `isActive()`, `isAvailable()`,
  `isDefaultRecordTypeMapping()`, `isMaster()`.
- Bulk API 2.0 Developer Guide — ingest job JSON (`object`, `contentType`, `operation`,
  `lineEnding`), the `insert / update / delete / hard delete / upsert` operation list, and the
  `LF` / `CRLF` line-ending rule.
- Apex Developer Guide, *Triggers and Order of Execution* — what a `RecordTypeId` update actually
  runs.
