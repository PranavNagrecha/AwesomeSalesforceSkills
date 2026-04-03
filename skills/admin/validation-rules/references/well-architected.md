# Well-Architected Mapping: Validation Rules

---

## Pillars Addressed

### Reliability

**Principle: Data Integrity at the Point of Entry**
Validation rules are the declarative enforcement layer for data quality. A record that enters the org wrong will cause problems downstream — in reports, integrations, automations, and analytics. Catching bad data at the source is cheaper than cleaning it later.

- WAF check: Are critical business rules enforced declaratively (can't be bypassed by accident)?
- WAF check: Do validation rules have bypass mechanisms so they don't block legitimate system operations?
- WAF check: Is the error message actionable — does it tell the user how to fix the problem?

**How this skill addresses it:**
- Mode 1 produces rules with correct formula structure and error messages
- Mode 2 surfaces rules that could silently block integrations
- Bypass patterns ensure rules don't become operational blockers

**Risk of not following this:** Data quality degrades. Reports built on the data produce incorrect outputs. Integrations fail silently. Support tickets spike every data migration.

### Operational Excellence

**Principle: Rules Are Maintainable and Documented**
A validation rule with no documentation, no bypass, and a one-word error message is a future support ticket. Rules need to be understandable to an admin who didn't write them.

- WAF check: Is each rule documented with its business justification?
- WAF check: Is there a bypass mechanism that doesn't require deactivating the rule in production?
- WAF check: Is the rule scoped to the right Record Types and contexts?

**How this skill addresses it:**
- The template in `templates/` captures business justification and ownership
- Naming conventions make rule purpose visible in the Setup menu
- Bypass pattern documentation prevents "deactivate in prod" anti-pattern

**Risk of not following this:** Admin turnover creates orphaned rules no one understands. Data migrations require disabling rules. Rules accumulate with no owner and no review cadence.

---

## Pillars Not Addressed

- **Security** — Validation rules don't enforce security (FLS/CRUD does). A validation rule can reference a field the user can't see, but that's a formula evaluation issue, not a security control.
- **Performance** — Cross-object validation rules add query overhead. Worth noting but rarely a primary concern unless on very high-volume objects (millions of records per day).
- **Scalability** — Validation rules scale declaratively with Salesforce's platform; no action required.
- **User Experience** — Partially addressed (error message quality), but UX design of the rule placement is out of scope.

---

## Governance Recommendations

**Who should own validation rules?**
- Business owner: defines the requirement ("Close Date required on Closed Opportunities")
- Salesforce Admin: translates to formula + tests + deploys
- Data/Integration team: reviews for impact on integrations before deployment

**Review cadence:**
- Audit active rules annually — check for inactive rules, rules with no bypass, rules tied to deprecated processes
- Review rules before any data migration
- Review rules when integrations are added or changed

**Change management:**
- Any new validation rule should be tested in sandbox with the integration user before production deployment
- Communicate to integration teams before deploying rules that affect objects they write to

## Official Sources Used

- Salesforce Well-Architected Overview — reliability and change-discipline framing for validation design
- Metadata API Developer Guide — validation-rule metadata behavior in releases
