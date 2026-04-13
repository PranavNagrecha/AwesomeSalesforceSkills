# Well-Architected Notes — CPQ Deployment Administration

## Relevant Pillars

- **Reliability** — The primary pillar for CPQ deployment. A failed or incomplete CPQ data migration produces quotes with incorrect pricing or unenforced product rules in production. Reliability requires a validated, ordered, idempotent migration process with dry-run testing before any production deployment.

- **Operational Excellence** — CPQ configuration changes happen frequently as pricing strategy evolves. Operational excellence demands a repeatable, version-controlled, and peer-reviewable deployment process — not ad-hoc CSV exports. Tooling that produces an audit trail (Prodly, Copado) and a defined runbook reduce operational risk.

- **Security** — CPQ configuration records can expose pricing logic, discount approval thresholds, and partner tier structures. Org access for migration tooling must follow least-privilege: the integration user or connected app performing data export/import should have only the permissions needed for SBQQ objects, not broad system administrator access. Migration credentials must not be embedded in export plan files committed to version control.

- **Performance** — Large CPQ configurations (hundreds of Price Rules, thousands of Option Constraints) can cause quote calculation timeouts if rules are evaluated redundantly or if Price Rule conditions are poorly ordered. Deployment of CPQ data is also a performance concern: bulk upsert operations against SBQQ objects can trigger CPQ background recalculation jobs that impact sandbox performance during migration.

- **Scalability** — As the product catalog and pricing complexity grow, a manual CSV-based migration approach does not scale. Architecture decisions made early — external ID scheme, tooling choice, dependency graph documentation — compound in value as configuration volume increases.

## Architectural Tradeoffs

**Prodly / Copado vs. SFDMU / Data Loader:**
Prodly and Copado Data Deploy automate the dependency graph resolution and provide UI-driven deployment plans, at the cost of licensing fees and vendor dependency. SFDMU and Data Loader are free and flexible but require the team to own and maintain the ordered export plan and external ID scheme. For orgs deploying CPQ configuration more than once per quarter, the operational cost of maintaining a manual migration plan typically exceeds the cost of purpose-built tooling.

**External ID scheme design:**
A poorly designed external ID (e.g. using the Salesforce record Name which may not be unique, or a sequential integer that shifts on re-export) will cause duplicate records or failed upserts on re-migration. A hash-based or composite-key external ID (combining object type, parent name, and rule name) is more durable but requires more upfront design. This is a one-time investment: changing external IDs after initial migration requires a full data reload.

**Salto IaC approach:**
Salto represents CPQ configuration as declarative HCL-like files in version control, enabling PR-based review and diff of CPQ changes. This is the highest-maturity approach but requires team familiarity with the Salto platform and ongoing maintenance of the Salto configuration. It is most valuable when CPQ configuration is treated as code — reviewed, tested, and promoted through a formal pipeline.

## Anti-Patterns

1. **Using Change Sets or Metadata API for CPQ configuration** — CPQ objects are sObjects (data records), not metadata components. Change Sets will deploy the object schema but zero data. This is the single most common CPQ deployment mistake and produces invisible production failures.

2. **Migrating CPQ records without verifying product catalog parity** — Option Constraints and many Product Rules reference `Product2` records by lookup ID. Migrating rules before confirming that all referenced products exist in the target org produces silent null-lookup failures that disable constraint enforcement without error.

3. **Skipping dry-run migration against a non-production environment** — Migrating directly to production without a validated dry run in a staging sandbox means that ordering errors, missing fields, or broken string references are discovered in production during a live pricing window.

## Related Skills

- `devops/salesforce-devops-tooling-selection` — Choose between Prodly, Copado, Salto, and SFDMU before designing the pipeline
- `devops/copado-essentials` — Use when Copado is the org's DevOps platform and you are extending it with Data Deploy for CPQ
- `devops/pre-deployment-checklist` — Pre-migration gates: package version parity, permission set readiness, environment health
- `devops/post-deployment-validation` — Post-migration validation: rule execution, template rendering, pricing accuracy

## Official Sources Used

- Salesforce CPQ Product Rule Guidelines — https://help.salesforce.com/s/articleView?id=sales.cpq_product_rule_guidelines.htm
- Salesforce CPQ Price Rules Introduction — https://help.salesforce.com/s/articleView?id=sf.cpq_price_rules_intro.htm
- Salesforce CPQ Quote Templates — https://help.salesforce.com/s/articleView?id=sales.cpq_quote_templates.htm
- Salesforce CPQ Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_guide_intro.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
