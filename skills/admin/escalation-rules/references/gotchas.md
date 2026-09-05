# Gotchas — Escalation Rules

Non-obvious Salesforce platform behaviors that cause real production problems.

Field names and enum values below come from the Metadata API Developer Guide `EscalationRules` section (`RuleEntry`, `EscalationAction`); `Case` and `BusinessHours` field behaviour comes from the Object Reference. Where a claim is widely repeated but not present in a fetchable official source, it is marked UNVERIFIED next to the claim rather than dropped.

## Gotcha 1: The Time-Based Engine Is Not Real-Time

**What happens:** An escalation set to fire after 4 hours does not fire at exactly the 4-hour mark. The time-based engine processes escalation actions in batches. A case that crosses the 4-hour threshold at 10:35 AM may not escalate until the engine's next pass.

UNVERIFIED (2026-09-04): the specific "approximately once per hour" cadence is not stated in the Metadata API guide, the Object Reference, or the App Limits cheat sheet, and help.salesforce.com cannot be fetched. The batched (non-immediate) behaviour is safe to design around; the interval itself should be measured in the target org before it is quoted to a customer.

**When it occurs:** Every time an escalation action fires. There is no way to guarantee sub-hour precision. This is inherent to the declarative time-based engine.

**How to avoid:** Do not commit to customers or SLAs that require minute-level escalation precision. If real-time enforcement is required, use Apex Schedulable with a short interval or Platform Events to build a near-real-time escalation path. Document this platform behavior in your SLA agreements with stakeholders.

---

## Gotcha 2: Only One Active Escalation Rule Per Org — Silently Deactivates Previous

**What happens:** When you activate a second escalation rule, Salesforce automatically deactivates the previously active rule without any warning or error message. All escalation entries and actions from the deactivated rule stop firing. Cases that were in flight against the old rule are no longer evaluated.

UNVERIFIED (2026-09-04): the Metadata API guide models `escalationRule` as a repeating element, gives each its own `active` boolean, and says rules are "processed in the order they appear in the EscalationRules container" — it neither states the one-active ceiling nor the silent-deactivation behaviour. The equivalent behaviour for assignment rules is documented in `admin/assignment-rules` `references/gotchas.md`. Check Setup > Escalation Rules in the target org before designing around a second active rule.

**When it occurs:** Whenever an admin clicks the "Active" checkbox on a new escalation rule and saves, or when deploying metadata with a second rule marked `<active>true</active>`.

**How to avoid:** Always audit Setup > Escalation Rules before creating a new rule. Check which rule is currently Active. If a rule exists, add entries to it rather than creating a parallel rule. If you must replace the rule, deploy the replacement with `<active>false</active>` first and flip the flag in its own deploy — the cutover table in `references/metadata-examples.md`. `scripts/check_escalation_rules.py` errors when a file contains two rules with `active` true.

---

## Gotcha 3: Default Business Hours Are 24/7 — "Use Business Hours" Without Configuration Has No Effect

**What happens:** Every org has a default business hours record that runs 24 hours a day, 7 days a week. If you set an entry's `businessHoursSource` to `Case` or `Static` without explicitly restricting the calendar it lands on, the clock still runs on weekends and overnight. Escalations fire at 3 AM Saturday as expected — because "business hours" technically include that time.

The Object Reference states the dependency plainly on the `BusinessHours` object: "Escalation rules are run only during these hours." That sentence is only useful once "these hours" are narrower than every hour.

**When it occurs:** When a team configures escalation entries with a business-hours source but never restricts the working window on the calendar those entries resolve to.

**How to avoid:** After choosing `Case` or `Static`, verify the calendar itself — days, times, and time zone — under `admin/business-hours-and-holidays`. The name "Default" does not mean Mon–Fri 9–5; it means 24/7 unless changed.

---

## Gotcha 4: Reopened Cases May Escalate Immediately

**What happens:** When a case is reopened, the escalation clock does not restart if `escalationStartTime` is `CaseCreation` — it is still measured from the original creation date. A case that was open for 6 hours, closed, and reopened two weeks later can fire escalation actions on the next engine pass when the threshold is 4 hours.

**When it occurs:** Any time cases are closed and reopened. Common in support orgs that close cases optimistically and reopen when customers reply.

**How to avoid:** If your support process regularly reopens cases and you want to give agents a fresh escalation window after reopening, set the entry's `escalationStartTime` to `CaseLastModified`. Be aware of the trade-off in Gotcha 6: that setting resets the clock on *every* update, not only a reopen.

---

## Gotcha 5: Entry Criteria Must Match Exact Field Values Used in Production

**What happens:** An escalation entry with criteria `Priority equals High` never fires because the org's picklist has values `High`, `Medium`, `Low` but cases are being created with `1-High`, `2-Medium`, `3-Low` from a legacy import. The criteria never match — cases are silently never evaluated.

**When it occurs:** After data migrations, picklist value changes, or when building rules in a sandbox that has slightly different picklist values than production.

**How to avoid:** Before finalizing rule entry criteria, inspect the actual field values in production using a report or SOQL: `SELECT Priority, COUNT(Id) FROM Case GROUP BY Priority`. Ensure the criteria values match exactly. The `value` element accepts a comma-separated list for a multi-value `equals`, so `Sev-1,High` in one criterion is one entry, not two.

---

## Gotcha 6: `CaseLastModified` Restarts the Clock on Any Edit — Including Automation

**What happens:** `escalationStartTime` set to `CaseLastModified` measures the age from the last modification of the record, not from the last *human* touch. A nightly integration that stamps a field, a record-triggered Flow that recalculates a rollup, a Data Loader correction pass, or a sharing recalculation that writes to the record all move `LastModifiedDate` forward and push the escalation threshold out. In an org with chatty automation, an entry set this way can escalate a case never — the clock is reset faster than it runs.

**When it occurs:** Whenever `CaseLastModified` is chosen to "reset the clock when the agent responds" in an org where something other than the agent also writes to Case.

**How to avoid:** Before selecting `CaseLastModified`, inventory everything that updates Case: record-triggered Flows, Apex triggers, integrations, and scheduled jobs. If any of them touch the record on a cadence shorter than the SLA, keep `CaseCreation` and express "the agent responded" through the entry criteria or through `disableEscalationWhenModified` instead. Verify with `SELECT Id, CreatedDate, LastModifiedDate, LastModifiedById FROM Case WHERE IsClosed = false` — if `LastModifiedById` is an integration user on most rows, this setting will not do what the requirement says.

---

## Gotcha 7: `disableEscalationWhenModified` Is a Different Lever From `escalationStartTime`

**What happens:** These two `ruleEntry` fields are routinely confused because both react to an edit, and they do opposite things. `escalationStartTime` = `CaseLastModified` *restarts* the timer on modification — escalation still arrives, later. `disableEscalationWhenModified` = `true` *ends* escalation on modification — the guide's wording is "the escalation is disabled when the record is modified". Setting the first when the requirement was the second produces late escalations instead of none; setting the second when the requirement was the first silently stops escalating cases that agents merely glanced at.

**When it occurs:** On any tier whose requirement is phrased as "stop escalating once someone picks it up" or "reset the clock when the agent updates it" — two different sentences that map to two different fields.

**How to avoid:** Decide both fields explicitly on every entry and record the pair in `templates/escalation-rules-template.md`. "Any touch ends escalation" is `disableEscalationWhenModified` true. "Any touch buys another window" is `escalationStartTime` `CaseLastModified`. Setting both, as entry 3 in `references/metadata-examples.md` does, is a deliberate choice, not a default.

---

## Gotcha 8: `minutesToEscalation` Is Minutes, While Setup Shows Hours

**What happens:** The Setup UI expresses escalation ages in hours; the metadata field is an `int` of minutes. An admin transcribing a "4 hour" tier into XML as `<minutesToEscalation>4</minutesToEscalation>` deploys a rule that escalates four minutes after the clock starts, on every matching case. Nothing in the deploy warns — 4 is a perfectly valid positive integer. The guide's own sample definition uses `1440`, which is 24 hours, not 1440 hours.

**When it occurs:** Any time an SLA agreed in hours is hand-written into metadata, and any time a rule is round-tripped through a spreadsheet or a requirements document that speaks in hours.

**How to avoid:** Write the arithmetic as a comment next to every action (`<!-- 8 business hours = 480 minutes -->`), and keep the hours-to-minutes column in `templates/escalation-rules-template.md`. `scripts/check_escalation_rules.py` flags any `minutesToEscalation` that is missing, non-numeric, or not a positive integer, and reports the value in hours so a transcription error is visible in the lint output.

---

## Gotcha 9: A Reassigning Action Writes `OwnerId` and Re-Fires Record Automation

**What happens:** An `escalationAction` with `assignedTo` changes the case owner. That is a record update hours or days after creation, and it re-fires every record-triggered Flow, Apex trigger, workflow-era automation, and Omni-Channel interaction that reacts to an ownership change or to a Case update at all. Automation written on the assumption that ownership only changes at intake — welcome emails, first-touch stamps, SLA start-time fields, round-robin counters — runs again on an escalated case.

**When it occurs:** On the first escalation stage that carries `assignedTo`, in any org whose Case automation keys off `OwnerId` or off `ISCHANGED(OwnerId)` without excluding escalation-driven updates.

**How to avoid:** Inventory everything that writes or watches `OwnerId` on Case before staging a reassign action — `admin/assignment-rules` `references/troubleshooting.md` step 5 ("Did something overwrite the owner afterwards?") lists escalation-rule reassignment among the mechanisms that change ownership after intake, and is the checklist to run in reverse here. Where an automation must not re-run, gate it on a field the escalation does not touch rather than on the owner change itself.

---

## Gotcha 10: Holidays Suspend the Escalation Rules Attached to a Calendar

**What happens:** The Object Reference states, on the `BusinessHours` object, that if business hours are associated with any Holiday records then "business hours and escalation rules associated with business hours are suspended during the dates and times specified as holidays." The suspension is a property of the calendar, not of the escalation rule, so it applies to every entry whose `businessHoursSource` resolves to that calendar — and it applies to nothing when the source is `None`. A holiday list that stops at the end of last year quietly changes SLA behaviour on the first public holiday of the new year, in the opposite direction to what everyone expects: escalations that used to pause now fire.

**When it occurs:** At each year boundary on non-recurring holidays, when a new region's calendar is created without its holiday set, and whenever a `None` entry is assumed to inherit the org's holiday behaviour.

**How to avoid:** Treat the holiday list as part of the escalation configuration's annual maintenance, owned by whoever owns the SLA — the calendar and holiday mechanics live in `admin/business-hours-and-holidays`. When reviewing an escalation rule, check the holidays on every calendar its entries resolve to, and note explicitly which entries are `None` and therefore observe no holidays at all.

---

## Gotcha 11: `IsEscalated` Is an Ordinary Writable Boolean, Not an Engine Lock

**What happens:** The Object Reference describes `Case.IsEscalated` as a boolean with `Create`, `Defaulted on create`, `Filter`, `Group`, `Sort` and `Update` properties, and says: "A case's escalated state does not affect how you can use a case, or whether you can query, delete, or update it. You can set this flag via the API." Two consequences follow. Anything with update access — a data load, a Flow, an integration user, an agent with the field on the layout — can set or clear it, so the flag is evidence of an escalation report, not proof of an escalation event. And because it does not restrict use of the record, clearing it does not "reset" anything in the engine.

**When it occurs:** During migrations that carry `IsEscalated` across from a legacy system, in orgs where the Escalated checkbox is editable on the page layout, and whenever an audit uses `IsEscalated = true` as a count of rule firings.

**How to avoid:** For monitoring, pair the flag with corroborating evidence: owner change history, the escalation email's activity record, or `LastModifiedDate` movement at the expected threshold. The queries in `references/metadata-examples.md` filter on `IsEscalated = true AND IsClosed = false` to find cases needing follow-up, which is a legitimate use; do not present the same count as "the rule fired N times". Remove the field from layouts where agents should not toggle it.

---

## Gotcha 12: Whether the Engine Skips Closed Cases Is Not Something to Assume

**What happens:** Two beliefs circulate, and they cannot both be right: that the engine automatically excludes closed cases, and that a closed case still escalates unless the entry criteria exclude it. This file's Gotcha 4 and `references/llm-anti-patterns.md` Anti-Pattern 5 have historically stated opposite positions.

UNVERIFIED (2026-09-04): the Metadata API guide's `RuleEntry` and `EscalationAction` tables describe no closed-case behaviour, and the Object Reference's `IsClosed` entry says nothing about escalation. Neither belief is grounded in a fetchable official source.

**When it occurs:** On any tier whose entry criteria do not mention `Status` or `IsClosed`, in an org where cases are closed before the longest threshold expires.

**How to avoid:** Do not rely on either belief. Put the exclusion in the entry criteria explicitly — `Case.Status notEqual Closed` as a `criteriaItems` entry, or `NOT(IsClosed)` inside a `formula`, as the entries in `references/metadata-examples.md` do. It costs one criterion, it is visible in review, and it makes the behaviour identical whichever belief is correct. Then prove it once in a sandbox: create a case, close it before the threshold, and check whether the escalation email arrives.
