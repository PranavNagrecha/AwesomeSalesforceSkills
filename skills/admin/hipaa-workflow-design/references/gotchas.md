# Gotchas: HIPAA Workflow Design

Non-obvious platform behaviors that break HIPAA audit and access designs in Health Cloud. Sources are listed in `well-architected.md`. Line references cite the `pdftotext -layout` extraction of the Summer '26 Salesforce Security Guide (`salesforce_security_impl_guide`), Object Reference (`object_reference`), and Metadata API Developer Guide (`api_meta`). HIPAA regulation text and BAA terms did not fetch for this pass; claims that rest on them carry an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: Field history lasts 18 months without Field Audit Trail

**What happens:** "When Field Audit Trail is turned off, Salesforce retains field history data for up to 18 months, and up to 24 months via the API. If Field Audit Trail is turned on, Salesforce retains field history data until you delete it" (`salesforce_security_impl_guide L4631-4634`). With Field Audit Trail, history is copied to the `FieldHistoryArchive` big object; "by default, Salesforce archives data after 18 months in production, after one month in sandboxes, and stores all archived data until you delete it" (`L4880-4882`). Earlier versions of this skill said Field Audit Trail keeps history "up to 10 years"; the current guide says until deleted.

**When it occurs:** An audit asks for the change history of a PHI field from three years ago in an org that relies on standard field history.

**How to avoid:** Decide the retention period with counsel, use Field Audit Trail where it exceeds 18 months, and write a deletion procedure for archived data, because nothing is deleted automatically. UNVERIFIED (2026-10-03): the "6-year" HIPAA retention figure used by earlier versions of this skill is commonly attributed to 45 CFR 164.316(b)(2) (documentation retention); the regulation text did not fetch.

---

## Gotcha 2: Long text, multi-select, and formula fields cannot be history-tracked

**What happens:** The Security Guide lists fields that cannot be tracked: formula, roll-up summary, or auto-number fields; Created By and Last Modified By; Expected Revenue on opportunities; Master Solution Title and Details on solutions; long text fields; and multi-select fields (`salesforce_security_impl_guide L4885-4891`).

**When it occurs:** Clinical notes, assessment narratives, or symptom lists are stored in long text or multi-select fields, and the design assumes every PHI change is in field history.

**How to avoid:** Flag untrackable PHI fields in the inventory and choose alternative evidence for each: versioned child records, a custom audit object written by automation, or a different field type where the content allows it.

---

## Gotcha 3: Access logs expire on different clocks depending on the source

**What happens:** "All Shield and Event Monitoring customers have 1 year of Event Log File storage enabled by default" (`object_reference L112550`). Real-Time Event Monitoring "streaming events are retained for up to three days" (`salesforce_security_impl_guide L5449`). Event Log Objects (Hyperforce only) retain "log data ... for up to 30 days" (`L9837`). The LoginEvent comparison table gives 6 months for LoginEvent and LoginHistory and 30 days for the Login event type in Event Log Files (`L6341`). Earlier versions of this skill said all Event Monitoring logs expire after 30 days.

**When it occurs:** A multi-year access history is promised from platform storage alone, or a team builds on Event Log Objects expecting Event Log File retention.

**How to avoid:** Write the log retention target into the requirements and export Event Log Files to an external store before the one-year window ends. Treat the 30-day figure in the Login comparison table as a reason to export early, since the two statements in the guides differ. Monitor the export, because a failed export loses data once the window passes.

---

## Gotcha 4: Turning on Platform Encryption does not encrypt history already archived

**What happens:** "If you turn on Platform Encryption, the previously archived data remains unencrypted." Salesforce encrypts the live field, new history, and history still in the related list, "but phone number history data already archived in the FieldHistoryArchive object remains stored without encryption. To encrypt previously archived data, contact Salesforce to encrypt and rearchive the stored field history data, and then delete the unencrypted archive" (`salesforce_security_impl_guide L4899-4906`).

**When it occurs:** An org runs Field Audit Trail for a year, then enables Platform Encryption on PHI fields and assumes all copies are now encrypted.

**How to avoid:** Enable encryption on PHI fields before their history is archived, or schedule the re-encryption request and the deletion of the unencrypted archive as part of the encryption rollout.

---

## Gotcha 5: Deleting a record does not delete its archived history

**What happens:** "If you delete a record in your production data, the delete cascades to the related history tracking records, but Salesforce doesn't delete the history copied into the FieldHistoryArchive big object" (`salesforce_security_impl_guide L4895-4897`).

**When it occurs:** A patient record is deleted under a data request or retention rule, and PHI values remain in the archive.

**How to avoid:** Pair every record deletion process with a documented procedure for the archived history ("Delete Field History and Field Audit Trail Data" in the Security Guide), and decide with counsel which obligation (retention or deletion) wins for each data class.

---

## Gotcha 6: Tracked fields are capped at 20 per object without Field Audit Trail

**What happens:** "With Field Audit Trail, you can track up to 200 fields per object ... Without Field Audit Trail, you can track only up to 20 fields per object" (`salesforce_security_impl_guide L4836-4838`). An earlier example in this skill called 15 the standard maximum.

**When it occurs:** A patient or clinical object has more than 20 PHI fields that policy says must be audited.

**How to avoid:** Count trackable PHI fields per object during design. Above 20, either license Field Audit Trail or narrow the audited set with counsel's agreement.

---

## Gotcha 7: The PHI inventory belongs on the field definition

**What happens:** `CustomField.complianceGroup` (API 47.0) "indicates the compliance acts, definitions, or regulations related to the field's data", with values including `HIPAA`, and `securityClassification` (API 45.0) records sensitivity (`Public`, `Internal`, `Confidential`, `Restricted`, `MissionCritical`) (`api_meta L43334-43345`, `L43614-43622`).

**When it occurs:** The PHI inventory lives in a spreadsheet, new fields are added without updating it, and audit coverage silently shrinks.

**How to avoid:** Require `complianceGroup` HIPAA and a `securityClassification` on every PHI field in code review, so the inventory is the metadata itself (example in `metadata-examples.md`).

---

## Gotcha 8: Retention policy metadata has documentation conflicts

**What happens:** The HistoryRetentionPolicy entry says policies "are defined as part of a standard or custom object" and shows `historyRetentionPolicy` inside `CustomObject`, with `archiveAfterMonths` (1 to 18, default 18), `archiveRetentionYears` ("a reminder for manually deleting data"), and `gracePeriodDays`; it requires the `RetainFieldHistory` permission (`api_meta L44074-44125`). The CustomObject field table lists `historyRetentionPolicy` as "Reserved for future use" (`api_meta L42164`). The Security Guide adds that "Salesforce doesn't include the default retention policy when you retrieve the object's definition through Metadata API" (`salesforce_security_impl_guide L4882-4884`).

**When it occurs:** A team hand-writes a retention policy into an object file, or expects a retrieve to show the default policy, and the deploy or the review goes wrong.

**How to avoid:** Deploy the policy with a user who has `RetainFieldHistory`, test it in a sandbox first, and retrieve after deploy to confirm the custom policy is present. Remember that `archiveRetentionYears` deletes nothing.
