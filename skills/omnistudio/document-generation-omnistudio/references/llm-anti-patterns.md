# LLM Anti-Patterns — Document Generation OmniStudio

Common mistakes AI coding assistants make when generating or advising on OmniStudio Document Generation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inventing Non-Existent Token Syntax

**What the LLM generates:** The AI suggests token syntax like `${AccountName}`, `<<AccountName>>`, `{!AccountName}`, or `[[AccountName]]` in Document Templates, borrowing from other templating engines or Visualforce merge field syntax.

**Why it happens:** LLMs trained on diverse codebases default to whichever templating syntax appears most frequently in training data (e.g., JSP `${}`, Visualforce `{! }`, or Mustache/Handlebars `{{}}`). Getting to `{{ }}` is only half the job, and the second half is where the failures cluster: because the outer syntax *looks* like Mustache, the model completes the pattern with **Mustache/Handlebars sigils** — `{{%img}}`, `{{&raw}}`, `{{#if cond}}` — all of which are real syntax in *those* engines and none of which OmniStudio recognises. OmniStudio instead uses **named prefixes inside the braces**.

**Correct pattern:**

```text
Documented in "Tokens in Microsoft Word or Microsoft PowerPoint Documents":

  Variable            {{FieldName}}
  Repeating content   {{#ArrayName}}...{{/ArrayName}}
                      {{^ArrayName}}...{{/ArrayName}}   (inverted / empty case)
  Condition           {{#IF_BooleanField}}...{{/IF_BooleanField}}
                      {{^IF_BooleanField}}...{{/IF_BooleanField}}
  Image               {{IMG_imagetokenname}}
  Hyperlink           {{HYP_hyperlinktokenname}}
  Rich text           {{RTB_richtexttokenname}}
  Data true-up        {{DT_FieldName}}
  Bypass              bypass_tokens  (comma-separated list)

The prefix is part of the TOKEN NAME, inside the braces.
There is no %, &, or ! sigil anywhere in OmniStudio DocGen.
{{#if cond}} is Handlebars, NOT OmniStudio — it must be {{#IF_cond}}.
```

**Detection hint:** Reaching `{{ }}` is not sufficient — grep the template XML for `\{\{[%&!]` and for `\{\{#\s*if\s` (lowercase `if` followed by whitespace). All are Mustache/Handlebars carry-over and all are wrong. Then confirm every non-variable token name starts with one of `IMG_`, `HYP_`, `RTB_`, `DT_`, or `IF_`. `scripts/check_document_generation_omnistudio.py` implements exactly these checks. The failure is silent — an unrecognised token raises no error and leaves the raw string or a blank in the generated document — so a mechanical check is the only reliable guard.

---

## Anti-Pattern 2: Claiming Server-Side DocGen Does Not Support Image or Rich Text Tokens

**What the LLM generates:** "Image tokens and rich text tokens are client-side only. Server-side DocGen does not support them — if the template needs dynamic images you must switch to client-side generation, or pre-render the images into the payload as base64." Frequently paired with an invented byte cap ("dynamic images are capped at approximately 2.5 MB per image").

**Why it happens:** Two mechanisms. First, **plausible-asymmetry filling**: headless/server-side renderers genuinely are more limited than browser renderers in many products, so "server-side can't do the rich stuff" is a strong prior that the model applies without evidence. Second, **wrong-dimension limits**: asked for an image constraint, the model produces a *file size* in MB, because that is how image limits are usually expressed elsewhere on the platform (attachment ceilings, ContentVersion sizes). Salesforce's actual DocGen image constraints are **pixel dimensions**. The number and the unit are both invented, but the invention is disciplined enough — "approximately", a plausible magnitude — to survive review.

This one is expensive when wrong: it forces an architecture decision (abandon batch/headless generation, or bolt on an external image service) on a false premise.

**Correct pattern:**

```text
Salesforce publishes a dedicated topic:
  "Map Image Tokens in the Omnistudio Data Mapper for Server-Side
   Omnistudio Document Generation"

  "Use image tokens in a Microsoft Word or Microsoft PowerPoint document
   template to insert dynamic images in generated DOCX and PDF files.
   The image token must start with IMG_, such as {{IMG_header}}."

Server-side image wiring = TWO Data Mapper bundles:
  1. Data Mapper Extract   -> retrieves the image ID from
                              Files (ContentDocument),
                              Notes & Attachments (Attachment), or
                              Documents (Contract Document)
  2. Data Mapper Transform -> maps extracted data to the document token,
                              optionally defines height/width formulas

Image constraints are DIMENSIONAL, not byte-based:
  default              : max 350 px (w) x 400 px (h) on an A4 portrait page
  both dims defined    : max 600 px x 800 px on an A4 portrait page
  aspect ratio         : "define either the height or the width, but not both"
  megabyte cap         : none documented

Rich text {{RTB_...}} and hyperlink {{HYP_...}} tokens are listed in the
token reference without a mode restriction. Do not assert a client-side-only
limitation for them either.
```

**Detection hint:** Two greps on generated guidance. (1) `client-side only` within the same paragraph as `image token` or `rich text token` — the claim is unsupported; require the URL of a page that states the restriction before accepting it. (2) Any image constraint expressed in `MB`/`KB` — DocGen image limits are documented in pixels, so a byte figure is the signature of this fabrication. More generally: when a stated limit's *unit* differs from the unit the official page uses, treat the whole claim as reconstructed rather than recalled.

---

## Anti-Pattern 3: Assuming DocGen Produces PDF Natively

**What the LLM generates:** The AI states that setting the output format to "PDF" in the Document Generation Setting will directly produce a PDF file, omitting the conversion step.

**Why it happens:** LLMs generalize from other document generation platforms where PDF is a direct output format. In OmniStudio, the template engine produces .docx or .pptx output, and PDF conversion is a separate downstream step.

**Correct pattern:**

```text
Client-side PDF: DocGen step -> fndMultiPDFConvertLwc Visualforce page -> PDF ContentVersion
Server-side PDF: DocGen step -> Apex conversion utility or external service callout -> PDF ContentVersion
```

**Detection hint:** Any advice that describes PDF generation without mentioning a conversion step (fndMultiPDFConvertLwc, Apex utility, or external service) is incomplete.

---

## Anti-Pattern 4: Using Visualforce Merge Field Syntax in Data Mapper Formulas

**What the LLM generates:** The AI writes Data Mapper formula expressions using Visualforce syntax like `{!Account.Name}` or SOQL-style dot notation like `Account__r.Name` inside OmniDataTransform mapping fields.

**Why it happens:** LLMs conflate Salesforce formula syntax across different contexts. OmniDataTransform uses its own expression syntax for formulas and field references, which differs from Visualforce merge fields, Process Builder formulas, and Flow formulas.

**Correct pattern:**

```text
OmniDataTransform field reference: Account.Name (no {! } wrapper, no __r suffix)
OmniDataTransform formula: IF(Account.BillingCountry = "US", true, false)
```

**Detection hint:** Any `{!...}` syntax or `__r` relationship suffix in an OmniDataTransform mapping expression is incorrect.

---

## Anti-Pattern 5: Confusing OmniDataTransform Types for Document Generation

**What the LLM generates:** The AI recommends using a "Turbo Extract" or "Extract" type OmniDataTransform for token mapping, or creates a generic DataRaptor Extract without specifying the Mapping type needed for template token extraction.

**Why it happens:** OmniDataTransform has multiple types (Extract, Load, Transform, Mapping/Turbo Extract), and LLMs do not always distinguish which type serves the document generation use case. The Mapping type is specifically designed to extract tokens from a template and map them to Salesforce fields.

**Correct pattern:**

```text
For DocGen token mapping: OmniDataTransform of type "Mapping" (Data Mapper)
  - Extracts tokens automatically from the uploaded .docx/.pptx template
  - Provides visual mapping of tokens to Salesforce fields
  - Produces the JSON payload consumed by the template engine

For data extraction (feeding data into the DocGen flow): OmniDataTransform of type "Extract"
  - Pulls data from Salesforce objects
  - Output feeds into the Mapping Data Mapper or directly into the DocGen JSON
```

**Detection hint:** Any recommendation to use a "Turbo Extract" or generic "Extract" DataRaptor as the token mapping component for DocGen is incorrect. The token mapping must use a "Mapping" type Data Mapper.

---

## Anti-Pattern 6: Hallucinating a Built-In Document Preview Component

**What the LLM generates:** The AI suggests using a built-in OmniScript step like "DocGen Preview" or "Document Preview" to show the user a rendered preview of the document before finalizing, citing a component that does not exist in the standard OmniStudio component library.

**Why it happens:** Document preview is a common UX pattern in other platforms, and LLMs extrapolate that OmniStudio must have a native preview step. OmniStudio does not provide a built-in document preview component in the OmniScript designer.

**Correct pattern:**

```text
To preview a document before finalizing:
  1. Generate the document via the DocGen step
  2. Use a custom LWC element to render the generated file (e.g., embed a PDF viewer iframe or download link)
  3. Add a confirmation step before the final save

There is no native "preview" step in the OmniScript DocGen component library.
```

**Detection hint:** Any reference to a "DocGen Preview" step, "Document Preview" OmniScript element, or similar built-in preview component is a hallucination.
