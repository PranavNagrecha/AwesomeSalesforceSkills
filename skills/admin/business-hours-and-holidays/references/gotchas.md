# Gotchas — Business Hours and Holidays

Non-obvious platform behaviors that cause real production problems. Each is grounded in the Metadata API Developer Guide, the Object Reference, or the Apex Reference Guide (v62 PDFs) cited in `well-architected.md`; where a behavior could not be re-verified against an official page it is marked UNVERIFIED beside the claim.

## Gotcha 1: The shipped default calendar is 24 hours a day, 7 days a week

**What happens:** Every new org contains a calendar named `Default` with `default` = `true` and every weekday stored as start `00:00:00.000Z`, end `00:00:00.000Z`. The Metadata API guide's own sample definition shows exactly this shape, and the same pair of values means "open the whole day". Escalation entries left on the default, entitlement processes with no calendar, and Apex calls that fall back to `IsDefault = true` all count wall-clock time.

**When it occurs:** Any org that enabled escalation rules or entitlements before anyone edited the default calendar. The symptom is an SLA that "breaches over the weekend".

**How to avoid:** Decide explicitly what the default should be. Either edit it to the primary region's hours or create regional calendars and set one of them as default. Never leave the shipped 24/7 calendar as the default in an org that promises business-hours SLAs.

---

## Gotcha 2: A holiday only pauses calendars it is attached to

**What happens:** In `BusinessHoursSettings`, each `holidays` entry carries a `businessHours` value, "the name of the business hours setting that applies to this holiday". A holiday with no calendar attached is stored and displayed in Setup but suspends nothing. The Object Reference states the effect only for associated holidays: business hours and the escalation rules that use them are suspended during the dates and times specified as holidays.

**When it occurs:** Admin creates the year's public holidays from the Holidays page and stops there, or adds a second regional calendar after the holidays were created and forgets to attach them to it.

**How to avoid:** Treat attachment as part of creating a holiday. Retrieve `Settings:BusinessHours` and check that every `holidays` entry names the calendars it should; the skill's checker flags unattached holidays.

---

## Gotcha 3: Each escalation entry chooses its own calendar source

**What happens:** An escalation rule entry has `businessHoursSource` = `None`, `Case`, or `Static`. `None` ignores every calendar. `Static` uses the named `businessHours` and ignores the Case's field. Only `Case` reads `Case.BusinessHoursId`. A regional design that populates the Case field is silently defeated by any entry still set to `None` or to a static calendar.

**When it occurs:** Escalation rules built before regional calendars existed; a "Sev-1 always on" entry copied to create a Sev-2 entry without changing the source.

**How to avoid:** List every entry with its source (`admin/escalation-rules`, `references/metadata-examples.md` in `admin/assignment-rules` shows the XML), and make `None` a deliberate, documented exception.

---

## Gotcha 4: `Case.BusinessHoursId` is empty unless something sets it

**What happens:** Nothing populates the Case's calendar at creation: not the assignment rule, not Email-to-Case, not Web-to-Case. An empty field means the org default for every consumer that says "use the Case's hours".

**When it occurs:** Regional calendars exist, escalation entries are correctly set to `Case`, and every case still follows the default calendar.

**How to avoid:** A before-save record-triggered Flow on Case sets `BusinessHoursId` from the account's region, origin, or entitlement, with an explicit fallback. It runs before the assignment rule and before any timer starts. Document the mapping in the intake design (`admin/case-management-setup`).

---

## Gotcha 5: Milestones read the process calendar, not the Case calendar, unless told otherwise

**What happens:** An entitlement process carries its own business hours, and each milestone can override them. Neither reads `Case.BusinessHoursId` by default. A Case with a regional calendar can therefore escalate on the regional clock (escalation rule set to `Case`) while its first-response milestone counts on the process calendar.

**When it occurs:** Entitlements added after escalation rules, configured by a different admin.

**How to avoid:** Choose one authority per SLA policy. Either the process calendar is the contract calendar and escalation entries use `Static` to match it, or the Case calendar is authoritative and the process is set accordingly. See `admin/entitlements-and-milestones` for the process-level versus milestone-level rule.

---

## Gotcha 6: Times are stored in the calendar's own time zone, and the documented file shape cannot tell "open all day" from "closed"

**What happens:** Day windows are stored as `HH:mm:ss.SSSZ` in the calendar's `timeZoneId`, not in the deploying user's zone and not in UTC despite the `Z` suffix. The shipped `Default` calendar is 24/7 and is stored with every day as start `00:00:00.000Z`, end `00:00:00.000Z`. The Metadata API guide's second sample calendar (`bh1`) also stores its weekend days as `00:00:00.000Z` to `00:00:00.000Z`, so from the documented shape alone you cannot tell whether that pair means "open 24 hours" or "closed" (UNVERIFIED: the guide does not say; set one day to closed and one to 24 hours in Setup, retrieve, and compare before hand-writing either).

**When it occurs:** Copying a calendar from one region to another and only changing `timeZoneId`; hand-writing a weekend as midnight-to-midnight from the sample and getting a seven-day calendar.

**How to avoid:** Build calendars in Setup once, retrieve `Settings:BusinessHours`, and use the retrieved file as the template. Verify a hand-edited calendar with a clock test (`references/examples.md`, Example 4) before relying on it.

---

## Gotcha 7: Apex methods take milliseconds and ignore nothing you did not pass

**What happens:** `add`, `addGmt`, and `diff` work in milliseconds (`60 * 60 * 1000L` for one hour in the Apex Developer Guide's example). `add` returns the local time zone result and `addGmt` the GMT result of the same calculation; mixing them shifts targets by the zone offset. `isWithin` includes holidays in its check; a date on an attached holiday returns `false`. Passing a null or inactive calendar Id is a runtime error, not a fallback to the default.

**When it occurs:** Custom SLA code that passes `Case.BusinessHoursId` directly when the field can be empty; unit conversions that use seconds.

**How to avoid:** Resolve the calendar first (`BusinessHoursId != null ? BusinessHoursId : defaultId`), keep one unit helper, and test with a start time just before closing and a start time on a holiday.

---

## Gotcha 8: The settings file is the whole calendar set

**What happens:** All calendars and holidays deploy as one `Settings` member, `BusinessHours`. Deploying a hand-built file with one calendar into an org that has five is a change to the whole set, and a sandbox refresh replaces the sandbox file with production's. A calendar that is referenced by an escalation entry, an entitlement process, or a Case cannot simply disappear; deactivate rather than delete.

**When it occurs:** Deploying business hours from a scratch org into a long-lived sandbox; editing the file after a refresh from a stale branch.

**How to avoid:** Retrieve `Settings:BusinessHours` from the target org first, merge, deploy the merged file, and keep the file in source control so a refresh does not lose sandbox-only calendars.
