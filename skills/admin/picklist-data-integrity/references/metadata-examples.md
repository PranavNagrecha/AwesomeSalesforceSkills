# Metadata Examples — Picklist Data Integrity

This file owns the **governance artefacts**: the audit that compares *stored* values against
*defined* values, the runbook that retires a value without orphaning records, the checklist for
turning an unrestricted picklist restricted, and the written record of the change.

It deliberately does **not** re-teach the metadata shapes. `GlobalValueSet`, `StandardValueSet`,
the `valueSet` element on a `CustomField`, the `__gvs` suffix, the retrieve asymmetry, and the
deploy-omission rule all live in `admin/picklist-and-value-sets` →
`references/metadata-examples.md` §§1–2, 7–9 and `references/gotchas.md` §§9–10, 14. Read that
first if you are *building* the picklist. Read this if you are *changing one that already has
data behind it*.

| Governance question | Artefact below |
|---|---|
| What values are records actually carrying? | §1 stored-vs-defined audit (Apex) |
| Same question, no Apex allowed | §2 the SOQL-only path |
| How do I retire a value safely? | §3 deactivation sequence |
| Setup **Replace** or a Bulk update? | §4 replacement runbook |
| Can I make this picklist restricted? | §5 conversion checklist + pre-check |
| Where does the decision get written down? | §6 governance record (YAML) |
| What do I deploy, and how do I prove it landed? | §7 package.xml, §8 commands, §9 verification |

---

## The four facts this whole file rests on

| Fact | Source |
|---|---|
| "Users can select only active values from a picklist. An API retrieve operation for global picklist values returns all active and inactive values in the picklist. But retrieving the values of a non-global, unrestricted picklist returns only the active values." | api_meta.txt:47521–47526 |
| "If picklist values are missing from a component definition, they get deactivated when deployed. Deactivation occurs for picklist values of both standard and custom fields." | api_meta.txt:47482–47483 |
| `getPicklistValues()` "Returns a list of active `PicklistEntry` objects… Only active picklist values are returned." | apexrefguide.txt:190848–190849 |
| "The API doesn't enforce the list of values for advisory (unrestricted) picklist fields on `create()` or `update()`. When inserting an unrestricted picklist field that doesn't have a PicklistEntry, the system creates an 'inactive' picklist value… When creating new, inactive picklists, the API checks to see if there's a match. This check is case-insensitive." | object_reference.txt:2363–2367 |

Together they produce the central asymmetry of picklist governance: **the platform will tell you
what is active, and the records will tell you what is stored, and nothing will tell you the
difference.** You have to compute it.

---

## 1. Stored-vs-defined audit — anonymous Apex

Paste into Developer Console → Debug → Open Execute Anonymous Window. Change the three constants
at the top. It reads the field's *defined* values through describe, reads the *stored* values
through an aggregate query, and prints the set difference in both directions.

```apex
// ---- configure ----------------------------------------------------------
final String OBJECT_API  = 'Case';
final String FIELD_API   = 'Status';
final Integer SAMPLE_IDS = 5;      // record Ids to print per orphaned value
// -------------------------------------------------------------------------

Schema.SObjectType sot = Schema.getGlobalDescribe().get(OBJECT_API);
Schema.DescribeFieldResult dfr =
    sot.getDescribe().fields.getMap().get(FIELD_API).getDescribe();

System.debug('field            : ' + OBJECT_API + '.' + FIELD_API);
System.debug('restricted       : ' + dfr.isRestrictedPicklist());
System.debug('dependent        : ' + dfr.isDependentPicklist());
if (dfr.isDependentPicklist()) {
    System.debug('controller       : ' + dfr.getController());
}

// DEFINED. getPicklistValues() returns ACTIVE entries only
// (apexrefguide.txt:190848-190849) — so this set is "what a user can pick today",
// never "every value the field has ever had".
Map<String, String> definedValueToLabel = new Map<String, String>();
for (Schema.PicklistEntry pe : dfr.getPicklistValues()) {
    definedValueToLabel.put(pe.getValue(), pe.getLabel());
    if (pe.isDefaultValue()) {
        System.debug('default value    : ' + pe.getValue());
    }
    // Label drift: the stored key and the display text have diverged.
    if (pe.getValue() != pe.getLabel()) {
        System.debug(LoggingLevel.WARN,
            'LABEL DRIFT      : stored "' + pe.getValue() +
            '" displays as "' + pe.getLabel() + '"');
    }
}
System.debug('defined (active) : ' + definedValueToLabel.keySet());

// STORED. One aggregate row per distinct value actually on records.
// COUNT() + GROUP BY consumes one query row per grouping, not one per record
// (apexdev.txt:9562-9566) — so this is cheap even on a large object.
String soql =
    'SELECT ' + FIELD_API + ' v, COUNT(Id) c ' +
    'FROM '   + OBJECT_API + ' ' +
    'GROUP BY ' + FIELD_API + ' ' +
    'ORDER BY COUNT(Id) DESC';

Map<String, Integer> storedValueToCount = new Map<String, Integer>();
for (AggregateResult ar : Database.query(soql)) {
    Object raw = ar.get('v');
    if (raw == null) { continue; }          // blank is not a value; skip it
    storedValueToCount.put(String.valueOf(raw), (Integer) ar.get('c'));
}
System.debug('stored           : ' + storedValueToCount);

// A. ORPHANED — on records, not offered to users. Migration backlog.
for (String stored : storedValueToCount.keySet()) {
    if (!definedValueToLabel.containsKey(stored)) {
        Integer n = storedValueToCount.get(stored);
        System.debug(LoggingLevel.ERROR,
            'ORPHANED         : "' + stored + '" on ' + n + ' record(s)');
        List<String> ids = new List<String>();
        for (SObject s : Database.query(
                'SELECT Id FROM ' + OBJECT_API +
                ' WHERE ' + FIELD_API + ' = :stored LIMIT :SAMPLE_IDS')) {
            ids.add(String.valueOf(s.get('Id')));
        }
        System.debug(LoggingLevel.ERROR, '  sample Ids     : ' + ids);
    }
}

// B. UNUSED — offered to users, on zero records. Deactivation candidate.
for (String defined : definedValueToLabel.keySet()) {
    if (!storedValueToCount.containsKey(defined)) {
        System.debug(LoggingLevel.WARN,
            'UNUSED           : "' + defined + '" is active but on 0 records');
    }
}
```

How to read it:

- **ORPHANED is the number that matters.** Every orphaned value is a record set that no report
  picklist filter will match and no user can re-select. It is the input to §3 and §4.
- **UNUSED is not automatically a problem.** A value added last week for a process starting next
  quarter is legitimately unused. UNUSED is a prompt to ask, not an instruction to deactivate.
- **`LABEL DRIFT` is the rename fingerprint.** `PicklistEntry.getValue()` is the stored key,
  `getLabel()` is the display text (apexrefguide.txt:193677–193686). A divergence means somebody
  renamed a label; anything keyed on the label — a report filter typed by hand, an integration
  mapping — is now pointing at a string the database does not contain.
- **Do not write `if (!pe.isActive())` to find retired values.** `getPicklistValues()` already
  filtered them out (apexrefguide.txt:190848–190849), so that branch is unreachable. See
  `references/gotchas.md` § 11.
- **Multi-select picklists break this script.** Stored values are semicolon-delimited
  (`admin/picklist-and-value-sets` → `references/gotchas.md` § 7), so `GROUP BY` buckets each
  *combination*. Split on `;` before comparing, or audit multi-selects separately.

---

## 2. The same audit without Apex

For admins who cannot run anonymous Apex, three steps replace the script.

**Step 1 — what is stored.** A report is the practical tool, but the exact set is a query
(Developer Console → Query Editor, Workbench, or `sf data query`):

```sql
SELECT Status, COUNT(Id)
FROM Case
GROUP BY Status
ORDER BY COUNT(Id) DESC
```

Every row is a value that exists on at least one record, whether or not the picklist still
offers it.

**Step 2 — what is defined.** `PicklistValueInfo` "Represents the active picklist values for a
given picklist field. This object is available in API version 40.0 and later"
(object_reference.txt:219760–219761). Its fields are `DurableId`, `EntityParticleId`, `IsActive`,
`IsDefaultValue`, `Label`, `ValidFor`, and `Value` — `Value` being "The API name of the picklist
value" (object_reference.txt:219800–219836).

```sql
SELECT Value, Label, IsActive, IsDefaultValue, ValidFor
FROM PicklistValueInfo
WHERE EntityParticleId = 'Case.Status'
```

**UNVERIFIED (2026-09-04):** the Object Reference documents the object, its `query()` support and
its fields, but does not state whether `EntityParticleId` accepts the `Object.Field` string form
shown above or requires the durable Id, nor whether the `WHERE` clause is mandatory. If the query
errors, fall back to Setup → Object Manager → *Object* → Fields → *Field*, which lists the same
values, or to the Apex script in §1. Note also that the object's own description says *active*
values, so treat `IsActive` as a field you can read rather than as a way to enumerate retired
values.

**Step 3 — the difference.** Paste both result sets into a sheet and outer-join on the value
string. Rows present in Step 1 and absent in Step 2 are the orphans.

```text
value            stored_records   defined   verdict
---------------  --------------  --------  ------------------------------------
New                       1,204   active    ok
Working                     318   active    ok
Escalated                    77   active    ok
On Hold                      30   —         ORPHANED → migrate (§4)
Pending Customer              —   active    UNUSED   → ask before retiring
```

---

## 3. Deactivation sequence

The order is not stylistic. Records keep a value after it is deactivated, so the only window in
which the platform will help you move them is **before** the value stops being selectable.

| # | Step | Proof it worked |
|---|---|---|
| 1 | Run §1 in **production** (read-only). Record the count for the value being retired. | A number in the governance record (§6) |
| 2 | Decide the target value, and whether every affected record maps to it or the mapping is per-record. | `replacement_value` filled in, or a documented per-record rule |
| 3 | Move the records — §4. | Re-run §1: the retiring value's count is 0 |
| 4 | Deactivate by **setting `isActive` to `false` in the retrieved file**, never by deleting the element. | Diff shows one changed line, not one deleted block |
| 5 | Deploy the whole retrieved file. | `sf project deploy start --dry-run` clean first |
| 6 | Re-run §1. The value is now absent from `defined` (describe returns active only) and absent from `stored`. | Both sets agree |

Step 4 is where deployments destroy orgs. The guide gives two ways to deactivate a global picklist
value: "invoke an `update()` call on … `GlobalValueSet` … with the value omitted, or with the
value's `isActive` field set to false" (api_meta.txt:47478–47480). Those are not equivalent in a
source-control workflow, because omission is also what a hand-trimmed file looks like: "If picklist
values are missing from a component definition, they get deactivated when deployed"
(api_meta.txt:47482–47483). Deactivate explicitly and the intent is in the diff; deactivate by
deletion and every value you also forgot goes with it. Full treatment:
`admin/picklist-and-value-sets` → `references/gotchas.md` § 10.

The explicit form, on a local field value set:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Support_Tier__c</fullName>
    <label>Support Tier</label>
    <type>Picklist</type>
    <trackHistory>true</trackHistory>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Bronze</fullName>
                <label>Bronze</label>
                <default>true</default>
                <isActive>true</isActive>
            </value>
            <value>
                <fullName>Silver</fullName>
                <label>Silver</label>
                <default>false</default>
                <isActive>true</isActive>
            </value>
            <value>
                <fullName>Gold</fullName>
                <label>Gold</label>
                <default>false</default>
                <isActive>true</isActive>
            </value>
            <value>
                <fullName>Tier_1</fullName>
                <label>Legacy — Tier 1</label>
                <default>false</default>
                <isActive>false</isActive>
                <description>Retired 2026-09-04. Records migrated to Gold; see governance record PKL-2026-014.</description>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

How to read it:

- `Tier_1` is **still in the file**. That is the whole point. It is retired by
  `<isActive>false</isActive>`, and a reviewer reading the diff can see exactly what was turned off.
- `<description>` on a `CustomValue` is "A picklist value's description… so the reason for creating
  it can be tracked. Limit: 255 characters" (api_meta.txt:47517–47520). Retirement reasons fit, and
  they survive in the org where a Jira ticket does not.
- `<label>Legacy — Tier 1</label>` versus `<fullName>Tier_1</fullName>` is deliberate: `label`
  "defaults to the API name" when omitted (api_meta.txt:47527–47528), so writing them separately is
  what makes the drift visible to `scripts/check_picklist_data_integrity.py`.
- Exactly one `<default>` is `true`; `default` is "Required… set to `true` by default"
  (api_meta.txt:47513–47516). Deactivating the value that was the default without moving `default`
  to another value leaves the field with no selectable default.
- **This file is not a hand-authored file.** It is a retrieved file with one line changed. See §8.

---

## 4. Replacement runbook — Setup **Replace** vs a Bulk update

Both move records off a value. They differ in what else fires, which is the whole decision.

| | Setup → Object Manager → *Field* → **Replace** | Data Loader / Bulk API update |
|---|---|---|
| What you supply | Old value, new value | A CSV of `Id` + new value |
| Scope | Every record with the old value, org-wide | Exactly the Ids in your file |
| Per-record mapping | No — one target for all | Yes |
| Rollback | No undo; re-run in reverse and hope | Re-load the pre-image CSV you exported first |
| Audit trail | Thin | The success and error files |
| Automation side effects | **UNVERIFIED (2026-09-04):** whether the Replace job fires validation rules, record-triggered Flows, Apex triggers, assignment rules, or field history is not stated in any of the extracted guides (api_meta, object_reference, apexdev, apexrefguide, salesforce_data_loader, api_asynch, api_rest). Test it in a sandbox on this org's automation before trusting it in production. | Fully documented and controllable — see below |
| Best for | Small orgs, low automation, a clean 1-to-1 retirement | Anything with triggers, validation rules, or a per-record mapping |

**Choose Bulk when automation exists.** The trade is that you now own everything a data load
implies: batch size, the assignment-rule header, blanks-do-not-clear, hard-fail on oversized
values, and static state not resetting between the 200-record chunks of one Bulk request. Every one
of those is documented in `admin/data-import-and-management` → `references/gotchas.md`; do not
re-derive them here. Two matter specifically for picklists:

1. **The load can invent values.** On an unrestricted picklist the API "doesn't enforce the list of
   values… on `create()` or `update()`" and a value with no matching `PicklistEntry` creates an
   inactive picklist value, matched case-insensitively (object_reference.txt:2363–2367). A typo in
   the CSV's target column becomes a permanent entry in the field definition, not an error.
   `references/gotchas.md` § 10.
2. **Truncation changed behaviour at Data Loader 15.0.** "Allow field truncation" covers "Email,
   Multi-select Picklist, Phone, Picklist, Text, and Text (Encrypted)"; in "versions 14.0 and
   earlier, Data Loader truncates values for fields of those types if they're too large. In Data
   Loader version 15.0 and later, the load operation fails if a value is specified that is too
   large" (salesforce_data_loader.txt:437–452, 1863–1877). A multi-select migration that used to
   silently trim now fails rows. `references/gotchas.md` § 13.

The minimum-safe Bulk sequence:

```bash
# 0. Pre-image. This CSV is the rollback plan; do not skip it.
sf data query \
  --query "SELECT Id, Support_Tier__c FROM Account WHERE Support_Tier__c = 'Tier_1'" \
  --result-format csv \
  --target-org production > preimage_PKL-2026-014.csv

# 1. Build the update file from the pre-image: same Ids, new value.
#    (spreadsheet, or awk; the point is that the Id list is the queried set,
#     not a list somebody typed)

# 2. Sandbox first, on refreshed data, with the org's automation switched on.
sf data update bulk \
  --sobject Account \
  --file update_PKL-2026-014.csv \
  --target-org full-sandbox --wait 30

# 3. Re-run the §1 audit in the sandbox. Expect Tier_1 count = 0.

# 4. Production, same file shape.
sf data update bulk \
  --sobject Account \
  --file update_PKL-2026-014.csv \
  --target-org production --wait 30

# 5. Re-run the §1 audit in production BEFORE deactivating (§3 step 4).
```

**UNVERIFIED (2026-09-04):** `sf data update bulk` flag spellings were not checked against an
installed CLI in this session. Confirm with `sf data update bulk --help`; older CLI versions expose
this as `sf data upsert bulk` / `force:data:bulk:upsert`. The sequence, not the flag names, is the
guidance.

---

## 5. Making an unrestricted picklist restricted

Flipping `restricted` to `true` is a one-line metadata change with a data precondition. `restricted`
is "Whether the picklist's values are limited to only the values defined by a Salesforce admin"
(api_meta.txt:45847–45849), and the glossary states the consequence: a restricted picklist is one
"whose values are restricted to those values defined by a Salesforce admin. Users can't load
unapproved values through the API" (object_reference.txt:2463–2464).

**Pre-check — the values that would start being rejected.** Run §1. Every value in the ORPHANED
list is a value the field currently accepts and would not accept after the change. So is every
value that only *inbound integrations* write. The query that isolates them:

```sql
-- Everything stored on the field, ranked. Cross-reference against the
-- picklist definition (§2 step 2). Anything here that is not in the
-- definition is a write path that breaks the moment restricted = true.
SELECT Support_Tier__c, COUNT(Id)
FROM Account
WHERE Support_Tier__c != null
GROUP BY Support_Tier__c
ORDER BY COUNT(Id) DESC
```

Checklist:

- [ ] §1 audit run in **production**, not sandbox — sandboxes lose the integration traffic that
      created the phantom values in the first place.
- [ ] Every ORPHANED value has a disposition: *add it to the definition*, or *migrate the records*
      (§4). No third option.
- [ ] Every inbound integration that writes this field is identified, and its source value list is
      compared against the picklist definition. A source system that can emit a new value next month
      will start failing next month, not today.
- [ ] The owning team has agreed to a process for adding a new value **before** the source system
      emits it. Restricted turns a silent data-quality problem into a loud integration failure; that
      is the point, and somebody has to be on the receiving end of the noise.
- [ ] Case sensitivity checked. Unrestricted matching is case-insensitive
      (object_reference.txt:2363–2367), so `gold` and `Gold` may have collapsed into one entry that
      restricted enforcement will now compare exactly. **UNVERIFIED (2026-09-04):** whether
      restricted-picklist API validation is itself case-sensitive is not stated in the extracted
      guides; assume it is and normalise the source system's casing.
- [ ] Retrieve the field **before** editing (the retrieve of a non-global unrestricted picklist
      "returns only the active values", api_meta.txt:47521–47526 — so the file you get is already
      incomplete; reconcile it against §1's output before you deploy it back).
- [ ] Rollback decided: flipping back to `restricted=false` re-permits writes but does not undo any
      rejected inbound messages, which are gone unless the middleware retries.
- [ ] Error handling agreed with the integration owner. **UNVERIFIED (2026-09-04):** the specific
      API status code returned for a rejected restricted-picklist write —
      `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST` as named in this skill's SKILL.md — does not appear
      in api_rest.txt, apexdev.txt, api_meta.txt, object_reference.txt or api_asynch.txt. The
      *rejection* is documented (object_reference.txt:2463–2464); the exact code string is not.
      Capture the real code from a sandbox failure and put it in the runbook rather than coding
      against the string above.

The change itself, on the field's retrieved file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Support_Tier__c</fullName>
    <label>Support Tier</label>
    <type>Picklist</type>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Bronze</fullName>
                <label>Bronze</label>
                <default>true</default>
                <isActive>true</isActive>
            </value>
            <value>
                <fullName>Silver</fullName>
                <label>Silver</label>
                <default>false</default>
                <isActive>true</isActive>
            </value>
            <value>
                <fullName>Gold</fullName>
                <label>Gold</label>
                <default>false</default>
                <isActive>true</isActive>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

If the field is instead backed by a global value set, there is no `valueSetDefinition` to guard —
"A custom picklist that uses a global value set is restricted" already
(`admin/picklist-and-value-sets` → `references/metadata-examples.md` §2). The governance question
becomes who may edit the global set, not whether the field is restricted.

---

## 6. The governance record

One YAML file per value change, committed alongside the metadata diff. This is the artefact that
survives the admin who made the change. `scripts/check_picklist_data_integrity.py --governance-dir`
lints it.

```yaml
# governance/picklists/PKL-2026-014.yml
id: PKL-2026-014
object: Account
field: Support_Tier__c
value: Tier_1
action: replace              # add | deactivate | replace | rename-label
replacement_value: Gold      # required when action is "replace"
reason: >
  Tiering model collapsed from five bands to three in the FY27 support plan.
  Tier 1 has no owner and no SLA attached to it after 2026-10-01.
affected_records: 1847       # from the §1 audit, run in production
audit_run_at: "2026-09-04T09:12:00Z"
audit_environment: production
affected_reports:
  # Report + Dashboard are queryable standard objects; filter text is not.
  # Query: SELECT Id, Name, DeveloperName, FolderName FROM Report
  #        WHERE Format != 'MatrixFormat' -- then open each and read its filters
  - name: Support Tier Mix by Segment
    id: 00O5g000004ABCDEA1
    action_required: filter references Tier_1; repoint to Gold before deploy
affected_flows:
  # UNVERIFIED (2026-09-04): FlowDefinitionView / FlowVersionView are Tooling-API
  # objects and are not documented in object_reference.txt. Enumerate flows from
  # the retrieved force-app/main/default/flows/*.flow-meta.xml instead:
  #   grep -rl "Tier_1" force-app/main/default/flows/
  - name: Account_Tier_Escalation
    action_required: decision outcome tests Tier_1; add Gold branch first
affected_validation_rules:
  # Retrieved metadata is authoritative and greppable:
  #   grep -rl "Tier_1" force-app/main/default/objects/*/validationRules/
  - name: Account.Tier_Requires_CSM
    action_required: ISPICKVAL(Support_Tier__c, "Tier_1") — rewrite for Gold
affected_apex:
  #   grep -rn "Tier_1" force-app/main/default/classes/
  - name: AccountTierService
    action_required: hardcoded string constant TIER_1
affected_integrations:
  - name: NetSuite customer sync (inbound)
    action_required: source emits TIER1; mapping table updated 2026-09-02
owner: pranav.nagrecha@example.com
approved_by: revops-lead@example.com
date: 2026-09-04
deploy_ticket: REL-2231
rollback: >
  Re-deploy the retrieved field file with isActive true on Tier_1, then bulk-update
  the 1847 Ids in preimage_PKL-2026-014.csv back to Tier_1. Pre-image CSV is
  attached to REL-2231.
```

How to read it:

- **`affected_records` is a measurement, not an estimate.** It comes from §1 run against
  production, and `audit_environment` records that so a sandbox number cannot masquerade as one.
- **The dependency lists are grep targets, not guesses.** Validation rules, flows and Apex are all
  text in the retrieved source tree, so a value's real blast radius is a `grep -rl` away. Report
  filters are the exception — the filter criteria are not in a queryable field — which is why the
  `affected_reports` entry carries a manual `action_required` rather than a query.
- **`rename-label` is in the action list for a reason.** It is the one action that changes nothing
  about stored data (api_meta.txt:47527–47528 on `label`), and therefore the one most likely to be
  waved through without a record. It still breaks every report filter and integration mapping keyed
  on the label string. Record it.
- **`owner` is a person, not a team.** Value lists rot when the owner is "Ops".

---

## 7. `package.xml`

The governance change touches the field (or the global set), and usually the automation that
references the value. Retrieve them together so the diff is one reviewable unit.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Support_Tier__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Account.Tier_Requires_CSM</members>
        <name>ValidationRule</name>
    </types>
    <types>
        <members>Account_Tier_Escalation</members>
        <name>Flow</name>
    </types>
    <version>62.0</version>
</Package>
```

If the values live in a global value set instead, swap the `CustomField` block for a
`GlobalValueSet` block whose member carries the `__gvs` suffix — see
`admin/picklist-and-value-sets` → `references/metadata-examples.md` §7 for that manifest and for
why `StandardValueSet` must be named rather than wildcarded.

---

## 8. Retrieve and deploy

```bash
# 1. Retrieve. Never author the field file — the value list you do not retrieve
#    is the value list you deactivate (api_meta.txt:47482-47483).
sf project retrieve start --manifest package.xml --target-org production

# 2. Reconcile the retrieved file against the org's REAL value set. A non-global
#    unrestricted picklist retrieves ACTIVE values only
#    (api_meta.txt:47521-47526), so the file is a partial snapshot.
#    Run the §1 audit and confirm every stored value appears in the file.

# 3. Edit: isActive -> false on the retiring value (§3), or restricted -> true (§5).

# 4. Lint the edit and the governance record.
python3 scripts/check_picklist_data_integrity.py \
  --manifest-dir force-app/main/default \
  --governance-dir governance/picklists

# 5. Dry run against production. Nothing is saved.
sf project deploy start \
  --manifest package.xml \
  --dry-run \
  --target-org production

# 6. Deploy only after the record migration (§4) shows zero on the old value.
sf project deploy start --manifest package.xml --target-org production
```

**UNVERIFIED (2026-09-04):** `sf` CLI flag spellings above were not re-checked against an installed
CLI in this session. `admin/picklist-and-value-sets` → `references/metadata-examples.md` §8 records
them as verified against `@salesforce/cli` 2.149.9 on 2026-09-04; if your CLI disagrees, that file's
`--help` note is the one to follow.

---

## 9. Verification

A green deploy proves the file parsed. It proves nothing about the data. Three checks, in order.

**Check 1 — the value is gone from the definition.** Re-run §1. The retired value must be absent
from the `defined (active)` line, because `getPicklistValues()` returns active entries only
(apexrefguide.txt:190848–190849). Present-and-inactive is not a state you can observe from
describe; absent *is* the observation.

**Check 2 — the value is gone from the data.** This must return zero rows:

```sql
SELECT COUNT(Id)
FROM Account
WHERE Support_Tier__c = 'Tier_1'
```

Non-zero after a deactivation means records were created or updated with the old value between the
migration and the deploy — a live integration, a scheduled job, or a Flow. Find the write path
before re-running the migration, or you will do this again next week.

**Check 3 — Setup agrees.** Setup → Object Manager → Account → Fields & Relationships → Support
Tier. The Values list shows active values; the "Inactive Values" section below it shows `Tier_1`
with a Reactivate and a Delete action. **Delete is not a synonym for Deactivate** — deleting a
value nulls every record that still carries it, with no undo
(`admin/picklist-and-value-sets` → `references/gotchas.md` § 4). Confirm the value sits under
Inactive Values and leave it there.

If the field is per-record-type restricted, one more: a value added or retired at the field level
does not propagate to record types on its own
(`admin/record-types-and-page-layouts`, and `admin/picklist-and-value-sets` →
`references/gotchas.md` § 5). Check each record type's available-values list before declaring the
change complete.
