---
name: prompt-builder-templates
description: "Use when creating, reviewing, or troubleshooting Prompt Builder templates (Field Generation, Record Summary, Sales Email, or Flex types), including grounding with merge fields, Flow, or Apex. Trigger keywords: prompt template, Prompt Builder, field generation, record summary, sales email template, flex template, grounding, merge fields, LLM template, Einstein generative AI. NOT for versioning, promoting or rolling back a template — use agentforce/prompt-template-versioning. NOT for Data Cloud vector-search RAG pipelines that ground an agent (chunking, embeddings, retrievers) — use agentforce/rag-patterns-in-salesforce."
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
  - "how do I create a prompt template in Prompt Builder"
  - "my prompt template is returning blank or empty output"
  - "how do I ground a prompt template with related record data"
  - "flex template not working as expected in agent action"
  - "how do I share or package a prompt template across orgs"
  - "prompt builder isn't working"
  - "deploy a prompt template with the Metadata API without breaking the active version"
  - "ground a Field Generation prompt template with an Apex merge field"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Prompt Builder Templates

This skill activates when a practitioner needs to create a new prompt template in Prompt Builder, audit or review an existing template library, deploy templates between orgs, or diagnose why a prompt template is returning unexpected output. It covers the four core template types (Field Generation, Record Summary, Sales Email, and Flex) and every grounding resource Prompt Builder offers.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Einstein generative AI is set up, and that Sales Emails is turned on: the Generative AI guide's Enable Prompt Builder steps include "To build prompt templates, turn on Sales Emails."
- Identify the template type needed. Each type has a different deployment surface and a different set of available merge fields.
- Confirm permission sets: **Prompt Template Manager** for people who create and manage templates (the user must also have access to Setup), and **Prompt Template User** for end users who run them. The Metadata API also requires Prompt Template Manager to retrieve or deploy GenAiPromptTemplate.
- Determine whether grounding data lives on the record, needs logic (Flow or Apex), lives in Data Cloud, or is unstructured (a retriever).
- Only one version of a template can be active at a time, and an activated version becomes immutable. Know which version is active before making changes.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Where will the output appear: a record field, an email composer, a flow, or an agent action?" | Type decides the surface, the merge fields, and the Apex CapabilityType (Gotcha 9) | One template type per surface | The template shows up where users expect it, first time |
| "How will this template move to production: change set, Metadata API, or package?" | Flex templates can't import or export metadata, retrievers don't travel, and the deploy setting can fail templates without an active version (Gotchas 5, 6, 7) | A deployment path and the setting for active-only deploys | Releases don't fail at the end, and no retriever is missing in production |
| "Which data needs Flow or Apex rather than record merge fields?" | Changing a flow's or Apex class's inputs breaks the template and blocks new versions (Gotcha 3) | A frozen input contract for each Flow and Apex resource | Grounding code can evolve without stranding the template |
| "Who changes templates, and how are changes recorded?" | Template changes aren't in the Setup Audit Trail, and activated versions are immutable (Gotchas 1, 4) | A version-naming rule and an external change log | Every live change can be traced and rolled back by activating the prior version |
| "How many merge fields, related lists, and inputs will it use?" | Hard limits: 128,000 characters, 50 versions, 50 merge fields, 5 Flow, 5 Apex, 5 related list merge fields, 5 Flex inputs (Gotcha 8) | A resource count checked against the limits | The template is not redesigned after it is half built |
| "Which records will the preview use?" | Records with no Name or an encrypted Name can't be previewed, and related list grounding follows the running user's page layout (Gotchas 2, 10) | A named preview record set per persona | Preview proves the same data real users will send |

---

## Core Concepts

### Template Types

Prompt Builder lists these template types: Campaign Brief, Contextual Service Replies, Field Generation, Flex, Grounded Service Replies, Knowledge Answers, Provider Account Summary, Record Prioritization, Record Summary, Sales Emails, and Sales Pitch Coaching. The Metadata API `type` values for GenAiPromptTemplate are `einstein_gpt__fieldCompletion`, `einstein_gpt__salesEmail`, `einstein_gpt__recordSummary`, `einstein_gpt__flex`, and `einstein_gpt__caseEmailDraft`. (Source: Generative AI guide, Prompt Template Types; Metadata API, GenAiPromptTemplate.)

**Field Generation**: populates a record field; in Lightning Experience users click a button to run the prompt and fill the field. Bind it to a field on a Lightning record page with Lightning App Builder. It can't be used for rich text areas on Knowledge (`__kav`) entities.

**Record Summary**: summarizes a record and is used by the Summarize Record standard invocable action; agents use the Summarize Record standard agent action.

**Sales Email**: drafts personalized customer email from record data. Merge fields are Recipient (contact or lead), Sender (user), and Current Organization.

**Flex**: content for any purpose the other types don't cover; you define your own resources, up to 5 inputs. UNVERIFIED (2026-10-03): earlier versions said only Flex templates can be used by agent actions; the guide says custom actions that reference a prompt template can use any Salesforce-managed model but does not list which types an agent action accepts.

**Structured output (Spring '26).** GenAiPromptTemplateVersion has `responseFormat` (HTML, JSON, MarkDown) and `outputSchema` ("the expected JSON schema structure for the generated output"). UNVERIFIED (2026-10-03): the earlier claim that a template binds to a Lightning type for platform-validated JSON was not found in a fetched source. Preview still matters: a schema checks shape, not business correctness.

### Grounding Resources

Merge fields can reference record fields, flows, Apex, Data Cloud DMOs, related lists, data graphs, record snapshots, and retrievers. (Source: Generative AI guide, Ground Prompt Templates with Salesforce Resources.)

**Record merge fields**: added as `Input:RecordName.FieldName`, for example `{!$Input:Account.Name}`. Correction (2026-10-03): earlier examples in this skill used `{!$Record.Subject}`, which is Flow syntax, not Prompt Builder syntax.

**Flow merge fields**: build a **Template-Triggered Prompt Flow**; "Other flow types aren't available to prompt templates." Each **Create Prompt Instructions** element adds instructions, and the flow's output fills the merge field (`{!$Flow:Get_Open_Cases_for_Account}`). Correction (2026-10-03): the element is Create Prompt Instructions, not "Add Prompt Instructions." For flows, all inputs are required and must be present in the template. Flow Builder's Debug option isn't available for this flow type.

**Apex merge fields**: one `@InvocableMethod` that takes `List<Request>` (only the first element has data) and returns `List<Response>` with a single String `Prompt` variable. A `CapabilityType` *can* be specified and ties the class to one template type: `PromptTemplateType://einstein_gpt__fieldCompletion`, `...salesEmail`, `...recordSummary`, `...recordPrioritization`, or `FlexTemplate://template_API_Name`. Correction (2026-10-03): earlier versions said the capability type must match or grounding fails. The guide now says the Flex capability "is no longer needed" and recommends removing `CapabilityType=FlexTemplate://*`; Apex inputs are optional unless annotated as required. Don't specify a CapabilityType for `einstein_gpt__caseEmailDraft`.

**Related list merge fields**: fields come from the parent's page layout for the current user; "Record-level filters aren't applied"; Activities related lists aren't supported; a user without the related list on their layout or without Read access sends no related list data.

**Retrievers (RAG)**: default retrievers come with each Data Cloud search index; custom retrievers are built in Einstein Studio. Search text is limited to 255 characters, globals, and prompt inputs. See `agentforce/rag-patterns-in-salesforce`.

### Versioning and Activation

"After you save a new prompt for the first time, it becomes Version 1." Save keeps working on the current version; Save As > Save as a New Version creates the next one. Correction (2026-10-03): earlier versions said every save creates a version. "Only one version of a template can be active at a time, and if no versions are active the template becomes unavailable to your users." "Activating a template version makes it immutable. Even if deactivated, any version that was ever active remains immutable." Each version can carry a different model configuration, and only the active version's model is used.

"Creating or updating a prompt template isn't tracked in the Setup Audit Trail." Maintain version discipline through naming conventions or an external change log.

### Einstein Trust Layer Integration

Prompts from Prompt Builder templates pass through the Einstein Trust Layer: secure data retrieval under the running user's permissions, system policies (prompt defense), data masking (on by default; field-based masking covers record merge fields and related lists), toxicity scoring, and audit. These are configured in Einstein Trust Layer setup, not in Prompt Builder. Masking is disabled for agents. (Source: Generative AI guide, Einstein Trust Layer chapter.)

---

## Common Patterns

### Mode 1: Create a New Prompt Template

**When to use:** A practitioner needs to build a net-new template from scratch for a defined use case.

**How it works:**

1. Confirm Einstein generative AI is set up, Sales Emails is on, and the author has Prompt Template Manager.
2. From Setup, in Quick Find enter Prompt Builder, and select Prompt Builder. Click New Prompt Template.
3. Select the template type. For field population, select Field Generation and choose the object and field.
4. Write the prompt body. Use the Resource picker to insert merge fields rather than typing API names. Separate context from instructions: on its own line write `Instructions:` and wrap the instructions in triple quotes.
5. Choose grounding with the Decision Guidance table below.
6. Preview with a real record: inspect the resolution (merge fields replaced with data, masked values shown as placeholders) and the response.
7. Activate when the preview meets expectations. Remember the version becomes immutable.
8. For Field Generation, add the template to the field on the Lightning record page. For Sales Email, add it to Einstein Sales Emails. Assign Prompt Template User to end users.

**Why not skip Preview:** Merge fields that look correct in the editor can resolve to nothing on real records, and preview is where masking, related list access, and large-prompt summarization show up.

### Mode 2: Review or Audit an Existing Template Library

**When to use:** Assessing an org's prompt template posture before a release, or identifying why specific templates are not surfacing for users.

**How it works:**

1. Open Prompt Builder. Review all templates, their type, and active version.
2. Check that each template in use has an active version; with none active, the template is unavailable to users.
3. Verify end users have Prompt Template User and access to the objects and fields the template reads; related list grounding also depends on their page layout.
4. Confirm every Flow and Apex resource is deployed, and that nobody has changed their inputs since the template was built.
5. Count resources against the limits table (128,000 characters, 50 merge fields, 5 Flow, 5 Apex, 5 related list).
6. If templates are packaged, confirm subscribers have the right permission sets. UNVERIFIED (2026-10-03): the earlier claim that packages install without the permission and templates then silently fail was not found in a fetched source.

### Mode 3: Troubleshoot Grounding Failures

**When to use:** A template that was previously working returns blank, partial, or generic responses after a metadata change, deployment, or data change.

**How it works:**

1. Preview with a representative record and read the resolution.
2. If a merge field resolves to nothing, check the field path, the record's data, field-level access, and (for related lists) the running user's page layout.
3. If the resolution looks right but the response is weak, refine the instructions rather than the grounding.
4. For Flow-grounded templates: Flow Builder's Debug option isn't available for Template-Triggered Prompt Flows, so test through Prompt Builder preview. UNVERIFIED (2026-10-03): the earlier claim that a failing flow returns an empty string with no error was not found in a fetched source.
5. For Apex-grounded templates: open the Developer Console before previewing; "you can see debug statements in the Developer Console." If the flow or class inputs were changed, the template no longer works and new versions can't be saved; restore the original inputs.
6. Check Trust Layer masking: masked values appear as placeholders in preview, and the LLM sees only the placeholders. See `einstein-trust-layer`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Data lives on the context record or a directly related object | Record merge fields | Simplest, no code required, resolves at runtime |
| Data requires traversing multiple objects, filtering, or aggregation | Template-Triggered Prompt Flow | Declarative; each Create Prompt Instructions element adds text |
| Data requires an external callout, JSON formatting, or programmatic filtering | Apex merge field (`@InvocableMethod`) | The guide names SOQL, external APIs, JSON, and filtering as Apex use cases |
| Use case involves an Agentforce agent action | Flex template (UNVERIFIED that it is the only type accepted) | Flex lets you define your own resources and inputs |
| Use case populates a specific record field from a button | Field Generation | Bound to object and field on the Lightning record page |
| Data includes unstructured articles, emails, or transcripts | Retriever (RAG in Data Cloud) | Search index plus retriever returns relevant chunks |
| Template must deploy between orgs | GenAiPromptTemplate through the Metadata API, tested in a sandbox first for Flex | The guide says Flex template metadata can't be imported or exported (its examples include change sets and Flex-related Apex and flows), while the Metadata API lists `einstein_gpt__flex` as a valid type |

---

## Recommended Workflow

1. Answer the Questions table: surface, type, deployment path, grounding resources, resource counts, and preview records.
2. Build the grounding first: record merge fields, then a Template-Triggered Prompt Flow or an `@InvocableMethod` Apex class with its test class, keeping their input contracts fixed.
3. Create the template in Prompt Builder, write instructions in an `Instructions:` block, and preview with each persona's records.
4. Activate the version, record the change in the external log, and assign Prompt Template User.
5. Retrieve the GenAiPromptTemplate, run `python3 scripts/check_prompt_builder_templates.py --manifest-dir <project>` (limits, deprecated version tags, Apex Request and Response shape, published-status rules), and deploy using `references/metadata-examples.md`.
6. In the target org, recreate any retriever before deploying, confirm the active version, and preview again.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Template type matches the intended deployment surface
- [ ] One version is active, and the change is recorded outside Setup Audit Trail
- [ ] Preview tested against real records for each persona; resolution and response both checked
- [ ] Flow and Apex resources deployed, with unchanged input contracts and Apex test coverage
- [ ] Resource counts within the limits table
- [ ] End users have Prompt Template User and access to the grounded objects and fields
- [ ] Deployment path checked against the Flex and retriever limitations
- [ ] Trust Layer masking behaviour validated in the org where the template runs

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **No active version means no template**: "if no versions are active the template becomes unavailable to your users." Users see nothing to click, which looks like a permission or layout problem.

2. **Subscriber permissions for packaged templates**: UNVERIFIED (2026-10-03): earlier versions said packages install without Prompt Template Manager and templates then can't be invoked. Assign Prompt Template Manager to authors and Prompt Template User to end users in every org.

3. **Changing Flow or Apex inputs breaks the template**: "If you change the inputs for a flow or Apex class that's used as a resource in a prompt template, the prompt template no longer works and you can't save new versions of the prompt template."

4. **Custom objects and fields not immediately available in Prompt Builder**: "To use a new custom object or field immediately, log out and log back in."

5. **CapabilityType is optional, and the Flex capability is retired**: Correction (2026-10-03): earlier versions said a capability type mismatch silently drops Apex data. The guide says the Flex capability "is no longer needed," recommends removing `CapabilityType=FlexTemplate://*`, and notes a CapabilityType ties a class to one template type.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Activated prompt template | A named, versioned, active prompt template ready for binding to a deployment surface |
| GenAiPromptTemplate metadata | Retrieved and checked template file with package.xml entry |
| Grounding strategy decision | Written rationale for merge field vs. Flow vs. Apex vs. retriever choice |
| Template review findings | Checklist-based assessment of active status, permissions, grounding health, limits, and Trust Layer behaviour |
| Troubleshooting report | Root cause and remediation steps for blank, partial, or generic template output |

---

## Related Skills

- `einstein-trust-layer` — Diagnose data masking effects on resolved prompts; required reading before troubleshooting templates in production orgs with sensitive data
- `agentforce-agent-creation` — Covers how to bind a Flex prompt template to an agent action
- `scratch-org-management` — Covers metadata deployment of prompt templates across environments using Salesforce DX
