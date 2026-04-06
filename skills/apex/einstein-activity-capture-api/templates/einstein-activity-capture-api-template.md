# Einstein Activity Capture API — Work Template

Use this template when working on tasks that involve reading EAC-synced activity data from Apex, querying ActivityMetric, or advising on EAC reporting.

## Scope

**Skill:** `einstein-activity-capture-api`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before writing any code or recommendations.

- **EAC storage model:** [ ] Standard EAC (external store, ActivityMetric only) / [ ] Write-Back enabled (Summer '25+) / [ ] Unknown — needs confirmation
- **Required data shape:** [ ] Aggregate counts only (ActivityMetric sufficient) / [ ] Individual activity records needed (requires UnifiedActivity or Write-Back)
- **Users with connected accounts:** How many org users have active EAC-connected Gmail or Outlook accounts? Partial coverage affects data completeness.
- **Sandbox vs production:** [ ] Working in sandbox (no live EAC data) / [ ] Production (live EAC data possible)
- **Known constraints:** (list governor limits, edition restrictions, or feature availability notes)
- **Failure modes to watch for:** (e.g., empty results for unconnected accounts, read-only restriction on ActivityMetric DML)

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Aggregate count query via `ActivityMetric` — use when need email/meeting counts per contact/lead
- [ ] `UnifiedActivity` query — use only if org has enhanced EAC storage provisioned
- [ ] Scheduled batch for downstream logic — use when reaction to new EAC activity is needed (no trigger path)
- [ ] EAC report type guidance — use when reporting requirements are in scope

Describe why this pattern fits the use case:

## Checklist

- [ ] Confirmed EAC storage model before choosing query surface.
- [ ] All EAC reads use `ActivityMetric` or `UnifiedActivity` — not `Task`, `Event`, or `EmailMessage` for synced records in non-Write-Back orgs.
- [ ] No Apex trigger designed to fire on EAC sync events.
- [ ] No production DML targeting `ActivityMetric`.
- [ ] Report requirements use EAC report type, not standard Activities.
- [ ] Code guards against empty results (zero-default, not exception).
- [ ] Test class seeds `ActivityMetric` in `@isTest` context rather than relying on sandbox data.
- [ ] Code comments document the EAC storage model assumption.

## Notes

Record any deviations from the standard pattern and why, including any EAC edition-specific behavior observed.
