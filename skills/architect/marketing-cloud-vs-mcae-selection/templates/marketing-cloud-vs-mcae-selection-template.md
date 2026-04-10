# Marketing Cloud vs. MCAE Platform Selection — Work Template

Use this template when working on platform selection tasks for a Salesforce marketing implementation.

## Scope

**Skill:** `marketing-cloud-vs-mcae-selection`

**Request summary:** (describe what the customer or stakeholder is trying to decide)

---

## Context Gathered

Answer each question before making a recommendation.

### Audience Type
- [ ] B2C (consumer-facing, subscriber-based, self-serve)
- [ ] B2B (known prospects tied to Accounts, sales-assisted)
- [ ] Mixed (both B2C and B2B motions present)

If mixed, document the volume and primary motion for each segment:

| Segment | Audience Type | Estimated Volume | Primary Channel |
|---|---|---|---|
| (segment name) | B2B / B2C | (count) | (email / SMS / push / etc.) |

### Channel Requirements

| Channel | Required? | Notes |
|---|---|---|
| Email | Yes / No | |
| SMS | Yes / No | If yes, MCE is required |
| Push notifications | Yes / No | If yes, MCE is required |
| In-app messaging | Yes / No | If yes, MCE is required |
| Advertising audiences | Yes / No | If yes, MCE Advertising Studio required |
| Social posting | Yes / No | |

### Volume and Record Counts
- Estimated subscriber / prospect count (current): ___________
- Estimated subscriber / prospect count (12-month projection): ___________
- Estimated subscriber / prospect count (36-month projection): ___________

MCAE edition limits for reference:
- Growth / Plus / Advanced: 10,000 prospects
- Premium: 75,000 prospects
- Above 75,000: MCE required for that audience

### Sales Alignment Requirements
- [ ] Sales team needs prospect-level engagement data in Salesforce CRM
- [ ] Lead scoring required (activity-based numeric score)
- [ ] Lead grading required (profile-fit letter grade)
- [ ] Automated sales alerts on hot prospects required
- [ ] Opportunity influence / campaign attribution required in CRM
- [ ] None of the above — no sales alignment needed

If any of the above are checked, MCAE is required.

### CRM Integration Requirements
- [ ] Real-time (or near-real-time) bidirectional sync with Salesforce Leads/Contacts
- [ ] Custom object sync with Salesforce
- [ ] Opt-out sync only
- [ ] No CRM integration required

Notes: (describe the specific sync requirements)

### License Availability
- [ ] MCE license available / budgeted
- [ ] MCAE license available / budgeted
- [ ] Both available / budgeted
- [ ] Budget allows only one platform — document which

---

## Platform Recommendation

Based on context gathered above, the recommended platform configuration is:

- [ ] **MCE only** — rationale: (fill in)
- [ ] **MCAE only** — rationale: (fill in)
- [ ] **Both MCE + MCAE with MC Connect** — rationale: (fill in)

---

## Decision Matrix

| Requirement | MCE Capability | MCAE Capability | Decision Driver |
|---|---|---|---|
| Email sending at scale | Yes — Data Extensions, no record limit | Yes — up to 75K prospects | MCE if >75K |
| SMS | Yes — MobileConnect | No | MCE required if SMS in scope |
| Push notifications | Yes — MobilePush | No | MCE required if push in scope |
| Lead scoring | No | Yes — activity-based scoring | MCAE required if scoring needed |
| Lead grading | No | Yes — profile-based grading | MCAE required if grading needed |
| Native CRM Lead/Contact sync | Requires MC Connect | Yes — native bidirectional | MCAE advantage for B2B |
| Engagement Studio nurture | No | Yes | MCAE required for rule-based nurture |
| Journey Builder | Yes | No | MCE required for event-driven journeys |
| Advertising audiences | Yes — Advertising Studio | No | MCE required for retargeting |

---

## Capability Gap Register

Document what the selected platform configuration does NOT cover:

| Capability Gap | Accepted? | Mitigation (if any) |
|---|---|---|
| (capability not covered) | Yes / No | (custom integration, future license, etc.) |

---

## Open Questions

List requirements not yet confirmed that could change this recommendation:

1. (question)
2. (question)
3. (question)

---

## Review Checklist

- [ ] Audience type documented (B2C / B2B / mixed)
- [ ] All required channels confirmed; SMS/push drives MCE requirement
- [ ] Prospect/subscriber volume confirmed against MCAE edition limits
- [ ] Sales alignment requirements assessed (scoring, grading, CRM sync)
- [ ] License availability confirmed
- [ ] Capability gaps documented and accepted by stakeholder
- [ ] MC Connect scope addressed if both platforms recommended
- [ ] Recommendation documented with written rationale

---

## Notes

(Record any deviations from the standard decision logic, unusual requirements, or customer-specific constraints.)
