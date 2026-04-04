# Well-Architected Mapping — Well-Architected Review

This skill is the foundational skill for applying the Salesforce Well-Architected Framework. It maps directly to all five internal WAF dimensions and all three top-level WAF pillars.

---

## Pillar Mapping

### Security (Trusted pillar)

This skill directly exercises the Security dimension as its primary review activity. The Trusted pillar review covers:
- Sharing model completeness (OWDs, sharing rules, role hierarchy, Apex sharing)
- FLS enforcement in Apex and LWC
- Authentication strength (MFA, SSO, trusted IP ranges)
- Shield applicability (field audit trail, event monitoring, platform encryption)
- Data classification and compliance readiness (GDPR, HIPAA, PCI-DSS)

A WAF review is the mechanism by which Security findings are surfaced, rated, and handed to a remediation owner. Without a structured review, Security posture degrades silently.

---

### Reliability (Trusted pillar)

The Trusted pillar also covers Reliability: whether the org behaves correctly under failure conditions. This skill surfaces Reliability findings through:
- Error handling coverage in Apex (uncaught exceptions, swallowed errors)
- Integration resilience (callout retry logic, fault connectors in Flows)
- Transaction integrity (DML with rollback strategy, batch job error isolation)
- Monitoring and observability (Event Monitoring, custom logging, alerts for integration failures)

---

### Performance (Adaptable pillar — implicit)

Performance is surfaced in the Adaptable pillar review through:
- Lightning page load time assessment
- Synchronous Apex on page load (should be asynchronous where possible)
- SOQL selectivity on high-volume objects
- Bulk API vs REST API usage for large data operations

---

### Scalability (Adaptable pillar)

The Adaptable pillar review explicitly covers Scalability:
- Governor limit headroom at current and projected data volumes
- Bulkification of Apex and Flow logic
- LDV (Large Data Volume) patterns on high-growth objects
- API call volume trend vs daily limit

---

### User Experience (Easy pillar)

The Easy pillar is the primary carrier of User Experience findings:
- Page layout quality and component count per Lightning page
- Mobile readiness for orgs with field or mobile users
- Accessibility compliance (WCAG 2.1 AA baseline)
- Error message clarity and recoverability
- Process simplicity (automation eliminating manual steps)
- Adoption metrics as a proxy for UX effectiveness

---

### Operational Excellence (Adaptable pillar)

The Adaptable pillar review covers Operational Excellence:
- Test coverage and assertion quality
- Source control and deployment pipeline maturity
- Sandbox refresh cadence
- Architecture decision documentation
- Dependency management (managed packages, API version currency)
- Configuration vs code ratio

---

## This Skill as a Gateway

The WAF review skill is a gateway, not a destination. Its outputs are:
1. A scorecard identifying which areas need deeper assessment
2. Pointers to pillar-specific skills for remediation:
   - **Red Trusted findings** → `security-architecture-review` skill
   - **Red Adaptable/Scalability findings** → `limits-and-scalability-planning` skill
   - **High technical debt finding** → `technical-debt-assessment` skill
   - **Multi-org concerns surfaced during review** → `multi-org-strategy` skill

A WAF review does not replace these skills. It determines whether they are needed and in what priority order.

---

## Official Sources Used

- Salesforce Well-Architected Framework Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Salesforce Well-Architected: Easy — https://architect.salesforce.com/docs/architect/well-architected/guide/easy.html
- Salesforce Well-Architected: Adaptable — https://architect.salesforce.com/docs/architect/well-architected/guide/adaptable.html
