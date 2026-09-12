# Holiday maintenance runbook — M4-S01 (Business Hours and Holidays)

Declared output of `plan.json` `steps[M4-S01].outputs[]`. It exists because **Q90** was answered
("a named owner in Service Operations, with a yearly holiday deploy booked in the release calendar
each Q4") and because `skills/admin/business-hours-and-holidays/SKILL.md` § Questions to Ask records
the consequence of not having one: *"Holidays expire; unmaintained calendars silently stop pausing."*

**Nothing in this build deploys.** Every command below is text for a human to run.

---

## 1. Owner and cadence (Q90)

| Item | Value | Status |
|---|---|---|
| Accountable team | Service Operations | decided (Q90) |
| Named individual | **not supplied** — Q90 answered the role and the cadence, not the person | **OPEN** — name this person at the M4 gate |
| Cadence | one holiday deploy per year, booked in the Q4 release calendar | decided (Q90) |
| What the deploy covers | the next 12 months of holidays for **every** calendar in `settings/BusinessHours.settings-meta.xml` | decided |
| Trigger to bring it forward | any new region, any new calendar, or any change to a public-holiday date | this runbook |

The yearly deploy is not optional housekeeping. Every holiday in this file is a **one-off entry with
an explicit `activityDate`** (§ 3 says why), so the file stops pausing anything the day after its last
date passes, with no error anywhere.

## 2. The calendars this file maintains

| Calendar | Default? | Time zone | Window | Holidays attached |
|---|---|---|---|---|
| `US Support` | **yes** | `America/New_York` | Mon–Fri 08:00–20:00 | 6 |
| `EMEA Support` | no | `Europe/London` | Mon–Fri 08:00–18:00 | 9 |
| `Severity 1 24x7` | no | `America/New_York` | every day, all day | **none, by design** |

`Severity 1 24x7` carries no holidays on purpose: `requirement.md` L18 says Severity 1 outages
"are 24/7 and never pause", and a holiday attached to that calendar would pause it.
Its time zone is immaterial to a calendar that is always open; `America/New_York` was chosen to match
the org default (Q40 — "US is the default calendar") rather than to express a working region, and the
checker requires a `timeZoneId` on every calendar.

Weekends are **absent** from `US Support` and `EMEA Support` rather than written as
`00:00:00.000Z`–`00:00:00.000Z`. That is deliberate and grounded:
`skills/admin/business-hours-and-holidays/references/examples.md` says of its own sample, *"Weekend
days are omitted here because the file was retrieved from a calendar built in Setup with those days
closed; do not add `00:00:00.000Z` pairs by hand (gotchas #6)."*

## 3. The holiday set is a SEED, not Acme's list — confirm it before deploy

**Nothing in the clarification set supplies Acme's holiday list.** Q39 established that each region
observes its own holidays; no question asked which ones, and `answers-key.md` has no row for it. The
14 entries in the file are therefore the commonly observed public-holiday closures for the two regions
over the 12 months from 2026-09-12, seeded so that the calendars pause on *something* and so the
shape is reviewable. Every weekday below was computed, not recalled.

| Holiday | Date | Weekday | Calendars | Whole day? |
|---|---|---|---|---|
| Thanksgiving 2026 | 2026-11-26 | Thursday | US Support | yes |
| Day after Thanksgiving 2026 | 2026-11-27 | Friday | US Support | yes |
| Christmas Eve 2026 early close | 2026-12-24 | Thursday | EMEA Support | **no — 13:00–18:00** |
| Christmas Day 2026 | 2026-12-25 | Friday | US Support, EMEA Support | yes |
| Boxing Day 2026 (substitute day) | 2026-12-28 | Monday | EMEA Support | yes |
| New Year's Day 2027 | 2027-01-01 | Friday | US Support, EMEA Support | yes |
| Good Friday 2027 | 2027-03-26 | Friday | EMEA Support | yes |
| Easter Monday 2027 | 2027-03-29 | Monday | EMEA Support | yes |
| Early May bank holiday 2027 | 2027-05-03 | Monday | EMEA Support | yes |
| Spring bank holiday 2027 | 2027-05-31 | Monday | EMEA Support | yes |
| Memorial Day 2027 | 2027-05-31 | Monday | US Support | yes |
| Independence Day 2027 (observed) | 2027-07-05 | Monday | US Support | yes |
| Summer bank holiday 2027 | 2027-08-30 | Monday | EMEA Support | yes |
| Labor Day 2027 | 2027-09-06 | Monday | US Support | yes |

Notes a reviewer should check rather than assume:

- **Boxing Day 2026 falls on a Saturday**, so the entry uses the following Monday (2026-12-28). It is
  a substitute day, not the holiday's calendar date. Same shape as the skill's own worked example.
- **Independence Day 2027 falls on a Sunday**, so the entry uses the observed Monday (2027-07-05).
- **2027-05-31 carries two entries**, one per region (Memorial Day, Spring bank holiday). They are
  separate holidays that happen to coincide; merging them into one entry attached to both calendars
  would deploy fine but would misname the US closure.
- **Christmas Eve is a partial day** and is the one entry with `startTime` / `endTime`. Both must be
  present or both absent — the checker enforces the pair.
- Acme may close on days not listed (company days, regional offices) and may work on days listed.
  **The Service Operations owner replaces this table before the file is deployed to production.**

### Why every entry is non-recurring

`SKILL.md` documents `isRecurring`, `recurrenceStartDate` and `recurrenceEndDate` for a recurring
holiday, and the worked example shows `New Year's Day` as `isRecurring=true` with
`recurrenceStartDate=2026-01-01`. It documents **no element that states the recurrence frequency**
(yearly, monthly, which weekday of which month). So a recurring entry written from this skill alone
asserts "this repeats" without saying how — and this agent does not invent element names
(`agents/metadata-builder/AGENT.md` Step 5 rule 1). Every entry here is therefore the fully documented
form: `isRecurring=false` plus an explicit `activityDate`.

The cost is exactly the yearly deploy Q90 booked. The benefit is that the checker can see an expiry:
a one-off `activityDate` in the past is an ISSUE it reports by name, while a recurring entry with no
frequency would look healthy forever.

## 4. The yearly procedure (Q4, each year)

1. **Collect next year's dates** for each region from the authority the business uses (HR calendar,
   public-holiday source per country). Confirm the substitute-day rule for any holiday falling at a
   weekend.
2. **Retrieve the target org's current file first** — never deploy this file blind:

   ```bash
   sf project retrieve start --metadata Settings:BusinessHours --target-org <alias>
   ```

   `references/gotchas.md` #8: the settings file is the **whole** calendar set. Deploying a file
   holding three calendars into an org holding five removes nothing silently — it is a change to the
   entire set, and a sandbox refresh replaces the sandbox's file with production's.
3. **Merge** next year's entries into the retrieved file. Keep the expired entries out; keep every
   calendar the target org has that this build does not know about.
4. **Check** before deploying:

   ```bash
   python3 skills/admin/business-hours-and-holidays/scripts/check_business_hours_and_holidays.py \
     --manifest-dir <retrieved-dir>
   ```

   It reports: a holiday attached to no calendar or to an unknown one; a non-recurring holiday whose
   `activityDate` is in the past; a calendar with no window; more than one default; a default that is
   inactive; a `startTime` without an `endTime`.
5. **Deploy** (a human, in a sandbox first) and re-run the clock test in § 5.
6. **Record** the deploy in the release calendar and book the next one.

## 5. Clock test after every holiday deploy

From `references/examples.md` Example 4 — the evidence that the calendar actually pauses:

1. Create a Case with `BusinessHoursId` = `EMEA Support` at 17:30 London on the working day **before**
   an attached holiday, with an escalation entry on the `Case` source and a 2-hour action.
2. Expect the escalation target to land in the **first open window after the holiday**, not that
   evening and not on the holiday itself.
3. Repeat for `US Support`.
4. If the target lands inside the holiday, work the four causes in order: the org default calendar,
   the escalation entry's `businessHoursSource`, `Case.BusinessHoursId`, and whether the holiday is
   attached to that calendar (`SKILL.md` § Salesforce-Specific Gotchas).

## 6. What breaks if this runbook is not followed

| If | Then |
|---|---|
| No one owns the yearly deploy | every holiday expires after 2027-09-06 and both regional calendars run straight through every public holiday, with no error |
| Holidays are created in Setup but not attached | they suspend nothing (`gotchas.md` #2) — the Setup list looks complete |
| This file is deployed without retrieving the target first | the target org's other calendars are overwritten as a set (`gotchas.md` #8) |
| A new region is added without a calendar | its Cases fall back to `US Support`, the org default (Q40) — which is a decision, not a bug, only while someone has decided it |
