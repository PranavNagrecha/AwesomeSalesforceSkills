# Data Cloud Segmentation — Work Template

Use this template when creating, modifying, or troubleshooting a Data Cloud segment and its activation.

---

## Scope

**Skill:** `data-cloud-segmentation`

**Request summary:** (fill in what the user or business asked for)

**Business goal:** (e.g., "daily list of high-value customers for CRM outreach" or "real-time cart abandonment segment for personalization")

---

## Prerequisites Verified

- [ ] Data Cloud is provisioned and at least one data stream is ingested
- [ ] Identity resolution has run and Unified Individual DMO is populated
- [ ] Activation target is configured in Data Cloud Setup (name: ______________)
- [ ] Org segment count checked: _______ / 9,950
- [ ] Rapid Publish segment count checked (if Rapid Publish planned): _______ / 20

---

## Segment Design

**Segment name:** _______________

**Segment type:**
- [ ] Standard
- [ ] Real-Time
- [ ] Waterfall
- [ ] Dynamic
- [ ] Data Kit

**Base DMO:** Unified Individual

**Filter criteria:**

```
(fill in filter conditions)
Example:
  LifetimeValue__c >= [value]
  AND LastPurchaseDate__c >= LAST_N_DAYS:[n]
  AND Email IS NOT NULL        ← REQUIRED: always include null exclusion
```

**Refresh schedule:**
- [ ] Standard (every 12–24 hours) — use for most cases and any date lookback > 7 days
- [ ] Rapid Publish (every 1–4 hours) — only if: lookback <= 7 days AND org count < 20
- [ ] Incremental — only if DMO has reliable change timestamps

**Justification for refresh choice:** _______________

**Expected population size:** _______________

---

## Activation Design

**Activation name:** _______________

**Activation target:** _______________

**Required identity field mapping:**

| Data Cloud Field | Target Field | Notes |
|---|---|---|
| Email | (target email field) | Required; filtered IS NOT NULL in segment |
| FirstName | | |
| LastName | | |

**Related attributes (max 20; not available if population > 10M):**

| Data Cloud Field | Target Field |
|---|---|
| | |
| | |

**Activation publish schedule:** _______________

Note: This is set independently from the segment refresh schedule.

---

## Checklist

- [ ] Segment filter includes `Email IS NOT NULL` (or required identity field IS NOT NULL)
- [ ] Segment type matches the use case
- [ ] Rapid Publish: confirmed org count < 20 before selecting
- [ ] Rapid Publish: all date filters reference data within last 7 days
- [ ] Activation publish schedule explicitly configured (not left at default)
- [ ] Related attribute count on activation is 20 or fewer
- [ ] Segment population is below 10M if related attributes are mapped
- [ ] Activation was manually published and first run confirmed with member count check
- [ ] Delivery to target system verified (records appear in expected location)

---

## Validation Results

**Segment population count (after first refresh):** _______________

**Activation delivery confirmed:** [ ] Yes / [ ] No

**Issues found:** (document any problems and how they were resolved)

---

## Notes

(Record any deviations from the standard pattern, business-specific constraints, or future follow-up items)
