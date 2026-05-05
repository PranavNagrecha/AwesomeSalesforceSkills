# Well-Architected Notes — Flow Time-Based Patterns

## Relevant Pillars

- **Reliability** — Recheck-entry-condition is the
  highest-leverage reliability investment in Scheduled Paths.
  Default-off behavior fires reminders against records whose state
  has changed since queue time — closed cases, reassigned owners,
  deleted records. Toggle on by default unless you have a specific
  reason not to.
- **Operational Excellence** — Time-zone basis decisions documented
  per flow keep future maintainers from rediscovering the same
  surprise. "Why is this firing at 3 AM for me?" is always a
  time-zone question; the answer should be in the flow's docs, not
  rediscovered each time.

## Architectural Tradeoffs

- **Scheduled Path vs Scheduled Flow.** Path is per-record-event;
  Flow is cron-driven. Path runs in the saving user's TZ; Flow runs
  in org default. Pick by whether the work is record-bound or
  schedule-bound.
- **Wait element vs Scheduled Path.** Wait pauses an interview;
  Path queues async work off a trigger. Wait is interactive
  (resume on event), Path is fire-and-forget. Different
  mechanisms, different runtime constraints.
- **Recheck on vs off.** On = silent exit when state changes
  (correct for most reminders). Off = path always fires
  (correct for time-stamped audit-trail tasks where the record's
  state at queue-time is what matters).
- **Apex `System.scheduleBatch` vs Scheduled Flow.** Apex for
  high-volume, complex logic; Flow for admin-owned, modest-volume
  work. Don't reach for Apex when Flow fits the requirement.

## Anti-Patterns

1. **Scheduled Path with no recheck-entry-condition.** Fires against
   stale state; reminders go to wrong owners on closed cases.
2. **Time-zone basis assumed without verification.** "9 AM" without
   specifying whose 9 AM is the most common time-zone bug.
3. **Wait element in record-triggered flow.** Doesn't compile; use
   Scheduled Path.
4. **Negative offset against past-dated record fires immediately
   when expected to be a no-op.** Add an entry-condition check.
5. **Workflow Rule migration that drops "or updated" half.** New flow
   fires only on insert; users notice missing automation later.
6. **Long Wait element pauses across flow definition releases.**
   Stale definition references can make resume fail.

## Official Sources Used

- Add Scheduled Paths to Your Flow — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_scheduled.htm&type=5
- Configure the Scheduled Path Trigger — https://help.salesforce.com/s/articleView?id=sf.flow_build_extend_pathways_scheduled.htm&type=5
- Schedule a Flow — https://help.salesforce.com/s/articleView?id=sf.flow_distribute_schedule.htm&type=5
- Wait Element — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_wait.htm&type=5
- Migrate from Workflow Rules to Flow — https://help.salesforce.com/s/articleView?id=sf.workflow_migration_tool.htm&type=5
- Salesforce Time Zone Settings — https://help.salesforce.com/s/articleView?id=sf.admin_supported_timezone.htm&type=5
- Sibling skill — `skills/flow/flow-error-notification-patterns/SKILL.md`
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
