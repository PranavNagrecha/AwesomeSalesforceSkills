# Gotchas — Government Cloud Compliance

"Government Cloud guide" below means the Salesforce *Government Cloud* guide (`government_cloud.pdf`, Spring '26 edition served under the 262 release path). Claims that rest on external government frameworks (NIST, OMB, DISA, CMS) or on pages this pass could not fetch carry an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: AppExchange Packages Sit Outside the Authorization Boundary

**What happens:** A team designs a Government Cloud Plus solution around four AppExchange managed packages (document generation, e-signature, a CPQ add-on, scheduling) and treats them as covered by the Salesforce authorization. They are not. The Government Cloud guide ("Using AppExchange with Government Cloud") says AppExchange and the apps listed on it are not included in the authorization boundaries of Government Cloud Plus or Government Cloud Plus - Defense, and the FedRAMP and DoD authorizations do not include AppExchange apps.

Correction (2026-10-03): earlier text said packages "cannot be installed" in a Government Cloud Plus org unless they appear on an authorized products list. The guide says all managed and unmanaged packages are supported when the subscriber org is in Government Cloud, and unsupported only when the subscriber org is outside it. The "Compatible With Government Cloud" and "FedRAMP Compliant" AppExchange labels are self-reported by the ISV, and native apps are generally not eligible for a FedRAMP or DoD provisional authorization at all. The blocker is the authorizing official's risk decision, not installability.

**When it occurs:** Any design built in a commercial org before the Government Cloud Plus org exists, where package choice is treated as a functional decision only.

**How to avoid:** For each package, record the AppExchange labels (Government Cloud, FedRAMP Compliant, Native), cross-check any FedRAMP claim on the FedRAMP Marketplace or DoD Cloud Catalog as the guide recommends, and list every external callout the package makes (the guide's example is Salesforce Maps calling AWS for geolocation). Take the list to the AO with the 3PAO-recommended control set the guide publishes (AT, IR, PS, SA, SI families). Partners should also know that the License Management App cannot update a Government Cloud subscriber's license from outside Government Cloud.

---

## Gotcha 2: New Features Reach Government Cloud Later Than Commercial

**What happens:** A program officer sees a demo of a new Einstein feature and asks for it in the Government Cloud deployment. At go-live the feature is not there. UNVERIFIED (2026-10-03): the "one to two releases" lag in earlier text comes from field experience; the Government Cloud guide only says products are classified as authorized or interoperable and that the guide's answers can change with each release.

**When it occurs:** Any design that references a feature from the last two releases without checking its Government Cloud status.

**How to avoid:** Check the product against "Government Cloud Available Products and Features" (linked from the guide) and record whether it is authorized or interoperable. Get written confirmation from the Salesforce account team for anything not yet listed, and do not tie a contractual delivery date to it. Agentforce is a hard example: the *Generative AI* guide ("Considerations for Agents") says agents are not available for Government Cloud.

---

## Gotcha 3: Commercial Middleware and ETL Tools Break the Boundary

**What happens:** A Government Cloud Plus org syncs records to an agency data warehouse through the integration team's existing commercial iPaaS tenant. The AO rejects the design because federal data transits a system outside any authorized boundary. The Government Cloud guide defines the authorization boundary as a logical barrier around the components inside the operating zone that also specifies interactions with external systems, so every hop has to be accounted for.

**When it occurs:** Integration designs drawn by teams with commercial experience who default to familiar tools.

**How to avoid:** Document the platform and authorization status of every hop that receives, processes, stores, or transmits in-scope data. UNVERIFIED (2026-10-03): the earlier list of acceptable platforms (MuleSoft Government Cloud, Azure Integration Services on Azure Government, AWS Step Functions and Lambda on AWS GovCloud, a Boomi FedRAMP environment) reflects vendor marketplace claims not checked in this pass; verify each on the FedRAMP Marketplace at the required impact level. On-premise middleware in the agency's own authorized data center is acceptable if documented in the boundary.

---

## Gotcha 4: Scratch Orgs and Commercial DevOps Habits Do Not Transfer

**What happens:** A team with strong Salesforce DX habits plans scratch-org-based development and a CI pipeline on a commercial runner. UNVERIFIED (2026-10-03): earlier text said scratch org creation is not available in Government Cloud; the Government Cloud guide does not address scratch orgs, so confirm with Salesforce before planning around them either way. The pipeline issue is firmer: runners that pull metadata and test data out of the org are in the data path.

**When it occurs:** Any team moving from commercial DX practice to Government Cloud Plus.

**How to avoid:** Plan on sandboxes created from the Government Cloud production org until scratch-org support is confirmed. Run CI on compute inside an authorized boundary. Mask production data before it lands in Developer or Partial Copy sandboxes (see `security/sandbox-data-masking`).

---

## Gotcha 5: A Significant Change Can Require AO Review Before Deployment

**What happens:** A team ships a new Experience Cloud partner site with new connected apps and sharing changes through normal change management. Weeks later the agency ISO flags it as a significant change that needed prior notification to the authorizing official. UNVERIFIED (2026-10-03): the significant-change obligation comes from NIST SP 800-37 Rev 2 and OMB Circular A-130, which are outside Salesforce documentation and were not fetched in this pass.

**When it occurs:** Teams treating the ATO as a one-time event and applying commercial change management.

**How to avoid:** Write a significant-change policy into the continuous monitoring plan. Typical triggers: a new external integration, a feature that changes the attack surface, a change to encryption key management, a change to authentication methods, or a change to the system boundary (such as a new Experience Cloud site). Route deployments through a significant-change gate and get the AO's written determination before production.

---

## Gotcha 6: Government Cloud Plus Is IL4, Not IL5

**What happens:** A DoD program needs IL5. The team picks Government Cloud Plus because it is FedRAMP High and assumes that is enough. It is not. The Government Cloud guide ("Government Cloud Offerings", "Compliance by Operating Zone") says Government Cloud Plus provides FedRAMP High and DoD IL4 (plus IRS 1075 and NIST SP 800-171 attestations), while Government Cloud Plus - Defense uses physically dedicated, isolated infrastructure for the DoD and holds the DoD IL5 provisional authorization.

Correction (2026-10-03): earlier text said IL5 requires "Hyperforce GovCloud on AWS GovCloud" with customer-managed keys. The guide names Government Cloud Plus - Defense as the IL5 offering. The "FedRAMP High is necessary but not sufficient for IL5" point stands.

**When it occurs:** Programs that conflate FedRAMP High with IL5, or that provision the offering before the IL is confirmed.

**How to avoid:** Confirm the impact level in writing first. For IL5, specify Government Cloud Plus - Defense. Read the DISA Cloud Computing SRG for IL5 obligations (UNVERIFIED 2026-10-03: external document, not fetched). Note that some features differ by zone: Field Service dispatch mapping and Appointment Assistant are interoperable in Government Cloud Plus but not available in Government Cloud Plus - Defense.

---

## Gotcha 7: Deterministic Encryption Is Not FIPS-Validated

**What happens:** The team enables Shield Platform Encryption with deterministic encryption so encrypted fields can still be filtered and matched, then claims FIPS 140 compliance. The Government Cloud guide ("Encryption and Compliance for Government Cloud") says Shield Platform Encryption uses FIPS-validated AES-256 in CBC mode with a random initialization vector by default, and that a static initialization vector (deterministic encryption) is not FIPS-validated.

**When it occurs:** Designs that need filtering, matching, or duplicate rules on encrypted fields.

**How to avoid:** Record each encrypted field with its scheme. Keep probabilistic encryption on fields whose SC-28 evidence must cite FIPS validation. Where deterministic encryption is needed for function, document the risk acceptance with the AO, as the guide suggests reviewing with a partner or Salesforce Customer Support.

---

## Gotcha 8: Information Spillage Cleanup Is the Customer's Job

**What happens:** A user uploads a document above the org's authorization level. The team opens a ticket expecting Salesforce to clean it up. The Government Cloud guide ("Customer Data Information Spillage", "Mitigate Information Spillage") says the customer is responsible for remediation, and Salesforce cannot assess what data types a customer stores. The documented steps are: delete the data through the UI or API, permanently delete it from the Recycle Bin (Modify All Data required to empty the org Recycle Bin), then open a support case to request a physical delete. Shield Platform Encryption customers can instead destroy their key material (cryptographic erase), which the guide warns must be done carefully to limit data loss.

**When it occurs:** Any Government Cloud org without a written spillage runbook.

**How to avoid:** Put a spillage runbook in the incident response plan (IR-9 is in the guide's recommended control set). Name who holds Modify All Data and Manage Encryption Keys for the cleanup. Decide in advance whether cryptographic erase is acceptable for the encrypted data classes, since it renders all data under that key unusable.

---

## Gotcha 9: "Interoperable" Features Send Data Outside the Boundary When Switched On

**What happens:** An admin turns on Field Service map features or mobile analytics in a Government Cloud Plus org. The Government Cloud guide says interoperable products have been functionally tested but not assessed against FedRAMP or DoD boundary requirements. For Field Service, API calls to Google Maps are at the authorization boundary and off by default ("Send geolocation and map data to Google and Apple"), and the mobile app's analytics and crash reports go to third-party systems outside the boundary when "Allow third parties to store mobile analytics data" and "Send crash reports to Microsoft App Center" are turned on.

**When it occurs:** Feature enablement done in Setup without a boundary review, often during UAT when someone wants maps to "just work".

**How to avoid:** Keep a register of interoperable features and their Setup switches. Require an AO risk acceptance before any of them is turned on. Test interoperable features in a non-production environment first, as the guide requires, and remember that restricted networks such as NIPRNet can block them.

---

## Gotcha 10: Salesforce Express Connect Is Not Available to .mil Orgs

**What happens:** A DoD program plans private connectivity with Salesforce Express Connect. The Government Cloud guide ("Connect to Government Cloud Plus via Salesforce Express Connect") says it is not applicable to DoD customers using a `.mil` My Domain, because their traffic traverses the DISA Boundary Cloud Access Point.

**When it occurs:** Network designs copied from civilian agency deployments.

**How to avoid:** For civilian Government Cloud Plus orgs, follow the guide's routing: specific inbound and outbound routes for non-Hyperforce orgs, per-instance routes for Hyperforce Government Cloud, and a support case with the Government Cloud Network Security team for IP-range restrictions. For DoD `.mil` orgs, design around the BCAP path instead.

---

## Gotcha 11: Audit Retention Depends on Licensed Features

**What happens:** The SSP claims field history and event logs are retained for the agency's AU-11 period, but only standard features are licensed. The Salesforce Security Guide ("Field History Tracking") says that without Field Audit Trail, field history is kept for up to 18 months (24 months through the API). With Field Audit Trail on, it is kept until you delete it, under a `HistoryRetentionPolicy`. The Object Reference (`EventLogFile`) says Shield and Event Monitoring customers get 1 year of event log file storage by default.

Correction (2026-10-03): the control-mapping table earlier described Field Audit Trail as "10-year field history". The current Security Guide wording is retention until deleted, governed by the retention policy.

**When it occurs:** SSP control statements written from marketing summaries rather than from the licensed feature set.

**How to avoid:** Write AU-11 statements from what is licensed. If the retention period exceeds 1 year for event logs, export them nightly to an authorized log store. Define `HistoryRetentionPolicy` per object when Field Audit Trail is on.
