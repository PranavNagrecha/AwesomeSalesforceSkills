# LLM Anti-Patterns — FSL Multi-Region Architecture

Common mistakes AI coding assistants make when generating or advising on FSL Multi-Region Architecture.

## Anti-Pattern 1: One OperatingHours Record for All Territories

**What the LLM generates:** Territory configuration with all territories referencing a single "Standard Business Hours" OperatingHours record.

**Why it happens:** LLMs default to the simplest configuration. In single-timezone orgs this works, but the pattern fails for multi-timezone deployments.

**Correct pattern:** Create one OperatingHours record per timezone in the deployment. Name them clearly by timezone. Assign each territory the record for its geographic timezone.

**Detection hint:** Any multi-timezone FSL deployment with only one OperatingHours record is incorrectly configured.

---

## Anti-Pattern 2: Not Noting Timezone-Boundary Constraint for Territory Polygons

**What the LLM generates:** Territory design that groups resources by operational region (state, sales territory) without checking whether the proposed territory polygons cross timezone lines.

**Why it happens:** LLMs optimize for operational organizational structure without knowing the FSL appointment booking constraint.

**Correct pattern:** Before finalizing territory design, map territory boundaries against IANA timezone boundaries. Split any territory that crosses a timezone line into two territories.

**Detection hint:** Any multi-region FSL territory design that doesn't address timezone alignment is incomplete.

---

## Anti-Pattern 3: Concurrent Optimization Without Checking Shared Resources

**What the LLM generates:** "Schedule all territory optimization jobs to run at 10pm simultaneously for efficiency."

**Why it happens:** Parallel execution is usually more efficient. The shared-resource conflict is specific to FSL's optimization architecture.

**Correct pattern:** Identify territories that share resources via Secondary ServiceTerritoryMember. These territories must be optimized sequentially with sufficient time gaps. Territories with no shared resources can run concurrently.

**Detection hint:** Any multi-territory optimization schedule that runs all territories simultaneously without confirming no shared resources exist is potentially problematic.

---

## Anti-Pattern 4: Configuring Secondary Assignments Without Soft Boundary in Scheduling Policy

**What the LLM generates:** Instructions to create Secondary ServiceTerritoryMember records for cross-territory resources, without checking or setting the scheduling policy boundary mode to Soft.

**Why it happens:** LLMs know Secondary assignments are the mechanism for cross-territory resource access but don't always model that the scheduling policy boundary mode overrides the assignment type.

**Correct pattern:** Secondary ServiceTerritoryMember + Soft Boundary in scheduling policy = cross-territory scheduling enabled. If the scheduling policy uses Hard Boundaries, Secondary assignments are ignored. Verify both pieces are configured.

**Detection hint:** Any cross-territory resource design that only creates Secondary STM records without verifying the scheduling policy boundary mode is incomplete.

---

## Anti-Pattern 5: Using UTC Offset Instead of IANA Timezone for OperatingHours

**What the LLM generates:** OperatingHours configured with TimeZone = "UTC-5" or "GMT-8" instead of IANA identifiers.

**Why it happens:** UTC offsets look correct and are simpler than IANA timezone names.

**Correct pattern:** Use IANA timezone identifiers (e.g., "America/New_York", "America/Los_Angeles"). These automatically handle Daylight Saving Time transitions. UTC offsets are static and don't adjust for DST, causing 1-hour appointment discrepancies during DST transitions.

**Detection hint:** Any OperatingHours configuration using UTC offsets instead of IANA timezone identifiers is incorrect for regions that observe DST.
