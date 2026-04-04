# Well-Architected Alignment — Government Cloud Compliance

## WAF Pillars: Security and Reliability

Government Cloud compliance directly addresses two Salesforce Well-Architected Framework (WAF) pillars: Trusted (Security) and Resilient (Reliability). The compliance posture required for FedRAMP High imposes discipline that elevates both.

---

## Trusted Pillar: Security in Government Deployments

The WAF Trusted pillar defines a well-secured system as one where identity and access are strictly controlled, data is protected at rest and in transit, custom code respects security boundaries, and security decisions are documented and reviewed on a cadence.

FedRAMP High certification operationalizes the Trusted pillar through the NIST 800-53 control framework:

### Access Control (AC Family — WAF Identity and Access)

The WAF guidance on least privilege and minimum necessary access aligns directly with NIST 800-53 AC-6. GovCloud Plus deployments implement this through:
- Permission set architecture over broad profiles
- OAuth scope minimization for all Connected Apps
- Integration user accounts with the minimum CRUD permissions required (not "Modify All Data")
- Automated alerts when high-privilege permission sets are assigned (AC-2 account management)

The WAF anti-pattern of granting broad access for convenience (e.g., system administrator profiles for integration users, full OAuth scope for all Connected Apps) is explicitly a FedRAMP finding at the Moderate level and higher.

### Audit and Accountability (AU Family — WAF Governance)

The WAF Trusted pillar requires that security-relevant actions are logged and that logs are protected. FedRAMP AU controls require complete, tamper-resistant audit logs retained for a defined period. Shield Event Monitoring satisfies the WAF audit requirement and the FedRAMP AU-2, AU-3, AU-9, AU-11, and AU-12 controls simultaneously — making it mandatory rather than recommended for GovCloud deployments.

### Data Protection (SC Family — WAF Data Security)

The WAF data security guidance recommends encrypting sensitive data at rest. FedRAMP High SC-28 requires it. Platform Encryption in GovCloud Plus, and CMEK via Hyperforce, are the implementation mechanisms. The WAF principle that encryption decisions should be made at data classification time — not retrofitted after go-live — is enforced by FedRAMP: adding encryption after ATO is a significant change.

---

## Resilient Pillar: Reliability in Government Deployments

### Contingency Planning (CP Family — WAF Availability)

The WAF Resilient pillar requires documented RTO and RPO targets and tested recovery procedures. FedRAMP CP controls require contingency plans, backup procedures, and annual contingency plan testing. GovCloud deployments must document:
- Salesforce GovCloud SLA commitments (inherited)
- Customer-owned contingency plan for org data recovery (customer-owned)
- Backup strategy for org configuration (Metadata API backups on a documented schedule)
- Sandbox restore testing as evidence of CP-4 (contingency plan testing)

### Change Management (CM Family — WAF Adaptability)

The WAF guidance that changes should be versioned, tested, and reversible aligns with FedRAMP CM controls. GovCloud-specific requirements add the significant change notification gate — a compliance-enforced change management control that prevents untested changes from reaching production. This is more stringent than typical commercial Salesforce change management but results in a higher-quality, more controlled release process.

---

## WAF Anti-Pattern: Treating Compliance as a One-Time Event

The WAF Trusted pillar explicitly warns against treating security as a go-live checklist. This is doubly true for FedRAMP deployments. The FedRAMP continuous monitoring model requires ongoing authorization, not a static ATO. Organizations that obtain an ATO and then fail to maintain POA&M items, miss monthly reporting deadlines, or deploy significant changes without notification risk ATO suspension or revocation.

The WAF recommendation — build security in as a continuous practice, not a one-time gate — maps directly to the FISMA continuous monitoring requirement. The compliance automation patterns in this skill (Shield Event Monitoring exports to SIEM, automated evidence collection, significant change review gates) are the operational implementation of this WAF principle.

---

## WAF Anti-Pattern: Feature Optimization Before Compliance Baseline

Government Cloud deployments sometimes face pressure to enable new Salesforce features quickly as they become available on commercial cloud. The WAF principle of architectural integrity over incremental feature adoption is directly applicable here. Adding an un-authorized feature (one not yet in Salesforce's FedRAMP package) to a GovCloud deployment is a compliance violation — the feature is effectively outside the authorization boundary until Salesforce completes its re-authorization process.

---

## Official Sources Used

- Salesforce Well-Architected Framework Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Salesforce Government Cloud Overview — https://www.salesforce.com/solutions/government/
- Salesforce Trust and Compliance documentation — https://compliance.salesforce.com/en/services/government-cloud
- FedRAMP Authorization for Salesforce Government Cloud — https://marketplace.fedramp.gov/#/product/salesforce-government-cloud
- NIST SP 800-53 Rev 5 Security and Privacy Controls — https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- NIST SP 800-37 Rev 2 Risk Management Framework — https://csrc.nist.gov/publications/detail/sp/800-37/rev-2/final
- NIST SP 800-171 Rev 2 Protecting CUI in Nonfederal Systems — https://csrc.nist.gov/publications/detail/sp/800-171/rev-2/final
- DISA Cloud Computing SRG (DoD Impact Levels) — https://public.cyber.mil/dccs/
- CMS Acceptable Risk Safeguards (ARS) — https://www.cms.gov/research-statistics-data-and-systems/cms-information-technology/informationsecurity/cms-ars
- Salesforce Hyperforce Overview — https://help.salesforce.com/s/articleView?id=sf.hyperforce_overview.htm
- Salesforce Shield Overview — https://help.salesforce.com/s/articleView?id=sf.security_shield.htm
