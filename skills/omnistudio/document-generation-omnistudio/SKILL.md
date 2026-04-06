---
name: document-generation-omnistudio
description: "Generating documents (PDF, DOCX, PPTX) from OmniStudio using Document Templates, OmniDataTransform token mapping, and OmniScript or Integration Procedure orchestration. Use when building client-side interactive or server-side batch document generation flows. NOT for Salesforce CPQ document generation. NOT for standard Salesforce mail merge or Lightning email templates. NOT for Contract Lifecycle Management (CLM) native document generation."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
triggers:
  - "how do I generate a PDF from an OmniScript"
  - "document template merge tokens not populating in generated DOCX"
  - "server-side document generation with Integration Procedure"
  - "OmniDataTransform mapping for document template tokens"
  - "client-side vs server-side DocGen in OmniStudio"
  - "dynamic images in OmniStudio document generation"
  - "batch document generation from Integration Procedure"
tags:
  - omnistudio
  - document-generation
  - docgen
  - omniscript
  - integration-procedure
  - omnidatatransform
  - pdf
  - document-template
inputs:
  - "Document output format required: PDF, DOCX, or PPTX"
  - "Generation mode: client-side (interactive, OmniScript-driven) or server-side (batch/headless, Integration Procedure-driven)"
  - "Data source: which Salesforce objects or external data feed the template tokens"
  - "Template complexity: simple merge fields, conditional sections, repeating rows, or dynamic images"
  - "Volume: single document per user action vs batch generation of many documents"
outputs:
  - "Document Template (.docx or .pptx) with correctly placed {{ }} merge tokens"
  - "OmniDataTransform (Data Mapper) configuration mapping Salesforce fields to template tokens"
  - "OmniScript or Integration Procedure orchestrating the end-to-end generation flow"
  - "Document Generation Setting record linking template, mapping, and generation mode"
  - "Generated document stored as ContentVersion (Files) or delivered to an external system"
dependencies:
  - omnistudio/omniscript-design-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# OmniStudio Document Generation

This skill activates when the work requires generating documents (PDF, DOCX, PPTX) using OmniStudio's Document Generation framework. It covers the two generation modes -- client-side (interactive, OmniScript-driven, synchronous in the browser) and server-side (headless, Integration Procedure-driven, asynchronous on Salesforce compute) -- along with template authoring, token mapping via OmniDataTransform, and the orchestration components that tie them together.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the OmniStudio DocGen feature is enabled.** Check Setup > OmniStudio Settings and verify the Document Generation toggle is active. Server-side DocGen requires an additional setting (`Enable Server-Side Document Generation`) to be turned on separately.
- **Identify the generation mode early.** Client-side DocGen runs synchronously in the user's browser via an OmniScript and is suitable for interactive, single-document scenarios. Server-side DocGen runs asynchronously via an Integration Procedure and is suitable for batch, headless, or large-document scenarios. Choosing the wrong mode late in development forces a full re-architecture of the orchestration layer.
- **Understand that image tokens and rich text tokens are client-side only.** Server-side DocGen does not support image merge tokens or rich text tokens. If the template requires dynamic images, you must use client-side generation or pre-render the images into the JSON payload as base64.
- **Dynamic images are capped at approximately 2.5 MB per image.** Exceeding this limit causes the image token to render as blank or throws a generation error without a clear message.

---

## Core Concepts

### Document Templates

A Document Template is a .docx or .pptx file uploaded to Salesforce that contains merge tokens in `{{ }}` double-curly-brace syntax. Tokens are placeholders that map to JSON keys in the input data. Templates support several token types:

- **Simple tokens:** `{{AccountName}}` -- replaced with a single value from the JSON input.
- **Repeating tokens:** `{{#LineItems}}...{{/LineItems}}` -- iterates over an array in the JSON to produce repeating rows or sections.
- **Conditional tokens:** `{{#if ShowDiscount}}...{{/if}}` -- renders the enclosed content only when the condition evaluates to true.
- **Image tokens:** `{{%ImageField}}` -- inserts a dynamic image (client-side only). The JSON value must be a base64-encoded image string.
- **Rich text tokens:** `{{&RichTextField}}` -- inserts HTML-formatted rich text (client-side only).

Templates are stored as ContentVersion records and referenced by the Document Generation Setting. The token names are case-sensitive and must match the JSON keys produced by the OmniDataTransform exactly.

### OmniDataTransform (Data Mapper) for Token Mapping

The OmniDataTransform (historically called DataRaptor) is responsible for extracting data from Salesforce and shaping it into the JSON structure that the template expects. A Mapping Data Mapper reads the uploaded template, extracts the token names, and lets you map each token to a Salesforce field or formula.

Key points:
- The Data Mapper can extract tokens automatically from a .docx/.pptx template.
- Each token maps to either a direct field reference (e.g., `Account.Name`) or a formula/transform expression.
- Repeating tokens require the Data Mapper to produce a JSON array at the corresponding key.
- The output JSON from the Data Mapper is the input JSON for the template engine. If the JSON structure does not match the template token paths, tokens render as blank without error.

### Client-Side vs Server-Side Generation

**Client-side** generation is orchestrated by an OmniScript. The OmniScript collects user input, calls the Data Mapper, passes the JSON to the template engine running in the browser, and renders the output. The user sees the document immediately. PDF conversion happens via a Visualforce page (`fndMultiPDFConvertLwc`) or a custom conversion step.

**Server-side** generation is orchestrated by an Integration Procedure. The Integration Procedure calls the Data Mapper, passes the JSON to the server-side template engine, converts the output to the target format, and stores the result as a ContentVersion. No user interaction is required. This mode supports larger documents and batch processing but does not support image or rich text tokens.

### Document Generation Setting

The Document Generation Setting is the metadata record that ties the template, the Data Mapper, and the generation mode together. It specifies:
- Which Document Template to use
- Which OmniDataTransform provides the token mapping
- Whether the generation is client-side or server-side
- The output format (DOCX, PPTX, or PDF)
- The OmniScript or Integration Procedure that orchestrates the flow

---

## Common Patterns

### Pattern 1: Interactive Single-Document Generation (Client-Side)

**When to use:** A user needs to generate a single document (e.g., a quote, proposal, or contract) during an interactive session, potentially reviewing or customizing inputs before generation.

**How it works:**

1. Create a .docx template with `{{ }}` tokens for all dynamic fields.
2. Create an OmniDataTransform (Mapping type) that extracts tokens from the template and maps them to Salesforce fields.
3. Create a Document Generation Setting linking the template and Data Mapper, set to client-side.
4. Build an OmniScript that:
   - Collects any user input on initial steps.
   - Calls the Data Mapper via a DataRaptor Extract action to produce the JSON payload.
   - Includes a DocGen Document step that references the Document Generation Setting.
   - Optionally includes PDF conversion via the `fndMultiPDFConvertLwc` component.
5. The generated document is stored as a ContentVersion attached to the context record.

**Why not server-side:** Server-side generation is asynchronous -- the user would not see the document immediately and cannot preview or customize inputs inline.

### Pattern 2: Batch/Headless Document Generation (Server-Side)

**When to use:** Documents must be generated without user interaction -- triggered by a platform event, scheduled job, or Flow-initiated callout. Common for batch invoice generation, renewal notices, or compliance documents.

**How it works:**

1. Create a .docx template with `{{ }}` tokens (no image or rich text tokens).
2. Create an OmniDataTransform mapping tokens to Salesforce fields.
3. Create a Document Generation Setting linking the template and Data Mapper, set to server-side.
4. Build an Integration Procedure that:
   - Accepts context parameters (e.g., record IDs) as input.
   - Calls the Data Mapper to produce the JSON payload.
   - Invokes the server-side DocGen action referencing the Document Generation Setting.
   - Stores the output ContentVersion and optionally sends it via email or posts to an external system.
5. Trigger the Integration Procedure from a Flow, Apex, or scheduled process.

**Why not client-side:** Client-side requires an active browser session and processes one document at a time synchronously. It cannot handle batch volumes or headless triggers.

### Pattern 3: Multi-Template Document Package

**When to use:** A single business process requires generating multiple documents from different templates (e.g., a cover letter + contract + terms and conditions) and combining or delivering them together.

**How it works:**

1. Create separate Document Templates for each document type.
2. Create a shared or per-template OmniDataTransform.
3. In the OmniScript (client-side) or Integration Procedure (server-side), chain multiple DocGen steps, each referencing a different Document Generation Setting.
4. Combine the output ContentVersions into a single delivery (e.g., attach all to the same record, or merge PDFs using a custom Apex utility).

**Why not a single template:** Splitting into multiple templates improves maintainability, allows conditional inclusion of documents, and avoids template size limits on complex documents.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| User reviews/customizes data before generating a single document | Client-side via OmniScript | Synchronous, interactive, immediate preview |
| Batch generation of hundreds of documents on a schedule | Server-side via Integration Procedure | Asynchronous, no browser session required, handles volume |
| Template needs dynamic images or rich text | Client-side only | Image and rich text tokens are not supported server-side |
| Document generation triggered by platform event or Apex | Server-side via Integration Procedure | No user session available for client-side |
| Output must be PDF | Either mode, but add a PDF conversion step | Neither mode produces PDF natively from .docx -- conversion step required |
| Template exceeds browser memory for large documents | Server-side | Server-side uses Salesforce compute resources, not browser memory |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the generation mode.** Determine whether the use case is interactive (client-side) or batch/headless (server-side). Check whether the template requires image or rich text tokens, which force client-side.
2. **Author the Document Template.** Create the .docx or .pptx file with `{{ }}` merge tokens. Use `{{#Array}}...{{/Array}}` for repeating sections and `{{#if Condition}}...{{/if}}` for conditional content. Upload the template as a ContentVersion.
3. **Build the OmniDataTransform.** Create a Mapping Data Mapper, extract tokens from the uploaded template, and map each token to the correct Salesforce field or formula. Verify the output JSON structure matches the template token paths exactly.
4. **Create the Document Generation Setting.** Link the template, Data Mapper, and generation mode. Set the output format.
5. **Build the orchestration component.** For client-side, build an OmniScript with a DocGen Document step. For server-side, build an Integration Procedure with a DocGen action. Wire the Document Generation Setting into the orchestration.
6. **Test with representative data.** Generate a test document using real record data. Verify all tokens populate, repeating sections iterate correctly, and conditional sections render as expected. Check that the output file opens cleanly in the target application.
7. **Validate edge cases.** Test with null/blank token values, empty arrays for repeating sections, and maximum-size images (if client-side). Confirm graceful handling or explicit error messages.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Document Template uploaded as ContentVersion with correct .docx or .pptx format
- [ ] All `{{ }}` tokens in the template have corresponding mappings in the OmniDataTransform
- [ ] OmniDataTransform output JSON structure matches template token paths (case-sensitive)
- [ ] Document Generation Setting links the correct template, Data Mapper, and generation mode
- [ ] Image tokens (if any) are used only in client-side mode and images are under 2.5 MB
- [ ] Rich text tokens (if any) are used only in client-side mode
- [ ] Repeating sections produce correct output with 0, 1, and many items
- [ ] Conditional sections render correctly when condition is true and when false
- [ ] PDF conversion step is included if PDF output is required
- [ ] Generated document is stored as ContentVersion on the correct parent record
- [ ] Server-side DocGen setting is enabled in OmniStudio Settings (if using server-side)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Token names are case-sensitive across template, Data Mapper, and JSON.** If the template uses `{{AccountName}}` but the Data Mapper outputs `accountName` (lowercase 'a'), the token renders blank. There is no warning or error -- just an empty space in the output document. Always verify exact case matching across all three layers.
2. **Image and rich text tokens silently fail in server-side mode.** If a template containing `{{%ImageField}}` or `{{&RichTextField}}` is used with server-side generation, those tokens render as blank or as the raw token string. The generation does not throw an error. This is a design limitation, not a bug.
3. **Empty arrays in repeating sections can produce ghost rows.** If the OmniDataTransform returns an empty array `[]` for a repeating section, some template engines leave a blank row in the output rather than omitting the section entirely. Wrap repeating sections in a conditional `{{#if}}` check on array length to avoid phantom rows.
4. **PDF conversion is a separate step, not native to DocGen.** Neither client-side nor server-side DocGen produces PDF directly from a .docx template. Client-side uses the `fndMultiPDFConvertLwc` Visualforce component for conversion. Server-side requires a custom Apex conversion utility or external service callout. Forgetting the conversion step results in .docx output when the user expected PDF.
5. **Dynamic image size cap (~2.5 MB) is not documented in error messages.** When a base64-encoded image exceeds the limit, the generation may fail silently or produce a corrupt document. Pre-validate image sizes in the OmniScript before passing them to the DocGen step.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Document Template (.docx/.pptx) | The authored template file with `{{ }}` merge tokens, uploaded as a ContentVersion |
| OmniDataTransform | Data Mapper configuration mapping Salesforce fields to template tokens |
| Document Generation Setting | Metadata record linking template, Data Mapper, and generation mode |
| OmniScript or Integration Procedure | Orchestration component driving the end-to-end generation flow |
| ContentVersion (generated document) | The output document stored in Salesforce Files |

---

## Related Skills

- omniscript-design-patterns -- use when designing the OmniScript that orchestrates client-side DocGen
- omnistudio-custom-lwc-elements -- use when embedding a custom LWC for document preview or user input within the DocGen OmniScript
- omnistudio-lwc-integration -- use when the generated document flow must be embedded inside a custom Lightning page
