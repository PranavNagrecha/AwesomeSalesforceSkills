# Well-Architected Notes — License Optimization Strategy

## Relevant Pillars

License optimization maps most directly to the Operational Excellence and Security pillars of the Salesforce Well-Architected Framework. The framework organises pillars under three top-level values: Trusted, Easy, and Adaptable.

- **Operational Excellence (Adaptable value)** — The primary pillar for license optimization. Maintaining a right-sized license footprint, tracking seat utilisation, reclaiming inactive seats, and choosing the correct license tier for each user population are all operational hygiene practices. An org that allows license waste to accumulate is not operationally excellent: it is paying for capacity it does not use, running a risk of hitting the license ceiling at an inconvenient time, and carrying over-privileged users who represent an unnecessary access risk.

- **Security (Trusted value)** — Inactive users with active licenses represent an unnecessary attack surface. A user account that has not logged in for six months and has not been deactivated is a credential that could be compromised without detection. Reclaiming inactive licenses is simultaneously a cost and a security action. Similarly, PSL assignments that grant feature access to users who do not use those features violate the principle of least privilege. Right-sizing licenses and PSLs reduces the org's access footprint to the minimum required for each user's actual job function.

- **Performance (Adaptable value)** — Not a direct driver for license optimization, but license tier selection affects API allocation. Salesforce's daily API request allocation scales with the number of Salesforce and API-enabled licenses in the org. Downsizing licenses may reduce the API allocation headroom. Validate that a license reduction does not push the org's API consumption into a headroom risk before completing the migration.

- **Reliability (Trusted value)** — Indirect relevance. An org that is consistently near its license ceiling runs the risk of being unable to add new users during growth events without a contract amendment, which can delay onboarding and create a reliability risk for business operations. Proactive reclamation maintains headroom for growth.

---

## Architectural Tradeoffs

### Cost vs. Feature Access

The core tradeoff in license optimization is between cost reduction and feature access. Downgrading from a full CRM license to a Platform license or Identity license reduces per-seat cost but removes access to standard CRM objects. The decision requires a thorough audit of actual usage — not just assumed usage. A user who never opens the Opportunities tab may still be included in reports or lead assignment rules that depend on their license tier. Validate usage before migrating.

### Seat vs. Login Billing

Login-Based Licensing reduces cost for infrequent users but introduces variable monthly cost. Per-seat licensing provides predictable cost but charges for capacity whether used or not. The breakeven point varies by the contracted rates; it must be calculated org-specifically. Organizations with highly seasonal usage patterns (heavy quarter-end, light off-season) may find LBL economically superior overall even if some months exceed the breakeven.

### Centralised Reclamation vs. Self-Service Offboarding

Centralised license reclamation (an admin or automation periodically queries and reclaims inactive seats) is reliable but reactive. Self-service offboarding (HR system triggers deactivation on termination or role change) is proactive but requires integration maintenance. Both should be in place: the integration handles planned transitions, and the periodic audit catches missed cases.

---

## Anti-Patterns

1. **Over-licensing all users "to be safe"** — Assigning full CRM licenses to all users regardless of their actual workflow is a common org setup pattern. It eliminates the complexity of managing multiple license types but generates significant unnecessary cost at scale. The correct approach is to audit actual object usage by job function and assign the minimum license tier that satisfies each group's genuine requirements, validated in sandbox.

2. **Treating license reclamation as a one-time project** — License waste accumulates continuously as users are onboarded and offboarded imperfectly. A one-time reclamation effort without an ongoing monitoring cadence will return to the same wasteful state within months. The operational pattern must include a recurring audit (quarterly is typical) and a preventive offboarding integration with HR systems.

3. **Ignoring PSL costs in license reviews** — Permission Set License costs are separate from base license costs and are frequently overlooked in license audits that focus only on user license seat counts. PSLs for products like Einstein Analytics, Revenue Cloud CPQ, and Field Service can represent a material cost line. Include PSL utilisation in every license review.

---

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- View Your Org's User License Information — https://help.salesforce.com/s/articleView?id=sf.users_license_types_available.htm
- Permission Set Licenses — https://help.salesforce.com/s/articleView?id=sf.users_permissionset_licenses_overview.htm
- Login-Based Licensing — https://help.salesforce.com/s/articleView?id=sf.users_login_based_licensing.htm
- UserLogin Object (Freeze Users) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.doc/object_reference/sforce_api_objects_userlogin.htm
- UserLicense Object — https://developer.salesforce.com/docs/atlas.en-us.api_meta.doc/api_meta/meta_userlicense.htm
- REST API Limits Resource — https://developer.salesforce.com/docs/atlas.en-us.api_rest.doc/api_rest/resources_limits.htm
