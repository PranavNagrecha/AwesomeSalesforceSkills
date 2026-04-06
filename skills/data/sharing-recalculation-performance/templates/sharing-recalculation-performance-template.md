# Sharing Recalculation Performance — Work Template

Use this template when planning or executing structural sharing changes that will trigger a recalculation job.

## Scope

**Skill:** `sharing-recalculation-performance`

**Request summary:** (fill in what the user asked for — e.g., "tighten OWD on Account from Public Read Only to Private")

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Affected objects and record counts:**
- **Type of change (OWD direction, sharing rule add/remove, role/group edit):**
- **Apex managed sharing in use on any affected object?** (yes/no — if yes, list object and sharing reason names)
- **Registered recalculation batch class for each Apex sharing reason:** (class name or "none — MUST RESOLVE BEFORE PROCEEDING")
- **Current async job queue depth:**
- **Maintenance window available?** (yes/no — start/end time)

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1 — Batch Multiple Structural Changes with Defer Sharing Calculations
- [ ] Pattern 2 — OWD Tightening with Apex Managed Share Protection
- [ ] Pattern 3 — Role Hierarchy Restructuring in Maintenance Window

Reason for selected pattern: (fill in)

## Staged Change Plan

List all structural changes to apply under the deferral window, in order:

1.
2.
3.

## Checklist

- [ ] All structural changes identified and listed above before enabling deferral
- [ ] Every Apex sharing reason on affected objects has a registered recalculation batch class
- [ ] OWD tightening changes scheduled during maintenance window (not business hours)
- [ ] Defer Sharing Calculations enabled before first structural change
- [ ] All structural changes applied while deferred
- [ ] Defer Sharing Calculations disabled — recalculation job started
- [ ] Async job queue monitored to completion
- [ ] Apex share rows verified on sample records post-recalculation
- [ ] Setup Audit Trail reviewed to confirm all expected changes captured

## Notes

Record any deviations from the standard pattern and why.
