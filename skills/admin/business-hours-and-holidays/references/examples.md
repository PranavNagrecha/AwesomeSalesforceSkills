# Examples — Business Hours and Holidays

## Example 1: Two regional calendars with attached holidays (deployable)

**Context:** EMEA support works 08:00 to 18:00 London time Monday to Friday; US support works 08:00 to 20:00 Eastern Monday to Friday. US is the default. Each region observes its own public holidays; one holiday (New Year's Day) applies to both.

`force-app/main/default/settings/BusinessHours.settings-meta.xml`, deployed as `Settings` member `BusinessHours` (shape per the Metadata API Developer Guide sample; the day windows below were built in Setup and retrieved, see gotchas #6):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<BusinessHoursSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <businessHours>
        <active>true</active>
        <default>true</default>
        <name>US Support Hours</name>
        <timeZoneId>America/New_York</timeZoneId>
        <mondayStartTime>08:00:00.000Z</mondayStartTime>
        <mondayEndTime>20:00:00.000Z</mondayEndTime>
        <tuesdayStartTime>08:00:00.000Z</tuesdayStartTime>
        <tuesdayEndTime>20:00:00.000Z</tuesdayEndTime>
        <wednesdayStartTime>08:00:00.000Z</wednesdayStartTime>
        <wednesdayEndTime>20:00:00.000Z</wednesdayEndTime>
        <thursdayStartTime>08:00:00.000Z</thursdayStartTime>
        <thursdayEndTime>20:00:00.000Z</thursdayEndTime>
        <fridayStartTime>08:00:00.000Z</fridayStartTime>
        <fridayEndTime>20:00:00.000Z</fridayEndTime>
    </businessHours>
    <businessHours>
        <active>true</active>
        <default>false</default>
        <name>EMEA Support Hours</name>
        <timeZoneId>Europe/London</timeZoneId>
        <mondayStartTime>08:00:00.000Z</mondayStartTime>
        <mondayEndTime>18:00:00.000Z</mondayEndTime>
        <tuesdayStartTime>08:00:00.000Z</tuesdayStartTime>
        <tuesdayEndTime>18:00:00.000Z</tuesdayEndTime>
        <wednesdayStartTime>08:00:00.000Z</wednesdayStartTime>
        <wednesdayEndTime>18:00:00.000Z</wednesdayEndTime>
        <thursdayStartTime>08:00:00.000Z</thursdayStartTime>
        <thursdayEndTime>18:00:00.000Z</thursdayEndTime>
        <fridayStartTime>08:00:00.000Z</fridayStartTime>
        <fridayEndTime>18:00:00.000Z</fridayEndTime>
    </businessHours>
    <holidays>
        <name>New Year's Day</name>
        <businessHours>US Support Hours</businessHours>
        <businessHours>EMEA Support Hours</businessHours>
        <isRecurring>true</isRecurring>
        <recurrenceStartDate>2026-01-01</recurrenceStartDate>
    </holidays>
    <holidays>
        <name>Thanksgiving 2026</name>
        <businessHours>US Support Hours</businessHours>
        <isRecurring>false</isRecurring>
        <activityDate>2026-11-26</activityDate>
    </holidays>
    <holidays>
        <name>Boxing Day 2026</name>
        <businessHours>EMEA Support Hours</businessHours>
        <isRecurring>false</isRecurring>
        <activityDate>2026-12-28</activityDate>
    </holidays>
    <holidays>
        <name>Christmas Eve early close</name>
        <businessHours>EMEA Support Hours</businessHours>
        <isRecurring>false</isRecurring>
        <activityDate>2026-12-24</activityDate>
        <startTime>13:00:00.000Z</startTime>
        <endTime>18:00:00.000Z</endTime>
    </holidays>
</BusinessHoursSettings>
```

How to read it:

- A holiday lists every calendar it applies to with repeated `businessHours` elements; the guide's sample attaches Labor Day to both `Default` and `bh1` the same way.
- `startTime` / `endTime` are both absent for a whole-day holiday and both present for a partial day.
- Recurring holidays use `recurrenceStartDate` (and optionally `recurrenceEndDate`); one-off holidays use `activityDate`.
- Weekend days are omitted here because the file was retrieved from a calendar built in Setup with those days closed; do not add `00:00:00.000Z` pairs by hand (gotchas #6).

package.xml and CLI:

```xml
<types>
    <members>BusinessHours</members>
    <name>Settings</name>
</types>
```

```bash
sf project retrieve start --metadata Settings:BusinessHours --target-org my-sandbox
python3 skills/admin/business-hours-and-holidays/scripts/check_business_hours_and_holidays.py --manifest-dir force-app/main/default
sf project deploy start --metadata Settings:BusinessHours --target-org my-sandbox
```

## Example 2: Setting the Case calendar at creation (before-save Flow)

**Context:** Cases must follow their account's region.

**Flow design:** record-triggered Flow on Case, "A record is created", before-save, optimized for fast field updates.

1. Get Records: `BusinessHours` where `Name` equals the value mapped from `{!$Record.Account.Region__c}` (`EMEA` → `EMEA Support Hours`, everything else → `US Support Hours`). Store the Id only.
2. Decision: found a calendar?
3. Update the triggering record: `BusinessHoursId` = found Id; otherwise leave empty so the default applies, and log the miss in a text field for the weekly review.

**Why before-save:** the assignment rule and every escalation timer run after this point in the save, so the Case's calendar is already correct when the clock starts (`flow/flow-record-save-order-interaction`). An after-save update lands after the escalation engine computed its target on the default calendar (gotchas #4).

## Example 3: Working hours open, in Apex

```apex
public with sharing class CaseBusinessTime {

    private static Id defaultCalendarId {
        get {
            if (defaultCalendarId == null) {
                defaultCalendarId = [SELECT Id FROM BusinessHours WHERE IsDefault = true LIMIT 1].Id;
            }
            return defaultCalendarId;
        }
        set;
    }

    /** Business hours between case creation and now, on the case's calendar or the org default. */
    public static Decimal hoursOpen(Case c) {
        Id calendarId = c.BusinessHoursId != null ? c.BusinessHoursId : defaultCalendarId;
        Long ms = BusinessHours.diff(calendarId, c.CreatedDate, Datetime.now());
        return Decimal.valueOf(ms).divide(3600000, 2);
    }

    /** First-response target: 4 business hours from creation, or the next open time if created after hours. */
    public static Datetime firstResponseTarget(Case c) {
        Id calendarId = c.BusinessHoursId != null ? c.BusinessHoursId : defaultCalendarId;
        Datetime start = BusinessHours.nextStartDate(calendarId, c.CreatedDate);
        return BusinessHours.add(calendarId, start, 4 * 60 * 60 * 1000L);
    }
}
```

`diff` and `add` take milliseconds (the Apex Developer Guide example uses `60 * 60 * 1000L`); `nextStartDate` returns the input when it already falls inside business hours. Wrap the query in a cached property so bulk triggers do not query per record.

## Example 4: Clock test before go-live

**Context:** Prove the calendar pauses before trusting it with an SLA.

1. Note the EMEA calendar's Friday close (18:00 London).
2. At 17:30 London on a Friday, create a Case with `BusinessHoursId` = EMEA and an escalation entry set to `Case` with a 2-hour action.
3. Expected: the escalation fires at roughly 09:30 the following Monday (30 minutes Friday plus 90 minutes Monday), not at 19:30 Friday.
4. Repeat on the day before an attached holiday: the target lands on the first open day after the holiday.
5. If the target is Friday evening, work through `SKILL.md` gotchas in order: default calendar, entry source, Case field, holiday attachment.

## Anti-Pattern: One global calendar named "Business Hours"

A single calendar in the head office's time zone with head-office holidays. EMEA cases pause on US Thanksgiving and keep running on Boxing Day; APAC cases are "after hours" for the whole APAC working day. The fix is Example 1 plus Example 2, not a wider window on the one calendar.
