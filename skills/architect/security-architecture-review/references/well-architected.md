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

- Salesforce Well-Architected Framework Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (HTTP 403 on 2026-10-03; pillar framing follows `standards/well-architected-mapping.md`)
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html (HTTP 403 on 2026-10-03, not re-read)
- Secure Apex Classes (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm (read as the Summer '26 PDF below)
- Apex Security and Sharing (LWC Developer Guide) — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security (HTTP 403 on 2026-10-03, not re-read)
- Salesforce Sharing Model — https://help.salesforce.com/s/articleView?id=sf.sharing_model.htm (help.salesforce.com does not fetch; the Security Guide PDF below was read instead)
- Connected App Overview — https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm (help.salesforce.com does not fetch; connected app policy claims marked UNVERIFIED)
- Salesforce Shield Overview — https://help.salesforce.com/s/articleView?id=sf.security_shield.htm (help.salesforce.com does not fetch; not re-read)
- Field-Level Security Overview — https://help.salesforce.com/s/articleView?id=sf.admin_fls.htm (help.salesforce.com does not fetch; not re-read)
- Salesforce Security Guide, Summer '26 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf. "Organization-Wide Sharing Defaults" (external level cannot exceed internal; pre- and post-Spring '20 external defaults; Private recommended; reporting note), "Connected Apps" (creation restricted as of Spring '26; external client apps recommended), Shield components, "Field History Tracking" (18/24 months without Field Audit Trail)
- Apex Developer Guide, Summer '26 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf. "Enforce Object and Field Permissions" (user mode by default at 67.0; personal-info settings not enforced in Apex; Automated Process user needs permission sets), "Security Tips for Apex and Visualforce Development" (default escaping, `escape="false"`), "Custom Settings" (protection only in managed packages; guest-readable otherwise), "Metadata" (protected metadata readable only in-namespace)
- Object Reference, Summer '26 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf. `SetupAuditTrail` (at least 180 days, aggregate limits), `OauthToken` (`LastUsedDate`, `UseCount`, Customize Application visibility), `ConnectedApplication`, `ExternalClientApplication`, `PermissionSet` (`PermissionsPermissionName`, `IsOwnedByProfile`), `PermissionSetAssignment`

