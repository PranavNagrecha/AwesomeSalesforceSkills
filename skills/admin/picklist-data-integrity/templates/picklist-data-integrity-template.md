# Picklist Value Change — Work Template

One copy per value change. Fill it as you go; §6 is the artefact that gets committed.

**Skill:** `picklist-data-integrity`
**Change id:** `PKL-____-___`
**Request summary:**

---

## 1. Target

| | |
|---|---|
| Object | |
| Field API name | |
| Field is | local value set / global value set (`__gvs`) / standard value set |
| Restricted today? | true / false / inherited (GVS-backed) |
| Dependent picklist? | no / controlling field is `____` / this field controls `____` |
| Multi-select? | no / yes — the audit needs the semicolon split |
| Change type | add / deactivate / replace / rename-label / make restricted |

If the field is GVS-backed, list every other field that consumes the same set. A change here is a
change on all of them (`admin/picklist-and-value-sets` → `references/gotchas.md` § 1).

---

## 2. Audit — run BEFORE deciding anything

Run `references/metadata-examples.md` §1 (Apex) or §2 (SOQL-only) against **production**.

```text
defined (active) :
stored           :
ORPHANED         :
UNUSED           :
LABEL DRIFT      :
```

| | |
|---|---|
| Audit run at (UTC) | |
| Environment | production / sandbox — **must be production for the record** |
| Records on the value being changed | |

A sandbox count is not the count. Say so here rather than discovering it at deploy time.

---

## 3. Blast radius

Grep the retrieved source tree; the value's API name is a plain string in all of these.

```bash
grep -rln "<VALUE_API_NAME>" \
  force-app/main/default/objects/*/validationRules/ \
  force-app/main/default/flows/ \
  force-app/main/default/classes/ \
  force-app/main/default/triggers/ \
  force-app/main/default/lwc/ \
  force-app/main/default/aura/
```

| Consumer | Found? | Action required |
|---|---|---|
| Validation rules | | |
| Flows | | |
| Apex / triggers | | |
| Formula fields / roll-ups | | |
| Reports and dashboards (**not greppable — check by hand**) | | |
| List views (**not greppable**) | | |
| Inbound integrations writing this field | | |
| Outbound consumers reading this field | | |
| Record types whose available-value list includes it | | |

Reports, dashboards and list views are the ones that break on a *label* rename while everything
else survives — `references/gotchas.md` § 14.

---

## 4. Approach

| | |
|---|---|
| Pattern from SKILL.md | A / B / C / D — and why |
| Migration mechanism | Setup **Replace** / Data Loader / Bulk API / Flow / Apex |
| Why that mechanism | (Setup Replace fires unknown automation — `references/metadata-examples.md` §4) |
| Target value for existing records | |
| Per-record mapping needed? | no (single target) / yes (attach the mapping) |
| Pre-image CSV exported? | path: |
| Sandbox rehearsal done? | org: date: result: |

If this is a **make restricted** change, work the checklist in
`references/metadata-examples.md` §5 instead and record each box here.

---

## 5. Execution order

Tick in order. Do not reorder — records can only be moved while the value is still selectable.

- [ ] Audit run in production; count recorded in §2
- [ ] Target value agreed and recorded
- [ ] Blast-radius consumers updated to handle the new value **first** (they must accept both during the window)
- [ ] Pre-image CSV exported
- [ ] Migration rehearsed in sandbox on refreshed data with automation on
- [ ] Migration run in production
- [ ] Audit re-run: old value count is **zero**
- [ ] Field/value-set file **retrieved** (never hand-authored) and reconciled against the audit
- [ ] `isActive` set to `false` on the retiring value — value left in the file, not deleted
- [ ] `python3 scripts/check_picklist_data_integrity.py --manifest-dir <dir> --governance-dir <dir>` clean
- [ ] `sf project deploy start --dry-run` clean
- [ ] Deployed
- [ ] Verification §9 checks 1–3 pass
- [ ] Record types checked (a field-level change does not propagate to them)
- [ ] Governance record committed alongside the metadata diff

---

## 6. Governance record

Copy the YAML shape from `references/metadata-examples.md` §6 into
`governance/picklists/PKL-____-___.yml` and fill it. Required keys the checker enforces:
`id`, `object`, `field`, `value`, `action`, `reason`, `affected_records`, `owner`, `date` — plus
`replacement_value` when `action` is `replace`.

---

## 7. Notes and deviations

Record anything done differently from the pattern, and why. In particular: any step skipped
because the record count was zero, any automation temporarily disabled for the migration and when
it was re-enabled, and any value that was **deleted** rather than deactivated (deletion nulls every
record that still carries it, with no undo — `admin/picklist-and-value-sets` →
`references/gotchas.md` § 4).
