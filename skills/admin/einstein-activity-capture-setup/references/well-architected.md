# Well-Architected Notes — Einstein Activity Capture Setup

## Relevant Pillars

- **Security** — EAC has broad access to user email and calendar data. The auth model chosen (User-Level vs Org-Level OAuth), the exclusion domain configuration, and the Private Activities setting all directly determine what data enters Salesforce and who can see it. An improperly configured EAC deployment can inadvertently expose sensitive communications (legal, HR, executive) to unauthorized users or persist data in Salesforce that should never have entered the system. Security review and Legal/Compliance sign-off on exclusion rules is a mandatory pre-go-live gate, not an optional step.

- **Operational Excellence** — EAC Configuration profiles are the primary operational control surface. Multiple profiles allow different policies for different user groups. Org-Level OAuth reduces ongoing support burden by eliminating per-user token management. Monitoring Unresolved Items and sync health as a recurring operational task prevents silent match failures from degrading data quality over time. Documentation of which users are on which Configuration profile is essential for troubleshooting and onboarding new reps.

- **Reliability** — For User-Level OAuth, individual user token expiry or password changes break that user's sync independently without alerting the admin. Org-Level OAuth is more reliable at scale because a single service account manages the connection, but requires the Microsoft 365 AAD consent to remain valid. Regular sync health checks (weekly during the first month, monthly thereafter) catch silent failures before they cause significant data gaps. Contact email address data quality directly impacts sync reliability — poor data quality causes persistent match failures that are invisible to users unless the Unresolved Items queue is monitored.

- **Scalability** — As of Summer '25, EAC email storage consumes org storage. A 1000-rep org syncing 40 emails per day can generate 2–5 GB/month in EmailMessage storage depending on attachments. Scalability planning must include a storage archival or retention policy. Configuration profiles scale horizontally — there is no enforced limit on the number of profiles, but each user can belong to only one active profile.

- **User Experience** — EAC's value to end users is automatic activity capture that eliminates manual logging. If sync fails silently, reps lose trust in the Activity Timeline and revert to manual entry (defeating the purpose). Ensuring that EAC setup is complete and verified before communicating to reps that sync is live avoids a negative first impression. The Unresolved Items queue is the UX safety valve — reps can manually associate unmatched activities, but a high Unresolved Items count signals a data quality or configuration problem that should be fixed at the admin level.

## Architectural Tradeoffs

**User-Level OAuth vs Org-Level OAuth:** User-Level OAuth is simpler to set up but requires per-user authorization and is prone to individual token failures. Org-Level OAuth requires Microsoft 365 AAD Global Admin involvement and only works for Microsoft 365, but scales reliably. For orgs with more than 50 users on Microsoft 365, Org-Level OAuth is the better architectural choice. For smaller orgs or Google Workspace, User-Level OAuth is the only or most practical option.

**Single Configuration profile vs Multiple profiles:** A single Configuration profile is simpler to manage but cannot accommodate different privacy policies or sync scopes for different user groups. Multiple profiles add management complexity but allow granular control. The right tradeoff depends on whether the org has distinct user populations with meaningfully different requirements (e.g., executives needing privacy, sales managers needing broader calendar access, field reps needing email only).

**Full bi-directional calendar sync vs one-directional:** Bi-directional calendar sync ensures Salesforce-created events appear in the user's email calendar, which improves rep adoption. However, it requires reps to trust Salesforce as the authoritative source of calendar truth, which can cause friction if reps edit events from both sides. One-directional (email-client to Salesforce) is safer for initial rollout, with bi-directional enabled after change management has prepared reps.

## Anti-Patterns

1. **Skipping the exclusion domain review** — Going live with EAC without a Legal/Compliance-reviewed exclusion list means sensitive emails (legal hold, HR matters, executive communications with board members) enter Salesforce records and become visible to users with record access. Once synced, removal requires manual cleanup. This is both a security and legal risk.

2. **Treating EAC as a set-and-forget feature** — EAC requires ongoing operational attention: monitoring Unresolved Items, checking for users whose tokens have expired (User-Level OAuth), reviewing storage growth, and auditing Configuration assignments when users change roles or leave the org. Orgs that treat EAC as "enable once, never revisit" experience data quality degradation over time — gaps in the Activity Timeline, stale token failures, and rising Unresolved Items queues.

3. **Assuming pre-Summer '25 storage behavior persists** — Prior to Summer '25, EAC data was outside org storage. Architectural decisions (not buying storage, not planning archival) made under that assumption are invalid for orgs on Summer '25+. Any EAC design document or enablement guide that does not address storage must be reviewed against the current release behavior.

## Official Sources Used

- Einstein Activity Capture Setup — https://help.salesforce.com/s/articleView?id=sf.einstein_sales_activity_capture.htm
- Considerations for Setting Up Einstein Activity Capture — https://help.salesforce.com/s/articleView?id=sf.einstein_sales_activity_capture_consideration.htm
- Einstein Activity Capture Configuration Profiles — https://help.salesforce.com/s/articleView?id=sf.einstein_sales_activity_capture_configuration.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
