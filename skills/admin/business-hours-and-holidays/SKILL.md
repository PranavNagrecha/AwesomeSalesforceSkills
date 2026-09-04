---
name: business-hours-and-holidays
description: "Use this skill when creating, deploying, or troubleshooting Salesforce Business Hours and Holidays: the calendars that pause Case escalation rules, entitlement milestones, and Apex BusinessHours math outside working hours. Covers the BusinessHoursSettings metadata, the default calendar, per-region calendars, holiday attachment, the Case Business Hours field, and the BusinessHours Apex class. Trigger keywords: business hours, holidays, SLA clock, escalation not pausing, working hours, support hours, milestone timer weekend. NOT for the escalation rule entries themselves — use admin/escalation-rules. NOT for entitlement process design — use admin/entitlements-and-milestones. NOT for Field Service operating hours or shift scheduling — use admin/fsl-scheduling-setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "escalation rule is firing over the weekend even though we set business hours"
  - "how do I set up business hours and holidays for support cases"
  - "milestone SLA clock is not pausing on public holidays"
  - "deploy business hours from sandbox to production"
  - "calculate elapsed working hours between two dates in Apex"
  - "cases from EMEA are using the US business hours calendar"
tags:
  - business-hours
  - holidays
  - sla
  - escalation-rules
  - entitlements
  - case-management
inputs:
  - "Which regions or teams need their own calendar, with time zone and daily windows"
  - "Which consumers read the calendar: escalation rule entries, entitlement processes or milestones, Apex"
  - "How a Case should pick its calendar at creation (region, entitlement, channel)"
  - "Holiday list per region and whether each recurs"
outputs:
  - "Deployable BusinessHoursSettings metadata with calendars and attached holidays"
  - "Rule for populating Case.BusinessHoursId at creation"
  - "Consumer map: which escalation entries, milestones, and Apex read which calendar"
  - "Troubleshooting result for a clock that did not pause"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Business Hours and Holidays

Activates when an SLA clock has to stop outside working hours. A business-hours calendar is the only thing that makes escalation rules, milestones, and `BusinessHours` Apex methods count working time instead of wall-clock time, and a holiday only counts once it is attached to a calendar.

---

## Before Starting

- **Which calendar is the org default?** Setup ships with a default calendar that is 24 hours, 7 days. Every consumer that is not told otherwise reads it, so an org that "has business hours" but never edited the default is still running SLAs round the clock.
- **Who reads the calendar?** Escalation rule entries choose `None`, the Case's calendar, or a named calendar. Entitlement processes read the process-level calendar or a milestone-level override. Apex reads whichever Id you pass. Omni-Channel and approval processes read no calendar at all.
- **How does a Case get its calendar?** `Case.BusinessHoursId` is empty unless something sets it. Empty means the default calendar for every consumer that says "use the Case's hours".
- **Time zone per calendar.** Each calendar carries its own time zone; the daily windows are stored in that zone.

## Questions to Ask Before Configuring

Ask these before touching Setup; the answers decide the design, and an LLM that skips them produces a calendar that looks right and pauses nothing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which SLA promise are we making, and to whom: one business day, four working hours, calendar hours?" | Fixes whether business time is needed at all and which consumers must read it | The consumer map: escalation entries, milestones, Apex |
| "Which regions or teams work different hours or observe different holidays?" | Each distinct answer is a calendar | The calendar list, each with a time zone and holiday set |
| "How do we know a Case's region at creation?" | Decides the `Case.BusinessHoursId` rule; if unknowable at creation, the design falls back to the default | The before-save Flow logic and its fallback |
| "Is there any Case type that must be worked round the clock?" | Those escalation entries use `businessHoursSource` = `None` on purpose | Documented exceptions instead of accidental 24/7 |
| "Who maintains next year's holidays, and when?" | Holidays expire; unmaintained calendars silently stop pausing | An owner and a yearly deploy in the release calendar |
| "Do reports or code need elapsed working time?" | Formulas cannot compute it; Apex `diff` can | A decision to build (or not build) the Apex helper |

What a proper configuration adds over "just creating business hours": the SLA clock actually stops on weekends and holidays per region, escalation and milestone targets agree with each other, and the yearly holiday update is a reviewed deploy rather than a forgotten Setup task.

---

## Core Concepts

### The calendar record

A calendar is a `BusinessHours` record: name, active flag, default flag, time zone, and a start and end time for each weekday. All users can read `BusinessHours` through the API even without setup permissions, which is why Apex and Flow can look one up freely. Exactly one calendar is the org default. The Object Reference states the escalation consequence directly: "Escalation rules are run only during these hours", and holidays associated with the calendar suspend both the hours and the escalation rules that use them.

| Field | Meaning |
|---|---|
| `Name` | Referenced by name in escalation rule metadata (`businessHours`) and in settings |
| `IsActive` | Inactive calendars cannot be selected by new consumers |
| `IsDefault` | The org default; only one |
| `TimeZoneSidKey` | Zone the day windows are expressed in |
| `MondayStartTime` … `SundayEndTime` | Window per weekday; a day with no window is closed |

### Deployable metadata: one settings file

All calendars and holidays live in one file, `settings/BusinessHours.settings-meta.xml`, deployed as `Settings` with member `BusinessHours` (API 29.0+). Each `businessHours` entry carries `name`, `active`, `default`, `timeZoneId`, and the fourteen day-window fields in `HH:mm:ss.SSSZ`. Each `holidays` entry carries `name`, `description`, `isRecurring`, `activityDate` (non-recurring), `recurrenceStartDate` / `recurrenceEndDate` (recurring), and `startTime` / `endTime`, which are both null for a whole-day holiday. The full example is in `references/examples.md`.

### Holidays are inert until attached

A holiday record does nothing by itself. It suspends time only for the calendars it is attached to, and a holiday can be attached to several calendars. "We added the holiday" with no attachment is the single most common reason a clock kept running on a public holiday.

### Apex `BusinessHours` methods

All static, all take the calendar Id as a String; intervals are milliseconds.

| Method | Returns |
|---|---|
| `add(bhId, start, ms)` | Datetime reached after `ms` of business time from `start`, in the local time zone |
| `addGmt(bhId, start, ms)` | Same, returned in GMT |
| `diff(bhId, start, end)` | Business milliseconds between two datetimes |
| `isWithin(bhId, target)` | `true` if `target` falls in business hours; holidays are included in the check |
| `nextStartDate(bhId, target)` | Next datetime the calendar is open, or `target` itself if already open |

---

## Common Patterns

### Pattern: Regional calendars selected at Case creation

**When to use:** Support teams in more than one region, one SLA policy, weekends and public holidays differ per region.

**How it works:**
1. Create one calendar per region (time zone, windows) and attach that region's holidays to it.
2. Keep the org default as the fallback region, not 24/7.
3. Add a before-save record-triggered Flow on Case that sets `BusinessHoursId` from the account's region, the Case origin, or the entitlement. The Flow runs before the assignment rule and before any escalation timer starts.
4. Point escalation entries at `businessHoursSource` = `Case` and milestones at the process default, so every consumer follows the Case's own calendar.

**Why not one calendar:** one calendar means every region's SLA pauses on one region's weekend and holidays.

### Pattern: Working-time age in Apex or a formula-backed field

**When to use:** Reports need "business hours open" or a trigger needs to act after N working hours.

**How it works:** `BusinessHours.diff(c.BusinessHoursId, c.CreatedDate, Datetime.now())` returns milliseconds of business time; divide by 3,600,000 for hours. Fall back to the default calendar when `BusinessHoursId` is null: `[SELECT Id FROM BusinessHours WHERE IsDefault = true]`. Formula fields cannot call the class, so write the result to a number field from a scheduled Flow or Apex.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single support team, one time zone | Edit the default calendar; attach holidays to it | Every consumer already reads the default |
| Several regions with different holidays | One calendar per region; set `Case.BusinessHoursId` at creation | Escalation and milestones can follow the Case's calendar |
| One escalation entry must ignore hours (Sev-1) | `businessHoursSource` = `None` on that entry | Entry-level choice beats a per-Case calendar |
| SLA defined by contract tier, not region | Calendar at entitlement-process or milestone level | Milestones read the process calendar, not the Case field |
| Need "hours open" on a report | Apex `diff` written to a field | No formula access to business time |

---

## Recommended Workflow

1. Inventory consumers — list every escalation entry (`businessHoursSource`), entitlement process, milestone override, and Apex call that reads a calendar; the agent `/configure-business-hours` does this as a referenced-by inventory
2. Design calendars — one per distinct time zone plus holiday set; decide which is the org default and whether the shipped 24/7 default is acceptable
3. Attach holidays — every holiday to every calendar it applies to; check the coming twelve months
4. Set the Case calendar — a before-save Flow populates `BusinessHoursId`; document the rule and the fallback
5. Deploy — retrieve `Settings:BusinessHours` first, edit, deploy the whole file; run `scripts/check_business_hours_and_holidays.py` on it
6. Test with a clock — create a Case just before closing time and confirm the escalation or milestone target date lands on the next open window (`references/examples.md`)

---

## Review Checklist

- [ ] The org default calendar is intentional, not the shipped 24/7 default
- [ ] Every calendar has the correct time zone and a window for each working day
- [ ] Every holiday is attached to at least one calendar and the next twelve months are covered
- [ ] `Case.BusinessHoursId` is populated at creation or the fallback is documented
- [ ] Each escalation entry's `businessHoursSource` (`None` / `Case` / `Static`) is the intended one
- [ ] Entitlement process and milestone calendars are reviewed with the process owner
- [ ] Apex callers handle a null `BusinessHoursId`
- [ ] A test Case created after hours produced a target time in the next open window

---

## Salesforce-Specific Gotchas

1. **The default calendar is 24/7 out of the box** — an org that never edited it runs every SLA round the clock while believing it "has business hours".
2. **Unattached holidays do nothing** — a holiday suspends time only for calendars it is attached to; the record's existence alone changes nothing.
3. **Escalation entries pick their own source** — an entry set to `Static` with a named calendar ignores the Case's calendar, and one set to `None` ignores all calendars; a regional design that only sets `Case.BusinessHoursId` is defeated by entries left on `None`.

Deeper treatment in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `settings/BusinessHours.settings-meta.xml` | All calendars and holidays, deployable as `Settings:BusinessHours` |
| Case calendar rule | Before-save Flow logic that sets `BusinessHoursId`, with fallback |
| Consumer map | Escalation entries, milestones, Apex callers and the calendar each reads |
| Clock test record | Evidence that an after-hours Case escalated in the next open window |

---

## Related Skills

- admin/escalation-rules — the entries that consume the calendar through `businessHoursSource`
- admin/entitlements-and-milestones — process-level and milestone-level calendars
- admin/case-management-setup — where `Case.BusinessHoursId` is set in the intake design
- admin/assignment-rules — routing runs at save; the calendar only governs what happens afterwards
- admin/omni-channel-routing-setup — a negative check: Omni-Channel availability has no calendar input
- flow/record-triggered-flow-patterns — the before-save Flow that populates the Case calendar
