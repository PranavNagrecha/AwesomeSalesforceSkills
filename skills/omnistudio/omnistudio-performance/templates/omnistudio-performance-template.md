# OmniStudio Performance Review — Work Template

Use this template when diagnosing or fixing performance issues in OmniStudio assets.

---

## Scope

**Skill:** `omnistudio-performance`

**Asset(s) under review:** (OmniScript name, FlexCard name, Integration Procedure name, or DataRaptor name)

**Request summary:** (what the user or team reported — e.g., "Submit step takes 5 seconds", "FlexCard page loads slowly")

**Environment:** (Sandbox / Production / Scratch Org)

---

## Context Gathered

Answer these before proposing any fix:

- **Asset type affected:** [ ] OmniScript [ ] FlexCard [ ] Integration Procedure [ ] DataRaptor
- **Symptom location:** (initial load / step transition / submit / card render)
- **Observed latency:** (e.g., "4–6 seconds on step 3")
- **OmniScript runtime:** [ ] LWC Runtime [ ] Legacy Managed Package [ ] Unknown
- **Current caching:** (is DataRaptor caching enabled? what is the cache key?)
- **Number of remote calls per step:** (count Action elements per step)
- **External callouts in play:** [ ] Yes [ ] No — (if yes, which services?)

---

## Root Cause Diagnosis

Check each applicable cause:

- [ ] Multiple independent DataRaptor calls on the same step (serialized round trips)
- [ ] DataRaptor caching disabled on read-only data
- [ ] Integration Procedure runs synchronously but result is not needed in the UI
- [ ] FlexCard fetches data per-card instead of aggregating in parent IP
- [ ] Lazy loading not configured on non-critical steps
- [ ] Running on legacy Managed Package runtime instead of LWC runtime
- [ ] External callout latency blocking user path

---

## Recommended Fixes

| Root Cause | Fix | Priority |
|---|---|---|
| (describe root cause) | (describe fix) | High / Medium / Low |

---

## Implementation Plan

### Fix 1: (name)

**Steps:**

1.
2.
3.

**Verification:** (how to confirm the fix works — OmniStudio debug mode timings, before/after comparison)

---

### Fix 2: (name if applicable)

**Steps:**

1.
2.

**Verification:**

---

## Checklist Before Sign-Off

- [ ] Each OmniScript step fires at most one network round trip.
- [ ] DataRaptor caching is enabled where data does not change mid-session.
- [ ] Cache keys are record-specific and will not cross-pollinate across accounts or users.
- [ ] Fire-and-forget IPs are invoked asynchronously and not read back.
- [ ] Lazy loading is enabled on steps unlikely to be reached by most users.
- [ ] FlexCard data aggregation happens in the parent IP, not per-card.
- [ ] OmniScript is running in LWC runtime.
- [ ] Async IPs have error handling (Platform Event, error log record, or monitoring).
- [ ] Performance tested with production-representative data volumes.

---

## Notes

(Record any deviations from the standard pattern, constraints, or decisions made during this review.)
