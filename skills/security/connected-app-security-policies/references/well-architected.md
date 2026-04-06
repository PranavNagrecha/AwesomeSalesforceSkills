# Well-Architected Notes — Connected App Security Policies

## Relevant Pillars

- **Security** — This skill is primarily a Security skill. OAuth policy misconfiguration is a top-ranked cause of Salesforce org compromise. IP relaxation, high-assurance sessions, PKCE, and credential rotation are all direct security controls that reduce the blast radius of credential compromise.
- **Reliability** — Client secret rotation with zero grace period (ECA model) is a reliability concern: uncoordinated rotation causes integration outages. Proper rotation procedures are part of reliable operations.
- **Operational Excellence** — Documenting IP relaxation choices, rotation runbooks, and clock-sync requirements makes these security controls repeatable and auditable rather than tribal knowledge.

## Architectural Tradeoffs

**IP Relaxation strictness vs. operational flexibility:** Enforcing IP restrictions eliminates a broad attack surface but requires that integration server egress IPs be stable and known. Cloud-native integrations with dynamic IP ranges (e.g., Lambda functions, auto-scaling groups) cannot use `enforceIpRanges` without a proxy layer or VPC NAT gateway. The tradeoff is: fixed egress infrastructure cost vs. IP-level defense depth.

**PKCE adoption in confidential server clients:** PKCE is designed for public clients but can also be applied to confidential clients for defense in depth. The tradeoff is minor additional latency (SHA-256 computation) vs. protection against authorization code interception even in server-side flows. Salesforce recommends PKCE for all new Connected App implementations where the flow supports it.

**High Assurance enforcement timing:** Blocking low-assurance sessions immediately improves security but may break legacy integrations that cannot satisfy MFA. The phased "Switch to High Assurance" state allows a migration window at the cost of deferred enforcement. The risk of leaving integrations in "Switch" state indefinitely must be explicitly accepted and tracked.

## Anti-Patterns

1. **Relaxed IP restrictions left permanently from development** — The most common misconfiguration. `relaxIpRanges` should never be the production posture for any Connected App unless there is a documented, approved exception. Treat it as a deployment blocker.

2. **Treating "Switch to High Assurance" as enforcement** — The "Switch" state is a migration aid, not an enforcement gate. Using it as a long-term policy gives a false sense of security while leaving low-assurance sessions in production.

3. **Undocumented credential rotation with ECA** — Rotating a Connected App secret in the ECA model without coordinating consumers is equivalent to a planned outage for those integrations. Treating it as a low-risk background task leads to production incidents.

## Official Sources Used

- Salesforce Help: Connected App OAuth Policies (IP Relaxation, Session Policies, Manage Access) — https://help.salesforce.com/s/articleView?id=sf.connected_app_manage_oauth.htm&type=5
- Salesforce Help: OAuth 2.0 JWT Bearer Flow for Server-to-Server Integration — https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5
- Salesforce Help: Connected App IP Relaxation and Continuous IP — https://help.salesforce.com/s/articleView?id=sf.connected_app_continuous_ip.htm&type=5
- Salesforce Help: Rotate the Consumer Key and Consumer Secret — https://help.salesforce.com/s/articleView?id=sf.connected_app_rotate_consumer_details.htm&type=5
- Salesforce Help: Require a High-Assurance Session for a Connected App — https://help.salesforce.com/s/articleView?id=sf.connected_app_session_policies.htm&type=5
- Salesforce REST API Developer Guide: OAuth 2.0 Authorization — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_oauth_and_connected_apps.htm
- Salesforce Metadata API Developer Guide: ConnectedApp — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_connectedapp.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Salesforce Well-Architected: Security — https://architect.salesforce.com/well-architected/secure/overview
