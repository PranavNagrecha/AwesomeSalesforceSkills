# Examples — Patient Engagement Requirements

## Example 1: Scoping Patient Self-Scheduling License Dependencies

**Context:** A multi-specialty medical group is implementing Health Cloud and wants patients to self-schedule appointments online without calling the clinic. The project team assumes this is included in the base Health Cloud license.

**Problem:** The project budget and timeline were built assuming appointment scheduling is native to Health Cloud. The team discovers during implementation kickoff that Intelligent Appointment Management (IAM) is a separately licensed add-on and that no-show prediction (a key stakeholder requirement) requires CRM Analytics — also a separate license.

**Solution:**
1. At requirements phase, identify "patient self-scheduling" as an IAM feature and flag it as a separate license dependency.
2. Confirm whether no-show prediction is a must-have vs. nice-to-have requirement. If must-have: add CRM Analytics to the license scope and project budget.
3. Identify the scheduling data source: Salesforce Scheduler only, EHR scheduling only (Epic/Cerner), or hybrid aggregation. Each has different integration complexity.
4. Document the requirements and license dependencies in the patient engagement feature inventory before contract signing.
5. Confirm with the Salesforce account team that both IAM and (if needed) CRM Analytics are included in the final contract.

**Why it works:** Identifying license dependencies during requirements phase allows them to be addressed in the contract before go-live, rather than discovered as scope gaps during implementation.

---

## Example 2: Confirming OmniStudio Prerequisites for Health Assessment Delivery

**Context:** A behavioral health organization wants patients to complete PHQ-9 depression screening and SDOH social needs assessments via a patient portal before their appointments.

**Problem:** The implementation team builds the portal and begins assessment configuration, then discovers that no OmniStudio runtime is set up in the org, the Discovery Framework feature was never enabled, and coordinators lack the permission set licenses that make Assessment records visible.

**Solution:**
1. At project inception, record the OmniStudio runtime: Omnistudio for Managed Packages (an installed package) or the standard runtime.
2. Confirm the Discovery Framework feature is enabled. The Salesforce Industries Developer Guide describes it as an org feature, not a package, so it will not appear under Installed Packages.
3. Assign the Health Cloud and Health Cloud Platform permission set licenses and the Health Cloud Permission Set License permission set to every persona that works with assessments (Agentforce Health Developer Guide, Health Assessments).
4. After installation, configure assessment templates using Discovery Framework's pre-built library (PHQ-9, GAD-7, SDOHCC screening).
5. Build OmniScript-based assessment delivery flows for the patient portal.
6. Design the notification workflow to alert care coordinators when high-risk PHQ-9 scores (>=10) are submitted.

**Why it works:** OmniStudio, Discovery Framework, and the permission set licenses are prerequisites for assessment delivery, and none of them is active by default. Confirming each before configuration prevents blocked implementation work.

---

## Anti-Pattern: Assuming Health Cloud License Includes Patient Portal Access

**What practitioners do:** Assume that purchasing Health Cloud automatically provides a patient-facing portal with appointment scheduling, health assessments, and messaging — because all these features appear in Health Cloud product documentation.

**What goes wrong:** Health Cloud is a care coordinator/clinician product. Patient-facing portal functionality requires the Experience Cloud for Health Cloud add-on (separate SKU with per-user licensing). Implementations that begin portal development before confirming this license will hit a hard stop when attempting to configure Experience Cloud for Health Cloud components.

**Correct approach:** At project inception, explicitly confirm which patient engagement features are in scope and verify that each required license SKU is included in the contract: Experience Cloud for Health Cloud (portal), IAM (scheduling), CRM Analytics (no-show prediction), Messaging add-on (secure messaging). Never assume portal capability is included in the base Health Cloud license.

---

## Example 3: Prerequisite Checks and an Appointment Payload for the Requirements Pack

The complete artifacts (file paths, metadata XML or API payloads, and the `package.xml` member form) are in `references/metadata-examples.md`.

```text
Evidence the requirements pack must contain before build:
1. ApptReasonEngmtChannelType inventory (reasons x channels x work types)
2. AssessmentEnvelope status query result from the target org
3. Agreed Book Appointment payload for the portal
4. Retrieved IAM integration class and Named Credential (or a note that the default FHIR adapter is used)
```
