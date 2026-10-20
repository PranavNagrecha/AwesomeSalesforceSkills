# Scheduled Apex Failure Detection And Monitoring — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `scheduled-apex-failure-detection-and-monitoring`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md here.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Name the detection layers chosen from SKILL.md Core Concepts (try-catch logging, `BatchApexErrorEvent`, `AsyncApexJob` watcher) and the job shape each one covers.

## Checklist

Tick each Recommended Workflow step from SKILL.md as you complete it.

- [ ] Scheduled jobs inventoried and classified from `CronTrigger`
- [ ] Every `execute()` body wrapped in try-catch with structured logging
- [ ] `Database.RaisesPlatformEvents` on every business-critical batch class
- [ ] `AsyncApexJob` watcher covers Failed/Aborted, stuck Queued/Holding, and Completed with `NumberOfErrors > 0`
- [ ] Notification channel chosen and idempotent
- [ ] Runbook linked from every alert payload
- [ ] Controlled failure injected in a sandbox and every alert path confirmed

## Notes

Record any deviations from the standard pattern and why.
