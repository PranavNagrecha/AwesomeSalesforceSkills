---
name: scheduled-flow-not-running-debug
description: "Use when a Schedule-Triggered Flow is configured but is not firing at the expected time, or appears active in Setup → Flows but never produces output. Covers where scheduled flows actually surface (Setup → Scheduled Jobs, NOT Setup → Apex Jobs), the AsyncApexJob / CronTrigger evidence trail, top causes (deactivated scheduling user, daylight-savings transitions, time-zone mismatches between scheduling user and org, fault-paths that quietly stop the schedule, daily async-Apex limit pressure), and recovery steps (re-schedule via Apex, run the flow manually with the same input, switch the scheduling user). Triggers: 'how do I schedule a flow to run every monday', 'scheduled flow not firing', 'flow scheduled but no execution', 'scheduled flow stopped working last week', 'monday 6am scheduled flow did not run after dst change'. NOT for designing a new scheduled flow's record scope or idempotency (use flow/scheduled-flows), NOT for record-triggered Scheduled Paths that don't fire (use flow/flow-time-based-patterns), NOT for general Batch Apex job monitoring (use admin/batch-job-scheduling-and-monitoring)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - scheduled-flow-not-running-debug
  - schedule-triggered-flow
  - async-apex-job
  - cron-trigger
  - flow-debugging
triggers:
  - "how do I schedule a flow to run every monday"
  - "scheduled flow not firing"
  - "flow scheduled but no execution"
  - "schedule triggered flow stopped running after the user was deactivated"
  - "monday 6am scheduled flow did not run after dst transition"
  - "where do I check if my scheduled flow ran last night"
  - "the flow is active in setup but never produces records"
  - "scheduled flow ran for months then quietly stopped"
inputs:
  - "Flow API name and the cadence the admin believes is configured (Once / Daily / Weekly + start time + day-of-week)"
  - "Which user originally scheduled the flow (and whether that user is still Active)"
  - "Org default time zone vs scheduling user's profile time zone"
  - "Whether the flow has fault paths and whether any nested invocable Apex action exists"
outputs:
  - "Diagnosis of why the schedule isn't firing — pinned to one of: not actually scheduled, scheduling user deactivated, time-zone mismatch, DST gap, fault path stopping interview, async-apex limit, deployment-aborted CronTrigger"
  - "SOQL evidence (`AsyncApexJob`, `CronTrigger`, `FlowInterview`) the admin can paste into Workbench / Developer Console"
  - "Recovery plan — re-schedule under a permanent integration user, run manually for the missed window, monitor the next fire"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
---

# Scheduled Flow Not Running Debug

Activate this skill when an admin reports a Schedule-Triggered Flow is configured but isn't running on its expected cadence. The skill is about *diagnosis and recovery* — not about whether the flow's design is right. If the question is "should I use a scheduled flow vs Batch Apex", route to `flow/scheduled-flows` instead.

The most common shape of this question: "I scheduled a flow for Monday 6 AM, the flow is Active in Setup → Flows, but Tuesday morning the records I expected weren't updated." 80% of these reports resolve to one of four causes — wrong place to check, deactivated scheduling user, time-zone confusion, or a fault path that silently aborted the interview. The remaining 20% are deployment side-effects, DST transitions, or maintenance-window collisions.

---

## Before Starting

Gather this context before writing any diagnosis:

- **Where the admin already looked.** If they only checked Setup → Flows and saw the flow as Active, they have not yet checked the only place schedule-triggered flows actually surface as runnable jobs (Setup → Scheduled Jobs). This is the most common false-negative — "the flow is active so the schedule must be working" is wrong.
- **Who scheduled the flow originally.** Schedule-Triggered Flows execute in the *running-user context* of the user who clicked "Schedule" when the flow was activated. If that user is now Inactive, the schedule keeps existing as a `CronTrigger` row but produces failed `AsyncApexJob` rows or stops firing entirely depending on how the deactivation happened.
- **Org time zone vs scheduling user's time zone.** The Schedule Trigger's "Start Time" is stored relative to the scheduling user's profile time zone, not the org default. A schedule set for "6 AM" by an EMEA-based admin will fire at 6 AM London for a US-org with a Pacific default — six hours earlier or later than American admins expect. This is documented behavior on the Schedule a Flow help page.
- **Recent changes.** Three changes routinely break scheduled flows: (1) a deployment of any Apex class invoked by the flow (auto-aborts the CronTrigger), (2) the scheduling user being deactivated as part of a license cleanup, (3) a daylight-savings transition during the configured fire-time window.
- **Whether the flow has any fault path.** A scheduled flow whose first run hits an unhandled fault generates a Flow Error email but the schedule itself remains. However, individual interview failures *do* surface in Setup → Process Automation → Paused and Failed Flow Interviews, not in Setup → Apex Jobs.

If the user can't answer "who scheduled it?" — that's already a finding. Investigate user activation status before anything else.

---

## Core Concepts

### Concept 1 — Where scheduled flows actually live in Setup

Schedule-Triggered Flow execution evidence is split across **three** Setup screens, none of which is named "Scheduled Flows":

| What you want to see | Where to look | What you're looking at |
|---|---|---|
| Is the schedule still registered? | Setup → **Scheduled Jobs** | A `CronTrigger` row whose `CronJobDetail.Name` references the flow. Shows next-fire time and owner. |
| Did the most recent run succeed or fail? | Setup → **Apex Jobs** | An `AsyncApexJob` row with `JobType = 'ScheduledApex'`. The `ApexClass.Name` looks like an internal Salesforce flow runner — NOT the flow's API name. |
| Did individual flow interviews fail mid-run? | Setup → **Paused and Failed Flow Interviews** (Process Automation menu) | A `FlowInterview` row in Failed status. Each represents one in-progress interview — useful for fault-path debugging. |

The reason admins miss these: Setup → **Flows** shows the flow's Active status and its design-time schedule, but it does NOT show whether the schedule is actually firing. A flow can be Active and have no underlying CronTrigger if the schedule was never confirmed during activation, or if a deployment aborted it.

The single most leveraged check: **Setup → Scheduled Jobs**. If there's no row there for your flow, the schedule isn't registered — re-schedule it.

### Concept 2 — The four most common causes of "active but not running"

In approximate frequency order:

1. **Scheduling user is deactivated.** When a user is deactivated, their CronTriggers do not auto-cascade. In some org configurations the next fire produces an `AsyncApexJob` with `Status = 'Failed'` and an error message referencing inactive-user context. In others, the trigger simply doesn't produce a job. Either way, the flow stops running. **Fix:** re-schedule the flow under a permanent integration user (a license dedicated to scheduled work, never to be deactivated).
2. **Time-zone mismatch between scheduling user and org-time-of-business.** A flow scheduled by a London-based admin to run at "6 AM Mondays" fires at 6 AM London — which is 1 AM Eastern, 10 PM Sunday Pacific. American operations teams check Monday morning and conclude "didn't run." It ran; just not when they were watching. **Fix:** check Setup → Scheduled Jobs for the *Next Fire Time* — that's stored in UTC and rendered in the viewing user's TZ. Confirm against the scheduling user's TZ in their User record.
3. **Daylight-savings transitions.** A "6 AM daily" schedule does not observe DST gracefully — on the spring-forward day, the 2 AM hour doesn't exist; on the fall-back day, 1 AM happens twice. Schedule-Triggered Flow behavior on those two days varies, and customers report missed runs on the spring-forward day specifically. **Fix:** schedule outside the DST gap window (avoid 2 AM – 3 AM local time) or move to UTC-based Batch Apex via `System.schedule()` if the schedule is mission-critical.
4. **Unhandled fault aborts the interview, but schedule keeps existing.** An interview that hits a fault — DML failure, governor limit, missing record — emits a Flow Error email but does NOT delete the CronTrigger. The next scheduled run will attempt again. So "my flow ran for two months then stopped" usually isn't this — the CronTrigger doesn't get removed by faults. **However**, if the underlying invocable Apex class was deployed in that window, the CronTrigger *is* aborted by the deployment (see Concept 3), and that's often confused with "fault stopped my flow." Distinguish by checking deployment history vs error-email history.

### Concept 3 — Deployment side-effects: the silent CronTrigger killer

When you deploy an Apex class that's referenced by a Schedule-Triggered Flow's invocable action, **the CronTrigger is automatically aborted** at deployment time. The flow definition is unaffected (still Active in Setup → Flows), but the underlying schedule disappears. The next fire never happens. Two weeks later somebody notices.

This is the same behavior that affects Batch Apex via `System.schedule()` — see `devops/go-live-cutover-planning` Gotcha 5 for the broader pattern. For scheduled flows specifically: any deploy that touches a class invoked by the flow can trigger this. Common offenders:

- An invocable Apex action class the flow calls
- A trigger handler on an object the flow updates (less direct but observed)
- An Apex test class that imports a class used by the flow (sometimes triggers it, version-dependent)

**Detection:** Run `SELECT Id, CronJobDetail.Name, State, NextFireTime FROM CronTrigger WHERE State = 'WAITING'` after every deployment. If the count drops, you lost a scheduled flow.

**Fix:** include "verify all expected scheduled flows still appear in Setup → Scheduled Jobs" as a post-deploy step in your runbook. Re-schedule any that are missing.

### Concept 4 — When the schedule fires but the flow does no work

Distinct from "flow not firing": the flow fires on schedule but produces no records. Two common shapes:

- **Start filter matches zero records.** The Schedule-Triggered Flow's `Start` element has an Object + Filter Conditions. If the filter is too restrictive (or the data hasn't met it yet), the flow runs and exits with zero loop iterations. `AsyncApexJob.JobItemsProcessed = 0` — no error, just no work. **Fix:** Loosen the filter, or add a Get Records element that diagnostically counts qualifying records and emails the result.
- **Daily async-Apex limit pressure.** Salesforce orgs have a daily limit on async Apex executions (`@future` + Queueable + Batch + Schedulable combined; the limit scales with user license count, default minimum 250,000/day). When this limit is approached, the platform may throttle scheduled flows — they're queued but their `AsyncApexJob` rows show `Status = 'Holding'`. **Fix:** Check `AsyncApexJob` for `Status = 'Holding'` rows on the day in question. If chronic, this is an architecture problem, not a flow problem — the org needs to consolidate async work.

---

## Common Patterns

### Pattern — Diagnose-then-recover, in that order

**When to use:** any "scheduled flow not running" report where the admin hasn't yet pinned a cause.

**How it works:**

1. Confirm the schedule is *actually* registered. Setup → Scheduled Jobs OR `SELECT Id, CronJobDetail.Name, State, NextFireTime FROM CronTrigger WHERE CronJobDetail.Name LIKE '%FlowName%'`.
2. If no row exists → the flow was never successfully scheduled, OR a deployment aborted it. Re-schedule.
3. If a row exists → check `NextFireTime`. Convert from UTC to the scheduling-user's TZ. Confirm against expectations.
4. Check the most recent `AsyncApexJob` rows: `SELECT Id, Status, JobItemsProcessed, ExtendedStatus, CompletedDate FROM AsyncApexJob WHERE JobType = 'ScheduledApex' ORDER BY CompletedDate DESC LIMIT 20`. Status `Failed` with `ExtendedStatus` referencing inactive-user context → scheduling user deactivated.
5. If status is `Completed` but `JobItemsProcessed = 0` → schedule fires but filter matches no records.
6. If no `AsyncApexJob` rows for recent dates → schedule isn't firing at all. Most likely deactivated user or aborted CronTrigger.

**Why not the alternative:** Jumping straight to "let me rebuild the flow" wastes hours and doesn't fix the underlying issue (which is usually environmental, not in the flow definition). Diagnose first.

### Pattern — Re-schedule under a dedicated integration user

**When to use:** any time you find the original scheduling user has been deactivated, OR you're inheriting a flow whose scheduler is a real human admin.

**How it works:**

1. Provision (or use an existing) Integration User license — a dedicated user account never used for personal login, never deactivated as part of seat cleanup.
2. As a System Admin, log in as the integration user (or use User Switching).
3. Setup → Flows → open the target flow. If scheduled, deactivate first to clear the existing CronTrigger.
4. Re-activate the flow under the integration user's session. Confirm the schedule.
5. Verify in Setup → Scheduled Jobs that the new CronTrigger's `OwnerId` is the integration user.
6. Document in the org's "long-running scheduled work" runbook that this user is not eligible for license cleanup.

**Why not the alternative:** Scheduling under a real human's identity is the single most common cause of mid-flight schedule loss. Treat scheduled flows as production infrastructure — they need a permanent identity.

---

## Decision Guidance

| Symptom | First Check | Most Likely Cause |
|---|---|---|
| Flow active in Setup → Flows, never visible in Setup → Apex Jobs | Setup → Scheduled Jobs (NOT Apex Jobs) | Looking in the wrong place — scheduled flows surface in Scheduled Jobs |
| Flow ran for months then stopped on a specific date | Was a deployment done that day? | Deployment aborted CronTrigger of an invoked Apex class |
| Flow ran for months then stopped without deployment | Is the scheduling user still Active? | Scheduling user deactivated during license cleanup |
| Flow fires, AsyncApexJob shows Completed, but no records updated | `JobItemsProcessed` value | Start filter matches zero records — not a schedule problem |
| Flow scheduled for "6 AM Monday" runs at unexpected hour | Scheduling user's TZ vs org-viewer's TZ | Time-zone mismatch — schedule is in scheduler's TZ, not org default |
| Missed run on second Sunday in March / first Sunday in November | DST transition window | DST gap; "2 AM" doesn't exist on spring-forward |
| `AsyncApexJob.Status = 'Holding'` | Daily async-apex limit consumption | Org-wide async limit pressure, not a flow problem |

---

## Recommended Workflow

1. **Confirm the schedule is registered.** Run `SELECT Id, CronJobDetail.Name, State, NextFireTime, OwnerId FROM CronTrigger WHERE State = 'WAITING'` in Workbench. If your flow's name doesn't appear in `CronJobDetail.Name`, the schedule does not exist — go to step 6.
2. **Check the most recent execution.** Query `AsyncApexJob` filtered to the last 7 days, `JobType = 'ScheduledApex'`, ordered by `CompletedDate` desc. Look for `Status = 'Failed'` with `ExtendedStatus` text — that's the smoking gun.
3. **Check the scheduling user.** Once you have `CronTrigger.OwnerId`, look up the User record. If `IsActive = false`, you found it.
4. **Check time zones.** Compare the scheduling user's `TimeZoneSidKey` to the org's default TZ (Setup → Company Information). If they differ, your "6 AM" is not what people think.
5. **Run the flow manually with the same start filter.** Setup → Flows → Run. If it succeeds with the same data, the flow is fine — your problem is the schedule, not the logic. Use the bundled checker `scripts/check_scheduled_flow_not_running_debug.py` against retrieved metadata to enumerate scheduled flows and their start filters for cross-checking.
6. **Recover — re-schedule under integration user.** As described in the pattern above. Verify Setup → Scheduled Jobs shows a new row.
7. **Add monitoring.** A daily scheduled Apex (or another scheduled flow) that queries `CronTrigger` and emails the admin if any expected job is missing. This is the only reliable way to catch deployment-side-effect aborts before the next miss.

---

## Review Checklist

Run through these before declaring the issue fixed:

- [ ] CronTrigger row exists in `WAITING` state with the flow's name in `CronJobDetail.Name`
- [ ] `NextFireTime` (UTC) converts to the expected local time in the scheduling user's TZ
- [ ] Scheduling user's `IsActive = true` and is a dedicated integration user, not a real human
- [ ] Most recent `AsyncApexJob` row for the flow has `Status = 'Completed'`
- [ ] A monitoring job exists that alerts on missing CronTrigger rows
- [ ] Post-deploy runbook step exists to verify scheduled flows survived the deploy
- [ ] If DST is a concern, the schedule is set outside the 2 AM – 3 AM local window

---

## Salesforce-Specific Gotchas

Non-obvious behaviors covered fully in `references/gotchas.md`:

1. **Setup → Apex Jobs hides the flow's identity** — Schedule-Triggered Flow execution rows surface as `JobType = 'ScheduledApex'` with an internal Apex class name, not the flow's API name. Filtering by flow name in Setup → Apex Jobs returns nothing. Use Setup → Scheduled Jobs to find the schedule, then cross-reference by time.
2. **Deactivating the scheduling user does not abort their CronTrigger** — the trigger continues to attempt firing and produces failed `AsyncApexJob` rows.
3. **Deployment auto-aborts CronTrigger** — deploying an Apex class invoked by a scheduled flow auto-aborts the CronTrigger; the flow stays Active but the schedule silently dies.
4. **Daylight-savings spring-forward can skip a 2 AM run** — the 2 AM – 3 AM hour does not exist on the transition day.
5. **Sandbox refreshes copy CronTrigger over from production** — scheduled flows fire in the sandbox immediately unless aborted via SandboxPostCopy.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Diagnosis summary | One-paragraph root-cause: which of the eight known causes matched, with SOQL evidence |
| Recovery script | Anonymous Apex (or `scripts/check_scheduled_flow_not_running_debug.py` output) to re-schedule the flow under a permanent integration user |
| Monitoring snippet | SOQL or scheduled-Apex template that alerts when an expected CronTrigger row goes missing |

---

## Related Skills

- `flow/scheduled-flows` — design-time guidance for new scheduled flows (record scope, idempotency, when to escalate to Batch Apex). Use when the question is "should I build a scheduled flow", not "why isn't it firing."
- `flow/flow-time-based-patterns` — covers Scheduled Paths on record-triggered flows (different mechanism, different gotchas, different debug surface).
- `admin/batch-job-scheduling-and-monitoring` — broader async job monitoring including Batch Apex, Scheduled Apex, Queueable. Use when the issue spans multiple async types, not just scheduled flows.
- `devops/go-live-cutover-planning` — covers the deployment-aborts-CronTrigger pattern in full deployment-runbook context.
- `flow/flow-error-monitoring` — fault-path observability for flow interviews that fire but fail mid-execution.
