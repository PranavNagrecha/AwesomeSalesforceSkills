# Well-Architected Notes — Analytics Security Architecture

## Relevant Pillars

- **Security** — This skill is primarily a Security pillar concern. CRM Analytics has three independent security layers (app-level, dataset-level, row-level predicate) none of which inherit from Salesforce OWD or sharing rules. All three must be explicitly designed and validated. Failure to configure row-level security means all licensed users see all rows — the platform default is permissive, not restrictive. Security predicates, sharing inheritance thresholds, and View All Data exposure must each be addressed in any secure Analytics implementation.

- **Trust** — Dashboards that surface incorrect data (either too much or too little, due to predicate misconfiguration) erode user trust rapidly. Incorrect security predicates — especially silent failures like case-mismatched column names that return zero rows — manifest as "the dashboard is broken" to end users, not as security errors. Correct predicate design, verified with persona-based testing, is the primary trust control.

- **Scalability** — The sharing inheritance 3,000-row limit is a hard scalability boundary. As orgs grow (more records, more users, larger role hierarchies), sharing inheritance configurations that worked correctly at lower data volumes will silently fail for high-volume users. Predicate-based designs must be reviewed against projected data growth. Cross-dataset entitlement patterns must account for entitlement dataset size as user populations grow.

- **Operational Excellence** — Security configuration is not a one-time activity. Entitlement datasets used in cross-dataset security patterns must be refreshed whenever access grants change. Predicate strings must be re-validated when dataflow or recipe changes rename or restructure dataset columns. Periodic access reviews (for View All Data permission holders, for dataset sharing grants) are an operational requirement, not a project-phase deliverable.

---

## Architectural Tradeoffs

**Sharing inheritance vs. hand-written predicate:**
Sharing inheritance is lower effort to configure and naturally mirrors the Salesforce role hierarchy, but it introduces the 3,000-row limit constraint and requires the source to be a Salesforce-connected dataset. A hand-written predicate requires more design and testing effort but is explicit, auditable, and not subject to undocumented row-count thresholds. For organizations where even a single user's hierarchy could span more than 3,000 source records, sharing inheritance should be treated as an optional complement to a predicate, not a replacement for one.

**Predicate simplicity vs. expressiveness:**
Simple predicates (`'OwnerId' == "$User.Id"`) are easy to verify and maintain. Complex predicates that use multiple conditions, OR clauses, or IN-list patterns (generated from `$User.*` attributes) approach the 5,000-character limit and become difficult to test exhaustively. The 5,000-character ceiling also constrains entitlement models with many possible values. Cross-dataset augment patterns move complexity into the dataflow/recipe layer (where it can be tested and versioned) rather than into an opaque predicate string.

**Query-time filtering vs. dataflow-time embedding:**
Security predicates filter at query time with no latency cost — they are appended to every SAQL query. Cross-dataset entitlement patterns embed security data at dataflow run time, meaning there is always a lag between when entitlements change in Salesforce and when the embedded dataset reflects those changes. For time-sensitive access changes (e.g., terminating an employee's access), a predicate-only approach is more responsive; for complex entitlement models, the augment approach may be the only feasible design.

---

## Anti-Patterns

1. **Assuming Salesforce sharing carries over** — Configuring strict OWD and sharing rules on Salesforce objects and then deploying CRM Analytics datasets without any predicate or sharing inheritance, on the assumption that Analytics respects the underlying Salesforce security model. It does not. This is the most common and highest-impact anti-pattern in CRM Analytics implementations.

2. **Sharing inheritance without a backup predicate** — Enabling sharing inheritance on a dataset and leaving the backup predicate empty. For any user who exceeds the 3,000-row threshold, this results in all rows being returned — a silent, permissive failure that does not surface any error in the UI, API, or platform logs.

3. **Writing predicates without verifying column name case** — Copying field API names from the Salesforce object manager into the predicate string without checking the actual column names as materialized in the Analytics dataset schema. Column casing can differ between the Salesforce field API name and the dataset column name depending on dataflow transformation steps. The resulting predicate silently returns zero rows for all users.

---

## Official Sources Used

- Set Up Dataset Security to Control Access to Rows — https://help.salesforce.com/s/articleView?id=sf.bi_security_datasets_overview.htm
- Add Row-Level Security with a Security Predicate — https://help.salesforce.com/s/articleView?id=sf.bi_security_predicate.htm
- Analytics Security Implementation Guide Spring '26 — https://help.salesforce.com/s/articleView?id=sf.bi_security.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
