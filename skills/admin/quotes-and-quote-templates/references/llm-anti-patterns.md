# LLM Anti-Patterns — Quotes and Quote Templates

Common mistakes AI coding assistants make when generating or advising on Salesforce Quotes and Quote Templates. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Multiple Quotes Can Be Synced Simultaneously

**What the LLM generates:** Advice such as "sync all your quote variants to the opportunity so products stay current" or code that iterates over quotes and calls sync on each one expecting all to remain synced simultaneously.

**Why it happens:** LLMs generalize from CRM concepts where multiple child records can all be "linked" to a parent. The platform constraint that only one quote can hold `IsSyncing = true` per opportunity is not intuitive from the data model alone.

**Correct pattern:**

```text
Only ONE quote per opportunity can be synced at a time.
Opportunity.SyncedQuoteId holds the ID of the single synced quote.
Starting sync on a second quote automatically stops sync on the first.
Draft quotes that are not synced do not update opportunity products.
```

**Detection hint:** Any instruction or code that iterates over multiple quotes and calls "Start Sync" or sets `IsSyncing = true` without first stopping sync on existing quotes.

---

---

## Anti-Pattern 2: Recommending Standard Quote Templates for CPQ Quote Lines

**What the LLM generates:** Instructions to create a standard Quote Template in Setup and configure it to display CPQ (SBQQ) quote lines in the PDF body table.

**Why it happens:** LLMs conflate "Salesforce Quotes" and "Salesforce CPQ Quotes" because both are marketed as quoting tools on the Salesforce platform. The distinction between `QuoteLineItem` (standard) and `SBQQ__QuoteLine__c` (CPQ) is often missing from training data context.

**Correct pattern:**

```text
Standard quote template body: renders QuoteLineItem records only.
CPQ quote lines: stored in SBQQ__QuoteLine__c — NOT rendered by standard templates.
For CPQ quotes: use CPQ SBQQ Document Templates
  (Setup > Installed Packages > Salesforce CPQ > Document Templates).
Do NOT advise using standard quote templates for CPQ quotes.
```

**Detection hint:** Any recommendation to use Setup > Quote Templates for a quote in an org with CPQ installed, without checking which quote line object is in use.

---

---

## Anti-Pattern 3: Claiming Custom Opportunity Fields Auto-Map to Quote Fields

**What the LLM generates:** Advice like "your custom Opportunity fields will automatically appear on the related Quote when the quote is created" or "Salesforce maps opportunity custom fields to quote fields the same way it maps lead fields during conversion."

**Why it happens:** Lead Conversion has a well-known field mapping mechanism. LLMs incorrectly generalize this behavior to the Opportunity-to-Quote relationship, which has no equivalent declarative mapping.

**Correct pattern:**

```text
There is NO platform-native field mapping from Opportunity/OpportunityLineItem
to Quote/QuoteLineItem.
Custom fields must be:
  1. Manually created on the Quote/QuoteLineItem object.
  2. Populated via Record-Triggered Flow on Quote creation/update, OR via custom Apex.
Lead Conversion field mapping (Setup > Lead Conversion Mapping) does NOT apply to Quotes.
```

**Detection hint:** Any claim that opportunity custom fields "appear on" or "are copied to" the quote without a Flow or Apex implementation step.

---

---

## Anti-Pattern 4: Building a Discount Approval That Writes Back to `Quote.Discount`

**What the LLM generates:** An approval design whose rejection action is "field update: set `Quote.Discount` = 15", or a Flow that does `Update Records → Quote → Discount`. Often paired with test instructions like "log in as an admin and submit a quote with a 20% discount to verify the approval fires."

**Why it happens:** `Quote.Discount` reads like a header input because it appears on the layout as a percentage next to an editable-looking total, and because the entry criterion `Quote.Discount > 15` genuinely works — the field is filterable. Nothing in the field name signals that it is a roll-up.

**Correct pattern:**

```text
Quote.Discount        percent   Filter, Nillable, Sort           <- NO Create, NO Update
                      "The difference between the QuoteLineItem record's subtotal and
                       its discounted total, divided by the QuoteLineItem's subtotal."
                      (object_reference.txt L239578-239592)

QuoteLineItem.Discount  percent  Create, Filter, Nillable, Sort, Update
                        "Editable number from 0 to 100."
                        (object_reference.txt L240758-240767)

READ  Quote.Discount           -> fine, in approval entry criteria and reports
WRITE Quote.Discount           -> impossible, no field update exists to build
WRITE QuoteLineItem.Discount   -> correct target for any reset or reversal

Also read-only on Quote (no Create, no Update):
  GrandTotal, Subtotal, TotalPrice, LineItemCount, QuoteNumber, IsSyncing, AccountId
Writable on Quote: Tax, ShippingHandling, Status, ExpirationDate, Pricebook2Id
```

Test with a non-admin user as well — but for the documented reason, not an invented one: an administrator can edit records that an approval process has locked, so an admin's run never exercises the lock. UNVERIFIED (2026-09-05): the older claim that System Administrators bypass approval *entry criteria* is not supported by the Metadata API Developer Guide or the Object Reference, and help.salesforce.com cannot be fetched. Do not generate it.

**Detection hint:** any field update, `inputAssignments` or `assignToReference` whose target is `Quote.Discount`, `Quote.GrandTotal`, `Quote.Subtotal`, `Quote.TotalPrice`, `Quote.QuoteNumber` or `Quote.IsSyncing`. `scripts/check_quotes_and_quote_templates.py` flags these as ERROR.

---

---

## Anti-Pattern 5: Treating Quote PDF as a Saved Snapshot Immune to Template Changes

**What the LLM generates:** Statements like "once you generate the PDF, it is saved on the quote record and will not change" or "the PDF attached to the quote is the final version that will be emailed."

**Why it happens:** LLMs assume that the "Generate PDF" action creates a static file. While Salesforce saves the PDF as a file on the record when the user clicks "Save PDF," the "Email Quote" button re-generates the PDF at send time from the current template state — it does not use the previously saved file.

**Correct pattern:**

```text
"Save PDF" button: creates a static PDF file attached to the quote record.
"Email Quote" button: re-generates a new PDF from the current template at send time.
  Does NOT use the previously saved PDF file.
If the template changes between "Save PDF" and "Email Quote," the customer receives
  the new version, not the reviewed version.
To guarantee the customer receives the exact reviewed PDF:
  1. Save the PDF as a Salesforce File on the quote.
  2. Email it as a manual attachment, NOT via the "Email Quote" button.
```

**Detection hint:** Any statement that the quote PDF "is saved" and will be the version emailed to the customer without qualifying that "Email Quote" re-generates from the current template.

---

---

## Anti-Pattern 6: Referencing Opportunity or Account Fields Directly in Quote Template Merge Fields

**What the LLM generates:** Template configuration instructions that include merge fields like `{!Opportunity.Name}`, `{!Account.BillingCity}`, or `{!Opportunity.Custom_Field__c}` directly in the quote template header or footer.

**Why it happens:** Salesforce merge fields work across object relationships in many contexts (email templates, formula fields). LLMs extrapolate this to quote templates without checking the specific field picker constraints.

**Correct pattern:**

```text
Quote template field picker only surfaces:
  - Quote object fields
  - QuoteLineItem fields (in the body table)
Opportunity and Account fields are NOT directly available as merge fields in quote templates.
Workaround: create mirror fields on Quote, populate via Flow, then use those Quote fields
  in the template field picker.
```

**Detection hint:** Any merge field in a quote template configuration that references a parent object (Opportunity, Account, Contact) rather than a Quote or QuoteLineItem field.

---

## Anti-Pattern 7: Treating Quote Templates as Deployable Metadata

**What the LLM generates:** A `package.xml` containing `<name>QuoteTemplate</name>`, a path like `force-app/main/default/quoteTemplates/Standard.quoteTemplate-meta.xml`, or a release plan whose sandbox-to-production step includes "deploy the quote template".

**Why it happens:** Nearly every Setup artefact in Salesforce has a metadata type, so the prior is overwhelming. The token `QuoteTemplate` also genuinely appears in the Metadata API guide — as an enum value — which is enough to make a plausible-looking type name.

**Correct pattern:**

```text
There is NO QuoteTemplate metadata type.
api_meta.txt contains "QuoteTemplate" exactly once (L83165), as a value of the
SummaryLayoutStyle enumeration on Layout.SummaryLayout. No file suffix, no
directory location, no field table, no sample definition.

Deployable around the template:
  Settings:Quote                 (enableQuote, enableQuotesWithoutOppEnabled)
  StandardValueSet:QuoteStatus   (statuses + allowEmail)
  CustomField / ValidationRule / Layout on Quote

Not deployable:
  the template itself -> rebuild in Setup per org, track in
  templates/quote-template-checklist.json, audit via QuoteDocument.DocumentTemplate
```

**Detection hint:** any `.quoteTemplate-meta.xml` path, any `QuoteTemplate` member in a manifest, or any migration plan that moves a template without a manual rebuild step.

---

---

## Anti-Pattern 8: Hand-Writing a Partial `QuoteStatus` Standard Value Set

**What the LLM generates:** A `QuoteStatus.standardValueSet-meta.xml` containing only the statuses relevant to the current request — typically two or three — presented as a complete file to deploy.

**Why it happens:** Sample definitions in documentation are always abbreviated, and picklist deploys feel additive by analogy with adding a field. The destructive behaviour is stated under `CustomValue`, not under `StandardValueSet`, so it is easy to miss even when reading the right page.

**Correct pattern:**

```text
"If picklist values are missing from a component definition, they get deactivated
 when deployed. Deactivation occurs for picklist values of both standard and
 custom fields."                                    (api_meta.txt L47481-47483)

ALWAYS:
  sf project retrieve start --metadata "StandardValueSet:QuoteStatus" --target-org <alias>
  edit the retrieved file
  sf project deploy start --manifest manifest/package.xml

The complete standard Quote.Status set (object_reference.txt L239996-240005):
  Draft, Needs Review, In Review, Approved, Rejected, Presented, Accepted, Denied
StandardValueSet also refuses "*" in package.xml (api_meta.txt L130830-130832).
```

**Detection hint:** a `QuoteStatus` value set authored from scratch, or one missing any of the eight standard statuses. The skill's checker reports this as ERROR.

---
