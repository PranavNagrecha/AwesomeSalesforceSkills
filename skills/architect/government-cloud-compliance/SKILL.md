---
name: government-cloud-compliance
description: "Use when architecting or assessing a Salesforce Government Cloud org — covering FedRAMP High authorization, Hyperforce GovCloud on AWS GovCloud regions, GovCloud Plus feature set, data residency and US-only data processing, FISMA continuous monitoring, CMS ARC-AMPE controls, NIST 800-53 control mapping, compliance automation patterns, DoD IL2/IL4/IL5 considerations, and multi-org architecture in government deployments. Triggers: FedRAMP, Government Cloud, GovCloud Plus, Hyperforce government, ATO, FISMA, NIST 800-53, CMS ARC-AMPE, IL4 IL5 DoD, data residency US government, compliance evidence automation, choose between Government Cloud Plus and Government Cloud Plus - Defense. NOT for general security reviews (use architect/security-architecture-review or security/* skills). NOT for platform encryption in isolation (use security/platform-encryption). NOT for general Well-Architected reviews (use architect/well-architected-review)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
tags:
  - fedramp
  - government-cloud
  - govcloud-plus
  - hyperforce
  - fisma
  - nist-800-53
  - ato
  - data-residency
  - cms-arc-ampe
  - dod-il4
  - compliance-automation
inputs:
  - Government program office or agency type (civilian, DoD, health agency, state/local)
  - Required authorization level (FedRAMP Moderate, FedRAMP High, IL2, IL4, IL5)
  - Applicable regulatory frameworks (FISMA, NIST 800-53, CMS ARC-AMPE, DFARS, StateRAMP)
  - Current Salesforce product set and edition (Sales Cloud, Service Cloud, Health Cloud, etc.)
  - Data sensitivity classification (CUI, PHI, PII, CDI, classified or unclassified)
  - Existing ATO status and agency sponsor
  - Integration landscape (which external systems must also be FedRAMP-authorized)
outputs:
  - Government Cloud architecture decision record (GovCloud vs GovCloud Plus vs Hyperforce GovCloud)
  - FedRAMP control applicability matrix (NIST 800-53 families mapped to Salesforce capabilities)
  - Data residency and sovereignty compliance assessment
  - FISMA continuous monitoring plan outline
  - CMS ARC-AMPE applicability checklist (when applicable)
  - Compliance automation pattern recommendations (Shield Event Monitoring, automated evidence)
  - Feature availability gap analysis (GovCloud vs commercial cloud)
  - Integration FedRAMP authorization checklist for connected systems
triggers:
  - "how do I configure Salesforce for FedRAMP High authorization"
  - "which Salesforce government cloud offering supports IL4 or IL5"
  - "how to map NIST 800-53 controls to Salesforce capabilities"
  - "what features are unavailable in Salesforce Government Cloud Plus"
  - "how do I build a continuous monitoring plan for FISMA compliance in Salesforce"
  - "check whether this AppExchange package can be used in our Government Cloud org"
  - "plan the cleanup when someone uploads data above our authorization level"
dependencies:
  - architect/security-architecture-review
  - security/platform-encryption
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

Use this skill when architecting, assessing, or advising on a Salesforce deployment that must meet US government compliance requirements — including FedRAMP Moderate or High authorization, FISMA compliance, DoD Impact Level requirements, CMS ARC-AMPE controls, or any combination of these. The skill covers both the infrastructure dimension (which Salesforce Government Cloud offering to use) and the compliance dimension (what controls to implement, automate, and evidence).

This skill does not replace the `architect/security-architecture-review` skill. That skill covers the org-level security architecture for any Salesforce deployment. This skill is specifically about the government compliance layer on top of that security baseline.

---

## Before Starting

- **What is the authorization level?** FedRAMP Moderate vs High changes the control baseline, the authorized features, and the infrastructure requirement. Confirm this before advising on anything else.
- **Is this civilian federal, DoD, or a state/local government deployment?** DoD programs require Defense Information Systems Agency (DISA) IL categorization in addition to FedRAMP. State programs may accept StateRAMP rather than FedRAMP. CMS ARC-AMPE applies only to Centers for Medicare and Medicaid Services contractors.
- **What data types are in scope?** Controlled Unclassified Information (CUI), Protected Health Information (PHI), Personally Identifiable Information (PII), and Covered Defense Information (CDI) each have distinct handling requirements that shape the control selection.
- **Is there an existing ATO or is this a new authorization effort?** An existing ATO from a different system can sometimes be leveraged through inheritance from Salesforce's own FedRAMP authorization package if the boundary is correctly scoped.
- **Which integrations are required?** Every external system that receives or transmits federal data must itself be FedRAMP-authorized or meet an equivalent standard. Non-FedRAMP-authorized integrations are a compliance blocker.

---

## Questions to Ask Before Configuring

Ask these before naming an offering or a control. Each traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What a proper design adds over just doing it |
|---|---|---|---|
| "What impact level has the AO confirmed in writing: FedRAMP High, DoD IL4, or DoD IL5?" | Government Cloud Plus is IL4; IL5 needs Government Cloud Plus - Defense (Gotcha 6) | The operating zone to provision | No mid-program migration between zones |
| "Which AppExchange packages and external services are planned, and what callouts do they make?" | AppExchange apps sit outside the authorization boundary (Gotcha 1); every data hop must be accounted for (Gotcha 3) | A package and integration register with labels, FedRAMP Marketplace checks, and callout lists | The AO decides on risk with evidence instead of discovering hops at assessment |
| "Which fields must be encrypted, and do any need filtering or matching?" | Deterministic encryption is not FIPS-validated (Gotcha 7) | A field list with scheme per field | SC-28 statements that cite the right scheme for each field |
| "Who runs spillage cleanup, and is cryptographic erase acceptable?" | Spillage remediation is the customer's job (Gotcha 8) | Named holders of Modify All Data and Manage Encryption Keys, and an erase decision | A tested IR-9 runbook before the first spill |
| "Which interoperable features (maps, mobile analytics, Express Connect) does the business expect?" | Interoperable features send data outside the boundary when on (Gotcha 9); Express Connect is unavailable to `.mil` orgs (Gotcha 10) | A register of switches that stay off without AO acceptance | Setup changes stop being silent boundary changes |
| "Which Shield features are licensed, and what retention does the SSP promise?" | Field history and event log retention depend on licensing (Gotcha 11) | AU-11 retention per data type mapped to licensed features | SSP statements that match what the org actually keeps |

What a proper design adds over "just provisioning Government Cloud": the operating zone matches the confirmed impact level, every package and integration has a recorded boundary decision, and the encryption, spillage, and retention statements in the SSP match the org's real configuration.

---

## Government Cloud Offering Selection

Grounding note (2026-10-03): the Salesforce *Government Cloud* guide (Spring '26) names two current offerings, Government Cloud Plus and Government Cloud Plus - Defense. It mentions FedRAMP Moderate only as one of the authorization boundaries a product can sit inside. The "GovCloud (FedRAMP Moderate)" description below is kept from earlier versions and is UNVERIFIED as a currently sold offering.

### GovCloud (FedRAMP Moderate)

Salesforce Government Cloud is a dedicated, logically separated environment hosted in US-based data centers. It holds a FedRAMP Moderate Authorization to Operate (ATO) sponsored by a federal agency. It is appropriate for systems processing federal data classified at the FISMA Moderate impact level — data whose confidentiality, integrity, or availability loss would have a serious but not catastrophic effect on agency operations.

Key characteristics:
- Dedicated infrastructure, not shared with commercial tenants
- US-only data storage and processing
- FedRAMP Moderate control baseline (800-53 Rev 5, approximately 325 controls; UNVERIFIED 2026-10-03, external FedRAMP figure)
- Supports most Salesforce core clouds: Sales Cloud, Service Cloud, Experience Cloud, Health Cloud
- Feature lag relative to commercial cloud — features often arrive one to two releases later after FedRAMP re-authorization
- No scratch orgs in GovCloud (development must use sandboxes created from GovCloud production orgs; UNVERIFIED 2026-10-03, the Government Cloud guide does not address scratch orgs)

### GovCloud Plus (FedRAMP High)

Salesforce Government Cloud Plus is a more restricted tier designed for FedRAMP High workloads. It meets the requirements for federal systems where data loss or compromise would have a severe or catastrophic effect on agency operations, national security, or public safety. FISMA High systems, many DoD programs, and health data systems holding sensitive PHI at scale require this tier.

Key characteristics:
- Grounded in the Government Cloud guide ("Compliance by Operating Zone"): FedRAMP High P-ATO from the Joint Authorization Board, DoD IL4 provisional authorization, IRS 1075, and NIST SP 800-171 attestations; a FedRAMP-approved 3PAO assesses it annually against NIST SP 800-53A
- Stricter personnel security requirements (US-persons-only for operations and support; UNVERIFIED 2026-10-03)
- FedRAMP High control baseline (approximately 421 controls under 800-53 Rev 5; UNVERIFIED 2026-10-03, external FedRAMP figure)
- Products are classified as authorized (inside the boundary) or interoperable (functionally tested, not assessed). Correction (2026-10-03): AppExchange packages are not "authorized for GovCloud Plus"; the guide says AppExchange apps are outside the boundary and all packages are supported when the subscriber org is in Government Cloud (see `references/gotchas.md` Gotcha 1)
- Additional access controls on Salesforce support access to tenant data (UNVERIFIED 2026-10-03)
- Required for DoD IL4 workloads as the minimum commercially available Salesforce option

### Government Cloud Plus - Defense (DoD IL5)

The Government Cloud guide describes Government Cloud Plus - Defense as physically dedicated and isolated infrastructure for the DoD with security enhancements for IL5 data. It holds the FedRAMP High P-ATO from the JAB, the DoD IL5 provisional authorization, and IRS 1075, with NIST SP 800-171 attestations. Some features differ from Government Cloud Plus: Field Service dispatch mapping and Appointment Assistant are interoperable in Government Cloud Plus and not available in Government Cloud Plus - Defense. Customers that need connectivity to the DoD NIPR network must use Field Service in Government Cloud Plus - Defense.

### Hyperforce for Government

Hyperforce is Salesforce's re-architecture of the platform onto major public cloud infrastructure (AWS, Azure, GCP). The Government Cloud guide confirms Hyperforce Government Cloud orgs exist (it gives separate Express Connect routing for non-Hyperforce and Hyperforce Government Cloud orgs). UNVERIFIED (2026-10-03): the remaining claims in this section (AWS GovCloud regions, infrastructure-layer US-person restrictions, BYOK keys in customer AWS KMS, faster re-authorization) are not in the guide. Correction (2026-10-03): earlier text tied DoD IL5 to Hyperforce; the guide names Government Cloud Plus - Defense as the IL5 offering.

Key differences from traditional GovCloud:
- Underlying compute and storage is AWS GovCloud (US-East and US-West), not Salesforce-owned data centers
- Data residency is enforced by AWS GovCloud region boundaries in addition to Salesforce contractual commitments
- Enables Bring Your Own Key (BYOK) encryption with keys stored in customer-controlled AWS GovCloud KMS
- Generally on a faster compliance re-authorization cycle because AWS GovCloud infrastructure already holds its own FedRAMP High P-ATO

---

## FedRAMP Authorization Concepts

### Authorization to Operate (ATO)

An ATO is the formal authorization from a federal agency to operate a system in its environment. Correction (2026-10-03): earlier text said the ATO is held by Salesforce and sponsored by an agency. The Government Cloud guide says Government Cloud Plus and Government Cloud Plus - Defense hold a FedRAMP High Provisional Authority to Operate (P-ATO) from the Joint Authorization Board; each agency still issues its own ATO for its system, using the Salesforce package (FedRAMP package ID FR2003061248, requested through the FedRAMP Package Access Request Form). Customers leverage the Salesforce authorization through an inheritance model: Salesforce is responsible for controls at the infrastructure and platform layer; the customer agency is responsible for controls at the application and data layer.

The FedRAMP authorization process follows these phases:
1. **System Security Plan (SSP)** — document all controls, their implementation status (inheritable from CSP vs. customer-implemented), and the system boundary
2. **Security Assessment** — third-party assessment organization (3PAO) tests the implementation
3. **Authorization Package** — SSP, Security Assessment Report (SAR), and Plan of Action and Milestones (POA&M) reviewed by the authorizing official
4. **Ongoing Authorization** — continuous monitoring: monthly vulnerability scans, annual assessments, significant change notifications

### Control Inheritance from Salesforce

Salesforce's FedRAMP authorization package documents which NIST 800-53 controls are fully inherited by customer agencies (Salesforce owns the implementation), partially inherited (shared responsibility), and customer-owned. Understanding this boundary is essential for scoping the customer's own SSP.

Typical inheritance model:
- **Fully inherited:** Physical and environmental controls (PE family), media protection at rest at the infrastructure layer (MP), personnel security at the infrastructure layer (PS)
- **Shared/partially inherited:** Audit and accountability (AU) — Salesforce provides audit logging infrastructure; customer must configure Shield Event Monitoring and define log retention policies. Access control (AC) — Salesforce enforces the platform access model; customer implements profiles, permission sets, and MFA policies. Identification and authentication (IA) — Salesforce enforces session policies; customer implements SSO, MFA configuration, and identity lifecycle management.
- **Customer-owned:** Configuration management for org configuration (CM), incident response procedures (IR), contingency planning for the agency's own data recovery (CP), awareness and training (AT)

---

## NIST 800-53 Control Family Mapping

The following families are most directly addressed by Salesforce GovCloud Plus configuration decisions:

| Control Family | Salesforce Implementation |
|---------------|--------------------------|
| AC — Access Control | Profiles, permission sets, OWD, sharing model, Connected App OAuth scopes, MFA enforcement |
| AU — Audit and Accountability | Shield Event Monitoring (login, data export, report export), Field Audit Trail (retains field history until deleted under `HistoryRetentionPolicy`; corrected 2026-10-03 from "10-year", per the Security Guide), standard audit trail |
| IA — Identification and Authentication | MFA enforcement, SSO via SAML 2.0, session policies, password policies, certificate-based auth for integrations |
| SC — System and Communications Protection | Platform Encryption (at-rest; probabilistic AES-256 is FIPS-validated, deterministic is not), TLS 1.2+ enforcement for all connections, Named Credentials (HTTPS only), network routing restrictions |
| SI — System and Information Integrity | Shield Platform Encryption key rotation, Event Monitoring anomaly detection, field history tracking for data integrity |
| CM — Configuration Management | Change sets, Salesforce DX, metadata backup, sandbox refresh policies, change management process |
| CP — Contingency Planning | Backup/restore SLA documentation, sandbox restore testing, RTO/RPO documentation for org data |

---

## Data Residency and US-Only Processing

Salesforce Government Cloud contractually commits to storing and processing all customer data within the United States. For Hyperforce GovCloud, this boundary is additionally enforced by AWS GovCloud region geography. UNVERIFIED (2026-10-03): neither sentence appears in the Government Cloud guide, which says the service runs on dedicated servers in an environment dedicated to government users and contractors; confirm the residency commitment in the contract. Key requirements to verify:

- **No cross-border data flows:** Any integration that sends Salesforce data to a non-US endpoint violates the data residency boundary unless the data is non-sensitive and explicitly excluded from the ATO boundary.
- **Backup and replication:** Salesforce's backup infrastructure for GovCloud is US-only. For Hyperforce GovCloud, replication is between AWS GovCloud US-East and US-West.
- **Support access:** GovCloud Plus restricts Salesforce support access to US-persons only. Log review and incident response by Salesforce engineers must occur within the US.
- **Org export and ETL tools:** Any ETL, data loader, or middleware that extracts GovCloud data must run on US-based infrastructure. Running the Salesforce Data Loader on a laptop that syncs to a cloud storage service outside the US is a residency violation.
- **Analytics and reporting:** CRM Analytics workloads in GovCloud are US-only. Exporting datasets to external BI tools running outside the US boundary is a compliance violation.

---

## FISMA Continuous Monitoring

FISMA requires ongoing security authorization — not just a one-time ATO. The key continuous monitoring obligations for Salesforce GovCloud deployments:

1. **Monthly vulnerability scanning** — Salesforce performs infrastructure-level scanning. Customer must additionally scan any custom-deployed infrastructure (middleware servers, integration platforms) that sits within the ATO boundary.
2. **Annual control assessments** — A subset of the 800-53 controls must be tested each year. Work with the agency AO to define the annual assessment scope.
3. **Significant change notifications** — Adding a new integration, enabling a new Salesforce feature, or changing the permission model in a material way may constitute a significant change requiring notification to the agency AO and potentially a partial re-assessment.
4. **POA&M management** — All identified control weaknesses must be entered into the Plan of Action and Milestones. POA&M items must have assigned owners, milestone dates, and status updates in monthly reporting to the agency.
5. **Incident reporting** — Security incidents must be reported to US-CERT within one hour of discovery for major incidents, per OMB M-20-04 (UNVERIFIED 2026-10-03: external federal requirement, not in Salesforce documentation; confirm the current reporting rule with the agency ISSO). The agency must define the incident response playbook that interfaces with Salesforce's incident notification process.

---

## CMS ARC-AMPE Controls

UNVERIFIED (2026-10-03): this section describes CMS frameworks that are outside Salesforce documentation and were not fetched in this pass; confirm every statement with the CMS program's ISSO before relying on it.

The Centers for Medicare and Medicaid Services (CMS) Acceptable Risk Safeguards (ARS) combined with the Application, Repository, and Collaboration (ARC) and the Application Modernization and Platform Engineering (AMPE) framework applies specifically to CMS contractors and systems that process Medicare and Medicaid data. If the deployment is for a CMS program:

- CMS ARS is CMS's overlay on top of NIST 800-53 — it adds CMS-specific controls and tightens some baselines beyond the FedRAMP High requirement
- CMS requires its own separate ATO process through the CMS CISO office, in addition to the FedRAMP authorization
- CMS ARC-AMPE imposes specific controls on change management, continuous integration/deployment pipelines, container security, and developer access — all of which affect how Salesforce DX pipelines must be configured
- CMS Health Insurance Portability and Accountability Act (HIPAA) controls are additive to FISMA controls — a CMS Salesforce deployment typically must satisfy FedRAMP High, CMS ARS, and HIPAA simultaneously

---

## DoD Impact Level Considerations

The Defense Information Systems Agency (DISA) Cloud Computing Security Requirements Guide (CC SRG) defines Impact Levels (IL) for DoD cloud deployments:

| Impact Level | Data Sensitivity | Minimum Salesforce Offering |
|-------------|-----------------|----------------------------|
| IL2 | Public, unclassified, non-CUI | GovCloud (FedRAMP Moderate) (UNVERIFIED 2026-10-03; the guide lists IL2 as an authorization boundary but no current IL2-only offering) |
| IL4 | Controlled Unclassified Information (CUI), Covered Defense Information (CDI) | Government Cloud Plus (FedRAMP High, DoD IL4 PA) |
| IL5 | National Security Systems (NSS) unclassified, higher sensitivity CUI | Government Cloud Plus - Defense (DoD IL5 PA); corrected 2026-10-03 from "Hyperforce GovCloud on AWS GovCloud" |
| IL6 | Classified information (SECRET) | Not available on commercial Salesforce (UNVERIFIED 2026-10-03; the guide does not mention IL6) |

IL5 workloads require Government Cloud Plus - Defense and additional customer-implemented controls around personnel vetting, audit log isolation, and encryption key management. IL6 is not available on any commercial Salesforce offering (UNVERIFIED 2026-10-03).

DFARS 252.204-7012 (Safeguarding Covered Defense Information) requires NIST SP 800-171 compliance for contractors handling CDI. NIST 800-171 maps to a subset of NIST 800-53, so GovCloud Plus FedRAMP High provides a strong baseline — but customers must still document their 800-171 System Security Plan separately.

---

## Compliance Automation Patterns

Manual evidence collection for FedRAMP audits is labor-intensive and error-prone. The following automation patterns reduce audit burden:

### Shield Event Monitoring for Audit Evidence

Shield Event Monitoring provides API access to 50+ event types (UNVERIFIED 2026-10-03: count not checked). Real-Time Event Monitoring stores events in queryable objects listed in the Platform Events Developer Guide ("Real-Time Event Monitoring Objects"). For FedRAMP AU controls, configure automated export of:
- `LoginEvent` — captures all authentication attempts, IP addresses, and outcomes (AU-2, AU-12)
- `ReportEvent` and `ListViewEvent` — data access audit evidence (AU-2, AU-3)
- `FileEventStore`: file events. Correction (2026-10-03): earlier text named a `ContentDistributionEvent` object; no such Real-Time Event Monitoring object is listed in the Platform Events Developer Guide (AU-9)
- `ApiEvent` and `BulkApiResultEventStore`: programmatic data access and bulk results (AU-12)
- `PermissionSetEventStore`: permission set assignment events, useful AC-2 evidence

Separately, use the `EventLogFile` object via the REST API to extract daily or hourly log files nightly and push them to a SIEM or audit log repository that meets the AU-9 protection requirement. Shield and Event Monitoring customers get 1 year of event log file storage by default (Object Reference, `EventLogFile`).

### Automated Control Evidence Collection

For recurring audit evidence packages, automate:
- Profile and permission set configuration snapshots (retrieve via Metadata API on a weekly schedule for CM-6 evidence)
- Connected App inventory with OAuth scope and IP restriction settings (for AC-17 evidence)
- MFA enforcement status — query `UserLogin` object and `AuthConfig` metadata for IA-5 evidence (UNVERIFIED 2026-10-03: `UserLogin` records frozen and password-lock state, not MFA; confirm the evidence source before citing it)
- Platform Encryption configuration export: retrieve `PlatformEncryptionSettings` metadata for SC-28 evidence. Correction (2026-10-03): earlier text named an `EncryptionPolicy` metadata type, which the Metadata API Developer Guide does not list
- Field Audit Trail configuration — document retained fields and retention period for AU-11 evidence

### Salesforce Flow for Control Attestation

Use Salesforce Flow or Apex scheduled jobs to:
- Alert the security team when a permission set with sensitive access is assigned to a new user (AC-2 account management)
- Alert when a Connected App's last-used date exceeds 90 days (AC-2, stale access)
- Alert when an admin-level profile change is made without an associated change ticket in the org's ITSM system (CM-3)

---

## Feature Availability in GovCloud

GovCloud and GovCloud Plus do not have feature parity with commercial Salesforce. Architects must explicitly confirm feature availability before including a commercial cloud capability in a GovCloud design:

- **Einstein AI features:** Generally available in GovCloud with a lag (UNVERIFIED 2026-10-03); some Einstein GPT and generative AI features are not yet FedRAMP-authorized. Confirm current status in the Salesforce Government Cloud Feature Availability Guide before designing Einstein-dependent solutions.
- **AppExchange managed packages:** Correction (2026-10-03): packages are not "authorized for GovCloud Plus". The Government Cloud guide says AppExchange apps sit outside the authorization boundary, all packages are supported when the subscriber org is in Government Cloud, and the Government Cloud, FedRAMP Compliant and Native labels are ISV self-reported. Before selecting an ISV, verify any FedRAMP claim on the FedRAMP Marketplace, list the package's external callouts, and get the AO's risk decision.
- **Scratch orgs:** Not available in GovCloud (UNVERIFIED 2026-10-03). Development workflows must use sandboxes created from the GovCloud production org. Salesforce DX project configuration must point to GovCloud instances.
- **Hyperforce-specific features:** Some Hyperforce capabilities (Customer-Managed Encryption Keys via AWS KMS, certain data residency selectors) are available only on Hyperforce GovCloud, not on the traditional GovCloud infrastructure (UNVERIFIED 2026-10-03).
- **Agentforce / Agent Studio:** The *Generative AI* guide ("Considerations for Agents", Spring '26) says agents are not available for Government Cloud. Do not include Agentforce agents in a Government Cloud design; design conversational needs with Einstein Bots and human routing, and recheck each release.
- **Field Service:** authorized for FedRAMP High and DoD IL5. Google Maps dispatch features and mobile analytics are off by default and send data outside the boundary when turned on (Government Cloud guide).

---

## Multi-Org Architecture in Government

Government deployments frequently span multiple Salesforce orgs to address program, security, or data separation requirements:

- **Program separation:** A large agency may maintain separate Salesforce orgs for different programs or business units to enforce data isolation between programs with different data classifications. Design cross-org integration using FedRAMP-authorized middleware only.
- **Sandbox strategy:** GovCloud sandboxes are created from the GovCloud production org and inherit the GovCloud compliance posture. Data masking (see `security/sandbox-data-masking`) is required before loading production data into sandboxes to prevent CUI/PHI from residing in non-production environments without equivalent controls.
- **DevOps pipeline restrictions:** CI/CD pipelines must run on FedRAMP-authorized compute. GitHub Enterprise Cloud GovCloud, GitLab FedRAMP, or Bitbucket Data Center are acceptable (UNVERIFIED 2026-10-03: vendor authorization claims not checked; confirm on the FedRAMP Marketplace). Running pipelines on commercial GitHub Actions or standard Bitbucket Pipelines to deploy to a GovCloud org creates a compliance boundary violation.
- **Connected app inventory:** Each org-to-org integration (e.g., Salesforce-to-Salesforce integration) requires a Connected App with documented OAuth scopes and is subject to the AC-17 remote access control requirements.

---

## Recommended Workflow

1. **Classify the data and determine the authorization level** — confirm FISMA impact level (Low/Moderate/High), DoD IL (if applicable), and any agency-specific overlays (CMS ARS, StateRAMP) before any architecture decisions.
2. **Select the Salesforce Government Cloud offering** — Government Cloud Plus for FedRAMP High and DoD IL4, Government Cloud Plus - Defense for DoD IL5; record each required capability as authorized, interoperable, or unavailable (agents are unavailable).
3. **Map customer-owned controls** — use the Salesforce FedRAMP inheritance matrix to identify which NIST 800-53 controls are customer-owned and build the System Security Plan (SSP) control implementation statements.
4. **Design compliance automation** — configure Shield Event Monitoring exports, automated evidence collection, and alert flows for the high-priority AU, AC, and CM control families before go-live.
5. **Validate integration and package boundary decisions** — for every external system and AppExchange package, confirm FedRAMP status on the FedRAMP Marketplace, list external callouts, and record the AO's decision; then run `python3 skills/architect/government-cloud-compliance/scripts/check_government_cloud_compliance.py --manifest-dir <retrieved-metadata>` to catch common FedRAMP High configuration gaps.
6. **Establish continuous monitoring cadence** — define POA&M management process, significant change notification procedures, and monthly reporting artifacts before ATO submission.
7. **Conduct ongoing feature availability checks** — before each Salesforce release, review the Government Cloud Feature Availability Guide for newly authorized features and for any features being removed from the authorized set.

---

## Related Skills

- `architect/security-architecture-review` — org-level security architecture review applicable to all Salesforce deployments; use as the security baseline before applying GovCloud-specific controls
- `security/platform-encryption` — Shield Platform Encryption design and BYOK patterns; required for SC-28 (protection of information at rest) in FedRAMP High deployments
- `architect/well-architected-review` — full WAF review across Security, Reliability, and Performance pillars; use for holistic architecture quality assessment
- `devops/bitbucket-pipelines-for-salesforce` — CI/CD pipeline patterns; must be adapted for FedRAMP-authorized compute in government deployments
- `architect/salesforce-shield-architecture` and `security/event-monitoring`: Shield licensing, Event Monitoring exports, and Field Audit Trail retention behind the AU-family statements
- `security/sandbox-data-masking`: masking production data before it lands in sandboxes
