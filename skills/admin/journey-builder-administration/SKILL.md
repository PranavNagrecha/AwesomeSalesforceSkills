---
name: journey-builder-administration
description: "Use when setting up, configuring, or troubleshooting Marketing Cloud Journey Builder — including entry sources, activities, decision splits, wait activities, goals, exit criteria, journey versions, test mode, or journey analytics. Triggers: 'journey builder setup', 'entry source configuration', 'decision split not routing', 'exit criteria not removing contacts', 'goal not tracking conversion', 'journey version publishing', 'journey re-entry settings', 'wait activity date field'. NOT for Flow-based automation, Marketing Cloud Account Engagement (Pardot) engagement programs, or Salesforce core automation rules."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "contacts not entering journey or entry source not evaluating"
  - "how do I set up decision splits and wait times in Journey Builder"
  - "exit criteria not removing contacts from journey on schedule"
  - "goal conversion not tracking or goal path not exiting contacts early"
  - "journey version published but need to make changes to active journey"
  - "contacts entering journey multiple times when re-entry should be limited"
  - "test mode journey not behaving same as live journey"
tags:
  - journey-builder
  - marketing-cloud
  - entry-sources
  - decision-splits
  - journey-goals
  - exit-criteria
  - journey-versions
  - automation
inputs:
  - "Marketing Cloud Business Unit and Journey Builder access permissions for the admin user"
  - "Entry source type: Data Extension (scheduled), Salesforce Data (CRM object trigger), API Event, CloudPages Smart Capture, or Audience Builder"
  - "Desired journey activities: Email, SMS, Push, Ad Audience, Update Contact, Salesforce Activity, custom activity"
  - "Decision split logic: attribute-based, engagement-based (opens/clicks), random split, or Einstein STO"
  - "Goal definition: the conversion event the journey is measuring (e.g., purchased, opted in, attended event)"
  - "Exit criteria: data condition that should remove a contact from the journey mid-flight"
  - "Re-entry policy: whether contacts can re-enter and the minimum interval between re-entries"
outputs:
  - "Journey configuration guidance including entry source setup, activity chain, and split logic"
  - "Goal and exit criteria setup with scheduling behavior documented"
  - "Journey version strategy for managing updates to active journeys"
  - "Test mode execution plan using test contacts"
  - "Journey analytics interpretation: entry, goal conversion, and exit metrics by version"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

You are a Salesforce Marketing Cloud expert in Journey Builder administration. Your goal is to help practitioners design, configure, and troubleshoot multi-step customer journeys — from entry source configuration through activities, splits, goals, and exit criteria — without creating data quality problems, re-entry loops, or stale journey versions.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first. Only ask for information not covered there.

Gather if not available:

- Which Marketing Cloud Business Unit owns this journey? Journey Builder is scoped to a Business Unit; access and data extensions are BU-specific.
- What is the entry source type? Each type has different evaluation timing: Data Extensions use scheduled or triggered evaluation; Salesforce Data entries fire on CRM record changes; API Events inject contacts in real time; CloudPages Smart Capture fires on form submission.
- Should contacts be able to re-enter this journey, and if so, how frequently? By default a contact can only be in a given journey version once. Re-entry must be explicitly enabled with a configurable minimum interval (e.g., every 30 days).
- Is there a conversion event (goal) to track? Goals evaluate at each activity step and immediately exit contacts who meet the criteria via the goal path.
- Are there conditions that should remove a contact from the journey early regardless of where they are? Exit Criteria handle this — but they run on a schedule (every 15 minutes by default), not in real time.
- What activities are required? Know which channels are provisioned (Email Studio, MobileConnect for SMS, MobilePush for push notifications, Advertising Studio for ad audiences).
- Is this a new version of an existing journey or a net-new journey? Publishing a journey creates an immutable version; edits require creating a new version.

---

## Core Concepts

### Entry Sources and Evaluation Timing

Journey Builder supports five entry source types. Understanding their evaluation timing is critical because it determines how quickly contacts enter after a triggering event:

| Entry Source | Trigger Mechanism | Timing |
|---|---|---|
| Data Extension | Scheduled automation or continuous evaluation | Configurable schedule (hourly, daily, etc.) |
| Salesforce Data | CRM record creation or field change event | Near real-time after record save |
| API Event | REST API call with contact data payload | Real-time injection |
| CloudPages Smart Capture | Form submission on a Marketing Cloud CloudPage | Real-time on form submit |
| Audience Builder | Segment refresh | Batch, depends on segment refresh schedule |

Only one entry source can be configured per journey version. A contact evaluates entry criteria once per version unless re-entry is enabled. When a contact is already active in a journey version, duplicate entry attempts are silently dropped — there is no error surfaced.

### Re-Entry Policy

By default, a contact can be in a given journey version at most once. This is the most common source of confusion when contacts stop entering a journey after initial population. Re-entry is a journey-level setting that must be explicitly enabled. When enabled, a minimum re-entry interval is configured (e.g., the same contact cannot re-enter until 30 days have passed since their last entry). This interval is evaluated at entry time, not exit time.

Re-entry does not apply across journey versions — a contact who completed version 1 can enter version 2 immediately unless version 2 also restricts re-entry.

### Goals vs. Exit Criteria

Goals and Exit Criteria are both mechanisms for removing contacts from a journey early, but they work very differently:

**Goals** define a conversion event (e.g., "contact made a purchase" or "contact updated their preference"). Goal evaluation occurs at every activity step as a contact moves through the journey. When a contact meets the goal condition at any step, they immediately exit the journey via the goal path rather than continuing to subsequent activities. Goals are evaluated in near real-time as activities execute.

**Exit Criteria** define a data condition that should remove a contact from the journey regardless of which step they are currently on (e.g., "contact has unsubscribed" or "contact's status changed to Inactive"). Unlike goals, exit criteria run on a scheduled evaluation — by default every 15 minutes. Contacts are removed in the next evaluation window, not immediately when the data changes. This delay is a platform behavior that practitioners frequently misunderstand.

### Journey Versions and Immutability

Publishing a journey creates an immutable version. Once a journey version is active, its activity configuration, split logic, and entry source cannot be edited in place. To make changes, an administrator must create a new version from the journey canvas. Contacts currently active in the original version remain in that version and complete it under its original configuration. New contacts enter the latest active version.

This behavior means that corrections to a live journey (fixing a broken email activity, changing a split attribute) require creating a new version. The original version should be left running until all in-flight contacts have exited, then stopped to prevent new entries.

---

## Common Patterns

### Pattern: Onboarding Journey With Goal-Based Conversion Tracking

**When to use:** A new customer or subscriber needs to receive a structured onboarding sequence, but contacts who complete a conversion event (e.g., login, first purchase) should exit early rather than receive all remaining messages.

**How it works:**
1. Create a Data Extension with the subscriber population and import it or point a scheduled automation at it.
2. Create the journey with a Data Extension entry source, configuring the schedule to match the automation frequency.
3. Add Email activities for each onboarding message, separated by Wait activities with appropriate durations (e.g., Day 1 email, wait 3 days, Day 4 email, wait 4 days, Day 8 email).
4. Define a Goal using a data extension field that captures the conversion event (e.g., `ConversionDate IS NOT NULL` or `LoginCount >= 1`). Set goal evaluation to apply at every activity.
5. Connect the goal exit path to a final "Thank you" email or a Update Contact activity that writes a completion flag to the contact's data extension record.
6. Test using test contacts with goal field pre-populated to verify they exit via goal path before the Day 4 email.

**Why not run all contacts through all steps:** Sending all onboarding steps to contacts who already converted creates a degraded experience and inflates send volume. Goal-based exit routes converted contacts off the journey immediately and frees their slot for other journeys.

### Pattern: Winback Journey With Attribute Decision Split

**When to use:** A set of lapsed customers should receive tailored re-engagement messaging based on their customer tier, purchase history, or engagement recency — different message sequences for different segments.

**How it works:**
1. Build a Data Extension or Audience Builder segment with lapsed contacts.
2. Create a journey with an Attribute Split as the first activity after entry.
3. Configure split arms for each customer segment (e.g., "High Value" where `LifetimeValue >= 500`, "Standard" where `LifetimeValue < 500`, and "Default" for unmatched contacts).
4. Build separate Email → Wait → Email activity chains for each split arm, with more aggressive re-engagement messaging for the High Value arm.
5. Set Exit Criteria to remove contacts who make a purchase (`PurchaseDate > JourneyEntryDate`) — remembering that this evaluates every 15 minutes, not immediately.
6. Configure re-entry with a 90-day interval so the journey can re-target contacts who lapse again.

**Why not use random splits for this:** Random splits distribute contacts uniformly with no regard to customer attributes. Attribute-based splits ensure each contact receives the message chain most relevant to their value tier, improving relevance and reducing unsubscribes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Real-time entry on a form submission | CloudPages Smart Capture or API Event entry source | Contacts inject in real time; Data Extension entry is batch and introduces delay |
| Entry based on a CRM record field change | Salesforce Data entry source | Fires near real-time when the specified Salesforce object field changes; no separate automation required |
| Contact should exit as soon as they unsubscribe | Exit Criteria — accept up to 15 min lag, or add an Update Contact activity in email paths that checks unsubscribe status | Exit Criteria are not real-time; if immediate removal is required, build unsubscribe handling into activity paths |
| Contacts stop entering after initial population | Check re-entry setting — likely disabled | Default allows each contact in a version only once; enable re-entry with interval if repeat participation is needed |
| Journey needs logic change without losing in-flight contacts | Create a new journey version | Versions are immutable; new version captures new entries; existing contacts finish in their version |
| Track whether a campaign drove conversion | Use Goal, not Exit Criteria | Goals evaluate at each step and produce goal conversion metrics in Journey Analytics; Exit Criteria do not contribute to conversion reporting |
| Different messaging for high vs. low value customers | Attribute Decision Split | Routes contacts based on data extension field values; more precise than random or engagement splits |
| Randomized A/B test of two email variants | Random Split | Distributes contacts evenly with no data dependency; correct tool for message testing |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Confirm Business Unit, licenses, and channel access** — Verify which Marketing Cloud Business Unit owns this journey and confirm that the required channel activities are provisioned (Email Studio, MobileConnect for SMS, MobilePush for push). Check that the admin user has Journey Builder access within the BU.

2. **Define and prepare the entry source** — Identify the entry source type and timing requirements. For Data Extension entries, ensure the source DE exists with correct schema and that any upstream automation feeding it is scheduled. For API Event entries, confirm the API event definition exists and the API payload matches the expected schema. Document the entry criteria so duplicate-entry behavior is understood before launch.

3. **Design the activity chain and split logic** — Map the journey flow on paper or in a design document before building: entry → split(s) → activities → wait activities → exit. Identify which activities belong to which split arm. Document the split attribute fields and the attribute values that define each arm. Ensure the data required for attribute splits exists on the contact at the time of entry — missing values will route contacts to the Default arm.

4. **Configure Goals and Exit Criteria** — Define the goal conversion event and confirm the data extension field used for evaluation is populated correctly. Set goal evaluation to "at each activity." Define exit criteria conditions and communicate to stakeholders that exits will occur within 15 minutes of the data condition being met — not instantly.

5. **Build and configure in Journey Builder canvas** — Create the journey, set the entry source and re-entry policy, add and configure all activities, configure all splits, attach the goal, and set exit criteria. Confirm all email activities reference valid email sends with correct from addresses and subject lines.

6. **Test with Test Mode** — Activate Test Mode and inject test contacts that cover each split path and the goal exit scenario. Verify: correct split arm routing, correct activity firing, goal exit behavior, and wait activity duration. Test Mode suppresses live message delivery so real contacts are not affected.

7. **Publish and monitor** — Deactivate Test Mode, publish the journey, and monitor Journey Analytics for the first 24–48 hours. Review entry counts, goal conversion rates, exit criteria counts, and drop-off rates per activity step. Confirm in-flight contact counts match expected population size.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Entry source type matches the required entry timing (real-time vs. scheduled)
- [ ] Re-entry policy is explicitly configured — not left at default unless single-entry behavior is intentional
- [ ] All Data Extension fields required for attribute splits are present on the source DE and populated
- [ ] Goal conversion event is defined and the goal data condition field is confirmed to be populated correctly
- [ ] Exit Criteria conditions are validated and stakeholders are informed of the 15-minute evaluation schedule
- [ ] All channel activities (Email, SMS, Push) reference valid message definitions with correct from addresses
- [ ] Test Mode has been run with test contacts covering all split arms and the goal exit path
- [ ] Journey Analytics dashboard is reviewed post-launch for entry, goal, and exit counts
- [ ] Journey version strategy is documented: what triggers a new version and how in-flight contacts will be handled

---

## Salesforce-Specific Gotchas

1. **Exit Criteria run on a schedule — not in real time** — Exit Criteria evaluate on a scheduled cycle (every 15 minutes by default). When a contact's data changes to meet an exit condition (e.g., unsubscribes, becomes inactive), they are not removed from the journey until the next evaluation window fires. Practitioners who expect immediate removal will see contacts receive messages after the exit-triggering event. Communicate this lag to stakeholders, and if immediacy matters, supplement exit criteria with conditional checks within activity paths.

2. **Default re-entry is off — duplicate attempts are silently dropped** — When re-entry is disabled (the default), a contact who has already been in a journey version is simply not entered again if they re-qualify for the entry source. There is no error, no notification, and no log entry in the contact's journey history that makes the skip obvious. This causes confusion when a campaign is refreshed or a new automation run includes contacts from the prior run. Always verify re-entry settings deliberately — do not rely on the default.

3. **Publishing a journey version is irreversible** — Once a journey version is published and contacts have entered, the activity configuration is locked. Even correcting a single broken email link or fixing a wrong split condition requires creating an entirely new version. In-flight contacts stay in the original version. For high-volume journeys this means running two versions in parallel for the overlap period, which complicates analytics. Build and test thoroughly in Test Mode before publishing.

4. **Attribute splits route to Default arm when data is missing** — If a contact enters a journey with an attribute decision split but the split attribute field is null or not present on the contact, the contact is routed to the Default split arm silently. There is no alert and no indicator in the activity metrics that the contact took the default path due to missing data rather than matching the default condition intentionally. Always validate that upstream data populates the split fields before launch.

5. **Goal exit does not trigger re-entry eligibility reset** — A contact who exits a journey via the goal path is treated the same as a contact who exited by completing all steps. If re-entry is disabled, that contact cannot re-enter the same journey version regardless of how they exited. If re-entry is enabled with an interval, the interval timer starts from their original entry date, not their goal exit date. Practitioners sometimes assume goal-exited contacts can re-enter immediately for a follow-up sequence; they cannot unless the re-entry interval has elapsed.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Journey configuration guidance | Entry source setup, activity chain design, split logic documentation |
| Goal and exit criteria setup | Conversion event definition, exit condition data requirements, evaluation timing |
| Journey version strategy | Rules for when to create a new version and how to manage in-flight contacts |
| Test Mode execution plan | Test contact scenarios covering each split arm and the goal exit path |
| Journey analytics interpretation | Entry, goal conversion, and exit metrics per version with diagnostic guidance |

---

## Related Skills

- **admin/salesforce-data-extensions** — Use when the Data Extension serving as a journey entry source has schema issues, missing fields, or incorrect sendable configuration. NOT for journey canvas configuration.
- **admin/marketing-cloud-automation-studio** — Use when the automation feeding contacts into a journey entry source Data Extension has scheduling or activity failures. NOT for journey activity design.
- **admin/email-studio-content-builder** — Use when the Email activity references a message with broken content, invalid personalization strings, or missing from-address configuration. NOT for journey routing logic.
