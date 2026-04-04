# Record Merge Implications — Pre-Merge Planning Template

Use this template before merging duplicate Account, Contact, or Lead records.

---

## Merge Scope

| Field | Value |
|---|---|
| Object being merged | Account / Contact / Lead |
| Number of merge sets | ___ |
| Merge method | UI / Apex Database.merge() / Duplicate Management |
| Executed by | ___ |
| Target sandbox / production | ___ |

---

## Master Record Selection

For each merge set, identify the master record:

| Merge Set | Master Record ID | Master Record Name | Reason for Selection |
|---|---|---|---|
| 1 | ___ | ___ | Most Opportunities / Oldest / Most complete data |
| 2 | ___ | ___ | ___ |

---

## Field Conflict Resolution

For each merge set, review fields with conflicting values:

| Field API Name | Master Record Value | Losing Record Value(s) | Decision (Keep Master / Use Losing / Merge) |
|---|---|---|---|
| OwnerId | ___ | ___ | Must update master before merge if losing owner is correct |
| ___ | ___ | ___ | ___ |

**Action required for fields to preserve from losing records:**
- [ ] Fields copied to master record before Apex merge: ___

---

## Child Record Audit (Before Merge)

| Related Object | Master Record Count | Losing Record Count | Expected Post-Merge Count |
|---|---|---|---|
| Opportunities | ___ | ___ | ___ |
| Cases | ___ | ___ | ___ |
| Activities (Tasks + Events) | ___ | ___ | ___ |
| Campaign Members | ___ | ___ | ___ (deduplicated per Campaign) |
| Custom related object: ___ | ___ | ___ | ___ |

---

## Automation Exposure

- [ ] Record-Triggered Flows on this object: ___ (name them)
- [ ] Apex triggers on this object: ___
- [ ] Workflows on this object: ___
- [ ] Delete triggers on this object (fires on losing records): ___
- [ ] Automation impact assessed: No unintended side effects expected / Action taken: ___

---

## Pre-Merge Data Export

- [ ] Losing record IDs exported to CSV for external system mapping
- [ ] Key field values from losing records documented
- [ ] Campaign Member response data reviewed for deduplication risk

---

## Post-Merge Verification

- [ ] Master record related lists checked for re-parented Opportunities, Cases, Activities
- [ ] Campaign Members verified — count matches expectation after deduplication
- [ ] OwnerId confirmed on master record
- [ ] Automation did not fire unexpectedly
- [ ] Losing record IDs confirmed as inactive (query returns master record data)

---

## External System Updates

| System | Field Storing Old Record ID | Update Method | Status |
|---|---|---|---|
| ___ | ___ | ___ | Pending / Done |
