# Examples — Data Cloud Segmentation

## Example 1: High-Value Customer Segment for CRM Campaign Activation

**Context:** A retail org wants to create a daily-refreshed audience of customers with lifetime spend over $500 and a purchase in the last 90 days, then push that list to a Salesforce CRM campaign for Sales Cloud reps to action.

**Problem:** Without Data Cloud segmentation, the CRM team relies on a manual report export to CSV and re-import — a process that is stale, error-prone, and cannot apply identity resolution across channels. Attempts to use a standard CRM report as a campaign member source do not deduplicate contacts who appear in multiple data streams.

**Solution:**

```
Segment definition (Data Cloud UI):
  Name: High-Value Active Customers
  Type: Standard
  DMO: Unified Individual

  Filter logic:
    LifetimeValue__c >= 500
    AND LastPurchaseDate__c >= LAST_N_DAYS:90
    AND Email IS NOT NULL

  Refresh schedule: Standard (every 12 hours)

Activation:
  Target: Salesforce CRM (Contact)
  Field mappings:
    Unified Individual: Email       → Contact: Email
    Unified Individual: FirstName   → Contact: FirstName
    Unified Individual: LastName    → Contact: LastName
  Related attributes (up to 20):
    LifetimeValue__c  → Contact custom field: DC_LifetimeValue__c
    LastPurchaseDate__c → Contact custom field: DC_LastPurchaseDate__c
  Activation publish schedule: Daily at 06:00 UTC
```

**Why it works:** The Standard segment type evaluates the full data history (no 7-day cutoff), so `LAST_N_DAYS:90` works correctly. The explicit `Email IS NOT NULL` filter prevents null-email contacts from being pushed to CRM where they would create orphaned records. The activation publish schedule (06:00 UTC daily) is set independently — the segment refreshes every 12 hours, but only the daily activation schedule determines when records land in CRM.

---

## Example 2: Cart Abandonment Rapid Publish Segment for Personalization

**Context:** An e-commerce org needs a segment of contacts who abandoned a cart in the last 48 hours to feed into a real-time personalization engine. The segment must refresh within a few hours of the abandon event to be useful.

**Problem:** A Standard segment refreshes every 12–24 hours, which is too slow for cart abandonment recovery. Without explicitly verifying the org's Rapid Publish quota, adding a new Rapid Publish segment may silently fail or push the org over the 20-segment limit.

**Solution:**

```
Pre-flight check (before creating segment):
  1. In Data Cloud Setup > Segments, filter by Refresh Type = Rapid Publish
  2. Confirm count is fewer than 20
  3. Confirm cart event data stream has a LastUpdatedDate within the last 7 days
     (Rapid Publish only evaluates data from the last 7 days)

Segment definition:
  Name: Cart Abandoners Last 48h
  Type: Standard
  DMO: Unified Individual (joined to CartEvent DMO)

  Filter logic:
    CartStatus__c = 'Abandoned'
    AND CartAbandonedDate__c >= LAST_N_DAYS:2
    AND Email IS NOT NULL

  Refresh schedule: Rapid Publish (every 2 hours)

Activation:
  Target: Marketing Cloud Engagement
  Publish schedule: Every 2 hours (matching segment refresh)
  Field mappings:
    Email, FirstName, LastName, CartValue__c
```

**Why it works:** The filter uses `LAST_N_DAYS:2`, which falls well within Rapid Publish's 7-day evaluation window. The org quota was verified before creation. The activation publish schedule is set to 2 hours to match the segment refresh — if the activation were left at the default daily schedule, the rapid segment refresh would provide no benefit.

---

## Anti-Pattern: Assuming Segment Refresh Frequency Drives Activation Delivery

**What practitioners do:** A practitioner creates a Rapid Publish segment and assumes contacts will automatically appear in the downstream Marketing Cloud activation within 1–4 hours, without separately configuring the activation's publish schedule.

**What goes wrong:** The segment refreshes every 2 hours as expected, but the activation was created with the default daily publish schedule. Contacts do not appear in Marketing Cloud until 24 hours later. The practitioner opens a support ticket believing Rapid Publish is broken.

**Correct approach:** After creating the segment with Rapid Publish, navigate to the activation record and explicitly set the activation's publish schedule to match the desired delivery frequency. Segment refresh schedule and activation publish schedule are two separate configurations in the Data Cloud UI — changing one does not change the other.

---

## Anti-Pattern: Using Rapid Publish for a 30-Day Engagement Segment

**What practitioners do:** A practitioner wants a segment of "active customers in the last 30 days" and selects Rapid Publish for freshness, expecting the segment to reflect all contacts who engaged within 30 days.

**What goes wrong:** Rapid Publish only evaluates the last 7 days of data. The segment silently under-counts members by excluding anyone whose most recent engagement was 8–30 days ago. The population appears much smaller than expected with no error message.

**Correct approach:** Use Standard refresh for any segment whose filter criteria reference data older than 7 days. Reserve Rapid Publish for use cases where the lookback window is 7 days or less (e.g., last-48-hours behavior, real-time cart activity).
