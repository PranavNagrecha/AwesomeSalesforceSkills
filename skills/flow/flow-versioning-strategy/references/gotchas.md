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

## 4. Subflow Version Is Resolved At Run Time, Not At Activation

Resolution is late, not early: "If a child flow has multiple versions,
the parent flow runs the child flow's active version. If a child flow
has no active version, the parent flow runs the latest version." The
parent holds a reference to the child flow, not to a pinned version
number, so activating a new child version changes the behaviour of
every already-active parent on its next interview — with no redeploy
and no re-activation of the parent.

Two consequences worth planning for:

- A subflow edit is a **production change to every caller**. Search
  metadata for `<flowName>` references before activating a new child
  version; the blast radius is not visible from the child's own screen.
- The "no active version" fallback is the trap. Deactivating a child
  flow does not stop callers — it silently drops them onto the latest
  (possibly unfinished, never-activated) draft. Deleting the version is
  the only way to stop it being reachable, and Gotcha 1 still applies to
  paused interviews pinned to it.

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
