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

**Compliance automation:** Shield Event Monitoring was licensed and configured. A nightly Apex scheduled job queries the EventLogFile object and pushes LoginEvent, ReportEvent, ApiEvent, and BulkApiResultEvent records (note 2026-10-03: those four are Real-Time Event Monitoring storage objects, queried directly; `EventLogFile` holds the separate daily or hourly log files, and the bulk results object is `BulkApiResultEventStore`) to the agency's Splunk SIEM instance (also FedRAMP-authorized). The SIEM is configured to alert on off-hours data export events and bulk API calls exceeding 10,000 records.

**Feature gap findings:**
- The team had planned to use an AppExchange document generation package. The package was not on the GovCloud Plus authorized list. (Correction 2026-10-03: the Government Cloud guide says AppExchange apps sit outside the authorization boundary and packages install in a Government Cloud subscriber org; the real reason to drop it was the AO declining the risk of its external document-rendering callout.) The agency replaced it with a Salesforce-native document generation approach using Visualforce PDF templates.
- Einstein Case Classification was not yet FedRAMP High authorized at the time of the migration. The feature was removed from the initial go-live scope and added to the post-ATO feature roadmap pending Salesforce's re-authorization cycle.

**Outcome:** The org migration to GovCloud Plus was completed. The agency submitted an ATO package with a complete SSP covering all 241 customer-owned and shared controls, a POA&M with 14 open items (all Low or Moderate risk), and a Security Assessment Report from their 3PAO. ATO was granted. The continuous monitoring cadence was established: monthly POA&M reviews, quarterly significant change assessments, annual 3PAO testing of a rotating subset of controls.

---

## Example 2: DoD Contractor — Designing for IL4 with CUI on Salesforce GovCloud Plus

**Context:** A defense contractor builds a supply chain management application on Salesforce for a Department of Defense program office. The application tracks contract deliverables, vendor performance, and program financial data. Some data elements are classified as Covered Defense Information (CDI) under DFARS 252.204-7012, requiring NIST SP 800-171 compliance. The program office requires DoD IL4, which mandates FedRAMP High as the minimum cloud baseline.

**Architecture decisions made:**

> UNVERIFIED (2026-10-03): the Hyperforce-on-AWS-GovCloud and AWS KMS key-hierarchy details in this example are not in the Salesforce Government Cloud guide. Shield Platform Encryption key management (tenant secrets, customer-supplied key material) is a Salesforce capability; confirm any external-KMS arrangement with Salesforce before copying this design.

**Offering selection:** GovCloud Plus on Hyperforce (AWS GovCloud US-East) was selected. The Hyperforce deployment was chosen over traditional GovCloud Plus because it enables customer-managed encryption keys (CMEK) through AWS Key Management Service in the AWS GovCloud region — a control the DoD program office required for CDI fields. CMEK allows the contractor to demonstrate that Salesforce cannot independently decrypt CDI-containing fields without the customer's key.

**NIST 800-171 SSP:** The contractor documented a separate NIST SP 800-171 System Security Plan in addition to the FedRAMP SSP. The 800-171 plan maps its 110 requirements to the 800-53 control implementations already documented in the FedRAMP package, reducing duplication. The primary additional 800-171 work was in the DFARS-specific incident reporting requirements (report to DIBNet portal within 72 hours) and media sanitization requirements for data exports.

**Encryption for CDI fields:** Shield Platform Encryption was enabled with Bring Your Own Key using a key stored in an AWS GovCloud KMS key hierarchy. CDI-tagged fields (program financial data, vendor performance assessments, contract numbers linked to classified programs) were encrypted at the field level. Key rotation was set to 90 days.

**AppExchange audit:** (Correction 2026-10-03: read "authorized" below as "accepted by the AO after boundary review"; AppExchange apps are outside the Salesforce authorization boundary.) Of the 11 AppExchange packages initially planned, 6 were confirmed GovCloud Plus-authorized. The remaining 5 were either unavailable for GovCloud Plus or pending authorization. Three of the five were replaced with native Salesforce functionality; two were deferred pending vendor authorization.

**DevOps pipeline:** The team's existing CI/CD pipeline used GitHub Actions on GitHub Enterprise Cloud commercial. This was not compliant — pipeline compute was not in a FedRAMP boundary. The pipeline was migrated to GitHub Enterprise Cloud for Government (GovCloud) which holds a FedRAMP High authorization. All Salesforce DX commands, Apex test runs, and deployment scripts were moved to GitHub-hosted runners on the government tenant.

**IL4 compliance gap:** The program office's security officer initially requested IL5 assurance. The team confirmed that the data did not meet the IL5 threshold (no NSS data, no higher sensitivity CUI categories listed in the CUI Registry as requiring IL5). The IL4 designation was documented in the Authorization Boundary diagram with explicit exclusion language for NSS data.

**Outcome:** The GovCloud Plus Hyperforce deployment achieved IL4 compliance. The DFARS 252.204-7012 assessment confirmed all 110 NIST 800-171 requirements were addressed. CMEK for CDI fields was operational before the first CDI record was created in the system. The CI/CD pipeline on GitHub Enterprise Government reduced deployment time while maintaining FedRAMP boundary integrity.

---

## Example 3: Decision Record for a DoD Logistics Office Requiring IL5 with Field Service

**Context:** A DoD logistics office will track depot maintenance work orders and technician dispatch for unclassified but sensitive defense data. The authorizing official has confirmed DoD IL5 in writing. Technicians need the mobile app on site, some sites reach Salesforce only over NIPR, and the program's My Domain is a `.mil` domain. The program office also asked whether an Agentforce agent could answer technician questions.

**Decision record (machine-readable form):**

```yaml
adr: GOV-012
title: Provision Government Cloud Plus - Defense for the depot maintenance system
status: accepted
date: 2026-10-03
context:
  impact_level: DoD IL5 (AO memo on file)
  data: CUI and Covered Defense Information on WorkOrder, ServiceAppointment, Asset
  network: some depots NIPR-only; My Domain on .mil
decision:
  operating_zone: Government Cloud Plus - Defense   # IL5 PA, FedRAMP High P-ATO (JAB), IRS 1075
  editions: Unlimited or Enterprise                  # Government Cloud availability
  field_service: core features + mobile app          # authorized FedRAMP High and DoD IL5
rejected:
  - option: Government Cloud Plus
    reason: authorized to DoD IL4, not IL5
  - option: Salesforce Express Connect for private connectivity
    reason: not applicable to DoD customers on a .mil My Domain (traffic traverses DISA BCAP)
  - option: Agentforce agent for technician Q&A
    reason: agents are not available for Government Cloud (Generative AI guide, Spring '26)
feature_switches:   # Field Service Settings > Advanced Security Settings
  send_geolocation_and_map_data_to_google_and_apple: off   # dispatch mapping not available in this zone
  allow_third_parties_to_store_mobile_analytics_data: off
  send_crash_reports_to_microsoft_app_center: off
encryption:   # Shield Platform Encryption
  default_scheme: probabilistic (FIPS-validated AES-256, CBC, random IV)
  deterministic_fields:
    - field: Asset.SerialNumber
      reason: duplicate matching on serial number
      status: AO risk acceptance required (deterministic is not FIPS-validated)
licences:
  - Shield (Platform Encryption, Event Monitoring, Field Audit Trail)
  - Field Service Mobile user licence for each technician
retention:
  field_history: Field Audit Trail on; HistoryRetentionPolicy per object (kept until deleted)
  event_logs: 1 year in-platform; nightly export to the program SIEM inside an authorized boundary
spillage_runbook:
  owners: [ISSO, Salesforce admin holding Modify All Data, key custodian holding Manage Encryption Keys]
  steps: [delete via UI/API, empty org Recycle Bin, support case for physical delete]
  cryptographic_erase: allowed only for the CDI tenant secret, with ISSO approval
compliance_docs: requested with a .mil email address (FedRAMP package FR2003061248)
consequences:
  - no Google Maps dispatch mapping in this zone; dispatch planning runs without a map view
  - technician Q&A handled by Knowledge search, not an AI agent, until agents are offered in this zone
```

**Package and integration boundary register (excerpt):**

| Item | Type | AppExchange labels | External callouts | FedRAMP Marketplace check | AO decision |
|---|---|---|---|---|---|
| Depot ERP sync | Integration (agency-hosted middleware) | n/a | Agency data center only | Agency system inside its own ATO | Accepted |
| Barcode label printing app | Managed package | Government Cloud, Native | None declared on the install screen | Not eligible (native app) | Accepted with AT/IR/PS/SA/SI controls review |
| Parts catalogue lookup | Managed package | FedRAMP Compliant | Vendor API | Listed at Moderate only | Rejected for IL5 data; rebuild as custom object |

**Why it works:** the operating zone follows the written impact level, every rejected option names the platform fact that rules it out, interoperable switches are recorded as off, and the encryption, retention and spillage entries are the same statements the SSP will make.

