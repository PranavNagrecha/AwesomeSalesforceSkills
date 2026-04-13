# Well-Architected Notes — Integration Admin: Connected Apps

## Relevant Pillars

- **Security** — Pre-authorization mode with profile/permission set assignment restricts connected app access to only the intended integration users. IP Relaxation controls whether the org's network-level security applies to API sessions. Refresh Token Policy determines how long compromised tokens remain valid.
- **Operational Excellence** — EventLogFile monitoring provides audit trail for connected app usage, supporting incident investigation and compliance reporting. Periodic OAuth usage audits prevent orphaned integrations from remaining active after integrations are decommissioned.

## Architectural Tradeoffs

**All users may self-authorize vs. Admin approved users are pre-authorized:** Self-authorize is simpler to configure but exposes the connected app to any user in the org who can trigger an OAuth flow. Pre-authorized mode is more secure but requires explicit assignment management for every integration user and every new integration. For production integration connected apps, pre-authorized is always the correct choice.

**IP enforcement vs. relaxation:** Enforcing login IP restrictions provides defense-in-depth — even if a token is compromised, it cannot be used from an unknown IP. However, this requires maintaining accurate IP range entries in the integration user's profile, which creates operational overhead when integration server IPs change. Evaluate whether the IP enforcement benefit justifies the maintenance burden for each integration.

## Anti-Patterns

1. **Pre-authorized without profile assignment** — The single most common connected app configuration error. All authentication attempts fail with a generic OAuth error. Always assign after setting pre-authorized mode.

2. **Granting admin profile to integration users** — Granting System Administrator or a cloned admin profile to integration users to "simplify" access. This bypasses the API-only flag, grants interactive login capability, and violates least-privilege principles. Always use the Minimum Access - API Only Integrations profile for integration users.

3. **No monitoring of connected app usage** — Deploying a production integration without configuring any EventLogFile monitoring. OAuth token revocations, anomalous IP access, or unauthorized usage are invisible until an integration breaks or a security incident occurs.

## Official Sources Used

- Manage OAuth Access Policies for a Connected App — https://help.salesforce.com/s/articleView?id=sf.connected_app_manage_oauth.htm&type=5
- Connected App IP Relaxation and Continuous IP — https://help.salesforce.com/s/articleView?id=sf.connected_app_continuous_ip.htm&type=5
- EventLogFile Supported Event Types — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_supportedeventtypes.htm
