# Gotchas — Journey Builder Administration

Non-obvious Salesforce Marketing Cloud platform behaviors that cause real production problems in this domain.

## Gotcha 1: Exit Criteria Are Not Real-Time — They Run on a 15-Minute Schedule

**What happens:** When a contact's data changes to meet an exit condition (e.g., they unsubscribe, their status changes to Inactive, or they make a purchase), they are not immediately removed from the journey. The exit criteria evaluator runs on a scheduled cycle — every 15 minutes by default. Until the next evaluation window fires, the contact remains active in the journey and may receive messages or be processed by non-email activities.

**When it occurs:** Any time a practitioner expects instant removal triggered by a data change. Common scenarios: unsubscribe compliance, purchase conversion (want to stop promotional messaging immediately), status-change cleanup (contact marked as Deceased or Suppressed in CRM).

**How to avoid:** Document the 15-minute evaluation lag for stakeholders upfront. For compliance-sensitive scenarios (unsubscribe, GDPR opt-out), do not rely on Exit Criteria as the primary protection — Marketing Cloud's native All Subscribers unsubscribe suppression fires at send time and is independent of journey state. For conversion-based exits where the 15-minute delay is acceptable, pair Exit Criteria with a Goal so that goal conversion metrics are captured correctly even when Exit Criteria fires before or after the goal evaluation.

---

## Gotcha 2: Re-Entry Is Disabled by Default — Duplicate Attempts Are Silently Dropped

**What happens:** By default, a contact can be in a given journey version at most once. If a contact who has already entered (and completed or is currently active in) a journey version re-qualifies for the entry source, the re-entry attempt is silently ignored. There is no error, no notification to the admin, no entry in the journey's contact history that explains the skip, and no alert in Journey Analytics. The contact simply does not enter.

**When it occurs:** Most commonly after a scheduled automation refreshes the entry Data Extension with a population that includes contacts from prior runs. It also occurs when a Salesforce Data entry source fires again for a contact whose record field changes back and forth (e.g., Status goes to Active → Inactive → Active).

**How to avoid:** Explicitly configure re-entry settings when creating or publishing a journey — do not accept the default without deliberate decision. If re-entry is intended (e.g., a quarterly winback campaign, a recurring nurture series), enable re-entry and set the minimum interval to match the campaign cadence. After initial launch, check Journey Analytics entry counts against expected population size to catch silent non-entries early.

---

## Gotcha 3: Attribute Split Routes to Default Arm When Field Is Null

**What happens:** When a contact enters a journey with an attribute decision split and the split attribute field is null (or the field does not exist on the contact record in the entry Data Extension), the contact is routed to the Default split arm. This routing happens silently — there is no alert in the journey canvas, no flag on the contact's journey record, and the activity metrics show only that the contact took the Default path, not why.

**When it occurs:** When the Data Extension used for journey entry does not include the attribute field used in the split, or when the upstream automation that populates the field has a lag (e.g., the contact enters the journey before the nightly CRM sync populates their CustomerTier field).

**How to avoid:** Before activating a journey with attribute splits, run a query against the entry Data Extension to confirm that the split attribute fields are populated for all contacts in the entry population. If there is a data lag (e.g., nightly sync), schedule the journey entry evaluation to fire after the sync completes. Add a pre-journey data validation automation step that flags records with missing split attribute values for data quality review.

---

## Gotcha 4: Publishing a Journey Version Is Irreversible — New Version Required for Any Edit

**What happens:** Once a journey is published and contacts have entered, its configuration is locked. Editing the email activity, changing a split condition, adjusting a wait duration, or fixing a broken API event definition requires creating a new journey version. The original version continues running for all contacts currently in it — they complete the original configuration regardless of what was changed in the new version.

**When it occurs:** When a data error, a broken email link, or a misconfigured split is discovered after launch. Even minor corrections (fixing a typo in a split attribute value, changing a wait from 3 days to 4 days) require a new version.

**How to avoid:** Test exhaustively in Test Mode before publishing. Test Mode allows running the full journey with test contacts — including split routing, goal exit, and wait activity simulation — without sending live messages. Document a pre-publish checklist that includes: email content review, split attribute validation, goal data condition test, and exit criteria data condition test. Accept that some in-flight contacts will complete on an older version and account for this in analytics by filtering Journey Analytics by version.

---

## Gotcha 5: Goal Exit and Exit Criteria Both Remove Contacts but Only Goal Contributes to Conversion Metrics

**What happens:** Exit Criteria and Goals can both remove a contact from a journey, but they contribute to different metrics. Contacts removed by Exit Criteria appear in the Exit Criteria exit count in Journey Analytics. Contacts removed by Goal evaluation appear in the Goal conversion count. If a practitioner configures Exit Criteria to handle conversions (e.g., `PurchaseDate IS NOT NULL`) instead of or in addition to a Goal, the conversion metric in Journey Analytics underreports the true conversion rate — because Exit Criteria exits are not counted as goal conversions.

**When it occurs:** When practitioners use Exit Criteria as a removal mechanism for a conversion event, reasoning that exit criteria removes contacts from the journey on conversion. Technically it does, but the analytics classification differs.

**How to avoid:** Always configure a Goal for conversion events that the business needs to measure. Configure Exit Criteria as a backup removal mechanism if real-time-ish removal is also needed. The two mechanisms are complementary: Goal captures the conversion metric correctly; Exit Criteria ensures removal occurs even if the contact has not yet reached an activity step where Goal would evaluate.

---

## Gotcha 6: Test Mode Differences From Live Mode

**What happens:** Test Mode suppresses live message delivery and routes sends to the configured test address — but it does not fully replicate all live journey behaviors. Specifically: wait activity durations are not scaled in Test Mode (a 7-day wait behaves as a 7-day wait unless the admin manually advances the test contact through steps). API Event entry in Test Mode requires the API call to include the `testMode` parameter. Einstein STO splits in Test Mode route contacts using static logic rather than the live model, so Einstein-based routing cannot be validated accurately in Test Mode.

**When it occurs:** Practitioners assume Test Mode is a complete end-to-end simulation and publish journeys without validating wait durations, API event payload handling, or Einstein split routing against live data.

**How to avoid:** Treat Test Mode as a message suppression and basic flow validation tool, not a full simulation. For journeys with Einstein STO splits, validate split routing behavior in a sandbox Business Unit with live-mode contacts using a small controlled population before full launch. For journeys with long wait activities, manually advance test contacts step-by-step rather than waiting for the full duration. Document which aspects of the journey were validated in Test Mode and which require live-mode verification.
