# FSL Reporting Data Model — Work Template

Use this template when building FSL operational reports and dashboards.

## Scope

**Skill:** `fsl-reporting-data-model`

**Request summary:** (fill in — e.g. "Build FSL operations dashboard with FTF rate, travel time, and utilization")

## Context Gathered

- **FSL Mobile adoption rate:** (% of technicians consistently using mobile check-in)
- **CRM Analytics / FSI licensed:** yes / no (determines if pre-built dashboards available)
- **FTF rate required:** yes / no (requires custom Flow + checkbox field if yes)
- **Metrics required:** (list)

## Pre-Reporting Data Quality Check

Run this SOQL before building any travel time or duration reports:
```soql
SELECT COUNT(Id) total, 
       SUM(CASE WHEN ActualDuration != null THEN 1 ELSE 0 END) has_duration,
       SUM(CASE WHEN ActualTravelTime != null THEN 1 ELSE 0 END) has_travel
FROM ServiceAppointment WHERE Status = 'Completed' AND SchedStartTime = LAST_N_DAYS:90
```
If `has_duration` or `has_travel` << `total`, mobile check-in adoption is low. Address before building KPIs.

## Metric Source Map

| Metric | Object | Fields | Prerequisite |
|--------|--------|--------|--------------|
| Job duration | ServiceAppointment | ActualDuration | FSL Mobile check-out |
| Travel time | ServiceAppointment | ActualTravelTime | FSL Mobile En Route |
| On-time arrival | ServiceAppointment | ActualStartTime vs. ArrivalWindowEnd | FSL Mobile check-in |
| Schedule adherence | ServiceAppointment | ActualStartTime vs. SchedStartTime | FSL Mobile check-in |
| First-time fix rate | WorkOrder | Is_First_Time_Fix__c (custom) | Flow deployment |
| Utilization | ServiceResource + SA | SchedStartTime/EndTime (planned) or Actual | FSL Mobile for actual |

## FTF Rate Flow Design

- Trigger: ServiceAppointment after update, when Status changes to Completed
- Get parent WorkOrder
- Get all ServiceAppointments on same WorkOrder where Status = "Cannot Complete"
- If count = 0: WorkOrder.Is_First_Time_Fix__c = true
- If count > 0: WorkOrder.Is_First_Time_Fix__c = false

## Implementation Checklist

- [ ] Mobile adoption rate validated before committing travel time KPIs
- [ ] FTF custom field created and Flow deployed (if FTF required)
- [ ] Historical FTF data backfilled via batch Flow or SOQL
- [ ] Dashboard documentation notes mobile check-in data dependency
- [ ] ServiceReport NOT used as operational metrics source
- [ ] SchedStartTime vs. ActualStartTime distinction documented for consumers

## Notes

(Record deviations and data quality findings.)
