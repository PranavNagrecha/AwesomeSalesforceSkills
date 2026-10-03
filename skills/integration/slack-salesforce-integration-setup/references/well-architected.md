# Well-Architected Notes — Slack Salesforce Integration Setup

## Relevant Pillars

- **Security**: What a shared record link reveals is set by the link unfurling data sharing option and the URL Unfurling Slack Record Layout (or the compact layout). The two "data viewable" options show data according to the Default Render User or the poster, not each channel member. Govern the option and the layouts per sensitive object; Government Cloud orgs cannot connect, and the apps are not FedRAMP or HIPAA certified.
- **Operational Excellence**: The three-step handshake (request and activate in Slack, approve in Salesforce) requires coordinated admin roles across two platforms. Documenting the setup process, role requirements, and channel governance policies is essential for operational sustainability.
- **Reliability**: The connection breaks when the org URL changes (the connection must be updated) and features may fail under Salesforce IP restrictions. Removing an app from a workspace deletes all user mappings. Monitor the connection after network and My Domain changes. UNVERIFIED (2026-10-03): an earlier version said token revocation by a Slack admin breaks the integration silently; the fetched sources do not describe that case.

## Architectural Tradeoffs

**Salesforce for Slack App vs. Custom Slack App:** The managed Salesforce for Slack app provides out-of-the-box record sharing, search, and notifications without code. A custom Slack app provides full control over UX, data exposure, and business logic but requires significant development effort. For standard sales productivity use cases, the managed app is sufficient. For deeply customized workflows, consider a custom app via Slack SDK.

**Record Preview Governance vs. No Sharing:** Completely disabling record URL sharing in Slack eliminates the data exposure risk but removes a core productivity feature. A policy-based approach (governance rules defining which object types can be shared in which channel types) balances security and usability.

## Anti-Patterns

1. **Leaving a Data-Viewable Unfurl Option on Sensitive Objects**: The channel sees the Default Render User's or poster's view of the record. Use preview-button options or restricted Slack Record Layouts, and publish a channel policy.

2. **Attempting Government Cloud Connection** — Government Cloud org connection to Slack is not supported. Proposing it as a configuration option wastes implementation effort. Identify org type early and route to alternative integration patterns.

3. **Skipping User Onboarding After Org Connection** — The org-level connection alone does not authorize individual users. Skipping the user personal account connection step results in poor adoption and support tickets claiming the integration "doesn't work."

## Official Sources Used

Fetched and read on 2026-10-03 unless marked.

- Slack Integrations, Spring '26 (Salesforce): Enable Salesforce for Slack Integrations (user permissions, Government Cloud note, setup sections), Set Record Detail Security for Your Salesforce Apps, Salesforce Apps for Slack Limitations (block limit, FedRAMP and HIPAA, Blackjack), Add Apps in Your Personal Slack Sidebar, Unfurling Slack Record Layouts with Data Sharing Options, Create a New URL Unfurling Slack Record Layout, Authorize Unfurling Links that Show Record Data. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/slack_apps.pdf
- Slack Help Center, Connect Salesforce and Slack (three steps, roles, Government Cloud, IP restrictions, org URL change, Unified Employee license, up to 20 additional orgs, available on all plans). https://slack.com/help/articles/30754346665747-Connect-Salesforce-and-Slack
- Slack Help Center, Configure Salesforce for use with Slack (the Slack-built app no longer supports new installations). https://slack.com/help/articles/360044038514-Configure-Salesforce-for-use-with-Slack
- Salesforce Well-Architected: Secure (Trusted), archived 2026-07-11. http://web.archive.org/web/20260711090005/https://architect.salesforce.com/docs/architect/well-architected/guide/secure.html
- Salesforce Well-Architected Overview, archived 2026-06-16. http://web.archive.org/web/20260616115029/https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Listed by an earlier version of this skill; help.salesforce.com returns a script shell and was not re-read: Connect the Salesforce for Slack App to a Salesforce Org https://help.salesforce.com/s/articleView?id=sf.slack_apps_digital_hq_setup.htm
