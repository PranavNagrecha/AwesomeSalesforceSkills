# Gotchas — Document Generation OmniStudio

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Token Case Sensitivity Across Three Layers

**What happens:** A token like `{{AccountName}}` in the template renders as blank even though the Data Mapper appears to have a mapping for it. The generated document shows empty space where the value should be.

**When it occurs:** The OmniDataTransform outputs the key as `accountName` (lowercase 'a') or `ACCOUNTNAME` (all caps), but the template expects `AccountName` (PascalCase). The mismatch is invisible in the Data Mapper UI because the extraction step shows the token name from the template, but the mapping output may use a different casing convention.

**How to avoid:** After building the Data Mapper, preview the output JSON and compare every key name character-by-character against the template tokens. Establish a naming convention (e.g., PascalCase) and enforce it in both template authoring and Data Mapper configuration.

---

## Gotcha 2: Image Tokens Silently Ignored in Server-Side Mode

**What happens:** A template containing `{{%CompanyLogo}}` image tokens generates successfully in server-side mode but the images are missing from the output. No error is thrown.

**When it occurs:** The template was originally designed and tested with client-side generation (where image tokens work), then reused for a server-side Integration Procedure flow without modification.

**How to avoid:** Maintain separate templates for client-side and server-side generation if images are needed. For server-side, pre-render images into the document template as static content, or use a post-processing step to insert images via an external service.

---

## Gotcha 3: PDF Conversion Is Not Automatic

**What happens:** The business requirement says "generate a PDF" but the DocGen output is a .docx file. Stakeholders report that the system is "broken" because they receive Word documents instead of PDFs.

**When it occurs:** The practitioner configures the Document Generation Setting and OmniScript but omits the PDF conversion step, assuming DocGen handles it natively.

**How to avoid:** For client-side, add the `fndMultiPDFConvertLwc` Visualforce component or an equivalent LWC-based conversion step after the DocGen Document step. For server-side, implement an Apex-based PDF conversion utility or callout to an external conversion service. Always include the conversion step in the design from the start.

---

## Gotcha 4: Empty Repeating Sections Leave Phantom Rows

**What happens:** A table in the generated document contains a blank row (with borders and formatting) even though there are no items in the data for that repeating section.

**When it occurs:** The OmniDataTransform returns an empty array `[]` for the repeating section key. The template engine processes the `{{#LineItems}}...{{/LineItems}}` block and produces an empty iteration that still renders the table row structure.

**How to avoid:** Wrap repeating sections in a conditional check: `{{#if LineItems}}{{#LineItems}}...{{/LineItems}}{{/if}}`. This ensures the entire section is omitted when the array is empty. Alternatively, ensure the Data Mapper omits the key entirely (rather than returning an empty array) when there are no items.

---

## Gotcha 5: Document Generation Setting Name Collisions Across Sandboxes

**What happens:** A Document Generation Setting that works in a sandbox fails or references the wrong template after deployment to another environment. The generation produces a document from an old or incorrect template.

**When it occurs:** Document Generation Settings reference ContentVersion records by ID. When deploying across environments, the ContentVersion IDs differ. If the deployment does not include the template file or the reference is not updated, the setting points to a stale or nonexistent template.

**How to avoid:** Include Document Templates (ContentVersion records) in the deployment package. Use a post-deployment script or manual step to verify that the Document Generation Setting references the correct ContentVersion in the target environment. Consider using a naming convention for templates that makes it easy to identify and re-link them after deployment.

---

## Gotcha 6: Server-Side DocGen Requires Separate Enablement

**What happens:** An Integration Procedure configured for server-side DocGen throws an error or the DocGen action is not available in the IP designer.

**When it occurs:** The org has OmniStudio Document Generation enabled but the server-side-specific setting has not been toggled on. The two settings are independent.

**How to avoid:** In Setup > OmniStudio Settings, verify that both the general Document Generation setting and the "Enable Server-Side Document Generation" setting are active. Check this in every target environment, as sandbox refreshes may not carry the setting forward.
