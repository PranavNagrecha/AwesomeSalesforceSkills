# Well-Architected Notes — HIPAA Compliance Architecture

## Relevant Pillars

- **Security** — The primary pillar for HIPAA compliance architecture. The HIPAA Security Rule maps directly to Salesforce Well-Architected Security principles: data classification and protection (SPE encryption of PHI fields), access control and least privilege (permission set architecture for minimum necessary access), audit and accountability (FAT + Event Monitoring), and supply chain / third-party risk (BAA scope validation for AppExchange packages). Security is non-negotiable in this domain — PHI breach carries regulatory, financial, and reputational consequences that make trade-offs with Security almost never acceptable.

- **Reliability** — HIPAA incident response requirements intersect with Reliability: the covered entity must be able to detect, respond to, and recover from security incidents involving PHI within defined timeframes (60-day breach notification window). Org backup and recovery design must ensure PHI availability for authorized users while maintaining confidentiality — disaster recovery planning for a HIPAA-covered org must address RTO/RPO for PHI-bearing objects. Shield BYOK key management is a reliability risk: key loss means permanent data loss.

- **Operational Excellence** — Ongoing HIPAA compliance is an operational discipline, not a one-time implementation gate. Operational excellence in this domain means: automated Shield key rotation scheduling, Event Monitoring log export pipelines to a SIEM with alerting on anomalous PHI access, quarterly BAA coverage reviews when new products are added, periodic access recertification reviews for users with PHI access, and documented run-books for incident response. Without operational excellence controls, a compliant architecture at launch degrades over time as product additions and user changes accumulate unchecked.

- **Performance** — SPE introduces query performance considerations. Encrypted fields cannot be indexed in the same way as plaintext fields. Deterministic encryption preserves exact-match SOQL but eliminates range queries and LIKE. Event Monitoring log export jobs and Shield re-encryption jobs consume async processing capacity. Performance testing with encryption enabled is a required step before go-live, not an afterthought.

- **Scalability** — Not a primary pillar for HIPAA compliance architecture specifically, but relevant when PHI volumes are large: Shield re-encryption jobs scale with record volume and can affect large orgs significantly. FAT storage scales with field change volume — high-frequency PHI field updates generate substantial archive storage that should be accounted for in org storage capacity planning.

## Architectural Tradeoffs

**Deterministic vs. Probabilistic Encryption:** Deterministic SPE enables SOQL search and is required for fields used in list views and formulas, but produces the same ciphertext for identical plaintext values — reducing theoretical security. Probabilistic encryption is stronger but breaks SOQL. The right answer is field-specific, not org-wide. The tradeoff is: security strength vs. functional completeness. Resolution: use probabilistic for stored-only fields (SSN, clinical notes) and deterministic for search-required fields (Name, MemberID). Document each assignment in the PHI field inventory.

**Tenant Secret vs. BYOK Key Management:** Salesforce-managed tenant secrets (default) provide strong encryption with minimal operational burden. BYOK gives the customer control of key material, satisfying regulatory requirements where key custody must rest with the data owner — but introduces operational risk: if the HSM is misconfigured or the key is accidentally destroyed, all data encrypted under that key is permanently lost. The tradeoff is: regulatory key control vs. operational risk and complexity. Resolution: use tenant secrets unless the organization's security policy or regulator explicitly requires customer key management.

**Shield Licensing Cost vs. Compliance Requirement:** Shield is a paid add-on. Its cost may be significant relative to the overall implementation budget. However, without Shield, the only encryption-at-rest alternative is Classic Encryption (limited to custom text fields, 175-character max, no key management) — which is insufficient for most PHI architectures. The tradeoff is: licensing cost vs. compliance coverage. Resolution: frame Shield as a compliance requirement, not an optional enhancement. If Shield cannot be licensed, document the resulting gaps in the risk register and present to the covered entity's compliance officer for formal risk acceptance.

## Anti-Patterns

1. **Treating the BAA as a one-time checkbox** — Teams execute a BAA at project kickoff and never review it again. New products are added (AppExchange packages, Einstein features, Experience Cloud templates) without checking BAA scope. Over time, PHI accumulates in uncovered services. Correct approach: implement a product addition review gate that includes BAA scope verification as a mandatory step, and conduct quarterly BAA coverage reviews.

2. **Encrypting all PHI fields with probabilistic encryption** — Applying probabilistic SPE to all PHI fields is the "secure by default" instinct, but it silently breaks SOQL queries, formula fields, list view sorting, and workflow rules that reference field values. Errors manifest as missing or incorrect data rather than explicit failures. Correct approach: conduct the functional dependency analysis before assigning encryption schemes; use deterministic encryption for fields with query or formula dependencies.

3. **Delegating HIPAA compliance entirely to the platform** — Assuming that once Shield is enabled and the BAA is signed, the covered entity's HIPAA obligations are fully met by Salesforce. HIPAA places compliance obligations on the covered entity, not its vendors. Salesforce's BAA and Shield controls reduce scope but do not eliminate the covered entity's responsibility for administrative safeguards (risk assessment, workforce training, incident response, sanction policy). Correct approach: produce the full HIPAA Security Rule safeguard matrix and assign each requirement to either a Salesforce control or an organizational policy owner.

## Official Sources Used

- Salesforce Shield Security Guide — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/security_overview.htm
- Salesforce HIPAA BAA Help Article — https://help.salesforce.com/s/articleView?id=sf.compliance_hipaa.htm
- Health Cloud Admin Guide (Protect Your Health Data with Salesforce Shield) — https://help.salesforce.com/s/articleView?id=sf.health_cloud_admin_guide.htm
- HIPAA Security Rule (HHS) — https://www.hhs.gov/hipaa/for-professionals/security/index.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Shield Platform Encryption Implementation Guide — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/security_pe_overview.htm
