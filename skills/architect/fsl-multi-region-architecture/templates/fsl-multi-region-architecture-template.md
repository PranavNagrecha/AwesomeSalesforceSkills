# FSL Multi-Region Architecture — Work Template

Use this template when designing FSL for multiple geographic regions or timezones.

## Scope

**Skill:** `fsl-multi-region-architecture`

**Request summary:** (fill in)

## Context Gathered

- **Regions/timezones:** (list all IANA timezones in scope)
- **Total territories:** (count)
- **Cross-territory resources:** (count, description)
- **Optimization sharing risk:** (do any territories share resources? yes/no — detail)
- **International deployment:** yes/no

## Territory-Timezone Mapping

| Territory | Geographic Area | IANA Timezone | OperatingHours Record | Polygon Crosses Timezone? |
|-----------|----------------|---------------|----------------------|---------------------------|
| (name) | (area) | America/New_York | Business Hours — Eastern | No |

## OperatingHours Records Required

(One per unique timezone in the deployment)

| Name | IANA Timezone | Hours | Territories Using |
|------|--------------|-------|-------------------|

## Cross-Territory Resource Matrix

| Resource | Primary Territory | Secondary Territories | Boundary Type |
|----------|------------------|----------------------|---------------|

## Optimization Serialization Schedule

| Region | Territories | Optimization Window | Shared Resources With |
|--------|-------------|--------------------|-----------------------|
| Northeast | T1, T2, T3 | 10:00pm – 10:45pm | None |
| Southeast | T4, T5 | 10:45pm – 11:30pm | None |

## Architecture Checklist

- [ ] Each territory has OperatingHours with IANA timezone (not UTC offset)
- [ ] No territory polygon crosses a timezone line
- [ ] Territories sharing resources have serialized optimization windows
- [ ] Cross-territory resources have Secondary STM records + Soft Boundary policy
- [ ] Appointment booking tested near timezone boundaries for correct local times
- [ ] Multi-region deployment map documented

## Notes

(Record design decisions, territory split rationale, resource sharing details.)
