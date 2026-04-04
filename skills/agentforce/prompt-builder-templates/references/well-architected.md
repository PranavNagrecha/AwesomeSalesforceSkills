# Well-Architected Notes — Prompt Builder Templates

## Relevant Pillars

### Security

Prompt Builder templates are a primary entry point for user-controlled data flowing into an LLM. Security concerns are not optional:

- All prompts pass through the **Einstein Trust Layer** before reaching the LLM. Sensitive data identified by org-level masking rules is redacted from the resolved prompt. This is automatic but must be understood — masking can silently remove the grounded data the LLM needs, causing generic output that looks like a template quality issue but is actually a security feature operating as designed.
- The running user's object and field-level permissions govern which fields can be used in merge fields and surfaced in the resolved prompt. A template may resolve correctly for an admin in preview but fail for an end user with restricted field access.
- Apex grounding code that calls external APIs must enforce callout security: validate the endpoint, use Named Credentials for authentication, and avoid logging resolved prompt content to custom objects where it could be accessed by users without appropriate permissions.

### User Experience

The quality of the generated response is a direct function of the template design:

- Prompt instruction quality (specificity, format constraints, persona assignment) drives output usefulness. Vague instructions produce vague responses regardless of how good the grounding data is.
- Grounding completeness determines factual accuracy. Templates with good instructions but missing or incorrect grounding produce confident hallucinations.
- The Einstein button (Field Generation) and agent action surface (Flex) must be discoverable by users. Activation state, page layout placement, and permission set assignment are all deployment concerns that affect whether users encounter the feature at all.
- Non-determinism is inherent to LLM output. The same prompt and grounding data can produce different responses on successive calls. Design templates with output format constraints (length, structure, tone) to reduce variance to an acceptable range.

## Architectural Tradeoffs

**Record merge fields vs. Flow grounding vs. Apex grounding**

The grounding strategy is the primary architectural decision in prompt template design. Record merge fields are lowest friction and lowest risk — no code, no separate deployment artifact, no runtime failure mode beyond a null field. They are appropriate for the majority of single-object use cases. Flow grounding adds declarative flexibility (multi-object traversal, aggregation, conditional logic) at the cost of a separate flow artifact that must be maintained and tested independently. Apex grounding adds maximum flexibility (external callouts, complex logic) at the cost of code ownership, test coverage requirements, and the silent capability-type mismatch risk described in gotchas.

Choose the simplest grounding strategy that satisfies the data requirements. Escalate to Flow only when merge fields cannot express the required data access. Escalate to Apex only when Flow cannot satisfy the requirement.

**Flex vs. purpose-specific template types**

Flex templates are the most flexible type but have no default deployment surface — they must be explicitly bound to an agent action, quick action, or custom UI component. Purpose-specific types (Field Generation, Sales Email, Record Summary) have dedicated deployment surfaces with platform-managed UX, but they cannot be repurposed outside those surfaces. Do not use Flex to replicate a Field Generation or Sales Email use case unless the standard deployment surface is genuinely insufficient.

## Anti-Patterns

1. **Activating without preview validation** — Activating a template without running Save & Preview against a real record with populated data is the most common cause of blank production output. The editor validates syntax but not runtime resolution. Merge fields that traverse relationships can look correct in the editor and fail silently against records where the relationship is null.

2. **Treating grounding as optional** — Publishing a prompt template that relies entirely on LLM knowledge without grounding it to org data accepts hallucination as a feature behavior. For any use case where factual accuracy matters (customer-facing content, legal terms, financial data), grounding to authoritative CRM or external system data is mandatory, not optional.

3. **Bypassing permission planning for packaged templates** — Distributing prompt templates in a managed package without documenting the Manage Prompt Templates permission requirement in the install guide results in silent feature failure in subscriber orgs. This is systematically misdiagnosed as a packaging bug rather than a permission gap.

## Official Sources Used

- Prompt Template Types — https://help.salesforce.com/s/articleView?id=ai.prompt_builder_standard_template_types.htm&language=en_US&type=5
- Ground Prompt Templates with Salesforce Resources — https://help.salesforce.com/s/articleView?language=en_US&id=ai.prompt_builder_ground_template.htm&type=5
- Prompt Builder Key Concepts — https://help.salesforce.com/s/articleView?id=ai.prompt_builder_key_concepts.htm&language=en_US&type=5
- Add Flow Merge Fields to a Flex Prompt Template — https://help.salesforce.com/s/articleView?id=sf.prompt_builder_add_flows_flex.htm&language=en_US&type=5
- Add Apex Merge Fields to a Flex Prompt Template — https://help.salesforce.com/s/articleView?id=sf.prompt_builder_add_apex_flex.htm&language=en_US&type=5
- Ground Your Prompt Templates with Data Using Flow or Apex (Salesforce Developer Blog) — https://developer.salesforce.com/blogs/2024/04/ground-your-prompt-templates-with-data-using-flow-or-apex
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
