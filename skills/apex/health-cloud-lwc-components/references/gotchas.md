# Gotchas — Health Cloud LWC Components

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Patient Card Does Not Support Standard LWC Slot Injection

**What happens:** Custom LWC components placed inside the Patient Card component area via Lightning App Builder do not appear on the patient card. The Patient Card renders with only its configured fields; child components added via App Builder slots are ignored.

**When it occurs:** When developers attempt to extend the Patient Card by adding child components using standard Lightning App Builder slot composition, analogous to how standard Lightning record pages support nested components.

**How to avoid:** All Patient Card field additions must go through Health Cloud Setup > Patient Card Configuration. This is the only supported way to add data to the Patient Card component. If a component needs to appear alongside (not within) the patient card, add it as a separate Lightning component in a different page layout region.

---

## Gotcha 2: Industries Timeline and Legacy HC Timeline Require Different Configuration

**What happens:** A TimelineObjectDefinition metadata record is created to add a new object to the timeline. The developer verifies the deployment succeeded. The new entry does not appear on the timeline in the org.

**When it occurs:** When the patient page uses the legacy Health Cloud managed-package timeline component (not the Industries Timeline). TimelineObjectDefinition metadata only affects the Industries Timeline. Orgs on the legacy component must use the legacy HC timeline configuration mechanism, which is separate.

**How to avoid:** Before building timeline configuration, verify which timeline component is active: check the patient Lightning page in App Builder for the component name. If it is the Industries Timeline component (backed by TimelineObjectDefinition), proceed with metadata configuration. If it is the legacy HC package timeline, use the legacy configuration mechanism and plan migration to the Industries Timeline.

---

## Gotcha 3: Custom Account/Contact Fields Are Invisible to Clinical Components

**What happens:** A custom field is added to the Account object and populated with clinical data via trigger or Flow. The field displays correctly on the standard account/record page, but is never visible in the PatientCard, Timeline, or other Health Cloud clinical components.

**When it occurs:** When clinical data is stored in custom Account or Contact fields instead of in the appropriate Health Cloud clinical objects (HealthCondition, ClinicalEncounter, PatientMedication, etc.).

**How to avoid:** Store all clinical data on the appropriate Health Cloud clinical standard objects with Account lookups. Clinical UI components query these clinical objects, not Account fields. For patient card additions, the field source must be a clinical object with an Account lookup, not Account itself.

---

## Gotcha 4: Apex Debug Logs Containing Clinical Data Are PHI

**What happens:** An Apex controller debugging session produces logs containing HealthCondition, PatientMedication, or ClinicalEncounter field values. These logs are stored in the org's debug log facility and are visible to any user with "View All Data" permission, potentially exposing PHI to unauthorized users.

**When it occurs:** During development and testing of clinical LWC Apex controllers, when debug logging is enabled and clinical data queries return real patient records.

**How to avoid:** Never enable FINEST or FINER debug log levels in production orgs with real PHI. In sandboxes with anonymized data, set debug log retention to the minimum necessary period. Implement automated purge policies for debug logs in Health Cloud orgs. Add a note in the code review checklist to check for clinical data in debug log output.
