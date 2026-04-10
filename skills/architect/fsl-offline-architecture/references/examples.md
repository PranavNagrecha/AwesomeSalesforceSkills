# Examples — FSL Offline Architecture

## Example 1: Priming Volume Calculation and Limit Breach

**Context:** An energy company deploys FSL Mobile to 400 field technicians. Each technician has an average of 15 Work Orders per day, each with 12 Work Order Line Items, and each WOLI is related to an Asset with 4 child objects (maintenance history, documents, etc.). The architect needs to validate that priming stays within the 1,000 page reference limit.

**Problem:** Initial calculation: 15 WOs × 12 WOLIs × 4 child objects = 720 page references per WO hierarchy path — appears safe. But the actual count is 15 WOs × (1 WO page + 12 WOLI pages + 12 × 4 child pages) = 15 × 61 = 915 page references. With any additional related object (one more child on a WOLI), the count exceeds 1,000 and some records will silently not be primed.

**Solution:**
1. Map the full priming hierarchy with page counts per level
2. Calculate total page references at the average and maximum volumes
3. Reduce depth: remove non-essential child objects from the priming configuration (e.g., documents not needed in the field) to bring count to ~600
4. Test with production-representative data in sandbox and verify all expected records are available offline
5. Document the priming depth decisions and their rationale

**Why it works:** Explicit page reference calculation before go-live prevents silent priming gaps that only manifest in field conditions.

---

## Example 2: Conflict Resolution Strategy Selection for Dispatcher + Technician Concurrent Edits

**Context:** A telecom field service team has dispatchers in a call center who frequently update appointment windows while technicians are on-site working. Dispatchers may extend appointment windows or add notes while technicians are updating work progress — creating concurrent edits on the same ServiceAppointment.

**Problem:** With the default `MERGE_ACCEPT_YOURS` strategy, technician sync overwrites the dispatcher's window extension with the technician's pre-sync version. Dispatchers discover their updates are lost 1–2 hours after making them, causing appointment chaos.

**Solution:**
1. Switch to `MERGE_FAIL_IF_CONFLICT` for ServiceAppointment objects
2. Build a conflict resolution UI in FSL Mobile that shows both versions when a conflict occurs
3. Train technicians: when a conflict alert appears, they see the dispatcher's version and their version and choose or merge
4. Alternatively, restrict dispatcher edits to fields that technicians never update offline (e.g., InternalNotes) to reduce conflict frequency

**Why it works:** `MERGE_FAIL_IF_CONFLICT` surfaces the conflict to the technician rather than silently discarding one version. This preserves both perspectives and allows human resolution.

---

## Anti-Pattern: Expecting Validation Rules to Catch Errors During Offline Work

**What practitioners do:** Configure Validation Rules on WorkOrder or ServiceAppointment to enforce data completeness (e.g., "Parts used must be documented before Completed status"). They assume VRs will prevent technicians from marking work complete without filling in required fields while offline.

**What goes wrong:** Validation rules do NOT fire during offline work. They fire when the device syncs with the server. A technician can mark 10 appointments Complete offline without entering parts data. The VRs fire at sync time and fail, leaving the technician's work in an error state that requires manual intervention.

**Correct approach:** For offline-compatible data quality:
1. Implement required-field checks in the FSL Mobile app's custom screen flow (LWC or OmniScript) before allowing status transitions
2. Use completion checklists in the custom action layer rather than relying on server-side VRs
3. Treat sync-time VR failures as an exception handling pattern, not a primary validation mechanism
