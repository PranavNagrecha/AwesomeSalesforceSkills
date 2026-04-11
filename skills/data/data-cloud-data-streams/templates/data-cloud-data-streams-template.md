# Data Cloud Data Streams — Work Template

Use this template when configuring a new data stream in Data Cloud, from connector setup through activation.

## Scope

**Skill:** `data-cloud-data-streams`

**Request summary:** (fill in what the user asked for — e.g., "ingest loyalty platform customer records and unify with CRM contacts")

---

## 1. Source System Context

| Field | Value |
|---|---|
| Source system name | |
| Connector type | CRM Connector / Ingestion API / S3 / SFTP / MuleSoft / Partner Connector |
| Refresh mode | Real-time (Ingestion API) / Scheduled batch |
| Deletions required? | Yes / No — if Yes, note deletion mechanism: |
| Source object / endpoint | |

---

## 2. Identity Attribute Inventory

List all fields in the source that can serve as identity match attributes:

| Source field name | Identity attribute type | Notes |
|---|---|---|
| (e.g., email) | Contact Point Email | Normalized to lowercase before ingest? |
| (e.g., mobile_phone) | Contact Point Phone | E.164 format required? |
| (e.g., loyalty_id) | Party Identification | Identification Type label: |
| (e.g., contact_id) | Individual primary key | |

**Individual ID source field:** ___________
(This field maps to Individual DMO `Individual ID` — must be a stable, unique per-person key)

---

## 3. DLO-to-DMO Field Mapping Plan

### Individual DMO Mapping

| Source field | Target DMO field | Notes |
|---|---|---|
| | Individual ID (PK) | |
| | First Name | |
| | Last Name | |

### Contact Point DMO Mapping (required — choose at least one)

**Contact Point Email:**

| Source field | Target DMO field | Notes |
|---|---|---|
| | Email Address | |
| | Individual ID (FK) | Must match Individual DMO primary key |

**Contact Point Phone (if applicable):**

| Source field | Target DMO field | Notes |
|---|---|---|
| | Phone Number | Normalized to E.164? |
| | Individual ID (FK) | |

**Party Identification (for external IDs — if applicable):**

| Source field | Target DMO field | Notes |
|---|---|---|
| | Identification Number | NOT Party Identification ID |
| | Identification Type | Label value (e.g., "Loyalty ID") |
| | Individual ID (FK) | |

---

## 4. Identity Resolution Ruleset

**Ruleset name:** ___________

**Current org ruleset count before this work:** ___ / 2 (hard limit)

**Match rules:**

| Priority | Match attribute | DMO | Match type |
|---|---|---|---|
| 1 | (e.g., Email Address) | Contact Point Email | Exact |
| 2 | (e.g., Phone Number) | Contact Point Phone | Exact (optional) |

**Expected Unified Individual count after first run:** ___________

---

## 5. Calculated Insights (if required)

| Insight name | SQL summary | Schedule | Base object |
|---|---|---|---|
| (e.g., purchase_count_90d) | COUNT of purchase events in last 90 days | Daily | UnifiedIndividual__dlm |

Note: Calculated Insights are batch-processed. Do not use for real-time segmentation use cases.

---

## 6. Activation Configuration

| Field | Value |
|---|---|
| Activation target type | Marketing Cloud / Advertising Audience / Webhook |
| Activation target name | |
| Segment name | |
| Segment filter summary | |
| Fields included in activation | |
| Activation frequency | On publish / Scheduled |

---

## 7. Pre-Delivery Review Checklist

- [ ] Individual DMO mapping complete: Individual ID, First Name, Last Name mapped
- [ ] At least one Contact Point DMO or Party Identification DMO mapping present
- [ ] Identity resolution ruleset created and run; Unified Individual count is non-zero
- [ ] Calculated Insights reference UnifiedIndividual__dlm as the base object (if applicable)
- [ ] Activation target configured and segment population count confirmed
- [ ] Ingestion API delete requirements reviewed: delete flows use standard pipeline, not Ingestion API
- [ ] Org identity resolution ruleset count is at or below 2

---

## 8. Notes and Deviations

(Record any deviations from the standard pattern and why — e.g., "Contact Point Phone used instead of Email due to no email field in source system")
