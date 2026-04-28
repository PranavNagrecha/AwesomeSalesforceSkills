# Pre-Load Sizing Template — Data Loader / Bulk API / Batch Apex

Fill this in for every high-volume load before kicking it off. It is the input the sizing checker (`scripts/check_data_loader_batch_window_sizing.py`) uses, and the artifact reviewers ask for in change-control.

---

## 1. Scope

| Field | Value |
|---|---|
| Load name | (e.g., "Q3 2026 Account historical migration") |
| Owner / load engineer | |
| Maintenance window (start / end UTC) | |
| One-time historical OR recurring | |
| Source system | |
| Target org (sandbox / production) | |

---

## 2. Target Object Profile

| Field | Value | Notes |
|---|---|---|
| SObject API name | (e.g., `Account`) | |
| Record count for this load | | exact or ±10% estimate |
| OWD setting | Public R/W / Public RO / Private | check Setup → Sharing Settings |
| Role hierarchy depth above load user | 0 / 1-2 / 3-5 / 6+ | implicit-share fan-out scales with depth |
| Sharing rules count on object | | each rule adds recalc work |
| Triggers on object (count) | | classic Apex triggers |
| Record-triggered Flows on object (count) | | each one fires per record |
| Validation rules count | | run on every insert/update |
| Duplicate rules active | yes / no | duplicate detection runs synchronously |
| Field history tracking — fields touched by this load | (list) | each field × each record = 1 history row |
| Feed tracking enabled | yes / no | feed item creation cost |
| Territories assigned (Territory Mgmt 2.0) | yes / no | mandates serial mode |
| Account/Opportunity/Case Teams active | yes / no | not covered by Defer Sharing Calculations |

---

## 3. Parent–Child Shape

| Field | Value |
|---|---|
| Is this a parent–child load? | yes / no |
| Parents already exist in target? | yes / no |
| External Id field on parent | (e.g., `Legacy_Account_Id__c`) or N/A |
| External Id field on child lookup | or N/A |
| Strategy | Strict parent-first / External Id deferred linkage |
| Row-skew check (max children per parent) | run `SELECT ParentId, COUNT(Id) FROM Child GROUP BY ParentId ORDER BY COUNT(Id) DESC LIMIT 50` and record the top result |
| Row-skew action | none needed / serial mode / redistribute ownership before load |

---

## 4. API Call Budget

| Field | Value |
|---|---|
| Daily API call quota (org limit) | |
| Calls already consumed today (running average) | |
| Headroom available for this load | |
| Estimated calls for this load | `record_count / batch_size × 2` |
| OK to proceed? | yes / no — if no, schedule for off-peak |

---

## 5. Recommendation

| Field | Value | Source |
|---|---|---|
| Recommended batch size | | Decision Guidance table in SKILL.md |
| Recommended mode | parallel / serial | row-skew + OWD + automation |
| Recommended API | Bulk V2 / Bulk V1 / REST Composite / Batch Apex | volume tier |
| Trigger bypass plan | none / TriggerControl__mdt for load user | one-time historical → bypass |
| Defer Sharing Calculations | ON / OFF for the window | Private OWD with sharing rules → ON |
| Field history tracking action | none / disable for fields X, Y during window | mass-update + tracked field → disable |
| Load user | dedicated load user (NOT personal admin) | |
| Estimated runtime | (e.g., 9–12 hours) | |
| Pilot plan | 5,000-record dry run before full | mandatory for >100K loads |

---

## 6. Fallback

If the first attempt fails or shows distress signals, the fallback is:

| Trigger | Action |
|---|---|
| `CPU_TIME_LIMIT_EXCEEDED` on a batch | drop batch size 50% and retry; if still failing, enable trigger bypass |
| `UNABLE_TO_LOCK_ROW` rate >2% | switch to serial mode; do NOT retry in parallel |
| Sharing recalc tail >2× expected runtime | enable Defer Sharing Calculations; cancel current recalc if possible |
| API call budget exhaustion mid-load | pause load; resume in next-day window or after coordinating with other consumers |
| Validation rule failure cascade | profile failures; consider bypassing validation for the load user via permission-set or CMDT |

---

## 7. Post-Load Verification

- [ ] Row count in target matches expected
- [ ] Spot-check 20 random records for field correctness
- [ ] Async sharing recalc has completed (Setup → Sharing Settings → Recalculation status)
- [ ] Trigger bypass CMDT flag has been cleared
- [ ] Field history tracking has been re-enabled
- [ ] Defer Sharing Calculations has been turned OFF (back to default)
- [ ] Reports and list views on the loaded object are responsive
- [ ] Post-load enrich Batch Apex job (if applicable) completed without errors
- [ ] Daily API call consumption is below 80% of quota (next-day headroom preserved)

---

## 8. Notes / Deviations

(record any deviations from the standard recommendation and the reasoning)
