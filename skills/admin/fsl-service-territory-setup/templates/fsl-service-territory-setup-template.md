# FSL Service Territory Setup — Configuration Checklist

Use this template when setting up or auditing FSL service territories. Fill in each section for the org being configured.

---

## Scope

**Org:** _______________________________________________

**Request summary:** _______________________________________________

**Date:** _______________________________________________

---

## Prerequisites Confirmed

- [ ] Field Service is enabled (Setup > Field Service Settings > Enable Field Service)
- [ ] ServiceTerritory and OperatingHours objects are accessible to the admin profile
- [ ] ServiceResource records exist for the technicians to be assigned
- [ ] Hard Boundary work rule status confirmed: [ ] Active  [ ] Not in use
- [ ] Territory hierarchy required: [ ] Yes (document depth: ___)  [ ] No

---

## 1. Operating Hours Inventory

List all `OperatingHours` records to create. One record per distinct time zone + schedule combination.

| Operating Hours Name | Time Zone | Days | Start Time | End Time | Territories Using This |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |

**Holiday operating hours needed:** [ ] Yes  [ ] No
If yes, list:
- _______________________________________________

---

## 2. Territory Hierarchy

Document the territory structure before creating records. Create parent territories before child territories.

```
[Level 1 - Region/National]
├── [Territory Name]
│   ├── [Level 2 - District/Zone]
│   │   ├── [Territory Name] — Operating Hours: ___
│   │   └── [Territory Name] — Operating Hours: ___
│   └── ...
└── ...
```

---

## 3. Territory Setup Checklist

For each territory, confirm the following before considering it complete:

| Territory Name | IsActive | OperatingHoursId Set | ParentTerritoryId Set | Notes |
|---|---|---|---|---|
| | [ ] | [ ] | [ ] N/A or ✓ | |
| | [ ] | [ ] | [ ] N/A or ✓ | |
| | [ ] | [ ] | [ ] N/A or ✓ | |

---

## 4. Territory Member Assignments

For each ServiceResource, document their membership assignments. Verify the "One Primary" rule is satisfied.

| Technician / Resource Name | ServiceResource Id | Territory Name | MemberType | EffectiveStartDate | EffectiveEndDate |
|---|---|---|---|---|---|
| | | | Primary | | (blank = open-ended) |
| | | | Primary | | |
| | | | Secondary | | |
| | | | Relocation | | REQUIRED |

**Member count per territory (must not exceed 50):**

| Territory Name | Member Count | Within Limit? |
|---|---|---|
| | | [ ] |
| | | [ ] |

---

## 5. Relocation Membership Audit

List all Relocation memberships. Every Relocation record must have both dates.

| ServiceResource | Destination Territory | EffectiveStartDate | EffectiveEndDate | Both Dates Present? |
|---|---|---|---|---|
| | | | | [ ] |
| | | | | [ ] |

---

## 6. Hard Boundary Compliance (complete only if Hard Boundary work rule is active)

For each territory where Hard Boundary is active, verify that schedulable technicians have Primary or Relocation membership (not Secondary only).

| Territory Name | Technician | MemberType | Satisfies Hard Boundary? |
|---|---|---|---|
| | | Primary | [ ] Yes |
| | | Secondary | [ ] No — upgrade to Primary or Relocation |
| | | Relocation | [ ] Yes (if dates valid) |

---

## 7. Polygon Boundaries (if polygon-based routing is in use)

- [ ] Polygon-based routing is enabled in scheduling policy
- [ ] ServiceTerritoryPolygon records created for all active territories
- [ ] Polygon coordinates verified for geographic accuracy
- [ ] No overlapping polygons without intentional multi-territory coverage design

---

## 8. Validation Run

- [ ] `python3 check_fsl_service_territory_setup.py --territories-csv territories.csv` — no issues
- [ ] `python3 check_fsl_service_territory_setup.py --members-csv members.csv` — no issues
- [ ] Test service appointment scheduled successfully in at least one territory
- [ ] Correct technicians appear as candidates in the Dispatcher Console
- [ ] Hard Boundary behavior confirmed (if applicable)

---

## Deviations and Notes

Record any intentional deviations from standard patterns and the reason:

| Deviation | Reason | Approved By |
|---|---|---|
| | | |
| | | |

---

## Sign-Off

| Role | Name | Date |
|---|---|---|
| Admin / Configurator | | |
| FSL Admin / Architect | | |
| UAT Sign-off | | |
