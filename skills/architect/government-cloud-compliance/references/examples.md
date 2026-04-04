# Examples — Government Cloud Compliance

## Example 1: Federal Health Agency — Transitioning to GovCloud Plus for FedRAMP High ATO

**Context:** A federal civilian health agency uses Salesforce Service Cloud to manage case intake for a public benefits program. The org currently runs on standard commercial Salesforce. The agency CISO has determined that the data processed — including income verification records, healthcare eligibility determinations, and Social Security numbers — meets the FISMA High impact level because compromise of this data would severely affect public welfare programs and individual privacy at scale. The agency is initiating a new ATO effort and must migrate to Salesforce Government Cloud Plus.

**Architecture decisions made:**

**Offering selection:** GovCloud Plus (FedRAMP High) was selected over standard GovCloud (FedRAMP Moderate) based on the FISMA High data classification. Hyperforce GovCloud was evaluated but not selected because the program does not require DoD IL5 and the agency already had a contracting vehicle for the traditional GovCloud Plus offering.

**Data residency verification:** The team audited all integrations. Three integrations were found to be sending Salesforce record data to a commercial cloud middleware platform (MuleSoft CloudHub running in US-East commercial region). This violated the data residency requirement — MuleSoft CloudHub commercial is not FedRAMP-authorized. The integration was redesigned to use MuleSoft Government Cloud (FedRAMP-authorized) before go-live.

**Control inheritance mapping:** Working with Salesforce's FedRAMP package documentation, the team identified:
- 180 controls fully inherited from Salesforce (physical, environmental, most audit infrastructure)
- 85 controls with shared responsibility requiring customer implementation statements
- 156 controls fully customer-owned (configuration management, incident response, training)
The customer SSP was scoped to the 241 non-fully-inherited controls.

**Compliance automation:** Shield Event Monitoring was licensed and configured. A nightly Apex scheduled job queries the EventLogFile object and pushes LoginEvent, ReportEvent, ApiEvent, and BulkApiResultEvent records to the agency's Splunk SIEM instance (also FedRAMP-authorized). The SIEM is configured to alert on off-hours data export events and bulk API calls exceeding 10,000 records.

**Feature gap findings:**
- The team had planned to use an AppExchange document generation package. The package was not on the GovCloud Plus authorized list. The agency replaced it with a Salesforce-native document generation approach using Visualforce PDF templates.
- Einstein Case Classification was not yet FedRAMP High authorized at the time of the migration. The feature was removed from the initial go-live scope and added to the post-ATO feature roadmap pending Salesforce's re-authorization cycle.

**Outcome:** The org migration to GovCloud Plus was completed. The agency submitted an ATO package with a complete SSP covering all 241 customer-owned and shared controls, a POA&M with 14 open items (all Low or Moderate risk), and a Security Assessment Report from their 3PAO. ATO was granted. The continuous monitoring cadence was established: monthly POA&M reviews, quarterly significant change assessments, annual 3PAO testing of a rotating subset of controls.

---

## Example 2: DoD Contractor — Designing for IL4 with CUI on Salesforce GovCloud Plus

**Context:** A defense contractor builds a supply chain management application on Salesforce for a Department of Defense program office. The application tracks contract deliverables, vendor performance, and program financial data. Some data elements are classified as Covered Defense Information (CDI) under DFARS 252.204-7012, requiring NIST SP 800-171 compliance. The program office requires DoD IL4, which mandates FedRAMP High as the minimum cloud baseline.

**Architecture decisions made:**

**Offering selection:** GovCloud Plus on Hyperforce (AWS GovCloud US-East) was selected. The Hyperforce deployment was chosen over traditional GovCloud Plus because it enables customer-managed encryption keys (CMEK) through AWS Key Management Service in the AWS GovCloud region — a control the DoD program office required for CDI fields. CMEK allows the contractor to demonstrate that Salesforce cannot independently decrypt CDI-containing fields without the customer's key.

**NIST 800-171 SSP:** The contractor documented a separate NIST SP 800-171 System Security Plan in addition to the FedRAMP SSP. The 800-171 plan maps its 110 requirements to the 800-53 control implementations already documented in the FedRAMP package, reducing duplication. The primary additional 800-171 work was in the DFARS-specific incident reporting requirements (report to DIBNet portal within 72 hours) and media sanitization requirements for data exports.

**Encryption for CDI fields:** Shield Platform Encryption was enabled with Bring Your Own Key using a key stored in an AWS GovCloud KMS key hierarchy. CDI-tagged fields (program financial data, vendor performance assessments, contract numbers linked to classified programs) were encrypted at the field level. Key rotation was set to 90 days.

**AppExchange audit:** Of the 11 AppExchange packages initially planned, 6 were confirmed GovCloud Plus-authorized. The remaining 5 were either unavailable for GovCloud Plus or pending authorization. Three of the five were replaced with native Salesforce functionality; two were deferred pending vendor authorization.

**DevOps pipeline:** The team's existing CI/CD pipeline used GitHub Actions on GitHub Enterprise Cloud commercial. This was not compliant — pipeline compute was not in a FedRAMP boundary. The pipeline was migrated to GitHub Enterprise Cloud for Government (GovCloud) which holds a FedRAMP High authorization. All Salesforce DX commands, Apex test runs, and deployment scripts were moved to GitHub-hosted runners on the government tenant.

**IL4 compliance gap:** The program office's security officer initially requested IL5 assurance. The team confirmed that the data did not meet the IL5 threshold (no NSS data, no higher sensitivity CUI categories listed in the CUI Registry as requiring IL5). The IL4 designation was documented in the Authorization Boundary diagram with explicit exclusion language for NSS data.

**Outcome:** The GovCloud Plus Hyperforce deployment achieved IL4 compliance. The DFARS 252.204-7012 assessment confirmed all 110 NIST 800-171 requirements were addressed. CMEK for CDI fields was operational before the first CDI record was created in the system. The CI/CD pipeline on GitHub Enterprise Government reduced deployment time while maintaining FedRAMP boundary integrity.
