# Examples — Large Data Volume Architecture

## Example 1: Custom object report timeouts with wide rows

**Context:** A B2B org stores five million rows on `Telemetry_Event__c` with eighty custom fields. Operational dashboards filter on `Event_Type__c` (picklist) and `Occurred_On__c` (date) but still time out.

**Problem:** The object is both wide and high-volume. Filters on the picklist alone may not be selective enough at five million rows; reporting also pays join cost between standard and custom field storage.

**Solution:**

1. Run aggregate SOQL to count rows per `Event_Type__c` and per day bucket for `Occurred_On__c`.
2. If combined filters still exceed custom index thresholds, request a **two-column custom index** on `Event_Type__c, Occurred_On__c` for the dashboard pattern.
3. If read paths need many scalar columns and filters are selective, open a **skinny table** discussion with Support using only supported field types (no formulas in the skinny column list).

**Why it works:** The LDV guide positions two-column indexes for exactly this list-and-sort pattern, and skinny tables remove join overhead once filters are under control.

---

## Example 2: Integration user owns four million rows

**Context:** A single `005` integration user owns all `Invoice__c` rows for downstream sync. Sharing rule recalculation spikes nightly.

**Problem:** Ownership skew concentrates sharing work on one user bucket, which the LDV guide calls out as a performance risk.

**Solution:**

- Introduce queue-owned or partitioned logical owners (region, brand, source system) so no identity holds more than the low tens of thousands of rows per object where possible.
- Narrow integration queries with selective filters instead of scanning the integration user’s visible set.
- For one-time replatforming, follow bulk-load sequencing: roles and users first, owners on records, then groups and rules, using **defer sharing calculation** only when administrators explicitly use that permissioned workflow.

**Why it works:** Redistributing ownership reduces recomputation fan-out; sequencing avoids repeated full sharing passes during loads.

---

## Anti-Pattern: Requesting a skinny table for formula-driven dashboards

**What practitioners do:** Ask Support for a skinny table that includes roll-up summary fields, rich text, or formulas used on dashboards.

**What goes wrong:** Skinny tables only include the scalar field types enumerated in the Large Data Volumes guide. Unsupported types cannot be placed in the skinny projection, so the case stalls or the dashboard still hits the main table for those columns.

**Correct approach:** Materialize only supported columns into the skinny request, or precompute needed values into indexed static fields via asynchronous processing, then report off those columns.
