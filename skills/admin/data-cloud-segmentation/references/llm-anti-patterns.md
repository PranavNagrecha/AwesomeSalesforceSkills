# LLM Anti-Patterns — Data Cloud Segmentation

Common mistakes AI coding assistants make when generating or advising on Data Cloud Segmentation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Segment Refresh with Activation Delivery Frequency

**What the LLM generates:** Instructions that say "set the segment to Rapid Publish to deliver contacts to Marketing Cloud every 2 hours" without separately configuring the activation's own publish schedule.

**Why it happens:** LLMs model the segment and the activation as a single pipeline. The fact that segment refresh and activation publish are two independently configured schedules is a Data Cloud-specific nuance that does not appear in generic CDP documentation.

**Correct pattern:**

```
Step 1: Configure segment refresh schedule (e.g., Rapid Publish every 2 hours)
Step 2: Separately navigate to the Activation record
Step 3: Set the Activation's own publish schedule to the desired delivery frequency
Note: These are two separate settings. Changing the segment schedule does NOT
      change the activation delivery schedule.
```

**Detection hint:** Any instruction that says "set segment refresh to X to deliver data every X hours" without mentioning a separate activation schedule is this anti-pattern.

---

## Anti-Pattern 2: Recommending Rapid Publish for Segments with Long Date Lookbacks

**What the LLM generates:** A segment design using Rapid Publish refresh with a filter like `LastPurchaseDate >= LAST_N_DAYS:30` or `CreatedDate >= LAST_N_DAYS:90`, without flagging that Rapid Publish only evaluates the last 7 days of data.

**Why it happens:** LLMs associate "Rapid Publish" with "fresher data" and recommend it whenever the user asks for a timely audience. The 7-day evaluation window restriction is a platform-specific limit that LLMs rarely surface because it is not a universal CDP behavior.

**Correct pattern:**

```
Rapid Publish is appropriate ONLY when:
  1. The filter criteria reference data from within the last 7 days
  2. The org has fewer than 20 existing Rapid Publish segments
  3. The use case genuinely requires sub-4-hour refresh (e.g., cart abandonment)

For any filter referencing data older than 7 days, use Standard refresh.
```

**Detection hint:** Any recommendation to use Rapid Publish paired with a date filter of `LAST_N_DAYS` > 7 is this anti-pattern.

---

## Anti-Pattern 3: Omitting Null Identity Field Filter from Segment Criteria

**What the LLM generates:** Segment filter logic that correctly captures the business audience (e.g., high-value customers, recent purchasers) but does not include a condition to exclude contacts with null email or null phone.

**Why it happens:** LLMs generate the business logic the user describes and do not default-add data quality filters. In most CRM and marketing systems, null-email contacts are excluded by the downstream system. In Data Cloud, null-email contacts pass through activation unless explicitly filtered.

**Correct pattern:**

```
Every segment that will be activated MUST include:
  Email IS NOT NULL
  (or the appropriate required identifier for the activation target:
   Phone IS NOT NULL for SMS targets,
   IndividualId IS NOT NULL for CDP activation targets)

Add this as an explicit AND condition alongside the business logic filters.
```

**Detection hint:** Any generated segment filter that contains business conditions (spend thresholds, date filters, behavior flags) but no IS NOT NULL condition on the primary contact identifier is this anti-pattern.

---

## Anti-Pattern 4: Treating Data Cloud Segmentation as Marketing Cloud Segmentation

**What the LLM generates:** Instructions that reference Marketing Cloud Contact Builder, Filtered Lists, Journey Builder entry sources, or Subscriber Key as part of a "Data Cloud segment" workflow. Or instructions that say "create the segment in Data Cloud and it will automatically appear as a list in Marketing Cloud."

**Why it happens:** Training data mixes Data Cloud (Customer Data Platform) documentation with Marketing Cloud Engagement documentation. The two systems have separate segmentation models. Data Cloud segments must be explicitly activated to Marketing Cloud via an activation target — they do not automatically become MC lists.

**Correct pattern:**

```
Data Cloud segmentation:
  - Created in Data Cloud > Segments
  - Uses Unified Individual DMO as the base object
  - Published via Activation to Marketing Cloud Engagement as a Data Extension

Marketing Cloud segmentation:
  - Created in MC > Contact Builder or Audience Builder
  - Operates on MC Contacts/Subscribers
  - Has no access to Data Cloud unified profiles

These are separate systems. Data Cloud segments must be activated to MC,
not "synced" or "linked." The activation creates/updates a Data Extension in MC.
```

**Detection hint:** Any instruction that mentions "sync the segment to Marketing Cloud" or references Audience Builder or Contact Builder in the context of a Data Cloud segment is this anti-pattern.

---

## Anti-Pattern 5: Ignoring Org-Level Hard Limits When Designing Segment Strategy

**What the LLM generates:** A multi-segment design (e.g., one segment per campaign, per product line, per region) without flagging the 9,950 total segment limit, the 20 Rapid Publish limit, or the 100 activations-with-related-attributes limit.

**Why it happens:** LLMs optimize for the described use case and do not model cumulative org-level quota consumption. Limits are often noted in footnotes of official docs and are easy to miss in training data.

**Correct pattern:**

```
Before recommending a multi-segment architecture, state:
  - Org limit: 9,950 total segments (all types)
  - Rapid Publish limit: 20 per org
  - Activations with related attributes: 100 per org
  - Related attributes per activation: 20 max
  - Related attributes blocked for segments > 10M profiles

Recommend governance practices:
  - Use Waterfall segments to consolidate mutually exclusive tiers
  - Implement segment decommission criteria (e.g., archive after 90 days of no activation)
  - Track Rapid Publish quota centrally before creating new high-frequency segments
```

**Detection hint:** Any segment architecture recommendation that creates more than 10 segments without mentioning org-level limits is likely missing this check.

---

## Anti-Pattern 6: Recommending Related Attributes for Large Segment Populations

**What the LLM generates:** An activation design for a broad segment (e.g., "all customers") that includes related attributes like loyalty tier, lifetime value, or product preferences — without checking whether the segment population exceeds 10 million profiles.

**Why it happens:** LLMs model the activation field mapping in isolation from segment population size. The 10M population threshold blocking related attributes is a platform enforcement that is not visible until activation save fails.

**Correct pattern:**

```
For segments expected to exceed 10 million Unified Profiles:
  - Do not configure related attributes on the activation
  - Use only core identity fields in the activation mapping
  - If related attributes are required, apply tighter filter criteria
    to reduce population below 10M, or split the segment into
    sub-segments (e.g., by region or product category)
```

**Detection hint:** Any activation design that includes related attributes for a segment described as "all customers," "entire database," or any population implied to be very large is this anti-pattern.
