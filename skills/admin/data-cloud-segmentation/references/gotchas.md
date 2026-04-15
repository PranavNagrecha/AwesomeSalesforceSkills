# Gotchas — Data Cloud Segmentation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Rapid Publish 7-Day Lookback Silently Truncates Segment Population

**What happens:** When a segment uses Rapid Publish refresh, Data Cloud only evaluates events and attribute values from the **last 7 days** of ingested data, regardless of how the filter is written. A filter like `LastPurchaseDate >= LAST_N_DAYS:30` appears to save and run without error, but only contacts with a purchase in the last 7 days are included. Contacts with a purchase 8–30 days ago are silently excluded from the segment population.

**When it occurs:** Any time a Rapid Publish segment's filter criteria reference data older than 7 days. The mismatch is especially common when migrating a Standard segment to Rapid Publish without reviewing filter date ranges.

**How to avoid:** Before selecting Rapid Publish, audit every date-based filter condition in the segment. If any condition references data older than 7 days, use Standard refresh instead. If sub-4-hour freshness is genuinely required for a longer lookback window, there is no native workaround — Rapid Publish's 7-day restriction is a platform limit, not a configuration option.

---

## Gotcha 2: Segment Refresh and Activation Publish Are Independent Configurations

**What happens:** Increasing the segment refresh frequency (e.g., switching from Standard to Rapid Publish) does not change how often the activation delivers records to the downstream system. Activation has its own publish schedule that defaults to daily and must be updated separately. A practitioner who sets a 2-hour segment refresh but leaves the activation on the default daily schedule will see no improvement in data freshness at the destination.

**When it occurs:** Any time a practitioner configures Rapid Publish on a segment without also updating the activation's publish schedule. The UI does not warn about the mismatch.

**How to avoid:** After configuring a segment refresh schedule, immediately navigate to every associated activation and confirm the activation publish schedule matches the intended delivery SLA. Treat them as two separate configurations that must be set independently.

---

## Gotcha 3: Null Email Addresses Are Activated by Default

**What happens:** Data Cloud includes Unified Profiles with null email addresses in segment membership. When the segment is activated, contacts with no email are pushed to the activation target. In Marketing Cloud, this creates empty subscribers or delivery failures. In Salesforce CRM, it creates Contact records with no email, bypassing CRM duplicate rules that rely on email matching.

**When it occurs:** Any segment that does not include an explicit `Email IS NOT NULL` (or equivalent required identifier) filter. This is the default behavior — there is no org-level setting to exclude null-email contacts globally.

**How to avoid:** Add `Email IS NOT NULL` (or the required identity field for the activation target) as an explicit filter condition in every segment that will be activated. If the activation target requires a different identifier (e.g., phone for SMS), filter on that field instead.

---

## Gotcha 4: Org-Wide 9,950 Segment Limit Has No UI Warning

**What happens:** The maximum number of segments across all types in a Data Cloud org is 9,950. When an org reaches this limit, attempts to create new segments fail. The error message is generic and does not surface the segment count limit as the cause, making diagnosis difficult.

**When it occurs:** Large enterprise orgs with automated segment generation pipelines, Data Kit distributions, or many A/B test variants can approach this limit. There is no proactive warning in the UI as the org approaches 9,950.

**How to avoid:** For orgs managing many segments programmatically, track segment count via the Data Cloud API and alert when the count exceeds a threshold (e.g., 9,500). Archive or delete stale segments on a regular cadence. Do not rely on the platform to warn you when you are near the limit.

---

## Gotcha 5: Related Attributes Are Blocked for Segments Over 10 Million Profiles

**What happens:** When creating or editing an activation for a segment whose population exceeds 10 million Unified Profiles, the activation UI will not allow the user to add related attributes. The related attribute section is either hidden or disabled without a clear error message. This means the activation can only publish core identity fields, not additional profile attributes.

**When it occurs:** Activations configured against very large audience segments — common in B2C orgs with millions of ingested contacts.

**How to avoid:** If the use case requires related attributes (e.g., loyalty tier, lifetime value, product category), apply tighter filter criteria to reduce the segment population below 10 million before creating the activation. Alternatively, split into sub-segments by geography or product line, each with its own activation.

---

## Gotcha 6: Rapid Publish Org Quota Is Shared Across All Segments

**What happens:** The 20 Rapid Publish segment limit is an org-wide quota, not a per-user or per-business-unit quota. If 20 Rapid Publish segments already exist in the org, attempting to create a 21st will fail. There is no per-org setting to increase this limit — it is a platform enforcement.

**When it occurs:** When multiple teams within a single org independently create Rapid Publish segments without central visibility into the org-wide count.

**How to avoid:** Establish a central registry or governance process for Rapid Publish segments. Before creating a new Rapid Publish segment, query the existing count via the Data Cloud admin interface or API. Treat the 20-segment quota as a shared resource that requires org-level governance.
