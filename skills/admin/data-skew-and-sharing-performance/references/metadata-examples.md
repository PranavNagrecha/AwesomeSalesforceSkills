# Metadata Examples — Data Skew and Sharing Performance

Deployable metadata for a skew remediation. Skew itself is *data*, not metadata — you cannot deploy your
way out of 400,000 records under one owner. What you deploy is the machinery that makes the remediation
survivable: the deferral switch, the bucket groups and owner rules that replace the single catch-all owner,
the OWD change that removes the implicit-sharing scan, and the indexed fields that keep the diagnostic
queries selective.

Worked scenario used throughout:

| Symptom | Object | Measurement | Skew type |
|---|---|---|---|
| Role change on the integration user runs for hours | `Loan__c` (Private OWD) | `Loan_Integration_User` owns 412,000 of 1,050,000 loans | Ownership |
| Single-record Contact owner change takes 30 s | `Contact` | Account `Unassigned Contacts` has 398,000 Contacts | Account / parent-child |
| Nightly load fails with `UNABLE_TO_LOCK_ROW` | `Loan__c` | 903,000 loans point at one `Servicer__c` record | Lookup |

---

## 1. `Sharing.settings` — suspend recalculation for the remediation window

`SharingSettings` values are stored in the `Sharing.settings` file in the `settings` directory
(Metadata API Developer Guide, `api_meta.txt` L126981). Two fields matter here, both API 49.0+
(`api_meta.txt` L126995 and L127025):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SharingSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <deferGroupMembership>true</deferGroupMembership>
    <deferSharingRules>true</deferSharingRules>
    <enableExternalSharingModel>true</enableExternalSharingModel>
    <enableManualUserRecordSharing>true</enableManualUserRecordSharing>
    <enableRestrictAccessLookupRecords>true</enableRestrictAccessLookupRecords>
    <enableSecureGuestAccess>true</enableSecureGuestAccess>
</SharingSettings>
```

**How to read it**

- `deferGroupMembership` — "Indicates whether group membership calculations are suspended (`true`) or not
  (`false`). This field has a default value of `false`." (`api_meta.txt` L126995)
- `deferSharingRules` — same shape for sharing rule calculation (`api_meta.txt` L127025).
- **The feature is off until Support turns it on.** "The defer sharing calculation feature isn't enabled by
  default. To enable it for your Salesforce org, contact Salesforce Customer Support."
  (`api_meta.txt` L127000). Deploying `true` into an org that never filed that case does nothing
  useful — check first, not on the night of the load.
- **Flipping `deferGroupMembership` back to `false` recalculates both.** "When you change the value of this
  field from `true` to `false`, group membership is automatically recalculated. Sharing rules are also
  automatically recalculated, unless the `deferSharingRules` field is set to `true` prior to modifying
  `deferGroupMembership`." (`api_meta.txt` L127004). Resume order is therefore: set
  `deferSharingRules` `true` first if you want the two recalculations separated in time.
- **You cannot change `deferSharingRules` while `deferGroupMembership` is `true`** — "Sharing rule
  calculations are suspended regardless of the value of `deferSharingRules`."
  (`api_meta.txt` L127021).
- Setting file names appear in `package.xml` as `<members>Sharing</members>` under `<name>Settings</name>`
  (`api_meta.txt` L127154–L127160).
- `SharingSettings` requires the Manage Sharing permission (`api_meta.txt` L126990).

The re-enable file is the same document with both flags set to `false`. Keep it in source control beside
the suspend file so the resume step is a deploy, not a click someone forgets.

---

## 2. `Group` — the ownership buckets that replace one catch-all owner

The mitigation for ownership skew is more owners. The Large Data Volumes guide states the goal plainly:
"Avoid having any user own more than 10,000 records." (`ldv.txt` L1033). Bucket queues or groups are how
you get there without inventing 40 licensed users.

`groups/Loan_Ops_Bucket_01.group`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Group xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Loan_Ops_Bucket_01</fullName>
    <name>Loan Ops Bucket 01</name>
    <description>Ownership bucket 1 of 4 for Loan__c. Target ceiling 10,000 loans per bucket.</description>
    <doesIncludeBosses>false</doesIncludeBosses>
</Group>
```

**How to read it**

- File suffix `.group`, stored in the `groups` directory (`api_meta.txt` L79617).
- `name` is Required and "Corresponds to Label in the user interface"; `fullName` "must be unique, begin
  with a letter, not include spaces, not end with an underscore, and not contain two consecutive
  underscores" (`api_meta.txt` L79643 and L79649).
- `description` is available in API version 62.0 and later (`api_meta.txt` L79635).
- `doesIncludeBosses` — "Indicates whether records shared with users in this group are also shared with
  users higher in the role hierarchy (`true`) or not (`false`). This field corresponds to the **Grant Access
  Using Hierarchies** checkbox" (`api_meta.txt` L79637). Set it `false` on bucket groups on purpose:
  every `true` adds hierarchy fan-out to a structure whose entire point is to *reduce* fan-out.
- **Deploying the group does not deploy who is in it.** "Members of the public group aren't migrated when
  you deploy the group type." (`api_meta.txt` L79630). Membership is `GroupMember` data — `GroupId` +
  `UserOrGroupId`, created through the API (Object Reference, `object_reference.txt` L154390).
  A bucket group with a sharing rule pointed at it and no members grants nothing at all.
- Group `Type` for a group you create must be `Regular`, `Personal`, or `Queue` — "Only `Personal`,
  `Regular`, and `Queue` can be used when creating a group. The other values are reserved."
  (`object_reference.txt` L154362). `Type` is not a `Group` *metadata* field; the metadata type has
  only `description`, `doesIncludeBosses`, `fullName`, `name` (`api_meta.txt` L79635–L79649).

`Group` supports the wildcard `*` in `package.xml` (`api_meta.txt` L79675), so `<members>*</members>`
retrieves every public group in the org for the audit.

---

## 3. `SharingRules` — owner rules per bucket, criteria rule on an indexed field

All rule kinds for one object live in a single `<object>.sharingRules` file in the `sharingRules` folder
(`api_meta.txt` L129254). `sharingRules/Loan__c.sharingRules`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SharingRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <sharingOwnerRules>
        <fullName>Loan_Bucket_01_To_Loan_Ops</fullName>
        <accessLevel>Edit</accessLevel>
        <description>Bucket 1 loans visible to the Loan Ops group. One rule per bucket keeps each
            recalculation scoped to under 10,000 records.</description>
        <label>Loan Bucket 01 To Loan Ops</label>
        <sharedFrom>
            <group>Loan_Ops_Bucket_01</group>
        </sharedFrom>
        <sharedTo>
            <group>Loan_Ops_Readers</group>
        </sharedTo>
    </sharingOwnerRules>
    <sharingCriteriaRules>
        <fullName>Loan_Servicer_Region_West</fullName>
        <accessLevel>Read</accessLevel>
        <criteriaItems>
            <field>Servicer_Region__c</field>
            <operation>equals</operation>
            <value>West</value>
        </criteriaItems>
        <description>Criteria rule filtered on an External Id field so the rule's own evaluation query
            stays selective.</description>
        <includeRecordsOwnedByAll>false</includeRecordsOwnedByAll>
        <label>Loan Servicer Region West</label>
        <sharedTo>
            <group>Loan_Ops_West</group>
        </sharedTo>
    </sharingCriteriaRules>
</SharingRules>
```

**How to read it**

- Element shape follows the guide's own sample definitions for criteria-based and ownership-based rules
  (`api_meta.txt` L129499–L129534).
- `accessLevel`, `label`, and `sharedTo` are Required on every rule; `description` has a maximum of 1000
  characters (`api_meta.txt` L129186–L129197).
- `sharedFrom` is Required on `SharingOwnerRule` and "Specifies the record owners"
  (`api_meta.txt` L129358).
- `<group>` inside `sharedTo` / `sharedFrom` is "A list of groups with sharing access. Use this field
  instead of the `groups` field." (`api_meta.txt` L129056). `<role>`, `<roleAndSubordinates>`,
  `<queue>`, `<territory>` are the other targets — `queue` "Applies only to lead, case, and CustomObject
  sharing rules" (`object_reference.txt` — see `api_meta.txt` L129158).
- `includeRecordsOwnedByAll` is Required on a criteria rule and **immutable**: "You can't edit this field
  after the sharing rule is created." (`api_meta.txt` L129312). It controls whether records owned
  by users who can't have an assigned role (high-volume users, system users) are swept in — which is
  precisely the population a parking-lot owner lives in. Get it right at creation.
- Sharing rules can be retrieved and deployed wholesale in API 33.0+, but "You can't retrieve, delete, or
  deploy manual sharing rules or sharing rules by their type" (`api_meta.txt` L129249). A skew
  remediation that depends on removing manual shares is a data task, not a deploy.
- One rule per bucket rather than one rule over all buckets is the point: each rule's recalculation is
  bounded by its bucket.

---

## 4. `CustomObject` / `CustomField` — OWD and the fields the diagnostics query

`objects/Loan_Payment__c/Loan_Payment__c.object-meta.xml` — the child whose sharing can follow its parent:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Loan Payment</label>
    <pluralLabel>Loan Payments</pluralLabel>
    <nameField>
        <label>Payment Number</label>
        <type>AutoNumber</type>
        <displayFormat>PAY-{00000000}</displayFormat>
    </nameField>
    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>ControlledByParent</sharingModel>
    <externalSharingModel>ControlledByParent</externalSharingModel>
</CustomObject>
```

`objects/Loan__c/fields/Legacy_Loan_Id__c.field-meta.xml` — the load key, indexed by virtue of being an
External Id:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Legacy_Loan_Id__c</fullName>
    <label>Legacy Loan Id</label>
    <type>Text</type>
    <length>40</length>
    <externalId>true</externalId>
    <unique>true</unique>
    <caseSensitive>false</caseSensitive>
    <required>false</required>
</CustomField>
```

`objects/Loan__c/fields/Servicer__c.field-meta.xml` — the skewed lookup itself:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Servicer__c</fullName>
    <label>Servicer</label>
    <type>Lookup</type>
    <referenceTo>Servicer__c</referenceTo>
    <relationshipName>Loans</relationshipName>
    <relationshipLabel>Loans</relationshipLabel>
    <required>false</required>
    <deleteConstraint>SetNull</deleteConstraint>
</CustomField>
```

**How to read it**

- `sharingModel` "Indicates the org-wide defaults for the object." Using API version 30.0 and later you can
  set it through the Metadata API; in API 29.0 and earlier it was read-only and UI-only
  (`api_meta.txt` L42250–L42256). `externalSharingModel` is the external counterpart
  (`api_meta.txt` L42132–L42135).
- Valid `SharingModel` values are `Private`, `Read`, `ReadWrite`, `ReadWriteTransfer`, `FullAccess`,
  `ControlledByParent`, `ControlledByCampaign`, `ControlledByLeadOrContact`; "Accounts, opportunities, and
  custom objects support `Private`, `Read` and `ReadWrite` values"
  (`api_meta.txt` L45801–L45816). `ControlledByParent` is available where the relationship supports it.
- `externalId` "Indicates whether the field is an external ID field (`true`) or not (`false`). This property
  is returned only if the custom field data type is AutoNumber, Email, Number, or Text."
  (`api_meta.txt` L43402–L43405) — you cannot make a Date, Picklist, or Formula field an External Id.
- Either flag creates the index: "If this field is `unique` or the `externalId` is set `true`, the
  `isIndexed` value is set to `true`." (`api_meta.txt` L43451–L43453), and the Large Data Volumes guide
  confirms "External IDs cause an index to be created on that field. The query optimizer then considers
  those fields." (`ldv.txt` L418).
- **Every lookup is already indexed.** The platform maintains indexes on `RecordTypeId`, `Division`,
  `CreatedDate`, `Systemmodstamp` (`LastModifiedDate`), `Name`, `Email` (contacts and leads), "Foreign key
  relationships (lookups and master-detail)", and the record Id (`ldv.txt` L400–L409). So the *lookup* in a
  skew diagnosis is indexed; what makes the diagnostic query slow is that the index is not **selective**
  when 903,000 of 1,050,000 rows share one value — see §6.
- Leaving the lookup blank beats pointing rows at a placeholder: "By default, the index tables don't include
  records that are null (records with empty values)." (`ldv.txt` L436) — blank rows are absent from
  the index table rather than piled onto one indexed value.

Optional, and only after a Support case: a `CustomIndex` component, suffix `.indx-meta`, stored in
`customindex` (`api_meta.txt` L41111; available API 50.0+, L41115). "To use this metadata and create
a custom index, review Indexes in Best Practices for Deployments with Large Data Volumes, and then contact
Salesforce Customer Support." (`api_meta.txt` L41119).

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CustomIndex xmlns="http://soap.sforce.com/2006/04/metadata">
    <allowNullValues>false</allowNullValues>
    <booleanIndexedValue>true</booleanIndexedValue>
</CustomIndex>
```

`allowNullValues` defaults to `false`; `booleanIndexedValue` is API 61.0 and later
(`api_meta.txt` L41125 and L41128).

---

## 5. `package.xml` and the deploy commands

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Sharing</members>
        <name>Settings</name>
    </types>
    <types>
        <members>*</members>
        <name>Group</name>
    </types>
    <types>
        <members>Loan__c</members>
        <name>SharingRules</name>
    </types>
    <types>
        <members>Loan__c</members>
        <members>Loan_Payment__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Loan__c.Legacy_Loan_Id__c</members>
        <members>Loan__c.Servicer__c</members>
        <name>CustomField</name>
    </types>
    <version>62.0</version>
</Package>
```

`Group` supports `*` (`api_meta.txt` L79675). `SharingRules` supports wildcards in API 33.0 and
later (`api_meta.txt` L129248), but `SharedTo` and `SharingBaseRule` themselves do **not**
(`api_meta.txt` L129239) — you never name those in a manifest, only the containing `SharingRules`.
Settings types do not take `*` for an individual setting (`api_meta.txt` L127165).

Retrieve the current state before changing anything:

```bash
sf project retrieve start --manifest manifest/package.xml --target-org prod
```

Deploy the suspend switch, verify it, then the structural change, then the resume switch — three deploys,
not one:

```bash
# 1. Validate the whole change set without committing it
sf project deploy validate --manifest manifest/package.xml --target-org prod --wait 60

# 2. Suspend recalculation (deferGroupMembership/deferSharingRules = true)
sf project deploy start --source-dir force-app/main/default/settings --target-org prod --wait 60

# 3. Buckets, rules, OWD, fields
sf project deploy start --manifest manifest/package.xml --target-org prod --wait 120

# 4. Resume — deploy the same Sharing.settings with both flags false
sf project deploy start --source-dir force-app/main/default/settings --target-org prod --wait 60
```

Metadata API file suffixes above are the ones the Metadata API Developer Guide documents (`.group`,
`.sharingRules`, `.settings`, `.indx-meta`).
UNVERIFIED (2026-09-05): the Salesforce DX source-format convention of appending `-meta.xml`
(`Loan__c.object-meta.xml`, `Loan__c.sharingRules-meta.xml`) is not stated in any of the offline guides used
here; it is taken from the repo's own retrieved-metadata layout, which the checker script globs.

---

## 6. Verification and diagnosis queries

Run these before the remediation to size it, and after to prove it landed. `GROUP BY ROLLUP` is the
guide's own method for getting distribution statistics (`ldv.txt` L248).

```sql
-- Ownership skew. LDV: "Avoid having any user own more than 10,000 records." (ldv.txt L1033)
SELECT OwnerId, COUNT(Id) cnt
FROM Loan__c
GROUP BY OwnerId
HAVING COUNT(Id) > 10000
ORDER BY COUNT(Id) DESC

-- Account (parent-child) skew. LDV: "Distribute child records so that no parent has more than
-- 10,000 child records." (ldv.txt L1052-L1055)
SELECT AccountId, COUNT(Id) cnt
FROM Contact
GROUP BY AccountId
HAVING COUNT(Id) > 10000
ORDER BY COUNT(Id) DESC

-- Lookup skew. Repeat per custom lookup on the object; the skew is in the TARGET, not the owner.
SELECT Servicer__c, COUNT(Id) cnt
FROM Loan__c
GROUP BY Servicer__c
HAVING COUNT(Id) > 10000
ORDER BY COUNT(Id) DESC

-- Full distribution, including the total, so you can compute selectivity rather than eyeball it.
SELECT Servicer__c, COUNT(Id)
FROM Loan__c
GROUP BY ROLLUP (Servicer__c)
```

Turn the counts into a selectivity verdict with the guide's published thresholds
(`ldv.txt` L463–L471):

| Index kind | Used when the filter matches | Worked example from the guide |
|---|---|---|
| Standard indexed field | < 30% of the first million records **and** < 15% of additional records | 2 M records → 450,000 or fewer; 5 M records → 900,000 or fewer (`ldv.txt` L463–L465) |
| Custom indexed field | < 10% of the first million records **and** < 5% of additional records | 500 K records → 50,000 or fewer; 5 M records → 300,000 or fewer (`ldv.txt` L468–L471) |

With `AND`, "the query optimizer uses the indexes unless one of them returns more than 20% of the object's
records"; with `OR`, "unless they all return more than 10%", and "All fields in the OR clause must be
indexed for any index to be used." (`ldv.txt` L476–L479). For `LIKE`, the optimizer "samples up to 100,000
records of actual data" instead of consulting its statistics table (`ldv.txt` L481).

Read that table against the scenario: 903,000 of 1,050,000 loans on one `Servicer__c` value is ~86% — far
past every threshold. The lookup is indexed and the index is useless for that value. That is what skew
means for the read path; the lock contention is the separate, worse half.

Post-deploy Setup and API checks:

```sql
-- Did the OWD change land?
SELECT QualifiedApiName, InternalSharingModel, ExternalSharingModel
FROM EntityDefinition
WHERE QualifiedApiName IN ('Loan__c', 'Loan_Payment__c')

-- Are the bucket groups actually populated? Group metadata does not carry members
-- (api_meta.txt L79630), so this is the check that catches an empty bucket.
SELECT GroupId, Group.DeveloperName, COUNT(Id) members
FROM GroupMember
WHERE Group.DeveloperName LIKE 'Loan_Ops_Bucket%'
GROUP BY GroupId, Group.DeveloperName

-- Did implicit parent sharing actually go away on the reparented children?
-- RowCause 'ImplicitParent' means access flows from a related record (object_reference.txt L17743).
SELECT RowCause, COUNT(Id)
FROM AccountShare
WHERE AccountId = '001xx000003DGXXAA4'
GROUP BY RowCause
```

Setup checks that have no query equivalent: **Setup → Sharing Settings** shows whether deferral is
available and currently suspended, and **Setup → Sharing Settings → Sharing Rules** shows each rule's
source, which is where you confirm no rule still sources from the old catch-all group.

---

## 7. The load-ordering plan the remediation runs inside

The Large Data Volumes guide gives an explicit order for a load into an org with a sharing model. Deviating
from it is the single most common way a "careful" remediation still takes the org down.

| Step | Instruction | Source |
|---|---|---|
| 0 | Use Public Read/Write security during initial load to avoid sharing calculation overhead — **initial loads only**, not a live-org remediation | `ldv.txt` L852–L853 |
| 1 | Load users into roles | `ldv.txt` L857 |
| 2 | Load record data with owners, triggering calculations in the role hierarchy | `ldv.txt` L858–L859 |
| 3 | Configure public groups and queues, and let those computations propagate | `ldv.txt` L860–L861 |
| 4 | Add sharing rules one at a time, letting computations for each rule finish before adding the next one | `ldv.txt` L862–L864 |
| — | Disable Apex triggers, workflow rules, and validations during loads; use batch Apex afterwards | `ldv.txt` L872–L874 |
| — | Group child records by parent: "group records by the field `ParentId` in the same batch to minimize locking conflicts" | `ldv.txt` L894–L896 |
| — | Defer sharing calculations until after all data has been loaded | `ldv.txt` L898–L900 |

Concurrency mode is where the two Bulk APIs differ, and the difference decides which one you use:

- **Bulk API (v1)** exposes `concurrencyMode` on `JobInfo` with `Parallel` (default) and `Serial`. "In
  serial mode, batches are processed serially with other batches from the same job and batches from other
  serial mode jobs, and each batch must complete before the next batch starts processing. Because batches
  are processed one at a time, the possibility of lock contention conditions are minimized. The cost of
  using serial mode is an increase in processing time." (`api_asynch.txt` L4986–L4989)
- **Bulk API 2.0** does not: `concurrencyMode` is "Reserved for future use. How the request is processed.
  Currently only parallel mode is supported. (When other modes are added, the API chooses the mode
  automatically. The mode isn't user configurable.)" (`api_asynch.txt` L3050–L3054, L3214–L3219)

So a job that must run serially because of skew has to be a Bulk API v1 job. A Bulk API v1 job plan:

```json
{
  "plan": "loan-reparent-2026-09",
  "jobs": [
    {
      "name": "reparent-contacts-batch-01",
      "object": "Contact",
      "operation": "update",
      "api": "Bulk API v1",
      "concurrencyMode": "Serial",
      "sortKey": "AccountId",
      "batchSize": 5000,
      "reason": "Updating ownership for records with private sharing is a documented lock-contention operation (api_asynch.txt L5011-L5015)."
    },
    {
      "name": "load-groupmember-buckets",
      "object": "GroupMember",
      "operation": "insert",
      "api": "Bulk API v1",
      "concurrencyMode": "Serial",
      "batchSize": 2000,
      "reason": "Creating users / updating user roles / updating territory hierarchies are the four operations the guide names as likely to cause lock contention (api_asynch.txt L2695-L2699)."
    }
  ]
}
```

**How to read the plan**

- `sortKey` implements the guide's instruction directly: "For large data loads, sort main records based on
  their parent record to avoid having different child records (with the same parent) in different jobs."
  (`api_asynch.txt` L2701–L2702). The AccountTeamMember worked example — "organize your CSV data files by
  `AccountId`" (`api_asynch.txt` L2703–L2707) — is the same shape as a skewed-parent reparent.
- The four operations flagged as lock-prone are **creating users, updating ownership for records with
  private sharing, updating user roles, updating territory hierarchies**
  (`api_asynch.txt` L2695–L2699, L5010–L5015). A skew remediation is made almost entirely of items 2 and 3.
- Parallel is the default and the guide's preference — "Avoid processing data in serial mode unless you know
  that parallel mode would otherwise result in lock timeouts and you can't reorganize your batches to avoid
  locks." (`api_asynch.txt` L4993–L4995). Reorganizing by parent is the first move; serial is the fallback.
- Bulk API v1 retries a locked batch, but not forever: "If there are problems acquiring locks for more than
  100 records in a batch, the Bulk API places the remainder of the batch back in the queue for later
  processing… records marked as failed aren't retried." and "it's placed back in the queue and reprocessed
  up to 10 times before the batch is permanently marked as failed."
  (`api_asynch.txt` L5002–L5008). Partial success inside a "failed" batch is normal — reconcile, do not
  blind-resubmit.
- Bulk API 2.0 surfaces `TooManyLockFailure`: "Too many lock failures while processing the current batch."
  (`api_asynch.txt` L2790–L2792).
- Any operation over 2,000 records is a Bulk candidate; under 2,000, use bulkified synchronous REST or SOAP
  (`ldv.txt` L826–L831). Batch allocation is 15,000 batches per rolling 24-hour period, shared between Bulk
  API and Bulk API 2.0 (`salesforce_app_limits_cheatsheet.txt` L737).
- For the extract half of a remediation, PK chunking is the guide's answer above 10 million rows: "Salesforce
  recommends that you enable PK chunking when querying tables with more than 10 million records or when a
  bulk query consistently times out." Default chunk size 100,000, maximum 250,000
  (`api_asynch.txt` L7180–L7181, L7172–L7176). It works on Sharing and History tables too, by naming the
  parent object in the `Sforce-Enable-PKChunking` header (`api_asynch.txt` L7312–L7314) — which is how you
  extract `AccountShare` for a before/after comparison.

Feed this plan and the query results from §6 to the checker:

```bash
python3 scripts/check_data_skew_and_sharing_performance.py \
    --manifest-dir force-app/main/default \
    --skew-plan skew-plan.json \
    --job-plan bulk-job-plan.json
```

---

## Official Sources Used

- Metadata API Developer Guide — `SharingSettings` (`api_meta.txt` L126974–L127167), `Group`
  (L79612–L79676), `SharingRules` / `SharingBaseRule` / `SharingCriteriaRule` / `SharingOwnerRule`
  (L129165–L129535), `SharedTo` (L129018–L129163), `CustomField` `externalId` / `unique` / `indexed`
  (L43402, L43451, L43702), `CustomObject.sharingModel` (L42250), `SharingModel` enumeration (L45801),
  `CustomIndex` (L41099–L41147).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Best Practices for Deployments with Large Data Volumes (Summer '26) — ownership and parent ceilings
  (L1033, L1052), load ordering (L852–L900), indexed standard fields and selectivity thresholds
  (L403–L481), null exclusion from index tables (L436), Defer Sharing Calculation (L595–L604).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/ldv.pdf
- Bulk API and Bulk API 2.0 Developer Guide — concurrency modes (L4983–L4995, L3050–L3054), lock-prone
  operations and batch organisation (L2684–L2709, L5009–L5019), retry behaviour (L5002–L5008), PK chunking
  (L7143–L7185, L7312–L7314).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf
- Object Reference for the Salesforce Platform — `AccountShare.RowCause` values including
  `ImplicitParent` (L17717–L17743), share-record compression (L17816), `Group.Type` values
  (L154307–L154362), `GroupMember` (L154390).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Salesforce App Limits Cheat Sheet — Bulk batch allocation, 15,000 per rolling 24 hours (L736–L739).
