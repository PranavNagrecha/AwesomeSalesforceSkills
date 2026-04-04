# Data Archival Strategies — Archival Plan Template

Use this template to document an archival strategy for a Salesforce org. Fill in each section before beginning implementation.

---

## 1. Request Summary

**Requestor:** (name / team)

**Date:** (YYYY-MM-DD)

**Driver:** (storage alert / query performance / data retention policy / compliance requirement)

**Org Edition:** (Essentials / Professional / Enterprise / Unlimited / Developer)

---

## 2. Object Inventory

Identify the objects to be archived. Collect record counts from Setup > Storage Usage or SOQL aggregate queries.

| Object API Name | Current Record Count | Monthly Growth Rate (est.) | Retention Policy (years) | Notes |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

**Field History Objects (check separately):**

| History Object | Current Record Count | Tracked Fields | History Tracking Needed? |
|---|---|---|---|
| | | | |
| | | | |

---

## 3. Storage Type Analysis

| Storage Type | Current Usage (GB) | Org Limit (GB) | % Used | Projected Time to Limit |
|---|---|---|---|---|
| Data Storage | | | | |
| File Storage | | | | |

**Recycle Bin Status:**
- Current Recycle Bin record count: ___
- Estimated storage impact if emptied: ___ GB

---

## 4. Archival Approach Selection

For each object in the inventory, select one approach and document the rationale.

| Object | Approach | Rationale |
|---|---|---|
| | Big Object | |
| | External Storage (S3 / Heroku / Data Cloud) | |
| | Soft-Delete (IsArchived__c) | |
| | Hard Delete (no retention required) | |

**For Big Object approach — composite index design:**

| Object | Big Object Name | Index Field 1 | Index Field 2 | Index Field 3 | Query Pattern |
|---|---|---|---|---|---|
| | `__b` | | | | |

**For external storage approach:**

| Object | External System | Access Method | Retrieval SLA |
|---|---|---|---|
| | | | |

---

## 5. Archival Cutoff Criteria

Define what makes a record eligible for archival.

| Object | Cutoff Field | Cutoff Logic | Additional Criteria |
|---|---|---|---|
| | CreatedDate / CloseDate / Custom__c | older than N years/months | e.g., IsClosed = true |
| | | | |

---

## 6. Implementation Phases

| Phase | Activity | Owner | Target Date | Status |
|---|---|---|---|---|
| 1 | Empty Recycle Bin | | | |
| 2 | Disable Field History Tracking on low-value fields | | | |
| 3 | Deploy Big Object metadata (if applicable) | | | |
| 4 | Build and test Batch Apex archival job in sandbox | | | |
| 5 | Run archival job in production (first pass) | | | |
| 6 | Validate storage reclamation | | | |
| 7 | Schedule recurring archival job | | | |
| 8 | Update list views, reports, and queues (soft-delete pattern only) | | | |

---

## 7. Recycle Bin Management Plan

| Action | Frequency | Method | Owner |
|---|---|---|---|
| Empty Recycle Bin | Weekly / Monthly | Setup UI or `Database.emptyRecycleBin()` | |
| Monitor Recycle Bin volume | Monthly | Setup > Recycle Bin | |
| Hard delete after bulk archival jobs | Per-job | `Database.emptyRecycleBin()` in Apex batch | |

---

## 8. Storage Reclamation Estimate

| Object | Records to Archive | Avg Record Size (KB) | Estimated Storage Reclaimed (GB) |
|---|---|---|---|
| | | 2 | |
| | | 2 | |
| **Total** | | | |

**Post-archival projected storage usage:**

- Data Storage: ___ GB used / ___ GB limit = ___% (target: below 80%)
- File Storage: ___ GB used / ___ GB limit = ___%

---

## 9. Compliance and Audit Sign-Off

| Item | Decision | Approved By | Date |
|---|---|---|---|
| Retention policy confirmed with legal/compliance | Yes / No | | |
| Archive destination meets data residency requirements | Yes / No | | |
| Audit access to archived records validated | Yes / No | | |
| Field history retention requirements confirmed | Yes / No | | |

---

## 10. Notes and Deviations

(Document any deviations from the standard archival approach and the rationale.)
