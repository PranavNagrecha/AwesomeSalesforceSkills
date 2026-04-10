# Gotchas — FSL Offline Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: 1,000 Page Reference Limit Causes Silent Priming Failure

**What happens:** When the priming engine traverses more than 1,000 related object references, it stops priming silently without raising an error. Records beyond the limit are simply absent from the device. Technicians discover missing data at job sites — not during testing.

**When it occurs:** Implementations with deep record hierarchies (many WOs per day × many WOLIs per WO × many child objects) or any org that adds new custom related objects to the priming hierarchy after go-live.

**How to avoid:** Calculate page references explicitly before go-live. Retest after any change that adds objects to the priming hierarchy.

---

## Gotcha 2: Ghost Records Persist Until cleanResyncGhosts() Is Explicitly Called

**What happens:** Records deleted on the server while a device was offline continue appearing on the device as live records until `cleanResyncGhosts()` is called via the FSL Mobile SDK. Technicians may navigate to cancelled appointments, attempt status transitions on deleted Work Orders, or prepare for jobs that no longer exist.

**When it occurs:** Any deployment where records (especially ServiceAppointments) are cancelled or deleted in the office while technicians are in the field.

**How to avoid:** Integrate `cleanResyncGhosts()` into the post-sync SDK workflow so it runs automatically after every sync. Do not rely on technicians manually triggering cleanup.

---

## Gotcha 3: Validation Rules Fire at Sync — Not During Offline Work

**What happens:** Apex triggers, validation rules, and workflow rules do NOT execute when records are created or updated offline. They execute when the device syncs with the server. Data that violates validation rules passes silently during offline work and produces sync errors that require manual intervention.

**When it occurs:** Any deployment that relies on VRs to enforce data quality in the mobile workflow.

**How to avoid:** Design offline data quality enforcement in the mobile app layer (custom LWC actions, OmniScript flows) rather than depending on server-side rules. Treat sync-time VR failures as an exception case, not the primary gate.

---

## Gotcha 4: MERGE_ACCEPT_YOURS Silently Overwrites Dispatcher Changes

**What happens:** With the default `MERGE_ACCEPT_YOURS` conflict resolution strategy, the technician's offline device version of a record overwrites the server version on sync. If a dispatcher updated an appointment window or added notes while the technician was offline, those changes are silently discarded when the technician syncs.

**When it occurs:** Any org where dispatchers and technicians both make changes to the same records — common for ServiceAppointment Status, Notes, and scheduling fields.

**How to avoid:** Evaluate conflict patterns during design. If dispatcher-technician concurrent edits on the same record are common, switch to `MERGE_FAIL_IF_CONFLICT` and build a conflict resolution UI.

---

## Gotcha 5: 50 Records Per Related List Is a Hard Priming Limit

**What happens:** Only the first 50 records of any related list are primed to the device. Work Orders with more than 50 line items, ServiceAppointments with more than 50 related records, or any object with deep related lists will have incomplete data on the device.

**When it occurs:** Any implementation with high-volume child records on primed objects — common in industries with complex multi-item work orders (construction, manufacturing).

**How to avoid:** Design Work Order structures to stay within the 50-record related list limit. If work regularly requires more than 50 line items, restructure as separate Work Orders for offline viability.
