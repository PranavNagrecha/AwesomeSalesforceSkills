# Business Hours and Holidays — Design Sheet

Fill this before creating or deploying calendars. Every row maps to a `businessHours` or `holidays` entry in `settings/BusinessHours.settings-meta.xml` or to a consumer setting.

## SLA promise

| Question | Answer |
|---|---|
| SLA wording in the contract or policy | e.g. "first response within 4 business hours" |
| Business time or calendar time? | |
| Round-the-clock exceptions (case types, severities) | |
| Owner of the yearly holiday update | |

## Calendars

| Calendar name | Default? | Time zone | Mon–Fri window | Sat | Sun | Used by (region / team / tier) |
|---|---|---|---|---|---|---|
| US Support Hours | yes | America/New_York | 08:00–20:00 | closed | closed | US accounts |
| EMEA Support Hours | no | Europe/London | 08:00–18:00 | closed | closed | EMEA accounts |

## Holidays (next 12 months)

| Holiday | Date / recurrence | Whole day or window | Attached calendars |
|---|---|---|---|
| New Year's Day | recurring from 2026-01-01 | whole day | US, EMEA |
| Christmas Eve early close | 2026-12-24 | 13:00–18:00 | EMEA |

## How a Case gets its calendar

| Input available at creation | Mapping | Fallback |
|---|---|---|
| Account.Region__c | EMEA → EMEA Support Hours; else US Support Hours | default calendar; log miss |

Implemented as: before-save record-triggered Flow on Case (Example 2).

## Consumer map

| Consumer | Setting | Calendar it reads | Confirmed? |
|---|---|---|---|
| Escalation rule entry "High priority" | `businessHoursSource` = Case | Case's calendar | [ ] |
| Escalation rule entry "Sev-1" | `businessHoursSource` = None | none (24/7 by design) | [ ] |
| Entitlement process "Premier" | process-level calendar | US Support Hours | [ ] |
| Milestone "First Response" | inherits process | US Support Hours | [ ] |
| Apex `CaseBusinessTime` | `Case.BusinessHoursId` with default fallback | Case's calendar | [ ] |

## Deploy and test

- [ ] `Settings:BusinessHours` retrieved from target, merged, checker run
- [ ] Deployed; `SELECT Name, IsDefault, IsActive, TimeZoneSidKey FROM BusinessHours` matches this sheet
- [ ] Clock test (Example 4) passed for each calendar and one attached holiday
