---
name: prompt-builder-templates
description: "Use when creating, reviewing, or troubleshooting Prompt Builder templates (Field Generation, Record Summary, Sales Email, or Flex types), including grounding with merge fields, Flow, or Apex. Trigger keywords: prompt template, Prompt Builder, field generation, record summary, sales email template, flex template, grounding, merge fields, LLM template, Einstein generative AI. NOT for agent topic instructions, Copilot action configuration, or Data Cloud segment activation."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - User Experience
tags:
  - prompt-builder
  - generative-ai
  - grounding
  - merge-fields
  - flex-template
  - einstein
inputs:
  - Target Salesforce object and field (for Field Generation templates)
  - Business use case and desired LLM output format
  - Data sources to ground the template (record fields, related objects, Flow, or Apex)
  - Target deployment surface (record page, agent action, email, quick action)
outputs:
  - Completed prompt template package ready for activation
  - Grounding strategy recommendation (merge fields vs. Flow vs. Apex)
  - Review findings for existing templates (permission gaps, inactive versions, missing grounding)
  - Troubleshooting guidance for templates returning blank or hallucinated responses
triggers:
  - how do I create a prompt template in Prompt Builder
  - my prompt template is returning blank or empty output
  - how do I ground a prompt template with related record data
  - flex template not working as expected in agent action
  - how do I share or package a prompt template across orgs
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Prompt Builder Templates

This skill activates when a practitioner needs to create a new prompt template in Prompt Builder, audit or review an existing template library, or diagnose why a prompt template is returning unexpected output. It covers all four standard template types — Field Generation, Record Summary, Sales Email, and Flex — and all grounding strategies.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Einstein generative AI is enabled in the org (`Setup > Einstein > Generative AI Settings`). Prompt Builder is unavailable without this.
- Identify the template type needed. Each type has a different deployment surface and a different set of allowed grounding approaches.
- Confirm the user has the **Manage Prompt Templates** (also referred to as Prompt Template Manager) permission. Without it, the user cannot create, edit, activate, or package templates — and this permission is required even to see templates in packages.
- Determine whether grounding data lives entirely inside Salesforce CRM, requires external systems, or requires Data Cloud. The answer drives the grounding strategy choice.
- Only one version of a template can be active at a time. Understand whether there is an active version before making changes.

---

## Core Concepts

### Template Types

Salesforce Prompt Builder (part of Einstein 1 Studio) provides four standard prompt template types, each scoped to a specific deployment surface. (Source: [Prompt Template Types](https://help.salesforce.com/s/articleView?id=ai.prompt_builder_standard_template_types.htm&language=en_US&type=5))

**Field Generation** — Populates a specific field on a Salesforce record using an LLM response. The template is bound to an object and a target field. An Einstein button appears in Lightning Experience to trigger generation. Field Generation is unsupported for rich text area fields on Knowledge entities.

**Record Summary** — Generates a natural-language summary of a Salesforce record (Opportunity, Case, Contact, etc.) by consuming record data and related activity. Displayed in a dedicated summary panel on the record page.

**Sales Email** — Drafts personalized outbound emails for sales reps using record data such as Opportunity, Contact, and Account fields. Renders in the activity composer.

**Flex** — A general-purpose template type for any use case not covered by the three types above. Flex templates accept up to five custom inputs defined at authoring time. They can be surfaced via agent actions, quick actions, screen flows, or custom UI. Flex templates are the correct type to use when integrating with Agentforce agent actions.

### Grounding Strategies

Grounding connects prompt template placeholders to real Salesforce data so the LLM produces contextually accurate output rather than hallucinated content. There are five grounding mechanisms, and they can be combined within a single template. (Source: [Ground Prompt Templates with Salesforce Resources](https://help.salesforce.com/s/articleView?language=en_US&id=ai.prompt_builder_ground_template.htm&type=5))

**Record Merge Fields** — Pull field values directly from the anchor record using the Insert Resource panel. This is the simplest approach and covers the majority of single-object scenarios. Syntax resolves at runtime against the context record.

**Flow Merge Fields** — Invoke a Template-Triggered Prompt Flow that is bound to the template. The flow uses an "Add Prompt Instructions" element (additive, can be used multiple times) to inject computed text. Use this approach when data assembly requires traversing multiple objects, running calculations, or filtering related records that cannot be expressed as a simple merge field.

**Apex Merge Fields** — Call an `@InvocableMethod`-annotated Apex class. The method receives a `List<Request>` containing invocable variables mapped from template inputs, processes data (including callouts to external systems), and returns a `List<Response>` with a `prompt` string variable. The capability type assigned to the method must match the template type (e.g., `FlexTemplate://template_API_name` for Flex templates). Use Apex when external API calls, complex business logic, or transformations beyond Flow capability are required.

**Related List Merge Fields** — Surface structured data from related records (e.g., last five cases on an Account). Limited to CRM data; cannot pull from external systems.

**Einstein Search Retriever** — Unstructured content retrieval from external knowledge sources indexed by Einstein Search. Useful for surfacing knowledge article content, documentation, or product specifications.

### Versioning and Activation

Every save of a template creates a numbered version. Activation makes exactly one version live; only the active version is resolved at runtime. To make changes to a live template, save a new version, test it in preview, then activate the new version (which automatically deactivates the previous). Deactivating a template without activating a replacement disables the feature for all users immediately.

Audit trail does not capture template creation or version changes. Maintain version discipline through naming conventions or an external change log.

### Einstein Trust Layer Integration

All prompts generated from Prompt Builder templates pass through the Einstein Trust Layer before reaching the LLM. The Trust Layer masks sensitive data (PII, credentials) identified in the org's data masking rules, encrypts data in transit, and never stores prompt data outside Salesforce. This behavior is automatic and non-bypassable; it is not configured in Prompt Builder itself. (Source: [Einstein Trust Layer](https://help.salesforce.com/s/articleView?id=ai.einstein_trust_layer_about.htm&language=en_US&type=5))

---

## Common Patterns

### Mode 1 — Create a New Prompt Template

**When to use:** A practitioner needs to build a net-new template from scratch for a defined use case.

**How it works:**

1. Confirm Einstein generative AI is enabled and the user has Manage Prompt Templates permission.
2. Navigate to `Setup > Einstein 1 Studio > Prompt Builder > New Prompt Template`.
3. Select the template type. For agent action integration, select **Flex**. For field population, select **Field Generation** and choose the target object and field.
4. Write the prompt body in natural language. Use the **Insert Resource** panel to add merge fields rather than typing raw field API names — the panel validates field availability.
5. Choose a grounding strategy based on data location and complexity (see Decision Guidance below).
6. Use **Save & Preview** with a real record to inspect the Resolved Prompt (substituted merge fields) and the Generated Response side-by-side. Iterate on the prompt text and grounding before activating.
7. Click **Activate** when the preview output meets quality expectations.
8. For Field Generation: use App Builder to bind the activated template to the field's Einstein button on the record page. For Flex: assign the template to an agent action or quick action.

**Why not skipping Preview:** Activating without previewing against real data is the primary cause of blank output in production — merge fields that look correct in the editor often fail to resolve against real records if the field API name or relationship traversal is wrong.

### Mode 2 — Review or Audit an Existing Template Library

**When to use:** Assessing an org's prompt template posture before a release, or identifying why specific templates are not surfacing for users.

**How it works:**

1. Navigate to `Setup > Einstein 1 Studio > Prompt Builder`. Review all templates and note their active/inactive status and type.
2. For each template, check that at least one version is active. Inactive templates produce no output and show no error to end users — they silently do nothing.
3. Verify that users who need the template output have the correct permission set or profile settings. Field Generation and Record Summary require that the running user's profile or permission set includes access to the object and fields used in the template, in addition to the Manage Prompt Templates permission for authors.
4. Confirm that any Flow or Apex grounding resources referenced in templates are themselves active and deployable to production.
5. If templates are packaged, confirm subscribers have the Manage Prompt Templates permission — package installation succeeds without it, but templates cannot be invoked.

### Mode 3 — Troubleshoot Grounding Failures

**When to use:** A template that was previously working returns blank responses, partial responses, or clearly hallucinated content after a metadata change, deployment, or data change.

**How it works:**

1. Open the template in Prompt Builder and use **Save & Preview** with a representative record.
2. Inspect the **Resolved Prompt** panel. If merge fields appear unresolved (showing the raw token instead of a value), the field reference or relationship path is broken. Check whether the field was renamed, whether the object relationship changed, or whether the record used in preview is missing data.
3. If the Resolved Prompt looks correct but the Generated Response is blank or wrong, the issue is likely in the prompt instruction quality, not the grounding. Refine the instruction text.
4. For Flow-grounded templates: test the underlying Template-Triggered Prompt Flow independently in Flow Builder. If the flow fails, it fails silently in the template — the merge field returns empty string.
5. For Apex-grounded templates: check that the `@InvocableMethod` capability type matches the template API name. A mismatch causes the Apex data to be silently excluded from the resolved prompt.
6. Check Trust Layer masking. If data masking rules are active in production but not in the sandbox where the template was authored, sensitive fields may be masked out of the resolved prompt, causing the LLM to produce generic output. (See `einstein-trust-layer` skill for full masking diagnostics.)

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Data lives on the context record or a directly related object | Record merge fields | Simplest, no code required, resolves at runtime with no latency overhead |
| Data requires traversing multiple objects, filtering, or aggregation | Flow grounding (Template-Triggered Prompt Flow) | Declarative, testable in Flow Builder independently of the template |
| Data requires external API call or logic beyond Flow capability | Apex grounding (`@InvocableMethod`) | Full Apex capability including HTTP callouts, complex queries, transformations |
| Use case involves Agentforce agent action | Flex template | Only Flex supports the flexible input model used by agent actions |
| Use case populates a specific record field via Einstein button | Field Generation | Bound directly to object + field; cannot use Flex for this surface |
| Data includes unstructured knowledge articles or external docs | Einstein Search Retriever | Retrieves and chunks unstructured content before injecting into prompt |
| Template needs to ship in a managed package | Any type, but author must ensure subscribers have Manage Prompt Templates | Package installs without the permission; templates silently fail without it |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Template type matches the intended deployment surface (Flex for agent actions, Field Generation for field population, etc.)
- [ ] At least one version is active
- [ ] Preview tested against a real record showing correct Resolved Prompt and acceptable Generated Response
- [ ] Grounding resources (Flows, Apex classes) are themselves active and deployed
- [ ] Users who will invoke the template have the required object/field permissions in addition to Manage Prompt Templates
- [ ] Trust Layer masking behavior has been validated in the environment where the template will run
- [ ] If packaged: subscriber Manage Prompt Templates permission requirement is documented
- [ ] Version history and change intent recorded (external log if Audit Trail is insufficient)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Silent failure on inactive templates** — When a template has no active version, it fails silently. End users see no Einstein button, no error, and no diagnostic message. The template simply does not render. This causes false debugging trails when practitioners assume the issue is a permission or page layout problem.

2. **Manage Prompt Templates required in package subscriber orgs** — When prompt templates are distributed via a managed package, the package installs successfully without the subscriber having Manage Prompt Templates permission. The templates exist in the org but cannot be invoked. This is undocumented in the package install flow and results in support escalations post-deployment.

3. **Flow grounding failures are silent in the resolved prompt** — If a Template-Triggered Prompt Flow errors at runtime (invalid SOQL, governor limit hit, null variable), the merge field that references the flow returns an empty string rather than surfacing the error. The resolved prompt appears valid but the grounded data is missing, which causes the LLM to hallucinate or produce generic output. Always test the flow independently before assuming the template is healthy.

4. **Custom objects and fields not immediately available in Prompt Builder** — Newly created custom objects and custom fields do not appear in the Insert Resource panel until the admin logs out and logs back in. Practitioners who create a field and immediately try to add it as a merge field in the same session will not find it in the picker.

5. **Apex capability type mismatch breaks grounding silently** — The capability type string in the `@InvocableMethod` annotation must exactly match the template type identifier. For Flex templates this is `FlexTemplate://your_template_api_name`. For Sales Email it is `PromptTemplateType://einstein_gpt__salesEmail`. A single character mismatch causes the Apex data to be excluded from the resolved prompt with no error surfaced in Prompt Builder or debug logs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Activated prompt template | A named, versioned, active prompt template ready for binding to a deployment surface |
| Grounding strategy decision | Written rationale for merge field vs. Flow vs. Apex choice based on data location and complexity |
| Template review findings | Checklist-based assessment of active status, permissions, grounding health, and Trust Layer compatibility |
| Troubleshooting report | Root cause and remediation steps for blank, partial, or hallucinated template output |

---

## Related Skills

- `einstein-trust-layer` — Diagnose data masking effects on resolved prompts; required reading before troubleshooting templates in production orgs with sensitive data
- `agentforce-agent-creation` — Covers how to bind a Flex prompt template to an agent action
- `scratch-org-management` — Covers metadata deployment of prompt templates across environments using Salesforce DX
