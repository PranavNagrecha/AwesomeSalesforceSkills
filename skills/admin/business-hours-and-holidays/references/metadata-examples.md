# Metadata Examples — Business Hours and Holidays

A second deployable scenario, grounded directly in the Metadata API Developer
Guide's `BusinessHoursSettings` reference and its declarative sample
definition (PDF v62, pages 2030–2033; line numbers below cite the plain-text
extraction, `api_meta.txt`, as `api_meta L<n>`). `references/examples.md`
covers a two-region support desk; this file covers a single-region
field-service dispatcher org with a genuine weekend-only calendar and a
named always-open severity tier.

## Scenario

A field-service dispatcher org, one region (Central time), three calendars:

- **`Dispatch Weekdays`** — the org default. Monday–Friday 07:00–19:00
  `America/Chicago`. This is the calendar every consumer with no calendar of
  its own falls back to, so it must not be the shipped 24/7 shape (gotcha 1).
- **`Weekend Standby`** — Saturday and Sunday only, 08:00–16:00
  `America/Chicago`, for the reduced weekend dispatch crew. Not the default.
- **`Critical 24x7`** — every day `00:00:00.000Z`–`00:00:00.000Z`, for a
  severity-1 entitlement that must never pause. Named explicitly (not
  `Default`) and not marked `<default>`, so it is the deliberate, non-default
  always-open shape the checker treats as INFO rather than ERROR (gotcha 1;
  same pattern as `Severity 1 24x7` in `references/examples.md` Example 1).

## Field grounding

`BusinessHoursSettings` has two child collections, `businessHours`
(`BusinessHoursEntry[]`) and `holidays` (`Holidays[]`) — `api_meta
L111281–111284`. In the package manifest "all organization settings
metadata types are accessed using the Settings name" (`api_meta L111267`),
and "there's only one settings file for each settings component" (`api_meta
L111272`). `BusinessHoursEntry` fields (`timeZoneId`, `name`, `active`,
`default`, and the fourteen `<day>StartTime`/`<day>EndTime` fields in
`HH:mm:ss.SSSZ`) are documented at `api_meta L111288–111357`. `Holidays`
fields (`name`, `description`, `isRecurring`, `activityDate`,
`recurrenceStartDate`, `recurrenceEndDate`, `startTime`, `endTime`,
`recurrenceType`, `recurrenceInterval`, `recurrenceDayOfWeek`,
`recurrenceDayOfMonth`, `recurrenceInstance`, `recurrenceMonthOfYear`,
`businessHours`) are documented at `api_meta L111361–111415`; `description`
specifically at `api_meta L111367`. The declarative sample definition — the
`Default` / `bh1` calendars and the `Labor Day` / `Christmas` holidays —
runs `api_meta L111420–111487`, and the matching package.xml sample runs
`api_meta L111489–111505`.

**Element order below follows the guide's sample, not `examples.md`'s
reading order.** The guide's own sample serializes each entry's child
elements alphabetically (`active`, `default`, `fridayEndTime`,
`fridayStartTime`, … `wednesdayStartTime` for a calendar; `activityDate`,
`businessHours`, `isRecurring`, `name`, `recurrence*`, `recurrenceType` for a
holiday — `api_meta L111423–111486`), which is also the shape a `sf project
retrieve` produces. `examples.md` reorders elements for human readability;
this file mirrors the retrieved shape instead, since gotcha 6 already
recommends building in Setup and retrieving rather than hand-writing.

## `force-app/main/default/settings/BusinessHours.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<BusinessHoursSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <businessHours>
        <active>true</active>
        <default>true</default>
        <fridayEndTime>19:00:00.000Z</fridayEndTime>
        <fridayStartTime>07:00:00.000Z</fridayStartTime>
        <mondayEndTime>19:00:00.000Z</mondayEndTime>
        <mondayStartTime>07:00:00.000Z</mondayStartTime>
        <name>Dispatch Weekdays</name>
        <thursdayEndTime>19:00:00.000Z</thursdayEndTime>
        <thursdayStartTime>07:00:00.000Z</thursdayStartTime>
        <timeZoneId>America/Chicago</timeZoneId>
        <tuesdayEndTime>19:00:00.000Z</tuesdayEndTime>
        <tuesdayStartTime>07:00:00.000Z</tuesdayStartTime>
        <wednesdayEndTime>19:00:00.000Z</wednesdayEndTime>
        <wednesdayStartTime>07:00:00.000Z</wednesdayStartTime>
    </businessHours>
    <businessHours>
        <active>true</active>
        <default>false</default>
        <name>Weekend Standby</name>
        <saturdayEndTime>16:00:00.000Z</saturdayEndTime>
        <saturdayStartTime>08:00:00.000Z</saturdayStartTime>
        <sundayEndTime>16:00:00.000Z</sundayEndTime>
        <sundayStartTime>08:00:00.000Z</sundayStartTime>
        <timeZoneId>America/Chicago</timeZoneId>
    </businessHours>
    <businessHours>
        <active>true</active>
        <default>false</default>
        <fridayEndTime>00:00:00.000Z</fridayEndTime>
        <fridayStartTime>00:00:00.000Z</fridayStartTime>
        <mondayEndTime>00:00:00.000Z</mondayEndTime>
        <mondayStartTime>00:00:00.000Z</mondayStartTime>
        <name>Critical 24x7</name>
        <saturdayEndTime>00:00:00.000Z</saturdayEndTime>
        <saturdayStartTime>00:00:00.000Z</saturdayStartTime>
        <sundayEndTime>00:00:00.000Z</sundayEndTime>
        <sundayStartTime>00:00:00.000Z</sundayStartTime>
        <thursdayEndTime>00:00:00.000Z</thursdayEndTime>
        <thursdayStartTime>00:00:00.000Z</thursdayStartTime>
        <timeZoneId>America/Chicago</timeZoneId>
        <tuesdayEndTime>00:00:00.000Z</tuesdayEndTime>
        <tuesdayStartTime>00:00:00.000Z</tuesdayStartTime>
        <wednesdayEndTime>00:00:00.000Z</wednesdayEndTime>
        <wednesdayStartTime>00:00:00.000Z</wednesdayStartTime>
    </businessHours>
    <holidays>
        <businessHours>Dispatch Weekdays</businessHours>
        <isRecurring>true</isRecurring>
        <name>New Year's Day</name>
        <recurrenceStartDate>2026-01-01</recurrenceStartDate>
    </holidays>
    <holidays>
        <businessHours>Dispatch Weekdays</businessHours>
        <isRecurring>true</isRecurring>
        <name>Christmas Day</name>
        <recurrenceDayOfMonth>25</recurrenceDayOfMonth>
        <recurrenceMonthOfYear>December</recurrenceMonthOfYear>
        <recurrenceStartDate>2026-12-25</recurrenceStartDate>
        <recurrenceType>RecursYearly</recurrenceType>
    </holidays>
    <holidays>
        <activityDate>2026-11-26</activityDate>
        <businessHours>Dispatch Weekdays</businessHours>
        <isRecurring>false</isRecurring>
        <name>Thanksgiving 2026</name>
    </holidays>
    <holidays>
        <activityDate>2026-12-26</activityDate>
        <businessHours>Weekend Standby</businessHours>
        <description>Extended holiday closure — standby crew stood down for the long weekend.</description>
        <isRecurring>false</isRecurring>
        <name>Weekend Standby Closure</name>
    </holidays>
</BusinessHoursSettings>
```

How to read it:

- **`Dispatch Weekdays`** omits Saturday/Sunday elements entirely rather than
  writing them as `00:00:00.000Z`–`00:00:00.000Z`. The guide's own `bh1`
  sample calendar *does* write closed weekend days that way (`api_meta
  L111459–111462`), but gotcha 6 already flags that the guide never states
  whether that pair means "open all day" or "closed" — `UNVERIFIED
  (2026-09-12): unresolved by the guide, carried over from gotcha 6, not
  newly introduced here.` Omitting the elements sidesteps the ambiguity
  rather than resolving it.
- **`Weekend Standby`** is the opposite shape: only `saturday*`/`sunday*`
  elements are present, no weekday elements at all, matching the same
  omit-what's-closed convention.
- **`Critical 24x7`** is every day `00:00:00.000Z`–`00:00:00.000Z` on
  purpose — the shipped-`Default` shape (`api_meta L111424–111449`), but on
  a calendar that is neither `<default>true</default>` nor named literally
  `Default`, which is exactly the condition the checker treats as INFO, not
  ERROR (see Verification below). No holiday is attached to it, which is
  also deliberate.
- **`Christmas Day`** mirrors the guide's own recurring-holiday sample
  almost element-for-element: `isRecurring`, `recurrenceDayOfMonth`,
  `recurrenceMonthOfYear`, `recurrenceStartDate`, `recurrenceType` together
  (`api_meta L111478–111486`, the `Christmas` holiday keyed to `bh1`). This
  is the most strongly grounded of the four holidays.
- **`New Year's Day`** uses only `isRecurring` + `recurrenceStartDate`, no
  `recurrenceType` — the same simpler shape `references/examples.md` already
  ships for its own New Year's Day holiday. `UNVERIFIED (2026-09-12): the
  guide's only recurring-holiday sample (Christmas) pairs
  recurrenceType/recurrenceMonthOfYear/recurrenceDayOfMonth with
  recurrenceStartDate; whether recurrenceStartDate alone is sufficient
  without recurrenceType is not stated. The checker does not require
  recurrenceType (it only requires recurrenceStartDate on a recurring
  holiday); deploy-time acceptance of the simpler shape is not independently
  confirmed here.`
- **`Weekend Standby Closure`** is the only holiday using `description`. The
  guide documents the field as "The description of the holiday" (`api_meta
  L111367`) but its own sample definition does not include `description` on
  either sample holiday. `UNVERIFIED (2026-09-12): description reads as a
  free-text label with no documented behavioral effect beyond display —
  the guide states its purpose but does not demonstrate it or say whether
  anything reads it back.`
- Recurring holidays are never checked against today's date; only
  non-recurring `activityDate` values are checked for staleness (script
  behavior, `check_business_hours_and_holidays.py`, not a Metadata API
  guarantee) — which is why `Christmas Day`'s `recurrenceStartDate` of
  `2026-12-25` and `New Year's Day`'s of `2026-01-01` both pass even though
  one predates today (2026-09-12) and the other doesn't.

## `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>BusinessHours</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

Member and type name (`BusinessHours` under `Settings`) match the guide's own
package.xml sample for this settings type (`api_meta L111489–111494` and
the general rule that "all organization settings metadata types are accessed
using the Settings name," `api_meta L111267`). The guide's own package.xml
sample pins `<version>29.0</version>` (`api_meta L111504`) — the minimum API
version `BusinessHoursSettings` supports (`api_meta L111276`), not a ceiling.
`62.0` here is a deliberate, current-API choice, not a grounding gap.

## Deploy order and retrieval shape

All calendars and holidays for the whole org live in this **one** file —
`businessHours.settings` at rest, retrieved/deployed as
`BusinessHours.settings-meta.xml` (`api_meta L111271–111272`, "there's only
one settings file for each settings component"). There is no per-calendar or
per-holiday deploy: a deploy of this file replaces the org's entire calendar
and holiday set, exactly as gotcha 8 describes.

```bash
# Retrieve first — the target org's existing calendars and holidays are
# the baseline; merge this scenario's calendars into that file rather than
# overwriting it blind (gotcha 8).
sf project retrieve start --metadata Settings:BusinessHours --target-org my-sandbox

# Validate the merged file before deploying.
python3 skills/admin/business-hours-and-holidays/scripts/check_business_hours_and_holidays.py \
  --manifest-dir force-app/main/default

# One file, one deploy — there is no way to deploy a subset of calendars.
sf project deploy start --metadata Settings:BusinessHours --target-org my-sandbox
```

## Verification

Run against the extracted example above (`--manifest-dir` pointed at the
directory containing `settings/BusinessHours.settings-meta.xml`):

```
$ python3 skills/admin/business-hours-and-holidays/scripts/check_business_hours_and_holidays.py --manifest-dir <extracted-example-dir>
INFO: BusinessHours.settings-meta.xml / always-open calendar 'Critical 24x7': SLA clocks on it never pause — intended for 24/7 severity tiers; confirm it is not attached to entitlements that expect business-hour pauses.
$ echo $?
0
```

This is the actual output of running the checker against the file above,
captured 2026-09-12. Exactly one INFO line, for `Critical 24x7` — the
non-default, non-`Default`-named always-open calendar — and exit `0`.
`Dispatch Weekdays` (the default) has real weekday windows, not the
midnight-to-midnight shape, so it never reaches the ERROR branch that gotcha
1 describes; `Weekend Standby` has real Saturday/Sunday windows, not
midnight-to-midnight, so it produces no finding at all. Every holiday names
a calendar that exists in the file (`Dispatch Weekdays` or
`Weekend Standby`), so none trips the "attached to unknown calendar" or
"attached to no calendar" checks, and both non-recurring `activityDate`
values (`2026-11-26`, `2026-12-26`) are after 2026-09-12, so neither trips
the stale-holiday check.

`--strict` produces the same output and the same exit code here — there is
no missing-settings-file WARN to promote, and `--strict` never promotes
INFO (script docstring, `check_business_hours_and_holidays.py` lines 20–25).
