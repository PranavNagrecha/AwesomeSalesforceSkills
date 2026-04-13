# Well-Architected Notes — Analytics Permission and Sharing

## Relevant Pillars

- **Security** — CRM Analytics has three independent security layers (PSL license, app sharing, dataset row-level security) none of which inherit from Salesforce OWD or sharing rules. All three must be explicitly configured. Row-level predicates are the only mechanism that enforces data isolation at the dataset level; leaving a dataset without a predicate grants all licensed users access to all rows by default. Security predicates must be tested under the running user's identity, not as an admin with View All Data.
- **Trust** — Analytics dashboards that display row-restricted data must be verifiably correct: the right user sees the right rows. Trust requires explicit validation (logging in as a non-admin user and confirming lens results) after every predicate change. The silent failure mode of a misconfigured predicate (empty results with no error) is particularly dangerous because it can mask a real access defect.
- **Reliability** — Sharing inheritance introduces a runtime dependency on Salesforce sharing infrastructure. If the underlying Salesforce sharing configuration changes (territory reassignment, ownership transfer, manual share removal), Analytics row visibility changes automatically. This is a feature, but it requires that Salesforce sharing be treated as a shared concern between the Salesforce admin and the Analytics admin. A change to Salesforce sharing without updating Analytics documentation can cause unexpected row access changes.
- **Scalability** — Security predicates must remain under 5,000 characters regardless of org growth. Predicates that enumerate explicit user or role IDs scale poorly; predicate designs must use data-driven joins (role-expansion datasets, user-mapping datasets) so that the predicate string length is constant regardless of headcount. Sharing inheritance has its own scale limit (3,000-record threshold per user); backup predicates must be configured before the org grows into that threshold.
- **Operational Excellence** — The three-layer security model must be documented at the dataset level. Each dataset should have a record of: which security method is applied (predicate, sharing inheritance, or none-intentional), the SAQL predicate text or object reference, the backup predicate, and when it was last tested. Without this documentation, security regressions are detected only after a user reports seeing data they should not.

## Architectural Tradeoffs

**Security predicate vs. sharing inheritance:**
- Sharing inheritance is lower maintenance when Salesforce object sharing is already correctly configured and the source object is one of the five supported types. Changes to Salesforce sharing flow through automatically. The tradeoff is the 3,000-record hard limit and the dependency on Salesforce sharing being correct — if OWD or sharing rules are wrong in Salesforce, the Analytics view inherits those errors.
- Security predicates give full control and work for any object or data source (including external data loaded via recipes). The tradeoff is that predicates must be maintained separately from Salesforce sharing, and can drift when field names change during recipe transformations.

**App sharing roles:**
- Assigning Viewer is sufficient for users who should only consume dashboards. Granting Editor or Manager to non-admin users creates a risk of accidental dataset modification or inadvertent re-sharing. Apply least-privilege: default to Viewer, promote to Editor only for content authors, Manager only for app owners.

**Predicate design — owner-based vs. hierarchy-based:**
- Owner-based predicates (`'OwnerId' == "$User.Id"`) are simple, readable, and correct for direct-ownership models. They do not account for managers seeing subordinates' data.
- Hierarchy-based predicates require a pre-computed role-expansion dataset joined in the recipe. This adds dataflow complexity but keeps the predicate string short and constant-length as the org grows.

## Anti-Patterns

1. **Relying on Salesforce OWD as the Analytics access control** — Assuming that "Private" OWD on an object prevents users from seeing rows in a CRM Analytics dataset built from that object. OWD has no effect on Analytics row visibility. Every dataset must have its own explicit security configuration.
2. **Leaving the sharing inheritance backup predicate blank** — A blank backup predicate silently grants all-visible access to users who exceed the 3,000-record threshold. This turns a scoped-access design into a data breach for high-volume users. Always set the backup predicate to `'false'`.
3. **Using app sharing as a substitute for row-level security** — Controlling data access by restricting app membership rather than configuring dataset predicates. App sharing controls UI navigation, not data rows. A user removed from an app share can still query a dataset directly via the REST API if no predicate is configured.

## Official Sources Used

- Analytics Security Implementation Guide (Spring '26) — https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/bi_admin_guide_security.pdf
- Add Row-Level Security with a Security Predicate — https://help.salesforce.com/s/articleView?id=sf.bi_security_overview_predicate.htm
- CRM Analytics REST API Developer Guide Spring '26 — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- CRM Analytics Setup and Administration — https://help.salesforce.com/s/articleView?id=sf.bi_setup_intro.htm
