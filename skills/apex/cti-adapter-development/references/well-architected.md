# Well-Architected Notes — CTI Adapter Development

## Relevant Pillars

- **Security** — The adapter page runs in a browser iframe and communicates cross-origin with Salesforce. The adapter domain must be on the CORS Allowed Origins List and CSP Trusted Sites. Sensitive telephony credentials (SIP passwords, API tokens) must never be hardcoded in the adapter JavaScript served from the `AdapterUrl`; use `CustomSettings` in `callcenter.xml` to pass environment-specific values that are read at runtime via `sforce.opencti.getCallCenterSettings`. The adapter should run only over HTTPS.
- **Reliability** — The adapter must check `response.success` on every Open CTI API callback. Silent failures in `saveLog`, `screenPop`, or `enableClickToDial` cause call records to be lost or agent workflows to break without obvious errors. Error states should surface to the agent via the softphone panel UI, not only the browser console.
- **Operational Excellence** — Call logging via `saveLog` creates auditable Task activity records that supervisors and analytics can consume. A well-designed adapter logs `CallDurationInSeconds`, `CallType`, `Subject`, and the related record ID on every call. This enables call volume reporting in Salesforce Reports without a separate data warehouse.
- **Performance** — The softphone panel is rendered in a persistent iframe in the utility bar. Keep the adapter page lightweight — avoid large JavaScript bundles and unnecessary polling. Use `setSoftphonePanelHeight` to size the panel correctly on load rather than relying on default heights that may clip the UI.
- **Scalability** — Open CTI is a per-session browser API. There is no server-side component that can become a bottleneck. However, if the adapter makes Salesforce REST API callouts (e.g., for ANI lookup during inbound calls), these callouts are subject to Salesforce API limits per org and per user. Batch or high-volume call centers should confirm API limit headroom before deploying.

## Architectural Tradeoffs

**Open CTI vs Service Cloud Voice:**
Open CTI is the correct choice for any third-party telephony system that is NOT Amazon Connect, and for organizations that want to host and control the softphone adapter code themselves. Service Cloud Voice is the correct choice when Amazon Connect is the telephony provider and the organization wants native real-time transcription, Einstein Conversation Insights, and unified Omni-Channel routing. These two are mutually exclusive paths for a given deployment; do not mix them.

**Adapter-hosted vs Salesforce-managed credentials:**
Adapter pages must be served from an external HTTPS host. Credentials or configuration values that change per environment (sandbox vs production) should be stored in `callcenter.xml` `CustomSettings` and retrieved at runtime, not hardcoded in the adapter JS. This avoids separate adapter deployments per environment.

**saveLog vs custom Apex REST:**
Using `saveLog` (Open CTI API) is simpler than writing a separate Apex REST endpoint and calling it from the telephony vendor's backend. `saveLog` runs in the agent's browser session with their permissions and creates the Task under their user record. A backend Apex REST approach is only warranted when the telephony vendor needs to log calls independently of the agent's browser session (e.g., for calls that were abandoned before the agent answered).

## Anti-Patterns

1. **Loading the Open CTI script manually** — Adding a `<script src="/support/api/60.0/lightning/opencti_min.js">` tag to the adapter page and expecting it to work. The `sforce.opencti` namespace is injected by the platform into the adapter iframe context automatically. Attempting to load it manually results in either a 404 or a duplicate conflicting namespace.

2. **Storing telephony credentials in the adapter JavaScript** — Including SIP passwords, vendor API keys, or tenant IDs directly in the adapter HTML/JS file served from the `AdapterUrl`. These files are accessible to anyone who can load the URL. Use `callcenter.xml` `CustomSettings` or a server-side configuration endpoint that requires authentication.

3. **Ignoring response.success checks** — Writing `saveLog` or `screenPop` calls without checking `response.success` in the callback. Failures are silent to the agent, resulting in missing call logs and confusing support tickets.

## Official Sources Used

- Open CTI Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_cti.meta/api_cti/sforce_api_cti_intro.htm
- Open CTI Methods for Lightning Experience — https://developer.salesforce.com/docs/atlas.en-us.api_cti.meta/api_cti/sforce_api_cti_methods_lightning.htm
- Call Center Definition File — https://developer.salesforce.com/docs/atlas.en-us.api_cti.meta/api_cti/sforce_api_cti_callcenter_def.htm
- lightning-click-to-dial Component Reference — https://developer.salesforce.com/docs/component-library/bundle/lightning-click-to-dial/documentation
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/trusted/overview.html
