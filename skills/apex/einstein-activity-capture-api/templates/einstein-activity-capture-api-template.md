# Einstein Activity Capture API — Work Template

Use this template when working on tasks that involve reading EAC-synced activity data from Apex, querying ActivityMetric, or advising on EAC reporting.

## Scope

**Skill:** `einstein-activity-capture-api`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before writing any code or recommendations.

- **EAC storage model:** [ ] Legacy EAC (external store, ActivityMetric only) / [ ] Sync Email as Salesforce Activity (email stored as standard Task + EmailMessage) / [ ] Unknown — needs confirmation
- **Retirement audit done?** [ ] Searched Apex, flows and validation rules for `ActivityMetric` and the six A360 objects (`UnifiedEmail`, `UnifiedEmailParticipant`, `UnifiedMeeting`, `UnifiedMeetingParticipant`, `UnifiedTask`, `UnifiedTaskParticipant`) — all retire Spring '27 (February 2027), and Activity Metrics fields return null before then. Hits found: ____
- **Required data shape:** [ ] Aggregate counts only / [ ] Individual activity records needed
- **Users with connected accounts:** How many org users have active EAC-connected Gmail or Outlook accounts? Partial coverage affects data completeness.
- **Sandbox vs production:** [ ] Working in sandbox (no live EAC data) / [ ] Production (live EAC data possible)
- **Known constraints:** (list governor limits, edition restrictions, or feature availability notes)
- **Failure modes to watch for:** (e.g., empty results for unconnected accounts, read-only restriction on ActivityMetric DML)

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Aggregate `Task` / `EmailMessage` grouped by Account or Opportunity — the durable pattern on Sync Email as Salesforce Activity
- [ ] Aggregate count query via `ActivityMetric` — legacy EAC only; log the Spring '27 migration debt in the same commit
- [ ] `UnifiedActivity` query — use only if org has enhanced EAC storage provisioned
- [ ] Scheduled batch for downstream logic — legacy EAC only, where no trigger path exists
- [ ] Ordinary `Task` / `EmailMessage` trigger — valid on Sync Email as Salesforce Activity; the trigger always runs implicitly `without sharing` and cannot declare otherwise, so scope the read in code, and set the access mode explicitly (`WITH USER_MODE` / `WITH SYSTEM_MODE`) on every query in the trigger and its handler
- [ ] EAC report type guidance — use when reporting requirements are in scope

Describe why this pattern fits the use case:

## Checklist

- [ ] Confirmed EAC storage model before choosing query surface.
- [ ] Read surface matches the confirmed architecture: `ActivityMetric` / `UnifiedActivity` on legacy EAC, standard `Task` / `EmailMessage` on Sync Email as Salesforce Activity.
- [ ] No **new** code built on `ActivityMetric` or the six A360 `Unified*` objects; every existing reference logged against the Spring '27 date. (`UnifiedActivity` is not on the published retirement list — verify org availability before relying on it either way.)
- [ ] Trigger assumptions match the architecture (none on legacy EAC; ordinary Task/EmailMessage triggers on the new one).
- [ ] No production DML targeting `ActivityMetric`.
- [ ] Report requirements use **Activities with Accounts** / **Activities with Opportunities**; the dedicated EAC report type only on legacy orgs, with the retirement noted.
- [ ] Code guards against empty results (zero-default, not exception).
- [ ] Test class seeds `ActivityMetric` in `@isTest` context rather than relying on sandbox data.
- [ ] Code comments document the EAC storage model assumption.

## Notes

Record any deviations from the standard pattern and why, including any EAC edition-specific behavior observed.
