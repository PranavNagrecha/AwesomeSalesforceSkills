# Well-Architected Mapping: Connected Apps and Auth

## Pillars Addressed

### Security

Connected apps, integration users, and OAuth flows form a major part of the org's security boundary.

- Least-privilege auth reduces unnecessary access.
- Managed secrets and revocation procedures reduce incident blast radius.

### Operational Excellence

Auth choices affect how easily teams can deploy, rotate, and support integrations.

- Named Credential patterns reduce config drift across environments.
- Ownership and runbooks make auth failures supportable.

### Reliability

Stable token handling, clear endpoint management, and tested recovery steps improve integration uptime.

- Environment-safe config reduces deployment-time outages.
- Explicit flow choice reduces recurring auth failures.

## Pillars Not Addressed

- **User Experience** - user UX matters only when delegated auth is required; this skill is primarily about security and operability.
- **Performance** - the focus is authentication design and operability, not payload optimization or throughput tuning.

## Official Sources Used

- Salesforce Well-Architected Overview — security and operational framing for integration access
- REST API Developer Guide — OAuth and API usage context for connected-app design
- Integration Patterns — auth and system-boundary tradeoffs for integrations
- Salesforce Platform: New Connected Apps Can No Longer Be Created in Spring '26 (https://help.salesforce.com/s/articleView?id=005228017&language=en_US&type=1) — creation "prevented through both API and UI, with the exception of package installation," the Salesforce Support exception path, and that "all existing connected apps will continue to work"
- Package Connected Apps in Second-Generation Managed Packaging (https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/sfdx_dev_dev2gp_connected_app.htm) — "External Client Apps are the new and improved generation of connected apps"; the 1GP round-trip required to include a connected app in a 2GP package, and that `sf project retrieve start` / Metadata API `retrieve()` don't work for it
- Connected App to External Client App Migration (https://help.salesforce.com/s/articleView?id=xcloud.connected_app_to_external_client_app_migration.htm&language=en_US&type=5) — the Migrate to External Client App button in App Manager, that "migration preserves your consumer key and secret," and the eligibility conditions (local app; User Provisioning, Custom Apex Handlers, Canvas, Dynamic Client Registration, and Triple DES for SAML disabled)
- Prepare for MFA Enforcement for All Employee Users (https://help.salesforce.com/s/articleView?id=000396727&language=en_US&type=1) — the enforcement scope: "all employee logins, including direct UI and Single Sign-On (SSO), across both production and sandbox orgs"
- Prepare for Phishing-Resistant MFA Enforcement for Privileged Users including Admins (https://help.salesforce.com/s/articleView?id=005321563&language=en_US&type=1) — the privileged population (System Administrator profile; Modify All Data, View All Data, Customize Application, Author Apex) and that "apps using JWT Bearer or Client Credentials flows are unaffected, as no UI login is required"
- Prepare for Connected App Usage Restrictions Change (https://help.salesforce.com/s/articleView?id=005132365&language=en_US&type=1) — the Connected Apps OAuth Usage page, Install and Block actions, the "early September 2025" uninstalled-app restriction, and that the Approve Uninstalled Connected Apps permission "is automatically assigned to the System Administrator standard profile"
- Manage OAuth Access Policies for a Connected App (https://help.salesforce.com/s/articleView?id=xcloud.connected_app_manage_oauth.htm&language=en_US&type=5) — Permitted Users options and the access loss when switching to admin-approved
- OAuth 2.0 Username-Password Flow for Special Scenarios (https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_username_password_flow.htm&language=en_US&type=5) — "if your org is created in Summer '23 or later, the username-password flow is blocked by default"; web server flow with PKCE and client credentials as alternatives
- Salesforce Platform: Migrate from OAuth Username-Password to Client Credentials Flow (https://help.salesforce.com/s/articleView?id=000886201&language=en_US&type=1) — that Salesforce "is deprecating this flow," the Run As user configuration, the grant_type swap, that "the client credentials flow doesn't support calls to login.salesforce.com or test.salesforce.com," and JWT bearer when the client uses multiple usernames in a single org
- Platform SOAP API login() Retirement (https://help.salesforce.com/s/articleView?id=005132110&language=en_US&type=1) — "retiring SOAP API login() in API versions 31.0 through 64.0 with the Summer '27 release"
- Create a Connected App, Mobile SDK Development Guide (https://developer.salesforce.com/docs/platform/mobile-sdk/guide/connected-apps-howto.html) — confirms the creation freeze on a renderable developer.salesforce.com page: "Connected apps creation is restricted as of Spring '26," "You can continue to use existing connected apps during and after Spring '26," "we recommend using external client apps instead," and "If you must continue creating connected apps, contact Salesforce Support" (verified 2026-08-13)
- Create an External Client App in Your Org, Salesforce DX Developer Guide (https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_eca.htm) — the DX split that qualifies "always use an ECA": "You're required to create an external client app when authorizing the org with the org login jwt command" versus "If you're authorizing a Dev Hub org and plan to create scratch orgs or sandboxes with the org create scratch|sandbox commands, then you create a connected app instead," plus the Flow Enablement → Enable JWT Bearer Flow step (verified 2026-08-13)
- ExternalClientApplication, Metadata API Developer Guide (https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_externalclientapplication.htm) — "ExternalClientApplication components are available in API version 59.0 and later," the deploy-time floor for ECA metadata (verified 2026-08-13)
- Create an External Client App, Hosted MCP Servers (https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide/create-external-client-app.html) — "You can't create External Client Apps directly in scratch orgs using the Setup UI" and the documented workaround: "create the External Client App in a developer hub org, add it to a package, and install the package in the target scratch org" (verified 2026-08-13)
