# Examples — AI Governance Architecture

## Example 1: Financial Services Firm Deploying Agentforce for Loan Decisioning (EU AI Act Compliance)

**Context:** A financial services firm is deploying an Agentforce agent to assist loan officers with credit assessment and loan decisioning recommendations. The use case involves AI output influencing credit decisions for individual applicants, placing it in the EU AI Act high-risk category. The EU AI Act high-risk compliance deadline is August 2026. The firm currently has Einstein Trust Layer enabled and considers that sufficient governance.

**Problem:** Einstein Trust Layer provides prompt injection detection, toxicity filtering, and zero-data-retention guarantees. It addresses prompt-level safety but does not satisfy EU AI Act Article 9 requirements, which mandate a documented risk management system, conformity assessment documentation, human oversight mechanisms, and technical robustness measures covering the full AI lifecycle. Treating Trust Layer as complete governance leaves the firm exposed to regulatory non-compliance and unable to produce audit evidence for supervisory review.

**Solution:**

```yaml
# AI Governance Framework — Loan Decisioning Agent
# Illustrative configuration mapping, not deployable YAML

Layer 1 — AI/ML Lifecycle:
  model_registry: Salesforce Model Builder (versioned)
  approval_workflow: Apex-triggered approval process before model promotion to production
  training_data_documentation: Data lineage tracked in Data Cloud lineage graph

Layer 2 — Security and Guardrails:
  einstein_trust_layer: enabled
  topic_guardrails:
    - topic: "definitive_credit_decision"
      action: block
      message: "I can provide recommendations only. A human loan officer must make the final credit decision."
  data_masking:
    - field: SSN
    - field: Date_of_Birth
    - field: Account_Number
  byollm_routing: all BYOLLM calls routed through Trust Layer Named Credential

Layer 3 — Audit and Observability:
  generative_ai_audit_trail: enabled (requires Data Cloud)
  export_pipeline: Data Cloud → S3 (daily batch, within 30-day window)
  siem_integration: Splunk — alert on blocked topic attempts > 5/hour
  retention_period: 7 years (S3 Glacier after 90 days)

Layer 4 — Responsible AI Controls:
  human_override: required for all final credit decisions (Flow approval step)
  fairness_monitoring: monthly bias analysis by protected characteristic cohorts
  transparency_documentation: EU AI Act conformity assessment document on file
  explainability: SHAP values logged per recommendation for regulatory evidence
```

**Why it works:** EU AI Act Article 9 requires a risk management system throughout the AI system lifecycle — not just at inference time. The 4-layer framework satisfies Article 9 by covering model lifecycle governance (Layer 1), technical safety measures (Layer 2), continuous audit evidence (Layer 3), and human oversight and transparency (Layer 4). The Data Cloud → S3 export pipeline ensures audit evidence persists beyond the 30-day native Audit Trail retention, which is essential for supervisory inquiries that can arrive years after a credit decision.

---

## Example 2: Healthcare Org Using BYOLLM (OpenAI GPT-4) for Clinical Documentation

**Context:** A healthcare organization has integrated OpenAI GPT-4 as a BYOLLM model in their Salesforce Health Cloud org to assist clinicians with clinical documentation drafting. The integration was built as a Named Credential pointing directly to the OpenAI API endpoint. HIPAA requires comprehensive audit logs of AI interactions involving protected health information (PHI), with a minimum 6-year retention period.

**Problem:** BYOLLM calls made through a Named Credential that bypasses the Einstein Trust Layer do not appear in the Salesforce Generative AI Audit Trail. The organization has audit trail enabled and believes all AI interactions are being logged — but GPT-4 invocations are silently absent from the audit log. A HIPAA audit requesting AI interaction logs for a patient encounter would find no records for any GPT-4 assisted documentation, creating a compliance gap that is invisible until audited.

**Solution:**

```apex
// Illustrative Apex — BYOLLM call routed through Trust Layer (conceptual pattern)
// Real implementation uses ConnectApi.EinsteinLLM or platform Trust Layer routing

public class ClinicalDocumentationService {

    // CORRECT: Route BYOLLM call through Trust Layer Named Credential
    // Named Credential must reference Trust Layer gateway endpoint, not OpenAI directly
    public static String generateDocumentationDraft(String clinicalContext) {
        // ConnectApi.EinsteinLLM routes through Trust Layer — captured in Audit Trail
        ConnectApi.EinsteinLLMGenerationsInput input = new ConnectApi.EinsteinLLMGenerationsInput();
        input.prompt = sanitizeForPHI(clinicalContext); // mask PHI before prompt send
        
        // Trust Layer applies data masking, logs interaction to Generative AI Audit Trail
        // Audit Trail record: timestamp, user, masked prompt, model response, model version
        ConnectApi.EinsteinLLMGenerationsOutput output =
            ConnectApi.EinsteinLLM.generateMessages(input);
        
        logToExternalSIEM(output); // belt-and-suspenders: also log to SIEM for 7-year retention
        return output.generations[0].text;
    }

    // WRONG (anti-pattern): Direct HttpCallout to OpenAI bypasses Audit Trail entirely
    // HttpRequest req = new HttpRequest();
    // req.setEndpoint('callout:OpenAI_Direct/v1/chat/completions'); // NOT routed through Trust Layer
    // Http h = new Http();
    // HttpResponse res = h.send(req); // Audit Trail captures nothing
}
```

**Why it works:** Routing BYOLLM calls through the Trust Layer gateway (via ConnectApi.EinsteinLLM or equivalent Trust Layer Named Credential routing) ensures interactions are captured in the Generative AI Audit Trail. The additional SIEM logging step addresses the 30-day native retention limit — HIPAA requires a 6-year retention minimum, which requires an external pipeline. The PHI data masking step ensures that even if audit log storage is compromised, raw PHI is not exposed in prompt logs.

---

## Anti-Pattern: Treating Einstein Trust Layer Enablement as Complete AI Governance

**What practitioners do:** An architect enables Einstein Trust Layer, reviews the Trust Layer configuration settings (zero-data-retention toggle, content classification, data masking), checks those boxes, and documents "AI governance complete" in the project sign-off. No model registry, no audit trail export pipeline, no Policy-as-Code, no human override workflow.

**What goes wrong:** The Trust Layer addresses prompt-level safety during inference. Model lifecycle governance is absent — models can be updated or replaced without approval gates. The Generative AI Audit Trail either is not enabled (no Data Cloud) or its 30-day retention is not addressed with an export pipeline. Regulatory audits cannot be answered with evidence. BYOLLM integrations added later bypass the audit trail entirely because no routing policy was defined. The organization is exposed to regulatory risk despite believing it has addressed AI governance.

**Correct approach:** Use the 4-layer governance framework. Trust Layer is Layer 2 (Security and Guardrails), not the full governance stack. Governance is complete only when all four layers are designed: AI/ML Lifecycle (model registry and approval gates), Security/Guardrails (Trust Layer), Audit/Observability (Audit Trail + export pipeline), and Responsible AI Controls (human override, fairness monitoring, transparency documentation).
