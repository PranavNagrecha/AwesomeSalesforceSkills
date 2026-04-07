# Well-Architected Notes — External User Data Sharing

## Relevant Pillars

- **Security** — External user data sharing is a direct security concern. External OWD, Sharing Sets, and sharing rules define the data access boundary for all portal and community users. Misconfigured External OWD or an accidentally permissive default can expose internal records to all external users simultaneously. Defense-in-depth requires explicit access grants, not reliance on application-layer filtering.
- **Reliability** — External OWD changes trigger org-wide sharing recalculation jobs. For large data volume orgs, these jobs can run for hours. Reliable access configuration requires change windows, recalculation monitoring, and validation before marking configuration live.
- **Operational Excellence** — The sharing mechanism selected (Sharing Set vs. criteria-based rule) must match the license type. Mismatches produce silent failures — no errors, no warnings, just missing access. Operational excellence requires documentation of which mechanism is used for each license type and test procedures that verify access as a user, not as an admin.

## Architectural Tradeoffs

**Sharing Set (HVP) vs. Criteria-Based Rules (CC Plus)**
Sharing Sets are relationship-based and require a direct lookup path from the record to the user's Account or Contact. They are simple, performant for HVP users, and fire consistently. They cannot express field-value-based access (e.g., region, status). For complex access patterns, CC Plus or Partner Community licenses with criteria-based rules are needed — but carry higher license costs and more complex sharing model overhead.

**External OWD Openness vs. Targeted Grants**
Setting External OWD to Public Read Only is the simplest way to give all external users read access to an object. It is appropriate for reference data (price books, knowledge articles, product catalog) where all external users should see the same records. For sensitive records (Cases, Opportunities, Contracts), Private External OWD with targeted Sharing Sets or sharing rules is required. The tradeoff is configuration complexity versus unintentional over-sharing.

**Partner Community Role Hierarchy vs. Explicit Sharing Rules**
Partner Community's three-tier role hierarchy (Executive/Manager/User) provides implicit upward visibility within an account without explicit sharing rules. This reduces sharing rule configuration but couples access to the account's role structure. When cross-account sharing is needed (e.g., a partner executive needs to see cases across multiple partner accounts), explicit external sharing rules are required.

## Anti-Patterns

1. **Using Sharing Sets for CC Plus or Partner Community users** — Sharing Sets are HVP-only. Applying them to CC Plus or Partner Community profiles produces no access and no error. The correct mechanism for those license types is criteria-based or external sharing rules.
2. **Relying on internal OWD to restrict external users** — Internal OWD controls internal user access only. External users have a separate External OWD. If External OWD is left at its default (inherited from internal OWD), changes to internal OWD for internal access control purposes can inadvertently open or close external access.
3. **Not validating sharing recalculation before go-live** — Deploying External OWD changes or new Sharing Sets to production and immediately declaring success without waiting for the background recalculation job to complete results in validation against an inconsistent state. Always confirm recalculation is complete before signing off.

## Official Sources Used

- Salesforce Help — External OWD Overview — https://help.salesforce.com/s/articleView?id=sf.security_owd_external.htm
- Salesforce Help — Create and Edit Sharing Sets — https://help.salesforce.com/s/articleView?id=sf.networks_setting_light_users.htm
- Salesforce Help — Sharing Data with Partner Users — https://help.salesforce.com/s/articleView?id=sf.networks_partner_sharing.htm
- Salesforce Help — Object and Record Sharing with External Users — https://help.salesforce.com/s/articleView?id=sf.networks_sharing_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
