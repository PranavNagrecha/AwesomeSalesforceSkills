# Investigation Recipes

End-to-end workflows for the most common Salesforce debug log scenarios. Each recipe is: symptom, triage commands, deep investigation, conclusion patterns, and fix recommendations.

## Recipe 1: Flip-flop field (field value keeps changing)

### Symptom
A field on a record takes value A, then value B, then A again, either within one transaction or across multiple transactions over time.

### Triage
```bash
cd /mnt/user-data/uploads
# 1. Triage all logs by timestamp and size
for f in *.log; do
  start=$(head -3 "$f" | tail -1 | awk '{print $1}')
  size=$(wc -c < "$f")
  echo "$start  $f  size=$size"
done | sort

# 2. Find every log that mentions the record ID
for f in *.log; do
  count=$(grep -c "<RECORD_ID>" "$f" 2>/dev/null)
  [ "$count" != "0" ] && echo "$f: $count references"
done
```

### Deep investigation

**Step 1: Extract field value transitions across all logs**

```python
python3 << 'EOF'
import re, os, glob
RECORD_ID = "003XXXXXXXXXX"   # replace
FIELD = "My_Field__c"         # replace

for f in sorted(glob.glob("*.log")):
    with open(f) as fp: content = fp.read()
    # Find all FLOW_VALUE_ASSIGNMENT dumps containing this record
    dumps = re.findall(r'FLOW_VALUE_ASSIGNMENT\|[^|]+\|[^|]+\|(\{[^}]*' + RECORD_ID + r'[^}]*\})', content)
    prev = None
    for i, d in enumerate(dumps):
        m = re.search(FIELD + r'=([^,}]+)', d)
        if m and m.group(1) != prev:
            print(f"{f} dump#{i}: {FIELD} = {m.group(1)}")
            prev = m.group(1)
EOF
```

Only transitions print. The pattern reveals where in the cascade the flip happens. If the transition always happens at the same dump index, the same automation is responsible every time.

**Step 2: Identify the writing mechanism**

Check each mechanism in order:

```bash
# 1. Apex direct write
grep -B2 -A2 "VARIABLE_ASSIGNMENT" log.log | grep "My_Field__c"

# 2. Flow assignment
grep "FLOW_ASSIGNMENT_DETAIL" log.log | grep "My_Field__c"

# 3. DLRS recalculation (rollup)
grep -E "dlrs_.*Trigger|RollupService" log.log

# 4. Workflow field update (legacy)
grep "WF_FIELD_UPDATE" log.log | grep "My_Field__c"
```

**Step 3: If no direct write found, suspect rollup or formula**

If the field appears in `FLOW_VALUE_ASSIGNMENT` record dumps with changing values but nothing in steps 1-3 matches, the field is being recalculated:
- Check metadata: is it a formula field? (nothing actually writes to it)
- Check metadata: is it a roll-up summary? (recalculated on child record changes)
- Check for DLRS: is the field defined in `dlrs__LookupRollupSummary2__mdt`?

**Step 4: If multiple writers, check order**

If multiple flows/triggers write the field, the "winner" depends on execution order.

```bash
# Get execution order of writers
grep -nE "CODE_UNIT_STARTED.*trigger|FLOW_START_INTERVIEW_BEGIN" log.log | head -30
```

### Conclusion patterns

- **Direct write + another direct write alternating**: two automations competing. Fix by choosing one as source of truth, suppressing the other.
- **Rollup recalculation**: child records flip-flop, rollup faithfully propagates. Fix upstream at the child.
- **Workflow field update in a cascade**: WF field update fires, re-saves record, another automation overwrites. Fix by migrating WF to flow with proper ordering.
- **Retry loop from managed package**: package retries failed operation every 10-60 seconds, each attempt writes status fields. Flip-flop is symptom of the loop. Find the root cause of the failure.
- **Different users writing different values**: integration user sets A, human user sets B. Permissions/process issue.

### Fix recommendations

1. Identify the authoritative source of truth for the field.
2. Suppress other writers (disable rule, add criteria, use guard field).
3. For rollups, consider scheduled recalc vs realtime.
4. For recursion, add recursion guard (static variable or processed-ID tracking).
5. If the field should be a formula or rollup but is currently a text/picklist, consider redesigning.

## Recipe 2: Merge failure diagnosis

### Symptom
Merge operation fails with `INSUFFICIENT_ACCESS_OR_READONLY, cannot merge with entity that is not accessible: []`.

### Triage

```bash
# Find the merge operation in the log
grep -B 5 -A 5 "Op:Merge\|cannot merge" log.log

# Identify the running user
grep "USER_INFO" log.log | head -1

# Identify master and losing record IDs
grep -B 10 "Op:Merge" log.log | grep -E "FLOW_VALUE_ASSIGNMENT|VARIABLE_ASSIGNMENT" | grep -oE "003[A-Za-z0-9]{15}" | sort -u
```

### Deep investigation

**Critical**: the empty brackets `[]` in the error are deliberate. Salesforce refuses to name the blocking record for security reasons. The log cannot tell you which child record is blocking.

**Step 1: Identify the running user**

```bash
grep "USER_INFO" log.log
```

Look for the user ID. If it is an integration user (often named "TracRTC Integration", "Marketo", "Boomi", etc.), the user probably has reduced permissions.

**Step 2: Reproduce with visibility**

Ask the user to:
1. Log in as admin.
2. Impersonate the integration user (Setup > Users > Login).
3. Navigate to the master or losing record.
4. Manually attempt the merge in the UI.

The UI error is typically more specific: it will name the blocking object (Opportunity, Task, Event, custom lookup).

**Step 3: Diff child record visibility**

For each relationship on the object (Contact, for example):
- `Opportunities` via Account lookup
- `Cases`
- `Tasks` and `Events` (Activities)
- `Campaign Members`
- Custom `__c` lookups pointing to Contact

Run these as admin and as the integration user, compare counts:

```sql
SELECT COUNT() FROM Opportunity WHERE ContactId = '<losing-id>'
SELECT COUNT() FROM Task WHERE WhoId = '<losing-id>'
SELECT COUNT() FROM Event WHERE WhoId = '<losing-id>'
-- for every custom lookup
```

Any relationship where admin count > integration user count has records the integration user cannot see. That is the blocker.

**Step 4: Fix permissions**

Options:
- Grant the integration user access to the blocking object (profile/permission set).
- Change sharing to give Read/Modify All Data.
- Transfer ownership of blocking records to a user the integration user can see.
- Use the `Transfer All Data` permission (drastic).

### Conclusion patterns

- **Orphaned Activities**: Tasks/Events owned by inactive users, integration user cannot access.
- **Restricted custom object**: a custom lookup points to a record whose object has OWD Private, and the integration user lacks sharing.
- **Ownership in another role branch**: role hierarchy does not give integration user access.
- **Encrypted record**: Shield-encrypted field on the blocking record, integration user lacks View Encrypted Data.

### Fix recommendations

1. Immediate: log in as integration user, identify blocker in UI, manually resolve (delete, reassign, or grant access).
2. Short-term: add integration user to sharing or grant View All Data on affected objects.
3. Long-term: review integration user permission design. Many orgs over-restrict integration users.
4. Suppress retries: set `TracRTC__Disable_Complete__c = true` (or equivalent disable flag) on records stuck in retry loops.

## Recipe 3: Governor limit exceeded

### Symptom
`System.LimitException: Too many SOQL queries: 101` or similar.

### Triage

```bash
# What limit was hit?
grep -E "LimitException|Too many|exceeded" log.log

# Summary of limit usage
grep -A 30 "CUMULATIVE_LIMIT_USAGE$" log.log

# Per-namespace usage
grep "LIMIT_USAGE_FOR_NS" log.log
```

### Deep investigation

**For SOQL limit:**

```bash
# Count queries
grep -c "SOQL_EXECUTE_BEGIN" log.log

# Group queries by the code unit that issued them
awk '
  /CODE_UNIT_STARTED/ { cu = $0 }
  /SOQL_EXECUTE_BEGIN/ { print cu }
' log.log | sort | uniq -c | sort -rn | head -20

# Identify queries in loops (same query many times)
grep -A 1 "SOQL_EXECUTE_BEGIN" log.log | grep "SELECT " | sort | uniq -c | sort -rn | head -20
```

If the same query text appears 50+ times, it is almost certainly in a loop.

**For DML limit:**

```bash
grep -c "DML_BEGIN" log.log
grep "DML_BEGIN" log.log | grep -oE "Type:[A-Za-z_0-9]+" | sort | uniq -c
```

If you see 150 DMLs on one object, you have DML inside a loop.

**For CPU limit:**

```bash
# Profile methods by duration (requires APEX_PROFILING)
grep -E "METHOD_ENTRY|METHOD_EXIT" log.log | head -40
```

Use a script to compute method time deltas:

```python
import re
times = {}
stack = []
with open('log.log') as f:
    for line in f:
        m = re.match(r'(\d+:\d+:\d+\.\d+).*METHOD_ENTRY\|.*\|([^|]+)$', line)
        if m:
            stack.append((m.group(1), m.group(2).strip()))
            continue
        m = re.match(r'(\d+:\d+:\d+\.\d+).*METHOD_EXIT\|.*\|([^|]+)$', line)
        if m and stack:
            start, name = stack.pop()
            # compute delta, accumulate
            def sec(x):
                h,m,s = x.split(':'); return int(h)*3600+int(m)*60+float(s)
            times.setdefault(name, 0)
            times[name] += sec(m.group(1)) - sec(start)

for n, t in sorted(times.items(), key=lambda x:-x[1])[:20]:
    print(f"{t:.3f}s  {n}")
```

**For heap limit:**

Heap accumulates. Check for large collections being held:
```bash
grep "VARIABLE_ASSIGNMENT" log.log | grep -oE "List<[^>]+>" | sort | uniq -c | sort -rn
```

### Conclusion patterns

- **SOQL in loop**: same query text repeated 20+ times. Apex or flow loop is the issue.
- **DML in loop**: same DML type repeated. Bulkification problem.
- **Unexpectedly high count from managed package**: the package is misconfigured or a trigger is firing too many times.
- **CPU from string manipulation**: heavy regex, JSON, or concatenation in a loop.
- **Heap from stateful batch**: instance variables growing across batches.

### Fix recommendations

1. Bulkify: collect IDs first, query once, iterate in memory.
2. Move heavy work to async (batch for >10k records, queueable for chained processing).
3. Add governor guard checks: `if (Limits.getQueries() > 90) break;`.
4. For managed packages, check their settings to reduce work.
5. For heap, use `Database.QueryLocator` in batch instead of loading all records.

## Recipe 4: UNABLE_TO_LOCK_ROW concurrency

### Symptom
`System.DmlException: Update failed. First exception on row 0 with id 001XXX; first error: UNABLE_TO_LOCK_ROW`.

### Triage

```bash
# Find the lock failure
grep -B 10 "UNABLE_TO_LOCK_ROW" log.log

# Identify the contested record and object
grep -B 20 "UNABLE_TO_LOCK_ROW" log.log | grep -E "DML_BEGIN|Id:"
```

### Deep investigation

**Step 1: Identify the contested object**

Common lock-contested objects:
- Account (children share implicit lock)
- Opportunity (lines and products lock the parent)
- Case
- Parent records in master-detail

**Step 2: Find the concurrent transaction**

The other transaction is not in this log (by definition, it is in another log at the same time). Ask the user for:
- Other logs at the same timestamp.
- Setup > Monitoring > Debug Logs for overlapping entries.
- Event Monitoring for concurrent API calls.

**Step 3: Look for usual suspects**

- Bulk API jobs in parallel mode.
- Scheduled Apex firing simultaneously on related records.
- Multiple integration users writing at once.
- LWC/mobile apps saving the same record from different tabs.
- CPQ calculator running on the same quote twice.

### Conclusion patterns

- **Bulk API parallel mode**: records split into batches, same parent updated by multiple batches.
- **Recursive async**: queueable updates parent, triggers fire, queueable enqueued for the same parent from the child trigger.
- **Chatty integration**: external system POSTs updates faster than SF can commit them.
- **Human vs automation**: user editing in UI while a scheduled flow tries to update.

### Fix recommendations

1. Switch Bulk API to Serial mode (slower but no contention).
2. Add retry logic in Apex (`FOR UPDATE` with exception handling).
3. Queue updates per parent instead of parallel.
4. Use optimistic locking (ETag, lastmodified compare) in UI.
5. For integrations, batch updates per parent instead of per child.
6. Consider `System.Finalizer` (Winter '22+) to handle async cleanup on failure.

## Recipe 5: Performance bottleneck (slow transaction)

### Symptom
"Save takes 30 seconds." "My batch is slow." User's page is unresponsive.

### Triage

```bash
# Overall transaction duration
grep "EXECUTION_STARTED\|EXECUTION_FINISHED" log.log
# Compute delta between them

# Per-category time breakdown
grep "CUMULATIVE_PROFILING" log.log

# SOQL and DML counts
echo "SOQL: $(grep -c SOQL_EXECUTE_BEGIN log.log)"
echo "DML: $(grep -c DML_BEGIN log.log)"
echo "Callouts: $(grep -c CALLOUT_REQUEST log.log)"
```

### Deep investigation

**Step 1: Check SOQL plans**

```bash
grep -A 1 "SOQL_EXECUTE_BEGIN" log.log | grep "SOQL_EXECUTE_EXPLAIN"
```

`TableScan` in any plan = query without index. Potentially slow.
`relativeCost > 1.0` = non-optimal plan.

**Step 2: Profile method durations**

(See Recipe 3 for method timing script.)

**Step 3: Find slow callouts**

```bash
python3 << 'EOF'
import re
last_req = None
with open('log.log') as f:
    for line in f:
        m = re.match(r'(\d+:\d+:\d+\.\d+).*CALLOUT_REQUEST\|', line)
        if m:
            last_req = m.group(1)
            continue
        m = re.match(r'(\d+:\d+:\d+\.\d+).*CALLOUT_RESPONSE\|', line)
        if m and last_req:
            def sec(x):
                h,mi,s = x.split(':'); return int(h)*3600+int(mi)*60+float(s)
            duration = sec(m.group(1)) - sec(last_req)
            print(f"{duration:.3f}s  {line.strip()}")
            last_req = None
EOF
```

**Step 4: Identify heavy managed packages**

```bash
grep "LIMIT_USAGE_FOR_NS" log.log
```

Namespace with high CPU, SOQL, DML is a target.

### Conclusion patterns

- **TableScan SOQL**: missing index. Add custom index or rewrite query.
- **Slow callout**: external system is slow. Consider async.
- **CPQ calculator**: redesign pricing rules or use batch pricing.
- **DLRS heavy**: too many realtime rollups. Switch some to scheduled.
- **Vlocity/OmniStudio scripts**: redesign scripts with fewer steps or precomputed data.
- **Heavy JSON parsing**: cache parsed results.

### Fix recommendations

1. Add indexes on frequently filtered fields.
2. Move callouts to async.
3. Bulkify everything.
4. Cache reused SOQL results.
5. Move heavy work to batch/queueable.
6. For CPQ, use Large Quote Threshold setting.
7. For DLRS, switch to scheduled recalc for non-critical rollups.

## Recipe 6: Recursion / infinite loop

### Symptom
Transaction times out, hits CPU limit, or creates unexpected data. Fields updated many times.

### Triage

```bash
# Same trigger firing many times
grep "CODE_UNIT_STARTED.*trigger" log.log | awk -F'|' '{print $NF}' | sort | uniq -c | sort -rn

# Same flow firing many times
grep "FLOW_START_INTERVIEW_BEGIN" log.log | awk -F'|' '{print $3}' | sort | uniq -c | sort -rn

# DML counts on the same object
grep "DML_BEGIN" log.log | grep -oE "Type:[A-Za-z_0-9]+" | sort | uniq -c
```

If a trigger fires 5+ times in one transaction, you likely have recursion.

### Deep investigation

**Step 1: Identify the recursion loop**

The recursion is typically: trigger A updates record R → trigger A fires again on R → repeat.

Or: trigger A on object X updates related record Y → trigger B on Y updates X → trigger A fires again.

Trace through the log to find the cycle.

**Step 2: Check recursion guards**

```bash
# Look for static boolean checks
grep -E "isExecuting|alreadyProcessed|isRunning" log.log
```

If no guard is visible, the trigger has no recursion protection.

### Conclusion patterns

- **Trigger updates same object, no guard**: classic. Add static boolean guard.
- **Trigger A → Flow → Trigger A**: flow updates triggering record, which re-fires trigger.
- **Cross-object cascade**: Parent updates Child, Child updates Parent, repeat.
- **Workflow field update + trigger**: WF field update re-fires trigger, which re-fires WF (WF rules evaluate twice).

### Fix recommendations

1. Add static boolean guard in Apex trigger handler.
2. Track processed record IDs in a static set.
3. In flows, use `IsChanged` entry criteria to avoid re-firing on no-op updates.
4. For cross-object cascades, use a "processing already done" field or Platform Cache.
5. For WF field update recursion, migrate to flow with `IsChanged` check.

## Recipe 7: Missing field update (expected change did not happen)

### Symptom
User expected field to update but it did not.

### Triage

```bash
# Did the automation fire at all?
grep "My_Flow_Name\|MyTrigger" log.log

# Did it evaluate the condition?
grep "FLOW_RULE_DETAIL" log.log | head -20
```

### Deep investigation

**Step 1: Verify trigger/flow fired**

Grep for the entry point.

**Step 2: If fired, verify the decision was true**

```bash
grep "FLOW_RULE_DETAIL" log.log | grep "<My Decision>"
```

Look for the outcome. If "false", the entry criteria did not match.

**Step 3: If decision was true, verify the assignment ran**

```bash
grep "FLOW_ASSIGNMENT_DETAIL" log.log | grep "My_Field__c"
```

**Step 4: If assignment ran, check for overwrite**

Another automation might have overwritten the value. Re-run Recipe 1 (flip-flop) steps.

**Step 5: Check for fault path that silently consumed the error**

```bash
grep "FLOW_ELEMENT_FAULT" log.log
```

### Conclusion patterns

- **Entry criteria not matching**: field value not what flow expects.
- **Trigger suppressed**: recursion guard blocked the firing.
- **Overwritten by later automation**: check execution order.
- **Silent fault**: fault connector consumed the error without surfacing.
- **User-initiated DML bypassed automation**: API with `disableFeeds=true` or similar flag.

### Fix recommendations

1. Check entry criteria match the actual field values.
2. Verify recursion guards allow legitimate re-fires.
3. Add fault-to-email handler in flow to surface errors.
4. Audit execution order for conflicts.

## Recipe 8: User can't see record

### Symptom
"User X cannot see record Y that I can see." Permission issue.

### Triage

```bash
# Identify the running user in the log
grep "USER_INFO" log.log | head -1

# Find the failed SOQL or DML
grep -E "INSUFFICIENT_ACCESS|null.*Id" log.log
```

### Deep investigation

The log itself rarely gives the full answer for access issues. You need to check:

1. **Object permissions**: Profile > Object Settings > Read access?
2. **Field-level security**: Profile/Permission Set > Field-Level Security > Read access?
3. **Sharing model (OWD)**: Is the object Private? If so, user needs sharing.
4. **Sharing rules**: Criteria-based, ownership-based sharing rules that might (or might not) apply.
5. **Role hierarchy**: Is the user in a role that includes the owner's role?
6. **Manual share**: Has anyone manually shared this record?
7. **Implicit sharing**: Account parent sharing to Contact/Opportunity?
8. **Territory management**: User in the right territory?
9. **Apex managed sharing** (__share table entries).
10. **Restriction rules**: Any restriction rules filtering this user?

### Conclusion patterns

- **OWD Private + no sharing rule**: expected behavior, grant via sharing rule or manual share.
- **Guest User in Community**: limited by Guest User profile settings.
- **External / Customer Community user**: cannot see internal records unless explicitly shared.
- **Restriction rule**: newer feature, filters records from certain users.

### Fix recommendations

1. Grant access via sharing rule, permission set, or role adjustment.
2. For integration users, consider "View All Data" profile permission for the specific object.
3. For Experience Cloud, configure Guest User Sharing Rules.
4. Use "Share Groups" for partner/customer community users.

## Recipe 9: Async job not running / batch stuck

### Symptom
User enqueued a batch/queueable/future but no log appears. Job status shows "Queued" or "Preparing" in Setup > Apex Jobs.

### Triage

Cannot debug purely from log. Check:
- Setup > Monitoring > Apex Jobs: status? Error?
- Setup > Monitoring > Apex Flex Queue: is it backed up?
- Setup > Monitoring > Scheduled Jobs: is the job scheduled for later?

### Deep investigation

**Possible states:**

1. **Queued, waiting for capacity**: org has hit async limit (250k per 24h or 5 concurrent batches).
2. **Holding**: batch is in holding because Flex Queue is full.
3. **Preparing**: large batch start() method is still running (reading records).
4. **Processing**: running now.
5. **Failed (unknown)**: check Apex Jobs for error message.

### Conclusion patterns

- **Stuck in holding**: Flex Queue is full (100 batch limit). Drain queue or wait.
- **Stuck in preparing**: start() method is slow. Refactor to use QueryLocator with selective SOQL.
- **Failed without log**: Apex Jobs shows the error. Common: start() threw an exception.

### Fix recommendations

1. Check Apex Jobs for status and error.
2. For Flex Queue full, abort unnecessary queued jobs.
3. For slow start(), pre-filter records and use QueryLocator.
4. Add `@future` fallback or Retry pattern via Transaction Finalizer.

## Recipe 10: Integration failing silently

### Symptom
"The data used to sync to [external system] but it stopped." No errors visible.

### Triage

```bash
# Look for any callout activity
grep "CALLOUT_REQUEST\|CALLOUT_RESPONSE" log.log

# Platform events published/subscribed
grep "EVENT_SERVICE_PUB\|EVENT_SERVICE_SUB" log.log

# Outbound messaging (legacy)
grep "WF_OUTBOUND_MSG" log.log
```

### Deep investigation

**Possible causes:**

1. **OAuth token revoked**: next callout fails with 401.
2. **Named Credential cert expired**.
3. **Remote endpoint changed**: getting 404 or 301.
4. **Remote system returning HTML error pages**: Apex parses as JSON, throws silently caught exception.
5. **Platform event subscriber fell behind**: 72h retention exceeded, events lost.
6. **CDC subscriber GAP_OVERFLOW**: bulk change overwhelmed subscriber.
7. **Outbound message queue aged out**: OM messages dropped after 24h.
8. **Trigger that was making the callout was disabled**.

### Conclusion patterns

- **No callouts in log**: the trigger or flow that makes them is not firing.
- **Callouts with 4xx/5xx**: external system issue.
- **Callouts with 200 but subsequent errors**: response parsing or downstream logic.
- **Platform events published but no subscribers firing**: subscriber disabled or failing.

### Fix recommendations

1. Check Setup > Connected Apps OAuth Usage.
2. Renew certificates.
3. Test endpoint manually via Workbench/Postman.
4. Check Setup > Event Manager for failed publications.
5. Check Apex Exception Email for caught-and-ignored errors.

## Recipe 11: Bulk upload failing

### Symptom
User loaded a CSV via Data Loader or Bulk API, some records failed.

### Triage

Check:
- Data Loader output: success/error files.
- Bulk API Job Status: Setup > Environments > Bulk Data Load Jobs.
- Debug log on the integration user for the load time.

### Deep investigation

Common causes:
1. **Validation rule violations**: error file shows the rule name.
2. **Duplicate rule blocking**: error says DUPLICATES_DETECTED.
3. **Required field missing**: CSV has blank required field.
4. **UNABLE_TO_LOCK_ROW**: parallel mode on related records.
5. **Trigger throwing on bulk**: non-bulkified trigger fails beyond 200 records.
6. **Too many DML rows**: trigger doing cascading DML exceeds 10,000 rows for the bulk.
7. **Field-level security**: integration user lacks edit access to a field being loaded.

### Fix recommendations

1. Review error file, classify by error code.
2. For lock errors, switch Bulk API to Serial mode.
3. For trigger errors, bulkify the trigger.
4. For FLS, grant integration user edit access.
5. For validation errors, clean data or fix validation rule.

## Recipe 12: Emergency "stop the bleeding" checklist

When something is actively firing repeatedly and causing data damage:

1. **Find the loop**: Recipe 6 for recursion, Recipe 1 for flip-flop.
2. **Suppress the loop**:
   - Deactivate the trigger (Setup > Apex Trigger > Active = false in Dev; use tooling API in prod).
   - Deactivate the flow (Setup > Flow > Deactivate).
   - Set kill-switch field on affected records (`TracRTC__Disable_Complete__c = true` or similar).
   - Abort scheduled jobs (Setup > Scheduled Jobs > Delete).
3. **Assess damage**: query affected records, compare to expected.
4. **Reverse damage**: if field was flip-flopped, set to correct value via Data Loader.
5. **Communicate**: tell stakeholders. Loops often hit many records.
6. **Root cause**: after bleeding stops, apply Recipe 1-6 to diagnose.
7. **Permanent fix**: deploy fix via sandbox + deployment process.
8. **Re-enable**: carefully re-enable automation and verify no recurrence.
