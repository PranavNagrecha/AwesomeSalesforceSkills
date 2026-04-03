# Escalation Rules — Configuration Template

Use this template to document the escalation rule configuration for an org.

---

## Escalation Rule Summary

| Property | Value |
|----------|-------|
| Rule Name | |
| Active | Yes / No |
| Object | Case |
| Business Hours Record | (e.g. "US Pacific Business Hours" or "Default — 24/7") |

---

## Rule Entries

### Entry 1

| Property | Value |
|----------|-------|
| Entry Order | 1 |
| Criteria | (e.g. Priority = P1) |
| Escalate when case age exceeds | ___ hours |
| Business Hours | Use business hours / 24/7 |
| Age basis | Case Created Date / Last Modified Date |

**Escalation Actions:**

| Time Threshold | Notify Target | Reassign To |
|---------------|---------------|-------------|
| ___ hours | (e.g. Case Owner's Manager) | (blank or queue name) |
| ___ hours | (e.g. Escalations Queue) | Escalations Queue |

---

### Entry 2 (if applicable)

| Property | Value |
|----------|-------|
| Entry Order | 2 |
| Criteria | (e.g. Priority = P2) |
| Escalate when case age exceeds | ___ hours |
| Business Hours | Use business hours / 24/7 |
| Age basis | Case Created Date / Last Modified Date |

**Escalation Actions:**

| Time Threshold | Notify Target | Reassign To |
|---------------|---------------|-------------|
| ___ hours | | |

---

## Business Hours Configuration

| Property | Value |
|----------|-------|
| Business Hours Record Name | |
| Time Zone | |
| Monday | _:__ AM to _:__ PM / Closed |
| Tuesday | _:__ AM to _:__ PM / Closed |
| Wednesday | _:__ AM to _:__ PM / Closed |
| Thursday | _:__ AM to _:__ PM / Closed |
| Friday | _:__ AM to _:__ PM / Closed |
| Saturday | _:__ AM to _:__ PM / Closed |
| Sunday | _:__ AM to _:__ PM / Closed |

---

## Validation Checklist

- [ ] Only one escalation rule is active in the org
- [ ] Rule entries are ordered correctly (most specific criteria first)
- [ ] All escalation time thresholds match agreed SLA windows
- [ ] Business hours record exists and is configured with correct working hours
- [ ] All escalation action notify targets are active users or populated queues
- [ ] Test case was aged past the threshold and escalation fired as expected
- [ ] Off-hours escalation behavior was tested (for business-hours entries)
- [ ] Rule entry criteria values match the actual picklist values used in production

---

## Notes

(Record any deviations from standard patterns, special case criteria, or stakeholder decisions here.)
