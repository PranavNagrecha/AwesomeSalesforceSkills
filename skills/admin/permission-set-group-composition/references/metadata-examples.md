# Metadata Examples — Permission Set Group Composition

Deploy-ready XML for one persona end to end: a **field service dispatcher** who
needs work-order dispatch rights but must not delete work orders. Every fence
here is a real file body — copy it, rename the file, change the API names.

The persona is deliberately different from the ones in `examples.md` (sales rep /
manager, refund approver, knowledge publisher) so the two files can be read side
by side without re-reading the same bundle twice.

Corpus citations are to the Metadata API Developer Guide text in `api_meta.txt`
(`api_meta L<n>`).

---

## 1. Directory layout

```text
force-app/main/default/
├── permissionsets/
│   ├── PS_WorkOrderDispatch.permissionset-meta.xml
│   └── PS_ServiceResourceRead.permissionset-meta.xml
├── mutingpermissionsets/
│   └── MutePS_NoWorkOrderDelete.mutingpermissionset-meta.xml
└── permissionsetgroups/
    └── PSG_FieldDispatcher_Prod.permissionsetgroup-meta.xml
manifest/
└── package.xml
```

The three directory names are fixed by the platform, not by house style:
permission sets live in `permissionsets` (`api_meta L94727`), muting permission
sets in `mutingpermissionsets` (`api_meta L89682`), groups in
`permissionsetgroups` (`api_meta L95301`). In each case the guide states that
the file name matches the API name — which is why none of the fences below
carry a `<fullName>` element: the API name is already in the file name, and
`PermissionSetGroup` inherits `fullName` from `Metadata` (`api_meta L95297`).

---

## 2. The two composable permission sets

`force-app/main/default/permissionsets/PS_WorkOrderDispatch.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Work order and service appointment access for dispatch. Composed into dispatcher and field-service-admin groups.</description>
    <label>Work Order Dispatch</label>
    <hasActivationRequired>false</hasActivationRequired>
    <license>Salesforce</license>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>WorkOrder</object>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>ServiceAppointment</object>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>
</PermissionSet>
```

`force-app/main/default/permissionsets/PS_ServiceResourceRead.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Read-only service resource access for dispatch-board lookups.</description>
    <label>Service Resource Read</label>
    <hasActivationRequired>false</hasActivationRequired>
    <license>Salesforce</license>
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>false</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>ServiceResource</object>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>
</PermissionSet>
```

Field notes, all from the `PermissionSet` field table:

| Element | Constraint | Citation |
|---|---|---|
| `description` | `Limit: 255 characters` — both fences above stay under 200 to keep headroom | `api_meta L94788` |
| `label` | Required, `Limit: 80 characters` | `api_meta L94824` |
| `license` | The permission set license or user license tied to the set | `api_meta L94826` |
| `hasActivationRequired` | Whether the set needs an active session; API 37.0+ | `api_meta L94820` |
| `objectPermissions` children | `allowCreate`, `allowDelete`, `allowEdit`, `allowRead`, `modifyAllRecords`, `object`, `viewAllRecords` are each **Required**, so a partial block is an invalid block | `api_meta L95069`–`L95110` |

Element order follows the guide's own `PermissionSet` sample, which puts
`description` before `label` (`api_meta L95369`–`L95370`).

---

## 3. The muting permission set — enable what you want muted

`force-app/main/default/mutingpermissionsets/MutePS_NoWorkOrderDelete.mutingpermissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MutingPermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>No Work Order Delete</label>
    <description>Mutes delete on WorkOrder inside any permission set group that includes this muting set.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <license>Salesforce</license>
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>false</allowEdit>
        <allowRead>false</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>WorkOrder</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</MutingPermissionSet>
```

**The polarity is inverted, and it is the single easiest thing to get wrong
here.** `allowDelete` is `true` because the guide says so: "Unlike
PermissionSet, settings **enabled** by MutingPermissionSet are turned off for
the permission set group that it's a component of" (`api_meta L89719`), and the
guide's own sample is described as having "administrative permissions **enabled**
to ensure that they're muted in the Permission Set Group" (`api_meta L89728`).
Writing `<allowDelete>false</allowDelete>` here mutes nothing — it is a no-op
file that deploys cleanly and leaves the permission granted.

Everything else on this type comes from `PermissionSet`: "MutingPermissionSet
has the same fields as PermissionSet, plus a single field, `label`"
(`api_meta L89718`), `label` being required (`api_meta L89722`). That shared
field table is why the 255-character `description` ceiling applies here too, and
why the checker treats muting files the same as permission sets for
`PSGC-DESC-01`.

The type is its own metadata type — it extends `PermissionSet` (`api_meta
L89678`) but is retrieved and deployed separately — and it is available in API
version 46.0 and later (`api_meta L89689`).

---

## 4. The permission set group

`force-app/main/default/permissionsetgroups/PSG_FieldDispatcher_Prod.permissionsetgroup-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSetGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Field service dispatcher, production. Work order dispatch plus service resource read, with delete on WorkOrder muted.</description>
    <label>Field Dispatcher Prod</label>
    <hasActivationRequired>false</hasActivationRequired>
    <mutingPermissionSets>MutePS_NoWorkOrderDelete</mutingPermissionSets>
    <permissionSets>PS_WorkOrderDispatch</permissionSets>
    <permissionSets>PS_ServiceResourceRead</permissionSets>
</PermissionSetGroup>
```

| Element | What the guide says | Citation |
|---|---|---|
| `description` | "The permission set group description provided by the permission set group creator" — **no `Limit:` clause, unlike `PermissionSet.description`** | `api_meta L95328` |
| `hasActivationRequired` | Whether the group requires an associated active session; default `false`; API 53.0+ | `api_meta L95331` |
| `label` | Required | `api_meta L95336` |
| `mutingPermissionSets` | "A permission set containing permissions to disable in the permission set group"; API 46.0+ | `api_meta L95338` |
| `permissionSets` | The permission set or sets included in the group | `api_meta L95341` |
| `status` | `Updated` / `Outdated` / `Updating` / `Failed` | `api_meta L95345`–`L95350` |

`status` is absent from the fence above on purpose. A **retrieved** group carries
it, and it looks like this:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSetGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Field service dispatcher, production. Work order dispatch plus service resource read, with delete on WorkOrder muted.</description>
    <label>Field Dispatcher Prod</label>
    <hasActivationRequired>false</hasActivationRequired>
    <mutingPermissionSets>MutePS_NoWorkOrderDelete</mutingPermissionSets>
    <permissionSets>PS_WorkOrderDispatch</permissionSets>
    <permissionSets>PS_ServiceResourceRead</permissionSets>
    <status>Updated</status>
</PermissionSetGroup>
```

The four values are documented as a closed enum, and the checker ERRORs on a
fifth. **UNVERIFIED (2026-09-12):** the guide never says whether `status` is
writable on deploy — it only describes the field as indicating recalculation
status — so treat a retrieved value as a reading of the platform's state at
retrieve time, not as something a deployment sets. Do not diff on it in a
source-tracked repo; it changes without anyone editing the file.

Also note `PermissionSetGroup.description` carries no documented ceiling
(`api_meta L95328`), which is why the 255-character rule the checker applies to
it is marked UNVERIFIED in `examples.md` rather than presented as documented
platform behaviour.

---

## 5. `package.xml` — all three types, one manifest

`manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>PS_WorkOrderDispatch</members>
        <members>PS_ServiceResourceRead</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>MutePS_NoWorkOrderDelete</members>
        <name>MutingPermissionSet</name>
    </types>
    <types>
        <members>PSG_FieldDispatcher_Prod</members>
        <name>PermissionSetGroup</name>
    </types>
    <version>62.0</version>
</Package>
```

All three types must be named. The guide is explicit on the pairing: "When you
retrieve permission set groups, also retrieve the related components. For
example, to retrieve `PermissionSetGroup`, you must also retrieve
`PermissionSet`" (`api_meta L95396`–`L95397`). `MutingPermissionSet` is listed
next to `PermissionSetGroup` in the guide's own manifest sample for the muting
type (`api_meta L89792`–`L89797`). A manifest that names only
`PermissionSetGroup` produces the mute-never-travelled failure in Gotcha 4.

---

## 6. Deploy order

Three deployments, in this order, when any of the members is new or changed:

| # | What deploys | Why it cannot move later |
|---|---|---|
| 1 | `PS_WorkOrderDispatch`, `PS_ServiceResourceRead` | The group names them as members; a member that does not exist yet cannot be resolved |
| 2 | `MutePS_NoWorkOrderDelete` | Same reason, via `mutingPermissionSets`; it is a separate metadata type, so it does not ride along inside the group's file |
| 3 | `PSG_FieldDispatcher_Prod` | Composition only, no permissions of its own |

A group references its members **by developer name**, not by id — the fences in
§4 carry bare strings, not 18-character keys. That is what makes the ordering
matter: name resolution happens at validation time. When a referenced permission
set is missing from the target org, or was itself rejected earlier in the same
deployment, the group fails with `permission set names are invalid`.

The cascade half of that was observed live: `sf project deploy start --dry-run`
against a Summer '26 developer org on 2026-09-11 rejected four `PermissionSet`
files for an over-length `description`, and every group that referenced one of
them failed with exactly that message. The error string is not in the Metadata
API guide (searching `api_meta.txt` for it returns nothing), so it is an
empirical observation, not a documented contract. **UNVERIFIED (2026-09-12):**
the *missing member* case — a group naming a permission set that was never
deployed at all, as opposed to one rejected in the same run — has not been
reproduced against an org; it is inferred from the same name-resolution
mechanism.

Practical consequence for the single-deployment habit: bundling all three types
into one `sf project deploy start` usually works, because the platform resolves
members within a deployment. It is the *failure* mode that is order-sensitive —
one bad member takes the group down with it, and a three-step deploy tells you
which layer broke instead of handing you a composition-layer error for a
field-length problem. Retirement runs the same ladder backwards, with the
recalculation wait from Gotcha 5 between the rungs.

---

## 7. Verify before deploying

Run the package checker against the tree:

```bash
python3 skills/admin/permission-set-group-composition/scripts/check_permission_set_group_composition.py \
    --manifest-dir force-app/main/default
```

On the four files above it reports:

```text
GOOD: mute: PSG 'PSG_FieldDispatcher_Prod' uses muting permission set 'MutePS_NoWorkOrderDelete' — explicit subtractive delta, preferred over cloning.

Summary: 1 good, 0 error, 0 warn, 0 info, scanned 1 PSG file(s).
```

What each finding would mean if it were not clean:

| Finding | Cause in this example set |
|---|---|
| `PSGC-DESC-01` ERROR | A `description` past 255 characters on any of the three types |
| `PSGC-DESC-02` WARN | A `description` past 200 — the headroom rung, which is why every fence here stays short |
| no `<label>` ERROR | Dropping `label` from the group or the muting file; both are documented as required |
| unknown `<status>` ERROR | A fifth value pasted into the retrieved-group fence |
| unresolved reference WARN | Deploying step 3 without steps 1 and 2 — the checker's static preview of `permission set names are invalid` |
| naming WARN | Renaming the group to something outside `PSG_<persona>_<env>`; add `--strict` to make it fail the run |

Point `--manifest-dir` at whatever directory contains the three metadata folders
— project root, `force-app/main/default`, or a scratch extraction of this file —
the checker walks recursively. A directory with no group files exits 0 with an
INFO, which is the signal that the retrieve scope, not the composition, is
wrong.
