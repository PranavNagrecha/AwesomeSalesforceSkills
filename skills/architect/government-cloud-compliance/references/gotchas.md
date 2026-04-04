# Gotchas — Government Cloud Compliance

## 1. FedRAMP Authorization Does Not Automatically Cover All AppExchange Packages

**What happens:** A team designs a solution for GovCloud Plus that relies on four AppExchange managed packages — a document generation tool, an e-signature integration, a CPQ add-on, and a scheduling tool. None of these packages were checked for GovCloud Plus authorization. The packages are installed in a commercial Salesforce org during development and appear to work correctly. When the GovCloud Plus org is provisioned, three of the four packages cannot be installed because they are not on the Salesforce Government Cloud Plus authorized products list.

**When it occurs:** Any time a solution design proceeds in a commercial Salesforce environment (developer edition, sandbox on commercial cloud) before the GovCloud Plus org is available. This is extremely common because GovCloud Plus orgs take longer to provision and development starts in the available environment.

**Why it matters:** ISV packages that are not FedRAMP-authorized cannot be installed in a GovCloud Plus org regardless of functionality. The ISV must independently complete the FedRAMP authorization process, which can take 6 to 18 months. Replacing a missing package late in a program schedule can cause significant cost and delay.

**What to do:** Before finalizing any solution design for GovCloud Plus, validate every planned AppExchange package against Salesforce's published Government Cloud Plus Products list. Contact the ISV directly if the product is not on the list — some ISVs have authorization in progress. Design native Salesforce alternatives for any package that cannot be confirmed as authorized within the program timeline.

---

## 2. Salesforce Features in GovCloud Lag Commercial Cloud by One to Two Releases

**What happens:** A program officer sees a demo of a new Einstein AI feature at Salesforce World Tour and asks the architecture team to include it in the GovCloud deployment. The feature was generally available on commercial cloud in the Winter '25 release. The team adds it to the design. At go-live, the feature is not available in GovCloud Plus because it has not yet been through the FedRAMP re-authorization cycle for the new functionality.

**When it occurs:** Any time a GovCloud design references a feature announced or released in the last two Salesforce release cycles. New features require Salesforce to update their FedRAMP System Security Plan and potentially conduct a significant change assessment with their 3PAO before the feature can be made available in authorized environments.

**Why it matters:** Committing a program to a feature that is not yet GovCloud-authorized creates a scope gap at go-live. For government contracts with fixed delivery dates, this can create contract compliance issues.

**What to do:** Reference the Salesforce Government Cloud Feature Availability documentation (available through the Salesforce Government Cloud customer portal) before finalizing any feature that was announced or released in the most recent two Salesforce releases. For features in the pipeline, get written confirmation from the Salesforce account team of the expected GovCloud authorization timeline and do not commit to a delivery date that depends on that timeline.

---

## 3. Commercial Middleware and ETL Tools Break the FedRAMP Boundary

**What happens:** A GovCloud Plus deployment needs to sync Salesforce records to an on-premise agency data warehouse. The integration team uses their existing MuleSoft CloudHub (commercial) instance as the middleware layer because it is already configured and familiar. The data flows: GovCloud Plus → MuleSoft CloudHub (commercial) → agency data warehouse. At the FedRAMP boundary review, the agency AO rejects the design because MuleSoft CloudHub commercial is not FedRAMP-authorized, and federal data is transiting through a non-authorized system.

**When it occurs:** Integration designs are almost always drawn by teams with commercial cloud experience who default to the tools they know. The FedRAMP authorization status of middleware tools is rarely checked during the initial integration design phase.

**Why it matters:** Any system that receives, processes, stores, or transmits federal data that is within the ATO boundary must itself be FedRAMP-authorized at the appropriate impact level. A non-authorized system in the data path invalidates the authorization boundary and can result in rejection of the ATO package or a finding requiring boundary restructuring.

**What to do:** For every integration in a GovCloud deployment, document the middleware or integration platform used and confirm its FedRAMP authorization status. Options for commonly used integration platforms: MuleSoft Government Cloud (FedRAMP authorized), Azure Integration Services on Azure Government (FedRAMP High authorized), AWS Step Functions and Lambda on AWS GovCloud (FedRAMP High authorized), Dell Boomi FedRAMP environment. On-premise middleware running in the agency's own FedRAMP-authorized data center is also acceptable if properly documented in the boundary.

---

## 4. Scratch Orgs Are Not Available in GovCloud — Development Workflows Must Change

**What happens:** A development team with strong Salesforce DX experience sets up their local development workflow using scratch orgs, as they do for all commercial cloud projects. They configure a scratch org definition file, set up VS Code with the Salesforce Extension Pack, and begin development. When the GovCloud Plus org is provisioned and they attempt to create scratch orgs from the GovCloud Dev Hub, the command fails. Scratch org creation is not available in Government Cloud.

**When it occurs:** Any team transitioning from commercial Salesforce DX development to GovCloud Plus development without reviewing the GovCloud feature restrictions.

**Why it matters:** Scratch orgs are the foundation of modern Salesforce DX development — disposable, source-driven environments for feature development and testing. Their absence in GovCloud requires significant changes to the development and CI workflow. Teams that do not adapt early end up with slower development cycles and inconsistent environment management practices.

**What to do:** Replace scratch orgs with sandboxes created from the GovCloud production org. Developer sandboxes serve the role of scratch orgs for individual developer work. Partial or Full sandboxes serve the role of staging and UAT environments. Adjust CI/CD pipelines to deploy to sandboxes rather than creating and deleting scratch orgs. Establish a sandbox refresh cadence and a sandbox naming and allocation policy. Data masking (see `security/sandbox-data-masking` skill) is required before loading any production data into developer or partial sandboxes to prevent CUI/PHI from residing in less-controlled environments.

---

## 5. A FISMA Significant Change Can Require a Partial Re-Assessment and Delay Deployments

**What happens:** A Salesforce team deploys a major new module to their GovCloud Plus production org — a new Experience Cloud site for external agency partners, with new Connected Apps, new API integrations, and changes to sharing rules. The deployment goes through the normal Salesforce change management process and is deployed successfully. Three weeks later, the agency ISO flags that this change constituted a significant change under FISMA that required prior notification to the Authorizing Official and potentially a partial security assessment before deployment.

**When it occurs:** Teams treat FedRAMP compliance as a one-time ATO event rather than an ongoing authorization. They apply normal commercial Salesforce change management practices without considering whether a change triggers significant change notification requirements.

**Why it matters:** Deploying a significant change without notifying the AO can void or jeopardize the ATO. FISMA continuous monitoring requirements (per NIST SP 800-37 Rev 2 and OMB A-130) require that the system owner notify the AO of significant changes before they are implemented in production, giving the AO the opportunity to determine whether a partial re-assessment is required.

**What to do:** Define a significant change policy for the Salesforce GovCloud deployment as part of the continuous monitoring plan. Significant changes typically include: adding a new external integration, enabling a new Salesforce feature that changes the attack surface, changing encryption key management, adding or removing user authentication methods, or materially changing the system boundary (e.g., adding a new Experience Cloud site). Route all deployment requests through a significant change review gate before production deployment. For changes determined to be significant, notify the AO and obtain a written determination on whether a partial assessment is required before proceeding.

---

## 6. GovCloud Plus Does Not Guarantee IL5 Compliance Out of the Box

**What happens:** A DoD program team is told by their contracting officer that their system requires IL5. The team selects Salesforce GovCloud Plus because it is FedRAMP High authorized and assumes this is sufficient for IL5. At the IL5 authorization review, the DISA reviewer identifies that the deployment is on traditional GovCloud Plus infrastructure (not Hyperforce AWS GovCloud), that there is no customer-managed encryption key implementation, and that Salesforce support access is not sufficiently restricted to meet the NSS-level personnel security requirements. The IL5 authorization is rejected.

**When it occurs:** FedRAMP High and DoD IL5 are frequently conflated. FedRAMP High is a necessary but not sufficient condition for IL5. IL5 has additional requirements beyond the FedRAMP High control baseline, particularly around personnel security for cloud service provider staff who can access tenant systems, encryption key management, and infrastructure isolation.

**Why it matters:** Building a system to FedRAMP High standards and then discovering IL5 requires additional infrastructure or key management capabilities mid-program creates significant rework. Hyperforce GovCloud with CMEK is materially different from traditional GovCloud Plus in the IL5 context, and migrating between them mid-program is not trivial.

**What to do:** If IL5 is a requirement, do not assume GovCloud Plus is sufficient. Explicitly verify with the DISA Cloud Authorization portal whether GovCloud Plus on Hyperforce with CMEK meets the current IL5 Provisional Authorization requirements. Confirm with the Salesforce account team that the specific Hyperforce GovCloud deployment meets DISA's IL5 provisional authorization. Read the DISA Cloud Computing SRG (Section 5.3 for IL5) before finalizing the infrastructure selection.
