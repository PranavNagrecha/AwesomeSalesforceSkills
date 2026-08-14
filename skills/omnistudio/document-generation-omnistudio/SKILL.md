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
runtime_orphan: true
---

# OmniStudio Document Generation

This skill activates when the work requires generating documents (PDF, DOCX, PPTX) using OmniStudio's Document Generation framework. It covers the two generation modes -- client-side (interactive, OmniScript-driven, synchronous in the browser) and server-side (headless, Integration Procedure-driven, asynchronous on Salesforce compute) -- along with template authoring, token mapping via OmniDataTransform, and the orchestration components that tie them together.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the OmniStudio DocGen feature is enabled.** Check Setup > OmniStudio Settings and verify the Document Generation toggle is active. Server-side DocGen requires an additional setting (`Enable Server-Side Document Generation`) to be turned on separately.
- **Identify the generation mode early.** Client-side DocGen runs synchronously in the user's browser via an OmniScript and is suitable for interactive, single-document scenarios. Server-side DocGen runs asynchronously via an Integration Procedure and is suitable for batch, headless, or large-document scenarios. Choosing the wrong mode late in development forces a full re-architecture of the orchestration layer.
- **Do not assume image or rich text tokens force client-side mode.** Salesforce publishes a dedicated topic, *Map Image Tokens in the Omnistudio Data Mapper for Server-Side Omnistudio Document Generation*, and the token reference lists image, hyperlink and rich text tokens without restricting them by generation mode. Image tokens work server-side; they are wired through a Data Mapper Extract (from Files/`ContentDocument`, Notes & Attachments/`Attachment`, or Documents/Contract Document) plus a Data Mapper Transform that maps the retrieved image to the token and optionally supplies height/width formulas. Choose the mode on interactivity and volume, not on a token-support myth.
- **Image constraints are dimensional, not byte-based.** A dynamic image renders "up to a maximum of 350 px (width) × 400 px (height) on an A4 portrait page" by default, and "up to a maximum of 600 px × 800 px on an A4 portrait page" when both height and width are defined in the Data Mapper Transform. To preserve the original aspect ratio, define either the height or the width, **not both**. There is no documented megabyte ceiling on a DocGen image.

---

## Core Concepts

### Document Templates

A Document Template is a .docx or .pptx file uploaded to Salesforce that contains merge tokens in `{{ }}` double-curly-brace syntax. Tokens are placeholders that map to JSON keys in the input data. Templates support several token types:

Every token type below uses a documented **prefix inside the braces** — `IMG_`, `HYP_`, `RTB_`, `IF_`, `DT_`. There is no `%`, `&`, or other sigil syntax in OmniStudio DocGen; if you see one, it is invented (see `references/llm-anti-patterns.md`).

- **Variable tokens:** `{{AccountName}}` -- replaced with a single value from the JSON input.
- **Repeating content tokens:** `{{#LineItems}}...{{/LineItems}}` -- iterates over an array in the JSON to produce repeating rows or sections. The inverted form `{{^LineItems}}...{{/LineItems}}` renders fallback content when the array is empty.
- **Condition evaluation tokens:** `{{#IF_ShowDiscount}}...{{/IF_ShowDiscount}}` -- renders the enclosed content only when the Boolean evaluates true. `{{^IF_ShowDiscount}}...{{/IF_ShowDiscount}}` is the negated form. Note the `IF_` prefix on the token name; this is **not** Handlebars `{{#if cond}}`.
- **Image tokens:** `{{IMG_header}}` -- inserts a dynamic image into generated .docx and .pdf files. Supported in both client-side and server-side generation; server-side is mapped through a Data Mapper Extract + Transform pair.
- **Hyperlink tokens:** `{{HYP_termsLink}}` -- inserts a dynamic URL.
- **Rich text tokens:** `{{RTB_Header}}` -- inserts formatted text (fonts, colours, ordered/unordered lists, hyperlinks) into .docx and .pdf output. Place a rich text token on its own new line in the template; it works in paragraphs, tables, text boxes, headers and footers.
- **Data true-up tokens:** `{{DT_FieldName}}` -- syncs field values between the document and the Salesforce record.

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

**Server-side** generation is orchestrated by an Integration Procedure. The Integration Procedure calls the Data Mapper, passes the JSON to the server-side template engine, converts the output to the target format, and stores the result as a ContentVersion. No user interaction is required. This mode supports larger documents and batch processing. It does **not** cost you the rich token types — image tokens are explicitly documented for server-side generation via the Data Mapper, and the token reference does not restrict hyperlink or rich text tokens by mode. The real tradeoff is interactivity and preview, not token support.

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

1. Create a .docx template with `{{ }}` tokens. Image (`IMG_`), hyperlink (`HYP_`) and rich text (`RTB_`) tokens are all usable here — image tokens additionally need a Data Mapper Extract that retrieves the image from Files (`ContentDocument`), Notes & Attachments (`Attachment`), or Documents (Contract Document).
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
| Template needs dynamic images or rich text | **Either mode** — decide on interactivity, not token support | Image tokens are documented for server-side generation via Data Mapper Extract + Transform; the token reference does not restrict rich text or hyperlink tokens by mode |
| Image must render larger than 350 px × 400 px on A4 portrait | Define **both** height and width in the Data Mapper Transform | Raises the ceiling to 600 px × 800 px. Defining both forfeits aspect-ratio preservation — set only one to keep the ratio |
| Document generation triggered by platform event or Apex | Server-side via Integration Procedure | No user session available for client-side |
| Output must be PDF | Either mode, but add a PDF conversion step | Neither mode produces PDF natively from .docx -- conversion step required |
| Template exceeds browser memory for large documents | Server-side | Server-side uses Salesforce compute resources, not browser memory |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the generation mode.** Determine whether the use case is interactive (client-side) or batch/headless (server-side). Decide on interactivity, volume and trigger — **not** on token support, which does not differ the way it is often claimed to.
2. **Author the Document Template.** Create the .docx or .pptx file with `{{ }}` merge tokens. Use `{{#Array}}...{{/Array}}` for repeating sections and `{{#IF_Condition}}...{{/IF_Condition}}` for conditional content (note the `IF_` prefix — this is not Handlebars). Use the `IMG_`, `HYP_`, `RTB_` and `DT_` prefixes for image, hyperlink, rich text and data-true-up tokens respectively. Upload the template as a ContentVersion.
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
- [ ] Token prefixes are the documented ones (`IMG_`, `HYP_`, `RTB_`, `IF_`, `DT_`) — no `{{%`, `{{&`, or Handlebars `{{#if `
- [ ] Image tokens (if any) have a Data Mapper Extract sourcing the image (ContentDocument / Attachment / Contract Document) and a Data Mapper Transform mapping it to the token
- [ ] Image rendered size is within 350 px × 400 px on A4 portrait, or both height and width are defined to reach the 600 px × 800 px ceiling
- [ ] Where original aspect ratio matters, only one of height/width is defined
- [ ] Repeating sections produce correct output with 0, 1, and many items
- [ ] Conditional sections render correctly when condition is true and when false
- [ ] PDF conversion step is included if PDF output is required
- [ ] Generated document is stored as ContentVersion on the correct parent record
- [ ] Server-side DocGen setting is enabled in OmniStudio Settings (if using server-side)
- [ ] Every Data Mapper and Integration Procedure in the pipeline has a non-blank Required Permission — blank means any user can run it, and the `DefaultRequiredPermission` fallback is inert unless `VlocityRequiredPermissionCheck` is implemented manually

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Token names are case-sensitive across template, Data Mapper, and JSON.** If the template uses `{{AccountName}}` but the Data Mapper outputs `accountName` (lowercase 'a'), the token renders blank. There is no warning or error -- just an empty space in the output document. Always verify exact case matching across all three layers.
2. **Invented token syntax renders as literal text, and nothing warns you.** The documented prefixes are `IMG_`, `HYP_`, `RTB_`, `IF_`, `DT_` — all *inside* the braces, e.g. `{{IMG_header}}`. A template written with sigil syntax (`{{%ImageField}}`, `{{&RichTextField}}`) or with Handlebars conditionals (`{{#if Cond}}`) does not error; the engine simply does not recognise the token and the raw string or a blank appears in the output. Verify prefixes against *Tokens in Microsoft Word or Microsoft PowerPoint Documents* before blaming the generation mode.
3. **Empty arrays in repeating sections can produce ghost rows.** If the OmniDataTransform returns an empty array `[]` for a repeating section, some template engines leave a blank row in the output rather than omitting the section entirely. Wrap repeating sections in a conditional `{{#if}}` check on array length to avoid phantom rows.
4. **PDF conversion is a separate step, not native to DocGen.** Neither client-side nor server-side DocGen produces PDF directly from a .docx template. Client-side uses the `fndMultiPDFConvertLwc` Visualforce component for conversion. Server-side requires a custom Apex conversion utility or external service callout. Forgetting the conversion step results in .docx output when the user expected PDF.
5. **Image constraints are pixel dimensions, not megabytes — and defining both height and width silently changes the aspect ratio.** The documented ceilings are 350 px × 400 px on an A4 portrait page by default, rising to 600 px × 800 px when *both* height and width are defined in the Data Mapper Transform. The trap is that defining both is exactly what you do to reach the larger ceiling, and doing so forfeits aspect-ratio preservation: Salesforce's guidance is "to maintain the original aspect ratio of an image, define either the height or the width, but not both." A logo that comes out stretched has usually been given both dimensions by someone chasing the higher size cap. There is no documented byte-size cap on a DocGen image.

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
