# Well-Architected Alignment — Security Architecture Review

## WAF Pillar: Trusted

This skill operates entirely within the Trusted pillar of the Salesforce Well-Architected Framework. The Trusted pillar covers three primary areas: security model completeness, compliance readiness, and authentication strength.

### Security Model Completeness

The WAF Trusted guidance defines a "well-secured" sharing model as one where:

- Every object has an explicit, documented OWD justification
- The principle of least privilege is applied to profiles, permission sets, and sharing rules
- Apex code enforces sharing intent — not just declares it
- System-context operations are documented and justified

A security architecture review operationalizes this guidance by converting it into auditable checklist items with explicit pass/fail criteria and severity ratings for deviations.

### Compliance Readiness

The WAF Trusted pillar recognizes that orgs holding regulated data (HIPAA PHI, PCI-DSS cardholder data, GDPR personal data) must implement controls beyond the standard Salesforce configuration. This skill's Shield Needs Assessment directly addresses the WAF guidance that regulated data requires audit logging (Event Monitoring), extended field history (Field Audit Trail), and data-at-rest encryption (Platform Encryption).

### Authentication Strength

WAF Trusted guidance requires MFA enforcement for all human users. This skill's Connected App review extends that requirement to machine-to-machine authentication: OAuth scope minimization, token lifetime controls, and IP restriction policies prevent connected system credentials from becoming persistent, unrestricted access vectors.

---

## Relationship to WAF Review Modes

The Salesforce WAF defines a Trusted review as examining:

1. **Identity and Access** — who can authenticate and what can they do
2. **Data Security** — what data is visible at the record and field level
3. **Application Security** — does custom code respect security boundaries
4. **Governance** — are security decisions documented and reviewed periodically

This skill's five review domains map directly to those four WAF areas:

| WAF Trusted Area | Skill Domain |
|-----------------|-------------|
| Identity and Access | Domain 4 (Connected Apps), Domain 1 (Sharing Model — role hierarchy) |
| Data Security | Domain 1 (Sharing Model), Domain 2 (FLS/CRUD) |
| Application Security | Domain 3 (Apex Security Patterns) |
| Governance | Domain 5 (Shield Assessment), recurring review recommendation |

---

## WAF Anti-Pattern: Security as a One-Time Event

The WAF Trusted pillar explicitly warns against treating security as a go-live checklist rather than an ongoing practice. A security architecture review is most valuable when it is repeated on a documented cadence (annually at minimum, quarterly for orgs holding regulated data) and when findings are tracked in a backlog with named owners and target remediation dates.

A one-time review that produces a report that is filed and forgotten is a WAF anti-pattern. The output of this skill should feed into the org's security backlog and be referenced in the next review cycle to confirm prior findings were remediated.

---

## Official Sources Used

- Salesforce Well-Architected Framework Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Secure Apex Classes (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm
- Apex Security and Sharing (LWC Developer Guide) — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security
- Salesforce Sharing Model — https://help.salesforce.com/s/articleView?id=sf.sharing_model.htm
- Connected App Overview — https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm
- Salesforce Shield Overview — https://help.salesforce.com/s/articleView?id=sf.security_shield.htm
- Field-Level Security Overview — https://help.salesforce.com/s/articleView?id=sf.admin_fls.htm
