# Well-Architected Notes — Journey Builder Administration

## Relevant Pillars

- **Reliability** — Journey versioning, exit criteria scheduling, and re-entry policy directly affect whether contacts receive the intended messages and exit the journey at the correct time. Misconfigured exit criteria or silent re-entry blocking creates unreliable journey behavior that is difficult to debug post-launch.
- **Operational Excellence** — Journey Builder's immutable versioning model demands operational discipline: thorough testing before publish, version documentation, and a governance process for managing in-flight contacts across versions. Journeys without version strategy accumulate orphaned versions and contradictory analytics.
- **Performance** — Large journey populations (millions of contacts) with complex attribute splits and high-frequency wait intervals can create evaluation lag at entry and activity steps. Entry source data extension schema and indexing affect how quickly contacts are ingested. Exit criteria evaluation at scale can queue behind other scheduled jobs.
- **Security** — Journey Builder operates within Marketing Cloud Business Unit boundaries. Ensuring the correct BU owns each journey prevents cross-BU data exposure. API Event entry sources require secure token management for the REST API calls that inject contacts. Contact data flowing through Update Contact activities can write back to Salesforce CRM objects — field-level security on those objects must be validated.
- **User Experience** — From the subscriber's perspective, well-architected journeys deliver the right message at the right time. Goal-based early exits, re-entry intervals, and channel coordination (Email + SMS without overlap) determine whether the journey feels relevant or intrusive.

## Architectural Tradeoffs

**Goal vs. Exit Criteria for conversion removal:** Goals provide real-time conversion exit and analytics attribution. Exit Criteria provide scheduled batch removal. Using only Exit Criteria for conversion tracking underreports goal conversion metrics. Using only Goals for removal means contacts who are between activity steps (e.g., in a Wait activity) may not be evaluated for exit until the next step fires. The recommended architecture is to configure both: Goal for metrics and step-level evaluation, Exit Criteria as a belt-and-suspenders removal mechanism.

**Single journey version with complex splits vs. multiple simpler journeys:** A single journey with many attribute split arms is easier to manage from a versioning perspective (one object to publish and monitor) but harder to test comprehensively and more likely to route contacts to the Default arm silently when data is missing. Multiple simpler journeys with dedicated entry Data Extensions (one per segment) are easier to test and diagnose but require more operational overhead to keep entry populations mutually exclusive. For journeys with more than four split arms, evaluate whether separate journeys per segment is a cleaner design.

**Scheduled Data Extension entry vs. real-time API Event entry:** Scheduled DE entry introduces entry timing lag (contacts enter on the next evaluation schedule, not immediately on the triggering event). API Event entry is real-time but requires API infrastructure, error handling for failed injection calls, and a process to handle contacts injected with incomplete data (missing split attribute fields, for example). Choose based on the business timing requirement: if near-instant entry matters, build the API infrastructure; if batch nightly entry is acceptable, scheduled DE entry is simpler to maintain.

## Anti-Patterns

1. **Using Exit Criteria as the only conversion removal mechanism** — Exit Criteria exits are classified in Journey Analytics as "Exit Criteria exits," not as goal conversions. A journey that uses only Exit Criteria for conversion tracking produces a goal conversion rate of zero even when the campaign drove purchases. The correct pattern is to configure a Goal for the conversion event and use Exit Criteria as a supplemental removal mechanism. Always ensure the conversion event is captured in both places.

2. **Editing a live journey version in place** — Journey Builder does not allow editing a published version's activities. Practitioners who attempt to "fix" a live journey by stopping it, recreating the same version, and relaunching inadvertently restart the journey entry, lose in-flight contact state, and corrupt analytics continuity. The correct pattern is to create a new version from the existing journey, make the changes, publish the new version, and let the original version drain its in-flight contacts before stopping it.

3. **Launching without Test Mode validation of all split arms** — Practitioners who test only the "happy path" through a journey miss misconfigured split conditions, missing Default arm activities, or broken email activities on less-traveled arms. The correct pattern is to create a test contact for every distinct split arm and the goal exit path before publishing, confirming each contact exits through the expected path without errors.

## Official Sources Used

- Salesforce Help — Journey Builder Entry Sources: https://help.salesforce.com/s/articleView?id=sf.mc_jb_entry_sources.htm
- Salesforce Help — Journey Builder Goals: https://help.salesforce.com/s/articleView?id=sf.mc_jb_goals.htm
- Salesforce Help — Exit Criteria in Journey Builder: https://help.salesforce.com/s/articleView?id=sf.mc_jb_exit_criteria.htm
- Salesforce Help — Decision Split Activities: https://help.salesforce.com/s/articleView?id=sf.mc_jb_decision_splits.htm
- Salesforce Help — Journey Builder Wait Activities: https://help.salesforce.com/s/articleView?id=sf.mc_jb_wait_activities.htm
- Salesforce Help — Journey Versions: https://help.salesforce.com/s/articleView?id=sf.mc_jb_journey_versions.htm
- Salesforce Help — Journey Builder Test Mode: https://help.salesforce.com/s/articleView?id=sf.mc_jb_test_mode.htm
- Salesforce Help — Journey Analytics: https://help.salesforce.com/s/articleView?id=sf.mc_jb_analytics_dashboard.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
