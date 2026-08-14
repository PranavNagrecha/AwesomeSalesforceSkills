# Gotchas — Document Generation OmniStudio

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Token Case Sensitivity Across Three Layers

**What happens:** A token like `{{AccountName}}` in the template renders as blank even though the Data Mapper appears to have a mapping for it. The generated document shows empty space where the value should be.

**When it occurs:** The OmniDataTransform outputs the key as `accountName` (lowercase 'a') or `ACCOUNTNAME` (all caps), but the template expects `AccountName` (PascalCase). The mismatch is invisible in the Data Mapper UI because the extraction step shows the token name from the template, but the mapping output may use a different casing convention.

**How to avoid:** After building the Data Mapper, preview the output JSON and compare every key name character-by-character against the template tokens. Establish a naming convention (e.g., PascalCase) and enforce it in both template authoring and Data Mapper configuration.

---

## Gotcha 2: Missing Images in Server-Side Output Is a Mapping Gap, Not a Mode Limitation

**What happens:** A template containing image tokens generates successfully in server-side mode but the images are missing from the output. No error is thrown. The natural — and wrong — conclusion is "server-side doesn't support image tokens," which sends the team to re-architect around client-side generation or to pre-render logos as static template content.

**When it occurs:** Server-side image tokens need a **two-bundle Data Mapper setup** that the client-side path does not make obvious:

1. A **Data Mapper Extract** that retrieves the image ID from one of the supported repositories — Files (`ContentDocument`), Notes & Attachments (`Attachment`), or Documents (Contract Document).
2. A **Data Mapper Transform** that maps the extracted data onto the document token and, optionally, defines height/width formulas.

Omit the Extract, point it at an unsupported repository, or fail to map the token in the Transform, and the image silently does not render. That is the actual failure, and it is fixable.

Salesforce documents this explicitly in *Map Image Tokens in the Omnistudio Data Mapper for Server-Side Omnistudio Document Generation*: "Use image tokens in a Microsoft Word or Microsoft PowerPoint document template to insert dynamic images in generated DOCX and PDF files. The image token must start with `IMG_`, such as `{{IMG_header}}`."

**Also check the token spelling.** A second silent-blank cause is invented syntax — `{{%CompanyLogo}}` instead of `{{IMG_CompanyLogo}}`. The engine does not recognise the token, does not error, and leaves a blank. `scripts/check_document_generation_omnistudio.py` flags this mechanically.

**How to avoid:** Before concluding a mode limitation, verify in order: (1) the token uses the `IMG_` prefix inside the braces; (2) a Data Mapper Extract sources the image from a supported repository; (3) the Data Mapper Transform maps the extracted image to that token; (4) the rendered size is inside 350 px × 400 px on A4 portrait, or both height and width are defined to reach 600 px × 800 px. A single template can then serve both modes.

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

---

## Gotcha 7: A Blank Required Permission Makes the DocGen Data Mapper Runnable by Anyone

**What happens:** The generated document is locked down by sharing on its ContentVersion, but any authenticated user can invoke the Data Mapper or Integration Procedure behind it directly and receive the raw JSON — pricing, PII, contract terms — without ever opening a document. The leak is upstream of the file, so auditing file sharing finds nothing.

**When it occurs:** Omnistudio Data Mappers and Integration Procedures have a **Required Permission** property, which "determines who has runtime access" and accepts roles, profiles, permission sets, custom permissions, or any combination. It is blank by default, and Salesforce states the consequence plainly: *"If Required Permission is blank, any user can run the Data Mapper or Integration Procedure unless the DefaultRequiredPermission property is set."* Access is broader than direct invocation — it *"also applies if an application the user is using calls the Data Mapper or Integration Procedure"*, which is how a DocGen OmniScript reaches it.

**The check does not cascade downward.** Salesforce is explicit: *"If a user has access to a parent Integration Procedure, the parent can invoke child Integration Procedures and Data Mappers to which the user doesn't have direct access."* A Required Permission on a child Data Mapper therefore does not protect it from anyone who can run the parent Integration Procedure. Secure the entry point first; child permissions guard only against the child being called directly.

**How to avoid:** Set Required Permission on every Data Mapper and Integration Procedure in the DocGen pipeline — starting with whatever the OmniScript or external caller invokes first — and treat a blank one as an audit finding, not a default. Back it with the three org-level controls in the **Omni Interaction Configuration** custom setting:

- `DefaultRequiredPermission` (String, default none) — the fallback applied to components whose Required Permission is blank. You must implement the `VlocityRequiredPermissionCheck` class manually; it does not work properly from inside the Vlocity managed package.
- `EnforceDMFLSAndDataEncryption` (True/False) — when true, Data Mappers run in the user context instead of the system context, so a Data Mapper cannot read a field the running user cannot see and merge it into the document, and encrypted fields render in plain text only for users with View Encrypted Data. Salesforce began enabling this setting by default in the week of 2 February 2026, so verify its current value rather than assuming either state.
- `CheckCachedMetadataRecordSecurity` (True/False, default **False**) — while False, cached metadata is not secured when Salesforce Sharing Settings or Sharing Sets control access. Set it to True to perform a record-level security check on cached metadata, at a small cost to caching performance.

---

## Gotcha 8: Client-Side DocGen Plus In-Progress Timeout Off Is the 120s Retry Bug

**What happens:** Client-side generation runs in the browser (token map / XML in the Omni JSON the guest can see). `isInProgRqstTmotEnab=false` means the request keeps waiting after the server accepted. The continuation dies near 120s; the client retries; a second PDF/ContentVersion appears.

**When it occurs:** Mixed client+server DocGen; PDF Action after an HTTP IP that already succeeded.

**How to avoid:** Prefer server-side. Enable in-progress request timeout. Do not put notice XML in the Omni JSON the guest sees. Persist an idempotency key before generate. The LWC wrapper that re-enables the OmniScript after PDF (`OmniscriptBaseMixin` + pubsub + `prefill`) must document the prefill contract or the script races.
