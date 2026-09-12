# Metadata Examples — List Views, Compact Layouts, Search Layouts

Deployable shapes for the three browse-and-scan metadata types, taken from the Metadata API Developer Guide (v62 PDF: `ListView`, `ListViewFilter`, `FilterScope`, `SharedTo`, `CompactLayout`, `SearchLayouts`, `ProfileSearchLayouts`) and extended to a Case triage example. All three live inside the object, not beside it — none of them is a standalone top-level folder in Metadata API terms.

## Where the files live

| Type | package.xml `<name>` | `<members>` syntax | Wildcard `*` | DX source file | API |
|---|---|---|---|---|---|
| `ListView` | `ListView` | `Object.ViewUniqueName` (e.g. `Account.AccountTeam`, `api_meta L2305`, `L2318`) | **Not supported** | `objects/<Object>/listViews/<Name>.listView-meta.xml` (e.g. `objects/Case/listViews/Escalations.listView-meta.xml`) | 14.0+ custom objects, 17.0+ standard objects |
| `CompactLayout` | `CompactLayout` | `Object.CompactLayoutName` (e.g. `Case.Case_Triage`) — see [Manifest member form](#manifest-member-form) | **Supported** | `objects/<Object>/compactLayouts/<Name>.compactLayout-meta.xml` (e.g. `objects/Case/compactLayouts/Case_Triage.compactLayout-meta.xml`) | 29.0+; external objects 42.0+ |
| `SearchLayouts` | reached through `CustomObject` | the object name | **Not supported** | inside `objects/Case/Case.object-meta.xml` | 14.0+ custom objects, 27.0+ standard objects except Event and Task |
| `ProfileSearchLayouts` | reached through `CustomObject` | the object name | — | inside `objects/<Object>/<Object>.object-meta.xml` | 48.0+ for custom objects |

The guide states the retrieval rule plainly: "You can access SearchLayouts only by accessing its encompassing CustomObject", and for a standard object's list views, "The easiest way to retrieve list views for a standard object is to retrieve the object."

> UNVERIFIED (2026-09-04): the decomposed DX paths in the table above (`objects/<Object>/listViews/*.listView-meta.xml`, `objects/<Object>/compactLayouts/*.compactLayout-meta.xml`) are the sfdx **source format** shape. The Metadata API Developer Guide documents only the MDAPI shape, where every one of these is nested inside a single `<CustomObject>` file. Both forms are shown below; the DX form is what `sf project retrieve start` writes into a source-tracked project.

## 1. Queue-scoped Case list view (DX source format)

`force-app/main/default/objects/Case/listViews/Escalations_Queue.listView-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ListView xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Escalations_Queue</fullName>
    <columns>CASES.CASE_NUMBER</columns>
    <columns>CASES.PRIORITY</columns>
    <columns>CASES.SUBJECT</columns>
    <columns>ACCOUNT.NAME</columns>
    <columns>CASES.STATUS</columns>
    <columns>LAST_UPDATE</columns>
    <filterScope>Queue</filterScope>
    <label>Escalations Queue</label>
    <queue>Tier_2_Escalations</queue>
</ListView>
```

> UNVERIFIED (2026-09-04): the standard-field column tokens above (`CASES.*`, `ACCOUNT.NAME`, `LAST_UPDATE`) follow the token style the guide uses in its own samples (`NAME`, `CREATED_DATE`, `CREATEDBY_USER`, `ACCOUNT.SITE`, `CORE.USERS.ALIAS`), but the guide publishes no per-object token list. Retrieve one existing list view on the target object and copy its tokens rather than guessing them.

## 2. "My open cases" with an advanced filter and shared to a public group

`force-app/main/default/objects/Case/listViews/My_Open_Cases.listView-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ListView xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>My_Open_Cases</fullName>
    <booleanFilter>1 AND (2 OR 3)</booleanFilter>
    <columns>CASES.CASE_NUMBER</columns>
    <columns>CASES.SUBJECT</columns>
    <columns>CASES.PRIORITY</columns>
    <columns>CASES.STATUS</columns>
    <filterScope>Mine</filterScope>
    <filters>
        <field>CASES.STATUS</field>
        <operation>notEqual</operation>
        <value>Closed</value>
    </filters>
    <filters>
        <field>CASES.PRIORITY</field>
        <operation>equals</operation>
        <value>High</value>
    </filters>
    <filters>
        <field>SLA_Breach_Risk__c</field>
        <operation>equals</operation>
        <value>true</value>
    </filters>
    <label>My Open Cases</label>
    <sharedTo>
        <group>Support_Agents_EMEA</group>
    </sharedTo>
</ListView>
```

### How to read both list views

- **`filterScope` is required.** The enumeration is `Everything`, `Mine`, `MineAndMyGroups`, `AssignedToMe` (ServiceAppointment only), `Queue`, `Delegated`, `MyTerritory`, `MyTeamTerritory`, `Team`, `SalesTeam` (49.0+), and `ScopingRule`. The guide's own sample definition writes them lowercase (`<filterScope>everything</filterScope>`); the enumeration table capitalises them. Use the capitalised form the table defines and let a retrieve confirm what the org emits.
- **`queue` is only meaningful with `filterScope` = `Queue`.** It holds the queue's developer name, so the `Queue` metadata must exist in the target org first (`admin/queues-and-public-groups`).
- **`filters` are ordered, and `booleanFilter` indexes them by position.** `1 AND (2 OR 3)` refers to the first, second, and third `<filters>` block in document order. Reorder the blocks and the logic changes silently — nothing in the file names the clauses.
- **`operation` is a closed enumeration**: `equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`, `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`, `within` (DISTANCE criteria only). There is no `isNull` — use `equals` with an empty `<value/>`.
- **The filter's field element is `<field>`, not `<filter>`.** UNVERIFIED (2026-09-04): the guide's `ListViewFilter` field table names the element `filter`, while the guide's own sample definition for `ListView` uses `<field>`. Only the sample could be checked here; retrieve an existing filtered view before hand-writing one.
- **`sharedTo` appears only on shared and private views.** The guide is explicit: `SharedTo` "is included in the metadata for shared and private list views. `SharedTo` isn't in the metadata for public list views." A file with **no** `sharedTo` element is a public view — absence is the loud case, not the quiet one.
- **`sharedTo` accepts `group`, `role`, `roleAndSubordinates`, `roleAndSubordinatesInternal`, `territory`, `territoryAndSubordinates`, `queue`, `allInternalUsers`, `allPartnerUsers`, `allCustomerPortalUsers`, `managers`, `managerSubordinates`, `portalRole`, `portalRoleandSubordinates`.** Use `group`/`role`/`territory` (22.0+), not the deprecated plural `groups`/`roles`/`territories`.
- **`language` matters only with `startsWith` or `contains`** in a Translation Workbench org, and the search terms must be in that language.
- **`division` applies only when the org uses divisions and the view is scoped to all records.**

## 3. Compact layout

The file lives at `objects/<Object>/compactLayouts/<Name>.compactLayout-meta.xml` — inside the object directory, never beside it. The guide states the containment rule but not the path: "Compact layouts are defined as part of the custom object, standard object, or external object definition" (`api_meta L43086-43088`), and its only sample nests `<compactLayouts><fullName>testCompactLayout</fullName>` inside a `<CustomObject>` (`api_meta L43147-43151`). That containment is why the package.xml member is **object-qualified** and not the bare `fullName` — see [Manifest member form](#manifest-member-form) before writing a manifest.

`force-app/main/default/objects/Case/compactLayouts/Case_Triage.compactLayout-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CompactLayout xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Case_Triage</fullName>
    <fields>CaseNumber</fields>
    <fields>Status</fields>
    <fields>Priority</fields>
    <fields>SLA_Target__c</fields>
    <label>Case Triage</label>
</CompactLayout>
```

How to read it:

- **Order is the design.** The guide: the fields' "order represents the prioritization given to them when defining the compact layout." The mobile card and the highlights panel truncate from the end, so field 1 must be the identifier and field 2 the state.
- **Four unsupported field types.** Compact layouts support all field types **except** text area, long text area, rich text area, and multi-select picklist. `Case.Description` (long text area) cannot go in one; a deploy that includes it fails rather than silently dropping it.
- **`label` is required in practice** even though the field table marks neither field required — the guide's sample carries both `fields` and `label`.

> UNVERIFIED (2026-09-04): `<fields>` entries above use standard-object **API names** (`CaseNumber`, `Status`). The guide's only `CompactLayout` sample uses a custom field (`textfield__c`), so it does not demonstrate the standard-field form. This is the opposite convention from `ListView` `columns` and `SearchLayouts`, which use legacy tokens — confirm with a retrieve before hand-writing standard fields.

## 4. Assignment and search layouts, inside the object file

A compact layout that is never assigned is inert. Assignment happens in two places, both inside the object's own metadata: `compactLayoutAssignment` on the `CustomObject` (the object default) and `compactLayoutAssignment` on each `RecordType`.

`force-app/main/default/objects/Case/Case.object-meta.xml` (fragment)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <compactLayoutAssignment>Case_Triage</compactLayoutAssignment>
    <recordTypes>
        <fullName>Escalated_Support</fullName>
        <active>true</active>
        <compactLayoutAssignment>Case_Triage</compactLayoutAssignment>
        <label>Escalated Support</label>
    </recordTypes>
    <recordTypes>
        <fullName>Billing_Enquiry</fullName>
        <active>true</active>
        <label>Billing Enquiry</label>
    </recordTypes>
    <searchLayouts>
        <listViewButtons>New</listViewButtons>
        <listViewButtons>Accept</listViewButtons>
        <listViewButtons>ChangeOwner</listViewButtons>
        <lookupDialogsAdditionalFields>Priority</lookupDialogsAdditionalFields>
        <massQuickActions>Create_MQA_Contact</massQuickActions>
        <searchResultsAdditionalFields>CREATEDBY_USER</searchResultsAdditionalFields>
    </searchLayouts>
</CustomObject>
```

How to read it:

- **`<compactLayoutAssignment>SYSTEM</compactLayoutAssignment>`** is the value the guide's sample uses for the platform default compact layout. Name your own layout there to override it.
- **`Billing_Enquiry` above carries no `compactLayoutAssignment`**, exactly like `RT2` in the guide's sample. UNVERIFIED (2026-09-04): the guide documents the field as "the compact layout that is assigned to the record type" but does not state the fallback when it is absent; confirm in the org which layout an unassigned record type renders.
- **`searchLayouts` has no `fullName` and no wildcard.** It is a singleton block per object, so a deploy replaces the whole block — you cannot add one button without shipping the rest.
- **The Name field is force-added back.** Per the guide, a text-type Name field "is always displayed as the first column in the search results page… it's not returned" by a field query, and an autonumber Name you delete from the list is re-added by Metadata API on import. That is the source of the endless one-line diff on `searchResultsAdditionalFields`.
- **`listViewButtons` is the "Buttons Displayed" value in the object's List View search layout** — this is the one search-layout field that governs the list-view surface rather than search results.
- **`excludedStandardButtons`** removes standard buttons from the search layout; `searchResultsCustomButtons` adds custom ones whose actions apply to any returned record.
- **Per-profile search results** use a sibling `<profileSearchLayouts>` block with `profileName` plus `fields`. The guide warns that the profile must already exist in the destination org, and for a custom object, search must be enabled and the object's tab must exist or ship in the same deployment.

## 5. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Case.Escalations_Queue</members>
        <members>Case.My_Open_Cases</members>
        <name>ListView</name>
    </types>
    <types>
        <members>Case.Case_Triage</members>
        <name>CompactLayout</name>
    </types>
    <version>62.0</version>
</Package>
```

`ListView` members use `objectName.listViewUniqueName` — the **View Unique Name**, not the label — and the type rejects `*`. `CompactLayout` is the only one of the three that accepts the wildcard (`api_meta L43199-43201`), so `<members>*</members>` is also valid for it; an *enumerated* compact-layout member, however, must be object-qualified. `SearchLayouts` has no members of its own; it rides along with `<name>CustomObject</name>`.

### Manifest member form

**Rule: every enumerated member of a type that lives inside an object is `<Object>.<Name>`.** That is documented for `ListView` — "Note the `objectName.listViewUniqueName` syntax in the `<members>` field" (`api_meta L2318`), with the sample `<members>Account.AccountTeam</members>` (`api_meta L2305`) — and for `CustomField`, "Note the `objectName.field` syntax" (`api_meta L2287`). `CompactLayout` behaves the same way, but the guide never says so.

> UNVERIFIED (2026-09-11): the Metadata API Developer Guide publishes **no** package.xml member-form statement and **no** manifest sample for `CompactLayout`. Its `CompactLayout` topic gives only the containment rule (`api_meta L43086-43088`) and wildcard support (`api_meta L43199-43201`). The object-qualified form below is grounded in a deploy, not in the guide.

The object-qualified form is verified by `sf project deploy start --manifest … --dry-run` against a Summer '26 developer org on 2026-09-09 (`examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md` § Mock deploy #3). A manifest carrying the bare `fullName`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_Intake</members>
        <name>CompactLayout</name>
    </types>
    <version>62.0</version>
</Package>
```

failed validation on a source tree that *did* contain `objects/Case/compactLayouts/Case_Intake.compactLayout-meta.xml`, with this error:

```text
An object 'Case_Intake' of type CompactLayout was named in package.xml, but was not found in zipped directory
```

The same tree, deployed with `--source-dir` instead, validated 12/12 — and the CLI's own component list named the compact layout **`CompactLayout Case.Case_Intake`**. Correcting the member to `Case.Case_Intake` is the fix.

**Why `--source-dir` hides the defect.** `--source-dir` derives the manifest from the files on disk, so it always produces the object-qualified member and can never disagree with the tree. `--manifest` takes the member list as written and matches it against the zip. A build that only ever validates with `--source-dir` will pass every time and still ship a manifest that fails the first time someone runs `--manifest` — the form a metadata-API deploy, a packaging build, or a CI validate step typically uses. Validate both ways before handing the manifest over.

**Does the same trap apply to `ListView`?** The documented member form is identical (`Object.ViewUniqueName`, `api_meta L2318`), so a bare `<members>Escalations_Queue</members>` under `<name>ListView</name>` contradicts the guide for the same reason. UNVERIFIED (2026-09-11): the bare-member `ListView` case was **not** exercised against an org, so the exact CLI error text for it is not claimed here — only the compact-layout error above was observed. The checker treats both types the same on the documented grounds.

## 6. Retrieve, check, deploy

```bash
# Pull the whole object so list views, compact layouts and search layouts arrive together
sf project retrieve start --metadata CustomObject:Case --target-org my-sandbox

# Or just the browse-and-scan pieces
sf project retrieve start --metadata "ListView:Case.My_Open_Cases" --metadata CompactLayout --target-org my-sandbox

# Static review before deploying. Point it at the PROJECT ROOT, not at force-app/,
# so manifest/package.xml is in scope for the member-form rules CL-MEM-01 / CL-MEM-02.
python3 skills/admin/list-views-and-compact-layouts/scripts/check_list_views_and_compact_layouts.py \
    --manifest-dir .

# Validate-only, then deploy
sf project deploy start --source-dir force-app/main/default/objects/Case --target-org my-sandbox --dry-run

# Validate the MANIFEST too: --source-dir derives members from the files and can never
# disagree with them, so it cannot catch a wrong <members> value. Only --manifest can.
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox --dry-run

sf project deploy start --source-dir force-app/main/default/objects/Case --target-org my-sandbox
```

## 7. Verify after deploy

The `ListView` object (API 32.0+, supports `describeSObjects()`, `query()`, `retrieve()`, `search()`) is the only one of the three with a queryable record, so it is the deploy check:

```sql
SELECT Id, SobjectType, DeveloperName, Name, IsSoqlCompatible
FROM ListView
WHERE SobjectType = 'Case'
ORDER BY DeveloperName
```

- `DeveloperName` must match the `fullName` you deployed; `Name` is the label.
- `IsSoqlCompatible = false` means the view's filters cannot be expressed in SOQL, so nothing that reads the view programmatically will reproduce it.
- Views whose `DeveloperName` you did not author and cannot find in source are usually the auto-created queue views (the guide: "When you create a queue, a corresponding list view is automatically created") or personal views, which never appear in source because Metadata API cannot see **Visible only to me** views at all.

Compact layouts and search layouts have no equivalent queryable object. Verify them in Setup → Object Manager → Case → Compact Layouts / Search Layouts, and confirm the assignment by opening one record of each record type on a phone-width viewport.
