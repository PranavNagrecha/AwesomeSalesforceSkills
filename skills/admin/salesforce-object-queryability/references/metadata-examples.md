# Metadata Examples — Salesforce Object Queryability

The diagnostic protocol in `SKILL.md` as runnable artefacts. Six blocks: the REST
probe sequence, the Apex six-check script, the permission-set fragment that grants
what the Object Reference's *Special Access Rules* demand, the licence/edition
probe, the API-version probe, and the verdict record that
`scripts/check_salesforce_object_queryability.py` lints.

Replace `MyDomainName` with your org's My Domain subdomain and `v67.0` with the
version block 5 returns.

---

## How to read it

- **The probe order is not arbitrary.** Versions → Describe Global → sObject
  Describe → query narrows one layer per call. Running `query` first and
  reasoning backwards from `INVALID_TYPE` is what produces the wrong verdict.
- **`queryable` arrives in the Describe Global payload**, alongside `name`,
  `keyPrefix`, `custom` and `createable` — one call for the whole org, not one
  describe per object (REST API Developer Guide, *Get a List of Objects*,
  `api_rest.txt` L2402–L2447).
- **Two REST surfaces answer "no such object" with two different codes.** A
  misspelled object on the sObject Rows / Basic Information path returns HTTP 404
  `NOT_FOUND` ("The requested resource does not exist"); a misspelled object in a
  SOQL `FROM` clause returns HTTP 400. Read the status line before the body
  (`api_rest.txt` L1202–L1209, L1140–L1153).
- **Only block 3 is deployable metadata.** Blocks 1, 2, 4 and 5 are probes you
  run against a live org; block 6 is the artefact you hand back.
- **The permission set is the remediation, not the diagnosis.** Deploy it only
  after block 1 has shown the object *is* in Describe Global and the failure is
  `INSUFFICIENT_ACCESS`.

---

## 1. The REST probe sequence, with the expected error per failure mode

### 1a. Which API versions does this org serve?

Unauthenticated; establishes the version ceiling before anything else.

```bash
curl https://MyDomainName.my.salesforce.com/services/data/
```

```json
[
  { "label": "Spring '11", "url": "/services/data/v21.0", "version": "21.0" },
  { "label": "Summer '26", "url": "/services/data/v67.0", "version": "67.0" }
]
```

Source: REST API Developer Guide, *Versions* resource (`api_rest.txt` L7739–L7752)
and *Get the Salesforce Version* (`api_rest.txt` L1452–L1468).

### 1b. Is the object in this org at all, and is it queryable?

```bash
curl https://MyDomainName.my.salesforce.com/services/data/v67.0/sobjects/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

```json
{
  "encoding": "UTF-8",
  "maxBatchSize": 200,
  "sobjects": [
    {
      "name": "Account",
      "label": "Account",
      "custom": false,
      "keyPrefix": "001",
      "queryable": true,
      "retrieveable": true,
      "searchable": true,
      "createable": true,
      "deprecatedAndHidden": false,
      "urls": {
        "sobject": "/services/data/v67.0/sobjects/Account",
        "describe": "/services/data/v67.0/sobjects/Account/describe",
        "rowTemplate": "/services/data/v67.0/sobjects/Account/{ID}"
      }
    }
  ]
}
```

Three distinct outcomes, three verdicts:

| What the listing shows | Verdict |
|---|---|
| Name absent entirely | `object-does-not-exist` — or `edition-or-feature-gated` if block 4 shows the feature is off |
| Name present, `"queryable": false` | `not-queryable-on-this-surface` — the object exists but has no `query()` call |
| Name present, `"queryable": true`, query still fails | Continue to 1c — it is access or fields |

Source: REST API Developer Guide, *Describe Global* (`api_rest.txt` L8139–L8155)
and its example payload (`api_rest.txt` L2402–L2447).

Add `If-Modified-Since` to skip the payload when nothing changed — a `304 Not
Modified` with no body, and the header also fires on org-wide events such as
permission, profile and field-label changes (`api_rest.txt` L8143–L8150,
L2459–L2470):

```bash
curl https://MyDomainName.my.salesforce.com/services/data/v67.0/sobjects/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "If-Modified-Since: Tue, 23 Mar 2015 00:00:00 GMT"
```

### 1c. Full describe for the one object

```bash
curl https://MyDomainName.my.salesforce.com/services/data/v67.0/sobjects/OauthToken/describe/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Source: REST API Developer Guide, *sObject Describe*, URI
`/services/data/vXX.X/sobjects/sObject/describe/` (`api_rest.txt` L8279–L8302).

### 1d. Run the query

```bash
curl -G https://MyDomainName.my.salesforce.com/services/data/v67.0/query/ \
  --data-urlencode "q=SELECT Id, AppName FROM OauthToken LIMIT 1" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 1e. Expected error payloads, by failure mode

| Mode | Status | Payload | Grounded at |
|---|---|---|---|
| Object name misspelled on an sObject resource path | 404 | `{"message":"The requested resource does not exist","errorCode":"NOT_FOUND"}` | `api_rest.txt` L1202–L1209 |
| Running user lacks access | 403 | `{"message":"You do not have permission to view this record.","errorCode":"INSUFFICIENT_ACCESS"}` | `api_rest.txt` L4900–L4904 |
| Bad field in the projection | 400 | `[{"message":"...","errorCode":"INVALID_FIELD"}]` | `api_rest.txt` L2738–L2742 |
| Org has no API access at all | — | `API_DISABLED_FOR_ORG` | `api_rest.txt` L412 |
| API call allocation exhausted | 403 | `REQUEST_LIMIT_EXCEEDED` | `api_rest.txt` L1146 |
| Resource/version mismatch | 409 | "Check that the API version is compatible with the resource you're requesting" | `api_rest.txt` L1152–L1153 |

`API_DISABLED_FOR_ORG` is an **org** verdict, not an object verdict: API access is
on by default in Enterprise, Performance, Unlimited and Developer Edition, and
Professional Edition adds it as a paid add-on (`api_rest.txt` L409–L412). Every
per-object probe below is meaningless until that error clears.

> UNVERIFIED (2026-09-04): the exact `errorCode` string returned for an unknown
> sObject in a SOQL `FROM` clause (commonly reported as `INVALID_TYPE`) is not
> printed in `api_rest.txt`; the guide documents only the HTTP 400 class and the
> `NOT_FOUND` shape above. Treat the `INVALID_TYPE` spelling in `SKILL.md` as
> field-observed, and branch on the HTTP status plus the Describe Global result
> rather than on the code string.

---

## 2. Apex anonymous script — the six checks with a printed verdict

Run with `sf apex run --file probe_queryability.apex`. It writes one verdict line
per object; paste that line into the record in block 6.

```apex
// probe_queryability.apex — six-check queryability probe.
// Prints one PIPE-delimited verdict row per object; no DML, no callouts.
String[] targets = new String[]{ 'OauthToken', 'SetupAuditTrail', 'OpenActivity' };
String probeField = 'Id';

Map<String, Schema.SObjectType> gd = Schema.getGlobalDescribe();

for (String target : targets) {
    List<String> notes = new List<String>();
    String verdict;

    // Check 1 — is the name a key of the global describe map?
    // Keys are namespace-prefixed for Apex saved using API 28.0 and later, so a
    // bare name misses a managed-package object even when the object exists.
    Schema.SObjectType token = gd.get(target);
    if (token == null) {
        Boolean namespacedHit = false;
        for (String key : gd.keySet()) {
            if (key.endsWithIgnoreCase('__' + target) || key.equalsIgnoreCase(target)) {
                namespacedHit = true;
                notes.add('found as ' + key);
                token = gd.get(key);
                break;
            }
        }
        verdict = namespacedHit ? 'namespace-prefix-missing' : 'object-does-not-exist';
        if (!namespacedHit) {
            System.debug(target + '|' + verdict + '|not a key of getGlobalDescribe()');
            continue;
        }
    }

    Schema.DescribeSObjectResult dsr = token.getDescribe();

    // Check 2 — does the object support query() for this user?
    if (!dsr.isQueryable()) {
        System.debug(target + '|not-queryable-on-this-surface|isQueryable()=false');
        continue;
    }

    // Check 3 — can the running user see the object at all?
    if (!dsr.isAccessible()) {
        System.debug(target + '|permission-denied|isAccessible()=false on the object');
        continue;
    }

    // Check 4 — can the running user see the field we are about to project?
    Schema.SObjectField f = dsr.fields.getMap().get(probeField);
    if (f == null) {
        System.debug(target + '|field-not-visible|no field named ' + probeField);
        continue;
    }
    if (!f.getDescribe().isAccessible()) {
        System.debug(target + '|field-not-visible|' + probeField + ' isAccessible()=false');
        continue;
    }

    // Check 5 — run the real query in the running user's context.
    try {
        List<SObject> rows = Database.query(
            'SELECT ' + probeField + ' FROM ' + target + ' LIMIT 1',
            AccessLevel.USER_MODE
        );
        // Check 6 — zero rows is a SUCCESS, never a failure verdict.
        verdict = 'queryable';
        notes.add(rows.isEmpty() ? 'zero rows returned (still a success)' : 'rows returned');
    } catch (System.QueryException e) {
        // Object and field checks already passed, so the query text is what failed:
        // a bad projection entry or filter clause. Mode 4, not "object missing".
        verdict = 'field-not-visible';
        notes.add(e.getMessage());
    } catch (System.NoAccessException e) {
        verdict = 'permission-denied';
        notes.add(e.getMessage());
    }

    System.debug(target + '|' + verdict + '|' + String.join(notes, '; '));
}
```

Why each Apex call is the right one:

| Call | What it settles | Source |
|---|---|---|
| `Schema.getGlobalDescribe()` | Existence — a runtime map of every sObject available to the org, generated from the running user's permissions | Apex Reference Guide, *Schema Class* (`apexrefguide.txt` L229131–L229136); Apex Developer Guide, *Accessing All sObjects* (`apexdev.txt` L11069–L11088) |
| `DescribeSObjectResult.isQueryable()` | "Returns true if the object can be queried by the current user, false otherwise" | `apexrefguide.txt` L192792–L192797 |
| `DescribeSObjectResult.isAccessible()` | "Returns true if the current user can see this object, false otherwise" | `apexrefguide.txt` L192664–L192672 |
| `DescribeFieldResult.isAccessible()` | Field-level visibility, the layer under object access | `apexrefguide.txt` L229740 |
| `AccessLevel.USER_MODE` on `Database.query` | Makes check 5 answer the running user's question, not the system's | `apexdev.txt` L11435–L11439, L11449–L11453 |

Two behaviours this script deliberately works around:

- `getGlobalDescribe()` keys are namespace-prefixed for Apex saved using API
  version 28.0 and later, so `gd.get('MyObject__c')` returns `null` inside
  namespace `NS1` where the key is `NS1__MyObject__c` (`apexdev.txt`
  L11081–L11088). The fallback loop is why check 1 can return
  `namespace-prefix-missing` rather than `object-does-not-exist`.
- `DescribeSObjectResult.isAccessible()` changed behaviour: in API version 54.0
  and later it returns `false` for custom settings and custom metadata type
  objects when the user lacks permission; in 53.0 and earlier it returned `true`
  regardless (`apexrefguide.txt` L192676–L192679). A probe class pinned below
  54.0 reports check 3 as passing when it has not.

The whole loop is bounded by the transaction's **100 synchronous SOQL queries**
and **50,000 rows retrieved** (Salesforce Developer Limits and Allocations Quick
Reference, Apex Governor Limits, `salesforce_app_limits_cheatsheet.txt` L51–L55).
Describe calls are not SOQL, but the `LIMIT 1` probe in check 5 is — so one probe
run covers at most 100 objects synchronously.

---

## 3. Permission set — granting what *Special Access Rules* demands

Deploy this only after block 1 shows the object exists and the failure is
access. Each `userPermissions` entry below is traceable to the object's own
*Special Access Rules* paragraph in the Object Reference.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Org_Diagnostics_Read</fullName>
    <label>Org Diagnostics Read</label>
    <description>Read-only access for queryability probes. Grants only the
        permissions named by the Special Access Rules of the setup objects the
        probe reads. No object CRUD beyond read; no Modify All Data.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <license>Salesforce</license>
    <userPermissions>
        <enabled>true</enabled>
        <name>ApiEnabled</name>
    </userPermissions>
    <userPermissions>
        <enabled>true</enabled>
        <name>ViewSetup</name>
    </userPermissions>
    <userPermissions>
        <enabled>true</enabled>
        <name>ManageUsers</name>
    </userPermissions>
    <userPermissions>
        <enabled>true</enabled>
        <name>CustomizeApplication</name>
    </userPermissions>
</PermissionSet>
```

| Permission | Unlocks the query on | Documented rule |
|---|---|---|
| `ApiEnabled` | Every API call at all | "To make any API call, a user must have the API Enabled permission turned on in the user profile they're assigned" (`api_rest.txt` L418–L419) |
| `ViewSetup` | `AsyncApexJob` | "If Apex isn't running in system mode, users must have the View Setup and Configuration permission to access this object" (`object_reference.txt` L42271) |
| `ViewSetup` | `ApexTestResult`, `ApexTestQueueItem`, `ApexTestResultLimits`, `ApexTestRunResult`, `ApexTestSuite` | "In API version 49.0 and later, users must have the View Setup and Configuration permission to access this object" (`object_reference.txt` L32222, L32329, L32565, L32718, L32900) |
| `ViewSetup` | `ApexPageInfo` | "As of Summer '20 and later, this object can only be accessed by users who can view a particular Visualforce page, and users with the View Setup and Configuration permission" (`object_reference.txt` L31568) |
| `ViewSetup` | `AccountTerritoryAssignmentRule`, `AccountTerritoryAssignmentRuleItem` | "Users with the View Setup and Configuration permission can access this object" (`object_reference.txt` L18116, L18206) |
| `ManageUsers` | `AuthSession` | "To access the AuthSession object, users must have the Manage Users permission" (`object_reference.txt` L47053) |
| `CustomizeApplication` | `OauthToken` | "Users with the Customize Application permission see all tokens for all users in the org. Otherwise, you see only your own tokens" (`object_reference.txt` L189605–L189606) |
| `CustomizeApplication` | `AuthProvider` | "Only users with Customize Application and Manage AuthProviders permissions can access this object" (`object_reference.txt` L46569) |

The `userPermissions` element shape — `name` plus a required `enabled` boolean,
one element per permission — is the Metadata API's own
`PermissionSetUserPermission` definition and its `PermissionSet` sample
(`api_meta.txt` L95170–L95178 and L95195–L95249; the `ViewSetup` sample at L95366–L95385). `ViewSetup` and `ApiEnabled` appear
verbatim in those samples; `ManageUsers` at `api_meta.txt` L24495;
`CustomizeApplication` at `api_meta.txt` L10981 and L22910.

> UNVERIFIED (2026-09-04): `AuthProvider` also needs a "Manage AuthProviders"
> permission, but its API name does not appear in `api_meta.txt`, so it is
> deliberately absent from the XML above. Likewise the Content* subscription
> objects (`ContentDocumentSubscription`, `ContentNotification`,
> `ContentTagSubscription`, `ContentUserSubscription`, `ContentVersionComment`)
> are documented as "Only users with Modify All Data permission have access to
> this object" (`object_reference.txt` L77514, L78466, L78556, L79068, L79934) —
> the label is grounded, the `ModifyAllData` API spelling is not. Retrieve an
> existing permission set from the org and copy the exact `<name>` before
> deploying either.

### package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Org_Diagnostics_Read</members>
        <name>PermissionSet</name>
    </types>
    <version>67.0</version>
</Package>
```

The Metadata API guide's own note on retrieving permission sets: "When you
retrieve permission sets, also retrieve the related components with assigned
permissions. For example, to retrieve `objectPermissions` and `fieldPermissions`
for a custom object, you must also retrieve the CustomObject component"
(`api_meta.txt` L95251–L95253). This manifest grants only `userPermissions`, so it
has no companion types — the moment you add `objectPermissions`, add the object.

### Retrieve and deploy

```bash
# Retrieve the org's current spelling of the permissions before editing
sf project retrieve start --manifest manifest/package.xml --target-org diag-sandbox

# Lint before deploying
python3 skills/admin/salesforce-object-queryability/scripts/check_salesforce_object_queryability.py \
  --manifest-dir force-app/main/default

# Validate-only, then deploy
sf project deploy start --manifest manifest/package.xml --target-org diag-sandbox --dry-run
sf project deploy start --manifest manifest/package.xml --target-org diag-sandbox
```

### Verification

Re-run block 1b as the assigned user. The object must now carry
`"queryable": true` in Describe Global, and this must return rows rather than 403:

```sql
SELECT Id, AppName, AppMenuItemId FROM OauthToken LIMIT 5
```

---

## 4. Licence and edition probe

Edition-gating and licence-gating are different verdicts and read from different
objects.

```sql
-- Edition. OrganizationType is a picklist: "Edition of the organization,
-- for example Enterprise Edition or Unlimited Edition."
SELECT Id, Name, OrganizationType, InstanceName, IsSandbox, NamespacePrefix
FROM Organization
```

```sql
-- Licences actually provisioned. Do NOT filter on UsedLicenses.
SELECT Id, Name, MasterLabel, LicenseDefinitionKey, Status, TotalLicenses, UsedLicenses
FROM UserLicense
WHERE Status = 'Active'
ORDER BY Name
```

| Field | What it is | Source |
|---|---|---|
| `Organization.OrganizationType` | "Edition of the organization, for example Enterprise Edition or Unlimited Edition" | `object_reference.txt` L205561–L205567 |
| `UserLicense.LicenseDefinitionKey` | "A string that uniquely identifies a particular user license" — `SFDC`, `AUL`, `PID_Customer_Community`, … | `object_reference.txt` L299545–L299645 |
| `UserLicense.Status` | `Active` or `Disabled`; available in API version 32.0 and later | `object_reference.txt` L299662–L299668 |
| `UserLicense.TotalLicenses` / `UsedLicenses` | Provisioned vs assigned to active users; both API version 32.0 and later | `object_reference.txt` L299670–L299684 |

`Organization` supports `describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), update()` but Customer Portal users can't access it
(`object_reference.txt` L205050–L205051). `UserLicense` supports
`describeSObjects(), query(), retrieve()` (`object_reference.txt` L299539–L299540).

**The trap:** `UserLicense.UsedLicenses` "isn't filterable in API version 64.0 or
later when using it in a `WHERE` clause in a SOQL query. Instead, you have to
process the data after fetching all the records" (`object_reference.txt`
L299685–L299686). `WHERE UsedLicenses > 0` on v64.0+ is a **field-level** failure
on a perfectly queryable object — verdict `field-not-visible`/`field-rejected`,
never `object-does-not-exist`.

---

## 5. API-version probe

An object introduced after the version you pinned is invisible, not missing. The
Object Reference states each object's floor in one sentence — "This object is
available in API version N.0 and later" — the phrase appears 2,081 times across
`object_reference.txt`, once per versioned object (e.g. `OauthToken`: "This object
is available in API version 32.0 and later", `object_reference.txt` L189587).

```bash
# 1. What does the org serve?
curl https://MyDomainName.my.salesforce.com/services/data/ | \
  python3 -c 'import json,sys; print(max(d["version"] for d in json.load(sys.stdin)))'

# 2. What does this Apex class run at? (the class's own floor, not the org's)
grep -h '<apiVersion>' force-app/main/default/classes/*.cls-meta.xml | sort -u

# 3. What does the CLI default to?
sf org list metadata --metadata-type CustomObject --target-org diag-sandbox --api-version 67.0
```

Re-run block 1b at the org's newest version. If the object appears there and not
at your pinned version, the verdict is `api-version-too-old` — bump and retry.
A `409` on the same call says the same thing from the other side: "Check that the
API version is compatible with the resource you're requesting" (`api_rest.txt`
L1152–L1155).

---

## 6. The verdict record

This is what the skill produces. `scripts/check_salesforce_object_queryability.py`
lints it — required keys, the six-mode vocabulary, one `checks` entry per probe,
and the consistency rules between a verdict and the checks that justify it.

```yaml
# verdicts/oauthtoken.verdict.yaml
object: OauthToken
surface: rest-data
api_version: "67.0"
checks:
  - name: org_api_enabled
    result: pass
    evidence: "GET /services/data/ returned 67.0; no API_DISABLED_FOR_ORG on any call"
  - name: in_describe_global
    result: pass
    evidence: "present in GET /services/data/v67.0/sobjects/ with keyPrefix 0Pa"
  - name: object_queryable
    result: pass
    evidence: "Describe Global entry carries queryable: true; Object Reference Supported Calls = describeSObjects(), query()"
  - name: object_accessible
    result: fail
    evidence: "403 INSUFFICIENT_ACCESS on SELECT Id FROM OauthToken LIMIT 1 as probe.user@example.com"
  - name: field_accessible
    result: skip
    evidence: "not reached; object access failed first"
  - name: query_executed
    result: fail
    evidence: "403; zero rows was never reached, so this is not an empty result set"
verdict: permission-denied
evidence:
  - "Special Access Rules for OauthToken: users with the Customize Application permission see all tokens for all users in the org; otherwise only their own (object_reference.txt L189605-L189606)"
  - "Probe user profile has neither CustomizeApplication nor a permission set granting it"
  - "Remediation: assign the Org_Diagnostics_Read permission set from block 3, then re-run"
```

Two more verdicts in the same shape, for contrast:

```yaml
# verdicts/permissionsetgroupassignment.verdict.yaml
object: PermissionSetGroupAssignment
surface: rest-data
api_version: "67.0"
checks:
  - name: org_api_enabled
    result: pass
    evidence: "other objects queried successfully in the same session"
  - name: in_describe_global
    result: fail
    evidence: "no entry named PermissionSetGroupAssignment in GET /services/data/v67.0/sobjects/"
  - name: object_queryable
    result: skip
    evidence: "not reached; the name is not in the org's object listing"
  - name: object_accessible
    result: skip
    evidence: "not reached"
  - name: field_accessible
    result: skip
    evidence: "not reached"
  - name: query_executed
    result: fail
    evidence: "HTTP 400 on SELECT Id, AssigneeId FROM PermissionSetGroupAssignment"
verdict: object-does-not-exist
evidence:
  - "Absent from Describe Global at v67.0, the org's newest version, so not api-version-too-old"
  - "No installed-package namespace prefix produces a matching name, so not namespace-prefix-missing"
  - "Real query is SELECT PermissionSetId, PermissionSetGroupId FROM PermissionSetAssignment WHERE PermissionSetGroupId != null"
```

```yaml
# verdicts/openactivity.verdict.yaml
object: OpenActivity
surface: rest-data
api_version: "67.0"
checks:
  - name: org_api_enabled
    result: pass
    evidence: "session authenticated; other objects returned rows"
  - name: in_describe_global
    result: pass
    evidence: "present in GET /services/data/v67.0/sobjects/"
  - name: object_queryable
    result: fail
    evidence: "Object Reference Supported Calls for OpenActivity is describeSObjects() only - no query() (object_reference.txt L191459)"
  - name: object_accessible
    result: skip
    evidence: "not reached; the object has no query() call to gate"
  - name: field_accessible
    result: skip
    evidence: "not reached"
  - name: query_executed
    result: fail
    evidence: "HTTP 400 on SELECT Id FROM OpenActivity"
verdict: not-queryable-on-this-surface
evidence:
  - "Read-only related-list object; reachable as a child subquery from its parent, not as a top-level FROM"
  - "Presence in Describe Global is not a promise of query() - check Supported Calls before concluding the object is missing"
```

Lint them:

```bash
python3 skills/admin/salesforce-object-queryability/scripts/check_salesforce_object_queryability.py \
  verdicts/oauthtoken.verdict.yaml \
  verdicts/permissionsetgroupassignment.verdict.yaml \
  verdicts/openactivity.verdict.yaml
```
