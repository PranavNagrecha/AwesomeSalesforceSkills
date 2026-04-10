# Gotchas — FSL Multi-Region Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Territory Polygon Crossing Timezone Boundary Produces Incorrect Slot Times

**What happens:** The `Book Appointment` Global Action derives available time slots from the territory's OperatingHours timezone, not from the customer's address timezone. If the territory polygon extends into a different timezone, customers in the boundary area see slots in the wrong local time with no error.

**When it occurs:** Any FSL deployment where territory boundaries are drawn along political or operational lines (state boundaries, sales territories) that cross timezone lines.

**How to avoid:** Map timezone lines against territory boundaries before finalizing territory design. Split any territory that crosses a timezone line into two territories, one per timezone.

---

## Gotcha 2: Book Appointment Derives Timezone From Territory's OperatingHours — Not Customer Address

**What happens:** Even if a customer's address is in Pacific time, if the ServiceTerritory serving them has an Eastern timezone OperatingHours record, slots are shown in Eastern time. The system does not automatically adjust for the customer's local timezone.

**When it occurs:** Mismatched territory-to-timezone configuration.

**How to avoid:** Each ServiceTerritory must have an OperatingHours record with the timezone that matches the territory's geographic area. Verify: `SELECT Name, TimeZone FROM OperatingHours WHERE Id IN (SELECT OperatingHoursId FROM ServiceTerritory)`.

---

## Gotcha 3: Concurrent Optimization for Territories Sharing Resources Produces Conflicting Assignments

**What happens:** When two or more Global optimization jobs run simultaneously for territories that share resources via Secondary ServiceTerritoryMember, both jobs attempt to assign the shared resource to different appointments. The last job to write commits its version, overwriting the other job's assignment. Both schedules are suboptimal and one has incorrect assignments.

**When it occurs:** Multi-region deployments where optimization is scheduled to run simultaneously across all territories.

**How to avoid:** Identify all territories that share resources. Schedule their optimization jobs sequentially with a time gap between regions that exceeds the expected job duration.

---

## Gotcha 4: Hard Boundary Overrides Secondary Territory Assignments

**What happens:** A resource is configured with Secondary ServiceTerritoryMember records in 3 additional territories. However, the scheduling policy is set to Hard Boundaries for that resource type. The resource is never scheduled in secondary territories despite having the assignments, because Hard Boundary restricts scheduling to the Primary territory only.

**When it occurs:** Orgs that configure Secondary territory assignments but have Hard Boundary as the default policy for the resource or work type.

**How to avoid:** Check the scheduling policy's boundary settings when configuring cross-territory resources. Secondary assignments + Soft Boundary is the correct combination for cross-territory scheduling.

---

## Gotcha 5: International FSL Deployments With Daylight Saving Time Transitions

**What happens:** OperatingHours records use IANA timezone identifiers (e.g., "America/New_York") that respect Daylight Saving Time automatically. However, some countries don't observe DST, or observe it on different dates than the US. If a territory's timezone is configured as a fixed UTC offset instead of an IANA timezone, DST transitions in bordering territories can create 1-hour appointment window discrepancies.

**When it occurs:** International deployments or custom timezone configurations that use UTC offsets instead of IANA timezone identifiers.

**How to avoid:** Always configure OperatingHours with IANA timezone identifiers, not UTC offsets. Review Salesforce's supported timezone values in the OperatingHours TimeZone field picklist.
