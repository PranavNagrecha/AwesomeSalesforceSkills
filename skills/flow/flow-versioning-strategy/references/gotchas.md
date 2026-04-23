# Flow Versioning — Gotchas

## 1. Paused Interviews Pin To Their Version

A paused interview always resumes on the version it started. If you
delete that version, the interview fails. Drain before delete.

## 2. "Obsolete" Versions Still Hold Paused Interviews

Status `Obsolete` does not automatically delete. Paused interviews can
still resume on obsolete versions. Check before cleanup.

## 3. Activation Is Per-Org

Activating a flow in the repo does nothing. Activation is per-org
metadata state. Track active version per environment.

## 4. Subflow Version Is Resolved At Activation

A subflow call resolves to whatever active version of the subflow
existed when the parent version was activated. Updating the subflow
activates for new interviews but doesn't re-bind existing paused.

## 5. Variable Rename Silently Breaks Callers

Renaming an output variable doesn't error in the flow builder but breaks
Apex/LWC/other-flow callers on the next invocation. Use search across
metadata before renaming.

## 6. Platform Hard Limit 50 Versions Per Flow

Hit the limit = cannot create new version without deleting old. Keeping
a clean version list prevents a panic-delete under pressure.

## 7. Rollback = Activate Prior, Not Redeploy

Rollback path is one click: activate prior inactive version. Redeploying
old metadata is slower and error-prone.

## 8. Scheduled Flows Reference Version At Run

Scheduled flow jobs pick the active version at run. Changing the schedule
keyed off old behaviour without planning can surprise.
