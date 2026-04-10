# FSL Optimization Architecture — Work Template

Use this template when designing or reviewing FSL scheduling optimization architecture.

## Scope

**Skill:** `fsl-optimization-architecture`

**Request summary:** (fill in)

## Territory Sizing Analysis

| Territory | Resources | SA/Day (avg) | Within Limits? | Action |
|-----------|-----------|--------------|----------------|--------|
| (name) | (count) | (count) | ≤50 / ≤1000 | Split / OK |

## Optimization Mode Selection

- [ ] **Global optimization** — nightly batch scheduling
- [ ] **In-Day optimization** — real-time same-day disruption handling
- [ ] **Resource Schedule** — individual technician re-optimization
- [ ] **Reshuffle** — fill gaps around pinned appointments

## ESO Adoption Plan

- **ESO licensed:** yes / no
- **Pilot territories (2-3):** (list)
- **Pilot validation period:** (e.g., 3 weeks)
- **Rollout sequence:** (territory order)
- **Manual dispatch contingency documented:** yes / no

## Optimization Schedule

| Region/Territory | Optimization Window | Mode | Notes |
|------------------|-------------------|------|-------|
| Territory A | 10:00pm – 10:45pm | Global | No shared resources with B |
| Territory B | 10:45pm – 11:30pm | Global | Serialized after A |

## Monitoring Plan

- [ ] Scheduled report or Flow checks optimization job status each morning
- [ ] Alert sent to dispatch manager if any job shows non-Completed status
- [ ] ESO operation limit thresholds documented and monitored

## Checklist

- [ ] No territory exceeds 50 resources or 1,000 SA/day
- [ ] ESO adoption is phased, not all-at-once
- [ ] Territories sharing resources have serialized optimization windows
- [ ] Manual dispatch contingency documented for ESO-enrolled territories
- [ ] Pinned appointment policy documented
- [ ] Monitoring in place for silent optimization failures

## Notes

(Record design decisions and rationale.)
