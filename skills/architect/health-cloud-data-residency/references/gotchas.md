# Gotchas — Health Cloud Data Residency

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Hyperforce Infrastructure Agreement and HIPAA BAA Are Separate Contracts — Both Are Required

**What happens:** Architects and procurement teams obtain the HIPAA Business Associate Agreement from Salesforce and consider their contractual data handling obligations satisfied. They do not separately execute the Hyperforce Infrastructure Agreement. When an auditor or DPO asks for documentation that data is stored in a specific region under specific infrastructure terms, the HIPAA BAA does not contain those commitments — regional infrastructure terms are in the Hyperforce Infrastructure Agreement. The two documents address different obligations: the BAA governs PHI handling as a business associate under HIPAA; the Hyperforce Infrastructure Agreement governs where and how data is stored on public cloud infrastructure.

**When it occurs:** During compliance audits, DPIA reviews, or when a data subject exercises GDPR Article 15 (right of access) and asks where their data is processed. Also triggered when the customer's legal team reviews subprocessor disclosures and finds Hyperforce infrastructure providers listed without a corresponding agreement.

**How to avoid:** At project initiation, create a contract checklist that includes both the HIPAA BAA and the Hyperforce Infrastructure Agreement as mandatory items. For EU orgs, also ensure the GDPR Data Processing Addendum is in place. Confirm all three (or whichever subset applies) are fully executed and retained before any PHI enters the system.

---

## Gotcha 2: Einstein Feature Inference Crosses Regional Boundaries Even on Hyperforce EU/AU Regions

**What happens:** A Health Cloud org provisioned in the EU Hyperforce region enables Einstein for Health or Einstein Copilot. Clinicians use Einstein to generate care gap summaries or draft clinical correspondence. The inference request — including PHI in the context window — is routed to Einstein's inference infrastructure, which is not necessarily co-located with the EU Hyperforce region. The org's primary data storage stays in the EU, but the Einstein inference job temporarily processes EU-stored PHI in infrastructure that may be outside the EU. This is a transient processing exception that is documented in Salesforce's AI Data Use Policy and Einstein terms, but not prominently surfaced during feature activation.

**When it occurs:** Any time an Einstein AI feature processes a record that contains PHI and the inference job is dispatched from a Hyperforce EU or AU region org. The most common triggers are Einstein Copilot in Health Cloud, Einstein for Health care gap generation, and any custom prompt template that includes patient record fields.

**How to avoid:** Before activating any Einstein AI feature on a Hyperforce EU or AU org that processes PHI:
1. Review Salesforce's current Einstein AI Data Use Policy and the applicable BAA addendum for Einstein features.
2. Confirm whether Salesforce has published EU or AU region inference availability for the specific feature — this changes as Hyperforce coverage expands.
3. If regional inference is not yet available, either disable the feature for PHI-heavy record types, implement prompt templates that exclude direct PHI identifiers (use anonymized patient identifiers instead of names/DOB/MRN), or obtain written GDPR/My Health Records Act risk acceptance from the DPO/Privacy Officer.
4. Document the decision and its basis in the compliance register.

---

## Gotcha 3: Health Cloud Intelligence (CRM Analytics) Datasets Persist PHI Even After Feature Deactivation

**What happens:** An implementation team enables Health Cloud Intelligence to evaluate population health dashboards during a pilot. PHI flows into CRM Analytics datasets as part of the data recipe. The team later decides not to proceed with Health Cloud Intelligence and deactivates the dashboards. However, the underlying CRM Analytics datasets — which contain PHI — remain in the org and in Salesforce's analytics storage layer. Because HCI operates on a separate compute and storage layer from core Health Cloud, simply removing the dashboards or disabling the HCI permission set does not delete the data from analytics storage.

**When it occurs:** After any pilot or exploratory use of Health Cloud Intelligence, CRM Analytics, or Einstein Discovery that ingested PHI, if the decision is made to discontinue the feature without explicitly deleting the underlying datasets and their storage artifacts.

**How to avoid:** Before running any CRM Analytics recipe against PHI-containing objects in a Health Cloud org:
1. Confirm the Health Cloud Intelligence BAA addendum is in place.
2. Establish a data lifecycle procedure that includes explicit dataset deletion (not just dashboard deletion) as part of any feature deactivation process.
3. When deactivating HCI, use the Analytics Studio interface to delete each dataset explicitly, and confirm deletion via the dataset list — deleted datasets should not appear.
4. If PHI was ingested into CRM Analytics before the BAA addendum was in place, treat this as a potential HIPAA breach event and follow the covered entity's breach notification assessment procedures.

---

## Gotcha 4: Sandbox Full Copy Includes ContentDocument Bodies — PHI in Files Is Often Overlooked

**What happens:** A full sandbox copy from a Health Cloud production org includes all `ContentDocument` and `ContentVersion` records, which contain the actual binary or text content of files attached to Health Cloud records — including scanned insurance cards, clinical documents, lab result PDFs, and patient consent forms. Most PHI audits and Data Mask configurations focus on structured fields in standard and custom objects. The file content stored in `ContentDocument` bodies is frequently overlooked in Data Mask configurations, leaving actual PHI documents accessible to sandbox users who are not covered by the HIPAA BAA.

**When it occurs:** Whenever a Full or Partial sandbox is created from a Health Cloud production org and Data Mask is not explicitly configured to handle `ContentDocument` / `ContentNote` content, which requires nullifying or replacing file body content rather than just masking text fields.

**How to avoid:** Include `ContentDocument`, `ContentNote`, `ContentVersion`, and `Attachment` objects in the sandbox de-identification strategy. For clinical document attachments, the safest approach is to nullify the file body in the Data Mask profile and replace with a synthetic placeholder document. Validate the outcome by spot-checking file attachments on clinical records in the sandbox after Data Mask runs — open actual attached files and confirm no real PHI content is present.

---

## Gotcha 5: MuleSoft Integration Logs May Retain PHI Outside the Hyperforce Region

**What happens:** A Health Cloud org uses MuleSoft to integrate with an EHR system (e.g., Epic or Cerner via HL7 FHIR APIs). MuleSoft Anypoint Platform's runtime logging and monitoring capture request and response payloads for debugging purposes. By default, Anypoint Monitoring and Anypoint Runtime Manager log transaction details — which often include PHI from FHIR resources — in MuleSoft's own infrastructure, which may not be in the same region as the Hyperforce Health Cloud org and is not covered by the Salesforce Health Cloud HIPAA BAA. MuleSoft requires its own separate BAA addendum, and logging configuration must be explicitly adjusted to suppress PHI from appearing in integration logs.

**When it occurs:** Any MuleSoft integration that processes FHIR Patient, Observation, Condition, or similar resources containing PHI, if MuleSoft Anypoint Monitoring or transaction logging is enabled with default settings.

**How to avoid:**
1. Execute the MuleSoft BAA addendum before any PHI flows through MuleSoft integrations.
2. Configure MuleSoft Anypoint Monitoring to mask or suppress PHI from log payloads — use DataWeave payload masking at the integration layer to replace sensitive fields with tokens before they reach logging infrastructure.
3. Confirm MuleSoft's data residency region for the Anypoint Platform Control Plane and Runtime Plane, and verify consistency with the Health Cloud Hyperforce region and applicable data residency requirements.
4. Include MuleSoft in the transient processing exception log and obtain compliance team sign-off.
