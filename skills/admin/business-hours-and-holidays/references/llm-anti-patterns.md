# LLM Anti-Patterns — Business Hours and Holidays

Mistakes AI assistants make in this domain, why they happen, and how to detect them.

## Anti-Pattern 1: Declaring the problem solved once a calendar exists

**What the LLM generates:** "Create Business Hours in Setup with your working hours, and escalation rules will now respect them."

**Why it happens:** The relationship between calendars and their consumers is indirect. Creating a calendar changes nothing until an escalation entry, an entitlement process, or a Case points at it.

**Correct pattern:** After creating the calendar, name the consumer and how it is wired: the escalation entry's `businessHoursSource`, the process-level calendar, or the Flow that sets `Case.BusinessHoursId`.

**Detection hint:** "business hours" configured with no mention of `businessHoursSource`, the entitlement process calendar, or `BusinessHoursId`.

## Anti-Pattern 2: Treating holidays as global

**What the LLM generates:** "Add the public holidays under Setup → Holidays and the SLA clock will pause on those days."

**Why it happens:** The Holidays page is separate from the calendar page, which suggests holidays apply everywhere.

**Correct pattern:** Each holiday must be attached to each calendar it applies to; in metadata that is the repeated `businessHours` element inside `holidays`.

**Detection hint:** Holiday instructions with no attachment step.

## Anti-Pattern 3: Assuming the default calendar is "office hours"

**What the LLM generates:** "Cases with no business hours set will use the default 9 to 5 calendar."

**Why it happens:** The word "default" suggests a sensible working week. The shipped default is 24/7.

**Correct pattern:** State that the shipped default is 24 hours, 7 days, and that it must be edited or replaced before it can be relied on.

**Detection hint:** Any claim about what the default calendar contains without a check.

## Anti-Pattern 4: Inventing a formula or Flow element for business time

**What the LLM generates:** A formula field using `BUSINESSHOURS()` or a Flow "Business Hours Diff" element.

**Why it happens:** Pattern-completion from other platforms and from the Apex class name.

**Correct pattern:** Business time is available only through the Apex `BusinessHours` class (`add`, `addGmt`, `diff`, `isWithin`, `nextStartDate`) or through platform consumers (escalation, milestones). Formulas and standard Flow elements cannot compute it; an invocable Apex action bridges Flow to the class.

**Detection hint:** Any formula function or Flow element name containing "BusinessHours" that is not the Apex class.

## Anti-Pattern 5: Writing calendar times in the wrong frame

**What the LLM generates:** Windows written in UTC "because of the Z", or `00:00:00.000Z` to `00:00:00.000Z` to mark a closed weekend.

**Why it happens:** The `Z` suffix looks like UTC; midnight-to-midnight reads as "no hours".

**Correct pattern:** Windows are in the calendar's `timeZoneId`; midnight-to-midnight is how the 24/7 default is stored; build closed days in Setup and retrieve rather than hand-writing them.

**Detection hint:** Hand-written settings XML with midnight pairs on weekend days, or a time zone comment saying UTC.

## Anti-Pattern 6: Setting the Case calendar after save

**What the LLM generates:** A scheduled Flow or after-save update that fills `BusinessHoursId` "once the region is known".

**Why it happens:** It looks harmless to backfill a lookup.

**Correct pattern:** The escalation engine and milestone timers compute targets when the Case is created; the calendar must be set before-save or the targets are computed on the default calendar.

**Detection hint:** `BusinessHoursId` assigned in any after-save or scheduled context for new Cases.

## Anti-Pattern 7: Passing `Case.BusinessHoursId` straight into Apex

**What the LLM generates:** `BusinessHours.diff(c.BusinessHoursId, start, end)` with no null handling.

**Why it happens:** The field looks required because escalation "always works".

**Correct pattern:** Resolve a null field to the default calendar Id before calling any `BusinessHours` method; a null Id is a runtime exception, not a fallback.

**Detection hint:** `BusinessHours.` call whose first argument is a record field with no null check.
