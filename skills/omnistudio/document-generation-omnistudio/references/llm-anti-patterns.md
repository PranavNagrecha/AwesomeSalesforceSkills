# LLM Anti-Patterns — Document Generation OmniStudio

Common mistakes AI coding assistants make when generating or advising on OmniStudio Document Generation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inventing Non-Existent Token Syntax

**What the LLM generates:** The AI suggests token syntax like `${AccountName}`, `<<AccountName>>`, `{!AccountName}`, or `[[AccountName]]` in Document Templates, borrowing from other templating engines or Visualforce merge field syntax.

**Why it happens:** LLMs trained on diverse codebases default to whichever templating syntax appears most frequently in training data (e.g., JSP `${}`, Visualforce `{! }`, or Mustache `{{}}`). The OmniStudio-specific double-curly-brace `{{ }}` syntax with specific prefixes for images (`%`) and rich text (`&`) is less represented.

**Correct pattern:**

```text
Simple:     {{FieldName}}
Repeating:  {{#ArrayName}}...{{/ArrayName}}
Conditional: {{#if BooleanField}}...{{/if}}
Image:      {{%ImageField}}
Rich text:  {{&RichTextField}}
```

**Detection hint:** Any token syntax in a template file that does not use `{{ }}` double curly braces is wrong for OmniStudio DocGen.

---

## Anti-Pattern 2: Claiming Server-Side DocGen Supports Image Tokens

**What the LLM generates:** The AI recommends using `{{%CompanyLogo}}` image tokens in a server-side Document Generation flow via Integration Procedure, or fails to mention the client-side-only restriction when advising on image-bearing templates.

**Why it happens:** The LLM treats all DocGen features as universally available across both modes, not distinguishing the client-side-only limitations for image and rich text tokens.

**Correct pattern:**

```text
Image tokens ({{%...}}) -> client-side only (OmniScript)
Rich text tokens ({{&...}}) -> client-side only (OmniScript)
Simple/repeating/conditional tokens -> both modes
```

**Detection hint:** Any recommendation that includes `{{%` or `{{&` tokens alongside "Integration Procedure" or "server-side" is incorrect.

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
