# Examples — Flow Error Monitoring

Three worked situations, then the two failure shapes that turn up most often in an org that
believes it already has monitoring. The deployable artefacts live in
`references/metadata-examples.md`; nothing here repeats them.

---

## Example 1: 80 flows, one drowned inbox, nobody reading it

**Context:** 80 active flows. Fault emails arrive constantly and every one of them lands in
a different individual's inbox. Two of those people have left the company.

**What is actually happening:** the org has never deployed a `Flow.settings` file, so
`enableFlowUseApexExceptionEmail` is at its default `false` and every error email goes to
"the user who last modified the process or flow" (`api_meta.txt` L116961–L116967). There is
no org-controlled destination at all — the routing is a side effect of who edited what last.

**The move, in order:**

1. Deploy `apexEmailNotifications` with the real recipients — **first**, because deploying
   the setting flag against an empty list is strictly worse than the default.
2. Deploy `Flow.settings` with `enableFlowUseApexExceptionEmail` set to `true`.
3. Only then start wiring fault connectors. The email is now a safety net under the sink,
   not the sink.

**What this does not fix:** email is still one message per fault. It is coverage, not a
monitoring architecture — see Example 3 for the aggregation.

---

## Example 2: "Our flow health dashboard shows zero errors"

**Context:** A weekly report built on `FlowInterviewLog`, grouped by `FlowDeveloperName`,
filtered to `InterviewStatus = 'Error'`. It has shown zero rows for four months. The
portfolio is 90% record-triggered.

**Diagnosis:** the report is correct and the org is not healthy. `FlowInterviewLog`
"represents the logs of a **screen flow** interview" (`object_reference.txt`
L140059–L140060). A record-triggered flow structurally cannot produce a row there.

**The replacement pair.** Live state first — this is the one that answers "is anything stuck
right now":

```sql
SELECT InterviewStatus, CurrentElement, COUNT(Id) stuck
FROM   FlowInterview
WHERE  InterviewStatus IN ('Paused', 'VersionPaused', 'Error')
GROUP BY InterviewStatus, CurrentElement
ORDER BY COUNT(Id) DESC
```

Then history, from the sink the fault paths write to:

```sql
SELECT Source__c, COUNT(Id) errors, MAX(CreatedDate) last_seen
FROM   Application_Log__c
WHERE  Severity__c IN ('ERROR', 'FATAL')
AND    CreatedDate = LAST_N_DAYS:30
GROUP BY Source__c
HAVING COUNT(Id) > 5
ORDER BY COUNT(Id) DESC
```

The second query returns nothing on day one, and that is the honest answer: history only
exists from the moment fault connectors were wired. Say so rather than presenting an empty
result as good news.

---

## Example 3: One data load, 200 alerts, and the fix that is not "send fewer emails"

**Context:** A nightly integration writes 200 records. One malformed batch takes the same
fault path 200 times. The on-call engineer gets 200 messages and mutes the channel — which
is how the *next* incident goes unnoticed.

**Why "just suppress it" is the wrong instinct:** suppression at the channel throws away the
count, and the count is the finding. 200 identical faults and 1 fault are different
incidents.

**The shape that works:** the fault path writes unconditionally and never notifies; a
separate record-triggered flow on the sink applies the threshold. Sketch of the entry
criteria on that second flow — one Get Records, one Decision, no loop:

```
[Start] Application_Log__c, RecordAfterSave, Create only
        entry: Severity__c In ('ERROR','FATAL')
   │
   ▼
[Get Records] Application_Log__c
        Source__c        = {!$Record.Source__c}
        Severity__c   In   ('ERROR','FATAL')
        CreatedDate  >=    {!Fifteen_Minutes_Ago}      (formula, DateTime)
        Store: all records, first record's fields only  →  {!Recent_Failures}
   │
   ▼
[Decision] Threshold_Breached?
        {!Recent_Failures} count  >  5      → [Action: emailSimple] → [End]
        default                              → [End]
```

Every element on that path needs its own fault connector too. A monitoring flow that fails
silently is the one failure nobody is watching for — which is why the checker lints *every*
flow in the tree, including this one.

**Ownership boundary:** choosing the channel and quietening an already-noisy one is
`flow/flow-error-notification-patterns`. Deciding that aggregation sits between the fault and
the channel is this skill.

---

## Anti-Pattern: One inbox for all fault emails

All 80 flows mail one alias. Within a month it is a folder nobody opens, and the org has
converted a per-flow problem into a single ignored one. **Fix:** route by severity, not by
flow — inline paging only for the band you have agreed to be woken for, everything else into
the sink and a scheduled review.

---

## Anti-Pattern: A log object with no severity, or with a severity nobody matched

Two versions of the same failure. Without `Severity__c` the log cannot be filtered, so the
headline view is unusable. *With* it, but written as free text, half the rows say `Error`,
half say `ERROR`, and the report's filter silently drops the ones it does not match.

**Fix:** reuse `templates/apex/custom_objects/fields/Severity__c.field-meta.xml` — a
`required`, `restricted` picklist with `fullName` values `DEBUGL`, `INFOL`, `WARN`, `ERROR`,
`FATAL` — and assign exactly one of those in every fault path. A restricted picklist turns a
reporting bug into a deploy-time error, which is where you want it.
