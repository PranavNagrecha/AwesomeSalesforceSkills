# LLM Anti-Patterns — FSL Reporting Data Model

Common mistakes AI coding assistants make when generating or advising on FSL Reporting Data Model.

## Anti-Pattern 1: Recommending ServiceReport as Operational Report Source

**What the LLM generates:** Advice to query or report on the `ServiceReport` object to get job completion data, technician performance, or appointment metrics.

**Why it happens:** "ServiceReport" sounds like an operational performance report. LLMs conflate the name with its purpose.

**Correct pattern:** `ServiceReport` is a customer-facing PDF/document object. Operational metrics come from `ServiceAppointment` (job duration, travel time, status) and `WorkOrder` (job-level aggregation, FTF rate).

**Detection hint:** Any suggestion to use `ServiceReport` for KPI reporting or performance dashboards is wrong.

---

## Anti-Pattern 2: Claiming a Native First-Time Fix Rate Field Exists

**What the LLM generates:** Instructions to "add the First_Time_Fix__c field" or "enable the FTF metric in Field Service Analytics settings" as if it's a built-in feature.

**Why it happens:** FTF is a standard field service KPI and LLMs assume it's natively provided.

**Correct pattern:** FSL has no native FTF field. Build it using a Record-Triggered Flow on ServiceAppointment: when Status = Completed, check for "Cannot Complete" predecessor SAs on the same WorkOrder, and stamp a custom checkbox on the WorkOrder.

**Detection hint:** Any statement that FSL provides a native first-time fix rate field or metric without custom development is incorrect.

---

## Anti-Pattern 3: Building Travel Time Reports Without Mobile Adoption Check

**What the LLM generates:** Travel time analytics setup instructions without any mention of the FSL Mobile check-in dependency for ActualTravelTime population.

**Why it happens:** LLMs don't model the data quality dependency between process adoption and field availability.

**Correct pattern:** Before building travel time reports, validate mobile adoption: `SELECT COUNT() FROM ServiceAppointment WHERE Status = 'Completed' AND ActualTravelTime = null`. Implement process controls requiring FSL Mobile check-in before relying on travel time data.

**Detection hint:** Travel time reporting recommendations that don't mention FSL Mobile check-in as a prerequisite are incomplete.

---

## Anti-Pattern 4: Conflating SchedStartTime with ActualStartTime

**What the LLM generates:** On-time arrival calculation using `SchedStartTime` compared to `ArrivalWindowStart`, ignoring that SchedStartTime is the FSL engine's planned time — not the actual arrival time.

**Why it happens:** "Scheduled start time" sounds like it means when work started, but in FSL it's the scheduling engine's assignment, not the technician's actual arrival.

**Correct pattern:** For on-time arrival: compare `ActualStartTime` (mobile check-in time) to `ArrivalWindowEnd` (customer commitment). For schedule adherence: compare `ActualStartTime` to `SchedStartTime`.

**Detection hint:** Any on-time arrival calculation using `SchedStartTime` as the "actual" arrival time is incorrect.

---

## Anti-Pattern 5: Ignoring FSI License Requirement for Field Service Analytics Dashboards

**What the LLM generates:** Instructions to enable Field Service Analytics or Field Service Intelligence dashboards in CRM Analytics without noting the separate license requirement.

**Why it happens:** LLMs know FSL has analytics capabilities but don't model separate licensing requirements.

**Correct pattern:** Field Service Intelligence (FSI) requires a CRM Analytics license in addition to FSL. If FSI is not licensed, use native Salesforce Reports with custom FTF fields and Flow-calculated metrics instead.

**Detection hint:** Any recommendation to use pre-built FSL Einstein/CRM Analytics dashboards without confirming the FSI license is available is premature.
