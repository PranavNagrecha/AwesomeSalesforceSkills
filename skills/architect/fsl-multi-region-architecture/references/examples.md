# Examples — FSL Multi-Region Architecture

## Example 1: Timezone-Split Territory Redesign

**Context:** A national utility company's FSL deployment has territories aligned to state boundaries. One territory covers Missouri — a state that spans both the Central and the Eastern timezone (a tiny sliver of eastern Missouri is in the Eastern timezone). The `Book Appointment` action for customers in the Eastern sliver is showing Central time slots.

**Problem:** The territory's OperatingHours record is configured for the Central timezone. All slot times derived from those hours are in Central time. Customers in the Eastern timezone edge see appointments that are 1 hour early compared to their expectations.

**Solution:**
1. Split the Missouri territory into two: "Missouri-Central" and "Missouri-Eastern"
2. Create two OperatingHours records: one with TimeZone = "America/Chicago" (Central) and one with TimeZone = "America/New_York" (Eastern)
3. Assign the appropriate OperatingHours to each split territory
4. Re-import KML polygons for each split territory ensuring neither polygon crosses the timezone line
5. For resources who operate near the border: add Secondary ServiceTerritoryMember records in both territories

**Why it works:** Each territory now derives slot times from an OperatingHours record with the correct timezone for that geographic area. Customers in both timezones see slots in their local time.

---

## Example 2: Cross-Regional Specialist Pool with Serialized Optimization

**Context:** A telecommunications company has FSL territories organized as 4 regions (Northeast, Southeast, Midwest, West). A pool of 8 certified fiber splicers serves all regions — these specialists are assigned as Secondary members in all 4 regions.

**Problem:** The operations team schedules Global optimization for all 4 regions to run at 10pm simultaneously. The shared fiber splicers are assigned to conflicting appointments by multiple concurrent optimization jobs, with the last job to commit "winning" — resulting in a suboptimal schedule with some splicers double-booked.

**Solution:**
1. Stagger optimization runs: Northeast 10pm, Southeast 10:45pm, Midwest 11:30pm, West 12:15am
2. The fiber splicer pool is only available to one optimization job at a time in this schedule
3. Add a buffer between regional runs to ensure each job completes before the next starts
4. Monitor optimization job history each morning to confirm all 4 jobs completed successfully

**Why it works:** Sequential optimization ensures each territory's optimization engine has exclusive access to the shared specialist pool when it runs. No conflicting assignments are created.

---

## Anti-Pattern: Single Global Operating Hours Record for All Territories

**What practitioners do:** Create one OperatingHours record named "Business Hours" and assign it to all service territories across 4 US timezones. The OperatingHours record has TimeZone = "America/New_York".

**What goes wrong:** All territories in US Pacific, Mountain, and Central time zones show appointment slots in Eastern time. Customers in California see "9am-5pm" slots that are actually 6am-2pm Pacific. The Book Appointment action shows times that don't match local business hours.

**Correct approach:** Create one OperatingHours record per unique timezone in the deployment. Name them clearly (e.g., "Business Hours — Pacific", "Business Hours — Eastern"). Assign each territory the OperatingHours record for its specific timezone.
