# Slack Workflow Builder — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `slack-workflow-builder`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Slack workspace / trigger:** (shortcut, reaction, channel event, schedule, external start)
- **Salesforce org connection:** (confirmed connected org, admin who owns Slack connector policy)
- **Target Flow:** (API name, process type AutoLaunchedFlow, active status, input and output variables)
- **Whose account each connector step uses:** (builder's account / the person using the workflow; for coded workflows END_USER or DEVELOPER)
- **Slack Connect exposure:** (external people allowed? connector steps they can run?)
- **Volume / bulk scenario:** (expected peak runs per hour, public vs private channel)

## Approach

Which pattern from SKILL.md applies (Slack→Salesforce shortcut, enrichment, or anti-pattern avoidance)? Why?

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Autolaunched + Active target for **Run a Flow** (if used)
- [ ] Account choice per connector step documented; workflow managers added
- [ ] Mappings null-safe; no unnecessary sensitive fields returned to Slack
- [ ] Direction validated (Slack-initiated vs Salesforce-initiated)
- [ ] Bulk or import path considered
- [ ] Failure path visible to the Slack user (message or log)

## Notes

Record Flow API name changes, Slack workflow publication IDs, or any deployment coupling discovered during the change.
