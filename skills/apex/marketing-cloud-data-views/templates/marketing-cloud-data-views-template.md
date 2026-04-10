# Marketing Cloud Data Views — Work Template

Use this template when writing or reviewing a SQL Query Activity that accesses one or more Marketing Cloud system data views (_Sent, _Open, _Click, _Bounce, _Subscribers, _Job, _Complaint, _SMSLog, _UndeliveredSMS).

## Scope

**Skill:** `marketing-cloud-data-views`

**Request summary:** (describe the business question or reporting goal — e.g., "build a 90-day click segment for re-engagement campaign")

---

## Context Gathered

Answers to the Before Starting questions from SKILL.md:

- **Data view(s) to query:** (e.g., `_Click`, `_Sent`, `_Subscribers`)
- **Date range required:** (e.g., "last 90 days") — flag if > 6 months
- **Retention window check:** [ ] Confirmed date range is within ~6 months for engagement views
- **Target Data Extension:** (name and whether it already exists)
- **Target DE Primary Key field:** (field name used for deduplication)
- **Query Activity action:** [ ] Overwrite / [ ] Update — (choose one and justify)
- **Join keys available:** SubscriberKey: ___ / JobID: ___ / EmailAddress (do not use as join key)
- **Deduplication requirement:** [ ] Yes — use DISTINCT or GROUP BY / [ ] No deduplication needed

---

## Data View Schema Reference

Fill in the fields you will use from the relevant data view(s):

### _Sent (if used)
| Field | Type | Notes |
|---|---|---|
| SubscriberKey | Text | Subscriber identifier |
| EmailAddress | Email | Subscriber email |
| EventDate | Date | Date/time of send event |
| JobID | Number | Links to _Job for email metadata |
| ListID | Number | List the subscriber was sent from |
| BatchID | Number | Sub-batch within the job |

### _Open (if used)
| Field | Type | Notes |
|---|---|---|
| SubscriberKey | Text | Subscriber identifier |
| EmailAddress | Email | Subscriber email |
| EventDate | Date | Date/time of open event |
| JobID | Number | Links to _Sent on JobID + SubscriberKey |
| IsUnique | Boolean | 1 = first open for this job |

### _Click (if used)
| Field | Type | Notes |
|---|---|---|
| SubscriberKey | Text | Subscriber identifier |
| EmailAddress | Email | Subscriber email |
| EventDate | Date | Date/time of click event |
| JobID | Number | Links to _Sent on JobID + SubscriberKey |
| URL | Text | URL that was clicked |
| IsUnique | Boolean | 1 = first click for this job |

### _Bounce (if used)
| Field | Type | Notes |
|---|---|---|
| SubscriberKey | Text | Subscriber identifier |
| EmailAddress | Email | Subscriber email |
| EventDate | Date | Date/time of bounce event |
| JobID | Number | Links to _Sent on JobID + SubscriberKey |
| BounceType | Text | HardBounce, SoftBounce, BlockBounce, TechnicalBounce |
| SMTPBounceReason | Text | SMTP error message |

### _Subscribers (if used)
| Field | Type | Notes |
|---|---|---|
| SubscriberKey | Text | Subscriber identifier |
| EmailAddress | Email | Subscriber email |
| Status | Text | Active, Bounced, Unsubscribed, Held |
| DateUnsubscribed | Date | Most recent unsubscribe date (not historical) |
| DateHeld | Date | Most recent held date |

### _Job (if used)
| Field | Type | Notes |
|---|---|---|
| JobID | Number | Unique identifier for the send job |
| EmailName | Text | Name of the email asset |
| Subject | Text | Email subject line |
| FromName | Text | Sender name |
| FromEmail | Email | Sender email address |
| SendDate | Date | Scheduled send date/time |
| DeliveredTime | Date | Actual delivery completion time |

---

## Query Draft

```sql
-- Marketing Cloud Data Views — Query Activity
-- Target DE: <TargetDEName>
-- Action: Overwrite | Update
-- Source view(s): <list data views>
-- Date range: <e.g., last 30 days>

SELECT
    -- List only the columns needed (no SELECT *)
    <column_list>
INTO <TargetDEName>
FROM <PrimaryDataView> <alias>
-- Add JOINs here if needed:
-- INNER JOIN _Job j ON <alias>.JobID = j.JobID
-- INNER JOIN _Click c ON <alias>.JobID = c.JobID AND <alias>.SubscriberKey = c.SubscriberKey
WHERE <alias>.EventDate >= DATEADD(DAY, -<N>, GETDATE())
-- Add additional filters:
-- AND <alias>.BounceType = 'HardBounce'
-- AND <alias>.Status = 'Active'
-- GROUP BY / DISTINCT (required if output must have one row per subscriber):
-- GROUP BY <alias>.SubscriberKey, <alias>.EmailAddress
```

---

## Pre-Run Checklist

Complete before embedding this query in an Automation Studio Query Activity:

- [ ] SELECT INTO targets a pre-existing DE with matching field names
- [ ] Query Activity action (Overwrite vs Update) confirmed and documented
- [ ] All date filters use T-SQL functions: `GETDATE()`, `DATEADD()` — no `NOW()` or `DATE_SUB()`
- [ ] Date range is 6 months (180 days) or less for all engagement data views
- [ ] Cross-view JOINs use `JobID + SubscriberKey` as the composite key
- [ ] DISTINCT or GROUP BY applied where duplicate SubscriberKey rows are possible
- [ ] No CTEs (`WITH` clauses) and no window functions (`ROW_NUMBER() OVER`, `RANK() OVER`)
- [ ] NULL checks use `IS NULL` / `IS NOT NULL`, not `= NULL`
- [ ] Query tested in Query Studio and completes within 30 minutes
- [ ] Row count in target DE verified after test run

---

## Post-Run Monitoring

After the first Automation Studio run:

- **Target DE row count:** ___ (expected) vs ___ (actual)
- **Automation Studio run time:** ___ minutes (flag if > 20 minutes)
- **Automation Studio status:** Success / Error (paste error message if applicable)
- **Row count anomaly check:** If actual rows << expected, check whether date range has aged out of the 6-month retention window

---

## Notes

Record any deviations from the standard pattern, edge cases encountered, or design decisions made during implementation:

- 
