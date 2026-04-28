# Template — Permission Set Group Composition Plan

Use this template when composing a new PSG, refactoring an existing PSG, or planning a deletion of a PS that is referenced by one or more PSGs. The template is designed to be filled in alongside `SKILL.md`'s Decision Guidance table.

---

## 1. Persona summary

| Field | Value |
|---|---|
| Persona name | `<e.g. Sales Manager>` |
| PSG name | `PSG_<persona>_<env>` |
| Owner (team / individual) | `<RACI>` |
| User license attached | `<e.g. Salesforce, Platform, Customer Community Plus>` |
| Lifecycle stage | `Draft / Piloted / Production / Deprecated` |
| Linked admin/permission-set-architecture decision | `<reference the strategic decision that led to this PSG>` |

---

## 2. Closest existing PSG (delta analysis)

| Field | Value |
|---|---|
| Closest existing PSG | `<e.g. PSG_SalesRep_Prod>` |
| Delta type | `Subtractive (mute) / Additive (new PS) / Combination (new PSG over existing PSes) / Greenfield (no close match)` |
| Permissions to remove | `<list, with object/field/permission>` |
| Permissions to add | `<list>` |
| Decision row from SKILL.md Decision Guidance | `<copy the row that matches>` |

---

## 3. Composition

### Included Permission Sets

| Permission Set | Capability summary | License requirement | Reused in N other PSGs? |
|---|---|---|---|
| `PS_<feature>_<scope>` | `<one-line capability>` | `<e.g. Salesforce only>` | `<count>` |
| `PS_<feature>_<scope>` | `<one-line capability>` | `<license>` | `<count>` |

### Mute Permission Set (if any)

| Field | Value |
|---|---|
| Mute PS name | `MutePS_<scope>_<delta>` |
| Subtracts | `<object/field/permission to mute>` |
| Reason for mute | `<business rationale — why this delta exists>` |
| Owner | `<who approved the exclusion>` |

If no mute is needed, write `N/A` and confirm in section 6 that the delta is additive or recombination.

---

## 4. Lifecycle plan

### Recalculation impact

- PSG count that will recalculate when an included PS changes: `<n>`
- PSG count that will recalculate when this PSG is deployed for the first time: `1`
- Quiet-window recommendation: `<e.g. deploy on Saturday 02:00 UTC, expect 5–10 minute recalc>`

### Assignment plan

- Assignment mechanism: `Manual admin / Flow / Identity provisioning / SCIM`
- Time-boxed? `Yes / No`
- If yes — `ExpirationDate` policy: `<e.g. 90 days from assignment, renewable on request>`
- Pre-assignment gate: `PermissionSetGroup.Status = 'Updated'` confirmed before any user is assigned.

### Audit hooks

- Setup Audit Trail review cadence: `<e.g. monthly>`
- Quarterly access review owner: `<RACI>`
- Documented business reason for the persona (link to ticket, change request, or policy doc): `<URL>`

---

## 5. Deployment manifest

Confirm `package.xml` / source-tracked retrieval includes ALL three metadata types:

```xml
<types>
    <members>PSG_<persona>_<env></members>
    <name>PermissionSetGroup</name>
</types>
<types>
    <members>PS_<feature>_<scope></members>
    <name>PermissionSet</name>
</types>
<types>
    <members>MutePS_<scope>_<delta></members>
    <name>MutingPermissionSet</name>
</types>
```

If the PSG has no mute, omit the `MutingPermissionSet` block. If the PSG has a mute, the block is mandatory — change-set deployments often miss this.

---

## 6. Verification

Tick these before considering the composition done:

- [ ] No PSG was cloned to make this variant — mute PS used for subtractive delta or new small PS used for additive delta.
- [ ] No mute-then-re-grant pattern inside the same PSG (mute always wins).
- [ ] PSG name follows `PSG_<persona>_<env>`.
- [ ] Mute PS name (if any) follows `MutePS_<scope>_<delta>`.
- [ ] Every included PS has a license requirement noted; persona license is compatible with all included PSes.
- [ ] If retiring a PS referenced by this PSG: detach → wait for `Status = Updated` → delete sequence is documented in section 4.
- [ ] Time-boxed assignments use `ExpirationDate`; no custom Flow replicates the platform primitive.
- [ ] `python3 skills/admin/permission-set-group-composition/scripts/check_permission_set_group_composition.py --manifest-dir <path>` exits 0 (or warnings reviewed and approved).
- [ ] Setup Audit Trail entry expected for this change is documented for the post-deploy review.

---

## 7. Notes

Record any deviations from the standard pattern here, with a clear business rationale and an expiration / re-review date for the deviation.
