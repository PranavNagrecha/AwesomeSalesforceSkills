# Flow Deployment — Gotchas

## 1. `FlowDefinition` vs `Flow` Metadata

`Flow` stores a version; `FlowDefinition` tracks which version is active.
Deploying `Flow` alone does not always flip activation.

## 2. "Deploy As Active" Varies By Tool

SFDX, SF CLI v2, change sets, and Package deploys have subtly different
defaults for auto-activation. Confirm for your tool.

## 3. Paused Interviews Pin To Version

A paused interview will resume into the exact version that paused it.
Deleting that version kills the interview.

## 4. Auto-Launched Flows From Apex Use The Active Version

So an Apex test that spins up a flow will use whatever is active at test
time. Test isolation requires discipline.

## 5. "Inactive" Still Runs If Invoked By Apex

An "inactive" flow can still be launched by `Flow.Interview.createInterview`
depending on how the developer wrote it. Inactive ≠ untouchable.

## 6. Package Deploys Can Overwrite Active Version

Installing an updated managed package can bump the active version
silently. Review package upgrade notes.

## 7. Rollback Can Affect Scheduled Interviews

Rolling back to an older version mid-day can orphan the current schedule;
the schedule points at the current version id.
