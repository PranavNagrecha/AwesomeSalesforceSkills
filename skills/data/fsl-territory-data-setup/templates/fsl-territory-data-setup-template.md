# FSL Territory Data Setup — Work Template

Use this template when bulk loading FSL service territory data.

## Scope

**Skill:** `fsl-territory-data-setup`

**Request summary:** (fill in)

## Context Gathered

- **Territory hierarchy depth:** (e.g., Region → District → Territory — 3 levels)
- **Polygon boundaries in scope:** yes / no
- **Unique operating hours patterns:** (count and list)
- **Resource count per territory (max):** (confirm ≤ 50 per territory)
- **Timezone coverage:** (list timezones, confirm no polygon crosses timezone line)

## Load Sequence

| Step | Object | Operation | Notes |
|------|--------|-----------|-------|
| 1 | OperatingHours | Upsert on Legacy_OH_Id__c | One per unique schedule |
| 2 | TimeSlot | Upsert on Legacy_TS_Id__c | Reference OperatingHours ext ID |
| 3 | ServiceTerritory (top level) | Upsert on Legacy_ST_Id__c | No parent |
| 4 | ServiceTerritory (mid level) | Upsert on Legacy_ST_Id__c | Map ParentTerritoryId |
| 5 | ServiceTerritory (leaf) | Upsert on Legacy_ST_Id__c | Map ParentTerritoryId |
| 6 | Polygon import (if in scope) | KML via Setup | One KML per territory |
| 7 | ServiceTerritoryMember | Upsert on Legacy_STM_Id__c | EffectiveStartDate + TerritoryType required |

## ServiceTerritoryMember CSV Required Columns

```
Legacy_STM_Id__c, ServiceTerritoryId (via Legacy_ST_Id__c), ServiceResourceId (via Legacy_SR_Id__c),
TerritoryType, EffectiveStartDate, EffectiveEndDate (if relocation)
```

## Validation Checklist

- [ ] All parent territories exist before child loads
- [ ] EffectiveStartDate present on all STM records
- [ ] TerritoryType explicitly set on all STM records
- [ ] No territory exceeds 50 members
- [ ] Polygon import verified with PolygonUtils.getServiceTerritoryForLocation()
- [ ] Test booking run confirms correct territory assignment and slot retrieval

## Notes

(Record deviations and any special handling.)
