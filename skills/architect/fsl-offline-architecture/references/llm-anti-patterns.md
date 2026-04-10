# LLM Anti-Patterns — FSL Offline Architecture

Common mistakes AI coding assistants make when generating or advising on FSL Offline Architecture.

## Anti-Pattern 1: Recommending Validation Rules for Offline Data Quality

**What the LLM generates:** "Add a validation rule on ServiceAppointment to require parts documentation before marking Complete."

**Why it happens:** Validation rules are the standard Salesforce quality gate. LLMs apply them without knowing they don't fire during offline FSL Mobile work.

**Correct pattern:** Validation rules fire at sync, not during offline work. Implement required-field checks in the FSL Mobile app layer (custom LWC actions, OmniScript screens) for real-time field enforcement. Keep VRs as a backstop at sync.

**Detection hint:** Any FSL Mobile offline design that relies solely on server-side validation rules for data quality is incomplete.

---

## Anti-Pattern 2: Not Noting the 1,000 Page Reference Limit

**What the LLM generates:** Instructions to add all relevant objects to the FSL priming hierarchy without any mention of the 1,000 page reference limit or a calculation.

**Why it happens:** LLMs don't model per-session data limits specific to FSL priming.

**Correct pattern:** Before finalizing the priming configuration, calculate total page references: WOs per technician × WOLIs per WO × related objects per level. Confirm total is under 1,000. Test with production-representative data volumes.

**Detection hint:** Any FSL offline priming design that doesn't include a page reference calculation is incomplete.

---

## Anti-Pattern 3: Assuming Ghost Record Cleanup Is Automatic

**What the LLM generates:** Offline design documentation that doesn't mention ghost records or implies deleted records disappear from devices automatically.

**Why it happens:** LLMs assume sync processes handle all data consistency automatically.

**Correct pattern:** Ghost records (server-deleted while device was offline) persist on device until `cleanResyncGhosts()` is explicitly called via the FSL Mobile SDK. Integrate this call into the post-sync workflow.

**Detection hint:** Any FSL Mobile offline design that doesn't mention ghost record cleanup is missing a required component.

---

## Anti-Pattern 4: Recommending MERGE_FAIL_IF_CONFLICT Without a Conflict Resolution UI

**What the LLM generates:** Instructions to switch to MERGE_FAIL_IF_CONFLICT without building a conflict resolution UI or training technicians on what to do when sync fails.

**Why it happens:** LLMs recommend the safer option (fail on conflict) without modeling the operational impact on technicians in the field.

**Correct pattern:** MERGE_FAIL_IF_CONFLICT requires a corresponding conflict resolution workflow — either a UI that shows both versions and allows the technician to choose, or a support process for dispatchers to resolve conflicts. Never recommend it without the resolution mechanism.

**Detection hint:** Any recommendation for MERGE_FAIL_IF_CONFLICT without a corresponding conflict resolution workflow is incomplete.

---

## Anti-Pattern 5: Not Testing Priming With Production-Representative Data

**What the LLM generates:** Go-live recommendations based on sandbox testing with minimal data (5–10 test records per technician).

**Why it happens:** LLMs don't model the data volume difference between sandbox testing and production.

**Correct pattern:** Test priming with a dataset that represents the maximum daily record volume for a single technician. Silent priming failures at the 1,000 page reference limit only manifest under production-scale data loads, not in minimal-data sandbox tests.

**Detection hint:** Any testing plan that doesn't specify priming tests at production-representative data volumes is incomplete for an FSL Mobile offline deployment.
