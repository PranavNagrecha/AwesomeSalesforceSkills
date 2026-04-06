# NFR Definition for Salesforce — NFR Register Template

Use this template to document non-functional requirements for a Salesforce implementation. Fill one table row per requirement. Every row must have a metric, threshold, measurement method, environment, and owner before it can be signed off.

## Project Context

| Field | Value |
|---|---|
| Project / Org | |
| Salesforce Edition | |
| Org Region | |
| Regulatory Context | (e.g. GDPR, HIPAA, PCI-DSS, none) |
| Go-Live Target | |
| 3-Year User Projection | |
| 3-Year Record Volume (key objects) | |
| NFR Register Owner | |
| Last Updated | |

---

## Performance NFRs

| ID | Description | Metric | Threshold | Measurement Method | Environment | Owner | Status |
|---|---|---|---|---|---|---|---|
| NFR-PERF-001 | Lightning record page load | Browser p95 load time | < 3 seconds | Browser Performance API via LWC logging | Full sandbox, 200 concurrent users | Platform Architect | Draft |
| NFR-PERF-002 | List view render time | Time to interactive | < 4 seconds for 2,000-record view | Manual timing | Full sandbox | Platform Architect | Draft |
| NFR-PERF-003 | Report execution time | Dashboard report load | < 30 seconds | Measured in Full sandbox | Full sandbox | Platform Architect | Draft |

---

## Scalability NFRs

| ID | Description | Business Target | Governor Limit Type | Utilisation at Launch | Utilisation at 3yr | Processing Mode | Method | Owner | Status |
|---|---|---|---|---|---|---|---|---|---|
| NFR-SCALE-001 | Integration throughput | ___ records/day | Daily API calls | ___ % | ___ % | Bulk API v2 | Salesforce Limits API | Integration Architect | Draft |
| NFR-SCALE-002 | Batch job window | ___ records/batch run | Batch Apex scope, SOQL rows | ___ % | ___ % | Batch Apex async | Job monitoring | Platform Architect | Draft |
| NFR-SCALE-003 | Concurrent user load | ___ users peak | API calls, Streaming API connections | ___ % | ___ % | Sync (UI) | Load test in Full sandbox | Platform Architect | Draft |

**Governor Limit Reference (Spring '25):**

| Limit Type | Value | Source |
|---|---|---|
| SOQL rows per sync transaction | 50,000 | Apex Governor Limits |
| DML statements per sync transaction | 150 | Apex Governor Limits |
| CPU time per sync transaction | 10,000 ms | Apex Governor Limits |
| Heap size (sync) | 6 MB | Apex Governor Limits |
| Heap size (async) | 12 MB | Apex Governor Limits |
| Daily REST API calls (Enterprise, 100 users) | ~1,000,000 | Varies by edition |
| Bulk API v2 records per job | 100,000,000 | Bulk API docs |

---

## Availability NFRs

### Level 1: Salesforce Infrastructure (Platform-Owned)

| ID | Description | SLA | Source | Notes |
|---|---|---|---|---|
| NFR-AVAIL-001 | Salesforce platform uptime | 99.9% | trust.salesforce.com | Covers datacenter, network, core platform; does NOT cover custom code |

### Level 2: Application Availability (Team-Owned)

| ID | Description | Target | RPO | RTO | Monitoring | Rollback Procedure | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| NFR-AVAIL-002 | Application availability during business hours | 99.5% | 1 hour | 4 hours | Custom monitoring flow + alerts | Change set rollback procedure | Platform Architect | Draft |
| NFR-AVAIL-003 | Scheduled batch job completion | 100% within nightly window | N/A | 2 hours | Job monitoring dashboard | Manual re-run + escalation | Integration Architect | Draft |

---

## Security and Compliance NFRs

### Applicable Regulations

- [ ] GDPR
- [ ] HIPAA
- [ ] PCI-DSS
- [ ] SOC 2
- [ ] Other: ___

### GDPR Controls (complete if GDPR applies)

| ID | Article | Control | Salesforce Feature | Acceptance Criterion | Owner | Status |
|---|---|---|---|---|---|---|
| NFR-GDPR-001 | Art. 17 | Right to erasure | Custom Flow + Apex batch | Personal data anonymised within 30 days of SAR | Data Protection Officer | Draft |
| NFR-GDPR-002 | Art. 7 | Consent audit log | Field History Tracking / Event Monitoring | Consent changes logged with actor, timestamp, old/new value | Platform Architect | Draft |
| NFR-GDPR-003 | Art. 44-49 | Data residency | EU region org provisioning | Org confirmed as EU-region instance via trust.salesforce.com | IT Operations | Draft |

### HIPAA Controls (complete if HIPAA applies)

| ID | Requirement | Control | Salesforce Feature | Acceptance Criterion | Owner | Status |
|---|---|---|---|---|---|---|
| NFR-HIPAA-001 | PHI encryption at rest | Field-level encryption | Shield Platform Encryption | PHI fields return encrypted token via REST API, not plaintext | Security Architect | Draft |
| NFR-HIPAA-002 | Audit trail | Access and change logging | Event Monitoring | All PHI object access logged; logs retained for 7 years | Security Architect | Draft |
| NFR-HIPAA-003 | BAA | Business Associate Agreement | Salesforce contract | Salesforce HIPAA BAA executed and on file before go-live | Legal / Account Exec | Draft |

### General Security NFRs

| ID | Description | Control | Acceptance Criterion | Owner | Status |
|---|---|---|---|---|---|
| NFR-SEC-001 | Authentication | MFA enforced for all users | All users required to enrol in MFA; verified in production | Salesforce Admin | Draft |
| NFR-SEC-002 | Session management | Idle session timeout | Session timeout ≤ 30 minutes for privileged users | Salesforce Admin | Draft |
| NFR-SEC-003 | API access | Named credential for all outbound callouts | No hardcoded credentials in Apex; all callouts use Named Credentials | Platform Architect | Draft |

---

## Usability NFRs

| ID | Description | Metric | Threshold | Measurement Method | Owner | Status |
|---|---|---|---|---|---|---|
| NFR-UX-001 | Page load time | Browser p95 load | < 3 seconds | (cross-reference NFR-PERF-001) | Platform Architect | Draft |
| NFR-UX-002 | Layout field density | Visible fields per page layout | ≤ 30 fields per layout | Manual audit of all layouts before go-live | UX Lead / Architect | Draft |
| NFR-UX-003 | Mobile readiness | Core workflows completable on mobile | ≥ 80% of tier-1 workflows | UAT on Salesforce Mobile App, iOS and Android | UX Lead | Draft |
| NFR-UX-004 | Accessibility | WCAG compliance | WCAG 2.1 AA for custom LWC on public pages | Automated a11y scan + manual screen reader test | UX Lead | Draft |

---

## Sign-Off Criteria

Before this NFR register is accepted as baseline:

- [ ] Every NFR row has a metric, threshold, measurement method, environment qualifier, and owner
- [ ] All governor limit utilisation calculations are complete and reviewed
- [ ] Availability responsibility split is documented and agreed with the business
- [ ] All applicable regulation controls are decomposed to control level (not regulation level)
- [ ] Usability NFRs include field count, mobile, and accessibility targets
- [ ] Every NFR has a test plan step in the UAT or go-live checklist
- [ ] No NFR uses vague adjectives (fast, secure, reliable) without a numeric threshold

---

## Revision History

| Date | Version | Author | Change |
|---|---|---|---|
| | 0.1 | | Initial draft |
